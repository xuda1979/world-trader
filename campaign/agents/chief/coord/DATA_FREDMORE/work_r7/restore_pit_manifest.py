#!/usr/bin/env python3
"""DATA_FREDMORE R7 (a): regenerate the PIT manifest rows destroyed by the
DATA_ORGANIZE 14:40 crash — ATOMICALLY (temp + os.replace, never truncate-then-crash).

Design (charter arithmetic: "update YOUR pin, not the manifest"):
  tools/quant/data/more_fred/manifest.csv is CANONICAL (144 data rows) and stays.
  tools/quant/data/alfred/manifest.csv becomes a purpose-built PIT manifest
  (rich_manifest_registry.json mechanism, DATA_ETF_MORE R7 post-mortem) carrying
  the 6 lost rows' facts in 3 merged vintage-centric rows: every fact the flat
  7-col schema cannot express (lag floors, PIT spans, byte pins, provenance).

Every cell is re-derived from disk (levels re-linted via fred_dl, lags re-measured
from the restored vintage CSVs, sha256_16 of the vintage bytes) — nothing is
transcribed from memory. Idempotent: re-running rewrites identical bytes.
"""
import csv
import datetime as dt
import hashlib
import os
import sys

REPO = "/Users/daxu/software/world-trader"
ALFRED = f"{REPO}/tools/quant/data/alfred"
MOREFRED = f"{REPO}/tools/quant/data/more_fred"
sys.path.insert(0, MOREFRED)
import fred_dl  # noqa: E402

PLAN = {
    "DRALACBS": dict(freq="quarterly", lag_floor=130, alfred_birth="2011-05-24"),
    "DRCLACBS": dict(freq="quarterly", lag_floor=130, alfred_birth="2011-05-24"),
    "WPU05320104": dict(freq="monthly", lag_floor=35, alfred_birth="2015-03-13"),
}
FIELDS = [
    "series_id", "artifact", "level_file", "level_rows", "level_start", "level_end",
    "level_gaps", "level_lint_pass", "vintage_rows", "release_span", "obs_span",
    "lag_min_days", "lag_max_days", "lag_floor_days", "alfred_birth", "vintage",
    "lint_pass", "restored_from", "sha256_16", "status", "note",
]


def sha256_16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def build_rows():
    rows = []
    for sid, cfg in PLAN.items():
        # level facts, re-linted from disk
        with open(f"{MOREFRED}/{sid}.csv") as fh:
            lvl = [(r["date"], float(r["value"])) for r in csv.DictReader(fh)]
        lint = fred_dl.lint(lvl, freq=cfg["freq"])
        assert lint["pass"] is True, (sid, lint)
        # vintage facts, re-measured from the restored artifact
        vpath = f"{ALFRED}/{sid}/vintage.csv"
        with open(vpath) as fh:
            vrows = [(r["release_date"], r["observation_date"]) for r in csv.DictReader(fh)]
        lags = [(dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days
                for a, b in vrows]
        assert min(lags) >= cfg["lag_floor"], (sid, min(lags))
        # alfred_dl documented semantics: the first RELEASE in ALFRED is the birth
        # date; its observation_date stamps the (earlier) period it refers to.
        assert vrows[0][0] >= cfg["alfred_birth"], (sid, vrows[0])
        rows.append({
            "series_id": sid,
            "artifact": f"{sid}/vintage.csv",
            "level_file": f"{sid}.csv",
            "level_rows": len(lvl),
            "level_start": lvl[0][0],
            "level_end": lvl[-1][0],
            "level_gaps": lint["gaps"],
            "level_lint_pass": "True",
            "vintage_rows": len(vrows),
            "release_span": f"{vrows[0][0]}..{vrows[-1][0]}",
            "obs_span": f"{vrows[0][1]}..{vrows[-1][1]}",
            "lag_min_days": min(lags),
            "lag_max_days": max(lags),
            "lag_floor_days": cfg["lag_floor"],
            "alfred_birth": cfg["alfred_birth"],
            "vintage": "True",
            "lint_pass": "True",
            "restored_from": "CAMP_BORROW/work_r6/vintage_rebuilt (2026-09-08 14:56, "
                             "byte-exact; live-ALFRED value-equal re-verified R7)",
            "sha256_16": sha256_16(vpath),
            "status": "ok",
            "note": (
                "R5 charter (a) PIT deliverable; rows destroyed by the DATA_ORGANIZE "
                "14:40 manifest sweep, restored R7 as a purpose-built manifest "
                "(rich_manifest_registry.json pin). Flat-schema more_fred rows for "
                "the level files are unchanged. Lag floor = release >= obs+%dd "
                "(fail-closed lint_vintage)." % cfg["lag_floor"]
            ) + (
                "; WPU vintage stream carries the documented 2015-10-01 "
                "suppressed-at-first-release coverage hole."
                if sid == "WPU05320104" else ""
            ),
        })
    return rows


def main():
    rows = build_rows()
    assert rows and len(rows) == 3
    path = f"{ALFRED}/manifest.csv"
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    with open(path, newline="") as fh:
        got = list(csv.DictReader(fh))
    print("restored %s: %d data rows (atomic tmp+replace)" % (path, len(got)))
    for r in got:
        print("  %s vintage_rows=%s lag %s..%sd floor=%s sha16=%s"
              % (r["series_id"], r["vintage_rows"], r["lag_min_days"],
                 r["lag_max_days"], r["lag_floor_days"], r["sha256_16"]))


if __name__ == "__main__":
    main()
