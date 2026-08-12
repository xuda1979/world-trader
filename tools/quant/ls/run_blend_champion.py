"""GBRT + RF prediction-blend at the frozen champion base (OOS>3 pursuit,
2026-08-04).

Research question: does blending decorrelated model errors (shallow GBRT on
the 4-factor ICIR core + deep RF on all 14 factors) raise OOS Sharpe above
the single-model champion (2.11) at realistic costs (3.8 bps one-side,
slippage 0, no market impact)?

Both legs use the champion's CAPM-alpha (ff3_real/mkt, bw60) residual label
(models_extra.roll_forward_rf now supports ff3_real).  Blends are
cross-sectionally z-scored before averaging (scale-free), then backtested
with the champion's portfolio settings.

Configs: blend_a040 / blend_a050 / blend_a060
Output: tools/quant/ls/results/blend_champion/compare_blend.csv
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd

from tools.quant.ls.config import Config
from tools.quant.ls import data, factors, ic_screen, model, backtest

RESULTS = os.path.join(os.path.dirname(__file__), "results")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/validation_test/d3r10n15g4_full/config.json")

RF_OVERRIDES = {
    "model_method": "rf",
    "rf_max_depth": 8, "rf_n_estimators": 500,
    "rf_min_samples_leaf": 15, "rf_max_features": "sqrt",
    "bypass_ic_screen": True,
}


def run_model(panel, cfg):
    """Factor pipeline + walk-forward predictions (mirrors runner step 2-4)."""
    processed, stacked, factor_names = factors.all_factors(panel, cfg)
    factor_names = list(processed.keys())
    fwd = ic_screen.forward_returns(panel["prices"], cfg.return_horizon_fwd)
    ic_df = ic_screen.compute_all_ic(processed, fwd, cfg)
    if getattr(cfg, "bypass_ic_screen", False):
        kept = list(factor_names)
        _, stats, _ = ic_screen.screen_factors(ic_df, cfg, factor_names)
        sign_flips = {}
    else:
        kept, stats, _ = ic_screen.screen_factors(ic_df, cfg, factor_names)
        sign_flips = {f: s.get("sign_flip", False) for f, s in stats.items()}
    if not kept:
        kept = factor_names[:5]
    out = model.roll_forward_dispatch(processed, panel, cfg,
                                      kept_factors=kept, sign_flips=sign_flips)
    return out["predictions"]


def _zscore_cs(pred: pd.DataFrame) -> pd.DataFrame:
    mu = pred.mean(axis=1)
    sd = pred.std(axis=1)
    out = pred.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)
    return out


def main() -> int:
    with open(SRC_CFG) as f:
        d = json.load(f)
    d.pop("name", None)
    d.pop("out_dir", None)
    d["slippage_bps"] = 0.0  # realistic cost model (user spec)
    d["plot"] = False
    d["verbose"] = True

    out_dir = os.path.join(RESULTS, "blend_champion")
    os.makedirs(out_dir, exist_ok=True)

    gbrt_cfg = Config(**d)
    rf_cfg = Config(**{**d, **RF_OVERRIDES})

    panel = data.load_panel(gbrt_cfg)
    print("Training GBRT leg...", flush=True)
    gbrt_pred = run_model(panel, gbrt_cfg)
    print(f"  GBRT pred dates: {gbrt_pred.notna().any(axis=1).sum()}", flush=True)
    print("Training RF leg...", flush=True)
    rf_pred = run_model(panel, rf_cfg)
    print(f"  RF pred dates: {rf_pred.notna().any(axis=1).sum()}", flush=True)

    g_z = _zscore_cs(gbrt_pred)
    r_z = _zscore_cs(rf_pred)

    rows = []
    for alpha in (0.6, 0.7, 0.8):
        name = f"blend_a{alpha:.1f}"
        blended = alpha * g_z + (1 - alpha) * r_z
        bt_cfg = Config(**d)
        bt_cfg.name = name
        bt_cfg.out_dir = out_dir
        bt_cfg.plot = False
        bt_cfg.verbose = False
        print(f"\n=== {name} ===", flush=True)
        result = backtest.run_backtest(panel, blended, bt_cfg)
        metrics = backtest.compute_metrics(result, bt_cfg, panel["prices"])
        row = {
            "config": name,
            "sharpe": metrics.get("sharpe"),
            "ann_ret": metrics.get("annual_return"),
            "ann_vol": metrics.get("annual_volatility"),
            "turnover": metrics.get("annual_turnover"),
            "max_dd": metrics.get("max_drawdown"),
        }
        rows.append(row)
        print(row, flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "compare_blend.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_blend.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
