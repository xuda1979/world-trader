"""Advanced model variants for higher Sharpe.

1. Multi-Horizon Blended Labels: predict the average forward return across
   multiple horizons (e.g., mean of h=5, h=10, h=21). This captures both
   short-term mean-reversion and medium-term momentum in a single signal,
   reducing the need for post-hoc ensemble of multiple models.

2. Cost-Aware Training Labels: subtract estimated transaction cost from the
   forward return label. This makes the GBRT learn to predict NET returns,
   inherently favoring signals that survive costs.

3. Turnover-Aware Loss: add a penalty term to the loss function that
   penalizes predictions that would cause high turnover.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional


def compute_multi_horizon_label(prices, horizons=(5, 10, 21), blend_method="mean"):
    """Compute a blended forward return across multiple horizons.

    For each horizon h, fwd_ret_h = P_{t+h} / P_t - 1.
    blend = mean(fwd_ret_h1, fwd_ret_h2, ...) across horizons.

    This creates a single label that captures alpha at multiple timescales,
    naturally diversifying the prediction target.

    Args:
        prices: DataFrame[T, N] of close prices
        horizons: tuple of prediction horizons in trading days
        blend_method: "mean" or "geometric" or "weighted"

    Returns:
        DataFrame[T, N] of blended forward returns
    """
    fwd_rets = []
    for h in horizons:
        fwd = (prices.shift(-h) / prices) - 1.0
        fwd = fwd.replace([np.inf, -np.inf], np.nan)
        fwd_rets.append(fwd)

    if blend_method == "mean":
        # Simple average — equal weight to each horizon
        blended = sum(fwd_rets) / len(fwd_rets)
    elif blend_method == "geometric":
        # Geometric mean: (prod(1+r_i))^(1/n) - 1
        product = np.ones_like(fwd_rets[0])
        for fwd in fwd_rets:
            product = product * (1 + fwd.fillna(0))
        blended = np.power(product, 1.0 / len(fwd_rets)) - 1.0
    elif blend_method == "weighted":
        # Weight shorter horizons more (more data, more reliable)
        weights = np.array([1.0 / h for h in horizons])
        weights = weights / weights.sum()
        blended = sum(w * fwd for w, fwd in zip(weights, fwd_rets))
    else:
        raise ValueError(f"Unknown blend_method: {blend_method}")

    return blended


def compute_cost_aware_label(prices, horizon, cost_bps_one_side=3.8,
                             n_positions=20, turnover_est=5.0):
    """Compute net-of-cost forward return label.

    Subtracts estimated transaction costs from the gross forward return.
    This makes the model predict NET returns, which inherently favors
    signals that survive the cost hurdle.

    Estimated cost per trade = cost_bps_one_side / 10000
    Annual turnover factor (per position) = turnover_est / n_positions
    Per-period cost = annual_turnover_factor * cost / 252 * horizon

    Args:
        prices: DataFrame of prices
        horizon: prediction horizon in days
        cost_bps_one_side: commission per side in bps
        n_positions: number of positions (long + short)
        turnover_est: estimated annual turnover

    Returns:
        DataFrame of net forward returns
    """
    fwd_gross = (prices.shift(-horizon) / prices) - 1.0
    fwd_gross = fwd_gross.replace([np.inf, -np.inf], np.nan)

    # Estimated cost per position over the horizon
    # Annual turnover per position = turnover_est / n_positions
    # Daily turnover per position = annual / 252
    # Horizon turnover = daily * horizon
    ann_turnover_per_pos = turnover_est / n_positions
    daily_turnover_per_pos = ann_turnover_per_pos / 252
    horizon_turnover_per_pos = daily_turnover_per_pos * horizon

    # Cost per position over horizon (as fraction of notional)
    cost_fraction = horizon_turnover_per_pos * cost_bps_one_side / 10000

    # Net return = gross - cost
    fwd_net = fwd_gross - cost_fraction

    return fwd_net


class TurnoverAwareLoss:
    """Custom loss function that penalizes high-turnover predictions.

    Loss = MSE(y_true, y_pred) + lambda_turnover * |y_pred_diff|_1

    where y_pred_diff is the change in prediction from the previous period,
    proxying for the turnover that would result from acting on the signal.

    This encourages the model to produce stable predictions that don't
    trigger unnecessary rebalancing.

    Note: this requires knowing the previous period's predictions, which
    makes it a stateful loss. Implementation uses a rolling EMA of
    predictions as the turnover proxy.
    """

    def __init__(self, lambda_turnover=0.01, ema_alpha=0.3):
        self.lambda_turnover = lambda_turnover
        self.ema_alpha = ema_alpha
        self.prev_pred = None

    def __call__(self, y_true, y_pred):
        mse = np.mean((y_true - y_pred) ** 2)

        if self.prev_pred is not None and len(y_pred) == len(self.prev_pred):
            turnover_penalty = np.mean(np.abs(y_pred - self.prev_pred))
        else:
            turnover_penalty = 0.0

        # Update EMA of predictions
        if self.prev_pred is None:
            self.prev_pred = y_pred.copy()
        else:
            self.prev_pred = (self.ema_alpha * y_pred +
                             (1 - self.ema_alpha) * self.prev_pred)

        return mse + self.lambda_turnover * turnover_penalty


def apply_turnover_penalty(y_pred_new, y_pred_prev, penalty=0.01):
    """Post-hoc turnover penalty on predictions.

    y_pred_adjusted = y_pred - penalty * |y_pred - y_pred_prev|

    This shrinks predictions toward the previous value, reducing turnover.
    Equivalent to L1-regularized prediction smoothing.
    """
    if y_pred_prev is None:
        return y_pred_new

    diff = np.abs(y_pred_new - y_pred_prev)
    # Penalize large changes more
    adjustment = penalty * diff * np.sign(y_pred_new - y_pred_prev)
    return y_pred_new - adjustment
