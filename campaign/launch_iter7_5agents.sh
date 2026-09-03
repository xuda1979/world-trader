#!/bin/bash
# Launch 5 parallel agents (tracks A-audit, B-verification, C-more-data) with SUPERPOWERS rigor.
cd /Users/daxu/software/world-trader
AGENTS=(loop_team/AUDIT_FRAMEWORK loop_team/VERIFY_BEST loop_team/DATA_MORE_ETF loop_team/DATA_MORE_FRED loop_team/DATA_MORE_CRYPTO)
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
  LOG="campaign/agents/$AGENT/LOG_iter7.log"
  echo "=== $AGENT start $(date) ===" >> "$LOG"
  claude -p --dangerously-skip-permissions \
    --append-system-prompt "You are research agent $AGENT in the GOAL100 quant campaign (project /Users/daxu/software/world-trader). OPERATE UNDER SUPERPOWERS RIGOR (read campaign/SUPERPOWERS_RIGOR.md): TDD failing-test-first RED->GREEN, verification-before-completion (evidence, exact numbers, never should/probably), systematic-debugging root-cause. Use the reusable campaign/bt framework (campaign/bt/engine.py, metrics.py, gates.py, reconcile.py) where appropriate. Be brutally honest; no fabrication. Work autonomously with python3 heredocs. For DATA agents: your task is downloading MORE free data — working API keys are in .env.local (TWELVEDATA_KEY, FRED_KEY, FINNHUB_KEY all TESTED). Respect rate limits (sleep between calls), fail-closed lint every series (span, rows, gaps), only write inside your designated output dir. Do not spawn sub-agents. API rate-limited ~25 req/min: batch work, if 429 wait 20-30s and retry once. Max ~150 tool calls. Read your CHARTER.md and execute fully; write exact numbers to FINDINGS.md. Last line exactly: $(basename $AGENT | tr 'a-z' 'A-Z') DONE" \
    "Read /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER.md and /Users/daxu/software/world-trader/campaign/SUPERPOWERS_RIGOR.md, then execute the charter with superpowers rigor. Record every check with exact numbers in campaign/agents/$AGENT/FINDINGS.md. Be efficient." \
    >> "$LOG" 2>&1 &
  PIDS+=($!)
  echo "launched $AGENT pid $!"
done
echo "--- all launched pids: ${PIDS[@]} ---"
wait "${PIDS[@]}"
echo "ALL 5 ITER7 AGENTS COMPLETE"
