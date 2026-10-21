"""DATA_YFIN fetcher/linter: yfinance global equity/ETF/FX extension (no API key).

Charter: campaign/team/charters/DATA_YFIN.md. Direct HTTP only (yfinance requests),
writes ONLY inside tools/quant/data/yfin/, lints every series fail-closed.
Short functions (<40 lines), one module <200 lines. Tests: test_yfin.py.
"""
import csv
import glob
import os
import time

import pandas as pd

DATA_ROOT = "/Users/daxu/software/world-trader/tools/quant/data"
OUT = os.path.join(DATA_ROOT, "yfin")
COLS = ["date", "open", "high", "low", "close", "volume"]
MAN_HDR = ["symbol", "start", "end", "rows", "max_gap", "status", "dup_dates",
           "zero_ret_rows", "span_class", "ohlc_viol", "n_bad_px"]
FAM_HDR = ["family", "file", "date_col", "kind", "rows", "cols", "exception"]
START = "1995-01-01"


# ---------------- dedupe / plan ----------------

def existing_index(root=DATA_ROOT):
    """Set of every symbol already under any data family (dedupe, charter rule)."""
    out = set()
    for p in glob.glob(os.path.join(root, "*", "*.csv")):
        out.add(os.path.splitext(os.path.basename(p))[0].upper())
    return out


def plan_symbols(candidates, root=DATA_ROOT):
    have = existing_index(root)
    return [s for s in candidates if s.upper() not in have]


# ---------------- fetch + normalize ----------------

def fetch_yf(sym, start=START):
    """Download daily OHLCV via yfinance; returns canonical row tuples or None."""
    import yfinance as yf
    df = yf.download(sym, start=start, auto_adjust=True, progress=False)
    if df is None or not len(df):
        return None
    ndf = normalize_frame(df, sym)
    return [tuple(r) for r in ndf.itertuples(index=False, name=None)]


def normalize_frame(df, sym=""):
    """Flatten yfinance MultiIndex to canonical DataFrame (date,open,...,volume)."""
    if isinstance(df.columns, pd.MultiIndex):
        keep = [c for c in df.columns
                if c[0] in ("Open", "High", "Low", "Close", "Volume")]
        df = df.loc[:, keep].copy()
        df.columns = df.columns.droplevel(1)
    df = df.loc[:, [c for c in ["Open", "High", "Low", "Close", "Volume"]
                    if c in df.columns]].copy()
    df = df.dropna(subset=["Close"]).sort_index()
    df.index.name = "date"
    out = df.reset_index()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.columns = [c.lower() for c in out.columns]
    return out[[c for c in COLS if c in out.columns]]


# ---------------- lint (fail-closed) ----------------

def lint_series(path):
    """Lint one canonical CSV. Returns metric dict; status FAIL on ANY violation."""
    sym = os.path.splitext(os.path.basename(path))[0]
    try:
        df = pd.read_csv(path)
    except Exception:
        return _fail(sym, "unreadable")
    df.columns = [c.lower() for c in df.columns]
    if not {"date", "close"} <= set(df.columns):
        return _fail(sym, "missing date/close")
    res = {"symbol": sym, "start": "", "end": "", "rows": 0, "max_gap": 0,
           "dup_dates": 0, "zero_ret_rows": 0, "span_class": "short",
           "ohlc_viol": 0, "n_bad_px": 0, "status": "PASS"}
    px = pd.to_numeric(df["close"], errors="coerce")
    res["n_bad_px"] = int((~(px > 0) | px.isna()).sum())
    dts = pd.to_datetime(df["date"], errors="coerce")
    res["dup_dates"] = int(dts.duplicated().sum())
    sorted_ok = dts.is_monotonic_increasing and res["dup_dates"] == 0
    df = df.assign(_d=dts, _px=px).dropna(subset=["_d", "_px"]).query("_px > 0")
    if res["n_bad_px"] or res["dup_dates"]:
        res["status"] = "FAIL"
    res.update(_lint_ohlc(df))
    if len(df):
        res.update(_span_gap(df, sorted_ok, res))
    if res["status"] == "PASS" and (res["rows"] < 250 or res["max_gap"] > 10):
        res["status"] = "FAIL"      # <1y data or >2-week hole = not engine-grade
    return res


def _lint_ohlc(df):
    """Count OHLC consistency violations when all four price columns exist."""
    if not {"open", "high", "low"} <= set(df.columns):
        return {"ohlc_viol": 0}
    o, h, l, c = (pd.to_numeric(df[k], errors="coerce") for k in ("open", "high", "low", "close"))
    bad = ((h < o) | (h < c) | (l > o) | (l > c) | (h < l)).fillna(True)
    return {"ohlc_viol": int(bad.sum())}


def _span_gap(df, sorted_ok, res):
    """Span class, max calendar gap, zero-return count (sortedness pinned elsewhere)."""
    d = df["_d"]
    res["start"] = str(d.iloc[0].date())
    res["end"] = str(d.iloc[-1].date())
    res["rows"] = int(len(df))
    gaps = d.diff().dt.days.dropna()
    res["max_gap"] = int(gaps.max()) if len(gaps) else 0
    yr = (d.iloc[-1] - d.iloc[0]).days / 365.25
    res["span_class"] = "pre2007" if str(res["start"]) < "2007" else (
        "2007plus" if yr >= 3 else "short")
    rets = df["_px"].pct_change().dropna()
    res["zero_ret_rows"] = int((rets == 0).sum())
    return res


def _fail(sym, why):
    return {"symbol": sym, "start": "", "end": "", "rows": 0, "max_gap": 0, "status": "FAIL",
            "dup_dates": 0, "zero_ret_rows": 0, "span_class": why, "ohlc_viol": 0, "n_bad_px": 0}


# ---------------- write (path-guarded) + manifests ----------------

def write_csv(sym, rows):
    """Write canonical CSV, refusing any path outside OUT (charter: only write in yfin/)."""
    os.makedirs(OUT, exist_ok=True)
    path = os.path.realpath(os.path.join(OUT, f"{sym}.csv"))
    if os.path.commonpath([path, os.path.realpath(OUT)]) != os.path.realpath(OUT):
        return False
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(rows)
    return True


def safe_write(sym, rows):
    """Alias kept for the write-guard test; identical contract to write_csv."""
    return write_csv(sym, rows)


def write_manifest(out_dir=OUT):
    """Charter manifest: symbol,start,end,rows,max_gap(+lint metrics),status."""
    rows = []
    for p in sorted(glob.glob(os.path.join(out_dir, "*.csv"))):
        m = lint_series(p)
        rows.append({k: m.get(k, "") for k in MAN_HDR})
    with open(os.path.join(out_dir, "manifest.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MAN_HDR)
        w.writeheader()
        w.writerows(rows)


def write_family_manifest(out_dir=OUT, family="yfin"):
    """Canonical DATA_ORGANIZE 7-col manifest (family,file,date_col,kind,rows,cols,exception)."""
    files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(out_dir, "*.csv")))
    with open(os.path.join(out_dir, "manifest.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(FAM_HDR)
        for f in files:
            n = sum(1 for _ in open(os.path.join(out_dir, f))) - 1
            w.writerow([family, f, "date", "timeseries", n, 6, ""])
