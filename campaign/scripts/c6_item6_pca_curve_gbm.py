"""Item 6: GBM on curve shape — PCA of 10 DGS tenors, level/slope/curv changes + vix/credit -> DGS10 book (-8.5*dy)."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader'); sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
import c6_round2_lib as L
from campaign.harness.data import apply_cost
from campaign.agents.B2_highfreq.gates import full_stats
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.decomposition import PCA

TEN = ['DGS1MO','DGS3MO','DGS6MO','DGS1','DGS2','DGS5','DGS7','DGS10','DGS20','DGS30']
Y = L.load_tenors(TEN)
Y = Y.interpolate(limit=3).dropna()
print('curve', Y.shape, str(Y.index[0].date()), str(Y.index[-1].date()))
vix = L.robust_fred('vix'); cred = (L.robust_fred('baa') - L.robust_fred('aaa'))


# PCA on levels (standardized); expanding refit yearly to stay purged
d = Y.index[252:]
Y = Y.loc[d]
Yc = Y - Y.expanding(min_periods=252).mean()   # demean vs expanding mean (no lookahead)
pcs = pd.DataFrame(0.0, index=d, columns=['PC1','PC2','PC3'])
# rolling PCA refit every 63d
pca_model = None; last = -1
for i in range(len(d)):
    if i - last >= 63 or pca_model is None:
        if i >= 252:
            Yfit = Yc.iloc[:i+1].dropna()
            if len(Yfit) < 10:
                pca_model = None
            else:
                pca_model = PCA(n_components=3).fit(Yfit.values)
            last = i
    if pca_model is not None:
        pcs.iloc[i, :] = pca_model.transform(Yc.iloc[[i]].values)[0]
feats = {}
for c in ['PC1','PC2','PC3']:
    feats[f'{c}_d1'] = pcs[c].diff(); feats[f'{c}_d5'] = pcs[c].diff(5); feats[f'{c}_d21'] = pcs[c].diff(21)
    feats[f'{c}_z'] = (pcs[c] - pcs[c].rolling(252).mean())/pcs[c].rolling(252).std()
feats['level'] = Y['DGS10'] - Y['DGS10'].rolling(252).mean()
vixd = vix.reindex(d).ffill(); credd = cred.reindex(d).ffill()
feats['vix_z'] = (vixd - vixd.rolling(63).mean())/vixd.rolling(63).std()
feats['cred_d21'] = credd.diff(21)
dfii = L.robust_fred('DFII10').reindex(d).ffill()
feats['be_d21'] = (Y['DGS10'] - dfii).diff(21)
X = pd.DataFrame(feats)
dy10 = Y['DGS10'].diff()
tgt = dy10.shift(-5)  # next-5d 10y yield change (pct pt)
cal = X.dropna().index.intersection(tgt.dropna().index)
X, tgt = X.loc[cal], tgt.loc[cal]
print('X', X.shape)

# walk-forward GBM refit monthly, expanding min 504d, purge 6d
dates = X.index; sig = pd.Series(0.0, index=dates); model=None; last_fit=-1
for i in range(len(dates)):
    if i - last_fit >= 21 or model is None:
        tr_end = i - 6
        if tr_end >= 504:
            ytr = tgt.iloc[:tr_end+1]; m = ytr.notna()
            model = GradientBoostingRegressor(n_estimators=80, max_depth=2, learning_rate=0.05)
            model.fit(X.iloc[:tr_end+1][m], ytr[m]); last_fit = i
    if model is not None:
        sig.iloc[i] = model.predict(X.iloc[[i]])[0]

# book: long duration when yield predicted to FALL: ret = -8.5 * dy10 (next 5d spread over 5 days, 1/5 per day)
pos = -np.sign(sig).shift(1)  # T+1
# 5d holding: scale by 1/5 each day to spread the trade
gross = (pos * (-8.5 * dy10.reindex(dates).fillna(0) / 5.0))
to = pos.diff().abs().fillna(0) + pos.abs()*0.0  # one-side turnover (positions from +/-1, spread over 5 days at 1/5 notional)
to = to/5.0
net = apply_cost(gross, to)
sc = L.vt_scale(net.fillna(0)).shift(1)
netv = (net.fillna(0)*sc)
netv = netv[sig.shift(1).reindex(netv.index).notna()]
res = L.gates_report(netv, 'item6_pca_gbm_dy10')
isr, oos = L.oos_is_split(netv); res['oos_is'] = f'OOS {oos:.2f}/IS {isr:.2f}'
L.pr(res)
imp = pd.Series(model.feature_importances_, index=X.columns).nlargest(8).round(3)
print('feature importances:', imp.to_dict())

# baseline: PCA-PC3 (curvature) fade — C2's fly worked as z-reversion; check PC-based simple rules
for c,w in [('PC3',63),('PC2',63),('PC1',252)]:
    z = (pcs[c]-pcs[c].rolling(w).mean())/pcs[c].rolling(w).std()
    p = (-np.sign(z)).shift(1)
    g = p*(-8.5*dy10.reindex(pcs.index).fillna(0)/5.0)
    n2 = apply_cost(g, p.diff().abs().fillna(0)/5.0)
    n2 = (n2.fillna(0)*L.vt_scale(n2.fillna(0)).shift(1)).dropna()
    r2 = L.gates_report(n2, f'base_{c}_fade{w}'); L.pr(r2)
