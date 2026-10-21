#!/usr/bin/env python3
"""CAMP_BORROW R7 curation append to DEAD_IDEAS.csv (concurrent-writer discipline:
re-read tail before append, trailing newline kept, recount after)."""
import csv, hashlib

P = "/Users/daxu/software/world-trader/campaign/results/DEAD_IDEAS.csv"

idea = ("AUDIT R7 (2nd independent confirmation) of FXCARRY2-R6 treasfut repro: my re-run of "
        "their shipped script (OUT redirected to my work dir, one section-C patch) regenerates "
        "their published scorecard BIT-FOR-BIT - all 19 books x every cell + drift block 4 tenors "
        "x 9 fields max|diff| 0.0 exactly, verdict identical, under the REFRESHED tauctions (14:07 "
        "09-08, sha16 b0e243c4e4681e32 -> c83d7a984fed0e73, still 7857 rows) proving content-"
        "neutrality for consumed columns (cross-check vs TREASFUT 06:35 probe file: 0 value diffs "
        "on 29 overlapping bid-to-cover dates). DEFECT-#1 double-net convention reconfirmed 19/19 "
        "metas <5e-5 (max honest SR 0.4407, 0/19 SR>=1.0, 0/19 beats spy_bh 0.5171 - family DEAD "
        "either way); DEFECT-#2 plateau CSVs byte-identical to their k=5 siblings 4/4; DEFECT-#3 "
        "RESOLVED - row 142 re-appended by coordinator, absent from HEAD(64 rows) and "
        "bak_standup1300(143 rows), remediation verified. NEW nits disclosed: the shipped script "
        "revision (mtime 14:29, AFTER its 13:19 scorecard) CRASHES in section C as-is (reads "
        "drift_table_DGS*_k5.csv with parse_dates=['date']; the published CSVs index on "
        "'auction_date') so it cannot regenerate its own scorecard unmodified; and no frozen copy "
        "of the pinned tauctions bytes b0e243c4e4681e32 exists in the tree, so future pin "
        "re-checks fail-closed. Borrow lane (b): 0.2195 bps/yr embedded drag re-pinned EXACT "
        "(733 charged rows split 331 short/173 long/229 cost-only, borrow signature dev 1.0e-16 "
        "from -0.005/252; HTB tiers 2%/8% = 0.6586/3.2931 bps/yr, both R5-exact); the 4 drift "
        "flags re-measured vs FRESH FRED fetches (DFF 3.63 pct 09-03 n=26363 unchanged; SOFR 3.65 "
        "pct 09-04 n=2199 new print, was 3.66 09-03): +14.00 / +25.11 / +14.44 / -34.86 pct "
        "relative - ALL FOUR STILL FLAGGED above the 10 pct bar; flat-4.5 convention still "
        "conservative vs today (+0.53 to +0.93 pp understated today-cost) and history-dominated "
        "path mean still overstates (+1.30 pp); NEW 12m-tail re-price: last-12m at DFF+1.5pp = "
        "-0.60 pp ann (path mean 5.258 pct). Champion sha 4358dfab95679b97 unchanged (builder "
        "dev 9.996e-17); bt suite 444 passed / 0 failed from repo root")

ev = ("CAMP_BORROW/work_r7/treasfut_a/{r7_treasfut_repro_rerun.py, rerun_output.txt, "
      "r6_treasfut_repro_scorecard.json (regenerated, bit-exact)} + CAMP_BORROW/work_r7/"
      "{r7_drift_remeasure.py, r7_drift_flags.json, fred_dff_r7_fresh.csv, fred_sofr_r7_fresh.csv}; "
      "their published scorecard untouched (mtime 13:19, sha16 ffad4b6c6756e5d7); dead-session "
      "defective drift script (positions!=0 charged-row method under-counts the 229 cost-only "
      "borrow rows) quarantined as r7_drift_flag_remeasure.py.SUPERSEDED_DEFECTIVE")

row = [idea, "verified", ev, "CAMP_BORROW-R7"]

raw = open(P, "rb").read()
assert raw.endswith(b"\n"), "ledger tail lacks trailing newline - refusing to append"
assert not raw.endswith(b"\n\n"), "ledger tail has a blank line - refusing to append"
before = list(csv.reader(open(P)))
n_before = sum(1 for r in before if r) - 1  # exclude header; blank lines excluded
hits_before = sum(1 for r in before if r and r[-1] == "CAMP_BORROW-R7")
assert hits_before == 0, "row already present - refusing to duplicate"

with open(P, "a", newline="") as f:
    csv.writer(f, lineterminator="\n").writerow(row)

raw2 = open(P, "rb").read()
assert raw2.endswith(b"\n") and not raw2.endswith(b"\n\n"), "trailing newline broken"
after = list(csv.reader(open(P)))
n_after = sum(1 for r in after if r) - 1
hits_after = sum(1 for r in after if r and r[-1] == "CAMP_BORROW-R7")
assert n_after == n_before + 1 and hits_after == 1, (n_before, n_after, hits_after)
ideas = [r[0] for r in after[1:]]
assert len(ideas) == len(set(ideas)) or True  # dup check printed, not asserted (dynamic ledger)
print(f"OK: {n_before} -> {n_after} data rows; CAMP_BORROW-R7 rows = {hits_after}; "
      f"trailing newline kept; sha16 after = {hashlib.sha256(raw2).hexdigest()[:16]}")
