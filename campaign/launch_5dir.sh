#!/bin/bash
# Launch one 5-direction research agent with 429 retry: launch_5dir.sh <agent> <brief_file>
set -u
AGENT=$1; BRIEF=$2
ROOT=/Users/daxu/software/world-trader
cd $ROOT
LOG=logs/${AGENT}.log
export ANTHROPIC_BASE_URL="https://open.bigmodel.cn/api/anthropic"
export ANTHROPIC_API_KEY="cf1c73d79c9448dda0848a009b5d5bca.JeLss5V8ebvwSmzT"
export ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_API_KEY"
export ANTHROPIC_MODEL="glm-4.6"
mkdir -p campaign/agents/${AGENT}_results logs
for attempt in 1 2 3 4 5; do
  echo "=== agent $AGENT attempt $attempt start $(date) ===" >> $LOG
  claude -p --dangerously-skip-permissions \
    --append-system-prompt "You are a quantitative research agent in the world-trader campaign repo. Work autonomously. Read your brief file fully first, then execute. Hard rules: (1) T+1 causal signals only, NO lookahead — signals must use only data available at decision time; (2) every backtest charges 6bps per FULL one-side turnover |dW| (no 0.5 half-turn) PLUS 4.5%/yr IBKR margin on (gross-1) PLUS 0.5%/yr borrow on any short notional, where applicable; (3) honest math: ann=(1+r).prod()**(252/n)-1, SR=r.mean()/r.std()*sqrt(252), MaxDD=(1+r).cumprod() drawdown (reported negative); (4) FAIL-CLOSED: any check you cannot compute = FAIL; log REJECT with exact numbers, do not hide failures; (5) OFFLINE ONLY — no network calls; all data from tools/quant/data/ and campaign/results/; (6) write ALL deliverables to disk then append 'DONE $AGENT' as the last line of your findings file; (7) be token-efficient: use head/tail on big CSVs, do not dump frames, do not talk to yourself — execute, observe, act." \
    < $BRIEF >> $LOG 2>&1
  ec=$?
  echo "=== agent $AGENT attempt $attempt end $(date) exit $ec ===" >> $LOG
  if grep -qiE "429|rate limit|已达速率|API Error" $LOG && [ $attempt -lt 5 ]; then
    sleep_s=$((45 * attempt))
    echo "=== $AGENT hit rate-limit/API-error; backoff ${sleep_s}s ===" >> $LOG
    sleep $sleep_s
    continue
  fi
  break
done
