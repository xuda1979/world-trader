#!/bin/bash
# TDD test for launch_all.sh idempotency guards (standup 2026-09-07).
# RED rationale: pre-guard launch_all.sh launched EVERY roster role unconditionally —
# real waste: a DONE role (HUNT_INTERNATIONAL2) was re-run all of round 1 by a leftover
# launcher; and a role with a live launcher would get a duplicate racing the same FINDINGS.
# Scenario 2 covers the 13-role COMBINED dir whose literal name is the space-joined role
# list — a per-role-only done_marker missed all 13 (real near-miss 2026-09-07, would have
# relaunched completed roles).
set -u
SCRIPT_UNDER_TEST="${SCRIPT_UNDER_TEST:?export SCRIPT_UNDER_TEST=/path/to/launch_all.sh}"
FIX=$(mktemp -d)
cleanup() { rm -rf "$FIX" "$FIX2" 2>/dev/null; }
trap cleanup EXIT
mkdir -p "$FIX/logs"
mkdir -p "$FIX/A_DONE" "$FIX/B_TODO" "$FIX/C_LIVE"
printf 'x\nROUND 1 DONE\n' > "$FIX/A_DONE/FINDINGS.md"
printf 'partial\n'     > "$FIX/B_TODO/FINDINGS.md"
printf 'A_DONE\nB_TODO\nC_LIVE\n' > "$FIX/AGENTS.txt"
cat > "$FIX/launch_agent_chief.sh" <<'STUB'
#!/bin/bash
echo "$1" >> "$FIX_LAUNCHED"
STUB
chmod +x "$FIX/launch_agent_chief.sh"
export FIX_LAUNCHED="$FIX/launched.txt"; : > "$FIX_LAUNCHED"
cat > "$FIX/proccheck" <<'STUB'
#!/bin/bash
[ "$1" = "C_LIVE" ]
STUB
chmod +x "$FIX/proccheck"

# --- scenario 1: DONE skipped, live skipped, only TODO launched ---
out=$(ROOT="$FIX" PROC_CHECK="$FIX/proccheck" STAGGER=0 ROUND=1 bash "$SCRIPT_UNDER_TEST" 2>&1)
launched=$(sort "$FIX_LAUNCHED" | tr '\n' ',')
echo "scenario1 launched: $launched"
fail=0
grep -q "skip A_DONE" "$FIX/logs/launcher.log" || { echo "FAIL: A_DONE not skipped"; fail=1; }
grep -q "skip C_LIVE" "$FIX/logs/launcher.log" || { echo "FAIL: C_LIVE (live proc) not skipped"; fail=1; }
[ "$launched" = "B_TODO," ] || { echo "FAIL: expected only B_TODO, got '$launched'"; fail=1; }

# --- scenario 2: combined-dir roster entry (shared FINDINGS.md) ---
FIX2=$(mktemp -d)
mkdir -p "$FIX2/logs"
# MUST be the exact full 13-role literal that launch_all.sh COMBINED falls back to
# (a shortened name never matches the fallback -> false-fail; caught 2026-09-07)
COMBO="HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON"
mkdir -p "$FIX2/$COMBO"
printf 'x\nROUND 1 DONE\n' > "$FIX2/$COMBO/FINDINGS.md"
mkdir -p "$FIX2/HUNT_CRYPTO2"   # per-role dir exists but has NO FINDINGS.md
printf 'HUNT_CRYPTO2\n' > "$FIX2/AGENTS.txt"
cat > "$FIX2/proccheck" <<'STUB'
#!/bin/bash
exit 1
STUB
chmod +x "$FIX2/proccheck"
out2=$(ROOT="$FIX2" PROC_CHECK="$FIX2/proccheck" STAGGER=0 ROUND=1 bash "$SCRIPT_UNDER_TEST" 2>&1)
echo "scenario2 out: $out2"
if echo "$out2" | grep -q "launch HUNT_CRYPTO2"; then
  echo "FAIL: combined-dir DONE role was relaunched"; fail=1
fi
grep -q "skip HUNT_CRYPTO2" "$FIX2/logs/launcher.log" || { echo "FAIL: combined-dir role not skipped"; fail=1; }

[ "$fail" = "0" ] && echo "PASS: launch_all skip guards (incl combined-dir)" || exit 1
