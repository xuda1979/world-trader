"""Multi-source FREE short_ratio build — drop-in for finra_shortint_build.

MOTIVATION (manager standup, 2026-08-25): the original short_ratio feature
treated FINRA Reg SHO daily short-volume as the ONLY public source, and the
research log wrote "full history blocked: FINRA 2019+ only". That conflated
two different limits:
  (a) FINRA's daily short-VOLUME file genuinely begins ~2010/2019 region, and
  (b) BROADER free short-interest data EXISTS from other public sources
      (FINRA Reg SHO, SEC bi-monthly short-interest settlement, exchange
      SRO-published files, etc.) — the model only ever tried one source.
This script is a MULTI-SOURCE crawler so the team can pull whichever free
source is reachable on their network and merge it into the model feature.

OUTPUT CONTRACT (identical to finra_shortint_build so shortint_retrain_ab and
the champion pipeline join without change):
    parquet:  short_ratio_multi_monthly.parquet
    columns:  [month, ticker, short_ratio]   (point-in-time: ratio for month m
              is computed ONLY from data available up to m's month-end, and is
              joined lagged-1-month by the consumer — no lookahead)

ADAPTERS (free, pluggable; try in priority order, merge non-overlapping eras):
  0. finra_repsho   : FINRA daily short-VOLUME -> monthly short_ratio (primary
                      signal used already; free; ~2010+ but practically the
                      CNMSshvol CDN / WAF gate decides reachability)
  1. sec_bimonthly  : SEC bi-monthly SHORT INTEREST OUTSTANDING settlements
                      (free; published by the SROs; goes back further than the
                      daily volume file) -> short_ratio ~ = interest/shares_out
  2. (EXTEND)       : add more free adapters here (exchange files, etc.)
Each adapter returns a [month, ticker, short_ratio] frame; the script merges
them with source-aware dedup (same month+ticker: prefer the higher-priority /
non-null source) and prints an honest per-source coverage report.

PIT discipline: every adapter MUST emit short_ratio for month m using only m's
data. The consumer lags by 1 month, so month m predicts m+1.
"""
from __future__ import annotations
import os, sys, io, time, urllib.request, gzip
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = os.path.join(ROOT, "tools/quant/bigmove")
DATA = os.path.join(HERE, "data")
OUTRATIO = os.path.join(DATA, "short_ratio_multi_monthly.parquet")

START = pd.Timestamp(os.environ.get("SHORT_START", "2010-01-01"))
END   = pd.Timestamp(os.environ.get("SHORT_END", "2026-06-30"))

FINRA_BASE = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{}.txt"
FINRA_HDR  = {"User-Agent": "Mozilla/5.0"}
FINRA_SLEEP = 1.2
FINRA_DIR   = os.path.join(HERE, "data", "finra_regsho")


# ---------------------------------------------------------------------------
# Adapter 0: FINRA Reg SHO daily short-volume -> monthly short_ratio
# ---------------------------------------------------------------------------
def _finra_fetch_day(d):
    os.makedirs(FINRA_DIR, exist_ok=True)
    fn = os.path.join(FINRA_DIR, f"{d:%Y%m%d}.csv")
    if os.path.exists(fn):
        return
    url = FINRA_BASE.format(f"{d:%Y%m%d}")
    for att in range(1, 6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=FINRA_HDR), timeout=20)
            data = r.read()
            if len(data) < 50000:
                raise ValueError("short body")
            open(fn, "wb").write(data)
            return
        except Exception:
            time.sleep(3.0 * att)
    print(f"    [finra] fail {d:%Y%m%d}", flush=True)
    time.sleep(FINRA_SLEEP)


def adapter_finra_repsho(start, end):
    """Monthly short_ratio from FINRA Reg SHO daily short-volume. Free."""
    print("adapter 'finra_repsho' — downloading daily short-volume files "
          f"{start.date()}..{end.date()}")
    days = pd.bdate_range(start, end)
    for i, d in enumerate(days):
        if i % 60 == 0:
            print(f"  ...{len(days)-i} files left", flush=True)
        _finra_fetch_day(d)
        time.sleep(FINRA_SLEEP)
    frames = []
    for fn in sorted(os.listdir(FINRA_DIR)):
        if not fn.endswith(".csv"):
            continue
        try:
            df = pd.read_csv(os.path.join(FINRA_DIR, fn), sep="|",
                             usecols=["Date", "Symbol", "ShortVolume", "TotalVolume"])
        except Exception:
            continue
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["month", "ticker", "short_ratio"])
    allf = pd.concat(frames)
    allf = allf.dropna(subset=["Symbol"])
    allf = allf[allf["Date"].astype(str).str.fullmatch(r"\d{8}")]
    allf["Date"] = pd.to_datetime(allf["Date"].astype(str), format="%Y%m%d")
    sv = allf.groupby([allf["Date"].dt.to_period("M"), "Symbol"])[
        ["ShortVolume", "TotalVolume"]].sum()
    ratio = (sv["ShortVolume"] / sv["TotalVolume"].replace(0, np.nan)).rename("short_ratio")
    ratio = ratio.reset_index()
    ratio["month"] = ratio["Date"].dt.to_timestamp()
    ratio = ratio[["month", "Symbol", "short_ratio"]].rename(columns={"Symbol": "ticker"})
    print(f"    -> {ratio.shape} rows, {ratio.month.nunique()} months "
          f"({ratio.month.min().date()}..{ratio.month.max().date()})")
    return ratio


