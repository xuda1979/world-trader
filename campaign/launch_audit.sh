#!/bin/bash
# Launch audit agent: launch_audit.sh <AGENT>
AGENT=$1
cd /Users/daxu/software/world-trader
LOG="campaign/agents/$AGENT/LOG_1.log"
export ANTHROPIC_API_KEY="cf1c73d79c9448dda0848a009b5d5bca.JeLss5V8ebvwSmzT"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"
export ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"
export ANTHROPIC_MODEL="GLM-5.3-Flash"
export ANTHROPIC_SMALL_FAST_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_SONNET_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_OPUS_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="GLM-5.3-Flash"
export CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=
echo "=== audit agent $AGENT start $(date) ===" >> "$LOG"
claude -p --dangerously-skip-permissions \
  --append-system-prompt "You are an ADVERSARIAL audit agent ($AGENT) in the GOAL100 quant campaign (project /Users/daxu/software/world-trader). Your mandate is to FIND PROBLEMS: bugs, lookahead, data leakage, unexplained artifacts, inflated claims. You have READ-ONLY access to the campaign/results and campaign/agents directories EXCEPT your own audit directory — do not modify any strategy code or data; write only your own FINDINGS.md and scratch scripts in your audit dir. Be ruthlessly skeptical; a clean audit requires positive evidence, not absence of complaints. Work autonomously with shell+python3. Use python3 - <<'EOF' heredocs." \
  "Read /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER.md and execute it fully. Record every check with exact numbers in campaign/agents/$AGENT/FINDINGS.md. If something cannot be verified, say UNVERIFIED explicitly — never assume. Max ~150 tool calls. Last line of FINDINGS.md must be exactly: AUDIT DONE" \
  >> "$LOG" 2>&1
echo "=== audit agent $AGENT end $(date) exit $? ===" >> "$LOG"
