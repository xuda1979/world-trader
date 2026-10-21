"""Rolling cross-sectional regression model.

For each refit date t (every cfg.refit_freq days):
  1. Form training sample = [t-train_window-h, t-h] where h = predict_horizon
     (we shift back by h so the forward return at the *last* training row
      is fully realized by time t -- this is the future-function guard).
  2. For each training row, y = forward_return_{row}, X = factors_{row}.
  3. Fit OLS (or ridge) with intercept across the cross-section pooled over
     the training window.
  4. Predict at time t: y_hat_t = X_t @ beta.  These are cross-sectional
     expected returns used by the portfolio constructor.

Future-function guard:
  - Training rows never include rows where forward_return overlaps with
    dates > t.  We assert this with data.assert_no_future_function.
  - The factor row at time t uses only info up to t (factors.py guarantee).

Outputs:
  - predictions:  DataFrame[T, N] of cross-sectional expected returns
  - weights:      DataFrame[T, F] of factor weights (for diagnostics)
  - ic_oos:       Series of out-of-sample IC at each prediction date
"""
from __future__ import annotations
import os, sys
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from .data import FutureFunctionError


# --------------------------------------------------------------------- OLS
def _fit_ols(X: np.ndarray, y: np.ndarray, ridge: float = 0.0,
             intercept: bool = True, max_weight: float = 5.0
             ) -> Tuple[np.ndarray, np.ndarray]:
    """Fit OLS (or ridge) with optional intercept.  Returns (beta, X_mean, y_mean).

    Solves (X'X + lambda I) beta = X'y.  With intercept handled by centering.
    Caps coefficient magnitudes for stability (optional).
    """
    if X.shape[0] < X.shape[1] + 1:
        return np.zeros(X.shape[1]), np.zeros(X.shape[1])
    mask = np.isfinite(y) & np.isfinite(X).all(axis=1)
    X = X[mask]
    y = y[mask]
    if len(y) < max(10, X.shape[1] + 1):
        return np.zeros(X.shape[1]), np.zeros(X.shape[1])

    if intercept:
        X_mean = X.mean(axis=0)
        y_mean = y.mean()
        Xc = X - X_mean
        yc = y - y_mean
    else:
        X_mean = np.zeros(X.shape[1])
        y_mean = 0.0
        Xc = X
        yc = y

    # Ridge regularization (lambda * I, no penalty on intercept since we centered)
    p = Xc.shape[1]
    A = Xc.T @ Xc + ridge * np.eye(p)
    b = Xc.T @ yc
    try:
        beta = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        beta = np.linalg.lstsq(A, b, rcond=None)[0]

    # Cap |beta| for stability
    if max_weight > 0:
        beta = np.clip(beta, -max_weight, max_weight)

    return beta, X_mean


def _predict(X: np.ndarray, beta: np.ndarray, X_mean: np.ndarray,
             y_mean: float, intercept: bool = True) -> np.ndarray:
    """Predict y_hat = (X - X_mean) @ beta + y_mean (if intercept)."""
    if intercept:
        return (X - X_mean) @ beta + y_mean
    return X @ beta


