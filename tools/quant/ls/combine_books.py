"""Portfolio-of-strategies combination framework, 2026-08-05.

Combines daily return streams from multiple strategy books using:
  - Equal-weight
  - Risk-parity (inverse-vol weighting)
  - Mean-variance optimization (full-sample, honest for comparison)
  - Walk-forward mean-variance (no look-ahead, refit every 60 days)

All portfolios are vol-targeted to 15% annualized for fair comparison.
"""
from __future__ import annotations
import os, sys, json, argparse
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def load_streams(book_dirs, col="daily_return"):
    """Load daily return series from multiple result directories."""
    streams = {}
    for label, path in book_dirs.items():
        csv_path = os.path.join(path, "daily_returns.csv")
        if not os.path.exists(csv_path):
            print(f"  SKIP {label}: no daily_returns.csv in {path}")
            continue
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        match = [c for c in df.columns if col.lower() in c.lower() or "return" in c.lower()]
        if not match:
            match = [df.columns[0]]
        streams[label] = df[match[0]]
        print(f"  LOADED {label}: {len(streams[label])}d, "
              f"mean={streams[label].mean():.5f}, std={streams[label].std():.5f}")
    return streams


def align(streams):
    """Align all streams on common dates."""
    common = streams[list(streams.keys())[0]].index
    for s in streams.values():
        common = common.intersection(s.index)
    return pd.DataFrame({k: v.loc[common] for k, v in streams.items()})


def sharpe_ann(r):
    """Annualized Sharpe from daily returns."""
    if len(r) < 60 or r.std() == 0:
        return 0.0
    return float(r.mean() / r.std() * np.sqrt(252))


def max_dd(r):
    """Maximum drawdown."""
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min())


def vol_target(r, target=0.15, window=60):
    """Vol-target daily returns to target annualized vol."""
    vol = r.rolling(window).std() * np.sqrt(252)
    scale = np.clip(target / vol.replace(0, np.nan), 0, 3.0).fillna(0)
    return r * scale.shift(1).fillna(0)


def metrics(r, label=""):
    """Compute standard metrics."""
    r = r.dropna()
    if len(r) < 60 or r.std() == 0:
        return {}
    eq = (1 + r).cumprod()
    return {
        "label": label,
        "sharpe": round(sharpe_ann(r), 4),
        "ann_ret": round(float(eq.iloc[-1] ** (252 / len(r)) - 1), 4),
        "ann_vol": round(float(r.std() * np.sqrt(252)), 4),
        "max_dd": round(max_dd(r), 4),
        "n_days": len(r),
    }


def equal_weight(aligned):
    """Equal-weight portfolio."""
    return aligned.mean(axis=1)


def risk_parity(aligned):
    """Risk-parity: weight = 1/vol for each stream, normalized."""
    vols = aligned.std()
    w = (1.0 / vols.replace(0, np.nan)).fillna(0)
    w = w / w.sum()
    return (aligned * w).sum(axis=1), w


def mean_variance(aligned, lmbda=0.5):
    """Mean-variance optimal weights (no shorts, sum to 1)."""
    n = len(aligned.columns)
    mu = aligned.mean().values * 252
    cov = aligned.cov().values * 252

    def objective(w):
        return - (mu @ w - 0.5 * lmbda * w @ cov @ w)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(0, 1)] * n
    w0 = np.ones(n) / n

    result = minimize(objective, w0, method="SLSQP",
                     bounds=bounds, constraints=constraints,
                     options={"maxiter": 1000, "ftol": 1e-12})
    w = result.x
    w = np.maximum(w, 0)
    w = w / w.sum()
    return (aligned.values @ w), pd.Series(w, index=aligned.columns)


def walk_forward_mv(aligned, window=60, lmbda=0.5):
    """Walk-forward mean-variance: refit every `window` days, no look-ahead."""
    daily = pd.Series(0.0, index=aligned.index)
    weights_history = []

    for t in range(window, len(aligned)):
        if (t - window) % window != 0 and t < len(aligned) - 1:
            # Use previous weights
            if weights_history:
                w = weights_history[-1][1]
                daily.iloc[t] = aligned.iloc[t].values @ w.values
            continue

        # Fit on past window
        hist = aligned.iloc[t - window:t]
        _, w = mean_variance(hist, lmbda)
        weights_history.append((aligned.index[t], w))
        daily.iloc[t] = aligned.iloc[t].values @ w.values

    # Fill gaps with equal weight
    for i in range(window):
        if i < len(daily):
            daily.iloc[i] = aligned.iloc[i].mean()
    return daily


