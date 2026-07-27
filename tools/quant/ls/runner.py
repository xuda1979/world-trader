"""End-to-end runner for the L/S framework.

Pipeline (all steps, with future-function guard at each stage):
  1. Load panel (data.py)
  2. Compute factors (factors.py)
  3. Compute IC + screen factors (ic_screen.py)
  4. Rolling model fit + predictions (model.py)
  5. Backtest with T+1 execution + risk controls (backtest.py)
  6. Diagnostics (diagnostics.py)
  7. Export all artifacts to out_dir

CLI:
  python -m tools.quant.ls.runner                      # baseline defaults
  python -m tools.quant.ls.runner --train_window 140 --n_long 20
  python -m tools.quant.ls.runner --preset loose       # named preset
  python -m tools.quant.ls.runner --sweep train_window 100,120,140

Python API:
  from tools.quant.ls import runner
  res = runner.run(cfg)                 # one experiment
  df  = runner.run_sweep(cfg, {'train_window':[100,120,140]})  # grid
"""
from __future__ import annotations
import os, sys, json, argparse, time
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from .config import Config, ConfigError
from . import data, factors, ic_screen, model, backtest, diagnostics, sharpe_gate


# --------------------------------------------------------------------- presets
PRESETS: Dict[str, Dict[str, Any]] = {
    "baseline": {},  # Config defaults
    "strict": {
        "icir_threshold": 0.40, "ic_mean_threshold": 0.03,
        "ic_bonferroni": True, "n_long": 8, "n_short": 8,
        "train_window": 120, "refit_freq": 5, "weighting": "mean_var",
    },
    "loose": {
        "icir_threshold": 0.10, "ic_mean_threshold": 0.01,
        "ic_bonferroni": False, "n_long": 15, "n_short": 15,
        "train_window": 120, "refit_freq": 5, "weighting": "risk_parity",
    },
    "fast": {
        "train_window": 80, "refit_freq": 10, "rebalance_freq": 10,
        "ic_window": 60, "icir_threshold": 0.20,
    },
    "robust": {
        "icir_threshold": 0.25, "ic_mean_threshold": 0.02,
        "train_window": 140, "refit_freq": 5, "weighting": "shrunk",
        "opt_lambda_risk": 2.0, "model_weight_smooth": 0.5,
        "position_cap_pct": 0.10,
    },
    # High-Sharpe preset: tuned for Sharpe >= 1.5 target.
    # Key levers: (a) ICIR-weighted ensemble (small-sample robust),
    # (b) concentrated 5+5 portfolio (higher sharpness), (c) vol-target 12%,
    # (d) looser screen to include all 4 significant factors,
    # (e) mean-variance optimizer with shrinkage, (f) Sharpe gate ON.
    "high_sharpe": {
        "model_method": "icir",
        "icir_threshold": 0.10, "ic_mean_threshold": 0.005,
        "ic_bonferroni": False, "ic_sign_check": True,
        "n_long": 5, "n_short": 5, "use_fixed_n": True,
        "weighting": "mean_var", "opt_method": "scipy_slsqp",
        "opt_lambda_risk": 2.0,
        "position_cap_pct": 0.25, "gross_leverage": 1.5,
        "vol_target_active": True, "vol_target_annual": 0.12,
        "train_window": 120, "refit_freq": 5, "rebalance_freq": 5,
        "model_weight_smooth": 0.5, "model_max_factor_weight": 3.0,
        "beta_max_abs": 0.10,
        "sharpe_gate_enabled": True, "sharpe_gate_threshold": 1.5,
        "cost_bps_one_side": 5.0, "cost_round_trip_bps": 10.0,
    },
    # Aggressive L/S: more leverage, vol-target 15%, 8+8 names
    "aggressive_ls": {
        "model_method": "icir",
        "icir_threshold": 0.08, "ic_mean_threshold": 0.005,
        "ic_bonferroni": False,
        "n_long": 8, "n_short": 8, "use_fixed_n": True,
        "weighting": "mean_var", "opt_lambda_risk": 1.5,
        "position_cap_pct": 0.20, "gross_leverage": 2.0,
        "vol_target_active": True, "vol_target_annual": 0.15,
        "train_window": 100, "refit_freq": 5, "rebalance_freq": 5,
        "model_weight_smooth": 0.3, "beta_max_abs": 0.10,
        "sharpe_gate_enabled": True, "sharpe_gate_threshold": 1.5,
        "cost_bps_one_side": 5.0,
    },
    # Pure momentum: only momentum-family factors, 5+5
    "momentum_focus": {
        "model_method": "icir",
        "icir_threshold": 0.05, "ic_mean_threshold": 0.005,
        "ic_bonferroni": False,
        "n_long": 5, "n_short": 5,
        "weighting": "equal", "gross_leverage": 1.5,
        "vol_target_active": True, "vol_target_annual": 0.12,
        "train_window": 120, "refit_freq": 5,
        "sharpe_gate_enabled": True, "sharpe_gate_threshold": 1.5,
        "cost_bps_one_side": 5.0,
    },
}


