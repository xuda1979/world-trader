"""Experiment harness for fast hyperparameter tuning.

Three ways to run experiments:

1. Single A/B:
   from tools.quant.ls import experiment as exp
   cmp = exp.compare_configs([
       ("baseline", {}),
       ("longer_window", {"train_window": 140}),
       ("more_names", {"n_long": 20, "n_short": 20}),
   ])

2. Grid sweep:
   df = exp.grid(Config(), {
       "train_window": [100, 120, 140],
       "n_long": [5, 10, 15],
       "weighting": ["equal", "risk_parity", "mean_var"],
   })

3. Random search (faster for large grids):
   df = exp.random_search(Config(), {
       "train_window": [80, 100, 120, 140, 160],
       "n_long": [5, 8, 10, 12, 15],
       "icir_threshold": [0.10, 0.20, 0.30, 0.40],
       "weighting": ["equal", "risk_parity", "mean_var", "shrunk"],
       "model_weight_smooth": [0.0, 0.3, 0.5],
   }, n=20, seed=42)

All experiments write a single comparison CSV + per-config artifacts under
out_dir/<name>/.
"""
from __future__ import annotations
import os, sys, time, json, random
from typing import Dict, List, Any, Optional, Tuple
from itertools import product
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from .config import Config
from . import runner, data, factors, ic_screen, model, backtest, diagnostics


# --------------------------------------------------------------------- compare
def compare_configs(specs: List[Tuple[str, Dict[str, Any]]],
                    base_cfg: Optional[Config] = None,
                    export: bool = True) -> pd.DataFrame:
    """Run several named configs and compare.  `specs` is a list of
    (name, overrides_dict).  Returns a comparison DataFrame.
    """
    if base_cfg is None:
        base_cfg = Config()
    rows = []
    bundles = []
    for name, overrides in specs:
        cfg = base_cfg.copy(**overrides, name=name)
        t0 = time.time()
        try:
            bundle = runner.run(cfg, export=export)
            dt = time.time() - t0
            row = {"name": name, "status": "ok", "runtime_s": round(dt, 1),
                   **{k: v for k, v in bundle["metrics"].items()
                      if isinstance(v, (int, float, np.floating))}}
            row["verdict"] = bundle["diagnostics"]["verdict"]["assessment"]
            row["n_flags"] = bundle["diagnostics"]["verdict"]["n_flags"]
            row["n_kept_factors"] = len(bundle["kept_factors"])
            bundles.append(bundle)
        except Exception as e:
            dt = time.time() - t0
            row = {"name": name, "status": f"error: {str(e)[:80]}",
                   "runtime_s": round(dt, 1)}
        rows.append(row)
    df = pd.DataFrame(rows)
    if export:
        out_dir = base_cfg.out_dir if os.path.isabs(base_cfg.out_dir) else os.path.join(ROOT, base_cfg.out_dir)
        os.makedirs(out_dir, exist_ok=True)
        df.to_csv(os.path.join(out_dir, "compare_configs.csv"), index=False)
    return df


# --------------------------------------------------------------------- grid
def grid(base_cfg: Config, grid_spec: Dict[str, List[Any]],
         export: bool = True, max_runs: Optional[int] = None) -> pd.DataFrame:
    """Full cartesian grid sweep.  Use `max_runs` to cap."""
    keys = list(grid_spec.keys())
    vals = [grid_spec[k] for k in keys]
    combos = list(product(*vals))
    if max_runs and len(combos) > max_runs:
        print(f"grid has {len(combos)} combos; capping to {max_runs} (first N)")
        combos = combos[:max_runs]
    print(f"=== Grid sweep: {len(combos)} configs ===")
    rows = []
    for i, combo in enumerate(combos):
        overrides = dict(zip(keys, combo))
        name = "_".join(f"{k}={v}" for k, v in overrides.items())
        cfg = base_cfg.copy(**overrides, name=name)
        t0 = time.time()
        try:
            bundle = runner.run(cfg, export=export)
            dt = time.time() - t0
            row = {"name": name, "status": "ok", "runtime_s": round(dt, 1),
                   **overrides,
                   **{k: v for k, v in bundle["metrics"].items()
                      if isinstance(v, (int, float, np.floating))}}
            row["verdict"] = bundle["diagnostics"]["verdict"]["assessment"]
            row["n_flags"] = bundle["diagnostics"]["verdict"]["n_flags"]
            rows.append(row)
        except Exception as e:
            dt = time.time() - t0
            rows.append({"name": name, "status": f"error: {str(e)[:80]}",
                         "runtime_s": round(dt, 1), **overrides})
        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{len(combos)}] done")
    df = pd.DataFrame(rows)
    if export:
        out_dir = base_cfg.out_dir if os.path.isabs(base_cfg.out_dir) else os.path.join(ROOT, base_cfg.out_dir)
        os.makedirs(out_dir, exist_ok=True)
        df.to_csv(os.path.join(out_dir, "grid_results.csv"), index=False)
        print(f"\nGrid results saved -> {os.path.join(out_dir, 'grid_results.csv')}")
    return df


