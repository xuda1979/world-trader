"""Value sleeve: B/M (book-to-market) with PIT rule (FY data used 6mo after FY end),
monthly long top-half / short bottom-half of B/M, gross 1.0, vt10, 6bps T+1."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from data import closes, save_sleeve
from util import gates, cost
import numpy as np
import pandas as pd

OUT = "/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/value_bm.csv"
f = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/fundamentals_annual.parquet")

px = closes()
ret = px.pct_change(fill_method=None)

# build PIT B/M: for each (symbol, fy) with fy-end assumed Dec-31 of fy, available Jul-1 fy+1
rows = []
for _, r in f.iterrows():
    if pd.isna(r["fy"]) or pd.isna(r["equity"]) or r["equity"] <= 0: continue
    avail = pd.Timestamp(year=int(r["fy"]) + 1, month=7, day=1)
    rows.append((r["symbol"], avail, r["equity"]))
bm_fund = pd.DataFrame(rows, columns=["symbol", "avail", "book"]).drop_duplicates(["symbol", "avail"])

symbols = list(px.columns)
# monthly decision dates
mend = pd.to_datetime(pd.Series(ret.index).groupby(ret.index.to_period("M")).max().values)
w = pd.DataFrame(0.0, index=mend, columns=symbols)
for t in mend:
    elig = bm_fund[bm_fund["avail"] <= t]
    if elig.empty: continue
    latest = elig.sort_values("avail").groupby("symbol").tail(1)
    # price at t
    try:
        pxrow = px.loc[:t].iloc[-1]
    except Exception:
        continue
    bm = latest.set_index("symbol")["book"].reindex(pxrow.index) / pxrow
    bm = bm.dropna()
    bm = bm[bm > 0]
    if len(bm) < 60: continue
    k = len(bm)//3
    hi = bm.nlargest(k).index; lo = bm.nsmallest(k).index
    w.loc[t, hi] = 1.0/len(hi) * 0.5
    w.loc[t, lo] = -1.0/len(lo) * 0.5

pos_exec = w.reindex(ret.index).ffill().shift(1).fillna(0.0)
pnl = (pos_exec * ret).sum(axis=1, min_count=1)
to = pos_exec.diff().abs().sum(axis=1).fillna(0)
r_net = cost(pnl, to)
vol = r_net.expanding(min_periods=126).std().shift(1)*np.sqrt(252)
lev = (0.10/vol).clip(0,3).fillna(0)
r = (r_net*lev).dropna()
r = r[r.index >= "2008-01-01"]
g = gates(r)
print("VALUE B/M:", g)
if g.get("pass_"):
    save_sleeve(r, OUT, "B/M value: monthly, top3 vs bottom3, PIT Jul-1 lag, vt10, 6bps T+1")
else:
    # also print raw quintile spread for diagnostics
    print("failed -> not saved")
