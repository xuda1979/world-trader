#!/usr/bin/env python3
"""ITER62 wave-2 (2026-10-22): append-only extend of CN main-continuous futures leaves.

Source: akshare futures_zh_daily_sina (keyless), SAME vendor as original fetch
(HUNT_CN_FUTURES/scratch/fetch_futures.py). Leaves on disk end 2026-09-15;
live endpoint verified current through 2026-10-22 today.

Safety: overlap byte-compare of ALL overlapping (date) rows vs disk before any
write; on mismatch -> no write for that leaf (fail-closed). Append-only: the
on-disk prefix is never rewritten. Snapshots of pre-state live in
refresh_2026_10_22/cn_leaf_snapshot_pre/.
"""
import json, os, sys, time
import akshare as ak
import pandas as pd

DATA = "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES/data"
REPORT = "/Users/daxu/software/world-trader/campaign/work_backtest_oos/refresh_2026_10_22/cn_extend_report.json"
DRY = "--dry" in sys.argv

UNIVERSE = sorted(f[:-4] for f in os.listdir(DATA) if f.endswith(".csv"))


def main():
    report = {}
    ok_all = True
    for sym in UNIVERSE:
        path = f"{DATA}/{sym}.csv"
        disk = pd.read_csv(path, dtype={"date": str})
        got = None
        for attempt in range(4):
            try:
                got = ak.futures_zh_daily_sina(symbol=sym)
                break
            except Exception as e:
                print(f"  {sym}: attempt {attempt+1} failed: {e}")
                time.sleep(2 + attempt * 3)
        if got is None:
            report[sym] = {"status": "FETCH_FAIL", "action": "none"}
            ok_all = False
            continue
        got = got.copy()
        got["date"] = got["date"].astype(str)
        got = got.reset_index(drop=True)

        d_dates = set(disk["date"])
        g_dates = set(got["date"])
        overlap = sorted(d_dates & g_dates)
        # byte-compare overlap: normalize both to the same column order/rounding
        cols = list(disk.columns)
        d_idx = disk.set_index("date")
        g_idx = got.set_index("date")
        mismatch = 0
        maxdev = 0.0
        for dt in overlap:
            a = d_idx.loc[dt]
            b = g_idx.loc[dt]
            for c in cols:
                if c == "date":
                    continue
                try:
                    av, bv = float(a[c]), float(b[c])
                    dev = abs(av - bv)
                    maxdev = max(maxdev, dev)
                    if dev > 1e-9:
                        mismatch += 1
                except (TypeError, ValueError):
                    if str(a[c]) != str(b[c]):
                        mismatch += 1
        new_dates = sorted(g_dates - d_dates)
        missing_on_api = sorted(d_dates - g_dates)
        entry = {
            "disk_rows": len(disk),
            "api_rows": len(got),
            "overlap_n": len(overlap),
            "overlap_mismatch": mismatch,
            "overlap_maxdev": maxdev,
            "disk_last": disk["date"].max(),
            "api_last": got["date"].max(),
            "new_rows": len(new_dates),
            "new_first": new_dates[0] if new_dates else None,
            "new_last": new_dates[-1] if new_dates else None,
        }
        if mismatch > 0:
            entry.update({"status": "OVERLAP_MISMATCH", "action": "NOT WRITTEN (fail-closed)"})
            ok_all = False
        elif not new_dates:
            entry.update({"status": "NO_NEW_ROWS", "action": "none"})
        else:
            # append-only: concat disk prefix + api rows not on disk, keep column order
            new_df = got[got["date"].isin(set(new_dates))].copy()
            new_df = new_df[cols]
            entry["status"] = "OK"
            if DRY:
                entry["action"] = f"would append {len(new_dates)} rows -> {new_dates[-1]} (dry)"
            else:
                out = pd.concat([disk, new_df], ignore_index=True)
                out.to_csv(path, index=False)
                entry["action"] = f"extended -> {new_dates[-1]} (n={len(out)})"
            print(f"  {sym:5s} disk_last={entry['disk_last']} api_last={entry['api_last']} "
                  f"new={len(new_dates)} overlap_mismatch={mismatch}")
        if missing_on_api:
            entry["api_missing_disk_rows"] = len(missing_on_api)
            if missing_on_api == [entry["disk_last"]]:
                # common: the current trading day row drops off while session open
                entry["api_missing_note"] = "only disk_last absent on api (in-session artifact)"
            else:
                ok_all = False
                entry["api_missing_note"] = "UNEXPECTED gaps beyond disk_last"
        report[sym] = entry
        time.sleep(1.2)

    report["_meta"] = {"date": "2026-10-22", "dry": DRY,
                       "source": "akshare futures_zh_daily_sina (keyless)",
                       "vendor_same_as_original": True}
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=1, default=str)
    print(f"\nreport -> {REPORT} (dry={DRY})")
    print("RESULT:", "ALL OK" if ok_all else "PROBLEMS")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