def apply_preset(cfg: Config, preset: str) -> Config:
    if preset not in PRESETS:
        raise ConfigError(f"unknown preset: {preset}; available: {list(PRESETS.keys())}")
    return cfg.copy(**PRESETS[preset], name=preset)


# --------------------------------------------------------------------- main run
def run(cfg: Config, export: bool = True) -> Dict[str, Any]:
    """Run the full pipeline for one config.  Returns a results bundle."""
    t0 = time.time()
    print(f"=== L/S backtest: {cfg.name} ===")
    print(f"  universe={cfg.universe or 'auto'}  train_window={cfg.train_window}  "
          f"refit_freq={cfg.refit_freq}  rebalance_freq={cfg.rebalance_freq}")

    # 1. Load panel
    print("[1/7] Loading panel...")
    panel = data.load_panel(cfg)
    m = panel["_meta"]
    print(f"  universe_size={m['universe_size']}  dates={m['n_dates']}  "
          f"range={m['date_start']}..{m['date_end']}")

    # 2. Factors (including extra factors for Sharpe 2.0 push)
    print("[2/7] Computing factors...")
    processed, stacked, factor_names = factors.all_factors(panel, cfg)
    # Add extra factors (rank-momentum, price acceleration, downside skew,
    # Amihud illiquidity, range vol) for the Sharpe 2.0 pursuit.
    if getattr(cfg, "use_extra_factors", True):
        extra_raw = factors.compute_extra_raw_factors(panel, cfg)
        extra_processed = factors.process_cross_section(extra_raw, panel, cfg)
        processed.update(extra_processed)
        factor_names = list(processed.keys())
    print(f"  factors computed: {len(processed)} -> {list(processed.keys())}")

    # 3. IC + screen
    print("[3/7] Computing IC / ICIR + screening...")
    fwd = ic_screen.forward_returns(panel["prices"], cfg.return_horizon_fwd)
    ic_df = ic_screen.compute_all_ic(processed, fwd, cfg)
    kept, stats, icir_full = ic_screen.screen_factors(ic_df, cfg, factor_names)
    sign_flips = {f: s.get("sign_flip", False) for f, s in stats.items()}
    print(f"  kept factors ({len(kept)}): {kept}")

    # Fallback: if no factors pass the gate, use all with |mean_ic| > some floor
    # so the pipeline still produces a runnable backtest (with a warning).
    if not kept:
        print("  WARNING: no factors passed the strict gate; using top 5 by |ICIR|")
        ranked = sorted(stats.items(), key=lambda x: -abs(x[1].get("icir", 0)))
        kept = [name for name, s in ranked[:5]
                if np.isfinite(s.get("icir", 0)) and abs(s.get("icir", 0)) > 0.01]
        if not kept:
            kept = factor_names[:5]
        print(f"  fallback kept: {kept}")

    # 4. Rolling model (OLS or ICIR-weighted ensemble per cfg.model_method)
    print("[4/7] Rolling model fit + predictions...")
    out_model = model.roll_forward_dispatch(processed, panel, cfg,
                                            kept_factors=kept, sign_flips=sign_flips)
    print(f"  predictions: {out_model['predictions'].shape}  "
          f"weights: {out_model['weights'].shape}")
    if out_model["ic_oos"].notna().any():
        print(f"  OOS IC: mean={out_model['ic_oos'].mean():.4f}  "
              f"std={out_model['ic_oos'].std():.4f}")

    # 4b. Pre-backtest Sharpe gate
    gate_estimate = None
    gate_proceed = True
    gate_reason = ""
    if cfg.sharpe_gate_enabled:
        print("[4b]   Running Sharpe gate (predicted Sharpe estimate)...")
        # Use the OOS IC series as the combined signal IC
        if out_model["ic_oos"].notna().sum() >= 10:
            gate_estimate = sharpe_gate.estimate_predicted_sharpe(
                out_model["ic_oos"], m["universe_size"],
                horizon=cfg.predict_horizon
            )
        else:
            # Fall back to factor-based estimate
            gate_estimate = sharpe_gate.estimate_from_factors(
                ic_df, kept, m["universe_size"], horizon=cfg.predict_horizon
            )
        gate_proceed, gate_reason = sharpe_gate.quality_gate(
            gate_estimate, cfg.sharpe_gate_threshold
        )
        print(f"  gate: predicted Sharpe (conservative) = "
              f"{gate_estimate.get('predicted_sharpe_conservative', 0):.2f}  "
              f"(threshold {cfg.sharpe_gate_threshold})")
        print(f"  gate: {gate_reason}")
        if not gate_proceed:
            print("  >>> GATE FAILED: skipping backtest (strategy predicted Sharpe < 1.5)")
            return {
                "config": cfg.as_dict(), "meta": m, "gate_estimate": gate_estimate,
                "gate_proceed": False, "gate_reason": gate_reason,
                "kept_factors": kept, "sign_flips": sign_flips,
                "predictions": out_model["predictions"],
                "weights": out_model["weights"],
                "ic_oos": out_model["ic_oos"],
                "ic_df": ic_df, "factor_stats": stats,
                "result": None, "metrics": {"sharpe": None, "skipped": True},
                "diagnostics": {"verdict": {"assessment": "gate_failed",
                                            "overfitting_flags": [gate_reason],
                                            "n_flags": 1}},
            }

    # 5. Backtest
    print("[5/7] Running backtest...")
    result = backtest.run_backtest(panel, out_model["predictions"], cfg)
    metrics = backtest.compute_metrics(result, cfg, panel["prices"])
    print("  --- metrics ---")
    for k in ["annual_return", "annual_volatility", "sharpe", "max_drawdown",
              "annual_turnover", "avg_abs_beta", "avg_net_exposure", "final_equity"]:
        v = metrics.get(k, 0)
        print(f"    {k:22s} {v:.4f}" if isinstance(v, float) else f"    {k:22s} {v}")

    # 6. Diagnostics
    print("[6/7] Running overfitting diagnostics...")
    diag = diagnostics.run_diagnostics(result, panel, out_model["predictions"],
                                       out_model["weights"], ic_df,
                                       processed, cfg, kept, sign_flips)
    verdict = diag["verdict"]
    print(f"  verdict: {verdict['assessment']}  ({verdict['n_flags']} flags)")
    for f in verdict["overfitting_flags"]:
        print(f"    - {f}")

    # 7. Export
    bundle = {
        "config": cfg.as_dict(),
        "meta": m,
        "panel": panel,
        "processed_factors": processed,
        "ic_df": ic_df,
        "icir_full": icir_full,
        "factor_stats": stats,
        "kept_factors": kept,
        "sign_flips": sign_flips,
        "predictions": out_model["predictions"],
        "weights": out_model["weights"],
        "ic_oos": out_model["ic_oos"],
        "train_sizes": out_model["train_sizes"],
        "result": result,
        "metrics": metrics,
        "monthly_returns": backtest.monthly_returns_table(result["daily_returns"]),
        "diagnostics": diag,
    }
    dt = time.time() - t0
    print(f"[7/7] Done in {dt:.1f}s")
    if export:
        _export_bundle(bundle, cfg)
    return bundle


