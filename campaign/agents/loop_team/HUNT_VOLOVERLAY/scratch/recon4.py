"""Recon 4: DD-throttle / vol-target / breadth / H1-fit-combo families."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VOLOVERLAY/scratch')
import lib, numpy as np, pandas as pd

r = lib.champion()
GROSS = 3.367
def ev(m, tag, cap=1.0, quiet=False):
    me = m.clip(upper=cap, lower=0.0).shift(1).reindex(r.index).fillna(1.0)
    turn = me.diff().abs().fillna(0.0)
    r_ov = r*me - turn*GROSS*6e-4
    s = lib.stats(r_ov[r_ov.index>='2008-01-01'])
    h = lib.halves(r_ov[r_ov.index>='2008-01-01'])
    if not quiet:
        print(f"{tag:40s} on%={(me<1).mean()*100:5.1f} SR={s['sr']:.3f} dSR={s['sr']-3.9397:+.3f} "
              f"ann={s['ann_geo']:5.1f} MDD={s['mdd']:6.2f} negy={s['negy']} H1={h[0]:.2f} H2={h[1]:.2f}")
    return s['sr']-3.9397, s, h

print("BASE: SR 3.940 ann 43.75 MDD -4.92 negy 0")

# ---- Family 1: DD-throttle (trailing 126d max) on the CHAMPION itself
eq = (1+r).cumprod()
rm126 = eq.rolling(126).max().shift(1); dd = eq.shift(1)/rm126-1
for thr in (0.01, 0.02, 0.04):
    m = pd.Series(np.where(dd.reindex(r.index) < -thr, 0.5, 1.0), index=r.index)
    ev(m, f"throttle<-{thr}x0.5 (champ own dd)")
# note: champion already throttles at -4%/-3% internally. Check overlap:
m04 = pd.Series(np.where(dd.reindex(r.index) < -0.04, 0.5, 1.0), index=r.index)
print("days champion own 126d-dd < -4%:", int((dd.reindex(r.index)<-0.04).sum()))

# ---- Family 2: vol-targeting the champion (rv63 trailing, tgt 10%, cap 2)
for win in (21, 63, 252):
    rv = r.rolling(win).std()*np.sqrt(252)
    sc = (0.10/rv.shift(1)).clip(0, 2.0)
    m = pd.Series(sc, index=r.index).fillna(1.0)
    ev(m, f"voltarget rv{win} tgt10 cap2")
    sc6 = (0.06/rv.shift(1)).clip(0, 2.0)
    m6 = pd.Series(sc6, index=r.index).fillna(1.0)
    ev(m6, f"voltarget rv{win} tgt6 cap2")

# ---- Family 3: breadth (twelve_big), trailing
px = lib.closes()
rets = px.pct_change()
breadth = (rets > 0).mean(axis=1)   # fraction of universe up that day, known at close t
br63 = breadth.rolling(63).mean()   # 63d breadth regime
brz = lib.exz(breadth.rolling(21).mean(), minp=252)
print("breadth coverage:", breadth.first_valid_index().date(), breadth.last_valid_index().date(),
      "names/day median:", int(rets.notna().sum(axis=1).median()))
m = pd.Series(np.where(br63.shift(1).reindex(r.index) > 0.5, 1.0, 0.0), index=r.index)
ev(m, "ON when breadth63>0.5")
m = pd.Series(np.where(brz.shift(1).reindex(r.index) > 0, 1.0, 0.0), index=r.index)
ev(m, "ON when breadth21z>0")
m = pd.Series(np.where(brz.shift(1).reindex(r.index) < 0, 0.0, 1.0), index=r.index)
ev(m, "OFF when breadth21z<0")

# ---- Family 4: H1-fit -> H2-test (honest split protocol)
print("--- H1-fit -> H2-test: pick best of recon2/3 H1 by dSR_H1, test on H2 ---")
from recon2 import CANDS  # reuse? no - rebuild minimal set inline below
