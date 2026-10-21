# m4b: fixed set ops; SPY vendor-hole test + SPY moves on CSV-missing days
import pandas as pd, numpy as np
CSV = "/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
r = pd.read_csv(CSV, index_col=0, parse_dates=True).iloc[:,0].sort_index()
spy = pd.read_csv("/Users/daxu/software/world-trader/tools/quant/data/twelvedata/SPY.csv")
dc = spy.columns[0]; spy[dc]=pd.to_datetime(spy[dc]); spy=spy.set_index(dc).sort_index()
spy = spy[(spy.index>=r.index[0]) & (spy.index<=r.index[-1])]
csv_open = set(r.index); spy_open = set(spy.index)
win = {d for d in spy_open if r.index[0]<=d<=r.index[-1]}
miss2 = sorted(win - csv_open); extra = sorted(csv_open - win)
print(f"SPY rows in window: {len(win)}; CSV rows: {len(csv_open)}")
print(f"SPY-has / CSV-missing: {len(miss2)}")
for d in miss2: print("   ", d.date(), d.day_name())
print(f"CSV-has / SPY-missing: {len(extra)}", [str(d.date()) for d in extra[:10]])
sret = spy['close'].pct_change()
vals = pd.Series([sret.get(d, np.nan) for d in miss2], index=pd.DatetimeIndex(miss2)).dropna()
print(f"\nSPY |ret| on CSV-missing days: mean {vals.abs().mean()*100:.3f}%  max {vals.abs().max()*100:.2f}% on {vals.abs().idxmax().date()}")
print(f"missing days with |SPY move|>1%: {int((vals.abs()>0.01).sum())}")
for d,v in vals[vals.abs()>0.01].items(): print(f"   {d.date()}: SPY {v*100:+.2f}%")
# cumulative SPY drift skipped by missing days
tot = (1+vals).prod()-1
print(f"compound SPY return across all missing days (if flat otherwise): {tot*100:+.2f}% over {len(vals)} days")

# what does the CSV do on the day AFTER a missing day?
print("\nCSV return on first day back after each gap (is PnL accumulated there?)")
after = []
for d in miss2:
    nxt = r.index[r.index.searchsorted(d)]
    if nxt > d: after.append((d, nxt, r.loc[nxt]))
import numpy as np
a = pd.Series({b:v for _,b,v in after})
base = r.median()
print(f"median |ret| after-gap day: {a.abs().median()*100:.3f}% vs overall median {base*100:.3f}%")
print(f"mean after-gap day: {a.mean()*100:+.3f}% vs overall mean {r.mean()*100:+.3f}%")
