#!/usr/bin/env python3
"""HUNT_FXCARRY2 R5 (b) DATA: fetch Frankfurter (ECB euro reference rates, keyless)
full daily history for all quoted currencies -> work_r5/frankfurter/ + manifest.

Source: https://api.frankfurter.dev/v1/{start}..{end}?base=EUR  (no key, live per
altdata5 roster 2026-09-08). Chunked year-by-year to keep responses small.
Lint: daily series, gap policy disclosed (ECB publishes TARGET business days only:
no weekends, no TARGET holidays — that is the native calendar, not missing data).
"""
import hashlib
import json
import os
import sys
import time
import urllib.request

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/work_r5/frankfurter"
os.makedirs(OUT, exist_ok=True)

BASE = "https://api.frankfurter.dev/v1"


def fetch(start, end, base="EUR"):
    url = f"{BASE}/{start}..{end}?base={base}"
    req = urllib.request.Request(url, headers={"User-Agent": "world-trader-research/1.0"})
    for attempt in range(3):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def main():
    # discover full history + currency set from an early probe
    probe = fetch("1999-01-01", "1999-01-15")
    currencies = sorted(probe["rates"][probe["start_date"]].keys())
    print(f"currencies at 1999 inception ({len(currencies)}): {currencies}")

    rows = {}
    year = 1999
    n_chunks = 0
    while year <= 2026:
        s, e = f"{year}-01-01", f"{year}-12-31"
        d = fetch(s, e)
        for dt, rates in d.get("rates", {}).items():
            rows[dt] = rates
        n_chunks += 1
        year += 1
        time.sleep(0.3)
    print(f"fetched {n_chunks} year-chunks, {len(rows)} dated rows "
          f"({min(rows)} .. {max(rows)})")

    df = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    df.index = pd.to_datetime(df.index)
    df.index.name = "date"

    # per-currency CSVs + manifest
    man = []
    for c in df.columns:
        s = df[c].dropna()
        f = f"{OUT}/{c}.csv"
        s.to_frame("value").to_csv(f)
        sha = hashlib.sha256(open(f, "rb").read()).hexdigest()[:16]
        # gap audit on the union calendar: consecutive-pub-day gaps
        dts = s.index
        gaps = dts.to_series().diff().dt.days
        man.append({
            "currency": c, "n": len(s), "start": str(dts.min().date()),
            "end": str(dts.max().date()), "sha256_16": sha,
            "max_gap_days": int(gaps.max()), "median_gap_days": float(gaps.median()),
        })
        print(f"{c}: n={len(s)} {dts.min().date()}..{dts.max().date()} "
              f"maxgap={int(gaps.max())}d sha={sha}")
    mdf = pd.DataFrame(man)
    mdf.to_csv(f"{OUT}/manifest.csv", index=False)

    # wide panel too (analysis input), + a raw JSON snapshot for provenance
    df.to_csv(f"{OUT}/FRANKFURTER_EUR_wide.csv")
    meta = {
        "source": "api.frankfurter.dev/v1 (ECB euro reference rates, keyless)",
        "base": "EUR", "fetched": "2026-09-08",
        "n_dates": int(len(df)), "span": [str(df.index.min().date()), str(df.index.max().date())],
        "currencies": list(df.columns),
        "calendar_note": "ECB TARGET business days only (no weekends/TARGET holidays) - native calendar",
    }
    json.dump(meta, open(f"{OUT}/fetch_meta.json", "w"), indent=1)
    print(f"\nWIDE panel: {df.shape[0]} dates x {df.shape[1]} currencies")
    print("manifest ->", f"{OUT}/manifest.csv")

    # lint gate: each series must have >=8y of daily data to be span-admissible (V2 s9)
    ok8y = mdf[mdf["n"] >= 8 * 252]
    print(f"span_class: {len(ok8y)}/{len(mdf)} currencies meet the 8y/~2000-obs bar "
          f"(2007plus/pre2007): {sorted(ok8y.currency.tolist())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
