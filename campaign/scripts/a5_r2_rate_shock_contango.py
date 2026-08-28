"""A5 r2 — VIX term-structure contango carry with a rate-shock conditioner.
PASSING sleeve (round r2): SR=1.02, H1=0.94/H2=1.10, neg years 2/18
(2011 -0.2%, 2022 -1.9%), scramble p=0.000, plateau 27/27 grid cells >= 0.80 peak.

Rule: long SPY while VIX<VIX3M (contango, th=1.02, hyst exit +0.05); exposure = 0
when us10y > 2.75% AND us10y - us10y[150d ago] > +25bps (lag-1d trailing rate shock).
Vol target 10% ann, expanding trailing (min 60d), T+1, 6bps/side on turnover.
Window 2009-09-16..2026-08-11 (vix3m data constraint).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import data as D

V1 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv',
                 parse_dates=['DATE']).set_index('DATE')['vix']
V3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv',
                 parse_dates=['DATE']).set_index('DATE')['vix3m']
TS = pd.concat([V1, V3], axis=1).dropna()
US = D.fred('us10y').reindex(TS.index).ffill()
R1 = D.closes()["SPY"].pct_change()
R1.index = R1.index.tz_localize(None)
R1 = R1.reindex(TS.index).fillna(0.0)

TH, HYST = 1.02, 0.05          # contango gate + hysteresis (r1 plateau)
W, CHG, LVL = 150, 0.25, 2.75  # rate-shock: >+25bps over 150d while us10y>2.75%
VT = 0.10

ratio = TS["vix"] / TS["vix3m"]
st = 0.0; base = []
for v in ratio.values:                 # hysteresis state machine (signal at t)
    if v < TH: st = 1.0
    elif v > TH + HYST: st = 0.0
    base.append(st)
C = pd.Series(base, index=ratio.index)
shock = (US > LVL) & ((US - US.shift(W)) > CHG)   # NaN rise history -> no shock
RS = (~shock.fillna(False)).astype(float)          # 1 ok, 0 shock
P = C * RS
pos = P.shift(1).fillna(0.0)                                     # T+1 execution
to = pos.diff().abs().fillna(pos.abs())
net0 = pos * R1 - to * D.COST / 1e4
vol = net0.expanding(min_periods=60).std()
sc = (VT / np.sqrt(252) / vol).clip(0, 2.0).shift(1).fillna(0.0)  # trailing-only
posf = pos * sc
to2 = posf.diff().abs().fillna(posf.abs())
net = (posf * R1 - to2 * D.COST / 1e4).dropna()

if __name__ == "__main__":
    D.save_sleeve(net, "/Users/daxu/software/world-trader/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
        meta=open(__file__.replace(".py", ".meta")).read() if False else "")
