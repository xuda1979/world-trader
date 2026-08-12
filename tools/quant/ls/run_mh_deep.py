"""Multi-horizon GBRT books on Twelve Data (8-year) panel.

Runs h={3,5,10,21} variants from the tw320_d4 champion base.
Each book saves daily returns for portfolio combination.

The champion base: tw320_d4, GBRT depth 4, CAPM-alpha label, trend gate -4%, 3.8bps.
Horizon adjustments: shorter h -> shorter train_window, faster refit, less smoothing.
"""
from __future__ import annotations
import os, sys, json, time
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner


def base_config(h_label):
    """Build base config from champion template, adjusted for horizon."""
    cfg = Config(
        name=f"mhdeep_{h_label}",
        seed=42,
        data_dir="tools/quant/data/twelvedata",
        universe_min_avg_vol=0,  # Twelve Data has zero volume; disable volume filter
        model_method="gbrt",
        gbrt_max_depth=4,
        gbrt_n_estimators=200,
        gbrt_learning_rate=0.05,
        gbrt_label_transform="zscore",
        gbrt_label_residual="ff3_real",
        gbrt_label_ff_factors="mkt",
        gbrt_label_ff_beta_window=60,
        gbrt_label_ff_min_obs=30,
        gbrt_label_winsorize=0.01,
        icir_threshold=0.08,
        ic_mean_threshold=0.02,
        ic_bonferroni=True,
        screen_trailing_only=True,
        n_long=15,
        n_short=15,
        use_fixed_n=True,
        weighting="mean_var",
        opt_lambda_risk=0.5,
        position_cap_pct=0.2,
        beta_max_abs=0.25,
        vol_target_active=True,
        cost_bps_one_side=3.8,
        slippage_bps=0.0,
        use_call_rate_financing=True,
        short_borrow_apply=True,
        long_financing_apply=True,
        trend_gate_enabled=True,
        trend_gate_lookback=60,
        trend_gate_threshold=-4.0,
        trend_gate_factor=0.0,
        use_extra_factors=False,
        save_intermediate=True,
        plot=False,
        verbose=True,
    )
    return cfg


HORIZONS = {
    "h3":  {"h": 3,  "train_window": 200, "refit_freq": 3,  "rebalance_freq": 6,  "smooth": 0.2, "vol_target": 0.20},
    "h5":  {"h": 5,  "train_window": 260, "refit_freq": 5,  "rebalance_freq": 10, "smooth": 0.3, "vol_target": 0.25},
    "h10": {"h": 10, "train_window": 320, "refit_freq": 10, "rebalance_freq": 20, "smooth": 0.5, "vol_target": 0.30},
    "h21": {"h": 21, "train_window": 320, "refit_freq": 21, "rebalance_freq": 21, "smooth": 0.6, "vol_target": 0.25},
}


def main():
    out_base = os.path.join(ROOT, "tools/quant/ls/results/mh_deep")
    os.makedirs(out_base, exist_ok=True)

    books = {}
    for label, params in HORIZONS.items():
        print(f"\n{'='*60}")
        print(f"  {label}: h={params['h']} tw={params['train_window']} "
              f"refit={params['refit_freq']} rb={params['rebalance_freq']}")
        print(f"{'='*60}")

        cfg = base_config(label)
        cfg.return_horizon_fwd = params["h"]
        cfg.predict_horizon = params["h"]
        cfg.train_window = params["train_window"]
        cfg.refit_freq = params["refit_freq"]
        cfg.rebalance_freq = params["rebalance_freq"]
        cfg.gbrt_pred_smooth = params["smooth"]
        cfg.vol_target_annual = params["vol_target"]
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

    # Portfolio combination
    print(f"\n{'='*60}")
    print("  Portfolio combination")
    print(f"{'='*60}")

    streams = {}
    for label, info in books.items():
        if not info.get("success"):
            continue
        path = os.path.join(out_base, f"mhdeep_{label}", "daily_returns.csv")
        if os.path.exists(path):
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            col = [c for c in df.columns if "return" in c.lower() or "daily" in c.lower()]
            if col:
                streams[label] = df[col[0]]

    if len(streams) < 2:
        print("Need >=2 books for portfolio")
        return 1

    # Align on common dates
    common = streams[list(streams.keys())[0]].index
    for s in streams.values():
        common = common.intersection(s.index)
    aligned = pd.DataFrame({k: v.loc[common] for k, v in streams.items()})

    # Correlation matrix
    corr = aligned.corr()
    print("\nCorrelation matrix:")
    print(corr.round(3).to_string())

    # Equal-weight portfolio
    ew = aligned.mean(axis=1)
    ew_sr = float(ew.mean() / ew.std() * np.sqrt(252)) if ew.std() > 0 else 0

    print(f"\nEqual-weight ({len(streams)} books): Sharpe {ew_sr:.4f}")

    # Mean-variance optimal
    cov = aligned.cov() * 252
    mu = aligned.mean() * 252
    try:
        inv_cov = np.linalg.inv(cov.values)
        w_mv = inv_cov @ mu.values
        w_mv = w_mv / np.abs(w_mv).sum()
        mv_daily = aligned.values @ w_mv
        mv_sr = float(pd.Series(mv_daily, index=aligned.index).mean() /
                      pd.Series(mv_daily, index=aligned.index).std() * np.sqrt(252))
        print(f"Mean-variance opt: Sharpe {mv_sr:.4f}")
        for i, label in enumerate(aligned.columns):
            print(f"  {label}: {w_mv[i]:.3f}")
    except Exception as e:
        print(f"MV opt failed: {e}")

    # Save
    port_dir = os.path.join(out_base, "portfolio")
    os.makedirs(port_dir, exist_ok=True)
    aligned.to_csv(os.path.join(port_dir, "aligned_daily.csv"))
    corr.to_csv(os.path.join(port_dir, "correlation.csv"))
    pd.DataFrame({"equal_weight": ew}).to_csv(os.path.join(port_dir, "equal_weight.csv"))

    summary = {
        "n_books": len(streams),
        "equal_weight_sharpe": round(ew_sr, 4),
        "books": {k: {"sharpe": books[k].get("sharpe", 0)} for k in streams},
        "mean_correlation": round(float(corr.values[np.triu_indices_from(corr.values, k=1)].mean()), 4),
    }
    with open(os.path.join(port_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nSaved -> {port_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
