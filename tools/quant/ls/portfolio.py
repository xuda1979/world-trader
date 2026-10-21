"""Portfolio construction: select long/short names and assign weights.

Inputs (per rebalance date t):
  - predictions:  Series of predicted returns at t (over the universe)
  - panel:        price/return panel (for covariance, beta, liquidity)
  - prev_weights: Series of previous day's weights (for turnover control)

Steps:
  1. Select long candidates: top n_long (or top quantile) by predicted return
  2. Select short candidates: bottom n_short (or bottom quantile)
  3. Compute covariance + beta estimates using only data up to t
  4. Optimize weights per cfg.weighting / cfg.opt_method
  5. Apply turnover control: if a current holding is still in the hold-zone
     (top/bottom `hold_zone_*_pct`), keep it; only rebalance if the new
     candidate's predicted return differs from the replaced name by more
     than `turnover_threshold_diff` (cost gate, rule VII.2).

Output: Series of target weights over the universe at date t.
"""
from __future__ import annotations
import os, sys
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from . import optimizer


# --------------------------------------------------------------------- candidate selection
def select_candidates(predictions: pd.Series, cfg, prev_holdings: Optional[pd.Series] = None
                      ) -> Tuple[pd.Series, pd.Series, np.ndarray, np.ndarray]:
    """Pick long and short candidates from predicted returns.

    Returns (long_pred, short_pred, long_mask, short_mask).
    Masks are boolean arrays aligned with predictions.index.
    """
    pred = predictions.dropna()
    if pred.empty:
        empty = pd.Series(dtype=float)
        return empty, empty, np.array([], dtype=bool), np.array([], dtype=bool)

    n = len(pred)
    if cfg.use_fixed_n:
        n_long = min(cfg.n_long, n // 2)
        n_short = min(cfg.n_short, n // 2)
    else:
        n_long = max(1, int(n * cfg.quantile_top_pct))
        n_short = max(1, int(n * cfg.quantile_bot_pct))

    # Rank: 1 = highest predicted return
    ranks = pred.rank(ascending=False, method="first")
    long_mask = (ranks <= n_long).values
    short_mask = (ranks > n - n_short).values

    return pred[long_mask], pred[short_mask], long_mask, short_mask


# --------------------------------------------------------------------- beta / cov estimates
def estimate_betas(returns: pd.DataFrame, benchmark: pd.Series) -> pd.Series:
    """Rolling beta = cov(r_i, r_bench) / var(r_bench) for each ticker."""
    if benchmark.var() == 0 or returns.empty:
        return pd.Series(0.0, index=returns.columns)
    cov = returns.covwith(benchmark) if hasattr(returns, "covwith") else None
    if cov is None:
        # Manual computation
        bv = benchmark.values
        betas = {}
        for col in returns.columns:
            r = returns[col].values
            mask = np.isfinite(r) & np.isfinite(bv)
            if mask.sum() < 10:
                betas[col] = 0.0
                continue
            cov_ib = np.cov(r[mask], bv[mask])[0, 1]
            var_b = np.var(bv[mask])
            betas[col] = float(cov_ib / var_b) if var_b > 0 else 0.0
        return pd.Series(betas)
    return cov / benchmark.var()


def estimate_covariance(returns: pd.DataFrame, cfg, shrinkage: float = 0.25) -> pd.DataFrame:
    """Shrunk covariance estimate of the candidate universe."""
    return optimizer.shrunk_covariance(returns, shrinkage=shrinkage)


# --------------------------------------------------------------------- turnover control
def apply_turnover_control(new_weights: pd.Series, prev_weights: pd.Series,
                           predictions: pd.Series, cfg) -> pd.Series:
    """Rule VII: keep existing holdings if still in hold-zone; only replace
    if the new candidate's predicted return exceeds the current holding's
    by more than the round-trip cost threshold.

    Additional (retail-friendly): if cfg.hold_to_reduce_turnover, use a
    WIDER hold zone (hold_zone_top_pct_wide) so existing positions are
    only swapped when the predicted-return advantage exceeds the threshold.
    This is critical for high-commission retail accounts.

    Simplified implementation: we only *gate* name swaps.  If a name is in
    the new long sleeve but wasn't in the old, and the difference in
    predicted return vs the name it's replacing is < turnover_threshold_diff,
    we keep the old name.  We rescale to preserve dollar neutrality.
    """
    if prev_weights is None or prev_weights.empty:
        return new_weights

    # Identify names that left / entered each sleeve
    old_long = prev_weights[prev_weights > 1e-6].index
    old_short = prev_weights[prev_weights < -1e-6].index
    new_long = new_weights[new_weights > 1e-6].index
    new_short = new_weights[new_weights < -1e-6].index

    entered_long = set(new_long) - set(old_long)
    exited_long = set(old_long) - set(new_long)
    entered_short = set(new_short) - set(old_short)
    exited_short = set(old_short) - set(new_short)

    w = new_weights.copy()

    # For each entered long name, check if its pred return advantage vs the
    # exited long names exceeds the threshold; if not, revert to old name.
    # For retail (high commission), use a 2x threshold to reduce churn.
    pred = predictions.dropna()
    threshold = cfg.turnover_threshold_diff
    if getattr(cfg, "hold_to_reduce_turnover", False):
        threshold = threshold * 2.0  # wider gate for retail

    def _gate_side(entered, exited, side_sign):
        nonlocal w
        for ent in list(entered):
            if ent not in pred.index:
                continue
            ent_pred = pred[ent]
            # Find the exited name with the closest pred value
            best_exited = None
            best_diff = np.inf
            for ex in exited:
                if ex not in pred.index:
                    continue
                diff = abs(pred[ex] - ent_pred)
                if diff < best_diff:
                    best_diff = diff
                    best_exited = ex
            if best_exited is not None and best_diff < threshold:
                # Revert: remove the entered name, add back the exited name
                # with the weight the entered name would have had.
                w_ent = w.get(ent, 0.0)
                w = w.drop(ent) if ent in w.index else w
                w[best_exited] = w.get(best_exited, 0.0) + w_ent
                entered.discard(ent)
                exited.discard(best_exited)

    _gate_side(entered_long, exited_long, 1)
    _gate_side(entered_short, exited_short, -1)

    # Rescale to maintain dollar neutrality and gross leverage
    return _rescale_ls(w, cfg)


def _rescale_ls(w: pd.Series, cfg) -> pd.Series:
    """Rescale so sum(w)=0 and |w|.sum()=gross_leverage."""
    longs = w[w > 0]
    shorts = w[w < 0]
    gross_long = longs.sum()
    gross_short = -shorts.sum()
    total_gross = gross_long + gross_short
    if total_gross == 0:
        return w
    target = cfg.gross_leverage
    # Scale each side to target/2
    if gross_long > 0:
        longs = longs * (target / 2 / gross_long)
    if gross_short > 0:
        shorts = shorts * (target / 2 / gross_short)
    out = pd.concat([longs, shorts])
    # Include zero weights
    zeros = w[w == 0]
    return pd.concat([out, zeros])


# --------------------------------------------------------------------- main constructor
def construct_target_weights(predictions: pd.Series, panel: Dict, cfg,
                             prev_weights: Optional[pd.Series] = None,
                             cov_window: int = 60) -> pd.Series:
    """Full pipeline: select -> estimate cov/beta -> optimize -> turnover gate.

    Returns target weight Series over the full universe (zeros for non-selected).
    """
    if predictions.dropna().empty:
        return pd.Series(0.0, index=predictions.index)

    pred = predictions
    universe = pred.dropna().index
    if len(universe) < (cfg.n_long + cfg.n_short):
        return pd.Series(0.0, index=predictions.index)

    # Candidate selection
    long_pred, short_pred, long_mask, short_mask = select_candidates(pred, cfg, prev_weights)
    # select_candidates builds masks on pred.dropna(); re-align to the FULL
    # prediction index so the optimizer's positional indexing matches (deep
    # panels can have a NaN-name at a rebalance date -> mask length != n).
    long_mask = pred.index.isin(long_pred.index)
    short_mask = pred.index.isin(short_pred.index)

    if len(long_pred) == 0 or len(short_pred) == 0:
        return pd.Series(0.0, index=predictions.index)

    # Apply leverage cap: create an effective cfg with gross_leverage capped
    max_lev = getattr(cfg, "max_gross_leverage", cfg.gross_leverage)
    if cfg.gross_leverage > max_lev:
        cfg = cfg.copy(gross_leverage=max_lev)

    # Covariance + beta using only data up to now (caller passes panel sliced)
    returns = panel["returns"][universe]
    Sigma = estimate_covariance(returns.tail(cov_window), cfg)

    # Benchmark beta
    bench_col = cfg.benchmark if cfg.benchmark in panel["returns"].columns else None
    if bench_col:
        bench = panel["returns"][bench_col].tail(cov_window)
        betas = estimate_betas(returns.tail(cov_window), bench)
    else:
        betas = pd.Series(0.0, index=universe)

    # Optimize
    if cfg.weighting == "equal":
        w_arr = optimizer.equal_weights(long_mask, short_mask, cfg)
        w = pd.Series(w_arr, index=pred.index)
    elif (prev_weights is not None and not prev_weights.empty
          and getattr(cfg, "gp_turnover_penalty", 0.0) > 0.0):
        # Gârleanu-Pedersen (2013): turnover-penalised mean-variance.
        # Internalises the 3.8 bps one-side commission inside the objective.
        w = optimizer.optimize_weights_with_turnover(
            pred, Sigma, betas, cfg, prev_weights, long_mask, short_mask)
    else:
        w = optimizer.optimize_weights(pred, Sigma, betas, cfg, long_mask, short_mask)

    # Turnover control (cost gate)
    if prev_weights is not None and not prev_weights.empty:
        # Gârleanu-Pedersen no-trade band (cheap L1 complement to the penalty
        # inside the optimiser).  Applied first so the hold-zone rule below
        # sees the post-band weights.
        gp_band = float(getattr(cfg, "gp_no_trade_band", 0.0))
        if gp_band > 0.0:
            w = optimizer.apply_gp_no_trade_band(w, prev_weights, gp_band)
        w = apply_turnover_control(w, prev_weights, pred, cfg)
    else:
        w = _rescale_ls(w, cfg)

    # Risk controls: VIX de-risking, max daily loss (applied in backtest loop
    # since they depend on portfolio state; here we just return target weights)

    # Position cap enforcement (final safety)
    cap = cfg.position_cap_pct * cfg.gross_leverage
    w = w.clip(-cap, cap)
    w = _rescale_ls(w, cfg)

    return w
