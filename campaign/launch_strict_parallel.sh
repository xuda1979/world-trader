#!/bin/bash
# Launch 5 STRICTAUDIT agents IN PARALLEL (backgrounded). Each writes its own LOG + FINDINGS.
cd /Users/daxu/software/world-trader
AGENTS=(STRICTAUDIT_METRICS STRICTAUDIT_CONSTRUCTION STRICTAUDIT_SLEEVES STRICTAUDIT_EXECUTION STRICTAUDIT_STATISTICS)
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
  LOG="campaign/agents/$AGENT/LOG_1.log"
  echo "=== $AGENT start $(date) ===" >> "$LOG"
  claude -p --dangerously-skip-permissions \
    --append-system-prompt "You are an ADVERSARIAL audit agent ($AGENT) in the GOAL100 quant campaign (project /Users/daxu/software/world-trader). Your mandate is to FIND PROBLEMS: bugs, lookahead, data leakage, unexplained artifacts, inflated claims, unreproducible builds. You have READ-ONLY access to the campaign tree EXCEPT your own audit dir — do not modify any strategy code or data; write only your own FINDINGS.md and scratch scripts under campaign/agents/$AGENT/. Be ruthlessly skeptical; a clean audit requires POSITIVE evidence, not absence of complaints. Work autonomously with shell+python3 heredocs. Do not spawn sub-agents. Max ~150 tool calls." \
    "Read /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER.md and execute it fully. Record every check with exact numbers in campaign/agents/$AGENT/FINDINGS.md. If something cannot be verified, write UNVERIFIED explicitly — never assume. Also read campaign/GOAL100_TRUTH_MEMO.md, campaign/GOAL100_FINAL_STATE.md, and agents/AUDIT2_sleeves/FINDINGS.md for prior-audit context (but form your OWN independent adversarial conclusions). Last line of FINDINGS.md must be exactly: $AGENT DONE" \
    >> "$LOG" 2>&1 &
  PIDS+=($!)
  echo "launched $AGENT pid $!"
done
echo "--- all 5 launched, pids: ${PIDS[@]} ---"
echo "waiting for completion..."
FAIL=0
for PID in "${PIDS[@]}"; do
  wait $PID || { echo "agent pid $PID exited nonzero"; FAIL=1; }
done
if [ $FAIL -eq 0 ]; then echo "ALL 5 STRICTAUDIT AGENTS COMPLETE"; else echo "some agent(s) failed (exit nonzero)"; fi
