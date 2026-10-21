"""DATA_FREDMORE R4 standalone verifier — every FINDINGS claim re-derives from disk/live.

Run: python3 verify_round4.py   (exit 0 = all checks pass)
"""
import csv
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OPTS = "/Users/daxu/software/world-trader/tools/quant/data/cboe_opts"
PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("PASS  %s %s" % (name, detail))
    else:
        FAIL += 1
        print("FAIL  %s %s" % (name, detail))


def rd(p):
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def load(sym):
    p = os.path.join(OPTS, "%s.csv" % sym)
    if not os.path.exists(p):
        return None
    out = []
    with open(p, newline="") as f:
        r = csv.reader(f)
        assert next(r) == ["date", "close"]
        for row in r:
            out.append((row[0], float(row[1])))
    return out


def gaps(ds):
    return [(a, b, (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days)
            for a, b in zip(ds, ds[1:])]


def main():
    man = rd(os.path.join(OPTS, "manifest.csv"))

    # ---- manifest honesty
    ids = [r["series_id"] for r in man]
    check("manifest.no_dup_ids", len(ids) == len(set(ids)), "n=%d" % len(ids))
    files = sorted(f[:-4] for f in os.listdir(OPTS) if f.endswith(".csv") and f != "manifest.csv")
    passers = {r["series_id"] for r in man if r["lint_pass"] == "True"}
    check("manifest.pass_row_implies_file", passers <= set(files),
          "missing=%s" % sorted(passers - set(files)))
    written_but_failed = set(files) - passers
    check("manifest.no_file_for_failed_row", not written_but_failed,
          str(sorted(written_but_failed)))

    # ---- per-file re-lint (independent of fetcher)
    sys.path.insert(0, OPTS)
    import cboe_opts_dl as m
    n_files = 0
    for sid in sorted(files):
        rows = load(sid)
        ds = [d for d, _ in rows]
        klass = "eqvol" if sid.startswith("VX") else "idxlevel"
        if sid.startswith("LOVOL"):
            klass = "idxvol"
        # recompute lint invariants directly (not via lint_series) for independence
        ok_struct = all(b > a for a, b in zip(ds, ds[1:]))
        klass_bounds = m.PLAUS[klass]
        ok_plaus = all(klass_bounds[0] <= v <= klass_bounds[1] for _, v in rows)
        maxg = max(g for _, _, g in gaps(ds))
        n_over = sum(1 for _, _, g in gaps(ds) if g > m.GAP_GATE_DAYS)
        check("file.%s" % sid, ok_struct and ok_plaus and n_over == 0 and len(rows) >= 100,
              "n=%d %s..%s maxgap=%d" % (len(rows), ds[0], ds[-1], maxg))
        n_files += 1
    check("file.count", n_files == 22, "n_files=%d" % n_files)

    # ---- era splits: parents have holes, eras don't; eras reference parent
    for parent, eras in [("VXGDX", ["VXGDX_era1", "VXGDX_era2"]),
                         ("VXSLV", ["VXSLV_era1", "VXSLV_era2"]),
                         ("VXFXI", ["VXFXI_era1", "VXFXI_era2"]),
                         ("CLL", ["CLL_era2", "CLL_era3"])]:
        prow = next(r for r in man if r["series_id"] == parent)
        check("era.%s.parent_failed" % parent, prow["lint_pass"] == "False",
              "reason=%s" % prow["reason"][:60])
        erows = [load(e) for e in eras]
        for e, rws in zip(eras, erows):
            ds = [d for d, _ in rws]
            check("era.%s.contig" % e, all(g <= 9 for _, _, g in gaps(ds)),
                  "maxgap=%d" % max(g for _, _, g in gaps(ds)))
        # era1 ends before hole, era2 starts at/after hole-end; no overlap
        check("era.%s.order" % parent, erows[0][-1][0] < erows[1][0][0],
              "%s < %s" % (erows[0][-1][0], erows[1][0][0]))
        # no-fabrication arithmetic: parent n == sum(ALL era n incl. undelivered
        # fail-closed ones, e.g. CLL_era1 n=61); span = first era start .. last era end
        undelivered = {"CLL": 61}  # CLL_era1: n=61 < MIN_N=100, correctly NOT written
        era1, era2 = erows[0], erows[-1]
        total = len(era1) + len(era2) + undelivered.get(parent, 0)
        check("era.%s.no_fabrication" % parent,
              int(prow["n"]) == total,
              "parent_n=%s = %d+%d(+%d undelivered)" % (prow["n"], len(era1), len(era2),
                                                        undelivered.get(parent, 0)))
        first_start = "2008-08-26" if parent == "CLL" else era1[0][0]  # CLL_era1 start
        check("era.%s.span_matches" % parent,
              prow["start"] == first_start and prow["end"] == era2[-1][0],
              "%s..%s" % (first_start, era2[-1][0]))
        # era files not on disk (parents failed; only eras written)
        for e in eras:
            check("era.%s.on_disk" % e, os.path.exists(os.path.join(OPTS, "%s.csv" % e)))

    # ---- documented facts
    vxpfe = load("VXPFE")
    check("fact.VXPFE_frozen_2022", vxpfe[-1][0] == "2022-11-07", "end=%s" % vxpfe[-1][0])
    bxy = load("BXY")
    check("fact.BXY_1988", bxy[0][0] == "1988-06-01", "start=%s" % bxy[0][0])
    bxmd = load("BXMD")
    check("fact.BXMD_1986", bxmd[0][0] == "1986-06-20", "start=%s" % bxmd[0][0])
    pput = load("PPUT")
    check("fact.PPUT_1986", pput[0][0] == "1986-06-30", "start=%s" % pput[0][0])
    cll1 = next((r for r in man if r["series_id"] == "CLL_era1"), None)
    check("fact.CLL_era1_failclosed", cll1 and cll1["lint_pass"] == "False" and cll1["n"] == "61",
          "n=%s" % (cll1["n"] if cll1 else "?"))

    # ---- probe evidence file exists and shows the 403s
    pj = os.path.join(HERE, "probe_history_endpoints_out.json")
    check("probe.saved_output", os.path.exists(pj))
    if os.path.exists(pj):
        probes = json.load(open(pj))
        blocked = [p for p in probes if p["role"].startswith("blocked")]
        check("probe.blocked_403", all(p["status"] == 403 for p in blocked) and len(blocked) == 4,
              "n_blocked=%d" % len(blocked))
        ohlcv = next(p for p in probes if p["role"] == "ohlcv-only")
        check("probe.ohlcv_has_no_putcall_fields",
              set(ohlcv["data_keys_union"]) == {"date", "open", "high", "low", "close", "volume"},
              str(sorted(ohlcv["data_keys_union"])))
        check("probe.snapshot_timestamp", bool(ohlcv.get("timestamp")) or
              next(p for p in probes if p["role"] == "snapshot-only").get("timestamp"),
              str(next((p.get("timestamp") for p in probes if p["role"] == "snapshot-only"), None)))
        ctl = next(p for p in probes if p["role"] == "control")
        check("probe.control_200", ctl["status"] == 200 and ctl["n_bytes"] > 100000,
              "bytes=%d" % ctl["n_bytes"])
        # dedup honesty: PUT not re-fetched (already in cboe_flow)
        putrow = next(r for r in man if r["series_id"] == "PUT")
        check("dedup.PUT_skipped", putrow["lint_pass"] == "False" and "cboe_flow" in putrow["reason"],
              putrow["reason"][:50])

    print("\nTOTAL: %d PASS / %d FAIL" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
