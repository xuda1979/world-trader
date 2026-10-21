"""Item 5: ML on sleeve-pool meta-state -> monthly dynamic weights; must beat EW OOS 2017+."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader'); sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd, glob, os
import c6_round2_lib as L
from campaign.harness.data import apply_cost
from campaign.agents.B2_highfreq.gates import full_stats
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge

# ---- pool: all saved agent sleeves + sleeve_library with >= ~8y coverage
files = sorted(glob.glob('/Users/daxu/software/world-trader/campaign/agents/*/sleeves/*.csv')) + \
        sorted(glob.glob('/Users/daxu/software/world-trader/campaign/results/sleeve_library/*.csv'))
rets = {}
for f in files:
    if f.endswith('.meta'): continue
    try:
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        r = df['ret'].dropna()
        r = r[r.index >= '2009-01-01']
        if len(r) >= 1500 and r.index[-1] >= pd.Timestamp('2025-01-01'):
            rets[os.path.basename(f)[:-4]] = r
    except Exception: pass
R = pd.DataFrame(rets).sort_index()
R = R.loc[:, R.count() > 0.9*len(R)]  # keep near-complete
R = R.fillna(0)
R = R.loc['2009-01-01':'2026-08-28']
print('pool:', R.shape[1], 'sleeves', str(R.index[0].date()), '->', str(R.index[-1].date()))
print(sorted(R.columns))

d = R.index; n = len(R.columns)
m21 = R.rolling(21).sum(); m63 = R.rolling(63).sum(); m252 = R.rolling(252).sum()
v21 = R.rolling(21).std()*np.sqrt(252); v63 = R.rolling(63).std()*np.sqrt(252)
# cross-sectional state (same for all sleeves): dispersion, avg pairwise corr (63d)
disp = R.std(axis=1).rolling(63).mean()
paircorr = R.rolling(63).corr().groupby(level=0).mean().mean(axis=1)
# features per sleeve-day: [sr21, sr63, sr252, vol21, vol63, dd252, disp, paircorr]
dd = (1+R).cumprod()
dd252 = dd / dd.rolling(252).max() - 1
def sr(x): return x.rolling(21).sum()/ (R.rolling(21).std()*np.sqrt(21))
F = pd.concat({'sr21': sr(R), 'sr63': m63/(R.rolling(63).std()*np.sqrt(63)),
               'sr252': m252/(R.rolling(252).std()*np.sqrt(252)), 'vol21': v21, 'vol63': v63,
               'dd252': dd252, 'disp': disp.reindex(d).reindex(d, method=None).values[:,None]*np.ones((1,n)) if False else disp,
               'pc': paircorr}, axis=1)
# build panel: stack to long form
# forward 21d sleeve ret (sum)
fwd = R.rolling(21).sum().shift(-21)
dates = d[::21]  # monthly grid
rows_X, rows_y, rows_dt, rows_cols = [], [], [], []
for dt in dates:
    i = d.get_loc(dt)
    if i < 252: continue
    xt = np.column_stack([F[k].iloc[i].values if hasattr(F[k],'iloc') else np.full(n, F[k].iloc[i]) for k in ['sr21','sr63','sr252','vol21','vol63','dd252']])
    yt = fwd.iloc[i].values
    ok = np.isfinite(xt).all(axis=1) & np.isfinite(yt)
    rows_X.append(xt); rows_y.append(yt); rows_dt.append(dt); rows_cols.append(ok)
    # extra features: dispersion & paircorr constants per date appended later
DT = pd.to_datetime(rows_dt)
Xt = np.array(rows_X); Yt = np.array(rows_y)
# add date-constant features
disp_v = disp.reindex(DT).ffill().bfill().fillna(0.0).values
pc_v = paircorr.reindex(DT).ffill().bfill().fillna(0.0).values
Xt = np.concatenate([Xt, disp_v[:,None,None]*np.ones((1,n,1)), pc_v[:,None,None]*np.ones((1,n,1))], axis=2)

# walk-forward: expanding, refit every 12 months, purge 21d (fwd horizon overlaps)
sig = np.full((len(DT), n), np.nan)
for i in range(len(DT)):
    dt = DT[i]
    if dt < pd.Timestamp('2014-01-01'): continue
    tr = [j for j in range(i-1, -1, -1) if (dt - DT[j]).days > 42]  # purge 2x horizon
    tr_idx = tr[24:]  # every obs allowed but leave initial
    if i < 60: continue
    Xtr = Xt[tr_idx].reshape(-1, Xt.shape[2]); ytr = Yt[tr_idx].reshape(-1)
    m = np.isfinite(Xtr).all(1) & np.isfinite(ytr)
    if m.sum() < 500: continue
    model = Ridge(alpha=10.0)
    model.fit(Xtr[m], ytr[m])
    if np.isfinite(Xt[i]).all(): sig[i] = model.predict(Xt[i])

S = pd.DataFrame(sig, index=DT, columns=R.columns)
# weights: long-only, top-5 by predicted next-21d ret, equal weight; hold 21d; T+1
W = pd.DataFrame(0.0, index=DT, columns=R.columns)
for i in range(len(DT)):
    s_ = S.iloc[i]
    if s_.notna().sum() >= 5:
        top = s_.nlargest(5).index
        W.loc[DT[i], top] = 0.2
# daily returns: apply month-grid weights to daily sleeve rets
Wd = W.reindex(d).ffill().fillna(0).shift(1)  # T+1
gross = (Wd * R).sum(axis=1)
to = Wd.diff().abs().sum(axis=1).fillna(0) + Wd.abs().sum(axis=1)
net = apply_cost(gross, to)
sc = L.vt_scale(net.fillna(0)).shift(1)
netv = (net.fillna(0)*sc)
# EW baseline same pipeline
Wew = pd.DataFrame(1.0/n, index=DT, columns=R.columns)
Wew_d = Wew.reindex(d).ffill().fillna(0)  # no shift: same info timing as strategy
g_ew = (Wew_d*R).sum(axis=1); net_ew = apply_cost(g_ew, pd.Series(0.0, index=d))
net_ew_v = net_ew.fillna(0)*L.vt_scale(net_ew.fillna(0)).shift(1)
both = pd.concat([netv, net_ew_v], axis=1).dropna()
both.columns = ['ml','ew']
for col in ['ml','ew']:
    r_ = both[col][both.index>='2017-01-01']
    print(col, 'OOS2017+ SR %.2f ann %.1f%%' % (full_stats(r_)['sr'], full_stats(r_)['ann']),
          '| FULL SR %.2f' % full_stats(both[col])['sr'])
ml, ew = both['ml'], both['ew']
print('diff OOS SR', full_stats(ml[ml.index>='2017-01-01'])['sr'], full_stats(ew[ew.index>='2017-01-01'])['sr'])
print('corr ml vs blend', round(L.corr_blend(ml),3), 'corr ml vs ew', round(ml.corr(ew),3))

# ---- variant: EXCLUDE predicted-worst-5, EW the rest (charter phrasing: predict underperformers)
Wx = pd.DataFrame(0.0, index=DT, columns=R.columns)
for i in range(len(DT)):
    s_ = S.iloc[i]
    if s_.notna().sum() >= 10:
        keep = s_.drop(s_.nsmallest(5).index).index
        Wx.loc[DT[i], keep] = 1.0/len(keep)
Wxd = Wx.reindex(d).ffill().fillna(0).shift(1)
gx = (Wxd*R).sum(axis=1); nx = apply_cost(gx, Wxd.diff().abs().sum(axis=1).fillna(0))
nxv = nx.fillna(0)*L.vt_scale(nx.fillna(0)).shift(1)
jx = pd.concat([nxv, net_ew_v], axis=1).dropna(); jx.columns=['excl','ew']
for col in ['excl','ew']:
    r_ = jx[col][jx.index>='2017-01-01']
    print('EXCL', col, 'OOS SR %.2f ann %.1f%%' % (full_stats(r_)['sr'], full_stats(r_)['ann']), '| FULL %.2f' % full_stats(jx[col])['sr'])

# GBM variant
sig2 = np.full((len(DT), n), np.nan)
for i in range(len(DT)):
    dt = DT[i]
    if dt < pd.Timestamp('2014-01-01'): continue
    tr = [j for j in range(i-1, -1, -1) if (dt - DT[j]).days > 42][24:]
    if i < 60: continue
    Xtr = Xt[tr].reshape(-1, Xt.shape[2]); ytr = Yt[tr].reshape(-1)
    m = np.isfinite(Xtr).all(1) & np.isfinite(ytr)
    if m.sum() < 500: continue
    model = GradientBoostingRegressor(n_estimators=60, max_depth=2, learning_rate=0.05)
    model.fit(Xtr[m], ytr[m])
    if np.isfinite(Xt[i]).all(): sig2[i] = model.predict(Xt[i])
S2 = pd.DataFrame(sig2, index=DT, columns=R.columns)
W2 = pd.DataFrame(0.0, index=DT, columns=R.columns)
for i in range(len(DT)):
    s_ = S2.iloc[i]
    if s_.notna().sum() >= 5:
        W2.loc[DT[i], s_.nlargest(5).index] = 0.2
W2d = W2.reindex(d).ffill().fillna(0).shift(1)
gross2 = (W2d*R).sum(axis=1); to2 = W2d.diff().abs().sum(axis=1).fillna(0)+W2d.abs().sum(axis=1)
net2 = apply_cost(gross2, to2); net2v = net2.fillna(0)*L.vt_scale(net2.fillna(0)).shift(1)
j2 = pd.concat([net2v, net_ew_v], axis=1).dropna(); j2.columns=['gbm','ew']
for col in ['gbm','ew']:
    r_ = j2[col][j2.index>='2017-01-01']
    print('GBM', col, 'OOS SR %.2f ann %.1f%%' % (full_stats(r_)['sr'], full_stats(r_)['ann']), '| FULL %.2f' % full_stats(j2[col])['sr'])
print('corr gbm vs blend', round(L.corr_blend(j2['gbm']),3))
