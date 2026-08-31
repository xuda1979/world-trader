#!/bin/bash
# Launch one headless research agent on the DP4 proxy. usage: launch_b_agent.sh <AGENT>
AGENT=$1
cd /Users/daxu/software/world-trader
LOG="campaign/agents/$AGENT/LOG_1.log"
export ANTHROPIC_API_KEY="$HUANXIN_DP4_API_KEY"
export ANTHROPIC_BASE_URL="http://127.0.0.1:64943"
export ANTHROPIC_MODEL=dp4
export ANTHROPIC_SMALL_FAST_MODEL=dp4
export ANTHROPIC_DEFAULT_SONNET_MODEL=dp4
export ANTHROPIC_DEFAULT_OPUS_MODEL=dp4
export ANTHROPIC_DEFAULT_HAIKU_MODEL=dp4
echo "=== agent $AGENT round 1 start $(date) ===" >> "$LOG"
claude -p --dangerously-skip-permissions \
  --append-system-prompt "You are research agent $AGENT in a multi-agent quant campaign (project /Users/daxu/software/world-trader). Work autonomously with shell+python3. Be brutally honest; reject sleeves failing any gate. Use python3 - <<'EOF' heredocs for analysis. Do not spawn sub-agents. You have a limited number of tool calls — be efficient, test the highest-value ideas first, and always record exact numbers in FINDINGS.md." \
  "Read /Users/daxu/software/world-trader/campaign/AGENT_BRIEF.md and /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER.md (your mission). Execute the charter ideas in order. For each: build signal -> backtest T+1 with 6bps/side -> run ALL gates -> if ALL pass save sleeve CSV+meta+repro script, else log failure with numbers in FINDINGS.md. Spend ~15-20 tool calls per idea. Append a numbered summary (idea, numbers, verdict) to campaign/agents/$AGENT/FINDINGS.md. Max ~120 tool calls. Last line of FINDINGS.md must be exactly: ROUND 1 DONE" \
  >> "$LOG" 2>&1
echo "=== agent $AGENT round 1 end $(date) exit $? ===" >> "$LOG"
