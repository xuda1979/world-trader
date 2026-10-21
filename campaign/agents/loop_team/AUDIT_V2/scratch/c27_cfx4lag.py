#!/usr/bin/env python3
"""CFX4 position-lag scramble deeper: the composite sig EW of 4 books may dilute a single
lag's damage. Try: (i) per-book pos-lag then re-aggregate (same lag all books, 400 draws);
(ii) more draws (1000); (iii) lags restricted differently. Also verify CFX4 concentration:
top-50d share of PnL (disclosed 73.9%/74%)."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
FXD = "/Users/daxu/software/world-trader/tools/quant/data/fx"
COST = 6.0/1e4
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
common = sig.dropna().index
sigc = sig.loc[common]; mvc = mv4.loc[common]
real = (sigc*mvc).mean()/(sigc*mvc).std()*np.sqrt(252)
print(f"real composite SR: {real:.4f}  n={len(sigc)}")

def poslag(nperm, seed, lo=21, hi=None):
    T = len(sigc); hi = hi or T-21
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(nperm):
        lag = int(rng.integers(lo, hi))
        pnl = np.roll(sigc.values, lag)*mvc.values
        if pnl.std()>0 and pnl.mean()/pnl.std()*np.sqrt(252) >= real: cnt += 1
    return cnt/nperm
print(f"pos-lag 1000x seed1: {poslag(1000,1):.4f}")
print(f"pos-lag 1000x seed2: {poslag(1000,2):.4f}")
print(f"pos-lag lags>=63:    {poslag(500,3,lo=63):.4f}")

# per-book lag, aggregate
def poslag_perbook(nperm, seed):
    T = len(sigc); rng = np.random.default_rng(seed); cnt = 0
    for _ in range(nperm):
        lags = rng.integers(21, T-21, size=4)
        pnl = np.zeros(T)
        for k in range(4):
            pnl += np.roll(sigc.values, int(lags[k]))*mvc.values
        pnl /= 4
        if pnl.std()>0 and pnl.mean()/pnl.std()*np.sqrt(252) >= real: cnt += 1
    return cnt/nperm
print(f"pos-lag per-book 500x: {poslag_perbook(500,4):.4f}")

# concentration on committed file
cfx = pd.read_csv("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
tot = cfx.sum(); o = np.argsort(cfx.values)[::-1]
for k in [5,10,20,50]:
    print(f"top-{k} days = {cfx.values[o[:k]].sum()/tot*100:.1f}% of PnL")
# max day
i = o[0]
print(f"max day {cfx.index[i].date()} {cfx.iloc[i]*100:.2f}%")
# gross exposure check (from c13): mean |sig| per book:
g = sig.abs().mean()
print(f"mean |sig| (composite) = {g:.4f}; p95 {sig.abs().quantile(0.95):.4f} max {sig.abs().max():.4f}")
