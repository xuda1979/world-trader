#!/bin/bash
# TDD test for launch_agent_chief.sh retry logic.
# Contract: a run that SUCCEEDS must terminate the retry loop immediately,
# even if the log already contains an OLD 429 from a previous attempt.
# pass condition: claude stub invoked EXACTLY 2 times (1x 429 + 1x success).
set -u
ROOT=/Users/daxu/software/world-trader
TMP=$(mktemp -d)
STUB="$TMP/fakebin/claude"
mkdir -p "$(dirname "$STUB")"
COUNT="$TMP/count"
: > "$COUNT"
cat > "$STUB" <<EOS
#!/bin/bash
n=0
[ -f "$COUNT" ] && n=\$(cat "$COUNT")
n=\$((n+1))
echo "\$n" > "$COUNT"
if [ "\$n" -le 1 ]; then
  echo "API Error: Request rejected (429) - rate limit"
  exit 0
fi
echo "stub success"
exit 0
EOS
chmod +x "$STUB"

LOG_DIR="$TMP/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/TDD_RETRY_TEST.log"
# Seed the log with a STALE 429 from a PREVIOUS attempt: a compliant retry loop
# must NOT let that old line trigger a pointless re-run after a real success.
echo "=== stale line from previous attempt: Request rejected (429) - rate limit ===" > "$LOG"
CLAUDE_BIN="$STUB" LOG_DIR="$LOG_DIR" bash "$ROOT/campaign/agents/chief/coord/launch_agent_chief.sh" TDD_RETRY_TEST 1 >/dev/null 2>&1
for i in $(seq 1 120); do
  grep -q "TDD_RETRY_TEST round 1 end" "$LOG" && break
  sleep 1
done
sleep 1
INVOCATIONS=$(cat "$COUNT" 2>/dev/null); INVOCATIONS=${INVOCATIONS:-0}
rm -rf "$TMP"
if [ "$INVOCATIONS" -eq 2 ]; then
  echo "PASS: claude invoked exactly 2 times (1x 429, 1x success)"
  exit 0
else
  echo "FAIL: expected 2 invocations, got [$INVOCATIONS] (stale-429 grep re-runs successful rounds, or CLAUDE_BIN ignored)"
  exit 1
fi
