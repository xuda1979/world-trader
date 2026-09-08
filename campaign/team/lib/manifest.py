"""manifest.py — tiny dataset manifest helpers (short-file pattern for data agents).

Builds/reads the canonical manifest.csv (symbol,start,end,rows,max_gap_days,family) that
DATA_ORGANIZE/CLEAN/MAESTRO share. Directly HTTP-free; pure stdlib/pandas only.
"""
import csv
import os


def row(family, symbol, start, end, rows, max_gap):
    """Return one manifest dict row (caller decides gaps)."""
    return {"family": family, "symbol": symbol, "start": start,
            "end": end, "rows": rows, "max_gap_days": max_gap}


def load(path):
    """Read a manifest.csv to a list of dict rows. Missing file -> [] (fail-closed, not None)."""
    if not os.path.isfile(path):
        return []
    with open(path) as fh:
        return list(csv.DictReader(fh))


def save(path, rows):
    """Write manifest rows to path (family dir must exist). Returns path."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    return path
