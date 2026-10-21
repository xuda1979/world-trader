"""H4 sweep: portfolio weighting scheme comparison.

Research question (RESEARCH_LOG.md §H4):
  Which weighting scheme maximises NET Sharpe after realistic costs?
  DeMiguel-Garlappi-Uppal (2009, RFS) find naive 1/N weighting often beats
  mean-variance out-of-sample. Test that here.

Base config (robust H1 winner):
  predict_horizon=10, rebalance_freq=10, n_long=13, n_short=13,
  vol_target_annual=0.30, model_method=icir, financing=on.

Grid (4 configs, matching RESEARCH_LOG §H4):
  weighting in {equal, risk_parity, mean_var, shrunk}
  Plus mean_var at two risk aversions (0.5, 3.0) to trace the MV frontier.

NOTE: rev3_equal / rev3_mv_l05 / rev3_mv_l3 already exist from an earlier
run at a different base. This script re-runs all four at the SAME robust
base so the comparison is apples-to-apples.

Output: tools/quant/ls/results/h4_weighting/compare_configs.csv
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import experiment as exp


def main() -> int:
    # Base matched to the H1 robust point (f_h10_n13_vt30, Sharpe 1.03).
    base = Config(
        name="h4_weighting_base",
        predict_horizon=10,
        return_horizon_fwd=10,
        rebalance_freq=10,
        n_long=13,
        n_short=13,
        vol_target_active=True,
        vol_target_annual=0.30,
        model_method="icir",
        use_extra_factors=False,      # match H1 sweep
        beta_max_abs=0.25,            # match H1 sweep
        icir_threshold=0.08,          # match H1 sweep
        use_call_rate_financing=True,
        long_financing_apply=True,
        out_dir="tools/quant/ls/results/h4_weighting",
        plot=False,
        verbose=False,
    )

    specs = [
        ("equal",        {"weighting": "equal"}),
        ("risk_parity",  {"weighting": "risk_parity"}),
        ("mean_var_l05", {"weighting": "mean_var", "opt_lambda_risk": 0.5}),
        ("mean_var_l10", {"weighting": "mean_var", "opt_lambda_risk": 1.0}),
        ("mean_var_l30", {"weighting": "mean_var", "opt_lambda_risk": 3.0}),
        ("shrunk",       {"weighting": "shrunk"}),
    ]

    print(f"=== H4 weighting sweep: {len(specs)} configs ===")
    print(f"base: h=10 rebal=10 n=13/13 vt=0.30 model=icir financing=on")

    df = exp.compare_configs(specs, base_cfg=base, export=True)

    print("\n=== H4 sweep ranked by Sharpe (net of costs) ===")
    if "sharpe" in df.columns:
        ranked = df.sort_values("sharpe", ascending=False)
        cols = ["name", "weighting", "opt_lambda_risk",
                "sharpe", "annual_return", "annual_turnover",
                "max_dd", "avg_gross_exposure", "verdict", "n_flags"]
        cols = [c for c in cols if c in ranked.columns]
        print(ranked[cols].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
