"""Item 7 (charter-linked rescue): ML regime-gating of KF small-value spread momentum (C1 near-miss SR 0.68).
Features (all trailing): credit z, vix z, slope z, UMD trailing stats, spread mom/vol -> choose w in {15,21,42}
or gate sign on/off. Walk-forward Ridge on spread fwd-21d ret. 2008+."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader'); sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
import c6_round2_lib as L
from campaign.harness.data import apply_cost
from campaign.agents.B2_highfreq.gates import full_stats

lines = open('/Users/daxu/software/world-trader/tools/quant/data/kenfrench/25_Portfolios_5x5_Daily.csv').read().splitlines()
hi = next(i for i,l in enumerate(lines) if 'Average Value Weighted Returns -- Daily' in l)
hdr = [h.strip() for h in lines[hi+1].split(',')][1:]
rows=[]
for l in lines[hi+2:]:
    if not l.split(',')[0].strip().isdigit(): break
    rows.append([float(x) if x.strip() else np.nan for x in l.split(',')])
P = pd.DataFrame(rows, columns=['date']+hdr).set_index('date')
P.index = pd.to_datetime(P.index, format='%Y%m%d')
P = (P.replace(-99.99, np.nan)/100).sort_index().loc['2004':]
print('25ff', P.shape, list(P.columns))
# small-value spread: SMALL HiBM - SMALL LoBM
sv = P['SMALL HiBM'] - P['SMALL LoBM']

# C1 baseline: w=21 sign timing, T+1
def run_sign(sv, w, gate=None):
    sig = np.sign(sv.rolling(w).sum())
    if gate is not None: sig = sig*gate
    pos = sig.shift(1)
    gross = pos*sv
    to = pos.diff().abs().fillna(0)
    net = apply_cost(gross, to)
    sc = L.vt_scale(net.fillna(0)).shift(1)
    return (net.fillna(0)*sc).dropna()

base = run_sign(sv, 21).loc['2008-09':]
r = L.gates_report(base, 'sv21_sign_base'); L.pr(r)

# regime features
vix = L.robust_fred('vix'); d2 = L.robust_fred('DGS2'); d10 = L.robust_fred('DGS10')
cred = (L.robust_fred('baa')-L.robust_fred('aaa'))
umd = L.ff_mom()['Mom'] if hasattr(L,'ff_mom') else None
import campaign.harness.data as H
umd = H.ff_mom()['Mom']
ff = H.ff_factors()
F = pd.DataFrame(index=sv.index)
def _z(s_, w):
    s_ = s_[~s_.index.duplicated(keep='last')].sort_index()
    return ((s_ - s_.rolling(w).mean())/s_.rolling(w).std()).reindex(sv.index).ffill()
F['vix_z'] = _z(vix, 63)
sl = d2-d10
sl = sl[~sl.index.duplicated(keep='last')].sort_index()
F['slope_z'] = ((sl - sl.rolling(252).mean())/sl.rolling(252).std()).reindex(sv.index).ffill()
def _rf(s_):
    return s_[~s_.index.duplicated(keep='last')].sort_index()
F['cred_z'] = ((_rf(cred) - _rf(cred).rolling(252).mean())/_rf(cred).rolling(252).std()).reindex(sv.index).ffill()
umd = umd[~umd.index.duplicated(keep='last')].sort_index()
F['umd_mom21'] = umd.rolling(21).sum().reindex(sv.index).ffill()
F['umd_vol21'] = umd.rolling(21).std().reindex(sv.index).ffill()
F['sv_mom21'] = sv.rolling(21).sum(); F['sv_vol21'] = sv.rolling(21).std()
ffm = ff['Mkt-RF'][~ff['Mkt-RF'].index.duplicated(keep='last')].sort_index()
F['mkt_mom21'] = ffm.rolling(21).sum().reindex(sv.index).ffill()
F = F.dropna()
print('F', F.shape)

# target: fwd-21d sv spread -> learn sign amplitude
fwd = sv.rolling(21).sum().shift(-21)
# walk-forward monthly Ridge: predict fwd; position = clip(pred / (vol21*sqrt(21)), -1, 1) T+1
dates = F.index; sig = pd.Series(0.0, index=dates); model=None; last_fit=-1
from sklearn.linear_model import Ridge
for i in range(len(dates)):
    if i < 504: continue
    if i - last_fit >= 21:
        tr_end = i - 22  # purge 22d > fwd horizon
        Xtr, ytr = F.iloc[:tr_end+1], fwd.reindex(dates[:tr_end+1])
        m = ytr.notna() & Xtr.notna().all(1)
        model = Ridge(alpha=100.0).fit(Xtr[m], ytr[m]); last_fit = i
    if model is not None:
        pred = model.predict(F.iloc[[i]])[0]
        svol = sv.rolling(21).std().iloc[i]*np.sqrt(21)
        sig.iloc[i] = np.clip(pred/(svol+1e-9), -1, 1) if svol>0 else 0
pos = sig.shift(1)
gross = pos*sv.reindex(dates).fillna(0)
to = pos.diff().abs().fillna(0)
net = apply_cost(gross, to)
netv = (net.fillna(0)*L.vt_scale(net.fillna(0)).shift(1)).dropna()
netv = netv.loc['2008-09':]
r2 = L.gates_report(netv, 'sv_ml_ridge'); isr,oos = L.oos_is_split(netv); r2['oos_is']=f'OOS {oos:.2f}/IS {isr:.2f}'; L.pr(r2)
imp = pd.Series(np.abs(model.coef_), index=F.columns).nlargest(5).round(4)
print('coefs:', imp.to_dict())

# regime gate variant: credit z percentile gate (C1 recommendation: credit/vol conditioning)
for col, thr_hi in [('cred_z', 0.5), ('vix_z', 0.5)]:
    q = F[col].rolling(756).rank(pct=True)
    gate = (q > thr_hi).astype(float).shift(1)
    g = run_sign(sv, 21, gate.reindex(sv.index).fillna(0)).loc['2008-09':]
    r3 = L.gates_report(g, f'sv21_gate_{col}>{thr_hi}'); L.pr(r3)
