#!/bin/bash
cd /Users/daxu/software/world-trader
AGENTS=(loop_team/HUNT_VXV_TERM loop_team/HUNT_CRYPTO_SAT loop_team/HUNT_SECTOR_FULL)
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
  LOG="campaign/agents/$AGENT/LOG_iter75.log"
  echo "=== $AGENT start $(date) ===" >> "$LOG"
  claude -p --dangerously-skip-permissions \
    --append-system-prompt "You are research agent $AGENT in the GOAL100 quant campaign (project /Users/daxu/software/world-trader). OPERATE UNDER SUPERPOWERS RIGOR (read campaign/SUPERPOWERS_RIGOR.md): TDD failing-test-first RED->GREEN, verification-before-completion (exact numbers, never should/probably), systematic-debugging root cause. USE THE REUSABLE campaign/bt FRAMEWORK (bt.engine/metrics/gates/reconcile) for every number — do NOT hand-roll. NEVER automate/control/touch the user's browser (permanent boundary) — only direct HTTP APIs for data (you mostly use LOCAL on-disk data: tools/quant/data/more_*.csv). Strict T+1, no lookahead, cost 6.4bps/side + borrow 0.5%/yr, capital-real <=1.6x. Use gates.scramble_positions with the CORRECT real-book baseline. Record instrument+price_path+price_source(REAL/SYNTH) for trade-record per TRADE_RECORD_STANDARD.md. Do not spawn sub-agents. Be brutally honest; reject anything failing gates; log dead variants with exact numbers. Work autonomously with python3 heredocs; API is rate-limited ~25 req/min (batch; on 429 wait 20-30s retry once). Max ~150 tool calls. Write exact numbers to FINDINGS.md. Last line exactly: $(basename $AGENT | tr 'a-z' 'A-Z') DONE" \
    "Read /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER.md, /Users/daxu/software/world-trader/campaign/SUPERPOWERS_RIGOR.md, /Users/daxu/software/world-trader/campaign/results/DEAD_IDEAS.csv, then execute the charter using campaign/bt. Record every check with exact numbers in campaign/agents/$AGENT/FINDINGS.md. Be efficient." \
    >> "$LOG" 2>&1 &
  PIDS+=($!)
  echo "launched $AGENT pid $!"
done
echo "--- all launched pids: ${PIDS[@]} ---"
wait "${PIDS[@]}"
echo "ALL 3 ITER75 HUNTS COMPLETE"
