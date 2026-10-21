"""Run AlphaPortfolio training over multiple seeds and report OOS Sharpe,
so we can compare configurations robustly (single-seed Sharpe is noisy)."""
import os, sys, numpy as np, pandas as pd
import torch
import run_replication_full as rrf

SEEDS = [int(s) for s in os.environ.get("SEEDS", "0 1 2").split()]


def sharpe(rets):
    r = np.asarray(rets, dtype=float)
    return float(r.mean() / (r.std() + 1e-9) * np.sqrt(12))


def run(seed):
    torch.manual_seed(seed); np.random.seed(seed)
    results = rrf.main(epochs=int(os.environ.get("EPOCHS", 60)),
                       lr=2e-3, seed=seed, device="cpu", report_path=None)
    # results[0] is AlphaPortfolio (DRL): (name, returns, months, is_ap)
    name, rets, months, _ = results[0]
    return sharpe(rets), rets


if __name__ == "__main__":
    srs, all_rets = [], []
    for s in SEEDS:
        sr, rets = run(s)
        srs.append(sr); all_rets.append(rets)
        print(f"  seed {s}: OOS Sharpe = {sr:.3f}", flush=True)
    print(f"MEAN OOS Sharpe over seeds {SEEDS}: {np.mean(srs):.3f}  (per-seed {[round(x,2) for x in srs]})")
    # concatenated-series Sharpe (pool all seeds' monthly returns)
    pooled = np.concatenate(all_rets)
    print(f"POOLED monthly-series Sharpe: {sharpe(pooled):.3f}")