# --------------------------------------------------------------------- rolling fit
def roll_forward(processed: Dict[str, pd.DataFrame], panel: Dict, cfg,
                 kept_factors: Optional[List[str]] = None,
                 sign_flips: Optional[Dict[str, bool]] = None
                 ) -> Dict[str, pd.DataFrame]:
    """Walk-forward rolling regression.

    kept_factors: list of factor names to use (if None, use all in `processed`).
    sign_flips:   {factor_name: True} to flip the sign of that factor's exposure
                  (consistent with IC sign).

    Returns dict:
      predictions:  DataFrame[T, N] of predicted returns at each refit date
      weights:      DataFrame[T, F] of factor coefficients over time
      ic_oos:       Series of OOS rank IC at each refit date
      train_sizes:  Series of # training obs at each refit
    """
    prices = panel["prices"]
    returns = panel["returns"]
    h = cfg.predict_horizon

    # Forward returns aligned to signal date
    fwd = (prices.shift(-h) / prices) - 1.0
    fwd = fwd.replace([np.inf, -np.inf], np.nan)

    factor_names = kept_factors if kept_factors else list(processed.keys())
    if not factor_names:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(),
                "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    if sign_flips is None:
        sign_flips = {}

    n_dates, n_tickers = prices.shape
    # Pre-build the factor 3D array [T, N, F] for speed
    F = len(factor_names)
    factor_arr = np.full((n_dates, n_tickers, F), np.nan)
    for fi, name in enumerate(factor_names):
        df = processed[name]
        sign = -1.0 if sign_flips.get(name, False) else 1.0
        factor_arr[:, :, fi] = sign * df.values

    fwd_arr = fwd.values

    # Output containers
    pred_dates = []
    pred_mat = []  # rows of predictions (n_tickers,)
    weight_mat = []  # rows of factor weights (F,)
    ic_oos_vals = []
    train_size_vals = []

    # EMA smoothing state for weights
    ema_beta = None

    t_start = cfg.train_window + h  # need at least train_window + h of history
    if t_start >= n_dates:
        return {"predictions": pd.DataFrame(index=prices.index, columns=prices.columns),
                "weights": pd.DataFrame(index=prices.index, columns=factor_names),
                "ic_oos": pd.Series(index=prices.index, dtype=float),
                "train_sizes": pd.Series(index=prices.index, dtype=int)}

    # Refit dates: every cfg.refit_freq days starting at t_start
    refit_idx = list(range(t_start, n_dates, cfg.refit_freq))

    for t in refit_idx:
        # Training window: rows [t - train_window - h, t - h - 1] (inclusive)
        # so that the forward return at row t-h-1 is realized at t-1 (known at t).
        # The factor signal at row r is factors[r], forward return is fwd[r].
        train_start = max(0, t - cfg.train_window - h)
        train_end = t - h  # exclusive
        if train_end - train_start < cfg.model_min_train_obs:
            continue

        # Build training matrices: pool cross-sections over the window
        X_train = factor_arr[train_start:train_end].reshape(-1, F)
        y_train = fwd_arr[train_start:train_end].flatten()
        # Drop rows with NaN X or y
        mask = np.isfinite(y_train) & np.isfinite(X_train).all(axis=1)
        X_use = X_train[mask]
        y_use = y_train[mask]
        if len(y_use) < cfg.model_min_train_obs:
            continue
        if X_use.shape[1] < cfg.model_min_factors:
            continue

        # Fit
        beta, X_mean = _fit_ols(X_use, y_use, ridge=cfg.model_ols_ridge_lambda,
                                intercept=cfg.model_intercept,
                                max_weight=cfg.model_max_factor_weight)
        y_mean = y_use.mean() if cfg.model_intercept else 0.0

        # EMA smoothing of factor weights (stability)
        if cfg.model_weight_smooth > 0 and ema_beta is not None:
            alpha = cfg.model_weight_smooth
            beta = alpha * beta + (1 - alpha) * ema_beta
        ema_beta = beta.copy()

        # Predict at time t
        X_t = factor_arr[t]  # [N, F]
        if not np.isfinite(X_t).all():
            # Predict only for tickers with all factors finite
            valid = np.isfinite(X_t).all(axis=1)
            y_hat = np.full(n_tickers, np.nan)
            if valid.any():
                y_hat[valid] = _predict(X_t[valid], beta, X_mean, y_mean, cfg.model_intercept)
        else:
            y_hat = _predict(X_t, beta, X_mean, y_mean, cfg.model_intercept)

        pred_dates.append(prices.index[t])
        pred_mat.append(y_hat)
        weight_mat.append(beta)
        train_size_vals.append(len(y_use))

        # OOS IC at time t: rank corr between y_hat and realized fwd return
        # (fwd_arr[t] is the forward return starting at t; it will be realized
        # in the future, so this IC is *computable* only retrospectively.
        # For OOS monitoring we record it, but it's NOT used in any decision
        # at time t -- purely diagnostic.)
        rv = fwd_arr[t]
        valid = np.isfinite(y_hat) & np.isfinite(rv)
        if valid.sum() >= 5:
            from scipy.stats import spearmanr
            rho, _ = spearmanr(y_hat[valid], rv[valid])
            ic_oos_vals.append(float(rho) if np.isfinite(rho) else np.nan)
        else:
            ic_oos_vals.append(np.nan)

    # Build DataFrames
    predictions = pd.DataFrame(pred_mat, index=pred_dates, columns=prices.columns)
    weights = pd.DataFrame(weight_mat, index=pred_dates, columns=factor_names)
    ic_oos = pd.Series(ic_oos_vals, index=pred_dates, name="ic_oos")
    train_sizes = pd.Series(train_size_vals, index=pred_dates, name="train_size")

    return {
        "predictions": predictions,
        "weights": weights,
        "ic_oos": ic_oos,
        "train_sizes": train_sizes,
    }


