"""fetch_all.py — DATA_AKSHARE pull script (direct HTTP via akshare; no browser).

Families -> tools/quant/data/akshare/<family>/<SYM>.csv + manifest.csv per family.
Fail-closed: series failing lint are NOT written; they're recorded with FAIL reason.
"""
import os
import sys
import time
import warnings

import akshare as ak
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aklib  # noqa: E402

warnings.filterwarnings("ignore")
ROOT = "/Users/daxu/software/world-trader/tools/quant/data/akshare"
SLEEP = 1.5  # respect source rate limits


def _gap_days(dates):
    gaps = pd.to_datetime(pd.Series(dates)).sort_values().diff().dt.days.dropna()
    return int(gaps.max()) if len(gaps) else 0


def save_series(family, symbol, df, min_span=365, max_gap=60):
    """Normalize, lint fail-closed, write <ROOT>/<family>/<SYM>.csv; return manifest row."""
    out = aklib.normalize(df)
    ok, why = aklib.lint(out, min_span_days=min_span, max_gap_days=max_gap)
    if not ok:
        return None, f"FAIL {family}/{symbol}: {why} (rows={len(df) if df is not None else 0})"
    d = pd.to_datetime(out["date"])
    row = aklib.manifest_row(family, symbol, out["date"].iloc[0], out["date"].iloc[-1],
                             len(out), _gap_days(out["date"]))
    aklib.write_csv(os.path.join(ROOT, family), f"{symbol}.csv", out)
    return row, f"ok {family}/{symbol}: {row['start']}..{row['end']} rows={row['rows']} gap={row['max_gap_days']}d"


def retry(fn, tries=3, wait=6):
    """Retry wrapper for flaky EastMoney/Sina endpoints."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            print(f"  retry {i+1} after {repr(e)[:80]}")
            time.sleep(wait * (i + 1))
    return None
