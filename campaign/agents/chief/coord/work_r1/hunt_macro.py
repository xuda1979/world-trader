#!/usr/bin/env python3
"""HUNT_MACRO2 round-1: (a) credit-cycle, (b) activity-nowcast composite, (c) real-rate
duration sleeve, (d) liquidity/fed-balance-sheet factor. T+1 with release-lag shifts."""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/work_r1')
from hunt_lib import *
import numpy as np, pandas as pd

FR = f"{ROOT}/tools/quant/data/more_fred"
ND = f"{ROOT}/tools/quant/data/newdata"

def fred(sid, d=FR):
    df = pd.read_csv(f"{d}/{sid}.csv")
    dcol, vcol = df.columns[0], df.columns[1]
    s = pd.Series(df[vcol].astype(float).values,
                  index=pd.to_datetime(df[dcol])).dropna()
    s.index.name = 'date'
    return s.sort_index()

def daily_ffill(s):
    return s.reindex(pd.bdate_range(s.index.min(), s.index.max())).ffill()

def eval_gate(sig, r, name, extra_lag=0):
    """signal at t (with release lag already in sig), trade t+1."""
    if extra_lag:
        sig = sig.shift(extra_lag)
    net, st = evaluate(sig, r)
    yok, yrs = yearly_ok(net)
    print(f"{name:<28} n={st['n']:>5} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} "
          f"h=({st.get('h1')},{st.get('h2')}) corr={champ_corr(net):.3f} yearly_ok={yok}")
    return net, st

# ---------- (a) CREDIT-CYCLE: BAA-AAA + HY OAS ----------
baa, aaa = fred('BAA'), fred('DAAA')
spread = daily_ffill(baa - aaa)
hyoas = fred('BAMLH0A0HYM2', ND)
hyoas_d = daily_ffill(hyoas)
# credit risk-on: spread compressed (below 6m ago) => risk-on
cred = (spread < spread.shift(126)).astype(float) * 2 - 1
cred_hy = (hyoas_d < hyoas_d.shift(126)).astype(float) * 2 - 1

print("== (a) credit-cycle factor, applied to equity (SPY-proxy QQQ) and HY-vs-IG ==")
qqq = load_close(f"{ROOT}/tools/quant/data/more_etf/QQQ.csv"); qqq_r = qqq.pct_change()
for nm, s in [('BAA-AAA 126d', cred), ('HYOAS 126d', cred_hy), ('BAA-AAA+HYOAS avg', (cred.reindex(cred_hy.index).ffill()+cred_hy)/2)]:
    eval_gate(s.shift(21), qqq_r, f"{nm} -> longQQQ")   # 21d macro release lag

lqd = load_close(f"{ROOT}/tools/quant/data/more_etf/LQD.csv"); hyg = load_close(f"{ROOT}/tools/quant/data/more_etf/JNK.csv")
lqd_r, hyg_r = lqd.pct_change(), hyg.pct_change()
credit_book = pd.DataFrame({'lo': cred_hy, 'hi': -cred_hy})
# L/S: long HY when spread compressing, long IG when widening
net_ls = evaluate(pd.concat([cred_hy, -cred_hy], axis=1), pd.concat([hyg_r, lqd_r], axis=1), vt=False)[0] if False else None
# simpler: long whichever of HY/IG the signal favors, 1 unit gross
sigdir = cred_hy
w = pd.DataFrame({'JNK': sigdir.clip(lower=0)*1.0 + sigdir.clip(upper=0)*0.0,
                  'LQD': (-sigdir).clip(lower=0)*1.0})
w = w.div(w.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
net = evaluate(pd.Series(0.0, index=w.index), hyg_r)[0]  # placeholder
# manual honest book eval:
rets_panel = pd.concat([hyg_r.rename('JNK'), lqd_r.rename('LQD')], axis=1)
ww = w.shift(1).fillna(0.0)
rg = (ww * rets_panel.fillna(0.0)).sum(axis=1)
sc = vt_scale(rg); ww2 = ww.mul(sc, axis=0)
prev = ww2.shift(1); prev.iloc[0] = 0.0
to = (ww2 - prev).abs().sum(axis=1)
net = (rg - to*COST - np.maximum(ww2.abs().sum(axis=1)-1,0)*MARGIN/ANN).dropna()
st = stat(net); yok, _ = yearly_ok(net)
print(f"{'HY/IG switch on HYOAS':<28} n={st['n']:>5} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} corr={champ_corr(net):.3f} yearly_ok={yok}")

# ---------- (b) ACTIVITY NOWCAST: INDPRO + CFNAIMA3 + RRSFS + PAYEMS z-average ----------
print("\n== (b) activity-nowcast composite -> long QQQ / long DBC ==")
comps = {}
for sid, path in [('INDPRO', FR), ('CFNAIMA3', ND), ('RRSFS', FR), ('PAYEMS', ND)]:
    try:
        s = fred(sid, path).pct_change(12)
        s = daily_ffill(s)
        z = (s - s.rolling(756).mean()) / s.rolling(756).std()
        comps[sid] = z
    except Exception as e:
        print(f"  {sid}: SKIP {repr(e)[:60]}")
zc = pd.DataFrame(comps).mean(axis=1)
act = (zc > 0).astype(float) * 2 - 1
eval_gate(act.shift(42), qqq_r, "nowcast -> longQQQ (42d lag)")
dbc = load_close(f"{ROOT}/tools/quant/data/more_etf/DBC.csv"); dbc_r = dbc.pct_change()
eval_gate(act.shift(42), dbc_r, "nowcast -> longDBC")

# ---------- (c) REAL-RATE duration: 10y TIPS yield trend -> long/short TLT ----------
print("\n== (c) real-rate duration sleeve ==")
dfii = fred('DFII10')
dfii_d = daily_ffill(dfii)
rr_tr = (dfii_d - dfii_d.shift(126)).dropna()
sig = pd.Series(np.where(rr_tr > 0, -1.0, 1.0), index=rr_tr.index)  # real yields falling -> long duration
tlt = load_close(f"{ROOT}/tools/quant/data/more_etf/TLT.csv"); tlt_r = tlt.pct_change()
eval_gate(sig, tlt_r, "realrate 126d -> TLT L/S")
ief = load_close(f"{ROOT}/tools/quant/data/more_etf/IEF.csv")
eval_gate(sig, ief.pct_change(), "realrate 126d -> IEF L/S")
# breakeven trend (T10YIE) as TIPS sleeve
t10 = daily_ffill(fred('T10YIE'))
be_tr = t10 - t10.shift(63)
sigbe = pd.Series(np.where(be_tr > 0, 1.0, -1.0), index=be_tr.index)
tip = load_close(f"{ROOT}/tools/quant/data/more_etf/TIP.csv")
eval_gate(sigbe, tip.pct_change(), "breakeven 63d -> TIP L/S")

# ---------- (d) LIQUIDITY: WALCL + RRPONTSYD ----------
print("\n== (d) liquidity factor ==")
walcl = fred('WALCL'); rrp = fred('RRPONTSYD')
liq = daily_ffill(walcl.pct_change(52)).dropna() - daily_ffill(rrp.pct_change(52)).reindex(daily_ffill(walcl).index).ffill().dropna()
liq = (liq - liq.rolling(252).mean()) / liq.rolling(252).std()
sigl = pd.Series(np.where(liq > 0, 1.0, -1.0), index=liq.index)
eval_gate(sigl.shift(5), qqq_r, "WALCL-RRP -> longQQQ")
eval_gate(sigl.shift(5), dbc_r, "WALCL-RRP -> longDBC")
