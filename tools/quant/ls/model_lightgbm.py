"""LightGBM model integration for the L/S framework.

Leaf-wise tree growth with GOSS and EFB. Better regularization than sklearn GBRT.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional


def _build_lgb(cfg):
    try:
        import lightgbm as lgb
    except ImportError:
        raise ImportError("lightgbm not installed: pip install lightgbm")
    return lgb.LGBMRegressor(
        n_estimators=getattr(cfg, "lgb_n_estimators", 200),
        max_depth=getattr(cfg, "lgb_max_depth", 3),
        learning_rate=getattr(cfg, "lgb_learning_rate", 0.05),
        num_leaves=getattr(cfg, "lgb_num_leaves", 31),
        subsample=getattr(cfg, "lgb_subsample", 0.8),
        colsample_bytree=getattr(cfg, "lgb_colsample_bytree", 0.8),
        reg_alpha=getattr(cfg, "lgb_reg_alpha", 0.1),
        reg_lambda=getattr(cfg, "lgb_reg_lambda", 1.0),
        min_child_samples=getattr(cfg, "lgb_min_child_samples", 20),
        boosting_type=getattr(cfg, "lgb_boosting_type", "gbdt"),
        random_state=cfg.seed, n_jobs=-1, verbosity=-1,
    )


def roll_forward_lightgbm(processed, panel, cfg, kept_factors=None, sign_flips=None):
    from scipy.stats import spearmanr
    import warnings

    prices = panel["prices"]
    h = cfg.predict_horizon
    fwd = (prices.shift(-h) / prices) - 1.0
    fwd = fwd.replace([np.inf, -np.inf], np.nan)

    factor_names = kept_factors if kept_factors else list(processed.keys())
    if not factor_names:
        return _empty(prices, factor_names)
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

    label_resid = str(getattr(cfg, "gbrt_label_residual", "none")).lower()
    if label_resid == "demean":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            cs_mean = np.nanmean(fwd_arr, axis=1, keepdims=True)
        cs_mean = np.where(np.isfinite(cs_mean), cs_mean, 0.0)
        fwd_arr = fwd_arr - cs_mean

    label_tf = str(getattr(cfg, "gbrt_label_transform", "raw")).lower()
    if label_tf == "zscore":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            mu = np.nanmean(fwd_arr, axis=1, keepdims=True)
            sd = np.nanstd(fwd_arr, axis=1, keepdims=True)
        mu = np.where(np.isfinite(mu), mu, 0.0)
        sd = np.where(np.isfinite(sd) & (sd > 1e-8), sd, 1.0)
        fwd_arr = (fwd_arr - mu) / sd
    elif label_tf == "sign":
        fwd_arr = np.sign(fwd_arr)

    win_p = float(getattr(cfg, "gbrt_label_winsorize", 0.0))
    alpha_smooth = float(getattr(cfg, "gbrt_pred_smooth", 0.0))
    clip_val = float(getattr(cfg, "gbrt_pred_clip", 0.0))

    pred_mat = np.full((n_dates, n_tickers), np.nan)
    ic_oos_vals, train_size_vals, pred_dates = [], [], []
    ema_pred = None
    t_start = cfg.train_window + h

    for t in range(t_start, n_dates):
        if (t - t_start) % cfg.refit_freq != 0:
            continue
        train_start = max(0, t - cfg.train_window - h)
        train_end = t - h

        X_train = factor_arr[train_start:train_end].reshape(-1, F)
        y_train = fwd_arr[train_start:train_end].flatten()
        mask = np.isfinite(y_train) & np.isfinite(X_train).all(axis=1)
        X_use, y_use = X_train[mask], y_train[mask]
        if len(y_use) < cfg.model_min_train_obs:
            continue
        if X_use.shape[1] < cfg.model_min_factors:
            continue

        if win_p > 0:
            lo = np.nanpercentile(y_use, win_p * 100)
            hi = np.nanpercentile(y_use, (1 - win_p) * 100)
            y_use = np.clip(y_use, lo, hi)

        try:
            lgb_model = _build_lgb(cfg)
            lgb_model.fit(X_use, y_use)
        except Exception:
            continue

        X_t = factor_arr[t]
        valid = np.isfinite(X_t).all(axis=1)
        y_hat = np.full(n_tickers, np.nan)
        if valid.any():
            pred = lgb_model.predict(X_t[valid])
            if clip_val > 0:
                pred = np.clip(pred, -clip_val, clip_val)
            y_hat[valid] = pred

        if alpha_smooth > 0 and ema_pred is not None:
            mf = np.isfinite(y_hat) & np.isfinite(ema_pred)
            y_hat[mf] = alpha_smooth * y_hat[mf] + (1 - alpha_smooth) * ema_pred[mf]
        if np.isfinite(y_hat).any():
            ema_pred = np.where(np.isfinite(y_hat), y_hat,
                                ema_pred if ema_pred is not None else np.nan)

        pred_mat[t] = y_hat
        pred_dates.append(prices.index[t])
        train_size_vals.append(int(len(y_use)))

        rv = fwd_arr[t]
        valid_ic = np.isfinite(y_hat) & np.isfinite(rv)
        if valid_ic.sum() >= 5:
            rho, _ = spearmanr(y_hat[valid_ic], rv[valid_ic])
            ic_oos_vals.append(float(rho) if np.isfinite(rho) else np.nan)
        else:
            ic_oos_vals.append(np.nan)

    if not pred_dates:
        return _empty(prices, factor_names)

    predictions = pd.DataFrame(pred_mat, index=prices.index, columns=prices.columns)
    weights = pd.DataFrame(np.nan, index=pred_dates, columns=factor_names)
    ic_oos = pd.Series(ic_oos_vals, index=pred_dates, name="ic_oos")
    train_sizes = pd.Series(train_size_vals, index=pred_dates, name="train_size")
    return {"predictions": predictions, "weights": weights,
            "ic_oos": ic_oos, "train_sizes": train_sizes}


def _empty(prices, factor_names):
    return {"predictions": pd.DataFrame(index=prices.index, columns=prices.columns),
            "weights": pd.DataFrame(index=prices.index, columns=factor_names),
            "ic_oos": pd.Series(index=prices.index, dtype=float),
            "train_sizes": pd.Series(index=prices.index, dtype=int)}
