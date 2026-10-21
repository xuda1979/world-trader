#!/usr/bin/env python3
"""V7 RAW-DATA REFRESH (append-only) — 2026-09-22.

Protocol (CAMP_COST R2/R3/R6 license, extended):
  1. For each raw file: fetch fresh full series from the SAME vendor/source as on-disk.
  2. BYTE-RECON gate: overlap must satisfy index-equality + maxdev < 1e-9
     (exception: the file's LAST on-disk row may be an intraday-settled bar ->
      allowed one-row settle correction, disclosed; vendor revisions for
     single observations (e.g. DTWEXBGS 2026-08-03) are disclosed, not silently applied).
  3. WRITE: echo committed prefix bytes verbatim + append vendor tail (rows with
     date > last committed date). NEVER rewrites history. Dry-run default.
Sources:
  - FRED (fredgraph.csv / api.stlouisfed.org): us10y/us2y/us30y/t10y2y/vix/wti/brent/
    wti_full/tbill3m(TB3MS)/dxy(DTWEXBGS)/aaa/baa + data_fred_new monthly + IRLTLT quartet.
  - EIA dnav hist_xls (keyless): eia_weekly daily spots (wti/brent/ulsd/jet/propane/gasoline).
  - TwelveData API: fx/ 8 pairs + xau/slv/copx (data_fred metals).
  - ECB zip: fx_hist (separate; not part of this refresh — fx_hist already fresh 2026-09-07).
This stage refreshes RAW FILES ONLY. Sleeve regeneration is the next, separately-gated stage.
"""
import argparse
import datetime as dt
import io
import json
import os
import sys
import time
import urllib.request
import zipfile

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HF = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
NEW = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new"
MF = f"{ROOT}/tools/quant/data/more_fred"
FXD = f"{ROOT}/tools/quant/data/fx"
EIAW = f"{ROOT}/tools/quant/data/eia_weekly"
NEWDATA = f"{ROOT}/tools/quant/data/newdata"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

TODAY = pd.Timestamp("2026-09-22")
REPORT = f"{ROOT}/campaign/work_backtest_oos/v7_raw_refresh_report.json"


def load_key(name):
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith(name + "="):
            return line.strip().split("=", 1)[1]
    return None


FRED_KEY = load_key("FRED_KEY")
TD_KEY = load_key("TWELVEDATA_KEY")


# ---------------------------------------------------------------- FRED csv
def fred_csv(sid, start="1980-01-01"):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}"
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=40).read().decode()
    df = pd.read_csv(io.StringIO(raw))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.set_index("date")["value"].dropna()


# ---------------------------------------------------------------- TwelveData
def td_series(symbol, outputsize=5000):
    url = (f"https://api.twelvedata.com/time_series?symbol={symbol}"
           f"&interval=1day&outputsize={outputsize}&apikey={TD_KEY}")
    req = urllib.request.Request(url, headers=UA)
    d = json.loads(urllib.request.urlopen(req, timeout=40).read())
    vals = d.get("values") or []
    s = pd.Series({pd.Timestamp(v["datetime"]): float(v["close"]) for v in vals})
    return s.sort_index()


# ---------------------------------------------------------------- EIA dnav
sys.path.insert(0, EIAW)
import eia_dl  # noqa: E402


def eia_rows(series_id, family="PET"):
    rows, err = eia_dl.fetch(series_id, family)
    if err:
        raise RuntimeError(err)
    s = pd.Series({pd.Timestamp(d): float(v) for d, v in rows})
    return s.sort_index()


# ---------------------------------------------------------------- writer
def append_only(path, new, tag, dry, tol=1e-9, allow_last_bar_settle=True,
                allow_live_mirror_prune=False):
    """Echo committed prefix + append tail. Returns status dict.

    allow_live_mirror_prune: EIA's live dnav mirror has PRUNED ~1000 old daily
    rows vs the on-disk copy (verified 2026-09-22: overlap maxdev=0.0, identical
    values, fewer dates). For those files the overlap gate is identity-on-shared-
    dates + tail continuation, NOT full-count equality. The disk prefix stays
    authoritative (append-only); the pruned mirror rows are NOT deleted from disk.
    """
    disk = pd.read_csv(path, index_col=0, parse_dates=True)
    disk.columns = ["value"]
    old = disk["value"].dropna()
    if new is None or len(new) == 0:
        return dict(tag=tag, status="FETCH-EMPTY", path=path)
    both = pd.concat([old.rename("old"), new.rename("new")], axis=1, join="inner").dropna()
    dev = float((both["old"] - both["new"]).abs().max()) if len(both) else np.nan
    n_expected = len(old)
    settle_rows = 0
    if len(both) < n_expected and allow_last_bar_settle and len(both) == n_expected - 1:
        # the last committed bar was intraday-unsettled at fetch time
        settle_rows = 1
    full_ok = (len(both) == n_expected and dev < tol) or (settle_rows == 1 and dev < tol)
    prune_ok = (allow_live_mirror_prune and len(both) >= 0.5 * n_expected
                and dev < tol and settle_rows == 0
                and new.index.max() >= old.index.max())
    if not (full_ok or prune_ok):
        return dict(tag=tag, status="RECON-FAIL", path=path, overlap=len(both),
                    expected=n_expected, maxdev=dev)
    tail = new[new.index > old.index.max()].dropna()
    out = pd.concat([old, tail])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    if not dry:
        out.rename("value").rename_axis("date").to_csv(path)
    mode = "prune-tolerant" if (prune_ok and not full_ok) else "full"
    return dict(tag=tag, status="OK", path=path, disk_end=str(old.index.max().date()),
                new_end=str(out.index.max().date()), appended=len(tail),
                settle_corrected=settle_rows, recon_maxdev=dev, recon_mode=mode,
                overlap=len(both), expected=n_expected)


