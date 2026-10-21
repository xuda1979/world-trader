"""H2 sweep: Gârleanu-Pedersen turnover penalty calibrated to real costs.

Research question (RESEARCH_LOG.md §H2):
  Calibrate the GP (2013, JF) turnover penalty to the actual cost structure
  (3.8bps one-side + 1bps slippage = 4.8bps per side) and find the
  (penalty, no_trade_band) pair that maximises NET Sharpe.

Base config (robust H1 winner):
  predict_horizon=10, rebalance_freq=10, n_long=13, n_short=13,
  vol_target_annual=0.30  ->  Sharpe 1.03 (the most cost-robust H1 point;
  h=3/Sharpe 1.6 is high-churn and likely cost-inflated).

Grid (20 configs):
  gp_turnover_penalty in {0, 0.00038, 0.00048, 0.001, 0.0038}
  gp_no_trade_band    in {0, 0.005, 0.01, 0.02}

Output: tools/quant/ls/results/h2_gp_penalty/compare_configs.csv
"""
from __future__ import annotations
import os
import sys
from itertools import product

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import experiment as exp


def main() -> int:
    # Base config matched to the H1 robust point (f_h10_n13_vt30, Sharpe 1.03)
    # so H2 results are directly comparable to the H1 sweep.
    base = Config(
        name="h2_gp_penalty_base",
        predict_horizon=10,
        return_horizon_fwd=10,
        rebalance_freq=10,
        n_long=13,
        n_short=13,
        vol_target_active=True,
        vol_target_annual=0.30,
        model_method="icir",          # ICIR-weighted factor model (H1 workhorse)
        weighting="mean_var",         # match H1 sweep (f_h10_n13_vt30)
        opt_lambda_risk=2.0,          # match H1 sweep
        use_extra_factors=False,      # match H1 sweep
        beta_max_abs=0.25,            # match H1 sweep
        icir_threshold=0.08,          # match H1 sweep
        use_call_rate_financing=True,  # realistic DFF-based short cost
        long_financing_apply=True,    # realistic debit-balance financing on levered long
        out_dir="tools/quant/ls/results/h2_gp_penalty",
        plot=False,
        verbose=False,
    )

    penalties = [0.0, 0.00038, 0.00048, 0.001, 0.0038]
    bands = [0.0, 0.005, 0.01, 0.02]

    specs = []
    for pen, band in product(penalties, bands):
        name = f"pen={pen}_band={band}"
        specs.append((name, {
            "gp_turnover_penalty": pen,
            "gp_no_trade_band": band,
        }))

    print(f"=== H2 GP-penalty sweep: {len(specs)} configs ===")
    print(f"base: h=10 rebal=10 n=13/13 vt=0.30 model=icir financing=on")
    print(f"grid: penalty x band = {len(penalties)} x {len(bands)}")

    df = exp.compare_configs(specs, base_cfg=base, export=True)

    # Summary ranked by Sharpe
    print("\n=== H2 sweep ranked by Sharpe (net of costs) ===")
    if "sharpe" in df.columns:
        ranked = df.sort_values("sharpe", ascending=False)
        cols = ["name", "gp_turnover_penalty", "gp_no_trade_band",
                "sharpe", "annual_return", "annual_turnover",
                "max_dd", "verdict", "n_flags"]
        cols = [c for c in cols if c in ranked.columns]
        print(ranked[cols].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
