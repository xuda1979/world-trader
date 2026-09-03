#!/bin/bash
# Launch 5 ITER6 agents IN PARALLEL (backgrounded). Each writes its own LOG + FINDINGS.
cd /Users/daxu/software/world-trader
AGENTS=(loop_team/SKILL_ALPHAAGB_B loop_team/HUNT_FXDEPO loop_team/HUNT_CROSSASSET2 loop_team/HUNT_VOLOVERLAY loop_team/AUDIT_V3)
export ANTHROPIC_API_KEY="cf1c73d79c9448dda0848a009b5d5bca.JeLss5V8ebvwSmzT"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"
export ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"
export ANTHROPIC_MODEL="GLM-5.3-Flash"
export ANTHROPIC_SMALL_FAST_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_SONNET_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_OPUS_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="GLM-5.3-Flash"
export CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=
PIDS=()
for AGENT in "${AGENTS[@]}"; do
  mkdir -p "campaign/agents/$AGENT"
  LOG="campaign/agents/$AGENT/LOG_iter6.log"
  echo "=== $AGENT start $(date) ===" >> "$LOG"
  claude -p --dangerously-skip-permissions \
    --append-system-prompt "You are research agent $AGENT in the GOAL100 multi-agent quant campaign (project /Users/daxu/software/world-trader). Work autonomously with shell+python3 heredocs. Be brutally honest; reject anything failing gates; never fabricate. Strict T+1, no lookahead. Each backtest must charge 6.4bps/side on turnover and borrow 0.5%/yr; where you build a new engine, ALSO record the instrument(s) you would trade and the price path used (for a future trade-record audit) in your FINDINGS.md. Do not spawn sub-agents. NEVER automate/control/touch the user's browser (permanent user directive) — use only direct HTTP APIs for data, no browser tools. Read your CHARTER.md and execute fully; write exact numbers to FINDINGS.md. Max ~150 tool calls." \
    "Read /Users/daxu/software/world-trader/campaign/GOAL100_AGENT_BRIEF.md and /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER.md, then execute the charter. Record every check with exact numbers in campaign/agents/$AGENT/FINDINGS.md. Be efficient: test highest-value ideas first, use campaign/harness/data.py + campaign/agents/B2_highfreq/gates.py helpers. Last line of FINDINGS.md must be exactly: $(basename $AGENT | tr 'a-z' 'A-Z') DONE" \
    >> "$LOG" 2>&1 &
  PIDS+=($!)
  echo "launched $AGENT pid $!"
done
echo "--- all launched pids: ${PIDS[@]} ---"
FAIL=0
for PID in "${PIDS[@]}"; do wait $PID || { echo "pid $PID nonzero"; FAIL=1; }; done
[ $FAIL -eq 0 ] && echo "ALL 5 ITER6 AGENTS COMPLETE" || echo "some failed"
