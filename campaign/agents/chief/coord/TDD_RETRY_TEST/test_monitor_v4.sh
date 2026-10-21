#!/bin/bash
# TDD for monitor.sh v4 (2026-09-07): round-aware DONE + exact tail marker + work-file freshness.
# Regressions encoded here (both REAL failures):
#  T3 family (07:04:04 snapshot): v3 substring-grepped "ROUND 1 DONE" and credited the
#    round-1 combined FINDINGS to 13 roles forever -> marked all 20 DONE while 3 agents
#    were mid-round-2. v4: DONE iff effective FINDINGS LAST LINE == "ROUND ${ROUND}DONE".
#  T9 (07:19:42): v4.0 called AUDIT_FWBUGS BLOCKED while it was alive mid-attempt, because
#    the launcher writes its log only at attempt boundaries. v4.1: a fresh file anywhere
#    under the role dir (excl. FINDINGS.md) also proves RUNNING.
set -u
COORD="$(cd "$(dirname "$0")/.." && pwd)"
MON="${MON:-$COORD/monitor_v4.sh}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/logs"
ROLES="HUNT_COT2 CAMP_SHORT HUNT_CRYPTO2 CAMP_BORROW AUDIT_RECON TDD_BLOCKED_TEST"
for r in $ROLES; do mkdir -p "$TMP/$r"; done
COMBINED="HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON"
mkdir -p "$TMP/$COMBINED"
printf '%s\n' $ROLES > "$TMP/AGENTS.txt"

FRESH=202609071200   # noon = "now" relative to test run
STALE=202401010000
mklog() { echo x > "$TMP/logs/$1.log"; touch -t "$2" "$TMP/logs/$1.log"; }

# T1: per-role tail ROUND 2 DONE + fresh log -> DONE wins at ROUND=2
printf 'work...\nROUND 2 DONE\n' > "$TMP/HUNT_COT2/FINDINGS.md"
mklog HUNT_COT2 "$FRESH"
# T4: no findings, fresh log -> RUNNING
mklog CAMP_SHORT "$FRESH"
# T3 (REGRESSION): combined role, combined tail ROUND 1 DONE, stale log -> BLOCKED at ROUND=2
printf 'old wave\nROUND 1 DONE\n' > "$TMP/$COMBINED/FINDINGS.md"
mklog HUNT_CRYPTO2 "$STALE"
# T3b: second combined role, same combined file -> BLOCKED at ROUND=2
mklog CAMP_BORROW "$STALE"
# T7+T9 (REGRESSION): prose-only marker (junk tail -> not DONE), stale log, but FRESH
# work file under the role dir -> RUNNING
printf 'we will write ROUND 2 DONE later\njunk last line\n' > "$TMP/AUDIT_RECON/FINDINGS.md"
mklog AUDIT_RECON "$STALE"
mkdir -p "$TMP/AUDIT_RECON/work"
echo "partial" > "$TMP/AUDIT_RECON/work/mutate3.py"
# T10: no findings, stale log, no work files -> BLOCKED (fail-closed)
mklog TDD_BLOCKED_TEST "$STALE"

ROOT="$TMP" ROUND=2 LOG_TTL_SECS=900 ONE_SHOT=1 bash "$MON" > "$TMP/hist_r2.txt"
ROOT="$TMP" ROUND=1 LOG_TTL_SECS=900 ONE_SHOT=1 bash "$MON" > "$TMP/hist_r1.txt"

pass=0; fail=0
ck() { if grep -Eq "$2" "$1"; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: $3"; fi; }

ck "$TMP/hist_r2.txt" "^  HUNT_COT2 +DONE$"        "T1 per-role ROUND 2 DONE -> DONE"
ck "$TMP/hist_r2.txt" "^  CAMP_SHORT +RUNNING$"    "T4 fresh log, no findings -> RUNNING"
ck "$TMP/hist_r2.txt" "^  HUNT_CRYPTO2 +BLOCKED$"  "T3 REGRESSION r1-combined file must NOT be DONE at ROUND=2"
ck "$TMP/hist_r2.txt" "^  CAMP_BORROW +BLOCKED$"   "T3b same for second combined role"
ck "$TMP/hist_r2.txt" "^  AUDIT_RECON +RUNNING$"   "T9 REGRESSION prose marker+stale log+fresh work -> RUNNING (not DONE, not BLOCKED)"
ck "$TMP/hist_r2.txt" "^  TDD_BLOCKED_TEST +BLOCKED$" "T10 fully stale, no findings -> BLOCKED (fail-closed)"
ck "$TMP/hist_r2.txt" "round=2"                    "T8 snapshot header records which ROUND was checked"
ck "$TMP/hist_r1.txt" "^  CAMP_BORROW +DONE$"      "T6 ROUND=1 backward compat on combined file"
ck "$TMP/hist_r1.txt" "^  HUNT_COT2 +RUNNING$"     "T4b ROUND=1 log fall-through (non-combined, r2 tail)"

echo "test_monitor_v4: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
