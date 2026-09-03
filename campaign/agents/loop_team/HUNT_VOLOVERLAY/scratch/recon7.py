"""Recon 7: VRP spread, real yield, inflation swap, liquidity, dollar-z overlays (last family)."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VOLOVERLAY/scratch')
import lib, numpy as np, pandas as pd

r = lib.champion()
GROSS = 3.367
def prep(s):
    s = s.dropna(); s.index = pd.to_datetime(s.index); return s.sort_index()
def ev(m, tag):
    me = m.clip(0,1).shift(1).reindex(r.index).fillna(1.0)
    turn = me.diff().abs().fillna(0.0)
    r_ov = r*me - turn*GROSS*6e-4
    s = lib.stats(r_ov[r_ov.index>='2008-01-01'])
    h = lib.halves(r_ov[r_ov.index>='2008-01-01'])
    print(f"{tag:44s} SR={s['sr']:.4f} dSR={s['sr']-3.9397:+.4f} ann={s['ann_geo']:5.1f} "
          f"MDD={s['mdd']:6.2f} negy={s['negy']} H1={h[0]:.2f} H2={h[1]:.2f}")
    return s['sr']-3.9397, h

spx = prep(lib.fred('spx'))
spx_rv21 = spx.pct_change().rolling(21).std()*np.sqrt(252)*100
vix = prep(lib.fred('VIXCLS'))
vrp = (vix - spx_rv21).dropna()      # variance risk premium proxy (permitted: vix/rates/EM FX)
vrp_z = lib.exz(vrp, minp=504)
print("VRP coverage:", vrp.index[0].date(), vrp.index[-1].date(), "mean", round(vrp.mean(),2))

for th in (-1.0, 0.0, 1.0):
    ev(pd.Series(np.where(vrp_z.reindex(r.index) > th, 1.0, 0.0), index=r.index), f"ON when vrp_z>{th}")
    ev(pd.Series(np.where(vrp_z.reindex(r.index) < th, 0.0, 1.0), index=r.index), f"OFF when vrp_z<{th}")
ev(pd.Series(np.where(vrp.reindex(r.index) > 0, 1.0, 0.0), index=r.index), "ON when vrp>0 (raw)")

dfii = prep(lib.fred('DFII10')); dz = lib.exz(dfii, minp=504)
for th in (-1.0, 0.0):
    ev(pd.Series(np.where(dz.reindex(r.index) > th, 1.0, 0.0), index=r.index), f"ON when real10_z>{th}")
    ev(pd.Series(np.where(dz.reindex(r.index) < th, 0.0, 1.0), index=r.index), f"OFF when real10_z<{th}")

t5ifp = prep(lib.fred('T5YIFP')); iz = lib.exz(t5ifp, minp=504)
ev(pd.Series(np.where(iz.reindex(r.index) > 0, 1.0, 0.0), index=r.index), "ON when inflswap_z>0")
ev(pd.Series(np.where(iz.reindex(r.index) < 0, 0.0, 1.0), index=r.index), "OFF when inflswap_z<0")

walcl = prep(lib.fred('WALCL')); wz = lib.exz(walcl.pct_change(63), minp=504)
ev(pd.Series(np.where(wz.reindex(r.index) > 0, 1.0, 0.0), index=r.index), "ON when liq63chg_z>0")

dtw = prep(lib.fred('DTWEXBGS')); dlz = lib.exz(dtw, minp=504)
ev(pd.Series(np.where(dlz.reindex(r.index) < 0, 1.0, 0.0), index=r.index), "OFF when dxy_z>0")
ev(pd.Series(np.where(dtw.diff(63).reindex(r.index) < 0, 0.5, 1.0), index=r.index), "HALF when dxy_mom63<0")
