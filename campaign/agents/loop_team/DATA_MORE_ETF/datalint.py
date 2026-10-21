"""Fail-closed lint for daily OHLCV CSVs (DATA_MORE_ETF). Columns: date,open,high,low,close,vol."""
import csv, math, os
from datetime import date

COLS = ["date", "open", "high", "low", "close", "vol"]

class DataLintError(ValueError):
    pass

def _pd(s):
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))

def lint(path):
    if not os.path.exists(path):
        raise DataLintError(f"{path}: file not found")
    with open(path) as f:
        rdr = csv.reader(f)
        header = next(rdr)
        if header[:6] != COLS:
            raise DataLintError(f"{path}: bad header {header}")
        rows, dates, closes, zero_ret, nan_rows = [], [], [], 0, 0
        prev_close = None
        for r in rdr:
            if not r or not any(r):
                continue
            if len(r) < 6:
                raise DataLintError(f"{path}: short row {r}")
            d, o, h, l, c = r[0], r[1], r[2], r[3], r[4]
            try:
                cd = float(c); ch = float(h); cl = float(l)
            except ValueError:
                raise DataLintError(f"{path}: non-numeric OHLC in row {r}")
            if math.isnan(cd):
                nan_rows += 1
                continue
            if cd <= 0 or cl <= 0:
                raise DataLintError(f"{path}: non-positive close {r}")
            if ch < cl:
                raise DataLintError(f"{path}: high<low in row {r}")
            if prev_close is not None and cd == prev_close:
                zero_ret += 1
            prev_close = cd
            dates.append(_pd(d)); rows.append(r)
    if len(rows) < 2:
        raise DataLintError(f"{path}: only {len(rows)} data rows")
    for a, b in zip(dates, dates[1:]):
        if b <= a:
            raise DataLintError(f"{path}: dates not strictly ascending at {a}->{b}")
    max_gap = max((b - a).days for a, b in zip(dates, dates[1:]))
    return {"rows": len(rows), "start": rows[0][0], "end": rows[-1][0],
            "max_gap_days": max_gap, "zero_ret_rows": zero_ret, "nan_rows": nan_rows}

def manifest_row(symbol, r):
    return {"symbol": symbol, "start": r["start"], "end": r["end"], "rows": r["rows"],
            "max_gap_days": r["max_gap_days"], "zero_ret_rows": r["zero_ret_rows"],
            "status": "OK"}
