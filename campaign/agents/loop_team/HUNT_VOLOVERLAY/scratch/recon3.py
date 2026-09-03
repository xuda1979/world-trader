"""Recon 3: flipped-sign gates (dim when signal BAD), NaN audit, quintile detail, calendar."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VOLOVERLAY/scratch')
import lib, numpy as np, pandas as pd

r = lib.champion()
GROSS = 3.367
def prep(s):
    s = s.dropna(); s.index = pd.to_datetime(s.index); return s.sort_index()
def ev(m, tag):
    me = m.shift(1).reindex(r.index).fillna(1.0)
    turn = me.diff().abs().fillna(0.0)
    r_ov = r*me - turn*GROSS*6e-4
    r_ov1 = r*me - turn*1.0*6e-4
    s = lib.stats(r_ov[r_ov.index>='2008-01-01']); s1 = lib.stats(r_ov1[r_ov1.index>='2008-01-01'])
    h = lib.halves(r_ov[r_ov.index>='2008-01-01'])
    print(f"{tag:34s} on%={(me<1).mean()*100:5.1f} SR={s['sr']:.3f} dSR={s['sr']-3.9397:+.3f} "
          f"d@1x={s1['sr']-3.9397:+.3f} ann={s['ann_geo']:5.1f} MDD={s['mdd']:6.2f} negy={s['negy']} "
          f"H1={h[0]:.2f} H2={h[1]:.2f}")
    return s

rv63z = lib.exz((r.rolling(63).std()*np.sqrt(252)), minp=252)
vix = prep(lib.fred('VIXCLS')); vixz = lib.exz(vix, minp=504)
t2 = prep(lib.fred('us2y')); t10 = prep(lib.fred('us10y')); slope_z = lib.exz((t10-t2).dropna(), minp=504)
cred_z = lib.exz((prep(lib.fred('baa'))-prep(lib.fred('aaa'))).dropna(), minp=504)
dvi21 = vix.diff(21)
ff = lib.ff_factors(); mkt = ff['Mkt-RF']; mktz = lib.exz(mkt.rolling(63).std()*np.sqrt(252), minp=252)
mxm = prep(lib.fred('DEXMXUS')).pct_change(21)

# NaN audit on alignment
x = dvi21.reindex(r.index)
print("NaN days in dvi21 alignment:", x.isna().sum(), " vix sample:", vix.index[0].date(), vix.index[-1].date())

print("--- FLIPPED gates: m=1 normally, DIM when signal bad ---")
ev(pd.Series(np.where(rv63z.reindex(r.index) > 1.0, 0.0, 1.0), index=r.index), "OFF when rv63z>1 (champ own)")
ev(pd.Series(np.where(mktz.reindex(r.index) > 1.0, 0.0, 1.0), index=r.index), "OFF when mkt_rv63z>1")
ev(pd.Series(np.where(slope_z.reindex(r.index) < -0.5, 0.0, 1.0), index=r.index), "OFF when slope_z<-0.5 (inverted)")
ev(pd.Series(np.where(cred_z.reindex(r.index) > 1.0, 0.0, 1.0), index=r.index), "OFF when cred_z>1 (stretched)")
ev(pd.Series(np.where(vixz.reindex(r.index) > 1.0, 0.0, 1.0), index=r.index), "OFF when vix_z>1")
ev(pd.Series(np.where(dvi21.reindex(r.index) > 0, 1.0, 0.0), index=r.index), "ON only when dvix21>0 (flip)")
ev(pd.Series(np.where(dvi21.reindex(r.index) < 0, 1.0, 0.0), index=r.index), "ON only when dvix21<0")
ev(pd.Series(np.where(mxm.reindex(r.index) > 0, 1.0, 0.0), index=r.index), "ON only when mx_mom21>0")

print("--- quintile detail (mean bp/day by quintile of signal at t-1) ---")
for nm, s in [('dvi21', dvi21), ('slope_z', slope_z), ('rv63z', rv63z), ('cred_z', cred_z), ('mxm21', mxm)]:
    j = pd.concat([r.rename('r'), s.shift(1).rename('x')], axis=1).dropna()
    q = pd.qcut(j.x, 5, labels=False, duplicates='drop')
    qm = (j.groupby(q).r.mean()*1e4).round(1)
    srq = j.groupby(q).r.apply(lambda z: z.mean()/z.std()*np.sqrt(252)).round(2)
    print(f"{nm:8s} qmeans {list(qm.values)}  qSRs {list(srq.values)}")

print("--- calendar structure of champion (full-sample, diagnostic only) ---")
dow = r.groupby(r.index.dayofweek).apply(lambda z: z.mean()/z.std()*np.sqrt(252))
print("SR by weekday Mon-Fri:", dow.round(2).to_dict())
mon = r.groupby(r.index.month).apply(lambda z: z.mean()/z.std()*np.sqrt(252))
print("SR by month:", mon.round(2).to_dict())
