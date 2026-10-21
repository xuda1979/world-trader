"""C6 Idea 1: Curve-ML. Walk-forward Ridge on treasury-curve features -> next-day DGS10 change
-> position in 10y bond book (proxy ret = -8.5*dy). T+1, 6bps/side, trailing vol target 10%.
Train purged: expanding window, refit quarterly, min 504d, 5d purge gap. OOS=every predicted day.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval
from sklearn.linear_model import Ridge

FRED = '/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
def load(name):
    df = pd.read_csv(f'{FRED}/{name}.csv', index_col=0, parse_dates=True)
    v = df.iloc[:, 0].astype(float)
    v = v[v > 0] if name != 'vix' else v[v > 0]
    return v[~v.index.duplicated(keep='last')]

y2, y5, y10 = load('DGS2'), load('DGS5'), load('DGS10')
be, baa, vix = load('T10YIE'), load('baa'), load('vix')
real = load('DFII10')
df = pd.DataFrame({'y2': y2, 'y5': y5, 'y10': y10, 'be': be, 'baa': baa, 'vix': vix, 'real': real}).sort_index()
df = df.loc['2003-01-01':]
df = df.ffill(limit=5).dropna()
print('panel', df.index.min().date(), df.index.max().date(), len(df))

# features (all trailing, computed at t)
f = pd.DataFrame(index=df.index)
for c in ['y2', 'y5', 'y10']:
    f[f'{c}_d1'] = df[c].diff()
    f[f'{c}_d5'] = df[c].diff(5)
    f[f'{c}_d21'] = df[c].diff(21)
f['slope'] = df['y10'] - df['y2']
f['slope_z'] = (f['slope'] - f['slope'].rolling(252).mean()) / f['slope'].rolling(252).std()
f['slope_d5'] = f['slope'].diff(5)
f['be_z'] = (df['be'] - df['be'].rolling(252).mean()) / df['be'].rolling(252).std()
f['be_d5'] = df['be'].diff(5)
f['cs'] = df['baa'] - df['y10']
f['cs_z'] = (f['cs'] - f['cs'].rolling(252).mean()) / f['cs'].rolling(252).std()
f['cs_d5'] = f['cs'].diff(5)
f['vix_z'] = (df['vix'] - df['vix'].rolling(252).mean()) / df['vix'].rolling(252).std()
f['y10_z'] = (df['y10'] - df['y10'].rolling(252).mean()) / df['y10'].rolling(252).std()
f['real_z'] = (df['real'] - df['real'].rolling(252).mean()) / df['real'].rolling(252).std()
f['curve_butter'] = df['y10'] - 2 * df['y5'] + df['y2']
f['curve_butter_z'] = (f['curve_butter'] - f['curve_butter'].rolling(252).mean()) / f['curve_butter'].rolling(252).std()

dy = df['y10'].diff()
dyv = dy.rolling(252).std()
target = dy.shift(-1)          # dy_{t+1} — label uses t+1 info, position formed at t, return realized t+1
X = f.replace([np.inf, -np.inf], np.nan)
data = X.copy(); data['target'] = target; data['dyv'] = dyv.shift(0)
data = data.dropna()
data = data[data.index >= '2006-01-01']
print('model rows', len(data), data.index.min().date(), data.index.max().date())

feats = [c for c in X.columns]
dates = data.index
# walk-forward: refit quarterly, expanding train, 5-day purge
qends = pd.date_range('2007-01-01', '2026-09-01', freq='QE')
preds = pd.Series(dtype=float)
alphas = [10.0, 100.0, 1000.0]
for qe in qends:
    te_mask = dates <= (qe - pd.Timedelta(days=5))
    tr_mask = dates < (qe - pd.Timedelta(days=7))   # purge: last train label at most 7d before first test
    tr_idx = np.where(tr_mask)[0]
    te_idx = np.where((dates > qe) & (dates <= qe + pd.offsets.QuarterEnd(1)))[0]
    if len(tr_idx) < 504 or len(te_idx) == 0:
        continue
    # alpha by trailing validation (last 252 rows of train)
    a_tr = tr_idx[-252:] if len(tr_idx) > 756 else tr_idx[:252]
    a_fit = tr_idx[:-252] if len(tr_idx) > 756 else tr_idx
    best_a, best_v = alphas[0], 1e9
    for a in alphas:
        m = Ridge(alpha=a).fit(data[feats].iloc[a_fit], data['target'].iloc[a_fit])
        v = ((m.predict(data[feats].iloc[a_tr]) - data['target'].iloc[a_tr]) ** 2).mean()
        if v < best_v: best_v, best_a = v, a
    m = Ridge(alpha=best_a).fit(data[feats].iloc[tr_idx], data['target'].iloc[tr_idx])
    for i in te_idx:
        preds[dates[i]] = m.predict(data[feats].iloc[[i]])[0]

print('preds', len(preds), preds.index.min().date(), preds.index.max().date())
# position at t: negative predicted dy (yield down -> bond up), scaled by trailing dy vol, cap 2
w = -preds / dyv.reindex(preds.index)
w = w.clip(-2, 2)
proxy = -8.5 * dy.reindex(w.index)          # bond book daily return at t+1 realized from position formed t
# T+1: position w_t earns proxy_{t+1}
pos = w.shift(0)
gross = (pos * proxy.shift(-1)).dropna()
turn = pos.diff().abs().reindex(gross.index).fillna(pos.iloc[0])
net = gross - 6e-4 * turn
net = net[net.index >= '2008-01-01']
net_s, scale = vol_target(net, 0.10)
print('scale mean', round(scale.mean(), 2), 'max', round(scale.max(), 2))
print('FULL', {k: (round(v, 2) if isinstance(v, float) else v) for k, v in full_stats(net_s).items() if k != 'yearly'})
h1, h2 = halves_sr(net_s); print('halves', round(h1, 2), round(h2, 2))
pv, real_sr = scramble_pval(net_s); print('scramble p', pv, 'sr', round(real_sr, 2))
oos = net_s[net_s.index >= '2017-01-01']
print('OOS 2017+', {k: (round(v, 2) if isinstance(v, float) else v) for k, v in full_stats(oos).items() if k != 'yearly'})
# corr vs blend
b = pd.read_csv('/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv', index_col=0, parse_dates=True)['ret']
j = pd.concat([net_s, b], axis=1, join='inner').dropna()
print('corr blend', round(j.corr().iloc[0, 1], 3), 'overlap', len(j))
net_s.to_frame('ret').to_csv('/tmp/c6_curve_ml.csv')
print('yearly', full_stats(net_s)['yearly'])
