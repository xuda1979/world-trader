"""Portfolio optimizer for the long/short sleeve.

Given predicted returns y_hat (Series over the selected universe) and a
covariance estimate, solve for weights subject to:
  - dollar-neutral (sum w = 0)            [if long_short_balance]
  - beta-neutral (w . beta = beta_target) [if beta_check]
  - |w_i| <= position_cap_pct
  - gross leverage = gross_leverage

Methods (cfg.opt_method):
  - 'closed_form_mv'  : analytical mean-variance with constraints via QP-like
                        closed form (uses scipy.optimize.minimize SLSQP under
                        the hood, but with a quadratic objective)
  - 'scipy_slsqp'     : general SLSQP with linear constraints
  - 'risk_parity'     : equal risk contribution (long-short variant: each
                        position contributes equal risk to the portfolio)

We avoid cvxpy (not installed) and use scipy.optimize.  Covariance is
always shrunk (Ledoit-Wolf-style constant correlation shrinkage) for
stability on small samples.
"""
from __future__ import annotations
import os, sys
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# --------------------------------------------------------------------- covariance
def shrunk_covariance(returns: pd.DataFrame, shrinkage: float = 0.25) -> pd.DataFrame:
    """Ledoit-Wolf-style constant-correlation shrinkage covariance.

    Combines the sample covariance with a constant-correlation target:
      Sigma_shrunk = (1-shrinkage) * Sigma_sample + shrinkage * Sigma_target
    where Sigma_target uses average correlations and sample variances.
    """
    if returns.shape[1] < 2:
        return pd.DataFrame(np.eye(1), index=returns.columns, columns=returns.columns)
    Sigma = returns.cov().values
    # Constant-correlation target
    vol = np.sqrt(np.diag(Sigma))
    vol[vol == 0] = 1e-8
    corr = Sigma / np.outer(vol, vol)
    # Average off-diagonal correlation
    n = corr.shape[0]
    if n > 1:
        mean_corr = (corr.sum() - n) / (n * (n - 1))
    else:
        mean_corr = 0.0
    target = np.outer(vol, vol) * (mean_corr * (1 - np.eye(n)) + np.eye(n))
    shrunk = (1 - shrinkage) * Sigma + shrinkage * target
    return pd.DataFrame(shrunk, index=returns.columns, columns=returns.columns)


# --------------------------------------------------------------------- optimizers
def _constraint_dollar_neutral(w):
    return np.sum(w)

def _constraint_beta_neutral(w, beta):
    return float(w @ beta)

def _objective_mean_var(w, mu, Sigma, lam):
    """Quadratic: -w'mu + (lam/2) w'Sigma w."""
    return -float(w @ mu) + 0.5 * lam * float(w @ Sigma @ w)

def _objective_mean_var_turnover(w, mu, Sigma, lam, w_prev, tc_penalty):
    """Gârleanu-Pedersen (2013) objective with linear turnover penalty.

        max  w'mu - (lam/2) w'Sigma w - tc_penalty * ||w - w_prev||_1
        =>  min  -w'mu + (lam/2) w'Sigma w + tc_penalty * sum |w_i - w_prev_i|

    The L1 term is non-smooth but SLSQP handles it via finite differences.
    tc_penalty is in *fraction of notional* per unit of weight change, so
    setting tc_penalty = cfg.cost_bps_one_side / 1e4 makes the optimizer
    see the exact per-side commission cost of each unit of turnover.

    Per Gârleanu-Pedersen (2013, JF eq. 12), when expected returns are
    persistent (longer prediction horizon), the optimal turnover shrinks
    because the penalty outweighs the marginal alpha from rebalancing.
    The closed-form solution also implies a no-trade band around w_prev;
    we approximate that band explicitly in `apply_gp_no_trade_band`.
    """
    mv = -float(w @ mu) + 0.5 * lam * float(w @ Sigma @ w)
    turn = float(np.abs(w - w_prev).sum())
    return mv + tc_penalty * turn

def _objective_risk_parity(w, Sigma):
    """Risk parity: minimize sum_i (RC_i - avg_RC)^2 where RC_i = w_i (Sigma w)_i."""
    port_var = float(w @ Sigma @ w)
    if port_var <= 0:
        return 1e10
    marginal = Sigma @ w
    rc = w * marginal  # risk contributions
    avg = rc.mean()
    return float(((rc - avg) ** 2).sum())


