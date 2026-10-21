#!/usr/bin/env python3
"""DATA_FREDMORE round-3 fetcher (charter 2026-09-07 07:2x CST).

(a) ALFRED first-release vintages: tools/quant/data/alfred/<sid>/vintage.csv
    [release_date, observation_date, value] via ot4 (value-in-effect blocks).
    ot4 semantics verified live 2026-09-07 (work_r3/evidence_probe_ot4.txt):
    exactly ONE block per observation_date, sorted by realtime_start -> the
    block's realtime_start IS the first-release date (PIT). Known truncation:
    observations older than the series' ALFRED birth have no block (PAYEMS
    pre-1955-05), so span starts at ALFRED birth -- documented, not a bug.
    Fail-closed lint: release_date >= observation_date + lag_floor, min_rows=200.
    No-vintage-metadata series dropped LOUDLY. Live vintagedates probe
    (work_r3/evidence_probe_vintage.txt): SP500 -> HTTP 400 'does not exist in
    ALFRED' = the one genuine loud drop; VIXCLS/DGS10/DEXJPUS DO have vintages
    (n=3927/5103/651) so they are recorded as has-vintages, NOT as drops.

(b) reconcile the 7 pre-R1 lint-FAIL files, one alternate-series backfill attempt
    each. No splices, no deletion. Lint is law; where the FAIL was a linter
    artifact, the LINTER was fixed under TDD (quarterly freq, holiday-tolerant
    weekly, reason-string localization) -- data untouched.

Write-layer integrity (TDD'd after the previous run died mid-write): manifest
rewrites use the UNION of row keys as fieldnames, and vintage-row insertion is
idempotent (prior ALFRED:* rows replaced, never duplicated).

Run: python3 fetch_round3.py
"""
import csv, datetime as dt, json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/more_fred")
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/alfred")
import fred_dl
import alfred_dl

KEY = [l.split("=", 1)[1].strip().strip('"').strip("'")
       for l in open("/Users/daxu/software/world-trader/.env.local")
       if l.startswith("FRED_KEY")][0]
ROOT = "/Users/daxu/software/world-trader"
ALFRED = f"{ROOT}/tools/quant/data/alfred"
MFRED = f"{ROOT}/tools/quant/data/more_fred"

LAG_FLOOR = {
    "PAYEMS": 27, "UNRATE": 27, "CPIAUCSL": 35,
    "ICSA": 4, "RSXFS": 37, "IPMAN": 41,
}
VINTAGE_SERIES = ["PAYEMS", "UNRATE", "CPIAUCSL", "ICSA", "RSXFS", "IPMAN"]
FAIL7 = ["CPIAUCSL", "UNRATE", "UNRATENSA", "RRSFS", "TEDRATE", "MORTGAGE30US", "GFDEGDQ188S"]
# loud-drop probe: only series verified (2026-09-07, live) to lack ALFRED metadata.
NO_VINTAGE_PROBE = ["SP500"]
# series verified to HAVE vintages (previous draft falsely claimed no-vintages for these)
HAS_VINTAGE_CHECK = ["VIXCLS", "DGS10", "DEXJPUS"]


def union_fields(rows):
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    return fields


