#!/usr/bin/env python3
"""ITER62 wave-1 (2026-10-16): raw-leaf fetch for the 8 stale sleeves' inputs.

Stage A — FRED leaves via api.stlouisfed.org (fredgraph.csv endpoint timing out
today, 2026-10-16; API endpoint verified live; SAME vendor FRED, SAME series):
  data_fred_new/{DAAA,DBAA,DGS10,DFF}.csv   (A5_r7_credit_composite inputs)

Convention reconstruction (verified this session, 2026-10-16):
  on-disk files == FRED API observations (1990+), dot-rows ('.') DROPPED,
  two columns date,value. Overlap disk-vs-API maxdev = 0.0 (exact string values).

Protocol (CAMP_COST license): BYTE-RECON gate on overlap (exact equality for
these leaves; values are decimal strings), append-only extend, fail-closed.
Dry-run first. NOT extended if recon fails.
"""
import json
import sys
import time
import urllib.request

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
NEW = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new"
REPORT = f"{ROOT}/campaign/work_backtest_oos/refresh_2026_10_16/fetch_raw_report.json"

SERIES = ["DAAA", "DBAA", "DGS10", "DFF"]


def load_key(name):
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith(name + "="):
            return line.strip().split("=", 1)[1]
    return None


FRED_KEY = load_key("FRED_KEY")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def fred_api_series(sid):
    """Full observation history from FRED API, ascending, 1990+ window applied
    by caller convention check. Returns DataFrame[date(str), value(str)]."""
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
    ok_all = True
    for sid in SERIES:
        path = f"{NEW}/{sid}.csv"
        try:
            disk = pd.read_csv(path, dtype=str)
            api = fred_api_series(sid)
            # convention: dot-rows dropped
            nodot = api[api["value"] != "."].reset_index(drop=True)
            # overlap recon: exact string equality
            m = disk.merge(nodot, on="date", suffixes=("_disk", "_api"))
            m_eq = m["value_disk"] == m["value_api"]
            n_eq = int(m_eq.sum())
            n_overlap = len(m)
            n_mismatch = n_overlap - n_eq
            mismatches = m.loc[~m_eq, ["date", "value_disk", "value_api"]].head(10)
            # tail = api rows strictly after disk's last date
            last_disk = disk["date"].max()
            tail = nodot[nodot["date"] > last_disk]
            rep = {
                "series": sid,
                "disk_rows": len(disk),
                "api_rows_nodot": len(nodot),
                "overlap_n": n_overlap,
                "overlap_exact": n_eq,
                "overlap_mismatch": n_mismatch,
                "disk_last": last_disk,
                "new_rows": len(tail),
                "new_first": tail["date"].iloc[0] if len(tail) else None,
                "new_last": tail["date"].iloc[-1] if len(tail) else None,
            }
            if n_overlap != len(disk):
                rep["status"] = "RECON-FAIL"
                rep["err"] = f"overlap {n_overlap} != disk {len(disk)} (API pruned or shape change)"
                ok_all = False
            elif n_mismatch > 0:
                rep["status"] = "RECON-FAIL"
                rep["mismatch_sample"] = mismatches.values.tolist()
                ok_all = False
            else:
                rep["status"] = "OK"
                if not dry and len(tail):
                    out = pd.concat([disk, tail[["date", "value"]]], ignore_index=True)
                    out.to_csv(path, index=False)
                    rep["action"] = f"extended -> {out['date'].max()} (n={len(out)})"
                else:
                    rep["action"] = "dry-run" if dry else ("no new rows" if not len(tail) else "noop")
            report[sid] = rep
            print(json.dumps(rep, indent=1, default=str))
        except Exception as e:
            ok_all = False
            report[sid] = {"series": sid, "status": "EXC", "err": f"{type(e).__name__}: {e}"}
            print(json.dumps(report[sid], indent=1))
        time.sleep(1.0)
    report["_meta"] = {"date": "2026-10-16", "dry": dry, "endpoint": "api.stlouisfed.org"}
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=1, default=str)
    print(f"\nreport -> {REPORT} (dry={dry})")
    print("RESULT:", "ALL OK" if ok_all else "PROBLEMS")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
