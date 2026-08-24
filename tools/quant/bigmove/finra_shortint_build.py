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


def download_days(days):
    os.makedirs(DATA, exist_ok=True)
    n_new = 0
    for d in days:
        fn = os.path.join(DATA, f"{d:%Y%m%d}.csv")
        if os.path.exists(fn):
            continue
        u = BASE.format(f"{d:%Y%m%d}")
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=HDR), timeout=25)
            open(fn, "wb").write(r.read())
            n_new += 1
        except Exception as e:
            print(f"  skip {d:%Y%m%d}: {type(e).__name__}")
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
        cov = last["ticker"].isin(uni).mean()
        print(f"last-month ticker overlap with union universe: {cov:.0%}")


if __name__ == "__main__":
    main()