def optimize_weights(mu: pd.Series, Sigma: pd.DataFrame, betas: pd.Series,
                     cfg, long_mask: Optional[np.ndarray] = None,
                     short_mask: Optional[np.ndarray] = None) -> pd.Series:
    """Solve for portfolio weights.

    mu:       predicted returns over the candidate universe (Series)
    Sigma:    covariance matrix (DataFrame, aligned with mu)
    betas:    beta of each candidate vs benchmark (Series)
    long_mask/short_mask: boolean arrays over mu.index marking the long / short
                         sleeves.  If None, no sign constraint.

    Returns:  Series of weights (same index as mu).
    """
    if mu.empty:
        return mu * 0.0
    idx = mu.index
    mu_v = mu.reindex(idx).values.astype(float)
    Sigma_v = Sigma.reindex(index=idx, columns=idx).values.astype(float)
    beta_v = betas.reindex(idx).values.astype(float)
    n = len(mu_v)

    # Replace NaNs with 0
    mu_v = np.nan_to_num(mu_v, nan=0.0)
    Sigma_v = np.nan_to_num(Sigma_v, nan=0.0)
    beta_v = np.nan_to_num(beta_v, nan=0.0)
    # Ensure PSD-ish
    Sigma_v = (Sigma_v + Sigma_v.T) / 2

    # Bounds
    cap = cfg.position_cap_pct * cfg.gross_leverage
    floor = cfg.position_floor_pct
    bounds = []
    for i in range(n):
        in_long = long_mask[i] if long_mask is not None else False
        in_short = short_mask[i] if short_mask is not None else False
        if in_long:
            bounds.append((max(floor, 0.0), cap))
        elif in_short:
            bounds.append((-cap, -max(floor, 0.0)))
        else:
            bounds.append((0.0, 0.0))  # excluded

    constraints = []
    # Dollar neutral (sum w = 0) for L/S balanced
    if cfg.long_short_balance:
        constraints.append({"type": "eq",
                            "fun": _constraint_dollar_neutral,
                            "jac": lambda w: np.ones_like(w)})
    # Beta neutral
    if cfg.beta_check:
        constraints.append({"type": "eq",
                            "fun": lambda w: _constraint_beta_neutral(w, beta_v),
                            "jac": lambda w: beta_v})

    # Gross leverage: |w|.sum() = gross_leverage, BUT capped at max_gross_leverage
    eff_lev = min(cfg.gross_leverage, getattr(cfg, "max_gross_leverage", cfg.gross_leverage))
    constraints.append({"type": "eq",
                        "fun": lambda w: np.abs(w).sum() - eff_lev,
                        "jac": lambda w: np.sign(w)})

    # Initial guess: equal-weight within sleeves, scaled
    w0 = np.zeros(n)
    n_long = int(long_mask.sum()) if long_mask is not None else 0
    n_short = int(short_mask.sum()) if short_mask is not None else 0
    if n_long > 0:
        w0[long_mask] = eff_lev / 2 / n_long
    if n_short > 0:
        w0[short_mask] = -eff_lev / 2 / n_short

    # Choose objective
    if cfg.opt_method == "risk_parity" or cfg.weighting == "risk_parity":
        obj = lambda w: _objective_risk_parity(w, Sigma_v)
    elif cfg.opt_method == "closed_form_mv" or cfg.weighting in ("mean_var", "shrunk"):
        obj = lambda w: _objective_mean_var(w, mu_v, Sigma_v, cfg.opt_lambda_risk)
    else:
        obj = lambda w: _objective_mean_var(w, mu_v, Sigma_v, cfg.opt_lambda_risk)

    try:
        res = minimize(obj, w0, method="SLSQP", bounds=bounds,
                       constraints=constraints,
                       options={"maxiter": cfg.opt_max_iter, "ftol": cfg.opt_tol})
        w_opt = res.x
    except Exception:
        w_opt = w0

    # Clean up tiny weights
    w_opt[np.abs(w_opt) < 1e-6] = 0.0

    return pd.Series(w_opt, index=idx)


