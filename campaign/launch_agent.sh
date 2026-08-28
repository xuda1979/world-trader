#!/bin/bash
# Launch one headless research agent: launch_agent.sh <agent_dir> <round>
AGENT=$1; ROUND=$2
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
  --append-system-prompt "You are research agent $AGENT in a multi-agent quant campaign (project /Users/daxu/software/world-trader). Work autonomously with shell+python (python3). Be brutally honest; reject sleeves failing any gate. Use python3 - <<'EOF' heredocs for analysis scripts. Do not spawn sub-agents." \
  "Read /Users/daxu/software/world-trader/campaign/AGENT_BRIEF.md and /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER.md. Then do round $ROUND of research for agent $AGENT: iterate through the ideas in your charter, one at a time. For each: build signal -> backtest T+1 with 6bps/side -> run ALL gates -> if ALL pass save sleeve + script + meta, else log failure in FINDINGS.md and move on. Spend up to ~20 tool calls per idea, max ~100 calls total. Append a summary of what you tried, what passed/failed (with numbers), to campaign/agents/$AGENT/FINDINGS.md (create if missing). End by making the last line of FINDINGS.md exactly: ROUND $ROUND DONE" \
  >> "$LOG" 2>&1
echo "=== agent $AGENT round $ROUND end $(date) exit $? ===" >> "$LOG"
