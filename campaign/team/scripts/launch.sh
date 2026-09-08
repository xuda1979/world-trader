#!/bin/bash
# Launch team agents in batches of <=5 (ai-devops rate-limit pattern: never fire 20 at once).
# Usage: bash launch.sh [AGENT ...]   (default = all 12 in roster order, batched)
ROOT="/Users/daxu/software/world-trader"
TEAM="$ROOT/campaign/team"
cd "$ROOT"
export ANTHROPIC_API_KEY="cf1c73d79c9448dda0848a009b5d5bca.JeLss5V8ebvwSmzT"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"
export ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"
export ANTHROPIC_MODEL="GLM-5.3-Flash"
export ANTHROPIC_SMALL_FAST_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_SONNET_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_OPUS_MODEL="GLM-5.3-Flash"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="GLM-5.3-Flash"
export CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST=

if [ $# -gt 0 ]; then AGENTS=("$@"); else
  AGENTS=(DATA_PULL DATA_ORGANIZE DATA_CLEAN DATA_MERGE DATA_MAESTRO \
          INFRA_STRUCTURE INFRA_REFACTOR QA_TESTS QA_AUDIT \
          QA_LEAK QA_CONSTRUCT QA_STAT \
          RES_BASIS RES_CALENDAR RES_META RES_VOL RES_CREDIT \
          RES_CARRY RES_REVERSAL RES_STATARB)
fi
BATCH=5
for ((i=0;i<${#AGENTS[@]};i+=BATCH)); do
  GROUP=("${AGENTS[@]:i:BATCH}")
  PIDS=()
  for AGENT in "${GROUP[@]}"; do
    mkdir -p "$TEAM/agents/$AGENT"
    LOG="$TEAM/agents/$AGENT/LOG.log"
    echo "=== $AGENT start $(date) ===" >> "$LOG"
    claude -p --dangerously-skip-permissions \
      --append-system-prompt "You are team agent $AGENT (project /Users/daxu/software/world-trader). Follow SUPERPOWERS rigor (TDD RED->GREEN, verification-before-completion, systematic-debugging root-cause) and the ai-devops skill (campaign/.claude/skills/ai-devops). Be brutally honest; never report PASS without fresh evidence. Reuse campaign/bt/ (engine/metrics/gates/reconcile) — no bespoke heredocs. Do not spawn sub-agents. KEEP CODE SHORT (functions<40 lines, classes<120, files<200). NEVER automate or control the user's browser — free data = direct HTTP only. Max ~150 tool calls." \
      "Read $TEAM/docs/ORG.md and $TEAM/charters/$AGENT.md (your charter), then execute it fully with rigor. Record every check with exact numbers in $TEAM/agents/$AGENT/FINDINGS.md. Be efficient." \
      >> "$LOG" 2>&1 &
    PIDS+=($!); echo "launched $AGENT pid $!"
  done
  echo "--- batch ${GROUP[*]} launched, waiting ---"
  wait "${PIDS[@]}"
  sleep 2
done
echo "ALL TEAM AGENTS COMPLETE"
