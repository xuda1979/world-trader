# m3: extreme-day forensics + zero-run forensics
import pandas as pd, numpy as np
CSV = "/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
r = pd.read_csv(CSV, index_col=0, parse_dates=True).iloc[:,0].sort_index()

print("== top-8 largest |returns| with neighbors ==")
top = r.abs().nlargest(8).index
for t in top:
    i = r.index.get_loc(t)
    lo, hi = max(0,i-3), min(len(r), i+4)
    print(f"--- {t.date()}  ret={r.loc[t]*100:+.3f}% ---")
    for j in range(lo,hi):
        d=r.index[j]; mark=">>>" if d==t else "   "
        print(f"  {mark} {d.date()} {r.iloc[j]*100:+.4f}%")

print("\n== zero runs ==")
z = (r.abs() < 1e-12)
runs=[]; start=None
for d, isz in z.items():
    if isz and start is None: start=d
    if not isz and start is not None:
        runs.append((start, prev, (r.index.get_loc(prev)-r.index.get_loc(start)+1))); start=None
    prev=d
if start is not None: runs.append((start, prev, len(r)-r.index.get_loc(start)))
runs.sort(key=lambda x:-x[2])
print(f"total zero days: {int(z.sum())}  interior zero days: {int(z.iloc[1:-1].sum())}")
print("runs >= 5 days:")
for s,e,n in runs:
    if n>=5: print(f"   {s.date()} .. {e.date()}  ({n} days)")
print(f"longest run: {runs[0][2]}d" if runs else "no zeros")

print("\n== distribution shape ==")
from scipy import stats as sps
print(f"skew={r.skew():.3f} exkurt={r.kurt():.3f}")
print(f"t-stat of mean (daily): {r.mean()/(r.std(ddof=1)/np.sqrt(len(r))):.2f}")

print("\n== stats under alternative conventions ==")
n=len(r)
print(f"arith ann (mu*252): {r.mean()*252*100:.2f}%   <- claimed 'ann 49.4%' convention")
print(f"CAGR (n/252):       {((1+r).prod()**(252/n)-1)*100:.2f}%")
print(f"SR with ddof=0:     {r.mean()/r.std(ddof=0)*np.sqrt(252):.3f}  vs ddof=1 {r.mean()/r.std()*np.sqrt(252):.3f}")
print(f"SR monthly (arith monthly mean/std): {r.resample('ME').apply(lambda x:x.sum()).mean()/r.resample('ME').apply(lambda x:x.sum()).std()*np.sqrt(12):.3f} (sum convention)")
