#!/usr/bin/env python3
"""DATA_FREDMORE round-2 fetcher (charter 2026-09-07).

(a) must-fetch list: BAMLH0A0HYM2 full-history repair, DEX*/DTWEXBGS FX dailies,
    RSAFS; verify-only for already-present T10YIE/UMCSENT/HOUST/PERMIT/USREC/CPIAUCSL.
(b) legit retry of R1 fail IRLTLT01NZM156N via start-trim (1979-10-01, R1 VIXCLS
    precedent for publish holes). No splices.

All writes go through fred_dl.lint (fail-closed): only PASS written to
tools/quant/data/more_fred/{id}.csv. Manifest merge semantics identical to
run_more_fred.py. Verify/structural evidence -> verify_structural.py.
"""
import sys, os, csv, shutil
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/tools/quant/data/more_fred")
import fred_dl

OUT = f"{ROOT}/tools/quant/data/more_fred"
WORK = os.path.dirname(os.path.abspath(__file__))


def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("FRED_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no FRED_KEY")


# (series_id, role, expected_freq, observation_start or None)
# Head-trim precedent = R1 VIXCLS: trim at genuine publish/closure holes only, no splices.
#   DEXJPUS 11bd hole @1971-08-16 (post-Nixon-shock FX closure) -> 1971-08-31
#   DEXUSUK  5bd hole @1971-08-16 (same closure)                -> 1971-08-23
#   DTWEXBGS 4bd @2010-02-08 + 3bd @2016-01-22 (Fed Board blizzard closures, MID-SERIES)
#     -> only clean trim is 2016-01-27 (loses 2010-2015; alternative is permanent fail)
# BAMLH0A0HYM2: refetch keeps the 3y licensing window (FRED policy Apr-2026, family-wide),
#   intentionally NOT labeled a repair -- it is the legitimate maximum from this source.
# TWEXBMTH: monthly broad dollar index 1973-2019 full history, zero holes (discontinued).
SERIES = [
    ("BAMLH0A0HYM2",     "hy-oas-3y-window",   "daily",   None),
    ("DEXUSEU",          "fx-eurusd",          "daily",   None),
    ("DEXJPUS",          "fx-usdjpy",          "daily",   "1971-08-31"),
    ("DEXCAUS",          "fx-usdcad",          "daily",   None),
    ("DEXUSUK",          "fx-usdgbp",          "daily",   "1971-08-23"),
    ("DTWEXBGS",         "dollar-index-daily", "daily",   "2016-01-27"),
    ("TWEXBMTH",         "dollar-index-monthly","monthly", None),
    ("RSAFS",            "retail-sales",       "monthly", None),
    ("IRLTLT01NZM156N",  "nz-long-rate-trim",  "monthly", "1979-10-01"),
]

results = []
for sid, role, want_freq, start in SERIES:
    t0_label = sid
    (rows, nmiss), err = fred_dl.fetch(sid, key(), start=start)
    rec = {"series_id": sid, "role": role, "status": "", "freq": "", "n": 0,
           "start": "", "end": "", "missing_codes": nmiss if nmiss is not None else 0,
           "gaps": 0, "max_run": 0, "lint_pass": False, "reason": "", "file": ""}
    if err is not None:
        rec["status"] = "FAIL:" + err
        results.append(rec)
        print("%-18s %s" % (t0_label, rec["status"]), flush=True)
        continue
    freq = fred_dl.detect_freq(rows)
    rec["freq"] = freq
    lr = fred_dl.lint(rows, freq=freq if freq != "unknown" else want_freq)
    rec.update(n=lr["n"], start=lr["start"] or "", end=lr["end"] or "",
               gaps=lr.get("gaps", 0), max_run=lr.get("max_run", 0),
               lint_pass=lr["pass"], reason=lr["reason"])
    rec["status"] = "ok"
    if lr["pass"]:
        # BAMLH repair: back up truncated file, verify overlap-identical before overwrite
        if sid == "BAMLH0A0HYM2":
            bak = os.path.join(WORK, "BAMLH0A0HYM2.truncated.bak.csv")
            if os.path.exists(os.path.join(OUT, sid + ".csv")):
                shutil.copy2(os.path.join(OUT, sid + ".csv"), bak)
                with open(bak) as f:
                    old = {r[0]: float(r[1]) for r in list(csv.reader(f))[1:]}
                new = dict(rows)
                common = sorted(set(old) & set(new))
                diffs = [(d, old[d], new[d]) for d in common if abs(old[d] - new[d]) > 1e-9]
                print("  overlap: %d dates, value-diffs=%d, maxdiff=%.6f" % (
                    len(common), len(diffs), max((abs(a - b) for _, a, b in diffs), default=0.0)))
                if len(common) < len(old):
                    print("  WARN: %d old dates dropped from new payload" % (len(old) - len(common)))
        with open(os.path.join(OUT, sid + ".csv"), "w", newline="") as f:
            fred_dl.write_csv(f, rows, sid)
        rec["file"] = sid + ".csv"
    print("%-18s %-6s n=%-6d %s..%s gaps=%-4d maxrun=%-3s miss=%d %s [%s]" % (
        sid, "PASS" if lr["pass"] else "FAIL", lr["n"], lr["start"], lr["end"],
        lr.get("gaps", 0), lr.get("max_run", "-"), nmiss, lr["reason"], freq), flush=True)
    results.append(rec)

