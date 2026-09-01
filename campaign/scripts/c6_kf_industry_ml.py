"""C6 Idea 2: KF-industry-ML. Cross-sectional Ridge on 48-industry VW trailing features ->
next-5d xs-z industry return -> long top3 / short bottom3, weekly rebalance.
Walk-forward expanding refit quarterly (purge 12d), T+1, 6bps/side, vol-target 10% trailing.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval
from sklearn.linear_model import Ridge

vw = pd.read_parquet('/tmp/kf48_vw.parquet').loc['2004-01-01':'2026-06-30']
inds = list(vw.columns)
logv = np.log1p(vw.clip(-0.5, 0.5))
m21, m63, m126, m252 = (np.log1p(vw.clip(-0.5,0.5)).rolling(w).sum() for w in (21,63,126,252))
vol21 = vw.rolling(21).std()
ret1 = vw.copy()
def rankz(df):
    r = df.rank(axis=1)
    return (r.sub(r.mean(axis=1),axis=0)).div(r.std(axis=1),axis=0)
def xsz(df):
    return df.sub(df.mean(axis=1),axis=0).div(df.std(axis=1),axis=0)
feats = {'mom21':m21,'mom63':m63,'mom126':m126,'mom252':m252,'vol21':vol21,'ret1':ret1}
X = pd.concat({k: rankz(v) for k,v in feats.items()}, axis=1)
X.columns = X.columns.get_level_values(0)+'_'+X.columns.get_level_values(1).astype(str)
fwd5x = xsz(vw.rolling(5).sum().shift(-5))

dates = X.index
qends = pd.date_range('2007-07-01','2026-06-30',freq='QE')
score = pd.DataFrame(np.nan, index=dates, columns=inds)
coefs = []
for qe in qends:
    te = (dates > qe) & (dates <= qe + pd.offsets.QuarterEnd(1))
    tr = dates <= qe - pd.Timedelta(days=12)
    if tr.sum() < 504 or te.sum()==0: continue
    ok = X[tr].notna().all(axis=1) & fwd5x[tr].notna().all(axis=1)
    Xi, yi = X[tr][ok], fwd5x[tr][ok]
    n=len(Xi)
    if n>1008: a_tr=np.arange(n)>=n//2; a_fit=~a_tr
    else:      a_fit=np.arange(n)<252; a_tr=~a_fit
    best_a, best_v = 10.0, 1e9
    Ymat = yi
    for a in (1.0, 10.0, 100.0):
        v = 0.0
        for c in inds:
            m = Ridge(alpha=a).fit(Xi.values[a_fit], Ymat[c].values[a_fit])
            v += ((m.predict(Xi.values[a_tr]) - Ymat[c].values[a_tr])**2).mean()
        v /= len(inds)
        if v < best_v: best_v, best_a = v, a
    for j,c in enumerate(inds):
        m = Ridge(alpha=best_a).fit(Xi.values, Ymat[c].values)
        Xte = X[te].ffill().fillna(0.0)
        score.loc[dates[te], c] = m.predict(Xte)
    coefs.append((str(qe.date()), best_a, [round(abs(m.coef_).sum(),3) for m in [Ridge(alpha=best_a).fit(Xi, Ymat[inds[0]])]]))

print('score coverage', score.notna().mean().mean().round(3), score.index.min().date(), score.index.max().date())
# weekly portfolio: first trading day of week, hold score from t-1 (T+1)
wk = score.copy()
dts = wk.index
is_reb = pd.Series(dts, index=dts).dt.dayofweek.diff().fillna(0) < 0   # new week
# portfolio held day t built from score at t-1: top3 long bottom3 short
sc = score.shift(1)
longs = sc.rank(axis=1, ascending=False) <= 3
shorts = sc.rank(axis=1) <= 3
pos = longs.astype(float)*0.5 - shorts.astype(float)*0.5   # +0.5 each long, -0.5 each short => gross 3.0, net 0
# recompute only on reb days? simpler: daily positions from shifted score (turnover small since ranks persistent)
r = vw
gross = (pos*r).sum(axis=1) - 0.0
turn = pos.diff().abs().sum(axis=1).fillna(pos.abs().sum(axis=1))
gross = gross - 6e-4*turn
gross = gross[gross.index>='2008-01-01']
ns, scale = vol_target(gross, 0.10)
st = full_stats(ns); h1,h2 = halves_sr(ns); pv,rsr = scramble_pval(ns)
print('FULL',{k:(round(v,2) if isinstance(v,float) else v) for k,v in st.items() if k!='yearly'})
print('halves',round(h1,2),round(h2,2),'scramble p',pv)
oos = ns[ns.index>='2017-01-01']; so = full_stats(oos)
print('OOS',{k:(round(v,2) if isinstance(v,float) else v) for k,v in so.items() if k!='yearly'})
b = pd.read_csv('/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv',index_col=0,parse_dates=True)['ret']
j = pd.concat([ns,b],axis=1,join='inner').dropna()
print('corr blend',round(j.corr().iloc[0,1],3),'n',len(j))
print('yearly',st['yearly'])
ns.to_frame('ret').to_csv('/tmp/c6_kf_ml.csv')
np.save('/tmp/kf_score_last.npy', np.array([str(qe.date()) for qe in qends[:3]]))