# --------------------------------------------------------------------- random search
def random_search(base_cfg: Config, grid_spec: Dict[str, List[Any]],
                  n: int = 20, seed: int = 42, export: bool = True) -> pd.DataFrame:
    """Random search over the grid (sample n combos without replacement)."""
    rng = random.Random(seed)
    keys = list(grid_spec.keys())
    combos = set()
    all_combos = list(product(*[grid_spec[k] for k in keys]))
    if n > len(all_combos):
        n = len(all_combos)
    sampled = rng.sample(all_combos, n)
    print(f"=== Random search: {n} configs (of {len(all_combos)} possible) ===")
    rows = []
    for i, combo in enumerate(sampled):
        overrides = dict(zip(keys, combo))
        name = "_".join(f"{k}={v}" for k, v in overrides.items())
        cfg = base_cfg.copy(**overrides, name=name)
        t0 = time.time()
        try:
            bundle = runner.run(cfg, export=export)
            dt = time.time() - t0
            row = {"name": name, "status": "ok", "runtime_s": round(dt, 1),
                   **overrides,
                   **{k: v for k, v in bundle["metrics"].items()
                      if isinstance(v, (int, float, np.floating))}}
            row["verdict"] = bundle["diagnostics"]["verdict"]["assessment"]
            row["n_flags"] = bundle["diagnostics"]["verdict"]["n_flags"]
            rows.append(row)
        except Exception as e:
            dt = time.time() - t0
            rows.append({"name": name, "status": f"error: {str(e)[:80]}",
                         "runtime_s": round(dt, 1), **overrides})
        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{n}] done")
    df = pd.DataFrame(rows)
    if export:
        out_dir = base_cfg.out_dir if os.path.isabs(base_cfg.out_dir) else os.path.join(ROOT, base_cfg.out_dir)
        os.makedirs(out_dir, exist_ok=True)
        df.to_csv(os.path.join(out_dir, "random_search_results.csv"), index=False)
        print(f"\nRandom search results -> {os.path.join(out_dir, 'random_search_results.csv')}")
    return df


# --------------------------------------------------------------------- top configs
def top_configs(df: pd.DataFrame, metric: str = "sharpe",
                ascending: bool = False, k: int = 5) -> pd.DataFrame:
    """Return top-k configs by a metric.  Excludes error rows."""
    if df.empty:
        return df
    df_ok = df[df.get("status", "ok") == "ok"].copy()
    if metric not in df_ok.columns:
        return df_ok.head(k)
    return df_ok.sort_values(metric, ascending=ascending).head(k)


# --------------------------------------------------------------------- reusable cache (optional)
_CACHED_PANEL: Optional[Dict] = None
_CACHED_PANEL_KEY: Optional[str] = None


