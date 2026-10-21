#!/usr/bin/env python3
"""AUDIT_V2 check 3: SCRAMBLE GATE degeneracy on diescrack + CFX4.
(a) literal return-permutation p(SR_perm >= SR_real) — 200x block + iid;
(b) position-lag circular scramble p — 200x, lags 21..T-21 (per HUNT_BASIS2's definition);
(c) 10d block bootstrap of returns p(SR_boot <= 0) (VET gate G6a).
For (b) I need per-unit gross pnl + positions; for diescrack use my raw rebuild pos;
for CFX4 use the composite: sig is book-average; approximate pos = sign structure via
rebuild from c17 but keep per-book: use the first-book sig vs its own pnl is not composite...
Simplify: implement (b) as circular shift of the NET return series vs itself? No — the
meaningful implementation: circular-shift the POSITION path against the PRICE-MOVE path.
For both engines I rebuild gross per-unit pnl r_path (sp.diff for diescrack; R[a]-R[b]
per book for CFX4) and position path pos_t (0/±1 or weight)."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import c17_sleeves as S
import warnings; warnings.filterwarnings('ignore')

def literal_perm_p(r, n=200, seed=3, block=10, mode='block'):
    x = np.asarray(r.dropna()); T = len(x); rng = np.random.default_rng(seed)
    real = x.mean()/x.std()*np.sqrt(252); cnt = 0
    if mode == 'iid':
        for _ in range(n):
            xp = rng.permutation(x)
            if xp.std()>0 and xp.mean()/xp.std()*np.sqrt(252) >= real: cnt += 1
    else:
        nb = T//block
        for _ in range(n):
            st = rng.integers(0, T-block, size=nb)
            xp = np.concatenate([x[s:s+block] for s in st])[:T]
            if xp.std()>0 and xp.mean()/xp.std()*np.sqrt(252) >= real: cnt += 1
    return cnt/n

def position_lag_p(pos, moveret, n=200, seed=5, lo=21, hi=None):
    """circular-lag position path vs return path; p(SR_circ >= SR_real)."""
    p = pos.dropna(); mv = moveret.reindex(p.index).fillna(0.0)
    T = len(p); hi = hi or T-21
    real_sr = (p*mv).mean()/(p*mv).std()*np.sqrt(252)
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(n):
        lag = int(rng.integers(lo, hi))
        ps = np.roll(p.values, lag)
        pnl = ps*mv.values
        if pnl.std()>0 and pnl.mean()/pnl.std()*np.sqrt(252) >= real_sr: cnt += 1
    return cnt/n

# ---- diescrack: rebuild pos + price-move path ----
import numpy as np
FRED1 = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
NEWD = "/Users/daxu/software/world-trader/tools/quant/data/newdata"
def fred(name):
    import os
    p1 = f"{FRED1}/{name}.csv"
    if not os.path.exists(p1): p1 = f"{NEWD}/{name}.csv"
    df = pd.read_csv(p1, index_col=0, parse_dates=True)
    s = df['value'] if 'value' in df.columns else df.iloc[:,0]
    return pd.to_numeric(s, errors='coerce')[~s.index.duplicated(keep='last')].sort_index()
dj = fred('DJFUELUSGULF')*42.0; wti = fred('wti_full')
sp = (np.log(dj) - np.log(wti)).dropna(); sp = sp[sp.index >= '2008-01-01']
m = sp.rolling(40).mean(); sd = sp.rolling(40).std()
z = (sp-m)/sd
pos = pd.Series(0.0, index=sp.index); pos[z < -2.0] = 1.0; pos[z > 2.0] = -1.0
moveret = sp.diff()            # close_t - close_{t-1}: pos_t is decided on info<=t, earns moveret_t (T+1 ≈ same alignment as engine's sp.diff().shift(-1) with pos shift)
# engine: net uses pos*ret with ret = sp.diff().shift(-1) at pos-time t. Equivalent: pnl_t = pos_{t-1} * sp.diff()_t
pos_l = pos.shift(1)
pnl = (pos_l*moveret).dropna()

# ---- CFX4: rebuild pos path per book ----
FXD = "/Users/daxu/software/world-trader/tools/quant/data/fx"
pairs = ["GBP_USD","NZD_USD","AUD_USD","EUR_USD"]
def loadf(p):
    df = pd.read_csv(f"{FXD}/{p}.csv", index_col=0, parse_dates=True)
    df = df[df.index.dayofweek < 5]
    df = df[~df.index.duplicated(keep='last')].sort_index()
    return df
C = pd.DataFrame({p: loadf(p).close for p in pairs}).dropna()
R = C.pct_change()
books = [("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD"),("EUR_USD","NZD_USD")]
sig_books = []
for a, b in books:
    spl = np.log(C[a])-np.log(C[b])
    zz = [(spl-spl.rolling(lb).mean())/spl.rolling(lb).std() for lb in (21,63)]
    z = sum(zz)/2
    w = (2.0*(-z)).clip(-2,2)/2
    sig_books.append(w.shift(1))
sig = pd.concat(sig_books, axis=1).mean(axis=1)
mv4 = pd.concat([(R[a]-R[b]) for a,b in books], axis=1).mean(axis=1)
pnl4 = (sig*mv4).dropna()

dies_ref = pd.read_csv(S.DIE, index_col=0, parse_dates=True).iloc[:,0]
cfx_ref = pd.read_csv(S.CFX, index_col=0, parse_dates=True).iloc[:,0]
print("=== diescrack_L40Z20 ===")
print(f"  real SR (raw per-unit pnl): {pnl.mean()/pnl.std()*np.sqrt(252):.4f}")
print(f"  literal iid-perm p(SR_perm>=real), 200x: {literal_perm_p(pnl, 200, mode='iid'):.3f}")
print(f"  literal 10d-block-perm p, 200x:          {literal_perm_p(pnl, 200, mode='block'):.3f}")
print(f"  position-lag circular-scramble p, 200x:  {position_lag_p(pos_l, moveret):.4f}")
print(f"  committed net file SR: {dies_ref.mean()/dies_ref.std()*np.sqrt(252):.4f}")
print(f"  committed literal 10d-block p: {literal_perm_p(dies_ref):.3f}")
print("=== CFX4 ===")
print(f"  real SR (raw per-unit pnl): {pnl4.mean()/pnl4.std()*np.sqrt(252):.4f}")
print(f"  literal iid-perm p, 200x: {literal_perm_p(pnl4, 200, mode='iid'):.3f}")
print(f"  literal 10d-block-perm p, 200x:          {literal_perm_p(pnl4, 200, mode='block'):.3f}")
print(f"  position-lag circular-scramble p, 200x:  {position_lag_p(sig, mv4):.4f}")
print(f"  committed net file SR: {cfx_ref.mean()/cfx_ref.std()*np.sqrt(252):.4f}")
print(f"  committed literal 10d-block p: {literal_perm_p(cfx_ref):.3f}")
