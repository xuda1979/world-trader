#!/bin/bash
cd /Users/daxu/software/world-trader/alphaportfolio_replication
for k in 5 8 14 17; do
  echo "### K=$k (3 seeds) ###"
  K=$k SEEDS="20 21 22" python3 run_champion_costs.py 2>/dev/null | grep -E "Gross|Net|Annualized"
done