# --------------------------------------------------------------------- exports
def _export_bundle(bundle: Dict, cfg: Config) -> None:
    out_dir = cfg.out_dir
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(ROOT, out_dir)
    out_dir = os.path.join(out_dir, cfg.name)
    os.makedirs(out_dir, exist_ok=True)

    if cfg.save_intermediate:
        # IC series + ICIR + factor stats
        bundle["ic_df"].to_csv(os.path.join(out_dir, "ic_series.csv"))
        bundle["icir_full"].to_csv(os.path.join(out_dir, "icir_series.csv"))
        pd.DataFrame(bundle["factor_stats"]).T.to_csv(os.path.join(out_dir, "factor_stats.csv"))
        # Factor weights
        bundle["weights"].to_csv(os.path.join(out_dir, "factor_weights.csv"))
        # Predictions (may be large; save as is)
        bundle["predictions"].to_csv(os.path.join(out_dir, "predictions.csv"))
        # OOS IC
        bundle["ic_oos"].to_csv(os.path.join(out_dir, "ic_oos.csv"))

    # Equity curve + daily returns + holdings
    bundle["result"]["equity_curve"].to_csv(os.path.join(out_dir, "equity_curve.csv"))
    bundle["result"]["daily_returns"].to_csv(os.path.join(out_dir, "daily_returns.csv"))
    bundle["result"]["turnover"].to_csv(os.path.join(out_dir, "turnover.csv"))
    bundle["result"]["gross_exposure"].to_csv(os.path.join(out_dir, "gross_exposure.csv"))
    bundle["result"]["net_exposure"].to_csv(os.path.join(out_dir, "net_exposure.csv"))
    bundle["result"]["portfolio_beta"].to_csv(os.path.join(out_dir, "portfolio_beta.csv"))
    bundle["monthly_returns"].to_csv(os.path.join(out_dir, "monthly_returns.csv"))

    # Metrics + diagnostics
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump({k: float(v) if isinstance(v, (int, float, np.floating)) else v
                   for k, v in bundle["metrics"].items()}, f, indent=2, default=str)
    with open(os.path.join(out_dir, "config.json"), "w") as f:
        f.write(cfg.to_json())

    # Diagnostics
    if not bundle["diagnostics"]["regime_split"].empty:
        bundle["diagnostics"]["regime_split"].to_csv(os.path.join(out_dir, "diag_regime.csv"))
    if isinstance(bundle["diagnostics"].get("window_sweep"), dict):
        ws_rows = []
        for w, d in bundle["diagnostics"]["window_sweep"].items():
            row = {"window": w}
            row.update({k: v for k, v in d.items() if k != "factor_weights"})
            ws_rows.append(row)
        pd.DataFrame(ws_rows).to_csv(os.path.join(out_dir, "diag_window_sweep.csv"), index=False)
    if not bundle["diagnostics"]["weight_stability"].empty:
        bundle["diagnostics"]["weight_stability"].to_csv(os.path.join(out_dir, "diag_weight_stability.csv"))
    if not bundle["diagnostics"]["icir_decay"].empty:
        bundle["diagnostics"]["icir_decay"].to_csv(os.path.join(out_dir, "diag_icir_decay.csv"))
    with open(os.path.join(out_dir, "verdict.json"), "w") as f:
        json.dump(bundle["diagnostics"]["verdict"], f, indent=2, default=str)

    # Plots
    if cfg.plot:
        _plot_bundle(bundle, out_dir)

    print(f"  artifacts -> {out_dir}")


