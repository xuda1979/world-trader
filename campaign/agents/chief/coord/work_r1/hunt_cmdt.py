#!/usr/bin/env python3
"""HUNT_CMDT2 round-1: xs momentum (rank, hold), sector rotation, inflation gate.
Honest T+1 (pos set at t executes t+1 via shift in book_eval), 6.4bps full-|dW|."""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/work_r1')
from hunt_lib import *
import numpy as np, pandas as pd

ET = f"{ROOT}/tools/quant/data/more_etf"
UNIV = {t: f"{ET}/{t}.csv" for t in
        ['USO','DBC','DBA','GSG','CANE','CORN','SOYB','WEAT','MOO','UNG','SLV','GLD','GDX']}

df = pd.DataFrame({t: load_close(p) for t, p in UNIV.items()})
rets_d = df.pct_change()

def xs_mom(look=252, hold=63, top=3, bottom=3):
    mom = df.pct_change(look)
    pos = pd.DataFrame(np.nan, index=df.index, columns=df.columns)
    for i in range(look, len(df)-1, hold):
        r = mom.iloc[i].dropna()
        if len(r) < 6: continue
        w = pd.Series(0.0, index=df.columns)
        w[r.nlargest(top).index] = 1.0/top
        if bottom:
            w[r.nsmallest(bottom).index] = -1.0/bottom
        pos.iloc[i+1] = w          # decided at t=i, effective t+1 (then held)
    return pos.ffill().fillna(0.0)

def book_eval(weights, rets_panel):
    w = weights.shift(1).fillna(0.0)
    rg = (w * rets_panel.fillna(0.0)).sum(axis=1)
    sc = vt_scale(rg)
    w = w.mul(sc, axis=0)
    prev = w.shift(1); prev.iloc[0] = 0.0
    to = (w - prev).abs().sum(axis=1)
    short = (-w.clip(upper=0.0)).sum(axis=1)
    gross = w.abs().sum(axis=1)
    net = ((w * rets_panel.fillna(0.0)).sum(axis=1) - to * COST - short * BORROW/ANN
           - np.maximum(gross-1.0,0)*MARGIN/ANN).dropna()
    return net

print("== (b) xs momentum rank/hold, top3/bot3 L/S ==")
grid = {}
for look, hold in [(252,63),(189,63),(126,63),(252,21),(126,21)]:
    w = xs_mom(look, hold)
    net = book_eval(w, rets_d)
    st = stat(net); grid[(look,hold)] = st['sr']
    print(f"mom{look}/{hold:<4} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} mdd={st.get('mdd')} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')}) corr={champ_corr(net):.3f}")

print("\n== (b2) long-only top3 ==")
for look, hold in [(252,63),(126,63)]:
    w = xs_mom(look, hold, top=3, bottom=0)
    net = book_eval(w, rets_d); st = stat(net)
    print(f"momLO{look}/{hold} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} corr={champ_corr(net):.3f}")

print("\n== (c) ENERGY/PRECIOUS/AGRI rotation, monthly, 6m mom ==")
grp = {'energy': ['USO','UNG','DBC'], 'precious': ['SLV','GLD','GDX'],
       'agri': ['DBA','CANE','CORN','SOYB','WEAT','MOO']}
gpx = {}
for g, ts in grp.items():
    sub = df[ts].dropna(how='all')
    nav = (1 + sub.pct_change().fillna(0)).cumprod(); nav = nav.div(nav.iloc[0])
    gpx[g] = nav.mean(axis=1)
gpx = pd.DataFrame(gpx).dropna(); retsg = gpx.pct_change()
posg = pd.DataFrame(np.nan, index=gpx.index, columns=gpx.columns)
for i in range(126, len(gpx)-1, 21):
    row = retsg.iloc[i-126:i].sum()
    w = pd.Series(0.0, index=gpx.columns)
    w[row.idxmax()] = 1.0
    posg.iloc[i+1] = w   # whole-row assignment (CoW-safe); decided t, effective t+1
posg = posg.ffill().fillna(0.0)
netg = book_eval(posg, retsg); st = stat(netg)
print(f"sector-rot SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} mdd={st.get('mdd')} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')}) corr={champ_corr(netg):.3f}")

print("\n== (d) CPI-regime gate on DBC (yoy accelerating => long) ==")
cpi = pd.read_csv(f"{ROOT}/tools/quant/data/more_fred/CPALTT01USM657N.csv", parse_dates=['date'], index_col='date')['value']
cpi_yoy = cpi.rolling(12).apply(lambda x: (1+x/100).prod()-1)
d = df[['DBC']].pct_change()
ci = cpi_yoy.reindex(d.index, method='ffill').shift(62)
sig = pd.Series(np.where(ci > ci.shift(63), 1.0, -1.0), index=d.index)
netd = book_eval(pd.DataFrame({'DBC': sig}), d); std = stat(netd)
print(f"cpi-gate SR={std['sr']:>6.3f} ann={std['ann']:>8.4f} negyr={std.get('neg_years')} corr={champ_corr(netd):.3f}")

print("\n== FULL GATES on the best of family (b) ==")
best = max(grid, key=grid.get)
w = xs_mom(*best); net = book_eval(w, rets_d)
st = stat(net); yok, yrs = yearly_ok(net)
sc_p, real = scramble(w.sum(axis=1), rets_d.fillna(0).sum(axis=1), n=200)
print(f"BEST mom{best} SR={st['sr']:.3f} yearly_ok={yok} negyears={st.get('neg_years')}")
print("years:", yrs)
