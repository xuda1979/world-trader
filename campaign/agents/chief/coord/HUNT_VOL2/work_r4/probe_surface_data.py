#!/usr/bin/env python3
"""HUNT_VOL2 ROUND 4 (a) — does usable cross-sectional pc_vol/skew/atm_iv CBOE history exist?

Charter: "If DATA_FREDMORE has landed usable CBOE history: test cross-sectional
pc_vol/skew/atm_iv as a champion-eligible sleeve. If data is absent/short-span (<8y),
say NOT JUDGEABLE and stop."

Fail-closed sweep: classify EVERY CSV in tools/quant/data + campaign/results into one of
  IVCOL   — carries implied-vol-ish columns (iv*, *_iv, iv30, pc_vol, skew-like cols)
  HISTORY — a date-indexed series with >= 8y span (2085 calendar days)
  SNAP    — point-in-time chain snapshot (no date column: spot/exp/typ/strike rows)
plus report exact spans. Exit 0 with verdict; never raises on data.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/daxu/software/world-trader")
OUT = ROOT / "campaign/agents/chief/coord/HUNT_VOL2/work_r4/surface_probe.json"
MIN_SPAN_DAYS = 2085  # 8y

IV_PAT = ("iv",)  # column-name substrings counted as implied-vol-ish

# directories whose CSVs are NOT candidate surface data (bit/feeds other lanes own)
SKIP_DIRS = {".pytest_cache", "__pycache__", "_raw"}


def classify(path: Path) -> dict:
    rel = str(path.relative_to(ROOT))
    try:
        head = path.read_text(errors="replace")[:4096]
        lines = head.splitlines()
        if not lines:
            return {"file": rel, "class": "EMPTY"}
        header = [c.strip().lower() for c in header_of(lines[0])]
        if not header:
            return {"file": rel, "class": "EMPTY"}
        iv_cols = [c for c in header if any(p in c for p in IV_PAT)]
        iv_cols = [c for c in iv_cols if not c.endswith("div")]
        has_date = any(c in ("date", "datetime", "time", "day", "timestamp") for c in header)
        if iv_cols and has_date:
            return {
                "file": rel, "class": "IVCOL", "iv_cols": iv_cols,
                "nbytes": path.stat().st_size,
            }
        if not has_date and {"spot", "exp", "typ", "strike"} <= set(header):
            return {"file": rel, "class": "SNAP", "nbytes": path.stat().st_size}
        return {"file": rel, "class": "OTHER"}
    except Exception as e:  # noqa: BLE001
        return {"file": rel, "class": "ERROR", "err": str(e)[:120]}


def header_of(line: str):
    if "," in line:
        return line.split(",")
    return [line]


def span_days(p: Path) -> int:
    try:
        df = pd.read_csv(p)
        dcol = None
        for cand in ("date", "datetime", "time", "day", "timestamp"):
            for c in df.columns:
                if c.strip().lower() == cand:
                    dcol = df.columns.get_loc(c)
                    break
            if dcol is not None:
                break
        if dcol is None:
            return -1
        s = pd.to_datetime(df.iloc[:, dcol], errors="coerce").dropna()
        if len(s) < 10:
            return -1
        return (s.max() - s.min()).days
    except Exception:
        return -1


def main():
    candidates = []
    scanned = 0
    for base in (ROOT / "tools/quant/data", ROOT / "campaign/results"):
        for p in base.rglob("*.csv"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            scanned += 1
            r = classify(p)
            if r.get("class") == "IVCOL":
                r["span_days"] = span_days(p)
            candidates.append(r)

    ivcol = [r for r in candidates if r.get("class") == "IVCOL"]
    snaps = [r for r in candidates if r.get("class") == "SNAP"]
    usable = [r for r in ivcol if r.get("span_days", -1) >= MIN_SPAN_DAYS]

    verdict = {
        "scanned_csvs": scanned,
        "ivcol_files": sorted(ivcol, key=lambda r: -r.get("span_days", -1)),
        "snap_files": [r["file"] for r in snaps],
        "n_usable_ge8y": len(usable),
        "usable": usable,
        "min_span_days_required": MIN_SPAN_DAYS,
    }
    OUT.write_text(json.dumps(verdict, indent=2))
    print(f"scanned={scanned} IVCOL={len(ivcol)} SNAP={len(snaps)} usable>=8y={len(usable)}")
    for r in verdict["ivcol_files"][:25]:
        print(f"  {r.get('span_days',-1):>6}d  {r['file_path']}  cols={r.get('iv_cols',[])}")
    if usable:
        print("VERDICT: DATA PRESENT")
        sys.exit(0)
    print("VERDICT: NO USABLE >=8y IV-COLUMN HISTORY IN TREE")


if __name__ == "__main__":
    main()
