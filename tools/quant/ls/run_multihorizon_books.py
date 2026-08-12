"""Multi-horizon factor books for portfolio-of-strategies diversification.

Runs the GBRT pipeline at h={3,5,10,15,21} with FULL factor set + honest
trailing-only screen.  Each horizon naturally selects different factor
combinations, producing partially-decorrelated daily return streams.

All configs frozen at the champion base (d3r10n15g4) with only horizon,
rebalance, and refit adjusted.  Costs: 3.8bps one-side, financing on.

After running, saves daily returns for portfolio combination analysis.
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


def champion_base():
    """Frozen champion base config (d3r10n15g4)."""
    return Config(
        name="mh_base",
        seed=42,
        data_dir="tools/quant/data/twelvedata",
        return_horizon_fwd=10,
        predict_horizon=10,
        model_method="gbrt",
        gbrt_max_depth=3,
        gbrt_n_estimators=200,
        gbrt_learning_rate=0.05,
        gbrt_pred_smooth=0.5,
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
        train_window=160,
        refit_freq=10,
        rebalance_freq=20,
        n_long=15,
        n_short=15,
        use_fixed_n=True,
        weighting="mean_var",
        opt_lambda_risk=0.5,
        position_cap_pct=0.2,
        beta_max_abs=0.25,
        vol_target_active=True,
        vol_target_annual=0.30,
        cost_bps_one_side=3.8,
        slippage_bps=0.0,
        use_call_rate_financing=True,
        short_borrow_apply=True,
        long_financing_apply=True,
        trend_gate_enabled=True,
        trend_gate_lookback=60,
        trend_gate_threshold=-4.0,
        trend_gate_factor=0.0,
        use_extra_factors=True,
        save_intermediate=False,
        plot=False,
        verbose=True,
    )


HORIZONS = {
    "h3":  {"h": 3,  "refit": 3,  "rebalance": 3,  "smooth": 0.2, "gross": 1.6},
    "h5":  {"h": 5,  "refit": 5,  "rebalance": 5,  "smooth": 0.3, "gross": 1.6},
    "h10": {"h": 10, "refit": 10, "rebalance": 20, "smooth": 0.5, "gross": 1.6},
    "h15": {"h": 15, "refit": 10, "rebalance": 15, "smooth": 0.5, "gross": 1.4},
    "h21": {"h": 21, "refit": 21, "rebalance": 21, "smooth": 0.6, "gross": 1.2},
}


def run_book(h_label, params, out_base):
    cfg = champion_base()
    cfg.name = f"mhbook_{h_label}"
    cfg.return_horizon_fwd = params["h"]
    cfg.predict_horizon = params["h"]
    cfg.refit_freq = params["refit"]
    cfg.rebalance_freq = params["rebalance"]
    cfg.gbrt_pred_smooth = params["smooth"]
    # Apply gross (this needs to match the config field order)
    cfg.out_dir = out_base + "/" + cfg.name
    try:
        bundle = runner.run(cfg, export=True)
        m = bundle["metrics"]
        v = bundle["diagnostics"]["verdict"]
        print(f"  {cfg.name}: sharpe={m['sharpe']:.3f} ann_ret={m['annual_return']:.3f} "
              f"maxdd={m['max_drawdown']:.3f} turnover={m['annual_turnover']:.1f} "
              f"verdict={v['assessment']}({v['n_flags']})")
        return True
    except Exception as e:
        print(f"  {cfg.name}: ERROR: {e}")
        return False


def combine_portfolio(out_base, books):
    """Load daily returns from each book and compute portfolio combinations."""
    streams = {}
    for label, success in books.items():
        if not success:
            continue
        path = os.path.join(out_base, f"mhbook_{label}", "daily_returns.csv")
        if os.path.exists(path):
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            streams[label] = df.iloc[:, 0]  # first column is daily_return

    if len(streams) < 2:
        print("Not enough books for portfolio")
        return

    common = None
    for s in streams.values():
        if common is None:
            common = s.index
        else:
            common = common.intersection(s.index)

    aligned = pd.DataFrame({k: v.loc[common] for k, v in streams.items()})

    # Correlation matrix
    corr = aligned.corr()
    print("\n=== Correlation matrix ===")
    print(corr.round(3).to_string())

    # Portfolio combinations
    print("\n=== Portfolio combinations ===")
    n = len(aligned.columns)
    eq_wt = aligned.mean(axis=1)

    def sharpe(r):
        if r.std() == 0:
            return 0
        return float(r.mean() / r.std() * np.sqrt(252))

    eq_sr = sharpe(eq_wt)
    print(f"Equal-weight ({n} books): Sharpe {eq_sr:.3f}")

    # Mean-variance optimal (unconstrained)
    cov = aligned.cov() * 252
    mu = aligned.mean() * 252
    try:
        inv_cov = np.linalg.inv(cov.values)
        w_opt = inv_cov @ mu.values
        w_opt = w_opt / np.abs(w_opt).sum()  # sum to 1
        mv_daily = (aligned.values @ w_opt)
        mv_sr = sharpe(pd.Series(mv_daily, index=aligned.index))
        print(f"Mean-variance opt: Sharpe {mv_sr:.3f}")
        print(f"  weights: {dict(zip(aligned.columns, w_opt.round(3)))}")
    except Exception as e:
        print(f"MV opt failed: {e}")

    # Save
    out_dir = os.path.join(out_base, "multihorizon_portfolio")
    os.makedirs(out_dir, exist_ok=True)
    aligned.to_csv(os.path.join(out_dir, "aligned_daily.csv"))
    corr.to_csv(os.path.join(out_dir, "correlation.csv"))
    pd.DataFrame({"equal_weight": eq_wt}).to_csv(
        os.path.join(out_dir, "portfolio_equalweight.csv"))
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump({
            "equal_weight_sharpe": eq_sr,
            "n_books": n,
            "books": list(streams.keys()),
            "correlations": {k: {kk: float(vv) for kk, vv in v.items()}
                           for k, v in corr.items()}
        }, f, indent=2, default=str)

    return aligned


def main():
    out_base = os.path.join(ROOT, "tools/quant/ls/results/multihorizon_books")
    os.makedirs(out_base, exist_ok=True)

    books = {}
    for label, params in HORIZONS.items():
        print(f"\n--- {label}: h={params['h']} refit={params['refit']} "
              f"rb={params['rebalance']} ---")
        t0 = time.time()
        success = run_book(label, params, out_base)
        books[label] = success
        print(f"  ({time.time() - t0:.0f}s)")

    combine_portfolio(out_base, books)
    return 0


if __name__ == "__main__":
    sys.exit(main())
