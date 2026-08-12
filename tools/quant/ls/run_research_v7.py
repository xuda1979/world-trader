
"""V7 Research: Push Sharpe higher - d3 CAPM-alpha + time-split + systematic sweep."""
from __future__ import annotations
import os, sys, json, time, copy, warnings
warnings.filterwarnings("ignore")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner
import pandas as pd

RESULTS = os.path.join(os.path.dirname(__file__), "results", "v7_research")
os.makedirs(RESULTS, exist_ok=True)

BASE = dict(
    predict_horizon=10, return_horizon_fwd=10,
    train_window=160, refit_freq=5, rebalance_freq=20,
    model_method="gbrt",
    gbrt_n_estimators=200, gbrt_max_depth=3, gbrt_learning_rate=0.05,
    gbrt_min_samples_leaf=20, gbrt_max_features="sqrt", gbrt_subsample=1.0,
    gbrt_label_transform="zscore", gbrt_label_residual="ff3_real",
    gbrt_label_ff_factors="mkt", gbrt_label_ff_beta_window=120,
    gbrt_label_ff_min_obs=30, gbrt_label_winsorize=0.01,
    gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0, gbrt_loss="squared_error",
    use_extra_factors=False, use_ohlc_factors=False,
    use_interaction_features=False, use_v2_factors=False,
    bypass_ic_screen=False,
    icir_threshold=0.08, ic_mean_threshold=0.02, ic_bonferroni=True,
    n_long=13, n_short=13,
    weighting="mean_var", opt_lambda_risk=0.5,
    position_cap_pct=0.20, gross_leverage=1.0, max_gross_leverage=1.6,
    beta_max_abs=0.25, vol_target_active=True, vol_target_annual=0.30,
    use_call_rate_financing=True, long_financing_apply=True,
    cost_bps_one_side=3.8, cost_round_trip_bps=7.6, slippage_bps=0.0,
    short_rebate_paid_bps=150.0, short_borrow_fee_etb_bps=25.0,
    long_financing_spread_bps=50.0,
    trend_gate_enabled=True, trend_gate_lookback=60,
    trend_gate_threshold=-0.05, trend_gate_factor=0.0,
    diag_window_sweep=(100, 120, 140), plot=False, verbose=False,
    save_intermediate=True, out_dir=RESULTS, seed=42,
)