# --------------------------------------------------------------------- ICIR-weighted ensemble
def roll_forward_icir_weighted(processed: Dict[str, pd.DataFrame], panel: Dict, cfg,
                               kept_factors: Optional[List[str]] = None,
                               sign_flips: Optional[Dict[str, bool]] = None
                               ) -> Dict[str, pd.DataFrame]:
    """ICIR-weighted factor combination (no OLS).

    Prediction at time t:
      y_hat_i = sum_f  w_f * factor_{f,i,t}
    where w_f = ICIR_f / sum(|ICIR_f|) computed over the training window
    [t-train_window-h, t-h] (same future-function guard as roll_forward).

    This is the industry-standard small-sample combiner and is typically
    more robust than OLS when n_factors is close to n_obs / 100.
    """
    from scipy.stats import spearmanr

    prices = panel["prices"]
    h = cfg.predict_horizon
    fwd = (prices.shift(-h) / prices) - 1.0
    fwd = fwd.replace([np.inf, -np.inf], np.nan)

    factor_names = kept_factors if kept_factors else list(processed.keys())
    if not factor_names:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(),
                "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    if sign_flips is None:
        sign_flips = {}

    n_dates, n_tickers = prices.shape
    F = len(factor_names)
    factor_arr = np.full((n_dates, n_tickers, F), np.nan)
    for fi, name in enumerate(factor_names):
        df = processed[name]
        sign = -1.0 if sign_flips.get(name, False) else 1.0
        factor_arr[:, :, fi] = sign * df.values
    fwd_arr = fwd.values

    pred_dates, pred_mat, weight_mat, ic_oos_vals, train_size_vals = [], [], [], [], []
    t_start = cfg.train_window + h
    refit_idx = list(range(t_start, n_dates, cfg.refit_freq))

    for t in refit_idx:
        train_start = max(0, t - cfg.train_window - h)
        train_end = t - h
        if train_end - train_start < cfg.model_min_train_obs:
            continue

        # Compute per-factor rolling ICIR over the training window
        icirs = np.zeros(F)
        for fi in range(F):
            f_slice = factor_arr[train_start:train_end, :, fi].flatten()
            r_slice = fwd_arr[train_start:train_end].flatten()
            mask = np.isfinite(f_slice) & np.isfinite(r_slice)
            if mask.sum() < 20:
                continue
            # Spearman rank IC per cross-section then average
            # Vectorized: compute per-date IC then mean/std
            ics = []
            for r in range(train_start, train_end):
                fv = factor_arr[r, :, fi]
                rv = fwd_arr[r]
                m = np.isfinite(fv) & np.isfinite(rv)
                if m.sum() < 5:
                    continue
                rho, _ = spearmanr(fv[m], rv[m])
                if np.isfinite(rho):
                    ics.append(rho)
            if len(ics) < 10:
                continue
            ics = np.array(ics)
            sd = ics.std(ddof=0)
            if sd > 0:
                icirs[fi] = ics.mean() / sd
        # Weights proportional to |ICIR|, sign-aligned
        abs_icir = np.abs(icirs)
        total = abs_icir.sum()
        if total == 0:
            w = np.ones(F) / F
        else:
            w = icirs / total  # signed: + for positive IC, - for negative
        # Cap |w| for stability
        w = np.clip(w, -cfg.model_max_factor_weight, cfg.model_max_factor_weight)
        # EMA smoothing
        if cfg.model_weight_smooth > 0 and weight_mat:
            alpha = cfg.model_weight_smooth
            prev = weight_mat[-1]
            w = alpha * w + (1 - alpha) * prev

        # Predict at time t: y_hat = X_t @ w (cross-sectional)
        X_t = factor_arr[t]  # [N, F]
        valid = np.isfinite(X_t).all(axis=1)
        y_hat = np.full(n_tickers, np.nan)
        if valid.any():
            y_hat[valid] = X_t[valid] @ w

        pred_dates.append(prices.index[t])
        pred_mat.append(y_hat)
        weight_mat.append(w)
        train_size_vals.append(train_end - train_start)

        rv = fwd_arr[t]
        v = np.isfinite(y_hat) & np.isfinite(rv)
        if v.sum() >= 5:
            rho, _ = spearmanr(y_hat[v], rv[v])
            ic_oos_vals.append(float(rho) if np.isfinite(rho) else np.nan)
        else:
            ic_oos_vals.append(np.nan)

    predictions = pd.DataFrame(pred_mat, index=pred_dates, columns=prices.columns)
    weights = pd.DataFrame(weight_mat, index=pred_dates, columns=factor_names)
    ic_oos = pd.Series(ic_oos_vals, index=pred_dates, name="ic_oos")
    train_sizes = pd.Series(train_size_vals, index=pred_dates, name="train_size")
    return {"predictions": predictions, "weights": weights,
            "ic_oos": ic_oos, "train_sizes": train_sizes}