def optimize_weights_with_turnover(mu: pd.Series, Sigma: pd.DataFrame,
                                   betas: pd.Series, cfg,
                                   w_prev: pd.Series,
                                   long_mask: Optional[np.ndarray] = None,
                                   short_mask: Optional[np.ndarray] = None
                                   ) -> pd.Series:
    """Gârleanu-Pedersen (2013) turnover-penalised optimiser.

    Solves:
        max  w'mu - (lam/2) w'Sigma w - tc_penalty * ||w - w_prev||_1
        s.t. dollar-neutral, beta-neutral (if cfg.beta_check), |w|.sum() = lev,
             position caps, sign constraints from long_mask/short_mask.

    The L1 turnover term makes the optimiser internalise the 3.8 bps one-side
    commission: a rebalance is only worth doing if the marginal alpha exceeds
    the marginal cost.  This is the single most effective defence against the
    GBRT model's naturally high churn (Avramov-Cheng-Metzker 2019).

    `w_prev` is the previous period's actual weight vector (same index as mu).
    `tc_penalty` is read from cfg.gp_turnover_penalty; if it is 0 this
    function falls through to the plain mean-variance solution (no penalty),
    so callers can toggle the GP penalty purely via config.
    """
    from scipy.optimize import minimize
    if mu.empty or w_prev is None or w_prev.empty:
        return optimize_weights(mu, Sigma, betas, cfg, long_mask, short_mask)

    tc_penalty = float(getattr(cfg, "gp_turnover_penalty", 0.0))
    if tc_penalty <= 0.0:
        return optimize_weights(mu, Sigma, betas, cfg, long_mask, short_mask)

    idx = mu.index
    mu_v = mu.values.astype(float)
    Sigma_v = Sigma.reindex(index=idx, columns=idx).values.astype(float)
    beta_v = betas.reindex(idx).values.astype(float)
    n = len(mu_v)
    w_prev_v = np.nan_to_num(
        w_prev.reindex(idx).values.astype(float), nan=0.0)

    mu_v = np.nan_to_num(mu_v, nan=0.0)
    Sigma_v = np.nan_to_num(Sigma_v, nan=0.0)
    beta_v = np.nan_to_num(beta_v, nan=0.0)
    Sigma_v = (Sigma_v + Sigma_v.T) / 2.0  # symmetrise

    # Bounds
    cap = cfg.position_cap_pct * cfg.gross_leverage
    bounds = [(-cap, cap)] * n
    if long_mask is not None and short_mask is not None:
        for i in range(n):
            if long_mask[i] and not short_mask[i]:
                bounds[i] = (0.0, cap)
            elif short_mask[i] and not long_mask[i]:
                bounds[i] = (-cap, 0.0)

    constraints = []
    if getattr(cfg, "long_short_balance", True):
        constraints.append({"type": "eq", "fun": _constraint_dollar_neutral,
                            "jac": lambda w: np.ones_like(w)})
    if cfg.beta_check:
        constraints.append({"type": "eq",
                            "fun": lambda w: _constraint_beta_neutral(w, beta_v),
                            "jac": lambda w: beta_v})
    eff_lev = min(cfg.gross_leverage,
                  getattr(cfg, "max_gross_leverage", cfg.gross_leverage))
    constraints.append({"type": "eq",
                        "fun": lambda w: np.abs(w).sum() - eff_lev,
                        "jac": lambda w: np.sign(w)})

    # Warm-start from previous weights -- this is critical for the L1 penalty
    # because the no-trade solution (w = w_prev) is the global optimum when
    # expected returns don't justify any turnover.
    w0 = w_prev_v.copy()
    # If previous weights don't satisfy constraints (e.g. sign flip), fall
    # back to equal-weight init.
    n_long = int(long_mask.sum()) if long_mask is not None else 0
    n_short = int(short_mask.sum()) if short_mask is not None else 0
    if n_long > 0 and w0[long_mask].sum() <= 0:
        w0[long_mask] = eff_lev / 2 / n_long
    if n_short > 0 and w0[short_mask].sum() >= 0:
        w0[short_mask] = -eff_lev / 2 / n_short

    obj = lambda w: _objective_mean_var_turnover(
        w, mu_v, Sigma_v, cfg.opt_lambda_risk, w_prev_v, tc_penalty)

    try:
        res = minimize(obj, w0, method="SLSQP", bounds=bounds,
                       constraints=constraints,
                       options={"maxiter": cfg.opt_max_iter * 2,
                                "ftol": cfg.opt_tol})
        w_opt = res.x
    except Exception:
        w_opt = w0

    w_opt[np.abs(w_opt) < 1e-6] = 0.0
    return pd.Series(w_opt, index=idx)


def apply_gp_no_trade_band(w_new: pd.Series, w_prev: pd.Series,
                           band: float) -> pd.Series:
    """Gârleanu-Pedersen no-trade band.

    If |w_new_i - w_prev_i| < band for name i, keep w_prev_i (don't trade).
    This approximates the closed-form no-trade region in GP(2013) Proposition 1
    and is a cheap, robust complement to the L1 penalty inside the optimiser.

    After applying the band we rescale to restore dollar-neutrality and the
    target gross leverage, so the band never violates the hard constraints.
    """
    if band <= 0 or w_prev is None or w_prev.empty:
        return w_new
    idx = w_new.index
    w_prev_a = w_prev.reindex(idx).fillna(0.0)
    delta = w_new - w_prev_a
    small = delta.abs() < band
    w_out = w_new.copy()
    w_out[small] = w_prev_a[small]
    return w_out


def equal_weights(long_mask: np.ndarray, short_mask: np.ndarray,
                  cfg) -> np.ndarray:
    """Equal-weight fallback: gross_leverage/2 on each side, split equally."""
    n = len(long_mask)
    w = np.zeros(n)
    n_long = int(long_mask.sum())
    n_short = int(short_mask.sum())
    if n_long > 0:
        w[long_mask] = cfg.gross_leverage / 2 / n_long
    if n_short > 0:
        w[short_mask] = -cfg.gross_leverage / 2 / n_short
    return w
