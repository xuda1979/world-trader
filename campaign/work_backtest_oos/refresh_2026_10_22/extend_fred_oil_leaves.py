#!/usr/bin/env python3
"""2026-10-22 wave-1: append-only extend of FRED oil leaves from EIA dnav dailies.

data_fred/brent.csv (ends 2026-09-15) and data_fred/wti_full.csv (ends
2026-09-15) are stale. Verified 2026-10-22 (this session): the FRED files are
EXACTLY identical to EIA dnav brent_spot_daily/wti_spot_daily on overlap --
100% common dates, maxdev 0.0, zero dates only in either (dnav provenance:
FRED DCOILBRENTEU/DCOILWTICO are the same EIA series). So we extend the FRED
leaves append-only from the fresh EIA dnav leaves (2026-09-16..2026-10-14),
values provenance-exact.

Unblocks: brwt7.csv (w=0.1703, top priority), A1_carry_seasonal_v2 oil inputs.

Method (append-only, fail-closed):
  1. snapshot pre-state into refresh dir
  2. re-verify overlap identity disk-FRED vs disk-EIA (maxdev must be 0.0,
     100% common dates on FRED's range)
  3. extend: prefix bytes verbatim (do NOT rewrite via pandas to_csv; the
     cnpair bytefix precedent: full rewrite changes float formatting), append
     new rows as text with EIA's own number formatting
  4. verify HEAD-prefix byte-identical + tail format
"""
import json
import subprocess
import sys

ROOT = "/Users/daxu/software/world-trader"
REFRESH = f"{ROOT}/campaign/work_backtest_oos/refresh_2026_10_22"
FRED = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
EIAW = f"{ROOT}/tools/quant/data/eia_weekly"
REPORT = f"{REFRESH}/fred_oil_extend_report.json"

PAIRS = [
    ("brent.csv", f"{EIAW}/brent_spot_daily.csv"),
    ("wti_full.csv", f"{EIAW}/wti_spot_daily.csv"),
]


def read_two_col(path):
    """Binary-safe read: these leaves are CRLF on disk; text mode would
    silently translate to LF and rewrite the whole file (cnpair bytefix
    precedent, second occurrence). Return (rows, raw_bytes, eol)."""
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("ascii")
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    assert lines[0] == "date,value", f"unexpected header in {path}: {lines[0]!r}"
    rows = []
    for ln in lines[1:]:
        d, v = ln.split(",")
        rows.append((d, v))
    return rows, raw, eol


def main():
    dry = "--dry-run" in sys.argv
    report = {}
    ok_all = True
    for fred_name, eia_path in PAIRS:
        fred_path = f"{FRED}/{fred_name}"
        snap = f"{REFRESH}/{fred_name}.snapshot_pre"
        subprocess.run(["cp", fred_path, snap], check=True)
        fred, _, _ = read_two_col(fred_path)
        eia, _, _ = read_two_col(eia_path)
        fmap = dict(fred)
        emap = dict(eia)
        common = sorted(set(fmap) & set(emap))
        only_f = set(fmap) - set(emap)
        only_e = set(emap) - set(fmap)
        devs = [abs(float(fmap[d]) - float(emap[d])) for d in common]
        maxdev = max(devs) if devs else None
        fdates = [d for d, _ in fred]
        # identity gate: 100% of FRED dates present in EIA, maxdev == 0
        identity_ok = (len(common) == len(fred)) and maxdev == 0.0
        last_fred = fdates[-1]
        new = [(d, emap[d]) for d, v in eia if d > last_fred and d in emap]
        rep = {
            "fred_leaf": fred_name,
            "eia_leaf": eia_path.split("/")[-1],
            "fred_rows": len(fred),
            "eia_rows": len(eia),
            "overlap_n": len(common),
            "overlap_maxdev": maxdev,
            "only_in_fred": len(only_f),
            "only_in_eia_in_range": len([d for d in only_e if d <= last_fred]),
            "identity_ok": identity_ok,
            "committed_last": last_fred,
            "new_rows": len(new),
            "new_first": new[0][0] if new else None,
            "new_last": new[-1][0] if new else None,
        }
        if not identity_ok:
            rep["status"] = "IDENTITY-FAIL"
            rep["err"] = (f"overlap {len(common)}/{len(fred)} maxdev {maxdev} "
                          f"only_fred {len(only_f)}")
            ok_all = False
        else:
            rep["status"] = "OK"
            if not dry and new:
                # binary-safe append: prefix bytes verbatim (CRLF preserved),
                # tail rows written with the file's own EOL
                with open(fred_path, "rb") as f:
                    pre = f.read()
                _, _, eol = read_two_col(fred_path)
                assert pre.endswith(eol.encode("ascii")), "expected trailing EOL"
                tail = "".join(f"{d},{v}{eol}" for d, v in new).encode("ascii")
                final = pre + tail
                # full byte equality gate: result == snapshot + tail exactly
                with open(fred_path, "wb") as f:
                    f.write(final)
                with open(fred_path, "rb") as f:
                    cur = f.read()
                prefix_ok = cur.startswith(pre) and cur == final
                post, _, _ = read_two_col(fred_path)
                rep["prefix_byte_identical"] = prefix_ok
                rep["eol"] = repr(eol)
                rep["action"] = f"extended -> {post[-1][0]} (n={len(post)})"
                if not prefix_ok:
                    rep["status"] = "PREFIX-FAIL"
                    ok_all = False
            else:
                rep["action"] = "dry-run" if dry else "no new rows"
        report[fred_name] = rep
        print(json.dumps(rep, default=str))
    report["_meta"] = {
        "date": "2026-10-22", "dry": dry, "mode": "append-only",
        "provenance": "FRED DCOILBRENTEU/DCOILWTICO == EIA dnav RBRTEd/RWTCd "
                      "(verified identical on overlap this session, maxdev 0.0)",
        "note": "prefix bytes verbatim (cnpair bytefix precedent); tail values "
                "from fresh EIA dnav leaves committed 2026-10-16",
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=1, default=str)
    print(f"\nreport -> {REPORT} (dry={dry})")
    print("RESULT:", "ALL OK" if ok_all else "PROBLEMS")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
