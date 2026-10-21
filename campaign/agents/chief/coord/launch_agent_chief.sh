#!/bin/bash
# CHIEF-ORCHESTRATED parallel agent launcher (works in this sandbox: explicit binary + env)
# usage: launch_agent_chief.sh <agent_name> <round>
AGENT=$1; ROUND=${2:-1}
CLAUDE_BIN="${CLAUDE_BIN:-/Users/daxu/homebrew/bin/claude}"
ROOT=/Users/daxu/software/world-trader
LOG_DIR="${LOG_DIR:-$ROOT/campaign/agents/chief/coord/logs}"
LOG="$LOG_DIR/$AGENT.log"
mkdir -p "$LOG_DIR"
export CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=
export ANTHROPIC_API_KEY="cf1c73d79c9448dda0848a009b5d5bca.JeLss5V8ebvwSmzT"
export ANTHROPIC_AUTH_TOKEN="cf1c73d79c9448dda0848a009b5d5bca.JeLss5V8ebvwSmzT"
export ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"
export ANTHROPIC_MODEL="GLM-5.3-Flash"
export ANTHROPIC_SMALL_FAST_MODEL="GLM-5.3-Flash"
{
  echo "=== $AGENT round $ROUND start $(date) ==="
  # Retry-on-429 with exponential backoff (LAUNCHED 20-at-once -> 13/20 hit rate limit).
  # Each attempt is judged on ITS OWN output only (ATTEMPT_LOG) — never the whole
  # transcript, or a stale 429 from a previous attempt re-triggers the loop forever.
  MAXTRY="${MAXTRY:-8}"
  ATTEMPT_LOG="$LOG_DIR/.${AGENT}.attempt.$$"
  for attempt in $(seq 1 $MAXTRY); do
    "$CLAUDE_BIN" -p --dangerously-skip-permissions \
      --append-system-prompt "You are research agent $AGENT in the GOAL100 multi-agent hedge-fund research campaign at /Users/daxu/software/world-trader. Work autonomously with shell+python3 heredocs. Be brutally honest; a sleeve/cycle passes ONLY if it survives every gate in your charter. Do not spawn sub-agents. Never modify other agents' directories or the committed champion without explicit instruction. Use TDD (failing test first) for any framework bug. Log all attempts + exact numbers to your FINDINGS.md." \
      "Read /Users/daxu/software/world-trader/campaign/agents/chief/coord/$AGENT/CHARTER.md. Execute round $ROUND per charter. Append a summary (what tried, what passed/failed with exact numbers, evidence from actual command output) to /Users/daxu/software/world-trader/campaign/agents/chief/coord/$AGENT/FINDINGS.md. End the last line of that FINDINGS.md with exactly: ROUND $ROUND DONE" \
      > "$ATTEMPT_LOG" 2>&1
    rc=$?
    cat "$ATTEMPT_LOG" >> "$LOG"
    # A COMPLETED attempt is decided by absence of API-error markers, with rc as a
    # required condition (claude emits 429s with exit 0, so rc alone can't decide;
    # and a success report may legitimately MENTION "429" in prose — real waste
    # 2026-09-06 22:0x: a succeeded agent was re-run 5x by the substring match).
    if [ "$rc" -eq 0 ] && ! grep -q "API Error\|速率限制" "$ATTEMPT_LOG" 2>/dev/null; then
      echo "=== $AGENT round $ROUND end $(date) exit $rc ===" >> "$LOG"
      break
    fi
    echo "=== $AGENT rate-limited or errored (attempt $attempt, rc=$rc); backing off ===" >> "$LOG"
    sleep $((30 * attempt))
  done
  rm -f "$ATTEMPT_LOG"
} &
echo "launched $AGENT (pid $!)"