def combine_all(streams, out_dir=None):
    """Run all combination methods and print comparison."""
    aligned = align(streams)
    print(f"\nAligned: {len(aligned)}d, {len(aligned.columns)} books")
    print(f"Range: {aligned.index[0].date()}..{aligned.index[-1].date()}")

    # Correlation matrix
    corr = aligned.corr()
    print(f"\n=== Correlation matrix ===")
    print(corr.round(3).to_string())
    mean_corr = float(corr.values[np.triu_indices_from(corr.values, k=1)].mean())
    print(f"Mean pairwise correlation: {mean_corr:.3f}")

    results = []

    # Individual books
    print(f"\n=== Individual books ===")
    for col in aligned.columns:
        r = aligned[col]
        m = metrics(r, col)
        results.append(m)
        print(f"  {col}: sharpe={m['sharpe']:.4f}  ann_ret={m['ann_ret']:.4f}  "
              f"vol={m['ann_vol']:.4f}  maxdd={m['max_dd']:.4f}")

    # Equal-weight
    ew = equal_weight(aligned)
    ew_vt = vol_target(ew)
    m = metrics(ew_vt, "equal_weight")
    results.append(m)
    print(f"\n=== Equal-weight === sharpe={m['sharpe']:.4f}  "
          f"ann_ret={m['ann_ret']:.4f}  vol={m['ann_vol']:.4f}  maxdd={m['max_dd']:.4f}")

    # Risk-parity
    rp, rp_w = risk_parity(aligned)
    rp_vt = vol_target(rp)
    m = metrics(rp_vt, "risk_parity")
    results.append(m)
    print(f"\n=== Risk-parity === sharpe={m['sharpe']:.4f}  "
          f"ann_ret={m['ann_ret']:.4f}  vol={m['ann_vol']:.4f}  maxdd={m['max_dd']:.4f}")
    print(f"  weights: {dict(zip(aligned.columns, rp_w.round(3)))}")

    # Mean-variance
    mv, mv_w = mean_variance(aligned, lmbda=0.5)
    mv_vt = vol_target(pd.Series(mv, index=aligned.index))
    m = metrics(mv_vt, "mean_variance")
    results.append(m)
    print(f"\n=== Mean-variance (full-sample) === sharpe={m['sharpe']:.4f}  "
          f"ann_ret={m['ann_ret']:.4f}  vol={m['ann_vol']:.4f}  maxdd={m['max_dd']:.4f}")
    print(f"  weights: {dict(zip(aligned.columns, mv_w.round(3)))}")

    # Walk-forward MV
    wf = walk_forward_mv(aligned, window=60, lmbda=0.5)
    wf_vt = vol_target(wf)
    m = metrics(wf_vt, "wf_mean_variance")
    results.append(m)
    print(f"\n=== Walk-forward MV === sharpe={m['sharpe']:.4f}  "
          f"ann_ret={m['ann_ret']:.4f}  vol={m['ann_vol']:.4f}  maxdd={m['max_dd']:.4f}")

    # Summary table
    print(f"\n{'='*60}")
    print(f"{'Method':<25s} {'Sharpe':>8s} {'AnnRet':>8s} {'Vol':>8s} {'MaxDD':>8s}")
    print(f"{'-'*60}")
    for r in results:
        print(f"{r['label']:<25s} {r['sharpe']:8.4f} {r['ann_ret']:8.4f} "
              f"{r['ann_vol']:8.4f} {r['max_dd']:8.4f}")

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        aligned.to_csv(os.path.join(out_dir, "aligned_daily.csv"))
        corr.to_csv(os.path.join(out_dir, "correlation.csv"))
        pd.DataFrame(results).to_csv(os.path.join(out_dir, "portfolio_comparison.csv"), index=False)

        # Save equal-weight and WF-MV for later use
        pd.DataFrame({"equal_weight": ew_vt}).to_csv(
            os.path.join(out_dir, "portfolio_equalweight.csv"))
        pd.DataFrame({"wf_mv": wf_vt}).to_csv(
            os.path.join(out_dir, "portfolio_wf_mv.csv"))

        print(f"\nSaved -> {out_dir}")

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", default=[],
                   help="Result dirs: label1=path1 label2=path2 ...")
    ap.add_argument("--base", default="",
                   help="Base directory containing book subdirs")
    args = ap.parse_args()

    book_dirs = {}
    if args.dirs:
        for item in args.dirs:
            if "=" in item:
                label, path = item.split("=", 1)
                book_dirs[label] = path
    elif args.base:
        for d in sorted(os.listdir(args.base)):
            full = os.path.join(args.base, d)
            if os.path.isdir(full) and os.path.exists(
                    os.path.join(full, "daily_returns.csv")):
                book_dirs[d] = full
    else:
        print("Usage: combine_books.py --dirs h3=/path/to/h3 h10=/path/to/h10")
        print("   or: combine_books.py --base /path/to/results/dir")
        return 1

    print(f"Loading {len(book_dirs)} books...")
    streams = load_streams(book_dirs)
    if len(streams) < 2:
        print("Need >=2 books with daily_returns.csv")
        return 1

    out_dir = os.path.join(os.path.dirname(list(book_dirs.values())[0]), "portfolio")
    combine_all(streams, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
