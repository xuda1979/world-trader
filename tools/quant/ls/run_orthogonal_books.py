"""Orthogonal factor books using mutually exclusive factor sets.

Each book uses a DIFFERENT subset of factors on the same 81-stock universe:
  - OHLC: intraday/overnight factors (open/high/low data only)
  - Value: MA deviation + reversal (mean-reversion signals)
  - Pure momentum: momentum-only factors (the champion's core)
  - Low-vol: volatility/risk factors only

All share the champion's base config (GBRT d=4, tw=320, h=10, rb=20, 3.8bps).
Factor isolation is achieved via factor_exclude (excluding all non-target factors).
"""
from __future__ import annotations
import os, sys, time, json
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

# All 14 base factor names
BASE_FACTORS = [
    "mom_1m", "mom_3m", "mom_6m", "mom_12m", "mom_12_1m",
    "high_dist", "reversal_1w", "reversal_3w",
    "vol_60d", "skew_60d",
    "ma_dev_200", "ma_dev_50",
    "vol_surprise", "liq_turnover",
]

# Extra factor names (when use_extra_factors=True)
EXTRA_FACTORS = [
    "rank_mom_6m", "rank_mom_12m", "price_accel",
    "downside_skew", "amihud_illiq", "range_vol_60d",
    "resid_mom_6m", "resid_mom_12m", "mom_12m_squared",
]

# Factor group definitions
GROUPS = {
    "momentum": [
        "mom_1m", "mom_3m", "mom_6m", "mom_12m", "mom_12_1m",
        "rank_mom_6m", "rank_mom_12m", "price_accel",
        "resid_mom_6m", "resid_mom_12m", "mom_12m_squared",
    ],
    "reversal": ["reversal_1w", "reversal_3w", "mom_1m"],
    "vol_risk": ["vol_60d", "skew_60d", "downside_skew", "range_vol_60d"],
    "value": ["ma_dev_200", "ma_dev_50", "high_dist"],
    "liquidity": ["liq_turnover", "amihud_illiq", "vol_surprise"],
}

ALL_BASE_EXTRA = BASE_FACTORS + EXTRA_FACTORS


def base_champion_config(name):
    return Config(
        name=name,
        seed=42,
        data_dir="tools/quant/data/twelvedata",
        universe_min_avg_vol=0,
        model_method="gbrt",
        gbrt_max_depth=4,
        gbrt_n_estimators=200,
        gbrt_learning_rate=0.05,
        gbrt_pred_smooth=0.5,
        gbrt_label_transform="zscore",
        gbrt_label_residual="ff3_real",
        gbrt_label_ff_factors="mkt",
        gbrt_label_ff_beta_window=60,
        gbrt_label_ff_min_obs=30,
        gbrt_label_winsorize=0.01,
        train_window=320,
        refit_freq=10,
        rebalance_freq=20,
        return_horizon_fwd=10,
        predict_horizon=10,
        icir_threshold=0.08,
        ic_mean_threshold=0.02,
        ic_bonferroni=True,
        screen_trailing_only=True,
        n_long=15, n_short=15, use_fixed_n=True,
        weighting="mean_var",
        opt_lambda_risk=0.5,
        position_cap_pct=0.2,
        beta_max_abs=0.25,
        vol_target_active=True, vol_target_annual=0.30,
        cost_bps_one_side=3.8, slippage_bps=0.0,
        use_call_rate_financing=True,
        short_borrow_apply=True,
        long_financing_apply=True,
        trend_gate_enabled=True,
        trend_gate_lookback=60,
        trend_gate_threshold=-4.0,
        trend_gate_factor=0.0,
        use_extra_factors=True,
        use_ohlc_factors=False,
        use_v2_factors=False,
        save_intermediate=True,
        plot=False, verbose=True,
    )


BOOKS = {
    "ortho_ohlc": {
        "desc": "OHLC factors only (intraday/overnight)",
        "use_ohlc_factors": True,
        "use_extra_factors": False,
        "bypass_ic_screen": True,  # let GBRT see all OHLC factors
        "factor_exclude": tuple(ALL_BASE_EXTRA),
    },
    "ortho_value": {
        "desc": "Value/mean-reversion factors only",
        "use_ohlc_factors": False,
        "use_extra_factors": True,
        "bypass_ic_screen": True,
        "factor_exclude": tuple(
            set(ALL_BASE_EXTRA) - set(GROUPS["value"] + GROUPS["reversal"])
        ),
    },
    "ortho_vol": {
        "desc": "Volatility/risk factors only",
        "use_ohlc_factors": False,
        "use_extra_factors": True,
        "bypass_ic_screen": True,
        "factor_exclude": tuple(
            set(ALL_BASE_EXTRA) - set(GROUPS["vol_risk"])
        ),
    },
    "ortho_mom_only": {
        "desc": "Pure momentum factors only (champion core)",
        "use_ohlc_factors": False,
        "use_extra_factors": True,
        "bypass_ic_screen": False,  # let ICIR screen momentum factors
        "factor_exclude": tuple(
            set(ALL_BASE_EXTRA) - set(GROUPS["momentum"])
        ),
    },
}


def main():
    out_base = os.path.join(ROOT, "tools/quant/ls/results/ortho_books")
    os.makedirs(out_base, exist_ok=True)

    books = {}
    for label, params in BOOKS.items():
        print(f"\n{'='*60}")
        print(f"  {label}: {params['desc']}")
        print(f"{'='*60}")

        cfg = base_champion_config(label)
        cfg.use_ohlc_factors = params["use_ohlc_factors"]
        cfg.use_extra_factors = params["use_extra_factors"]
        cfg.bypass_ic_screen = params["bypass_ic_screen"]
        cfg.factor_exclude = params["factor_exclude"]
        cfg.out_dir = out_base

        t0 = time.time()
        try:
            bundle = runner.run(cfg, export=True)
            m = bundle["metrics"]
            v = bundle["diagnostics"]["verdict"]
            print(f"\n  >>> {label}: sharpe={m['sharpe']:.4f} "
                  f"ann_ret={m['annual_return']:.4f} maxdd={m['max_drawdown']:.4f} "
                  f"turnover={m['annual_turnover']:.1f} "
                  f"verdict={v['assessment']}({v['n_flags']}) "
                  f"({time.time()-t0:.0f}s)")
            books[label] = {"sharpe": m["sharpe"], "success": True}
        except Exception as e:
            print(f"\n  >>> {label}: ERROR: {e} ({time.time()-t0:.0f}s)")
            books[label] = {"success": False, "error": str(e)}

    # Summary
    print(f"\n{'='*60}")
    print("  Orthogonal book summary")
    print(f"{'='*60}")
    for label, info in books.items():
        if info.get("success"):
            print(f"  {label:20s}: sharpe={info['sharpe']:.4f}")
        else:
            print(f"  {label:20s}: FAILED: {info.get('error','?')}")

    with open(os.path.join(out_base, "ortho_summary.json"), "w") as f:
        json.dump(books, f, indent=2, default=str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