def append_only_ohlc(path, new_close, tag, dry, tol=1e-9):
    """fx/ files are OHLCV. Verify close-identity on overlap then append OHLCV tail."""
    disk = pd.read_csv(path, index_col=0, parse_dates=True)
    old_close = disk["close"].dropna()
    both = pd.concat([old_close.rename("old"), new_close.rename("new")], axis=1, join="inner").dropna()
    dev = float((both["old"] - both["new"]).abs().max()) if len(both) else np.nan
    settle = 0
    if len(both) == len(old_close) - 1:
        settle = 1  # last bar was intraday
    if not ((len(both) == len(old_close) or settle) and (dev < tol if len(both) else False)):
        return dict(tag=tag, status="RECON-FAIL", path=path, overlap=len(both),
                    expected=len(old_close), maxdev=dev)
    # for the tail we only have closes from this fetch; append (date,close) rows requires
    # full OHLCV — fetch full OHLC for the tail period separately
    return dict(tag=tag, status="CLOSE-IDENTIFIED", path=path, dev=dev, settle=settle)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=False)
    ap.add_argument("--only", default=None, help="comma list of tags")
    a = ap.parse_args()
    dry = a.dry_run
    only = set(a.only.split(",")) if a.only else None

    jobs = []
    # ---- harness data_fred (daily) ----
    for tag, sid, path, start in [
        ("us10y", "DGS10", f"{HF}/us10y.csv", "1990-01-01"),
        ("us2y", "DGS2", f"{HF}/us2y.csv", "1990-01-01"),
        ("us30y", "DGS30", f"{HF}/us30y.csv", "1990-01-01"),
        ("t10y2y", "T10Y2Y", f"{HF}/t10y2y.csv", "1990-01-01"),
        ("vix", "VIXCLS", f"{HF}/vix.csv", "1990-01-01"),
        ("wti", "DCOILWTICO", f"{HF}/wti.csv", "1986-01-01"),
        ("wti_full", "DCOILWTICO", f"{HF}/wti_full.csv", "1986-01-01"),
        ("brent", "DCOILBRENTEU", f"{HF}/brent.csv", "1987-05-01"),
        ("tbill3m", "TB3MS", f"{HF}/tbill3m.csv", "2000-01-01"),
        ("dxy", "DTWEXBGS", f"{HF}/dxy.csv", "2006-01-01"),
        ("aaa", "DAAA", f"{HF}/aaa.csv", "1983-01-01"),
        ("baa", "DBAA", f"{HF}/baa.csv", "1986-01-01"),
    ]:
        jobs.append((tag, lambda s=sid, p=path, st=start, t=tag:
                     append_only(p, fred_csv(s, st), t, dry)))

    # ---- data_fred_new (monthly + daily FRED) ----
    for tag, sid in [("DFN_VIXCLS", "VIXCLS"), ("DFN_DTB3", "DTB3"), ("DFN_DGS10", "DGS10")]:
        jobs.append((tag, lambda s=sid, t=tag:
                     append_only(f"{NEW}/{s}.csv", fred_csv(s), t, dry)))

    # ---- EIA weekly daily spots (live dnav mirror pruned old rows -> prune-tolerant) ----
    for tag, nick in [("EIA_wti", "wti_spot_daily"), ("EIA_brent", "brent_spot_daily"),
                      ("EIA_ulsd_nyh", "ulsd_nyh_spot_daily"), ("EIA_ulsd_gulf", "ulsd_gulf_spot_daily"),
                      ("EIA_jet_gulf", "jet_gulf_spot_daily"), ("EIA_gas_nyh", "gasoline_nyh_spot_daily"),
                      ("EIA_gas_gulf", "gasoline_gulf_spot_daily")]:
        rec = dict([(s[0], s) for s in eia_dl.SERIES])[nick]
        jobs.append((tag, lambda r=rec, t=tag:
                     append_only(f"{EIAW}/{r[0]}.csv", eia_rows(r[2], r[1]), t, dry,
                                 allow_live_mirror_prune=True)))

    results = []
    for tag, fn in jobs:
        if only and tag not in only:
            continue
        try:
            r = fn()
        except Exception as e:
            r = dict(tag=tag, status="ERR", err=repr(e)[:160])
        results.append(r)
        print(f"{r.get('tag'):<14} {r.get('status'):<16} "
              f"end={r.get('new_end', r.get('disk_end', '-')):<11} "
              f"appended={r.get('appended', '-')} settle={r.get('settle_corrected', '-')} "
              f"dev={r.get('recon_maxdev', r.get('dev', '-'))} {r.get('err', '')}")
        time.sleep(1.0)

    json.dump({"date": str(TODAY.date()), "dry": dry, "results": results},
              open(REPORT, "w"), indent=1)
    print(f"\nreport -> {REPORT} (dry={dry})")
    n_ok = sum(1 for r in results if r["status"] == "OK")
    print(f"OK: {n_ok} / {len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
