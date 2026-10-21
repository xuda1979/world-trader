"""D02: unit verification + champion-window coverage + FX integrity.
Critical: determine whether brazil_selic values are DAILY percent or ANNUAL percent.
Anchor on published Selic history (Jan-2016 14.25%/yr, Aug-2020 2.00%/yr, Aug-2023 13.25%/yr).
"""
import os
import numpy as np, pandas as pd

ROOT="/Users/daxu/software/world-trader"
EM=os.path.join(ROOT,"tools/quant/data/em_rates")
FR=os.path.join(ROOT,"tools/quant/data/more_fred")

def ld(path, val="value"):
    df=pd.read_csv(path); df.columns=[c.strip().lower() for c in df.columns]
    df["date"]=pd.to_datetime(df["date"]); df=df.set_index("date").sort_index()
    return pd.to_numeric(df[val],errors="coerce")

selic=ld(os.path.join(EM,"brazil_selic.csv"))
print("=== SELIC UNIT CHECK ===")
for d in ["2016-01-15","2016-06-15","2020-08-15","2023-08-15","2025-06-16","2026-09-09"]:
    try:
        v=selic.asof(pd.Timestamp(d)); print(f"  {d}  raw={v:.5f}   x252={v*252:.2f}%/yr   x252cmp={((1+v/100)**252-1)*100:.2f}%/yr")
    except Exception as e: print("  ",d,"ERR",e)

dff=ld(os.path.join(FR,"DFF.csv"))
sofr=ld(os.path.join(FR,"SOFR.csv"))
print("=== USD RATES ===")
for nm,s in [("DFF",dff),("SOFR",sofr)]:
    print(f"  {nm}: n={len(s)} {s.index.min().date()}..{s.index.max().date()} last={s.iloc[-1]}")
    for d in ["2008-10-15","2015-06-15","2019-08-15","2023-08-15"]:
        try: print(f"     {d} = {s.asof(pd.Timestamp(d)):.3f}")
        except Exception: pass

print("\n=== CHAMPION-WINDOW COVERAGE (2008-03-31..2026-08-28) ===")
import pandas as pd
lo,hi=pd.Timestamp("2008-03-31"),pd.Timestamp("2026-08-28")
for f in ["brazil_usdbrl","czech_usdczk","peru_usdpen","poland_usdpln"]:
    s=ld(os.path.join(EM,f+".csv")); w=s.loc[lo:hi]
    full=len(pd.bdate_range(lo,hi))
    # yearly counts
    yc=w.groupby(w.index.year).size()
    dead=[int(y) for y,c in yc.items() if c<200]
    print(f"  {f:15s} n={len(w):5d}/{full} cov={len(w)/full:.3f}  start={w.index.min().date()} end={w.index.max().date()} thin_years={dead}")

print("\n=== FX INTEGRITY: stale runs > 5 consecutive identical values ===")
for f in ["brazil_usdbrl","czech_usdczk","czech_eurczk","peru_usdpen","poland_usdpln","poland_eurpln"]:
    s=ld(os.path.join(EM,f+".csv")).dropna()
    same=(s.diff()==0).astype(int)
    grp=(same!=same.shift()).cumsum()
    runs=same.groupby(grp).sum(); runs=runs[runs>5]
    big=s.pct_change().abs()
    print(f"  {f:15s} stale_runs>5: {len(runs):3d}  max_run={int(runs.max()) if len(runs) else 0}  "
          f"max|1d move|={big.max()*100:.2f}% on {big.idxmax().date()}  n_>5pct={int((big>0.05).sum())}")

print("\n=== TRIANGULAR CHECK: eurczk vs usdczk (implied EURUSD must be sane) ===")
a=ld(os.path.join(EM,"czech_eurczk.csv")); b=ld(os.path.join(EM,"czech_usdczk.csv"))
imp=(a/b).dropna()
print(f"  implied EURUSD from CZK crosses: n={len(imp)} {imp.index.min().date()}..{imp.index.max().date()}")
print(f"    min={imp.min():.4f} max={imp.max():.4f} last={imp.iloc[-1]:.4f}")
print(f"    pct of days outside [0.8,1.7]: {(~imp.between(0.8,1.7)).mean()*100:.2f}%")
a=ld(os.path.join(EM,"poland_eurpln.csv")); b=ld(os.path.join(EM,"poland_usdpln.csv"))
imp2=(a/b).dropna()
print(f"  implied EURUSD from PLN crosses: n={len(imp2)} min={imp2.min():.4f} max={imp2.max():.4f} last={imp2.iloc[-1]:.4f}")
print(f"    pct outside [0.8,1.7]: {(~imp2.between(0.8,1.7)).mean()*100:.2f}%")
