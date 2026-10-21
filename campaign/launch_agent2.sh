#!/bin/bash
# Launch round-N agent: launch_agent2.sh <agent_dir> <round> <charter_suffix>
AGENT=$1; ROUND=$2; SUF=$3
cd /Users/daxu/software/world-trader
LOG="campaign/agents/$AGENT/LOG_$ROUND.log"
export ANTHROPIC_API_KEY="cf1c73d79c9448dda0848a009b5d5bca.JeLss5V8ebvwSmzT"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"
export ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"
export ANTHROPIC_MODEL="GLM-5.3-Flash"
export ANTHROPIC_SMALL_FAST_MODEL="GLM-5.3-Flash"
export CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=
echo "=== agent $AGENT round $ROUND start $(date) ===" >> "$LOG"
claude -p --dangerously-skip-permissions \
  --append-system-prompt "You are research agent $AGENT in a multi-agent quant campaign (project /Users/daxu/software/world-trader). Work autonomously with shell+python3. Be brutally honest; reject sleeves failing any gate. Use python3 - <<'EOF' heredocs. Do not spawn sub-agents." \
  "Read /Users/daxu/software/world-trader/campaign/AGENT_BRIEF.md and /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER_$SUF.md (your round-$ROUND charter). Also read your FINDINGS.md for prior lessons. Execute the charter ideas in order; run ALL gates on each; save only passing sleeves. Append a numbered summary (idea, numbers, verdict) to campaign/agents/$AGENT/FINDINGS.md. Max ~100 tool calls. Last line of FINDINGS.md must be exactly: ROUND $ROUND DONE" \
  >> "$LOG" 2>&1
echo "=== agent $AGENT round $ROUND end $(date) exit $? ===" >> "$LOG"
