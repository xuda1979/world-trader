"""A5 r4 idea 1 — contango+rate-shock champion re-budgeted to vt15 (pure re-budget).

Same signal as saved A5_r2_contango_rateshock (vix/vix3m contango th=1.02 hyst=0.05,
rate-shock veto W150 +25bp lvl 2.75, T+1, 6bps/side); only the vol target moves
10% -> 15% ann. Round-r4 validation: SR=1.02, ann=13.5%, H1=0.94/H2=1.10,
neg years 2/18 (2011 -0.73%, 2022 -3.09%), scramble p=0.000 (real SR consistent
with eval SR), plateau: vt 0.12-0.18 all SR=1.019 (vt axis is a pure scale),
signal grid 8 neighbor cells SR 0.87-1.005.
Window 2009-09-16..2026-08-11 (vix3m data constraint), n=4249.
NOTE: corr to vt10 twin = 1.000 — this REPLACES the vt10 member in the champion,
it is NOT a new diversifier. Coordinator decision: swap in champion blend.
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
R1 = D.closes()["SPY"].pct_change(); R1.index = R1.index.tz_localize(None)
R1 = R1.reindex(TS.index).fillna(0.0)

TH, HYST = 1.02, 0.05
W, CHG, LVL = 150, 0.25, 2.75
VT = 0.15

ratio = TS["vix"] / TS["vix3m"]
st = 0.0; base = []
for v in ratio.values:
    if v < TH: st = 1.0
    elif v > TH + HYST: st = 0.0
    base.append(st)
C = pd.Series(base, index=ratio.index)
shock = (US > LVL) & ((US - US.shift(W)) > CHG)
RS = (~shock.fillna(False)).astype(float)
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
    D.save_sleeve(net, "/Users/daxu/software/world-trader/campaign/agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv",
                  meta="")
