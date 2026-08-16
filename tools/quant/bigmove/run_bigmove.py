"""bigmove — consolidated next-day >=5% return strategy (honest walk-forward).

Usage:  python3 run_bigmove.py

Trains the model on a rolling 3-year window (refit quarterly), predicts the
next-day >=5% probability for the whole US large-cap universe using only data
available at each close, and evaluates a long-only rule across probability
thresholds (default target >= 0.7/0.9). Writes results JSON + per-threshold
equity CSV to tools/quant/reports/.

This is a RESEARCH/EXPERIMENT artifact: the achievable precision (~10-30%) is
far below the 70% the user requested. See README.md for the honest verdict.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest_walkforward import main

if __name__ == "__main__":
    main()
