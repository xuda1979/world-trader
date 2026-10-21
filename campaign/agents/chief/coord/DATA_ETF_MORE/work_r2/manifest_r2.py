#!/usr/bin/env python3
"""Rebuild more_etf/manifest.csv: lint EVERY csv on disk with the round-1/2 gates.

Gates (fail-closed): n>=250 positive closes, start<=2007-01-01, max calendar gap<=10d,
|ret|>50% on <=3 days. Freshness (end>=2026-06) recorded but not gating here — the
R1/R2-written series all end 2026-09; a stale series would be flagged STALE.
Any FAIL is reported loudly (it must not silently stay in the hunt universe).
"""
import os
import pandas as pd

D = "/Users/daxu/software/world-trader/tools/quant/data/more_etf"
START_BOUND = pd.Timestamp("2007-01-01")

rows = []
for fn in sorted(os.listdir(D)):
    if not fn.endswith(".csv") or fn == "manifest.csv":
        continue
    sym = fn[:-4]
    df = pd.read_csv(f"{D}/{fn}")
    ok, status, detail = True, "OK", ""
    try:
        df["date"] = pd.to_datetime(df["date"])
        s = df.set_index("date")["close"].astype(float)
        s = s.sort_index()
        s = s[s > 0]
        n = len(s)
        start, end = str(s.index[0].date()), str(s.index[-1].date())
        dup = int(s.index.duplicated().sum())
        gaps = s.index.to_series().diff().dt.days.dropna()
        mg = int(gaps.max())
        jr = int((s.pct_change().abs() > 0.5).sum())
        zr = int((s.pct_change() == 0).sum())
        if n < 250:
            ok, status = False, "FAIL(short)"
        elif s.index[0] > START_BOUND:
            ok, status = False, "FAIL(start)"
        elif mg > 10:
            ok, status = False, "FAIL(gap)"
        elif jr > 3:
            ok, status = False, "FAIL(jumps)"
        elif end < "2026-06":
            status = "STALE"
        detail = f"jumps={jr} dup_dates={dup}"
    except Exception as e:
        ok, status, detail = False, "FAIL(read)", repr(e)[:60]
        n, start, end, mg, zr = len(df), "", "", "", ""
    rows.append(dict(symbol=sym, start=start, end=end, rows=n,
                     max_gap_days=mg, zero_ret_rows=zr,
                     status=f"{status}({detail})"))

out = pd.DataFrame(rows)
out.to_csv(f"{D}/manifest.csv", index=False)
bad = out[~out.status.str.startswith("OK") & ~out.status.str.startswith("STALE")]
print(f"manifest rebuilt: {len(out)} series, {len(out)-len(bad)} OK/STALE, {len(bad)} FAIL")
if len(bad):
    print(bad.to_string())
# charter (c): maxgap/zero_ret must be real numbers, never empty
empt = out[(out.max_gap_days == "") | (out.zero_ret_rows == "")]
assert len(empt) == 0, f"empty metric cols: {empt.symbol.tolist()}"
print("charter-(c) metric columns populated: OK")
