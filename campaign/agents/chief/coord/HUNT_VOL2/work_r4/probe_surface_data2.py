#!/usr/bin/env python3
"""HUNT_VOL2 ROUND 4 (a) v2 — CORRECTED fail-closed surface-data probe.

v1 (probe_surface_data.py, prior session) used IV_PAT=("iv",) which catches
atm_iv/iv30 but MISSES columns literally named 'pc_vol' or 'skew' — the exact
features this charter names. v2 scans with the charter's full feature vocabulary
(iv, skew, pc_vol, implied/impl) and classifies honestly:

  IVCOL   — date-indexed csv carrying >=1 charter-surface column
  HISTORY — date-indexed, >=8y span, no IV col (kept for the record)
  SNAP    — chain snapshot (spot/exp/typ/strike, no date)
  OTHER   — everything else

Also checks the charter-named landing spots explicitly (cboe_opts/,
MANIFEST_R4.md). Verdict printed + written; never raises on data.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/daxu/software/world-trader")
OUT = ROOT / "campaign/agents/chief/coord/HUNT_VOL2/work_r4/surface_probe_v2.json"
MIN_SPAN_DAYS = 2085  # 8y

# Charter feature vocabulary — deliberately broad, manually filtered after.
PAT_TOKENS = ("iv", "skew", "pc_vol", "pcvol", "impl", "vol_surf", "ats", "vs_term")
# substrings that mark NON-implied-vol columns even though they contain a token
EXCLUDE = ("div", "activity", "give", "civil", "priv", "deriv_path")


def cols_of(line: str):
    return [c.strip().lower() for c in line.split(",")] if "," in line else [line.strip().lower()]


def surface_cols(header):
    hits = []
    for c in header:
        if any(c.endswith(e) or e + "_" in c or c == e for e in EXCLUDE):
            # keep it simple: drop obvious non-IV words
            if any(x in c for x in ("dividend", "activity", "civil", "private")):
                continue
        if any(t in c for t in PAT_TOKENS):
            hits.append(c)
    return hits


def classify(path: Path):
    rel = str(path.relative_to(ROOT))
    try:
        head = path.read_text(errors="replace")[:4096]
        lines = head.splitlines()
        if not lines:
            return {"file": rel, "class": "EMPTY"}
        header = cols_of(lines[0])
        if not header:
            return {"file": rel, "class": "EMPTY"}
        hits = surface_cols(header)
        has_date = any(c in ("date", "datetime", "time", "day", "timestamp") for c in header)
        if hits and has_date:
            return {"file": rel, "class": "IVCOL", "cols": hits}
        if hits and not has_date and {"spot", "exp", "typ", "strike"} <= set(header):
            return {"file": rel, "class": "SNAP", "cols": hits}
        if hits:
            return {"file": rel, "class": "HITS_NODATE", "cols": hits}
        if has_date:
            return {"file": rel, "class": "OTHER_DATED"}
        return {"file": rel, "class": "OTHER"}
    except Exception as e:  # noqa: BLE001
        return {"file": rel, "class": "ERROR", "err": str(e)[:120]}


def span_days(p: Path):
    try:
        df = pd.read_csv(p)
        dcol = next((df.columns.get_loc(c) for c in df.columns
                     if c.strip().lower() in ("date", "datetime", "time", "day", "timestamp")),
                    None)
        if dcol is None:
            return -1
        s = pd.to_datetime(df.iloc[:, dcol], errors="coerce").dropna()
        return (s.max() - s.min()).days if len(s) >= 10 else -1
    except Exception:
        return -1


def main():
    scanned = 0
    rows = []
    for base in (ROOT / "tools/quant/data", ROOT / "campaign/results"):
        for p in base.rglob("*.csv"):
            if any(part in {".pytest_cache", "__pycache__", "_raw"} for part in p.parts):
                continue
            scanned += 1
            rows.append(classify(p))

    ivcol = [r for r in rows if r["class"] == "IVCOL"]
    for r in ivcol:
        r["span_days"] = span_days(ROOT / r["file"])
    usable = [r for r in ivcol if r["span_days"] >= MIN_SPAN_DAYS]

    cboe_opts = ROOT / "tools/quant/data/cboe_opts"
    manifest_r4 = ROOT / "campaign/agents/chief/coord/DATA_FREDMORE/MANIFEST_R4.md"

    verdict = {
        "scanned_csvs": scanned,
        "ivcol_any_span": sorted([r for r in ivcol], key=lambda r: -r.get("span_days", -1)),
        "n_usable_ge8y": len(usable),
        "usable": usable,
        "cboe_opts_dir_exists": cboe_opts.exists(),
        "data_fredmore_manifest_r4_exists": manifest_r4.exists(),
        "min_span_days_required": MIN_SPAN_DAYS,
    }
    OUT.write_text(json.dumps(verdict, indent=2))
    print(f"scanned={scanned} IVCOL={len(ivcol)} usable>=8y={len(usable)} "
          f"cboe_opts_dir={cboe_opts.exists()} MANIFEST_R4={manifest_r4.exists()}")
    for r in verdict["ivcol_any_span"][:30]:
        print(f"  {r.get('span_days', -1):>7}d  {r['file']}  cols={r['cols']}")
    print("VERDICT: DATA PRESENT" if usable else
          "VERDICT: NO USABLE >=8y CROSS-SECTIONAL pc_vol/skew/atm_iv HISTORY IN TREE")
    sys.exit(0)


if __name__ == "__main__":
    main()
