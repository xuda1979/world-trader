"""A6 r2 mission 1e: VT leverage cap + FAST (21d) vol scaling to blunt Jan-2022 pre-exit."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import stats, halves_sr, vol_target
from idea234_engine import resid_momentum, weights_long, rets, px

FRED = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
vix = pd.read_csv(f"{FRED}/vix.csv", parse_dates=["date"], index_col="date")["value"]
vix = vix[~vix.index.duplicated(keep="last")].sort_index().reindex(px.index).ffill()

_, resid_mom, _ = resid_momentum()
ok = rets.notna() & (px.notna().cumsum() >= 120)
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
mkt = px.mean(axis=1)
mkt_ret = rets.where(px.notna()).mean(axis=1)

def gate_dual(ma_len=150, confirm=10, dd_entry=None, dd_thresh=-0.15):
    ma_s = mkt.rolling(ma_len, min_periods=ma_len//2).mean()
    above = (mkt > ma_s).values; below = (mkt < ma_s*0.98).values
    dd = (mkt / mkt.rolling(252, min_periods=126).max() - 1.0)
    n = len(mkt); state = np.zeros(n); s = 0; cnt = 0
    for i in range(n):
        if np.isnan(ma_s.iloc[i]): continue
        need = dd_entry if (dd_entry is not None and not np.isnan(dd.iloc[i]) and dd.iloc[i] < dd_thresh) else confirm
        if s == 1 and below[i]: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if above[i] else 0
            if cnt >= need: s = 1
        state[i] = s
    return pd.Series(state, index=mkt.index)

def vt_cap(r, target=0.10, min_obs=60, cap=1.5):
    sd = r.expanding(min_obs).std().shift(1)
    lev = (target/np.sqrt(252)/sd).clip(0, cap).fillna(0.0)
    return r*lev

def report(net, tag):
    s = stats(net); h = halves_sr(net)
    yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = {int(k): round(v*100,1) for k,v in yr.items() if v < 0}
    okg = s['sr']>=0.6 and h['H1']>=0.3 and h['H2']>=0.3 and s['neg_years']<=2 and s['worst_year']>-5
    print(f"{tag:52s} SR={s['sr']:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}{neg} {'<<== ALL d+halves' if okg else ''}")

for gate_tag, g in [("noDDentry", gate_dual(150,10)), ("ddEntry20-15", gate_dual(150,10,20,-0.15))]:
    Wg = W.mul(g, axis=0)
    gross = (Wg.shift(1) * rets).sum(axis=1)["2007-01-01":]
    turn = (Wg.shift(1) - Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    raw = (gross - turn*6/1e4).dropna()
    report(raw, f"{gate_tag} RAW")
    for cap in [1.0, 1.25, 1.5]:
        report(vt_cap(raw, cap=cap), f"{gate_tag} VTcap{cap}")
    # fast VIX scaling on top (no VT)
    for w, cap in [(21, 0.18), (21, 0.22), (42, 0.20), (63, 0.20)]:
        mvol = mkt_ret.rolling(w, min_periods=max(10,w//2)).std()*np.sqrt(252)
        lev = (cap/mvol).clip(0, 1.0)
        report((raw*lev.shift(1)).dropna(), f"{gate_tag} volscale{w}d cap{cap} (noVT)")
    # VIX spike ladder: vix>25 -> 0.6x, vix>30 -> 0.35x (trailing, no latch)
    ladder = pd.Series(1.0, index=px.index)
    ladder[vix > 25] = 0.6; ladder[vix > 30] = 0.35; ladder[vix > 35] = 0.25
    report((raw*ladder.shift(1)).dropna(), f"{gate_tag} VIXladder (noVT)")
    report(vt_cap((raw*ladder.shift(1)).dropna(), cap=1.5), f"{gate_tag} VIXladder+VTcap1.5")
