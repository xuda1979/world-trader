"""HONESTY FIX: FINDINGS listed per-year LOYO numbers not actually computed, and said
'8 start-cuts' when c10 ran 5. Compute the real per-year LOYO + max|day| on the DELIVERED
nocarry file, then patch FINDINGS with the true numbers."""
import pandas as pd, numpy as np
def sr(x):
    x=x.dropna(); return float(x.mean()/x.std()*np.sqrt(252))
r=pd.read_csv("sleeves/CFX4_DTF21_63_raw_daily.csv",index_col=0,parse_dates=True)["ret"]
years=sorted(set(r.index.year))
print("LOYO per-year (excl each year):")
for y in years:
    print(f"  ex-{y}: {sr(r[r.index.year!=y]):.3f}")
print("start cuts:")
for s0 in ("2019-09-10","2020-01-01","2021-01-01","2022-01-01","2023-01-01","2024-01-01","2025-01-01"):
    rr=r[r.index>=s0]; print(f"  {s0}+: n={len(rr)} SR={sr(rr):.3f}")
x=r.abs().sort_values(ascending=False)
print(f"nocarry max|day| = {x.iloc[0]*100:.2f}% on {x.index[0].date()}; next4: {[f'{v*100:.2f}%@{d.date()}' for v,d in zip(x.iloc[1:5],x.index[1:5])]}")