def _plot_bundle(bundle: Dict, out_dir: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return

    # Equity curve
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(bundle["result"]["equity_curve"], label="equity", color="navy")
    ax.set_title("Equity Curve")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "equity_curve.png"), dpi=110)
    plt.close(fig)

    # Rolling ICIR (synthetic = mean across kept factors)
    fig, ax = plt.subplots(figsize=(10, 4))
    kept = bundle["kept_factors"]
    if kept:
        icir_kept = bundle["icir_full"][kept] if not bundle["icir_full"].empty else pd.DataFrame()
        if not icir_kept.empty:
            synth_icir = icir_kept.mean(axis=1)
            ax.plot(synth_icir, label="synthetic ICIR (kept factors)", color="darkgreen")
            ax.axhline(0, color="k", lw=0.5)
            ax.set_title("Rolling 120d Synthetic ICIR")
            ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "rolling_icir.png"), dpi=110)
    plt.close(fig)

    # Factor weights over time
    fig, ax = plt.subplots(figsize=(10, 5))
    if not bundle["weights"].empty:
        bundle["weights"].plot(ax=ax, kind="line", legend=True)
        ax.set_title("Factor Weights Over Time")
        ax.legend(loc="best", fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "factor_weights.png"), dpi=110)
    plt.close(fig)

    # Per-factor ICIR tracking
    fig, ax = plt.subplots(figsize=(10, 5))
    if not bundle["icir_full"].empty:
        for col in bundle["icir_full"].columns:
            ax.plot(bundle["icir_full"][col], label=col, alpha=0.7)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_title("Per-Factor Rolling ICIR")
        ax.legend(loc="best", fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "per_factor_icir.png"), dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------- sweep
