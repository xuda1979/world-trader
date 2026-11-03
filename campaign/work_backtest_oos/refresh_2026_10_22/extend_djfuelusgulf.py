#!/usr/bin/env python3
"""v71_stale_refresh_20261022 wave: fetch fresh DJFUELUSGULF (diesel Gulf spot)
from FRED API for the diescrack__prefix sleeve refresh.

Convention (verified vs on-disk, same as refresh_2026_10_16/fetch_raw_leaves.py):
  FRED API observations, dot-rows ('.') DROPPED, columns date,DJFUELUSGULF,
  values as decimal strings (3dp). Overlap disk-vs-API exact string equality.

Protocol: BYTE-RECON gate (exact equality), append-only extend, fail-closed.
Dry-run first; snapshot_pre taken by caller before write-mode run.
"""
import json
import shutil
import sys
import time
import urllib.request

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
PATH = f"{ROOT}/tools/quant/data/newdata/DJFUELUSGULF.csv"
WAVE = f"{ROOT}/campaign/work_backtest_oos/refresh_2026_10_22"
REPORT = f"{WAVE}/djfuelusgulf_extend_report.json"
SNAP = f"{WAVE}/DJFUELUSGULF.csv.snapshot_pre"
SERIES = "DJFUELUSGULF"


def load_key(name):
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith(name + "="):
            return line.strip().split("=", 1)[1]
    return None


FRED_KEY = load_key("FRED_KEY")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def fred_api_series(sid):
    url = (
        "https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={sid}&api_key={FRED_KEY}&file_type=json"
        "&observation_start=1990-01-01&sort_order=asc"
    )
    req = urllib.request.Request(url, headers=UA)
    data = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
    obs = data["observations"]
    df = pd.DataFrame([(o["date"], o["value"]) for o in obs], columns=["date", "value"])
    return df


def main():
    dry = "--dry-run" in sys.argv
    report = {}
    ok = True
    disk = pd.read_csv(PATH, dtype=str).rename(columns={SERIES: "value"})
    api = fred_api_series(SERIES)
    # disk convention (verified 2026-10-22): value written as %.3f; dot-rows kept
    # as EMPTY 2nd field. API raw strings differ only by trailing-zero format on
    # 244/8041 overlap rows — numerically identical (float maxdev = 0.0).
    # => canonicalize API values to 3dp strings BEFORE recon; then exact match.
    nodot = api[api["value"] != "."].copy().reset_index(drop=True)
    nodot["value"] = nodot["value"].astype(float).map(lambda x: f"{x:.3f}")

    # --- recon gate: overlap must equal full disk, exact string equality ---
    m = disk.merge(nodot, on="date", suffixes=("_disk", "_api"))
    m_eq = m["value_disk"] == m["value_api"]
    n_overlap = len(m)
    n_eq = int(m_eq.sum())
    last_disk = disk["date"].max()
    tail = nodot[nodot["date"] > last_disk]

    # disk convention: dot-rows retained as EMPTY 2nd field ("date,\n") — count them
    disk_empty = int((disk["value"].isna() | (disk["value"] == "")).sum())
    rep = {
        "series": SERIES,
        "disk_rows": len(disk),
        "disk_empty_value_rows": disk_empty,
        "api_rows_nodot": len(nodot),
        "overlap_n": n_overlap,
        "overlap_exact": n_eq,
        "overlap_mismatch": n_overlap - n_eq,
        "mismatch_sample": m.loc[~m_eq, ["date", "value_disk", "value_api"]].head(10).values.tolist(),
        "disk_last": last_disk,
        "new_rows": len(tail),
        "new_first": tail["date"].iloc[0] if len(tail) else None,
        "new_last": tail["date"].iloc[-1] if len(tail) else None,
    }

    if n_overlap != len(nodot[nodot["date"] <= last_disk]):
        rep["status"] = "RECON-FAIL"
        rep["err"] = (f"overlap {n_overlap} != api-nodot-up-to-disk-last "
                      f"{len(nodot[nodot['date'] <= last_disk])} (API history pruned/shape change)")
        ok = False
    elif (n_overlap - n_eq) > 0:
        rep["status"] = "RECON-FAIL"
        ok = False
    elif disk_empty != len(disk) - n_overlap:
        rep["status"] = "RECON-FAIL"
        rep["err"] = (f"disk non-empty rows {len(disk)-disk_empty} != overlap {n_overlap} "
                      "(dot-row convention divergence)")
        ok = False
    else:
        rep["status"] = "OK"
        if dry:
            rep["action"] = "dry-run"
        elif len(tail) == 0:
            rep["action"] = "no new rows"
        else:
            # values already canonicalized to 3dp strings above; append-only write
            shutil.copyfile(PATH, SNAP)
            with open(PATH, "a") as f:
                for _, r in tail.iterrows():
                    f.write(f"{r['date']},{r['value']}\n")
            new_disk = pd.read_csv(PATH, dtype=str).rename(columns={SERIES: "value"})
            # post-write verify: prefix rows unchanged, count right
            prefix_ok = new_disk.iloc[: len(disk)].equals(disk)
            rep["action"] = f"extended -> {new_disk['date'].max()} (n={len(new_disk)})"
            rep["prefix_unchanged"] = bool(prefix_ok)
            rep["new_rows_written"] = len(new_disk) - len(disk)
            if not prefix_ok or (len(new_disk) - len(disk)) != len(tail):
                rep["status"] = "VERIFY-FAIL"
                ok = False

    report[SERIES] = rep
    print(json.dumps(rep, indent=1, default=str))
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=1, default=str)
    print("RESULT:", "ALL OK" if ok else "PROBLEMS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
