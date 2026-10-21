#!/usr/bin/env python3
"""HUNT_SECTOR2 round-1: (a) xs 12-1 momentum top3/bot3 monthly, (b) div/style rotation,
(c) macro-regime gated long. Monthly rebalance to control 6.4bps drag."""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/work_r1')
from hunt_lib import *
import numpy as np, pandas as pd

ET = f"{ROOT}/tools/quant/data/more_etf"
SECT = ['XLK','XLY','XLP','XLE','XLF','XLV','XLI','XLB','XLU']
df = pd.DataFrame({t: load_close(f"{ET}/{t}.csv") for t in SECT})
rets_d = df.pct_change()

def rebalance_positions(score, hold_mask_days=21, top=3, bottom=3):
    pos = pd.DataFrame(np.nan, index=df.index, columns=df.columns)
    for i in range(0, len(df)-1, hold_mask_days):
        r = score.iloc[i].dropna()
        if len(r) < 6: continue
        w = pd.Series(0.0, index=df.columns)
        w[r.nlargest(top).index] = 1.0/top
        if bottom:
            w[r.nsmallest(bottom).index] = -1.0/bottom
        pos.iloc[i+1] = w
    return pos.ffill().fillna(0.0)

def book_eval(weights, rets_panel, vt=True):
    w = weights.shift(1).fillna(0.0)
    rg = (w * rets_panel.fillna(0.0)).sum(axis=1)
    if vt:
        sc = vt_scale(rg); w = w.mul(sc, axis=0)
    prev = w.shift(1); prev.iloc[0] = 0.0
    to = (w - prev).abs().sum(axis=1)
    short = (-w.clip(upper=0.0)).sum(axis=1)
    gross = w.abs().sum(axis=1)
    net = ((w * rets_panel.fillna(0.0)).sum(axis=1) - to * COST - short * BORROW/ANN
           - np.maximum(gross-1.0,0)*MARGIN/ANN).dropna()
    return net

print("== (a) 12-1 momentum xs, top3/bot3, monthly ==")
grid = {}
skip = 21
for look in [189, 252, 126]:
    mom = df.shift(skip).pct_change(look)
    for hold in [21]:
        w = rebalance_positions(mom, hold)
        net = book_eval(w, rets_d); st = stat(net); grid[(look,hold)] = (st['sr'], w, net)
        print(f"mom{look}-{hold}d SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} mdd={st.get('mdd')} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')}) corr={champ_corr(net):.3f}")

print("\n== (a2) long-only top3 ==")
for look in [189, 252]:
    mom = df.shift(skip).pct_change(look)
    w = rebalance_positions(mom, 21, top=3, bottom=0)
    net = book_eval(w, rets_d); st = stat(net)
    print(f"momLO{look} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} corr={champ_corr(net):.3f}")

print("\n== (c) regime-gated long-only (SPY 200d trend gate) ==")
spy = load_close(f"{ET}/QQQ.csv")
mkt = spy.pct_change()
ma200 = spy.rolling(200).mean()
gate = (spy > ma200).astype(float).reindex(df.index).ffill().fillna(0.0)
for look in [189]:
    mom = df.shift(skip).pct_change(look)
    w = rebalance_positions(mom, 21, top=3, bottom=0)
    wg = w.mul(gate.shift(1), axis=0)   # gate known at t applied t+1
    net = book_eval(wg, rets_d); st = stat(net)
    print(f"mom{look}GATE SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} corr={champ_corr(net):.3f}")

print("\n== FULL GATES best (a) ==")
best = max(grid, key=lambda k: grid[k][0])
sr, w, net = grid[best]
st = stat(net); yok, yrs = yearly_ok(net)
print(f"BEST mom{best} SR={st['sr']:.3f} neg={st.get('neg_years')} yearly_ok={yok} halves=({st.get('h1')},{st.get('h2')})")
print("years:", yrs)
sc_p, real = scramble(w.sum(axis=1), rets_d.fillna(0).sum(axis=1), n=200)
print(f"scramble_p={sc_p:.3f} corr={champ_corr(net):.4f}")