# manifest merge — same semantics as run_more_fred.py (update-in-place, sorted)
mfn = os.path.join(OUT, "manifest.csv")
existing = {}
if os.path.exists(mfn):
    with open(mfn) as f:
        for row in csv.DictReader(f):
            existing[row["series_id"]] = row
for rec in results:
    existing[rec["series_id"]] = {
        "series_id": rec["series_id"], "role": rec["role"], "status": rec["status"],
        "freq": rec["freq"], "n": rec["n"], "start": rec["start"], "end": rec["end"],
        "missing_codes": rec["missing_codes"], "gaps": rec["gaps"], "max_run": rec["max_run"],
        "lint_pass": rec["lint_pass"], "reason": rec["reason"], "file": rec["file"]}
with open(mfn, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["series_id","role","status","freq","n","start","end",
        "missing_codes","gaps","max_run","lint_pass","reason","file"])
    w.writeheader()
    for sid in sorted(existing):
        w.writerow(existing[sid])
npass = sum(1 for r in results if r["lint_pass"])
print("manifest rows: %d | this run: %d attempted, %d PASS, %d FAIL" % (
    len(existing), len(results), npass, len(results) - npass))

# ---- manifest reconciliation: lint is law against DISK reality ----
# 1) every on-disk CSV gets its verdict re-linted at detected freq (fixes rows that
#    claimed lint_pass=True on files that actually fail, backfills R1 rows never merged)
# 2) permanent structural fails (never written) get explicit fail rows with evidence
recon_fixed = []
for fn in sorted(os.listdir(OUT)):
    if not fn.endswith(".csv") or fn == "manifest.csv":
        continue
    sid = fn[:-4]
    with open(os.path.join(OUT, fn)) as f:
        rows = [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]
    fq = fred_dl.detect_freq(rows)
    lr = fred_dl.lint(rows, freq=fq if fq != "unknown" else "monthly")
    want = "True" if lr["pass"] else "False"
    reason = lr["reason"]
    if sid == "CPIAUCSL":
        reason = "REAL-UPSTREAM-HOLE: BLS published no Oct-2025 CPI (govt shutdown); " \
                 "verified '.' in raw FRED payload 2026-09-07 -> fail-closed, no splice"
    row = existing.get(sid, {"series_id": sid, "role": "", "status": "ok", "file": fn,
                             "missing_codes": ""})
    if str(row.get("lint_pass")) != want:
        recon_fixed.append((sid, row.get("lint_pass"), want))
    # preserve a prior informative reason when the verdict is unchanged (e.g. UMCSENT
    # trim note); fresh "ok" otherwise or when the verdict flipped
    if not (want == "True" and str(row.get("lint_pass")) == want
            and row.get("reason") and row.get("reason") != "ok"):
        row["reason"] = reason
    row.update({"freq": fq, "n": lr["n"], "start": lr["start"] or "", "end": lr["end"] or "",
                "gaps": lr.get("gaps", 0), "max_run": lr.get("max_run", 0),
                "lint_pass": want, "status": "ok", "file": fn})
    existing[sid] = row

PERM_FAILS = [
    ("NROU", "quarterly+forecast-rows-to-2036: unusable as history (R1 gaps=702 vs monthly "
             "grid); permanent fail, no splice", "R1"),
    ("LNS11300060", "gaps=1 @2025-10-01 (BLS shutdown, verified '.' in raw payload "
                    "2026-09-07); monthly zero-tolerance -> permanent fail", "R1"),
    ("CPILFESL", "gaps=1 @2025-10-01 (BLS shutdown, verified '.' in raw payload "
                 "2026-09-07); monthly zero-tolerance -> permanent fail", "R1"),
    ("BAMLH0A0HYM2-FULL-HISTORY", "FRED policy Apr-2026: ICE BofA family truncated to 3y "
             "(series notes; obs_start=2023-09-05 family-wide; ALFRED has no older "
             "vintages). Pre-2023 history only via paid ICE source -> permanent fail "
             "here; 3y window kept as BAMLH0A0HYM2", "R2"),
    ("DTWEXBGS-FULL", "mid-series Fed Board closures 4bd@2010-02-08 + 3bd@2016-01-22; "
             "not head-trimmable -> full-span daily is a permanent fail; trimmed "
             "2016-01-27.. kept as DTWEXBGS; discontinued DTWEXB has identical holes", "R2"),
]
for sid, why, rnd in PERM_FAILS:
    if sid not in existing or existing[sid].get("lint_pass") != "False":
        recon_fixed.append((sid, existing.get(sid, {}).get("lint_pass"), "False"))
    existing[sid] = {"series_id": sid, "role": "structural-fail", "status": "FAIL:structural",
                     "freq": "daily" if "DTWEXBGS" in sid else ("monthly" if sid != "NROU" else "quarterly"),
                     "n": 0, "start": "", "end": "", "missing_codes": 0, "gaps": 0,
                     "max_run": 0, "lint_pass": "False", "reason": why, "file": ""}

with open(mfn, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["series_id","role","status","freq","n","start","end",
        "missing_codes","gaps","max_run","lint_pass","reason","file"])
    w.writeheader()
    for sid in sorted(existing):
        w.writerow(existing[sid])
print("reconciliation: %d verdict corrections" % len(recon_fixed))
for sid, was, now in recon_fixed:
    print("  %-28s %s -> %s" % (sid, was, now))
print("manifest final rows: %d (PASS %d / FAIL %d)" % (
    len(existing),
    sum(1 for r in existing.values() if r["lint_pass"] == "True"),
    sum(1 for r in existing.values() if r["lint_pass"] != "True")))
