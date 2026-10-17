#!/usr/bin/env python3
"""ITER62 wave-1 (2026-10-16): append-only extend of the 5 lint-fail EIA spot leaves.

eia_dl.py full re-download lint-fails on pre-1995 publication holes for
wti/brent/gas_nyh/gas_gulf/jet (holes are pre-existing on disk; fail-correct).
This script extends those leaves append-only instead: fetch via eia_dl.fetch()
(same keyless dnav XLS, same parser), overlap recon vs on-disk (echo committed
prefix, tolerate EIA restatement up to RESTATE_TOL with disclosure), append tail.

ulsd_nyh/ulsd_gulf already extended by eia_dl.py this session (lint ok, 10-14).

Live-mirror prune (documented precedent v7_raw_refresh 2026-09-22): EIA's live
dnav mirror carries fewer old daily rows than the on-disk archives (pruned at the
source). Overlap on what the mirror DOES carry is exact (maxdev 0.0, n_restate 0,
verified 2026-10-16). Gate: overlap >= 50% of disk rows AND dev < RESTATE_TOL AND
live_end >= disk_end -> prefix echo from disk + append tail.
"""
import json
import sys

import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/eia_weekly")
import eia_dl  # noqa: E402

ROOT = "/Users/daxu/software/world-trader"
EIAW = f"{ROOT}/tools/quant/data/eia_weekly"
REPORT = f"{ROOT}/campaign/work_backtest_oos/refresh_2026_10_16/eia_extend_report.json"

# (nickname, series_id) for the leaves still ending 09-22
LEAVES = [
    ("wti_spot_daily", "RWTCd"),
    ("brent_spot_daily", "RBRTEd"),
    ("gasoline_nyh_spot_daily", "EER_EPMRU_PF4_Y35NY_DPGd"),
    ("gasoline_gulf_spot_daily", "EER_EPMRU_PF4_RGC_DPGd"),
    ("jet_gulf_spot_daily", "EER_EPJK_PF4_RGC_DPGd"),
]

RESTATE_TOL = 0.02  # $/gal tolerance for EIA restatement on overlap; echo prefix regardless


def main():
    dry = "--dry-run" in sys.argv
    report = {}
    ok_all = True
    for nick, sid in LEAVES:
        path = f"{EIAW}/{nick}.csv"
        try:
            disk = pd.read_csv(path, dtype=str)
            rows, err = eia_dl.fetch(sid, "PET")
            if err:
                raise RuntimeError(f"fetch err {err}")
            live = pd.DataFrame(rows, columns=["date", "value"])
            live["value"] = live["value"].astype(str)
            m = disk.merge(live, on="date", suffixes=("_disk", "_live"))
            num_d = pd.to_numeric(m["value_disk"], errors="coerce")
            num_l = pd.to_numeric(m["value_live"], errors="coerce")
            dev = float((num_d - num_l).abs().max())
            n_restate = int(((num_d - num_l).abs() > 1e-9).sum())
            last_disk = disk["date"].max()
            tail = live[live["date"] > last_disk]
            rep = {
                "leaf": nick, "sid": sid, "disk_rows": len(disk), "live_rows": len(live),
                "overlap_n": len(m), "overlap_maxdev": dev, "n_restate": n_restate,
                "disk_last": last_disk, "new_rows": len(tail),
                "new_first": tail["date"].iloc[0] if len(tail) else None,
                "new_last": tail["date"].iloc[-1] if len(tail) else None,
            }
            live_end = live["date"].max()
            full_ok = len(m) == len(disk) and dev <= RESTATE_TOL
            prune_ok = (len(m) >= 0.5 * len(disk) and dev <= RESTATE_TOL
                        and n_restate == 0 and live_end >= last_disk)
            if not (full_ok or prune_ok):
                rep["status"] = "RECON-FAIL"
                rep["err"] = (f"overlap {len(m)}/{len(disk)} dev {dev} restate {n_restate} "
                              f"live_end {live_end} vs disk_end {last_disk}")
                ok_all = False
            else:
                rep["status"] = "OK"
                rep["recon_mode"] = "full" if full_ok else "prune-tolerant"
                if not dry and len(tail):
                    out = pd.concat([disk, tail[["date", "value"]]], ignore_index=True)
                    out.to_csv(path, index=False)
                    rep["action"] = f"extended -> {out['date'].max()} (n={len(out)})"
                else:
                    rep["action"] = "dry-run" if dry else "no new rows"
            report[nick] = rep
            print(json.dumps(rep, default=str))
        except Exception as e:
            ok_all = False
            report[nick] = {"leaf": nick, "status": "EXC", "err": f"{type(e).__name__}: {e}"}
            print(json.dumps(report[nick], default=str))
    report["_meta"] = {"date": "2026-10-16", "dry": dry, "mode": "append-only",
                       "note": "prefix echoed from disk (committed vintage); EIA restatements "
                               "on overlap disclosed via n_restate/maxdev, not applied"}
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=1, default=str)
    print(f"\nreport -> {REPORT} (dry={dry})")
    print("RESULT:", "ALL OK" if ok_all else "PROBLEMS")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