def cached_panel(cfg: Config) -> Dict:
    """Cache the panel load (and factor computation) across experiments that
    share the same data_dir / universe settings.  Set cfg.save_intermediate
    False during sweeps to speed things up.
    """
    global _CACHED_PANEL, _CACHED_PANEL_KEY
    key = f"{cfg.data_dir}|{cfg.universe}|{cfg.start_date}|{cfg.end_date}"
    if _CACHED_PANEL_KEY != key or _CACHED_PANEL is None:
        _CACHED_PANEL = data.load_panel(cfg)
        _CACHED_PANEL_KEY = key
    return _CACHED_PANEL


# --------------------------------------------------------------------- parallel
def parallel_grid(base_cfg: Config, grid_spec: Dict[str, List[Any]],
                  n_workers: int = 4, export: bool = True,
                  use_multiprocessing: bool = True) -> pd.DataFrame:
    """Run a grid sweep in PARALLEL using multiprocessing.

    This is the 'multi-agent' equivalent: each worker process runs one
    full pipeline independently.  On a 4-8 core machine this gives 4-8x
    speedup vs sequential.

    Note: each worker re-loads the panel (no shared state).  For very large
    panels, prefer sequential + cached panel.  For our 80-ticker / 500-day
    panel, the load is ~2s, negligible vs the 30s backtest.
    """
    from itertools import product
    keys = list(grid_spec.keys())
    vals = [grid_spec[k] for k in keys]
    combos = list(product(*vals))
    print(f"=== Parallel grid sweep: {len(combos)} configs on {n_workers} workers ===")

    # Build the list of configs
    cfgs = []
    for combo in combos:
        overrides = dict(zip(keys, combo))
        name = "_".join(f"{k}={v}" for k, v in overrides.items())
        cfgs.append(base_cfg.copy(**overrides, name=name))

    if use_multiprocessing and n_workers > 1 and len(cfgs) > 1:
        try:
            import multiprocessing as mp
            ctx = mp.get_context("spawn")
            with ctx.Pool(n_workers) as pool:
                results = pool.map(_run_one_worker, cfgs)
        except Exception as e:
            print(f"  multiprocessing failed ({e}); falling back to sequential")
            results = [_run_one_worker(c) for c in cfgs]
    else:
        results = [_run_one_worker(c) for c in cfgs]

    # Build DataFrame
    rows = []
    for cfg, res in zip(cfgs, results):
        row = {"name": cfg.name, **{k: getattr(cfg, k) for k in keys}}
        if "error" in res:
            row["status"] = f"error: {res['error']}"
            row["sharpe"] = np.nan
        elif res.get("skipped"):
            row["status"] = "gate_failed"
            row["sharpe"] = np.nan
            row["predicted_sharpe"] = res.get("predicted_sharpe", np.nan)
        else:
            row["status"] = "ok"
            for k, v in res["metrics"].items():
                if isinstance(v, (int, float, np.floating)):
                    row[k] = float(v)
            row["verdict"] = res.get("verdict", "")
            row["n_flags"] = res.get("n_flags", 0)
        rows.append(row)
    df = pd.DataFrame(rows)
    if export:
        out_dir = base_cfg.out_dir if os.path.isabs(base_cfg.out_dir) else os.path.join(ROOT, base_cfg.out_dir)
        os.makedirs(out_dir, exist_ok=True)
        df.to_csv(os.path.join(out_dir, "parallel_grid_results.csv"), index=False)
        print(f"\nParallel grid results -> {os.path.join(out_dir, 'parallel_grid_results.csv')}")
    return df


def _run_one_worker(cfg: Config) -> Dict[str, Any]:
    """Worker function: run one full pipeline.  Returns a flat dict.

    Designed to be pickle-able for multiprocessing (no large objects
    returned -- just metrics + verdict).
    """
    try:
        bundle = runner.run(cfg, export=True)
        if bundle.get("metrics", {}).get("skipped"):
            return {"skipped": True,
                    "predicted_sharpe": bundle.get("gate_estimate", {}).get(
                        "predicted_sharpe_conservative", np.nan)}
        return {
            "metrics": bundle["metrics"],
            "verdict": bundle["diagnostics"]["verdict"]["assessment"],
            "n_flags": bundle["diagnostics"]["verdict"]["n_flags"],
        }
    except Exception as e:
        return {"error": str(e)[:120]}
