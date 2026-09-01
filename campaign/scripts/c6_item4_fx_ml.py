"""Item 4: FX-cross-ML — DEX* daily panel + DTWEXBGS target -> dollar sign -> majors basket."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader'); sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
import c6_round2_lib as L
from campaign.harness.data import fred, apply_cost
from sklearn.ensemble import GradientBoostingClassifier

FREED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
s = L.robust_fred

# --- panel: pairs quoted foreign-per-USD (dollar up -> series up) = sign +1; USD-per-foreign = -1
DEX = dict(DEXUSEU=-1, DEXUSUK=-1, DEXJPUS=1, DEXCAUS=1, DEXMXUS=1, DEXKOUS=1,
           DEXNOUS=1, DEXINUS=1, DEXBZUS=1)
px = pd.DataFrame({k: s(k) for k in DEX}).sort_index()
r = np.log(px).diff()
dtw = s('DTWEXBGS'); vix = s('vix'); d2 = s('DGS2'); d10 = s('DGS10'); xau = s('xau')
dxy = s('dxy')

feats = {}
for k in DEX:
    rr = r[k]
    feats[f'{k}_r5'] = rr.rolling(5).sum(); feats[f'{k}_r21'] = rr.rolling(21).sum()
    feats[f'{k}_z63'] = (px[k] - px[k].rolling(63).mean())/px[k].rolling(63).std()
    feats[f'{k}_v21'] = rr.rolling(21).std()
ldtw = np.log(dtw)
feats['dtw_r5'] = ldtw.diff(5); feats['dtw_r21'] = ldtw.diff(21)
feats['dtw_z63'] = (dtw - dtw.rolling(63).mean())/dtw.rolling(63).std()
feats['dxy_z63'] = (dxy - dxy.rolling(63).mean())/dxy.rolling(63).std()
feats['vix_z'] = (vix - vix.rolling(63).mean())/vix.rolling(63).std()
feats['d2_d21'] = d2.diff(21); feats['sprd_d21'] = (d2-d10).diff(21); feats['xau_r21'] = np.log(xau).diff(21)
X = pd.DataFrame(feats).sort_index()
dollar_ret_1d = pd.concat([r[k]*DEX[k] for k in DEX], axis=1).mean(axis=1)  # +1 = dollar strong day (major legs)
# tradeable majors book from FRED DEX noon rates (data/fx files start 2019-04 only -> unusable pre-2019)
majors = pd.concat([(np.log(px[k]).diff()*DEX[k]).rename(k) for k in ['DEXUSEU','DEXUSUK','DEXJPUS','DEXCAUS']], axis=1).mean(axis=1)
majors.index = pd.to_datetime(majors.index)

# target: sign of next-5d DTWEXBGS
tgt = np.sign(ldtw.shift(-5) - ldtw)
# reindex everything to vix-common calendar
cal = X.dropna().index
X = X.loc[cal]; tgt = tgt.reindex(cal)
idx = tgt.dropna().index
X, tgt = X.loc[idx], tgt.loc[idx]
print('X', X.shape, 'class bal', tgt.value_counts(normalize=True).round(3).to_dict())

# walk-forward GBM, refit every 21d, expanding min 504d, purge 7d
dates = X.index; sig = pd.Series(0.0, index=dates); last_fit = -1; model=None
for i in range(len(dates)):
    t = dates[i]
    if i - last_fit >= 21 or model is None:
        tr_end = i - 8
        if tr_end >= 504:
            Xtr, ytr = X.iloc[:tr_end+1], tgt.iloc[:tr_end+1]
            m = ytr.notna(); model = GradientBoostingClassifier(n_estimators=80, max_depth=2, learning_rate=0.05)
            model.fit(Xtr[m], ytr[m]); last_fit = i
    if model is not None:
        sig.iloc[i] = model.predict_proba(X.iloc[[i]])[0,1] - 0.5
print('sig stats', sig[sig!=0].describe().round(3).to_dict())

# T+1 execution: position from sig at t applied to t+1 majors ret
pos = (sig.shift(1)).clip(-1,1)
gross = pos * majors.reindex(dates).fillna(0)
to = pos.diff().abs().fillna(0) + pos.abs()  # one-side turnover: initial + changes
net = apply_cost(gross, to)
sc = L.vt_scale(net.fillna(0)).shift(1).clip(upper=3.0)  # trailing expanding vt, shift to avoid lookahead
net_vt = (net.fillna(0) * sc).dropna()
net_vt = net_vt[sig.shift(1).reindex(net_vt.index).notna().values]  # only traded days
res = L.gates_report(net_vt, 'item4_dxy_gbm')
isr, oos = L.oos_is_split(net_vt); res['oos_is'] = f'{oos:.2f}/{isr:.2f}'
L.pr(res)
# baselines: dtw 5d momentum sign, dtw 21d
for w in [5,21]:
    b = np.sign(ldtw.diff(w))
    g2 = (b.shift(1)*majors.reindex(ldtw.index).fillna(0))
    n2 = apply_cost(g2, b.shift(1).diff().abs().fillna(0)+b.abs().shift(1))
    n2 = (n2*L.vt_scale(n2.fillna(0)).shift(1)).dropna(); n2 = n2[n2.index>='2008-09-01']
    rr2 = L.gates_report(n2, f'base_dtw_mom{w}'); L.pr(rr2)