def run_sweep(cfg: Config, grid: Dict[str, List[Any]], export: bool = True
              ) -> pd.DataFrame:
    """Sweep over a grid of hyperparameters.  Returns a comparison DataFrame.

    Example: run_sweep(cfg, {'train_window':[100,120,140], 'n_long':[5,10,15]})
    """
    from itertools import product
    keys = list(grid.keys())
    vals = [grid[k] for k in keys]
    rows = []
    for combo in product(*vals):
        overrides = dict(zip(keys, combo))
        name = "_".join(f"{k}={v}" for k, v in overrides.items())
        cfg_i = cfg.copy(**overrides, name=name)
        try:
            bundle = run(cfg_i, export=export)
            row = {"name": name, **overrides}
            row.update({k: v for k, v in bundle["metrics"].items()
                        if isinstance(v, (int, float, np.floating))})
            row["verdict"] = bundle["diagnostics"]["verdict"]["assessment"]
            row["n_flags"] = bundle["diagnostics"]["verdict"]["n_flags"]
            rows.append(row)
        except Exception as e:
            rows.append({"name": name, **overrides, "error": str(e)[:120]})
    df = pd.DataFrame(rows)
    if export:
        out_dir = cfg.out_dir if os.path.isabs(cfg.out_dir) else os.path.join(ROOT, cfg.out_dir)
        os.makedirs(out_dir, exist_ok=True)
        df.to_csv(os.path.join(out_dir, "sweep_results.csv"), index=False)
        print(f"\nSweep results saved to {os.path.join(out_dir, 'sweep_results.csv')}")
    return df


# --------------------------------------------------------------------- CLI
def _parse_kv(items: List[str]) -> Dict[str, Any]:
    """Parse --set key=val key2=val2 ... into a dict with inferred types."""
    out = {}
    for it in items:
        if "=" not in it:
            continue
        k, v = it.split("=", 1)
        # Try int, float, bool, else string
        if v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
        else:
            try:
                out[k] = int(v)
            except ValueError:
                try:
                    out[k] = float(v)
                except ValueError:
                    out[k] = v
    return out


def _parse_list(s: str) -> List:
    parts = s.split(",")
    out = []
    for p in parts:
        p = p.strip()
        try:
            out.append(int(p))
        except ValueError:
            try:
                out.append(float(p))
            except ValueError:
                out.append(p)
    return out


def cli(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="L/S market-neutral backtest runner")
    p.add_argument("--preset", default="baseline", help=f"Named preset: {list(PRESETS.keys())}")
    p.add_argument("--set", nargs="*", default=[], help="Override config: --set train_window=140 n_long=20")
    p.add_argument("--sweep", nargs="+", default=None,
                   help="Sweep: --sweep train_window=100,120,140 n_long=5,10,15")
    p.add_argument("--no-export", action="store_true", help="Don't write artifacts to disk")
    p.add_argument("--no-plot", action="store_true", help="Skip plots")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    cfg = Config()
    cfg = apply_preset(cfg, args.preset)
    if args.set:
        cfg.set(**_parse_kv(args.set))
    if args.no_plot:
        cfg.set(plot=False)
    if args.quiet:
        cfg.set(verbose=False)

    if args.sweep:
        grid = {}
        for item in args.sweep:
            if "=" in item:
                k, v = item.split("=", 1)
                grid[k] = _parse_list(v)
        df = run_sweep(cfg, grid, export=not args.no_export)
        print("\n=== Sweep summary ===")
        cols = ["name"] + list(grid.keys()) + ["sharpe", "annual_return", "max_drawdown", "verdict"]
        cols = [c for c in cols if c in df.columns]
        print(df[cols].to_string(index=False))
        return 0

    run(cfg, export=not args.no_export)
    return 0


if __name__ == "__main__":
    sys.exit(cli())
