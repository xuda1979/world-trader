"""Recon 5: (a) SAFE/AGGR tilt screen, (b) ridge combo H1-fit->H2-test,
(c) full protocol on best-2 candidates, (d) overlay budget arithmetic."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VOLOVERLAY/scratch')
import lib, numpy as np, pandas as pd

r = lib.champion()
GROSS = 3.367
def prep(s):
    s = s.dropna(); s.index = pd.to_datetime(s.index); return s.sort_index()

SAFE = pd.read_csv(f"{lib.ROOT}/campaign/results/GOAL100_HONEST14V3_SAFE_daily.csv",
                   index_col=0, parse_dates=True).iloc[:,0]
AGGR = pd.read_csv(f"{lib.ROOT}/campaign/results/GOAL100_HONEST14V3_AGGRESSIVE_daily.csv",
                   index_col=0, parse_dates=True).iloc[:,0]

# signal panel (T+1 aligned)
rv63z = lib.exz((r.rolling(63).std()*np.sqrt(252)), minp=252)
vix = prep(lib.fred('VIXCLS')); vixz = lib.exz(vix, minp=504); dvi21 = vix.diff(21)
t2 = prep(lib.fred('us2y')); t10 = prep(lib.fred('us10y')); slope_z = lib.exz((t10-t2).dropna(), minp=504)
cred_z = lib.exz((prep(lib.fred('baa'))-prep(lib.fred('aaa'))).dropna(), minp=504)
ff = lib.ff_factors(); mktz = lib.exz(ff['Mkt-RF'].rolling(63).std()*np.sqrt(252), minp=252)
mxm = prep(lib.fred('DEXMXUS')).pct_change(21)
px = lib.closes(); breadth = (px.pct_change()>0).mean(axis=1); brz = lib.exz(breadth.rolling(21).mean(), minp=252)
S = pd.DataFrame({'rv63z':rv63z,'vixz':vixz,'dvi21':dvi21,'slope_z':slope_z,'cred_z':cred_z,
                  'mktz':mktz,'mxm21':mxm,'brz':brz}).shift(1).reindex(r.index)

print("=== (a) SAFE/AGGR relative-return tilt screen: corr(diff_{t}, sig_{t-1}) ===")
d = (AGGR-SAFE).reindex(r.index)
for c in S.columns:
    j = pd.concat([d.rename('d'), S[c].rename('x')], axis=1).dropna()
    print(f"  {c:8s} corr {j['d'].corr(j['x']):+.4f}")

print("=== (b) ridge combo H1-fit -> H2-test (target: r_{t+1} std'd; predict sign/mag) ===")
j = pd.concat([r.rename('r'), S], axis=1).dropna()
j = j[j.index>='2008-01-01']
mid = j.index[len(j)//2]
X = j[['rv63z','vixz','dvi21','slope_z','cred_z','mktz','mxm21','brz']].values
y = j.r.values
mu_x, sd_x = X.mean(0), X.std(0)+1e-12
Xz = (X-mu_x)/sd_x
h1 = j.index <= mid
for lam in (0.1, 1.0, 10.0):
    A = Xz[h1]; b = y[h1]
    beta = np.linalg.solve(A.T@A + lam*np.eye(8), A.T@b)
    # in-H1 and OOS-H2: apply beta as m-tilt around 1: m = 1 + k*pred/|pred|_scale... simplest honest mapping:
    # m_t = 1 + beta_dot_x_t clipped to [0.5, 1.05]  (can only DIM, never add leverage)
    ph1 = Xz[h1]@beta; ph2 = Xz[~h1]@beta
    for k in (2e4, 5e4):
        m1 = pd.Series(np.clip(1+k*ph1, 0.5, 1.0), index=j.index[h1])
        m2 = pd.Series(np.clip(1+k*ph2, 0.5, 1.0), index=j.index[~h1])
        m = pd.concat([m1, m2]).sort_index()
        me = m.shift(1).reindex(r.index).fillna(1.0)  # note: beta fit on H1 only, applied T+1
        turn = me.diff().abs().fillna(0.0)
        r_ov = r*me - turn*GROSS*6e-4
        sH1 = lib.stats(r_ov[j.index[h1]]); sH2 = lib.stats(r_ov[j.index[~h1]])
        print(f"  lam={lam:5.1f} k={k:g}: H1 SR {sH1['sr']:.3f} (base 3.811) H2 SR {sH2['sr']:.3f} "
              f"(base 4.069) | corr(pred,r) H1 {np.corrcoef(ph1,y[h1])[0,1]:+.4f} "
              f"H2 {np.corrcoef(ph2,y[~h1])[0,1]:+.4f}")
print("  (baseline halves: H1 3.811 H2 4.069)")

print("=== (c) full protocol on best-2 candidates ===")
def full_proto(m, tag, cap=1.0):
    m = m.clip(upper=cap, lower=0.0)
    me = m.shift(1).reindex(r.index).fillna(1.0)
    turn = me.diff().abs().fillna(0.0)
    r_ov = r*me - turn*GROSS*6e-4
    s = lib.stats(r_ov[r_ov.index>='2008-01-01'])
    h = lib.halves(r_ov[r_ov.index>='2008-01-01'])
    p1 = lib.poslag_scramble(r, m, n=200, seed=7, mcap=cap)
    p2 = lib.poslag_scramble(r, m, n=200, seed=11, mcap=cap)
    p3 = lib.poslag_scramble(r, m, n=200, seed=23, mcap=cap)
    wcorr = np.corrcoef(me.fillna(1.0), (r.rolling(63).std()*np.sqrt(252)).reindex(r.index).fillna(0))[0,1]
    ac1 = me.autocorr(1)
    print(f"  {tag}: SR {s['sr']:.4f} (dSR {s['sr']-3.9397:+.4f}) ann {s['ann_geo']:.2f} MDD {s['mdd']:.2f} "
          f"negy {s['negy']} H1 {h[0]:.3f} H2 {h[1]:.3f} | scramble p {p1[0]:.3f}/{p2[0]:.3f}/{p3[0]:.3f} "
          f"| corr(m_exec,rv63) {wcorr:+.3f} ac1(m) {ac1:+.3f}")
full_proto(pd.Series(0.10/lib.exz((r.rolling(252).std()*np.sqrt(252)), minp=252).abs().reindex(r.index).values, index=r.index).fillna(1.0), "voltarget rv252 tgt10 cap2")
# rebuild clean:
rv252 = r.rolling(252).std()*np.sqrt(252)
m_vt = pd.Series((0.10/rv252.shift(0)).clip(0,2.0), index=r.index).fillna(1.0)
full_proto(m_vt, "voltarget rv252 tgt10 cap2 (clean)")
dvi = vix.diff(21).reindex(r.index)
m_q = pd.Series(np.select([dvi<=dvi.quantile(0.2), dvi<=dvi.quantile(0.4), dvi<=dvi.quantile(0.6), dvi<=dvi.quantile(0.8)],
                          [0.85,0.90,0.95,1.00], default=1.00), index=r.index)
full_proto(m_q, "dvi21 quintile ramp 0.85-1.00")

print("=== (d) overlay budget arithmetic (why gates cannot win) ===")
print(f"  champion mean {r.mean()*1e4:.1f} bp/day, sd {r.std()*1e4:.1f} bp/day (2006+)")
j2 = pd.concat([r.rename('r'), dvi21.shift(1).rename('x')], axis=1).dropna()
q = pd.qcut(j2['x'], 2, labels=False); lo, hi = j2[q==0].r.mean()*1e4, j2[q==1].r.mean()*1e4
print(f"  best split (dvi21 med): mean_lo {lo:.1f} vs mean_hi {hi:.1f} bp/day; a 50%-off gate forgoes "
      f"{(lo+hi)/4:.1f} bp/day to harvest {(hi-lo)/2:.1f} bp/day of separation => net {(hi-lo)/2-(lo+hi)/4:.1f} bp/day")
