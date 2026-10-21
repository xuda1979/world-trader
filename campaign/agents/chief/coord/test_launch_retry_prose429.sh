#!/bin/bash
# TDD RED test (STANDUP 2026-09-06 22:49): a SUCCESSFUL attempt whose output merely
# MENTIONS "429" in prose (e.g. an agent reporting on rate limits) must NOT be
# classified as rate-limited and re-run. Real observed waste 2026-09-06 22:0x: the
# combined-role agent succeeded on attempt 3, but its success report contained the
# substring "429", so the launcher re-ran it attempts 4..8 (5 wasted full-charter
# runs against the rate-limited API).
# Contract: stub SUCCEEDS on attempt 1 with prose containing "429" -> invoked EXACTLY 1x.
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
echo "Round 1 executed. Note: earlier waves were blocked by API 429 rate limits; this run succeeded."
exit 0
EOS
chmod +x "$STUB"

LOG_DIR="$TMP/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/PROSE429.log"
MAXTRY=3 CLAUDE_BIN="$STUB" LOG_DIR="$LOG_DIR" bash "$ROOT/campaign/agents/chief/coord/launch_agent_chief.sh" PROSE429 1 >/dev/null 2>&1
for i in $(seq 1 60); do
  grep -q "PROSE429 round 1 end" "$LOG" && break
  sleep 1
done
sleep 1
INVOCATIONS=$(cat "$COUNT" 2>/dev/null); INVOCATIONS=${INVOCATIONS:-0}
rm -rf "$TMP"
if [ "$INVOCATIONS" -eq 1 ]; then
  echo "PASS: success-with-prose-429 not retried (1 invocation)"
  exit 0
else
  echo "FAIL: expected 1 invocation, got [$INVOCATIONS] (prose '429' in a SUCCESS output re-triggers the loop)"
  exit 1
fi
