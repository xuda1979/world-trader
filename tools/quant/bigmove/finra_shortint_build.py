"""FINRA Reg SHO daily short-VOLUME -> monthly short-intensity feature.

User ask (2026-08-23): "include short interest rate which is public data as
the input in the models."

FINRA Reg SHO daily file (public, point-in-time) reports per-symbol per-day:
  ShortVolume | ShortExemptVolume | TotalVolume
The practical public cross-sectional feature is the SHORT RATIO:
  short_ratio(m, tkr) = sum(short_vol) / sum(total_vol)  over month m
This is a genuine point-in-time short-intensity signal (no lookahead: it is
computed only from data available up to month-end m and used for month m+1).
It is NOT short-interest-outstanding (which is bi-monthly and not in repo);
Reg SHO daily short-volume is the standard public proxy and is used here.

This script downloads daily files for a date range, aggregates to a monthly
short_ratio per ticker, and saves a parquet joinable to gkx_monthly_panel on
(month, ticker). Re-runnable: set START/END to widen/extend the window.

Coverage note: Reg SHO data begins materially around 2010 (pre-2010 files are
sparse), so the full historical build should use START>=2010.
"""
from __future__ import annotations
import os, io, sys, urllib.request
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = os.path.join(ROOT, "tools/quant/bigmove")
DATA = os.path.join(HERE, "data", "finra_regsho")
OUT = os.path.join(HERE, "data")
START = pd.Timestamp(os.environ.get("SHORT_START", "2024-01-01"))
END = pd.Timestamp(os.environ.get("SHORT_END", "2026-06-30"))
BASE = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{}.txt"
HDR = {"User-Agent": "Mozilla/5.0"}


import time

MAX_ATTEMPTS = 5          # per file retries before giving up
SLEEP = 1.2               # polite inter-request delay (docs: FINRA CDN throttles)
BACKOFF = 3.0             # base backoff on transient errors (grows x2 per attempt)
MAX_CONSEC_FAIL = 40      # after this many graded failures in a row, take a long pause
LONG_PAUSE = 60.0


def download_days(days):
    os.makedirs(DATA, exist_ok=True)
    # months already fully fetched stay skipped (resume across interrupted runs)
    have = {fn[:-4] for fn in os.listdir(DATA) if fn.endswith(".csv")}
    todo = [d for d in days if f"{d:%Y%m%d}" not in have]
    n_new = 0
    consec_fail = 0
    for i, d in enumerate(todo):
        if i % 60 == 0:
            print(f"  ...{len(todo)-i} left, {len(os.listdir(DATA))} files local", flush=True)
        fn = os.path.join(DATA, f"{d:%Y%m%d}.csv")
        u = BASE.format(f"{d:%Y%m%d}")
        ok = False
        for att in range(1, MAX_ATTEMPTS + 1):
            try:
                r = urllib.request.urlopen(urllib.request.Request(u, headers=HDR), timeout=20)
                data = r.read()
                if len(data) < 50000:      # truncated / empty response
                    raise ValueError("short body")
                open(fn, "wb").write(data)
                ok = True
                consec_fail = 0
                n_new += 1
                break
            except Exception as e:
                time.sleep(BACKOFF * att)
        if not ok:
            consec_fail += 1
            print(f"  fail {d:%Y%m%d} after {MAX_ATTEMPTS} tries", flush=True)
            if consec_fail >= MAX_CONSEC_FAIL:
                print(f"  {MAX_CONSEC_FAIL} consecutive failures; pausing {LONG_PAUSE}s (throttle)", flush=True)
                time.sleep(LONG_PAUSE)
                consec_fail = 0
        time.sleep(SLEEP)
    return n_new


def build_monthly():
    frames = []
    for fn in sorted(os.listdir(DATA)):
        if not fn.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(DATA, fn), sep="|", usecols=["Date", "Symbol", "ShortVolume", "TotalVolume"])
        frames.append(df)
    if not frames:
        print("no files")
        return
    allf = pd.concat(frames)
    # drop FINRA footer row (bare line-count, no Symbol) and any bad-date rows
    allf = allf.dropna(subset=["Symbol"])
    allf = allf[allf["Date"].astype(str).str.fullmatch(r"\d{8}")]
    allf["Date"] = pd.to_datetime(allf["Date"].astype(str), format="%Y%m%d")
    sv = allf.groupby([allf["Date"].dt.to_period("M"), "Symbol"])[["ShortVolume", "TotalVolume"]].sum()
    ratio = (sv["ShortVolume"] / sv["TotalVolume"].replace(0, np.nan)).rename("short_ratio")
    ratio = ratio.reset_index()
    ratio["month"] = ratio["Date"].dt.to_timestamp()
    ratio = ratio[["month", "Symbol", "short_ratio"]].rename(columns={"Symbol": "ticker"})
    ratio.to_parquet(os.path.join(OUT, "finra_short_ratio_monthly.parquet"))
    print(f"monthly short_ratio: {ratio.shape} | months {ratio.month.min().date()}..{ratio.month.max().date()}")
    print(f"  coverage by month:\n{ratio.groupby('month').size().tail(3)}")
    return ratio


def main():
    days = pd.bdate_range(START, END)
    print(f"fetching {len(days)} trading days {START.date()}..{END.date()} (Reg SHO)", flush=True)
    n = download_days(days)
    print(f"downloaded {n} new files into {DATA}")
    ratio = build_monthly()
    if ratio is not None:
        # quick sanity vs union universe coverage
        sys.path.insert(0, HERE)
        import union_panel
        un = union_panel.load_union()
        uni = set(un["close"].columns)
        last = ratio[ratio.month == ratio.month.max()]
        ov = last["ticker"].isin(uni)
        print(f"last-month union coverage: {ov.sum()}/{len(uni)} union names "
              f"({ov.sum()/max(len(uni),1):.0%}); FINRA symbols {len(last)}")


if __name__ == "__main__":
    main()
