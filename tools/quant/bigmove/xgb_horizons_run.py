"""One-command runner: 20-year multi-horizon XGB test, honest portfolio,
and reliability validation (survivorship-corrected). Reproduces the
authoritative results in reports/xgb_horizons/RESEARCH_REPORT.md.

Usage:
    python3 xgb_horizons_run.py              # full 20y walk-forward + book + validate
    python3 xgb_horizons_run.py --book-only  # skip retrain, use cached preds
"""
from __future__ import annotations
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ)
ENV.setdefault("HZ_START", "2008-09-01")
ENV.setdefault("TRAIN_WIN", "504")          # 2y rolling warm-up from 2006 panel
ENV.setdefault("REFIT", "63")               # quarterly model update
ENV.setdefault("HZ_PRED_CACHE", os.path.join(HERE, "data", "horizon_preds_20y_f5.pkl"))


def run(mod, label):
    print(f"\n===== {label} =====", flush=True)
    subprocess.run([sys.executable, os.path.join(HERE, mod)], env=ENV, check=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--book-only":
        print("SKIPPING retrain (using cached 20y OOS preds).")
    else:
        run("xgb_multi_horizon.py", "20-YEAR WALK-FORWARD (model updates quarterly)")
    run("xgb_horizon_portfolio.py", "HONEST HOLD-H BOOK + vol-target + costs")
    run("xgb_horizon_validate.py", "RELIABILITY SUITE (permutation, sub-period, momentum, K/cost)")
    print("\nDONE. See reports/xgb_horizons/RESEARCH_REPORT.md & results jsons.")


if __name__ == "__main__":
    main()
