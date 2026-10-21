
"""S1: adversarial check of HUNT_SECTOR2-R7 "dead on admission" DEFECT-(c) claim.

Claim attacked (DEAD_IDEAS HUNT_SECTOR2-R7):
  "on-disk Reg SHO vintage (tools/quant/bigmove/data/finra_regsho, 181 daily files +
   finra_short_ratio_monthly.parquet n=104004) -> real data but 2 DISJOINT windows
   2019-01..02 + 2024-01..08 = max 8 contiguous monthly obs -> materially-short span,
   UNJUDGEABLE (V2 9b)"

Failure mode (c) SPAN/DATA DEFECT: was the candidate killed by a data artifact
rather than absence of signal?  If the on-disk span is longer than claimed, the
row understates the data.
"""
import os
from datetime import date

ROOT = "/Users/daxu/software/world-trader"
D = os.path.join(ROOT, "tools/quant/bigmove/data/finra_regsho")

fs = sorted(f for f in os.listdir(D) if f.endswith(".csv"))
print("dir:", D)
print("n .csv files:", len(fs))
print("distinct years:", sorted(set(f[:4] for f in fs)))
print("distinct YYYYMM:", sorted(set(f[:6] for f in fs)))

ds = [date(int(f[:4]), int(f[4:6]), int(f[6:8])) for f in fs]
gaps = []
for i in range(len(ds) - 1):
    delta = (ds[i + 1] - ds[i]).days
    if delta > 10:
        gaps.append((ds[i].isoformat(), ds[i + 1].isoformat(), delta))
print("gaps (calendar days > 10):", gaps)

runs = []
start = 0
for g in gaps:
    end = fs.index(g[0][:4] + g[0][5:7] + g[0][8:10] + ".csv")
    runs.append((fs[start], fs[end], end - start + 1))
    start = end + 1
runs.append((fs[start], fs[-1], len(fs) - start))
print("contiguous runs (first,last,n_files):")
for r in runs:
    print("   ", r)

p = os.path.join(D, "finra_short_ratio_monthly.parquet")
print()
print("parquet exists:", os.path.exists(p))
try:
    import pandas as pd
    df = pd.read_parquet(p)
    print("parquet shape:", df.shape, "cols:", list(df.columns)[:12])
    for c in df.columns:
        if "date" in c.lower() or "month" in c.lower() or "period" in c.lower():
            s = pd.to_datetime(df[c], errors="coerce")
            print("   col", c, "min", s.min(), "max", s.max(), "nuniq", s.nunique())
            if s.nunique() <= 30:
                print("      uniq:", [str(x)[:10] for x in sorted(s.dropna().unique())])
except Exception as e:
    print("parquet read failed:", repr(e))

if fs:
    f0 = os.path.join(D, fs[-1])
    with open(f0) as fh:
        head = [next(fh) for _ in range(3)]
    print()
    print("sample file", fs[-1], "first 3 lines:")
    for h in head:
        print("   ", h.rstrip()[:200])
    print("n lines:", sum(1 for _ in open(f0)))
