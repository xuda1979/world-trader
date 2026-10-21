#!/bin/bash
# Launch GOAL100 C-series agent: launch_goal100.sh <AGENT> <ROUND>
AGENT=$1; ROUND=${2:-1}
cd /Users/daxu/software/world-trader
LOG="campaign/agents/$AGENT/LOG_$ROUND.log"
export ANTHROPIC_API_KEY="cf1c73d79c9448dda0848a009b5d5bca.JeLss5V8ebvwSmzT"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"
export ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"
export ANTHROPIC_MODEL="GLM-5.3-Flash"
export ANTHROPIC_SMALL_FAST_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_SONNET_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_OPUS_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="GLM-5.3-Flash"
export CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=
echo "=== agent $AGENT round $ROUND start $(date) ===" >> "$LOG"
claude -p --dangerously-skip-permissions \
  --append-system-prompt "You are research agent $AGENT in the GOAL100 multi-agent quant campaign (project /Users/daxu/software/world-trader). Work autonomously with shell+python3. Be brutally honest; reject sleeves failing any gate. Use python3 - <<'EOF' heredocs for analysis. Do not spawn sub-agents. You have a limited number of tool calls — be efficient, test the highest-value ideas first, and always record exact numbers in FINDINGS.md." \
  "Read /Users/daxu/software/world-trader/campaign/GOAL100_AGENT_BRIEF.md and /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER.md (your mission). Execute the charter ideas in order. For each: build signal -> backtest T+1 with 6bps/side -> run ALL gates (incl. decorrelation vs current blend) -> if ALL pass save sleeve CSV+meta+repro script, else log failure with exact numbers in FINDINGS.md. Spend ~15-20 tool calls per idea. Append a numbered summary (idea, numbers, verdict) to campaign/agents/$AGENT/FINDINGS.md. Max ~150 tool calls. Last line of FINDINGS.md must be exactly: ROUND $ROUND DONE" \
  >> "$LOG" 2>&1
echo "=== agent $AGENT round $ROUND end $(date) exit $? ===" >> "$LOG"