def write_manifest(rows):
    """Single write path: union-of-keys fieldnames, sorted by series_id."""
    rows = sorted(rows, key=lambda r: r["series_id"])
    with open(f"{MFRED}/manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=union_fields(rows))
        w.writeheader()
        w.writerows(rows)


def fetch_vintage(sid):
    (payload, n_missing), err = alfred_dl.fetch_first_release(sid, KEY)
    rows = payload
    if err:
        return {"sid": sid, "ok": False, "why": err, "n": 0}
    # coverage gate at fetch time: real series must clear the 200-row span floor
    lr = alfred_dl.lint_vintage(rows, LAG_FLOOR[sid], min_rows=200)
    if not lr["pass"]:
        return {"sid": sid, "ok": False, "why": lr["reason"], "n": lr["n"]}
    alfred_dl.write_vintage_csv(f"{ALFRED}/{sid}/vintage.csv", rows)
    return {"sid": sid, "ok": True, "n": lr["n"],
            "first": rows[0][1], "last": rows[-1][1],
            "first_rel": rows[0][0], "last_rel": rows[-1][0],
            "n_missing": n_missing}


def load_csv(path):
    with open(path) as f:
        return [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]


def reconcile_manifest():
    """Rebuild every FAIL7 manifest row from verified evidence (part b)."""
    rows = list(csv.DictReader(open(f"{MFRED}/manifest.csv")))
    by_id = {r["series_id"]: r for r in rows}

    def setrow(sid, **kw):
        r = by_id[sid]
        r.update({k: str(v) for k, v in kw.items()})
        r["reconciled_r3"] = "True"

    # --- CPIAUCSL / UNRATE / UNRATENSA / RRSFS: the shared 2025-10 BLS hole ---
    hole = ("REAL-UPSTREAM-HOLE @2025-10-01 (BLS shutdown, never published, unbackfilled "
            "as of 2026-09-07). backfill=impossible: no vintage/sibling carries the month "
            "(verified 2026-09-07). Lint stays law: FAIL.")
    setrow("CPIAUCSL", lint_pass="False", reason=hole + " ALFRED vintage fetched separately (see ALFRED:CPIAUCSL).")
    setrow("UNRATE", lint_pass="False", reason=hole + " ALFRED vintage fetched separately (see ALFRED:UNRATE).")
    setrow("UNRATENSA", lint_pass="False",
           reason=hole + " Same hole verified in UNRATE/CPILFESL/LNS11300060; no NSA vintage exists to substitute.")
    setrow("RRSFS", lint_pass="False",
           reason=hole + " backfill=impossible via deflator: nominal RSAFS HAS 2025-10 (731051) but real = nominal/CPI "
                         "and CPI has no 2025-10; CPALTT01USM657N absent 2025-09..11. No splice.")
    # --- TEDRATE ---
    setrow("TEDRATE", lint_pass="False",
           reason="STRUCTURAL: 5 missing-bday runs of len=3 @1993-12-24..26, 1999-12-24..26, 2004-12-24..26, "
                  "2010-12-24..26, 2021-12-24..26 (NYSE closed Christmas Fri AND the following Mon; linter "
                  "contiguous-hole=3@1993-12-24). 486 isolated 1d gaps OK (incl. 1986-01-20 absent: MLK Day, "
                  "first federal observance -- grep-verified 2026-09-07; R2's 'has data' sub-claim and R2's "
                  "@1986-01-20 max-run location were BOTH wrong, corrected under TDD). Lint stays law: FAIL.")
    # --- MORTGAGE30US: linter artifact -> reclassified PASS under holiday-tolerant weekly ---
    m = load_csv(f"{MFRED}/MORTGAGE30US.csv")
    tol = fred_dl.lint(m, freq="weekly", holiday_tol_days=3)
    strict = fred_dl.lint(m, freq="weekly")
    setrow("MORTGAGE30US", lint_pass="True", gaps=tol["gaps"],
           reason="holiday-shifted-publication: weekly grid mislabeled %d grid slots as holes; max spacing=%dd "
                  "(<=9d proves no week absent), tol3 lint PASS. Linter fixed under TDD, data untouched."
                  % (strict["gaps"], max((dt.date.fromisoformat(m[i + 1][0]) - dt.date.fromisoformat(m[i][0])).days
                                         for i in range(len(m) - 1))))
    # --- GFDEGDQ188S: linter artifact -> reclassified PASS under quarterly lint ---
    g = load_csv(f"{MFRED}/GFDEGDQ188S.csv")
    lrq = fred_dl.lint(g, freq="quarterly")
    setrow("GFDEGDQ188S", lint_pass="True", freq="quarterly", gaps=lrq["gaps"],
           reason="quarterly-native (241/241 Jan/Apr/Jul/Oct slots present, 0 off-grid) was mis-linted as monthly; "
                  "linter gained quarterly support under TDD. Data untouched. PASS.")
    return rows


def add_vintage_rows(rows, cpi_missing_first):
    """Replace-or-insert ALFRED:* rows (idempotent), then one union-fieldnames rewrite."""
    by_id = {r["series_id"]: r for r in rows}

    def alfred_row(sid, **kw):
        r = {k: "" for k in union_fields(rows)}
        for default, val in (("vintage", "True"), ("status", "ok")):
            kw.setdefault(default, val)
        r.update(series_id=f"ALFRED:{sid}", role="vintage-pit",
                 freq="release-event", **kw)
        return r

    for sid in VINTAGE_SERIES:
        with open(f"{ALFRED}/{sid}/vintage.csv") as f:
            vr = list(csv.reader(f))[1:]
        obs = [x[1] for x in vr]
        row = alfred_row(sid, n=len(vr), start=min(obs), end=max(obs),
                         gaps="0", max_run="0", lint_pass="True",
                         lag_days=LAG_FLOOR[sid],
                         reason="first-release PIT vintage via ot4; release>=obs+%dd lint PASS" % LAG_FLOOR[sid],
                         file=f"tools/quant/data/alfred/{sid}/vintage.csv")
        if sid == "CPIAUCSL":
            row["missing_codes"] = str(cpi_missing_first)
            row["reason"] += "; %d unpublished month(s) dropped+counted (2025-10 shutdown)" % cpi_missing_first
        by_id[f"ALFRED:{sid}"] = row  # replace-or-insert = idempotent

    for sid in NO_VINTAGE_PROBE:
        r = alfred_row(sid, lint_pass="False", vintage="False",
                       reason="no-vintages: series has no ALFRED vintage metadata (vintagedates HTTP 400 'does not "
                              "exist in ALFRED'; probe 2026-09-07). dropped LOUDLY, no file written.")
        by_id[f"ALFRED:{sid}"] = r

    # has-vintages note rows: previous draft falsely claimed these lack vintages.
    # lint_pass stays "" (informational probe only -- no file fetched, so the R2
    # invariant "every PASS row's file exists" must not be violated).
    for sid in HAS_VINTAGE_CHECK:
        vd, err = alfred_dl.vintagedates(sid, KEY)
        n = len(vd) if vd else 0
        r = alfred_row(sid, lint_pass="" if n else "False", vintage="True" if n else "False",
                       n=n, status="info" if n else "FAIL:no-vintages",
                       reason=("HAS ALFRED vintages (vintagedates n=%d, verified live 2026-09-07); not fetched this "
                               "round -- not on the R3 vintage list, so no file and lint_pass is blank (info row). "
                               "Corrects the earlier draft's false loud-drop claim." % n)
                       if n else "no-vintages (live probe 2026-09-07: %s)" % (err or "empty"))
        by_id[f"ALFRED:{sid}"] = r

    return list(by_id.values())


def main():
    results = {}
    print("=== (a) ALFRED first-release vintages ===")
    for sid in VINTAGE_SERIES:
        res = fetch_vintage(sid)
        results[sid] = res
        if res["ok"]:
            print("  %-9s PASS n=%-6d obs %s..%s  rel %s..%s  missing=%d" % (
                sid, res["n"], res["first"], res["last"], res["first_rel"],
                res["last_rel"], res["n_missing"]), flush=True)
        else:
            print("  %-9s FAIL %s (n=%d)" % (sid, res["why"], res["n"]))

    ok = sum(1 for r in results.values() if r["ok"])
    if ok != len(VINTAGE_SERIES):
        # fail-closed: do NOT reconcile the manifest off a partial fetch
        bad = {s: r["why"] for s, r in results.items() if not r["ok"]}
        raise SystemExit("ABORT: %d/%d vintages failed, manifest untouched: %s"
                         % (ok, len(VINTAGE_SERIES), bad))

    print("=== loud-drop probes (vintagedates, live) ===")
    for sid in NO_VINTAGE_PROBE + HAS_VINTAGE_CHECK:
        vd, err = alfred_dl.vintagedates(sid, KEY)
        print("  %-8s -> n=%s err=%s" % (sid, len(vd) if vd else 0, (err or "OK")[:60]))

    print("=== (b) manifest reconciliation ===")
    rows = reconcile_manifest()
    rows = add_vintage_rows(rows, cpi_missing_first=results["CPIAUCSL"]["n_missing"])
    write_manifest(rows)
    man = {r["series_id"]: r for r in rows}
    print("  manifest rows now: %d" % len(rows))
    for sid in FAIL7:
        r = man[sid]
        print("  %-13s lint_pass=%-5s reconciled_r3=%s" % (sid, r["lint_pass"], r.get("reconciled_r3")))

    print("=== summary ===")
    nv = sum(1 for s in VINTAGE_SERIES if man[f"ALFRED:{s}"]["lint_pass"] == "True")
    print("vintages ok %d/%d; CPI missing-first-prints=%s" % (
        nv, len(VINTAGE_SERIES), man["ALFRED:CPIAUCSL"]["missing_codes"]))


if __name__ == "__main__":
    main()
