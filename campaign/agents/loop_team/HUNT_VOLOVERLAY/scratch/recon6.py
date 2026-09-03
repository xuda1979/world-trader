"""Recon 6: internal-state overlays (zero-run structure, loss streaks) + plateau of best family."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VOLOVERLAY/scratch')
import lib, numpy as np, pandas as pd

r = lib.champion()
GROSS = 3.367
def ev(m, tag):
    me = m.clip(0,1).shift(1).reindex(r.index).fillna(1.0)
    turn = me.diff().abs().fillna(0.0)
    r_ov = r*me - turn*GROSS*6e-4
    s = lib.stats(r_ov[r_ov.index>='2008-01-01'])
    h = lib.halves(r_ov[r_ov.index>='2008-01-01'])
    print(f"{tag:44s} SR={s['sr']:.4f} dSR={s['sr']-3.9397:+.4f} ann={s['ann_geo']:5.1f} "
          f"MDD={s['mdd']:6.2f} negy={s['negy']} H1={h[0]:.2f} H2={h[1]:.2f}")

# trailing zero-fraction of champion (proxy for gated-off sleeves)
z = (r.abs() < 1e-9).rolling(21).mean()
print("zero-day frac:", round((r.abs()<1e-9).mean(),4), " trailing-z range:", round(z.min(),3), round(z.max(),3))
for th in (0.2, 0.3, 0.5):
    ev(pd.Series(np.where(z.reindex(r.index) > th, 0.5, 1.0), index=r.index), f"OFF(m=0.5) when zerofrac21>{th}")
    ev(pd.Series(np.where(z.reindex(r.index) > th, 1.0, 0.5), index=r.index), f"ON(m=1) only when zerofrac21>{th}")

# loss-streak state
loss = (r < 0).astype(int)
streak = loss.rolling(3).sum()
for th in (2, 3):
    ev(pd.Series(np.where(streak.reindex(r.index) >= th, 0.5, 1.0), index=r.index), f"OFF after {th}-loss streak (3d)")

# champion magnitude state: |r| trailing mean (its own activity)
act = r.abs().rolling(63).mean()
az = lib.exz(act, minp=252)
ev(pd.Series(np.where(az.reindex(r.index) > 1.0, 0.7, 1.0), index=r.index), "OFF(0.7) when activity-z>1")
ev(pd.Series(np.where(az.reindex(r.index) < -1.0, 0.7, 1.0), index=r.index), "OFF(0.7) when activity-z<-1")

# plateau of best family (vol-target rv252): tgt sweep x cap sweep
print("--- voltarget rv252 plateau (tgt, cap) -> dSR ---")
rv252 = r.rolling(252).std()*np.sqrt(252)
for tgt in (0.06, 0.08, 0.10, 0.12):
    row = []
    for cap in (1.5, 2.0, 3.0):
        m = pd.Series((tgt/rv252).clip(0, cap), index=r.index).fillna(1.0)
        me = m.clip(0,1).shift(1).reindex(r.index).fillna(1.0)
        turn = me.diff().abs().fillna(0.0)
        r_ov = r*me - turn*GROSS*6e-4
        s = lib.stats(r_ov[r_ov.index>='2008-01-01'])
        row.append(f"cap{cap}: dSR {s['sr']-3.9397:+.4f} ann {s['ann_geo']:.1f}")
    print(f"  tgt{tgt:.2f} | " + " | ".join(row))
