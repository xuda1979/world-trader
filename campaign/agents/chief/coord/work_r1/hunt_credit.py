#!/usr/bin/env python3
"""HUNT_CREDIT2 round-1: (a) HY/IG spread carry w/ BAA-AAA gate, (b) 2s10s curve carry
(DGS2/DGS10 via TLT/IEF/SHY basket), (c) breakeven trend TIPS sleeve, (d) credit-impulse gate."""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/work_r1')
from hunt_lib import *
import numpy as np, pandas as pd

FR = f"{ROOT}/tools/quant/data/more_fred"
ET = f"{ROOT}/tools/quant/data/more_etf"
def fred(sid):
    df = pd.read_csv(f"{FR}/{sid}.csv")
    s = pd.Series(df[df.columns[1]].astype(float).values, index=pd.to_datetime(df[df.columns[0]])).dropna()
    return s.sort_index()

def book_eval(w, rets_panel, vt=True):
    w = w.shift(1).fillna(0.0)
    rg = (w * rets_panel.fillna(0.0)).sum(axis=1)
    if vt:
        sc = vt_scale(rg); w = w.mul(sc, axis=0)
    prev = w.shift(1); prev.iloc[0] = 0.0
    to = (w - prev).abs().sum(axis=1)
    short = (-w.clip(upper=0.0)).sum(axis=1)
    gross = w.abs().sum(axis=1)
    net = (rg - to * COST - short * BORROW/ANN - np.maximum(gross-1,0)*MARGIN/ANN).dropna()
    return net

jnk = load_close(f"{ET}/JNK.csv"); lqd = load_close(f"{ET}/LQD.csv")
jnk_r, lqd_r = jnk.pct_change(), lqd.pct_change()
panel = pd.concat([jnk_r.rename('JNK'), lqd_r.rename('LQD')], axis=1, sort=True)

print("== (a) HY-vs-IG carry: always-in L/S sized by BAA-AAA stability ==")
baa, aaa = fred('BAA'), fred('DAAA')
sp = (baa - aaa)
sp_d = sp.reindex(panel.index, method='ffill')
chg63 = sp_d - sp_d.shift(63)
# compressing spread (chg<0) => risk-on => overweight HY vs IG; widening => IG over HY
for thr in [0.0, 0.1, 0.25]:
    wgt = pd.Series(np.where(chg63 < -thr, 0.8, np.where(chg63 > thr, -0.8, 0.0)), index=panel.index)
    w = pd.DataFrame({'JNK': wgt, 'LQD': -wgt})
    net = book_eval(w, panel)
    st = stat(net); yok, _ = yearly_ok(net)
    print(f"hy-ig thr={thr} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} mdd={st.get('mdd')} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')}) corr={champ_corr(net):.3f} yearly_ok={yok}")

print("\n== (b) 2s10s curve: steepener/flattener via SHY/TLT (2y~SHY, 10y~IEF/TLT) ==")
t10y2y = fred('T10Y2Y')
shy = load_close(f"{ET}/SHY.csv"); tlt = load_close(f"{ET}/TLT.csv"); ief = load_close(f"{ET}/IEF.csv")
shy_r, tlt_r, ief_r = shy.pct_change(), tlt.pct_change(), ief.pct_change()
pan2 = pd.concat([shy_r.rename('SHY'), tlt_r.rename('TLT'), ief_r.rename('IEF')], axis=1, sort=True)
curve = t10y2y.reindex(pan2.index, method='ffill')
chg = curve - curve.shift(21)
# 2s10s steepening => long TLT (long end falls less)... standard: steepener = long short-end + short long-end
for horizon, lag in [(21,1),(63,1)]:
    chg = curve - curve.shift(horizon)
    sig_st = pd.Series(np.where(chg > 0, 1.0, -1.0), index=pan2.index)   # steepening: long 2y short 10y
    w = pd.DataFrame({'SHY': sig_st * 0.5, 'TLT': -sig_st * 0.5})
    net = book_eval(w, pan2)
    st = stat(net); yok, _ = yearly_ok(net)
    print(f"curve2s10s h={horizon} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')}) corr={champ_corr(net):.3f} yearly_ok={yok}")

print("\n== (c) breakeven trend: T10YIE 63d trend -> TIP long/short vs SHY ==")
t10 = fred('T10YIE').reindex(pan2.index, method='ffill')
bet = t10 - t10.shift(63)
sig = pd.Series(np.where(bet > 0, 1.0, -1.0), index=pan2.index)
tip = load_close(f"{ET}/TIP.csv"); tip_r = tip.pct_change()
pan3 = pd.concat([tip_r.rename('TIP'), shy_r.rename('SHY')], axis=1, sort=True)
w = pd.DataFrame({'TIP': sig * 0.5, 'SHY': -sig * 0.5})
net = book_eval(w, pan3)
st = stat(net); yok, _ = yearly_ok(net)
print(f"be-trend TIP/SHY SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')}) corr={champ_corr(net):.3f} yearly_ok={yok}")
# plain TIP L/S
netp = book_eval(pd.DataFrame({'TIP': sig}), pd.concat([tip_r.rename('TIP')], axis=1))
stp = stat(netp)
print(f"be-trend TIP L/S SR={stp['sr']:>6.3f} ann={stp['ann']:>8.4f} negyr={stp.get('neg_years')} corr={champ_corr(netp):.3f}")

print("\n== (d) credit-impulse gate: HY OAS 1y change -> gate the HY/IG carry off ==")
hy = fred('BAMLC0A4CBBB') if False else None
hyoas = pd.read_csv(f"{ROOT}/tools/quant/data/newdata/BAMLH0A0HYM2.csv")
hyoas = pd.Series(hyoas[hyoas.columns[1]].astype(float).values, index=pd.to_datetime(hyoas[hyoas.columns[0]])).dropna().sort_index()
imp = hyoas - hyoas.shift(252)
imp_d = imp.reindex(panel.index, method='ffill')
wgt = pd.Series(np.where(imp_d < 0, 0.8, 0.0), index=panel.index)  # spreads falling => carry on
w = pd.DataFrame({'JNK': wgt, 'LQD': 0.4})
net = book_eval(w, panel)
st = stat(net); yok, _ = yearly_ok(net)
print(f"credit-impulse HY/IG SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} corr={champ_corr(net):.3f} yearly_ok={yok}")
