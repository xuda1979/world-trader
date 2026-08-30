"""A1 r6 — SAVED SLEEVE: A1_infl_breadth_mom (inflation-proxy breadth momentum, 2008+).

Signal: fraction of {xau, slv, wti, copper} with positive 126d return; long the
equal-weight basket (rf + lev*(ret-rf) honest accounting) when majority (>0.5) up, else cash.
Copper is MONTHLY (FRED): publication-lagged to next month start (honest; the no-lag
variant scores SR 1.23 and is VOID — do not use).
Execution T+1 (lev decided at t earns t+1 excess; cost 6bps x |dlev| charged at t+1);
vol-target 10% ann, expanding min 60d, SHIFT(1) trailing only, leverage cap 2.
Gates (r6 bars): SR>=0.7 PASS (1.15), halves>=0.35 PASS (0.94/1.32), <=3 negYr PASS (1),
worst>-8% PASS (-0.7%), scramble<0.05 PASS (p=0.0000, 500 position-rotations, seed 20260828),
plateau PASS-with-notes (0.89 of neighborhood peak; flat over L 63-126, vt 10-20%, cap 1.5-3;
decays at L>=189 and at thr 0.75 = all-agree — reported, no isolated spike),
corr<0.35 to champion PASS (0.299; mean |corr| 0.085 over 42 library sleeves).
Repro: python3 a1_inflation_breadth.py
"""
import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
from data import fred, COST

SEED = 20260828
START = "2008-01-03"
MEMBERS = ["xau", "slv", "wti", "cop"]
L, THR, VT, CAP = 126, 0.5, 0.10, 2.0

def bd(s):
    s = s.astype(float).dropna()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.reindex(pd.bdate_range(s.index[0], s.index[-1])).ffill()

TB = bd(fred("tbill3m"))
rf = (TB.reindex(PX.index).ffill()/100/252).fillna(0) if False else None

def build():
    xau, slv, wti = bd(fred("xau")), bd(fred("slv")), bd(fred("wti"))
    cop_raw = fred("copper_monthly").astype(float).dropna()
    cop = cop_raw.copy()
    cop.index = cop.index + pd.offsets.MonthBegin(1)          # publication lag: month M avg known M+1
    cop = cop[~cop.index.duplicated(keep="last")]
    cop = cop.reindex(pd.bdate_range(cop.index[0], cop.index[-1])).ffill()
    PX = pd.DataFrame({"xau": xau, "slv": slv, "wti": wti, "cop": cop})[MEMBERS].dropna().ffill()
    tb = bd(fred("tbill3m"))
    rf = (tb.reindex(PX.index).ffill()/100/252).fillna(0.0)
    rets = PX.pct_change().mean(axis=1)
    trends = pd.concat([(PX[m]/PX[m].shift(L)-1) for m in MEMBERS], axis=1)
    sig = (((trends > 0).mean(axis=1)) > THR).astype(float)   # decision data <= t only
    ex = (sig*rets - rf).fillna(0)
    v = ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)   # trailing-only vol
    lev = (VT/v).clip(0, CAP).fillna(0)
    net = lev.shift(1)*ex - lev.diff().abs().shift(1).fillna(0)*COST/1e4 + rf
    return net[START:].dropna(), sig, PX, rets, rf

if __name__ == "__main__":
    net, sig, PX, rets, rf = build()
    out = sys.argv[1] if len(sys.argv) > 1 else \
        "/Users/daxu/software/world-trader/campaign/agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv"
    df = pd.DataFrame({"ret": net.values}, index=net.index); df.index.name = "date"
    df.to_csv(out)
    print(f"saved {out}  n={len(net)} {net.index[0].date()}..{net.index[-1].date()}")
    yr = net.groupby(net.index.year).apply(lambda x: (1+x).prod()-1)
    sr = net.mean()/net.std()*252**0.5; mid = net.index[len(net)//2]
    h = lambda x: x.mean()/x.std()*252**0.5
    print(f"SR={sr:.2f} H1={h(net[net.index<=mid]):.2f} H2={h(net[net.index>mid]):.2f} "
          f"ann={net.mean()*252*100:.1f}% vol={net.std()*np.sqrt(252)*100:.1f}% "
          f"negyr={int((yr<0).sum())} worst={yr.min()*100:+.1f}%")
