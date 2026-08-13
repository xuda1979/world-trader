#!/usr/bin/env bash
# Daily: run the floored flagship (primary core) + verify the T-bill floor guarantee.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${WT_PYTHON:-/Users/daxu/homebrew/bin/python3}"
LOG="$ROOT/tools/logs/floored-$(date '+%Y-%m-%d').log"
mkdir -p "$ROOT/tools/logs"
{
  echo "########## FLOORED FLAGSHIP $(date '+%Y-%m-%d %H:%M:%S %Z') ##########"
  cd "$ROOT"
  # 1) rebuild the base floored flagship stream + stats card
  "$PY" tools/quant/hedge_fund_strats/portfolio_floored.py 2>&1
  echo "---- T-bill floor monitor ----"
  # 2) verify no-losing-year guarantee still holds (T-bill >= 3.4%)
  "$PY" tools/quant/hedge_fund_strats/monitor_tbill_floor.py 2>&1
  echo ""
} | tee -a "$LOG"
# monitor exit 2 = floor breached -> surface loudly
"$PY" tools/quant/hedge_fund_strats/monitor_tbill_floor.py >/dev/null 2>&1
rc=$?
if [ $rc -ge 2 ]; then
  echo "!! FLOOR BREACH: no-losing-year guarantee at risk (see $LOG)" >> "$LOG"
fi
exit 0