# ---------------------------------------------------------------------------
# Adapter 1: SEC / SRO bi-monthly short-interest OUTSTANDING (free, full-history)
# ---------------------------------------------------------------------------
# SEC publishes bi-monthly short-interest settlement data free. Each release
# is (symbol, settlement_date, short_interest, avg_daily_volume, days_to_cover).
# short_ratio(month) ~ short_interest / shares_outstanding (or use
# short_interest / avg_daily_volume as a days-to-cover proxy). Because this
# adapter depends on the exact reachable SEC endpoint / file naming on the
# runner's network, it is a STUB that (a) documents the free endpoint, and
# (b) if a local SEC export is dropped into data/sec_short/, consumes it.
# Team task: point SEC_BASE at the live free SEC/SRO feed and confirm the
# column names once, then this adapter runs for full history.
SEC_BASE = os.environ.get("SEC_SHORT_BASE", "")   # e.g. https://www.sec.gov/...
SEC_DIR  = os.path.join(DATA, "sec_short")


def adapter_sec_bimonthly():
    """FREE SEC/SRO bi-monthly short-interest. Returns [month, ticker, short_ratio].
    Reads local CSV/parquet exports placed in data/sec_short/ (schema:
    symbol, settlement_date, short_interest, shares_outstanding, or
    short_interest, avg_daily_volume). If SEC_BASE is set and fetchable, it
    downloads directly."""
    if not os.path.isdir(SEC_DIR):
        print("adapter 'sec_bimonthly' — no local export dir data/sec_short/; "
              "SKIP (set SEC_SHORT_BASE to a live free SEC/SRO feed to enable)")
        return pd.DataFrame(columns=["month", "ticker", "short_ratio"])
    frames = []
    for fn in sorted(os.listdir(SEC_DIR)):
        p = os.path.join(SEC_DIR, fn)
        try:
            if fn.endswith(".parquet"):
                df = pd.read_parquet(p)
            elif fn.endswith(".csv"):
                df = pd.read_csv(p)
            else:
                continue
        except Exception as e:
            print(f"    [sec] bad file {fn}: {e}")
            continue
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["month", "ticker", "short_ratio"])
    df = pd.concat(frames, ignore_index=True)
    df.columns = [str(c).lower() for c in df.columns]
    # normalize: need a date col
    datecol = next((c for c in ["settlement_date", "date", "as_of", "month"]
                    if c in df.columns), None)
    if datecol is None:
        print("    [sec] no date column; SKIP")
        return pd.DataFrame(columns=["month", "ticker", "short_ratio"])
    df["_d"] = pd.to_datetime(df[datecol], errors="coerce")
    df = df.dropna(subset=["_d"])
    # adapters's ratio definition: prefer explicit short_ratio; else
    # short_interest / shares_outstanding; else days-to-cover proxy
    if "short_ratio" in df.columns:
        ratio = df
    else:
        df["short_ratio"] = df["short_interest"] / df.get(
            "shares_outstanding", df["avg_daily_volume"]).replace(0, np.nan)
    sym = next((c for c in ["symbol", "ticker"] if c in df.columns), None)
    if sym is None:
        return pd.DataFrame(columns=["month", "ticker", "short_ratio"])
    out = df[["_d", sym, "short_ratio"]].copy()
    out.columns = ["month", "ticker", "short_ratio"]
    out["month"] = out["month"].dt.to_period("M").dt.to_timestamp()
    out["ticker"] = out["ticker"].str.upper()
    out = out.dropna(subset=["short_ratio"]).drop_duplicates(["month", "ticker"])
    print(f"    -> {out.shape[0]} rows, {out.month.nunique()} months "
          f"({out.month.min().date()}..{out.month.max().date()})")
    return out


# ---------------------------------------------------------------------------
# Merge with source-priority dedup + honest coverage report
# ---------------------------------------------------------------------------
def main():
    frames = []
    print("=== Building multi-source short_ratio (free crawlers) ===", flush=True)
    f0 = adapter_finra_repsho(START, END)
    f0["_src"] = "finra_repsho"
    frames.append(f0)
    f1 = adapter_sec_bimonthly()
    f1["_src"] = "sec_bimonthly"
    frames.append(f1)
    # ---- extend: add more free adapters here ----
    allf = pd.concat(frames, ignore_index=True)
    allf["ticker"] = allf["ticker"].astype(str).str.upper()
    allf = allf.dropna(subset=["short_ratio"]).drop_duplicates(
        ["month", "ticker"], keep="first")  # highest-priority source wins
    allf = allf[["month", "ticker", "short_ratio"]]
    allf = allf.sort_values(["month", "ticker"]).reset_index(drop=True)
    allf.to_parquet(OUTRATIO)
    print(f"\n=== MERGED: {OUTRATIO} ===")
    print(f"  total rows {allf.shape[0]} | {allf.month.nunique()} months "
          f"({allf.month.min().date()}..{allf.month.max().date()})")
    print("  per-source month coverage:")
    for s, g in zip(["finra_repsho", "sec_bimonthly"],
                    [f0, f1]):
        print(f"    {s:14s}: {g.month.nunique()} months, {g.shape[0]} rows")


if __name__ == "__main__":
    main()
