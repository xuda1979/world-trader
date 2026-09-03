#!/bin/bash
# Launch 4 NEW ITER6B agents IN PARALLEL with SUPERPOWERS rigor. Backgrounded.
# Combined with running HUNT_CROSSASSET2 + BLOTTER_TESTER => 6 concurrent.
cd /Users/daxu/software/world-trader
AGENTS=(loop_team/HUNT_INDUSTRY48 loop_team/HUNT_LIQREV loop_team/HUNT_OVNIGHT loop_team/AUDIT_LEVFRONTIER)
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
  LOG="campaign/agents/$AGENT/LOG_iter6b.log"
  echo "=== $AGENT start $(date) ===" >> "$LOG"
  claude -p --dangerously-skip-permissions \
    --append-system-prompt "You are research agent $AGENT in the GOAL100 multi-agent quant campaign (project /Users/daxu/software/world-trader). OPERATE UNDER THE SUPERPOWERS RIGOR CONTRACT: read /Users/daxu/software/world-trader/campaign/SUPERPOWERS_RIGOR.md and obey it — (1) test-driven-development: every reconciliation gate must have a FAILING test watched RED before the code passes; (2) verification-before-completion: no claim without fresh verification evidence, quote exact numbers, never 'should/probably'; (3) systematic-debugging: find root cause before any fix; (4) use the campaign harness helpers. Work autonomously with shell+python3 heredocs; be brutally honest; reject anything failing gates; never fabricate. Strict T+1, no lookahead. Each backtest charges 6.4bps/side on turnover + borrow 0.5%/yr; where you build an engine, ALSO record instrument(s) + price path + price_source (REAL/SYNTH) for trade-record audit per TRADE_RECORD_STANDARD.md. Do not spawn sub-agents. API is rate-limited ~25 req/min — batch work, avoid re-archaeology.Background loops: if you hit a 429, wait ~20-30s and retry once. Max ~150 tool calls. Read your CHARTER.md fully and execute; write exact numbers to FINDINGS.md. Last line exactly: $(basename $AGENT | tr 'a-z' 'A-Z') DONE" \
    "Read /Users/daxu/software/world-trader/campaign/agents/$AGENT/CHARTER.md, /Users/daxu/software/world-trader/campaign/SUPERPOWERS_RIGOR.md, /Users/daxu/software/world-trader/campaign/GOAL100_AGENT_BRIEF.md, and /Users/daxu/software/world-trader/campaign/results/DEAD_IDEAS.csv, then execute the charter with superpowers rigor. Record every check with exact numbers in campaign/agents/$AGENT/FINDINGS.md. Be efficient." \
    >> "$LOG" 2>&1 &
  PIDS+=($!)
  echo "launched $AGENT pid $!"
done
echo "--- all launched pids: ${PIDS[@]} ---"
wait "${PIDS[@]}"
echo "ALL 4 ITER6B AGENTS COMPLETE"
