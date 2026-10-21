"""A5 idea 4: VIX break-glass — long SPY *amplified* (or gamma-hedge proxy:
long SPY after vol spike stabilizes) when vix/vix3m ratio spikes >1 while
VIX>32. Test as standalone event sleeve + as overlay multiplier."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/scripts")
from a5_common import *
import data as D

vd = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv', parse_dates=['DATE']).set_index('DATE')['vix']
v3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv', parse_dates=['DATE']).set_index('DATE')['vix3m']
ts = pd.concat([vd,v3],axis=1).dropna()
spy = D.closes()["SPY"]; r1 = spy.pct_change(); r1.index = r1.index.tz_localize(None)

def event_pos(spike=1.0, vth=32, hold=10):
    trig = ((ts["vix"]>vth) & (ts["vix"]/ts["vix3m"]>spike)).astype(float)
    # hold for `hold` days after trigger (trailing window max => still on)
    on = trig.rolling(hold, min_periods=1).max()
    pos = on.shift(1)  # T+1
    pos = pos.reindex(r1.index).fillna(0.0)
    return pos

def eval_pos(pos, name, lev=1.0):
    p = pos*lev
    gross = p*r1.reindex(p.index).fillna(0.0)
    to = p.diff().abs().fillna(p.abs())
    net = gross - to*D.COST/1e4
    s = stats(net); h1,h2 = halves(net)
    print(f"{name}: n={s['n']} SR={s['sr']:.2f} ann={s['ann']:.1f}% H1={h1:.2f} H2={h2:.2f} negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% days_on={int((p>0).sum())}")
    return net

if __name__ == "__main__":
    print("=== idea4 standalone event sleeve (long SPY during/after spike) ===")
    for vth in [28, 32, 36]:
        for hold in [5, 10, 20]:
            p = event_pos(1.0, vth, hold)
            eval_pos(p, f"vix>{vth} hold={hold}")
    # variant: LONG the recovery — buy when VIX was >32 in last 10d AND vix/vix3m fell back below 1
    trig_hi = (ts["vix"]>32).astype(float).rolling(15, min_periods=1).max()
    calm = (ts["vix"]/ts["vix3m"] < 1.0).astype(float)
    p = (trig_hi*calm).shift(1).reindex(r1.index).fillna(0.0)
    eval_pos(p, "post-spike re-contango")
    # variant: short SPY during active spike (break-glass hedge)
    p = event_pos(1.0, 32, 10)
    eval_pos(-p, "SHORT during spike")
