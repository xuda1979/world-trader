import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from lib6 import closes, stats, halves_sr, vol_target
from harness_shim import ff_factors, ff_mom

px = closes()
rets = px.pct_change(fill_method=None).clip(-0.5, 0.5)
hist = px.notna().cumsum()
univ = px.notna() & (hist >= 120) & rets.notna()

ff = ff_factors(); mom = ff_mom()
fac = ff.join(mom, how="outer").sort_index()
fac.columns = [c.strip() for c in fac.columns]
fac = fac[["Mkt-RF", "SMB", "HML", "Mom"]].fillna(0.0)

def resid_momentum(win=252):
    """12m momentum orthogonalized to FF3+Mom via TRAILING 252d rolling regression."""
    mom12 = px.pct_change(252, fill_method=None)  # 12m return, skip nothing (Blitz uses 12m)
    # trailing betas: rolling cov with each factor
    f = fac.reindex(px.index).fillna(0.0)
    rf = f["Mkt-RF"]; smb = f["SMB"]; hml = f["HML"]; umd = f["Mom"]
    def beta_of(y, x, win=252, mo=126):
        m_y = y.rolling(win, min_periods=mo).mean()
        m_x = x.rolling(win, min_periods=mo).mean()
        m_yx = (y.mul(x, axis=0)).rolling(win, min_periods=mo).mean()
        return (m_yx - m_y.mul(m_x, axis=0)).div(x.rolling(win, min_periods=mo).var() + 1e-12, axis=0)
    mkt = rets.mean(axis=1)
    b1 = beta_of(rets, mkt); b2 = beta_of(rets, smb); b3 = beta_of(rets, hml); b4 = beta_of(rets, umd)
    m_r = rets.rolling(win, min_periods=126).mean()
    resid_ret = rets.sub(b1.mul(mkt, axis=0)).sub(b2.mul(smb, axis=0)).sub(b3.mul(hml, axis=0)).sub(b4.mul(umd, axis=0))
    resid_mom = resid_ret.rolling(252, min_periods=200).sum()  # 12m of residual returns
    return mom12, resid_mom, b1

def weights_ls(score, ok, frac=1/3, cadence=21, inv_vol=None):
    r = score.where(ok)
    q_lo = r.quantile(frac, axis=1); q_hi = r.quantile(1-frac, axis=1)
    L = r.le(q_lo, axis=0) & ok; S = r.ge(q_hi, axis=0) & ok
    if inv_vol is None:
        lw = L.div(L.sum(axis=1).clip(lower=1), axis=0)
        sw = S.div(S.sum(axis=1).clip(lower=1), axis=0)
    else:
        inv = 1.0 / inv_vol.where(ok)
        lsum = (L*inv).sum(axis=1).clip(lower=1e-9); ssum = (S*inv).sum(axis=1).clip(lower=1e-9)
        lw = (L*inv).div(lsum, axis=0); sw = (S*inv).div(ssum, axis=0)
    w = 0.5*lw - 0.5*sw
    return carry(w, cadence)

def weights_long(score, ok, frac=1/3, cadence=21, inv_vol=None):
    r = score.where(ok)
    q_hi = r.quantile(1-frac, axis=1)
    L = r.ge(q_hi, axis=0) & ok
    if inv_vol is None:
        w = L.div(L.sum(axis=1).clip(lower=1), axis=0)
    else:
        inv = 1.0 / inv_vol.where(ok)
        w = (L*inv).div((L*inv).sum(axis=1).clip(lower=1e-9), axis=0)
    return carry(w, cadence)

def carry(w, cadence):
    arr = np.array(w.values); cur = arr[0]
    for i in range(len(arr)):
        if (np.arange(len(arr)) % cadence == 0)[i]: cur = arr[i]
        else: arr[i] = cur
    return pd.DataFrame(arr, index=w.index, columns=w.columns)

def backtest(W, tag, start="2007-01-01", vt=0.10, verbose=True):
    gross = (W.shift(1) * rets).sum(axis=1)[start:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[start:].fillna(0.0)
    net = gross - turn * 6 / 1e4
    if vt:
        net, lev = vol_target(net, vt)
    s = stats(net.dropna()); h = halves_sr(net.dropna())
    yr = net.groupby(net.index.year).apply(lambda x: (1+x).prod()-1)
    if verbose:
        neg = {int(k): round(v*100,1) for k,v in yr.items() if v < 0}
        print(f"{tag}: SR={s['sr']:.2f} ann={s['ann_ret']:.1f}% vol={s['ann_vol']:.1f}% H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']} worst={s['worst_year']:.1f}% turn/d={turn.mean()*100:.1f}% neg={neg}")
    return net
