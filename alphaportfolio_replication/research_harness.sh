#!/bin/bash
# research_harness.sh <tag> <DAILY|0|1> -- rebuild panel and run multiseed
TAG=$1; DFLAG=$2
cd /Users/daxu/software/world-trader/alphaportfolio_replication
DAILY=$DFLAG python3 build_features_full.py > /tmp/panel_${TAG}.log 2>&1
echo "=== panel ${TAG} built: $(tail -3 /tmp/panel_${TAG}.log | head -1)"
SEEDS="${SEEDS:-0 1 2}" python3 run_multiseed.py > /tmp/ms_${TAG}.log 2>&1
echo "=== multiseed ${TAG}:"
grep -E "seed |MEAN|POOLED" /tmp/ms_${TAG}.log