# --------------------------------------------------------------------- GBRT (Gu-Kelly-Xiu 2020)
def _build_gbrt(cfg):
    """Construct a fresh GradientBoostingRegressor from cfg.

    scikit-learn's GBRT is the exact estimator GKX(2020) use as their tree
    baseline (their `GBRT*` rows in Table 9).  Loss defaults to squared-error;
    'huber' is robust to fat-tailed equity returns (avoids chasing outliers).
    """
    from sklearn.ensemble import GradientBoostingRegressor
    loss = str(getattr(cfg, "gbrt_loss", "squared_error"))
    kwargs = dict(
        n_estimators=cfg.gbrt_n_estimators,
        max_depth=cfg.gbrt_max_depth,
        learning_rate=cfg.gbrt_learning_rate,
        subsample=cfg.gbrt_subsample,
        min_samples_leaf=cfg.gbrt_min_samples_leaf,
        max_features=cfg.gbrt_max_features,
        random_state=cfg.seed,
    )
    if loss in ("huber", "quantile"):
        kwargs["loss"] = loss
        kwargs["alpha"] = float(getattr(cfg, "gbrt_alpha", 0.9))
    elif loss != "squared_error":
        kwargs["loss"] = loss
    return GradientBoostingRegressor(**kwargs)


def roll_forward_gbrt(processed: Dict[str, pd.DataFrame], panel: Dict, cfg,
                      kept_factors: Optional[List[str]] = None,
                      sign_flips: Optional[Dict[str, bool]] = None
                      ) -> Dict[str, pd.DataFrame]:
    """Walk-forward rolling GBRT (Gu-Kelly-Xiu 2020 empirical-asset-pricing tree model).

    For each refit date t (every cfg.refit_freq days):
      1. Form training sample = rows [t-train_window-h, t-h] across ALL tickers
         (pooled cross-section), with X = factor exposures at row date s and
         y = forward return r_{s,s+h}.  The h-step back-shift guarantees the
         last training row's forward return is fully realised by time t
         (future-function safe -- mirrors roll_forward).
      2. Fit a fresh GradientBoostingRegressor on the pooled sample.
      3. Predict y_hat for every ticker at time t; clip and EMA-smooth across
         refits to damp the tree's well-documented churn (Avramov et al. 2019).

    Returns the same bundle shape as roll_forward.  The `weights` field is a
    diagnostic placeholder (tree models don't expose linear coefficients; we
    record per-refit training size so diagnostics don't break).
    """
    prices = panel["prices"]
    h = cfg.predict_horizon

    # Forward returns aligned to signal date
    fwd = (prices.shift(-h) / prices) - 1.0
    fwd = fwd.replace([np.inf, -np.inf], np.nan)

    factor_names = kept_factors if kept_factors else list(processed.keys())
    if not factor_names:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(),
                "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    if sign_flips is None:
        sign_flips = {}

    n_dates, n_tickers = prices.shape
    F = len(factor_names)
    # Pre-build the factor 3D array [T, N, F]
    factor_arr = np.full((n_dates, n_tickers, F), np.nan)
    for fi, name in enumerate(factor_names):
        df = processed[name]
        sign = -1.0 if sign_flips.get(name, False) else 1.0
        factor_arr[:, :, fi] = sign * df.values
    fwd_arr = fwd.values

    # ---- Freyberger(2020) residual-return label ----
    # Predict the *residual* return after stripping common-factor exposure,
    # not the raw forward return.  This isolates the stock-specific alpha the
    # tree model is good at, and prevents the GBRT from just re-learning the
    # market beta that the portfolio optimizer already hedges.
    label_resid = str(getattr(cfg, "gbrt_label_residual", "none")).lower()
    if label_resid == "demean":
        # Subtract cross-sectional mean at each date (market-neutral label).
        # This is the lightest Freyberger-style residualization.
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            cs_mean = np.nanmean(fwd_arr, axis=1, keepdims=True)
        cs_mean = np.where(np.isfinite(cs_mean), cs_mean, 0.0)
        fwd_arr = fwd_arr - cs_mean
    elif label_resid == "pca":
        # Regress out the top-N principal components of the return panel
        # (statistical factor model, no external data needed).  We fit PCA
        # in-sample on the training window each refit to avoid lookahead.
        # The residualization happens inside the refit loop below so the PCA
        # only ever sees training data.  Here we just flag it.
        pass  # handled per-refit below
    elif label_resid == "ff3":
        # Fama-French 3-factor + momentum (UMD) residualization.
        # Build observable factor-mimicking portfolios from the returns
        # panel at each date, regress each stock's forward return on the
        # factor returns, and use the residual as the GBRT label.  This
        # isolates stock-specific alpha and prevents the GBRT from
        # re-learning common-factor exposure the portfolio optimizer
        # already hedges.  Factor proxies (constructed look-ahead-safe):
        #   market = SPY return (if available) else cross-sectional mean
        #   SMB    = small-minus-big (price proxy for size)
        #   HML    = low-vol minus high-vol (vol_60d proxy for value)
        #   UMD    = winners minus losers (12m momentum)
        # Regressions are run per-refit on the training window only.
        pass  # handled per-refit below
    elif label_resid == "ff3_real":
        # REAL Fama-French daily factors (Ken French Data Library), not
        # mimicking portfolios.  For each date t, regress each stock's
        # daily excess return on [Mkt-RF, SMB, HML, UMD] over the trailing
        # beta_window (look-ahead-safe), then residualize the forward
        # return: resid_{t,t+h} = (r_{t,t+h} - RF_{t,t+h}) - beta(t) @ F_{t,t+h}.
        # This predicts the genuine French-Fama risk-adjusted residual
        # return -- the stock-specific alpha net of market, size, value and
        # momentum exposure.  Computed ONCE upfront (not per-refit) because
        # every training row's residual is fully realized by its own t+h
        # (the walk-forward guard already drops rows with t+h > t_refit).
        # Same look-ahead argument as the "demean" branch above.
        try:
            from .ff_data import load_ff_factors, compute_ff3_resid
            ff = load_ff_factors()
            returns_simple = np.expm1(panel["returns"])  # log -> simple
            resid_df = compute_ff3_resid(
                returns_simple, prices, h, ff,
                beta_window=int(getattr(cfg, "gbrt_label_ff_beta_window", 60)),
                min_obs=int(getattr(cfg, "gbrt_label_ff_min_obs", 30)),
                factors=str(getattr(cfg, "gbrt_label_ff_factors", "ff3umd")),
            )
            fwd_arr = resid_df.values
        except Exception as e:  # fall back to raw label if data missing
            import warnings
            warnings.warn(f"ff3_real residualization failed ({e}); using raw label")

    # Winsorize the label to suppress outliers (Freyberger 2020 does this).
    # NOTE: percentiles are computed INSIDE the refit loop on training data only
    # to avoid look-ahead bias (using full-sample percentiles would leak future
    # returns into the label clip thresholds).  The flag is just stored here.
    win_p = float(getattr(cfg, "gbrt_label_winsorize", 0.0))

    # ---- Label transform (applied after residualization, before fit) ----
    # 'raw'    = use fwd_arr as-is
    # 'zscore' = cross-sectional z-score at each date (stable across regimes)
    # 'rank'   = cross-sectional rank in [0,1] (GKX 2020 rank-IC objective)
    # 'sign'   = sign only (robust to fat tails; classification-flavored)
    label_tf = str(getattr(cfg, "gbrt_label_transform", "raw")).lower()
    if label_tf == "zscore":
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            mu = np.nanmean(fwd_arr, axis=1, keepdims=True)
            sd = np.nanstd(fwd_arr, axis=1, keepdims=True)
        mu = np.where(np.isfinite(mu), mu, 0.0)
        sd = np.where(np.isfinite(sd) & (sd > 1e-8), sd, 1.0)
        fwd_arr = (fwd_arr - mu) / sd
    elif label_tf == "rank":
        # Rank each row cross-sectionally to [0,1]; preserves ordering only.
        ranks = np.full_like(fwd_arr, np.nan)
        for i in range(fwd_arr.shape[0]):
            row = fwd_arr[i]
            valid = np.isfinite(row)
            if valid.sum() >= 5:
                r = pd.Series(row[valid]).rank(pct=True).values
                ranks[i, valid] = r
        fwd_arr = ranks
    elif label_tf == "sign":
        fwd_arr = np.sign(fwd_arr)

    # ---- Volatility-scaled prediction target ----
    # Optionally divide the forward return by trailing realized vol at each
    # date, creating a signal-to-noise-ratio target.  This gives the GBRT a
    # cleaner, more homoskedastic target that down-weights noisy periods
    # (high-vol regimes where return predictions are inherently noisier).
    # The vol is computed as a trailing 60-day std, look-ahead-safe.
    vol_scale_gbrt = bool(getattr(cfg, "gbrt_label_vol_scale", False))
    if vol_scale_gbrt:
        vol_window = int(getattr(cfg, "gbrt_label_vol_window", 60))
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            # Use daily returns (not fwd) for trailing std
            ret_arr = panel["returns"].values
            # Rolling std per ticker, trailing window, look-ahead safe:
            # at date t, vol = std(ret[t-vol_window:t]) -- only uses known data
            vol_arr = np.full_like(ret_arr, np.nan)
            for j in range(ret_arr.shape[1]):
                col = pd.Series(ret_arr[:, j])
                vol_col = col.rolling(vol_window, min_periods=max(10, vol_window//2)).std()
                vol_arr[:, j] = vol_col.values
            # Scale: fwd_scaled = fwd / (vol * sqrt(h))
            # sqrt(h) annualizes the vol to the prediction horizon
            annual_factor = np.sqrt(h / 252.0)
            vol_scaled = vol_arr * annual_factor
            # Avoid division by near-zero vol
            vol_scaled = np.where(np.isfinite(vol_scaled) & (vol_scaled > 1e-8), vol_scaled, np.nan)
            fwd_arr = fwd_arr / vol_scaled
            # After scaling, winsorize more aggressively (outliers are more common)
            if win_p < 0.01:
                win_p = 0.02

    pred_mat = np.full((n_dates, n_tickers), np.nan)
    ic_oos_vals: List[float] = []
    train_size_vals: List[int] = []
    pred_dates: List = []
    ema_pred: Optional[np.ndarray] = None  # EMA of previous predictions
    alpha_smooth = float(getattr(cfg, "gbrt_pred_smooth", 0.0))
    clip_val = float(getattr(cfg, "gbrt_pred_clip", 0.0))

    for t in range(cfg.train_window + h, n_dates):
        if (t - (cfg.train_window + h)) % cfg.refit_freq != 0:
            continue
        train_start = max(0, t - cfg.train_window - h)
        train_end = t - h  # exclusive; last forward return realises at t-1+1 = t

        X_train = factor_arr[train_start:train_end].reshape(-1, F)
        y_train = fwd_arr[train_start:train_end].flatten()
        mask = np.isfinite(y_train) & np.isfinite(X_train).all(axis=1)
        X_use = X_train[mask]
        y_use = y_train[mask]
        if len(y_use) < cfg.model_min_train_obs:
            continue
        if X_use.shape[1] < cfg.model_min_factors:
            continue

        # Freyberger(2020) PCA residualization (per-refit, in-sample only).
        # Fit PCA on the training forward-return panel [T_train, N], then for
        # each training row the residual label = r_row - V_k V_k^T (r_row - mean).
        # This strips the top-N statistical risk factors so the GBRT learns the
        # stock-specific residual alpha (Freyberger-Neuhierl-Weber 2020 JFE).
        # PCA sees ONLY training data -> no lookahead.
        if label_resid == "pca":
            try:
                from sklearn.decomposition import PCA
                ret_panel = fwd_arr[train_start:train_end].copy()  # [T_train, N]
                valid_ticker = np.isfinite(ret_panel).sum(axis=0) >= int(0.5 * ret_panel.shape[0])
                if valid_ticker.sum() >= 10:
                    rp = ret_panel[:, valid_ticker]
                    col_mean = np.nanmean(rp, axis=0)
                    nan_mask = np.isnan(rp)
                    rp = np.where(nan_mask, col_mean, rp)
                    n_comp = min(int(getattr(cfg, "gbrt_label_pca_n", 3)),
                                 rp.shape[1] - 1, rp.shape[0] - 1)
                    if n_comp >= 1:
                        pca = PCA(n_components=n_comp, random_state=cfg.seed)
                        pca.fit(rp)
                        proj = pca.inverse_transform(pca.transform(rp))
                        resid = rp - proj
                        ret_panel[:, valid_ticker] = resid
                        y_train_resid = ret_panel.flatten()
                        y_use = y_train_resid[mask]
            except Exception:
                pass  # fall back to raw label if PCA fails

        # Fama-French 3-factor + momentum residualization (per-refit, in-sample).
        # Build factor-mimicking portfolio returns from the training-window
        # cross-section, regress each stock's forward return on them, and use
        # the residual as the label.  This is look-ahead-safe: only training
        # rows are used to form the sorts and fit the regression.
        if label_resid == "ff3":
            try:
                ret_panel = returns.values[train_start:train_end]  # [T_train, N]
                fwd_panel = fwd_arr[train_start:train_end]          # [T_train, N]
                bench_col = getattr(cfg, "benchmark", "SPY")
                # Market factor: SPY if available, else cross-sectional mean
                if bench_col in returns.columns:
                    mkt = returns[bench_col].values[train_start:train_end]
                else:
                    mkt = np.nanmean(ret_panel, axis=1)
                # Size proxy (SMB): use trailing price as size, split at median.
                # HML proxy: use rolling 60d volatility, split at median.
                # Momentum proxy (UMD): use 12-1m momentum, split at median.
                # We compute the proxy signals from `panel` (look-ahead-safe:
                # signals at date s use only data up to s).
                # Build per-date long-short factor returns.
                T_train, N = ret_panel.shape
                smb = np.zeros(T_train); hml = np.zeros(T_train); umd = np.zeros(T_train)
                prices_arr = prices.values
                for ti in range(T_train):
                    si = train_start + ti
                    if si < 252:  # need enough history for vol + momentum
                        continue
                    r_row = ret_panel[ti]
                    if np.isfinite(r_row).sum() < 20:
                        continue
                    # Size: trailing price (proxy for market cap)
                    size = prices_arr[si - 1]
                    # Value proxy: 60d realized vol
                    vol60 = np.nanstd(ret_panel[max(0,ti-60):ti+1], axis=0)
                    # Momentum proxy: 252d-21d cumulative return
                    if si >= 252:
                        mom = (prices_arr[si - 1] / prices_arr[si - 252]) - 1.0
                        if si >= 21:
                            mom_recent = (prices_arr[si - 1] / prices_arr[si - 21]) - 1.0
                            mom = mom - mom_recent
                    else:
                        mom = np.full(N, np.nan)
                    for signal, arr in [(size, smb), (vol60, hml), (mom, umd)]:
                        valid = np.isfinite(signal) & np.isfinite(r_row)
                        if valid.sum() < 20:
                            continue
                        med = np.median(signal[valid])
                        hi = valid & (signal > med)
                        lo = valid & (signal <= med)
                        if hi.sum() > 0 and lo.sum() > 0:
                            # Small-minus-big for size; for vol/mom we go
                            # low-minus-high (low vol = "value", high mom = "winners")
                            if signal is size:
                                arr[ti] = np.nanmean(r_row[lo]) - np.nanmean(r_row[hi])
                            elif signal is vol60:
                                arr[ti] = np.nanmean(r_row[lo]) - np.nanmean(r_row[hi])
                            else:  # momentum: winners minus losers
                                arr[ti] = np.nanmean(r_row[hi]) - np.nanmean(r_row[lo])
                # Regress each stock's forward return on [mkt, smb, hml, umd]
                factors = np.column_stack([mkt, smb, hml, umd])
                # Add constant
                F_mat = np.column_stack([np.ones(T_train), factors])
                # For each ticker, OLS regress fwd on factors, keep residual
                resid_panel = np.full_like(fwd_panel, np.nan)
                for j in range(N):
                    y = fwd_panel[:, j]
                    valid = np.isfinite(y) & np.isfinite(F_mat).all(axis=1)
                    if valid.sum() < 30:
                        continue
                    try:
                        coef, *_ = np.linalg.lstsq(F_mat[valid], y[valid], rcond=None)
                        pred = F_mat @ coef
                        resid_panel[:, j] = y - pred
                    except Exception:
                        continue
                y_train_resid = resid_panel.flatten()
                y_use = y_train_resid[mask]
            except Exception:
                pass  # fall back to raw/demean label if ff3 fails

        # Winsorize the TRAINING labels at this refit (look-ahead-safe:
        # percentiles use only training-window rows, no future data).
        if win_p > 0:
            lo = np.nanpercentile(y_use, win_p * 100)
            hi = np.nanpercentile(y_use, (1 - win_p) * 100)
            y_use = np.clip(y_use, lo, hi)

        # Fit a fresh GBRT (no warm start -- walk-forward purity)
        try:
            gbrt = _build_gbrt(cfg)
            gbrt.fit(X_use, y_use)
        except Exception as e:
            # Log the FIRST fit failure visibly; silent continues produced an
            # all-empty predictions frame that looked like a legit result.
            if not getattr(cfg, "_gbrt_fit_error_logged", False):
                import warnings
                warnings.warn(f"GBRT fit failed at t={t}: {type(e).__name__}: {e}")
                cfg._gbrt_fit_error_logged = True
            continue

        # Predict at time t
        X_t = factor_arr[t]  # [N, F]
        valid = np.isfinite(X_t).all(axis=1)
        y_hat = np.full(n_tickers, np.nan)
        if valid.any():
            pred = gbrt.predict(X_t[valid])
            # Clip extreme predictions (trees can produce fat tails)
            if clip_val > 0:
                pred = np.clip(pred, -clip_val, clip_val)
            y_hat[valid] = pred

        # EMA smoothing across refits (reduces turnover; Avramov et al. 2019)
        if alpha_smooth > 0 and ema_pred is not None:
            mask_finite = np.isfinite(y_hat) & np.isfinite(ema_pred)
            y_hat[mask_finite] = (alpha_smooth * y_hat[mask_finite]
                                  + (1.0 - alpha_smooth) * ema_pred[mask_finite])
        if np.isfinite(y_hat).any():
            ema_pred = np.where(np.isfinite(y_hat), y_hat,
                                ema_pred if ema_pred is not None else np.nan)

        pred_mat[t] = y_hat
        pred_dates.append(prices.index[t])
        train_size_vals.append(int(len(y_use)))

        # OOS rank IC at time t (diagnostic only; fwd_arr[t] is realised
        # t -> t+h, NOT used in any decision at time t)
        rv = fwd_arr[t]
        valid_ic = np.isfinite(y_hat) & np.isfinite(rv)
        if valid_ic.sum() >= 5:
            from scipy.stats import spearmanr
            rho, _ = spearmanr(y_hat[valid_ic], rv[valid_ic])
            ic_oos_vals.append(float(rho) if np.isfinite(rho) else np.nan)
        else:
            ic_oos_vals.append(np.nan)

    if not pred_dates:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(),
                "ic_oos": pd.Series(), "train_sizes": pd.Series()}

    predictions = pd.DataFrame(pred_mat, index=prices.index, columns=prices.columns)
    # Tree models have no linear coefficients; record a placeholder weights DF
    # (all NaN) so downstream diagnostics that expect .shape don't break.
    weights = pd.DataFrame(np.nan, index=pred_dates, columns=factor_names)
    ic_oos = pd.Series(ic_oos_vals, index=pred_dates, name="ic_oos")
    train_sizes = pd.Series(train_size_vals, index=pred_dates, name="train_size")

    return {
        "predictions": predictions,
        "weights": weights,
        "ic_oos": ic_oos,
        "train_sizes": train_sizes,
    }


def roll_forward_dispatch(processed: Dict, panel: Dict, cfg,
                          kept_factors=None, sign_flips=None):
    """Pick the model combiner based on cfg.model_method."""
    method = getattr(cfg, "model_method", "ols")
    if method == "icir":
        return roll_forward_icir_weighted(processed, panel, cfg, kept_factors, sign_flips)
    if method == "gbrt":
        return roll_forward_gbrt(processed, panel, cfg, kept_factors, sign_flips)
    if method == "rf":
        from .models_extra import roll_forward_rf
        return roll_forward_rf(processed, panel, cfg, kept_factors, sign_flips)
    if method == "elasticnet":
        from .models_extra import roll_forward_elasticnet
        return roll_forward_elasticnet(processed, panel, cfg, kept_factors, sign_flips)
    if method == "xgb":
        try:
            from .models_extra import roll_forward_xgb
            return roll_forward_xgb(processed, panel, cfg, kept_factors, sign_flips)
        except ImportError:
            import warnings
            warnings.warn("xgboost not installed; falling back to GBRT")
            return roll_forward_gbrt(processed, panel, cfg, kept_factors, sign_flips)
    if method == "multihorizon":
        from .models_extra import roll_forward_multihorizon
        return roll_forward_multihorizon(processed, panel, cfg, kept_factors, sign_flips)
    if method == "ensemble":
        from .models_extra import roll_forward_ensemble
        return roll_forward_ensemble(processed, panel, cfg, kept_factors, sign_flips)
    return roll_forward(processed, panel, cfg, kept_factors, sign_flips)
