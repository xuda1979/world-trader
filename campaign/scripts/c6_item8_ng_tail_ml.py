"""Item 8: ML tail-gate of C5 natgas weekday premium. HistGB predicts next-day |strategy ret| from
trailing features; position scaled by 1/(1+k*pred) BEFORE the gate-g vol target. Goal: cut MaxDD << 29.5% keeping SR>=1."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader'); sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
import c6_round2_lib as L
from campaign.harness.data import apply_cost
from sklearn.ensemble import HistGradientBoostingRegressor

# rebuild C5 engine from FRED DHHNGSP (per C5_weekend_prem_ng.py spec)
gas = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv')
gas[gas.columns[0]] = pd.to_datetime(gas[gas.columns[0]])
gas = gas.set_index(gas.columns[0]).iloc[:,0].sort_index()
gas = gas[~gas.index.duplicated(keep='last')].dropna()
gas = gas[~gas.index.duplicated(keep='last')]
lr = np.log(gas).diff()
k=2.5
sig90 = lr.rolling(90).std()
skip = (lr.abs() > k*sig90.shift(1))
def wkpos(idx):
    wd = idx.dayofweek
    p = pd.Series(0.0, index=idx)
    p[wd==4] = 1.0   # long Fri->next print
    p[wd==2] = -0.5  # short Wed
    p[wd==3] = -0.5  # short Thu
    return p
pos0 = wkpos(gas.index)
pos0[skip] = 0.0
gross = (pos0.shift(1)*lr)  # T+1
to = pos0.diff().abs().fillna(0)
net = apply_cost(gross, to)
sc = L.vt_scale(net.fillna(0)).shift(1)
base = (net.fillna(0)*sc).dropna()
r0 = L.gates_report(base, 'c5_repro'); L.pr(r0)  # sanity vs C5 SR 1.74

# features (all trailing): dow one-hot, |lr| vol regimes, month, sleeve trailing stats
d = net.fillna(0).index
F = pd.DataFrame(index=d)
for w_ in [5,10,21,63]: F[f'rv{w_}'] = lr.rolling(w_).std()
F['absret10'] = net.abs().rolling(10).mean()
F['lr_z'] = (gas - gas.rolling(252).mean())/gas.rolling(252).std()
F['month'] = d.month.values/12.0
wd = pd.get_dummies(d.dayofweek, prefix='dow').set_index(d)
F = pd.concat([F, wd], axis=1)
y = net.abs().shift(-1)  # next-day |strategy net ret| (pre-vt)
m = F.notna().all(1) & y.notna()
gate = pd.Series(1.0, index=d)
Xf, yf = F[m], y[m]
# walk-forward refit quarterly
i0 = np.where(m.values)[0]
fit_every = 63
model = None; last_i = -10**9
for i in range(len(d)):
    if m.values[i] and i >= 504 and (i - last_i) >= fit_every:
        tr = (F.iloc[:i-2].notna().all(1)) & (y.shift(2).notna().values[:i]) if False else None
        Xtr = F.iloc[:i-2][F.iloc[:i-2].notna().all(1).values]
        ytr = y.shift(0).iloc[:i-2].reindex(Xtr.index)
        ytr = net.abs().reindex(Xtr.index)  # current-day |ret| as target proxy? need next-day; keep y but purge:
        yy = y.reindex(Xtr.index)
        mm = yy.notna() & Xtr.notna().all(1)
        model = HistGradientBoostingRegressor(max_depth=2, max_iter=80, learning_rate=0.05)
        model.fit(Xtr[mm], yy[mm]); last_i = i
    if model is not None and m.values[i]:
        gate.iloc[i] = 1.0/(1.0 + model.predict(F.iloc[[i]])[0]*50)  # k=50 tuning
gsc = gate.shift(1).fillna(1.0)  # T+1
netg = net*gsc
sc2 = L.vt_scale(netg.fillna(0)).shift(1)
out = (netg.fillna(0)*sc2).dropna()
r1 = L.gates_report(out, 'c5_ml_tailgate'); L.pr(r1)
print('gate mean %.3f min %.3f frac<0.5 %.3f' % (gsc.mean(), gsc.min(), (gsc<0.5).mean()))
# simple vol-responsive alternative (construction control, not ML): scale by 1/(1+10*rv10) pre-vt
alt_gate = (1.0/(1.0+20*F['rv10'].shift(1))).fillna(1.0)
out2 = (net*alt_gate).fillna(0)
out2 = out2*L.vt_scale(out2).shift(1)
r2 = L.gates_report(out2.dropna(), 'c5_rv10_gate'); L.pr(r2)
