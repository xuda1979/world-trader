"""A5 idea 2: Vol-managed equity premium (Moreira-Muir). Long SPY, scaled by
1/lagged realized vol (21d and variants), vol-target 10%, T+1, 6bps.
Baseline comparison: buy-hold SPY with same vol target."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
from a5_common import *
import data as D

spy = D.closes()["SPY"]
r1 = spy.pct_change(); r1.index = r1.index.tz_localize(None)
r1 = r1[r1.index >= "2007-01-01"]

def run(win=21, lev_cap=2.0, vt=0.10, minlen=60):
    rv = r1.rolling(win).std()
    # Moreira-Muir: w_t = vt / sigma_{t-1}; expand-min 60d warmup via min_periods
    w = (vt/np.sqrt(252)/rv).clip(0, lev_cap)
    w = w.where(pd.Series(np.arange(len(w)), index=w.index) >= minlen, 0.0) if False else w
    w.iloc[:minlen] = 0.0
    pos = w.shift(1)  # T+1
    gross = pos*r1
    to = pos.diff().abs().fillna(pos.abs())
    net = gross - to*D.COST/1e4
    return net.dropna()

def run_gate(win=21, lev_cap=2.0, vt=0.10):
    rv = r1.rolling(win).std()
    w = (vt/np.sqrt(252)/rv).clip(0,lev_cap); w.iloc[:60]=0.0
    pos = w.shift(1)
    gross = pos*r1
    to = pos.diff().abs().fillna(pos.abs())
    net = gross - to*D.COST/1e4
    # full gate_report incl. signal scramble (positions vs SPY returns)
    s = stats(net); h1,h2 = halves(net)
    sp = scramble_pval_sig(pos.dropna(), r1, n=200)
    ok_a = s['sr']>=0.6; ok_c = h1>=0.3 and h2>=0.3
    ok_d = s['neg_yr']<=2 and s['worst']>-5.0; ok_e = sp<=0.05
    print(f"win={win} cap={lev_cap}: SR={s['sr']:.2f} ann={s['ann']:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={s['neg_yr']} worst={s['worst']:.1f}% scram={sp:.3f} gates a={ok_a} c={ok_c} d={ok_d} e={ok_e}")
    return net, (ok_a and ok_c and ok_d and ok_e)

if __name__ == "__main__":
    # baseline vol-targeted buy&hold for reference
    w = pd.Series(1.0, index=r1.index); w.iloc[:60]=0.0
    strat_vol = (w*r1).rolling(60).std()
    sc = (0.10/np.sqrt(252)/strat_vol).clip(0,2).shift(1).fillna(0)
    bh = ((w*r1)*sc - (w*sc).diff().abs().fillna((w*sc))*D.COST/1e4).dropna()
    s = stats(bh); h1,h2 = halves(bh)
    print(f"BASELINE vol-tgt B&H: SR={s['sr']:.2f} ann={s['ann']:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={s['neg_yr']} worst={s['worst']:.1f}%")
    for win in [10, 21, 42, 63]:
        for cap in [1.5, 2.0, 3.0]:
            run_gate(win, cap)
