"""Extra model implementations: RandomForest, ElasticNet, XGBoost.
Imported by model.py dispatch as needed."""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

# --------------------------------------------------------------------- Random Forest
def _build_rf(cfg):
    from sklearn.ensemble import RandomForestRegressor
    return RandomForestRegressor(
        n_estimators=cfg.rf_n_estimators, max_depth=cfg.rf_max_depth,
        min_samples_leaf=cfg.rf_min_samples_leaf, max_features=cfg.rf_max_features,
        bootstrap=True, random_state=cfg.seed, n_jobs=-1)

def roll_forward_rf(processed, panel, cfg, kept_factors=None, sign_flips=None):
    from scipy.stats import spearmanr
    import warnings
    prices = panel["prices"]; h = cfg.predict_horizon
    fwd = (prices.shift(-h) / prices) - 1.0; fwd = fwd.replace([np.inf, -np.inf], np.nan)
    factor_names = kept_factors if kept_factors else list(processed.keys())
    if not factor_names:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(), "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    if sign_flips is None: sign_flips = {}
    n_dates, n_tickers = prices.shape; F = len(factor_names)
    factor_arr = np.full((n_dates, n_tickers, F), np.nan)
    for fi, name in enumerate(factor_names):
        df = processed[name]; sign = -1.0 if sign_flips.get(name, False) else 1.0
        factor_arr[:, :, fi] = sign * df.values
    fwd_arr = fwd.values
    label_tf = str(getattr(cfg, "gbrt_label_transform", "raw")).lower()
    label_resid = str(getattr(cfg, "gbrt_label_residual", "none")).lower()
    win_p = float(getattr(cfg, "gbrt_label_winsorize", 0.0))
    if label_resid == "demean":
        with warnings.catch_warnings(): warnings.simplefilter("ignore", RuntimeWarning)
        cs_mean = np.nanmean(fwd_arr, axis=1, keepdims=True)
        cs_mean = np.where(np.isfinite(cs_mean), cs_mean, 0.0); fwd_arr = fwd_arr - cs_mean
    elif label_resid == "ff3_real":
        # Real Ken French factor residualization (same block as roll_forward_gbrt).
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
    if label_tf == "zscore":
        with warnings.catch_warnings(): warnings.simplefilter("ignore", RuntimeWarning)
        mu = np.nanmean(fwd_arr, axis=1, keepdims=True); sd = np.nanstd(fwd_arr, axis=1, keepdims=True)
        mu = np.where(np.isfinite(mu), mu, 0.0); sd = np.where(np.isfinite(sd) & (sd > 1e-8), sd, 1.0)
        fwd_arr = (fwd_arr - mu) / sd
    elif label_tf == "sign": fwd_arr = np.sign(fwd_arr)
    pred_mat = np.full((n_dates, n_tickers), np.nan)
    ic_oos_vals, train_size_vals, pred_dates = [], [], []
    ema_pred = None; alpha_smooth = float(getattr(cfg, "gbrt_pred_smooth", 0.0))
    clip_val = float(getattr(cfg, "gbrt_pred_clip", 0.0))
    for t in range(cfg.train_window + h, n_dates):
        if (t - (cfg.train_window + h)) % cfg.refit_freq != 0: continue
        train_start = max(0, t - cfg.train_window - h); train_end = t - h
        X_train = factor_arr[train_start:train_end].reshape(-1, F)
        y_train = fwd_arr[train_start:train_end].flatten()
        mask = np.isfinite(y_train) & np.isfinite(X_train).all(axis=1)
        X_use, y_use = X_train[mask], y_train[mask]
        if len(y_use) < cfg.model_min_train_obs: continue
        if X_use.shape[1] < cfg.model_min_factors: continue
        if win_p > 0:
            lo = np.nanpercentile(y_use, win_p * 100)
            hi = np.nanpercentile(y_use, (1 - win_p) * 100)
            y_use = np.clip(y_use, lo, hi)
        try: rf = _build_rf(cfg); rf.fit(X_use, y_use)
        except Exception: continue
        X_t = factor_arr[t]; valid = np.isfinite(X_t).all(axis=1)
        y_hat = np.full(n_tickers, np.nan)
        if valid.any():
            pred = rf.predict(X_t[valid])
            if clip_val > 0: pred = np.clip(pred, -clip_val, clip_val)
            y_hat[valid] = pred
        if alpha_smooth > 0 and ema_pred is not None:
            mf = np.isfinite(y_hat) & np.isfinite(ema_pred)
            y_hat[mf] = alpha_smooth * y_hat[mf] + (1 - alpha_smooth) * ema_pred[mf]
        if np.isfinite(y_hat).any():
            ema_pred = np.where(np.isfinite(y_hat), y_hat, ema_pred if ema_pred is not None else np.nan)
        pred_mat[t] = y_hat; pred_dates.append(prices.index[t])
        train_size_vals.append(int(len(y_use)))
        rv = fwd_arr[t]; valid_ic = np.isfinite(y_hat) & np.isfinite(rv)
        if valid_ic.sum() >= 5:
            rho, _ = spearmanr(y_hat[valid_ic], rv[valid_ic])
            ic_oos_vals.append(float(rho) if np.isfinite(rho) else np.nan)
        else: ic_oos_vals.append(np.nan)
    if not pred_dates:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(), "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    predictions = pd.DataFrame(pred_mat, index=prices.index, columns=prices.columns)
    weights = pd.DataFrame(np.nan, index=pred_dates, columns=factor_names)
    ic_oos = pd.Series(ic_oos_vals, index=pred_dates, name="ic_oos")
    train_sizes = pd.Series(train_size_vals, index=pred_dates, name="train_size")
    return {"predictions": predictions, "weights": weights, "ic_oos": ic_oos, "train_sizes": train_sizes}


# --------------------------------------------------------------------- ElasticNet
def _build_elasticnet(cfg):
    from sklearn.linear_model import ElasticNetCV
    alphas = [1e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1]
    l1_ratios = [0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 1.0]
    return ElasticNetCV(l1_ratio=l1_ratios, alphas=alphas, cv=min(5, cfg.enet_cv_folds),
                       max_iter=2000, tol=1e-4, random_state=cfg.seed, selection="cyclic")

def roll_forward_elasticnet(processed, panel, cfg, kept_factors=None, sign_flips=None):
    from scipy.stats import spearmanr
    prices = panel["prices"]; h = cfg.predict_horizon
    fwd = (prices.shift(-h) / prices) - 1.0; fwd = fwd.replace([np.inf, -np.inf], np.nan)
    factor_names = kept_factors if kept_factors else list(processed.keys())
    if not factor_names:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(), "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    if sign_flips is None: sign_flips = {}
    n_dates, n_tickers = prices.shape; F = len(factor_names)
    factor_arr = np.full((n_dates, n_tickers, F), np.nan)
    for fi, name in enumerate(factor_names):
        df = processed[name]; sign = -1.0 if sign_flips.get(name, False) else 1.0
        factor_arr[:, :, fi] = sign * df.values
    fwd_arr = fwd.values
    pred_dates, pred_mat, weight_mat, ic_oos_vals, train_size_vals = [], [], [], [], []
    ema_beta = None; t_start = cfg.train_window + h
    for t in range(t_start, n_dates):
        if (t - t_start) % cfg.refit_freq != 0: continue
        train_start = max(0, t - cfg.train_window - h); train_end = t - h
        if train_end - train_start < cfg.model_min_train_obs: continue
        X_train = factor_arr[train_start:train_end].reshape(-1, F)
        y_train = fwd_arr[train_start:train_end].flatten()
        mask = np.isfinite(y_train) & np.isfinite(X_train).all(axis=1)
        X_use, y_use = X_train[mask], y_train[mask]
        if len(y_use) < cfg.model_min_train_obs: continue
        if X_use.shape[1] < cfg.model_min_factors: continue
        X_mean = X_use.mean(axis=0); X_std = X_use.std(axis=0, ddof=0)
        X_std = np.where(X_std < 1e-8, 1.0, X_std); X_scaled = (X_use - X_mean) / X_std
        try: enet = _build_elasticnet(cfg); enet.fit(X_scaled, y_use); beta = enet.coef_ / X_std
        except Exception: beta = np.zeros(F)
        max_w = cfg.model_max_factor_weight; beta = np.clip(beta, -max_w, max_w)
        if cfg.model_weight_smooth > 0 and ema_beta is not None:
            alpha = cfg.model_weight_smooth; beta = alpha * beta + (1 - alpha) * ema_beta
        ema_beta = beta.copy()
        X_t = factor_arr[t]; valid = np.isfinite(X_t).all(axis=1)
        y_hat = np.full(n_tickers, np.nan)
        if valid.any(): y_hat[valid] = X_t[valid] @ beta
        pred_dates.append(prices.index[t]); pred_mat.append(y_hat)
        weight_mat.append(beta); train_size_vals.append(len(y_use))
        rv = fwd_arr[t]; v = np.isfinite(y_hat) & np.isfinite(rv)
        if v.sum() >= 5:
            rho, _ = spearmanr(y_hat[v], rv[v])
            ic_oos_vals.append(float(rho) if np.isfinite(rho) else np.nan)
        else: ic_oos_vals.append(np.nan)
    predictions = pd.DataFrame(pred_mat, index=pred_dates, columns=prices.columns)
    weights = pd.DataFrame(weight_mat, index=pred_dates, columns=factor_names)
    ic_oos = pd.Series(ic_oos_vals, index=pred_dates, name="ic_oos")
    train_sizes = pd.Series(train_size_vals, index=pred_dates, name="train_size")
    return {"predictions": predictions, "weights": weights, "ic_oos": ic_oos, "train_sizes": train_sizes}


# --------------------------------------------------------------------- XGBoost (requires xgboost package)
def _build_xgb(cfg):
    try:
        import xgboost as xgb
    except ImportError:
        raise ImportError("xgboost not installed; run: pip install xgboost")
    return xgb.XGBRegressor(
        n_estimators=cfg.xgb_n_estimators, max_depth=cfg.xgb_max_depth,
        learning_rate=cfg.xgb_learning_rate, subsample=cfg.xgb_subsample,
        colsample_bytree=cfg.xgb_colsample_bytree, reg_alpha=cfg.xgb_reg_alpha,
        reg_lambda=cfg.xgb_reg_lambda, min_child_weight=cfg.xgb_min_child_weight,
        random_state=cfg.seed, n_jobs=-1, verbosity=0)

def roll_forward_xgb(processed, panel, cfg, kept_factors=None, sign_flips=None):
    from scipy.stats import spearmanr
    import warnings
    prices = panel["prices"]; h = cfg.predict_horizon
    fwd = (prices.shift(-h) / prices) - 1.0; fwd = fwd.replace([np.inf, -np.inf], np.nan)
    factor_names = kept_factors if kept_factors else list(processed.keys())
    if not factor_names:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(), "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    if sign_flips is None: sign_flips = {}
    n_dates, n_tickers = prices.shape; F = len(factor_names)
    factor_arr = np.full((n_dates, n_tickers, F), np.nan)
    for fi, name in enumerate(factor_names):
        df = processed[name]; sign = -1.0 if sign_flips.get(name, False) else 1.0
        factor_arr[:, :, fi] = sign * df.values
    fwd_arr = fwd.values
    label_tf = str(getattr(cfg, "gbrt_label_transform", "raw")).lower()
    label_resid = str(getattr(cfg, "gbrt_label_residual", "none")).lower()
    win_p = float(getattr(cfg, "gbrt_label_winsorize", 0.0))
    if label_resid == "demean":
        with warnings.catch_warnings(): warnings.simplefilter("ignore", RuntimeWarning)
        cs_mean = np.nanmean(fwd_arr, axis=1, keepdims=True)
        cs_mean = np.where(np.isfinite(cs_mean), cs_mean, 0.0); fwd_arr = fwd_arr - cs_mean
    elif label_resid == "ff3_real":
        # Real Ken French factor residualization (same block as roll_forward_gbrt).
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
    if label_tf == "zscore":
        with warnings.catch_warnings(): warnings.simplefilter("ignore", RuntimeWarning)
        mu = np.nanmean(fwd_arr, axis=1, keepdims=True); sd = np.nanstd(fwd_arr, axis=1, keepdims=True)
        mu = np.where(np.isfinite(mu), mu, 0.0); sd = np.where(np.isfinite(sd) & (sd > 1e-8), sd, 1.0)
        fwd_arr = (fwd_arr - mu) / sd
    elif label_tf == "sign": fwd_arr = np.sign(fwd_arr)
    pred_mat = np.full((n_dates, n_tickers), np.nan)
    ic_oos_vals, train_size_vals, pred_dates = [], [], []
    ema_pred = None; alpha_smooth = float(getattr(cfg, "gbrt_pred_smooth", 0.0))
    clip_val = float(getattr(cfg, "gbrt_pred_clip", 0.0))
    for t in range(cfg.train_window + h, n_dates):
        if (t - (cfg.train_window + h)) % cfg.refit_freq != 0: continue
        train_start = max(0, t - cfg.train_window - h); train_end = t - h
        X_train = factor_arr[train_start:train_end].reshape(-1, F)
        y_train = fwd_arr[train_start:train_end].flatten()
        mask = np.isfinite(y_train) & np.isfinite(X_train).all(axis=1)
        X_use, y_use = X_train[mask], y_train[mask]
        if len(y_use) < cfg.model_min_train_obs: continue
        if X_use.shape[1] < cfg.model_min_factors: continue
        if win_p > 0:
            lo = np.nanpercentile(y_use, win_p * 100)
            hi = np.nanpercentile(y_use, (1 - win_p) * 100)
            y_use = np.clip(y_use, lo, hi)
        try: xgb_model = _build_xgb(cfg); xgb_model.fit(X_use, y_use)
        except Exception: continue
        X_t = factor_arr[t]; valid = np.isfinite(X_t).all(axis=1)
        y_hat = np.full(n_tickers, np.nan)
        if valid.any():
            pred = xgb_model.predict(X_t[valid])
            if clip_val > 0: pred = np.clip(pred, -clip_val, clip_val)
            y_hat[valid] = pred
        if alpha_smooth > 0 and ema_pred is not None:
            mf = np.isfinite(y_hat) & np.isfinite(ema_pred)
            y_hat[mf] = alpha_smooth * y_hat[mf] + (1 - alpha_smooth) * ema_pred[mf]
        if np.isfinite(y_hat).any():
            ema_pred = np.where(np.isfinite(y_hat), y_hat, ema_pred if ema_pred is not None else np.nan)
        pred_mat[t] = y_hat; pred_dates.append(prices.index[t])
        train_size_vals.append(int(len(y_use)))
        rv = fwd_arr[t]; valid_ic = np.isfinite(y_hat) & np.isfinite(rv)
        if valid_ic.sum() >= 5:
            rho, _ = spearmanr(y_hat[valid_ic], rv[valid_ic])
            ic_oos_vals.append(float(rho) if np.isfinite(rho) else np.nan)
        else: ic_oos_vals.append(np.nan)
    if not pred_dates:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(), "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    predictions = pd.DataFrame(pred_mat, index=prices.index, columns=prices.columns)
    weights = pd.DataFrame(np.nan, index=pred_dates, columns=factor_names)
    ic_oos = pd.Series(ic_oos_vals, index=pred_dates, name="ic_oos")
    train_sizes = pd.Series(train_size_vals, index=pred_dates, name="train_size")
    return {"predictions": predictions, "weights": weights, "ic_oos": ic_oos, "train_sizes": train_sizes}

# --------------------------------------------------------------------- Ensemble (GBRT + RF prediction averaging)
def roll_forward_ensemble(processed, panel, cfg, kept_factors=None, sign_flips=None):
    """Ensemble: average cross-sectionally z-scored GBRT d=2 and RF predictions.

    For each refit: train GBRT(d=2) and RandomForest independently,
    cross-sectionally z-score each prediction set, then average.
    EMA-smooths the combined predictions via cfg.gbrt_pred_smooth.
    """
    from scipy.stats import spearmanr
    import warnings
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor

    prices = panel["prices"]; h = cfg.predict_horizon
    fwd = (prices.shift(-h) / prices) - 1.0
    fwd = fwd.replace([np.inf, -np.inf], np.nan)

    factor_names = kept_factors if kept_factors else list(processed.keys())
    if not factor_names:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(),
                "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    if sign_flips is None: sign_flips = {}

    n_dates, n_tickers = prices.shape; F = len(factor_names)
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

    win_p = float(getattr(cfg, "gbrt_label_winsorize", 0.0))
    clip_val = float(getattr(cfg, "gbrt_pred_clip", 0.0))
    alpha_smooth = float(getattr(cfg, "gbrt_pred_smooth", 0.0))
    gb_depth = int(getattr(cfg, "gbrt_max_depth", 2))
    gb_n_est = int(getattr(cfg, "gbrt_n_estimators", 200))
    gb_lr = float(getattr(cfg, "gbrt_learning_rate", 0.05))
    gb_leaf = int(getattr(cfg, "gbrt_min_samples_leaf", 20))
    gb_sub = float(getattr(cfg, "gbrt_subsample", 1.0))
    rf_depth = int(getattr(cfg, "rf_max_depth", 3))
    rf_n_est = int(getattr(cfg, "rf_n_estimators", 500))
    rf_leaf = int(getattr(cfg, "rf_min_samples_leaf", 20))

    pred_mat = np.full((n_dates, n_tickers), np.nan)
    ic_oos_vals, train_size_vals, pred_dates = [], [], []
    ema_pred = None

    for t in range(cfg.train_window + h, n_dates):
        if (t - (cfg.train_window + h)) % cfg.refit_freq != 0:
            continue
        train_start = max(0, t - cfg.train_window - h); train_end = t - h
        X_train = factor_arr[train_start:train_end].reshape(-1, F)
        y_train = fwd_arr[train_start:train_end].flatten()
        mask = np.isfinite(y_train) & np.isfinite(X_train).all(axis=1)
        X_use, y_use = X_train[mask], y_train[mask]
        if len(y_use) < cfg.model_min_train_obs: continue
        if X_use.shape[1] < cfg.model_min_factors: continue
        if win_p > 0:
            lo = np.nanpercentile(y_use, win_p*100)
            hi = np.nanpercentile(y_use, (1-win_p)*100)
            y_use = np.clip(y_use, lo, hi)

        X_t = factor_arr[t]; valid = np.isfinite(X_t).all(axis=1)
        y_hat = np.full(n_tickers, np.nan); pred_list = []

        # 1. GBRT prediction
        try:
            gb = GradientBoostingRegressor(
                n_estimators=gb_n_est, max_depth=gb_depth,
                learning_rate=gb_lr, subsample=gb_sub,
                min_samples_leaf=gb_leaf, max_features="sqrt",
                random_state=cfg.seed)
            gb.fit(X_use, y_use)
            if valid.any():
                p = gb.predict(X_t[valid])
                if clip_val > 0: p = np.clip(p, -clip_val, clip_val)
                pm, ps = np.nanmean(p), np.nanstd(p)
                if ps > 1e-8: p = (p - pm) / ps
                pred_list.append(p)
        except Exception: pass

        # 2. RF prediction
        try:
            rf = RandomForestRegressor(
                n_estimators=rf_n_est, max_depth=rf_depth,
                min_samples_leaf=rf_leaf, max_features="sqrt",
                bootstrap=True, random_state=cfg.seed+1, n_jobs=-1)
            rf.fit(X_use, y_use)
            if valid.any():
                p = rf.predict(X_t[valid])
                if clip_val > 0: p = np.clip(p, -clip_val, clip_val)
                pm, ps = np.nanmean(p), np.nanstd(p)
                if ps > 1e-8: p = (p - pm) / ps
                pred_list.append(p)
        except Exception: pass

        if not pred_list: continue

        avg = np.zeros(valid.sum())
        for p in pred_list: avg += p
        avg /= len(pred_list)
        y_hat[valid] = avg

        if alpha_smooth > 0 and ema_pred is not None:
            mf = np.isfinite(y_hat) & np.isfinite(ema_pred)
            y_hat[mf] = alpha_smooth*y_hat[mf] + (1-alpha_smooth)*ema_pred[mf]
        if np.isfinite(y_hat).any():
            ema_pred = np.where(np.isfinite(y_hat), y_hat,
                ema_pred if ema_pred is not None else np.nan)

        pred_mat[t] = y_hat; pred_dates.append(prices.index[t])
        train_size_vals.append(int(len(y_use)))
        rv = fwd_arr[t]; vic = np.isfinite(y_hat) & np.isfinite(rv)
        if vic.sum() >= 5:
            rho,_ = spearmanr(y_hat[vic], rv[vic])
            ic_oos_vals.append(float(rho) if np.isfinite(rho) else np.nan)
        else: ic_oos_vals.append(np.nan)

    if not pred_dates:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(),
                "ic_oos": pd.Series(), "train_sizes": pd.Series()}

    predictions = pd.DataFrame(pred_mat, index=prices.index, columns=prices.columns)
    weights = pd.DataFrame(np.nan, index=pred_dates, columns=factor_names)
    ic_oos = pd.Series(ic_oos_vals, index=pred_dates, name="ic_oos")
    train_sizes = pd.Series(train_size_vals, index=pred_dates, name="train_size")
    return {"predictions": predictions, "weights": weights,
            "ic_oos": ic_oos, "train_sizes": train_sizes}


# --------------------------------------------------------------------- Multi-Horizon Ensemble
def roll_forward_multihorizon(processed, panel, cfg, kept_factors=None, sign_flips=None):
    """Blend GBRT predictions from multiple horizons weighted by rolling OOS IC.

    Trains separate GBRT models for each horizon in cfg.predict_horizons (e.g.,
    [5, 10, 21]). For each refit date, computes predictions at each horizon,
    then blends them with weights proportional to each horizon's recent OOS IC.

    This exploits the low correlation (~0.53) between short-term (h=5) and
    medium-term (h=10) GBRT predictions, increasing effective breadth without
    requiring additional data.
    """
    from scipy.stats import spearmanr
    import warnings
    from sklearn.ensemble import GradientBoostingRegressor

    prices = panel["prices"]
    horizons = list(getattr(cfg, "predict_horizons", [5, 10, 21]))
    factor_names = kept_factors if kept_factors else list(processed.keys())
    if not factor_names or not horizons:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(),
                "ic_oos": pd.Series(), "train_sizes": pd.Series()}
    if sign_flips is None: sign_flips = {}

    n_dates, n_tickers = prices.shape; F = len(factor_names)
    factor_arr = np.full((n_dates, n_tickers, F), np.nan)
    for fi, name in enumerate(factor_names):
        df = processed[name]
        sign = -1.0 if sign_flips.get(name, False) else 1.0
        factor_arr[:, :, fi] = sign * df.values

    # Build fwd_arr for each horizon
    fwd_arrs = {}
    for h in horizons:
        fwd = (prices.shift(-h) / prices) - 1.0
        fwd = fwd.replace([np.inf, -np.inf], np.nan)
        fwd_arr = fwd.values

        # Label preprocessing
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
        fwd_arrs[h] = fwd_arr

    win_p = float(getattr(cfg, "gbrt_label_winsorize", 0.0))
    clip_val = float(getattr(cfg, "gbrt_pred_clip", 0.0))
    alpha_smooth = float(getattr(cfg, "gbrt_pred_smooth", 0.0))
    gb_depth = int(getattr(cfg, "gbrt_max_depth", 2))
    gb_n_est = int(getattr(cfg, "gbrt_n_estimators", 200))
    gb_lr = float(getattr(cfg, "gbrt_learning_rate", 0.05))
    gb_leaf = int(getattr(cfg, "gbrt_min_samples_leaf", 20))
    gb_sub = float(getattr(cfg, "gbrt_subsample", 1.0))

    # Track rolling OOS IC per horizon for adaptive weighting
    ic_rolling = {h: [] for h in horizons}
    ic_window = 5  # use last 5 refits to weight horizons

    pred_mat = np.full((n_dates, n_tickers), np.nan)
    ic_oos_vals, train_size_vals, pred_dates = [], [], []
    ema_pred = None

    for t in range(cfg.train_window + max(horizons), n_dates):
        if (t - (cfg.train_window + max(horizons))) % cfg.refit_freq != 0:
            continue

        horizon_preds = {}  # h -> predictions array
        for h in horizons:
            train_start = max(0, t - cfg.train_window - h)
            train_end = t - h
            X_train = factor_arr[train_start:train_end].reshape(-1, F)
            y_train = fwd_arrs[h][train_start:train_end].flatten()
            mask = np.isfinite(y_train) & np.isfinite(X_train).all(axis=1)
            X_use, y_use = X_train[mask], y_train[mask]
            if len(y_use) < cfg.model_min_train_obs: continue
            if X_use.shape[1] < cfg.model_min_factors: continue
            if win_p > 0:
                lo = np.nanpercentile(y_use, win_p*100)
                hi = np.nanpercentile(y_use, (1-win_p)*100)
                y_use = np.clip(y_use, lo, hi)

            X_t = factor_arr[t]; valid = np.isfinite(X_t).all(axis=1)
            if not valid.any(): continue

            try:
                gb = GradientBoostingRegressor(
                    n_estimators=gb_n_est, max_depth=gb_depth,
                    learning_rate=gb_lr, subsample=gb_sub,
                    min_samples_leaf=gb_leaf, max_features="sqrt",
                    random_state=cfg.seed + h)
                gb.fit(X_use, y_use)
                p = gb.predict(X_t[valid])
                if clip_val > 0: p = np.clip(p, -clip_val, clip_val)
                # Cross-sectional z-score
                pm, ps = np.nanmean(p), np.nanstd(p)
                if ps > 1e-8: p = (p - pm) / ps
                horizon_preds[h] = (valid, p)
            except Exception: pass

        if not horizon_preds: continue

        # Blend predictions using rolling IC weights
        weights = {}
        for h in horizons:
            if h in horizon_preds and h in ic_rolling:
                recent = ic_rolling[h][-ic_window:] if len(ic_rolling[h]) >= ic_window else ic_rolling[h]
                if recent:
                    mean_ic = np.nanmean([abs(x) for x in recent if np.isfinite(x)])
                    weights[h] = max(mean_ic, 0.01)  # floor weight
        if not weights:
            # Equal weight fallback
            for h in horizon_preds: weights[h] = 1.0
        else:
            # Horizons with predictions but no IC history yet get the floor
            # weight so the blend never KeyErrors on a missing entry.
            for h in horizon_preds:
                if h not in weights:
                    weights[h] = 0.01

        total_w = sum(weights.values())
        if total_w == 0: continue

        y_hat = np.full(n_tickers, np.nan)
        # All horizon predictions use the same valid mask (X_t valid)
        valid = list(horizon_preds.values())[0][0]
        blended = np.zeros(valid.sum())
        for h, (v, p) in horizon_preds.items():
            w = weights[h] / total_w
            blended += w * p
        y_hat[valid] = blended

        if alpha_smooth > 0 and ema_pred is not None:
            mf = np.isfinite(y_hat) & np.isfinite(ema_pred)
            y_hat[mf] = alpha_smooth*y_hat[mf] + (1-alpha_smooth)*ema_pred[mf]
        if np.isfinite(y_hat).any():
            ema_pred = np.where(np.isfinite(y_hat), y_hat,
                ema_pred if ema_pred is not None else np.nan)

        pred_mat[t] = y_hat; pred_dates.append(prices.index[t])
        train_size_vals.append(int(len(y_use)))

        # Track OOS IC for the reference horizon (cfg.predict_horizon)
        ref_h = int(getattr(cfg, "predict_horizon", 10))
        if ref_h in fwd_arrs:
            rv = fwd_arrs[ref_h][t]
            vic = np.isfinite(y_hat) & np.isfinite(rv)
            if vic.sum() >= 5:
                rho, _ = spearmanr(y_hat[vic], rv[vic])
                ic_oos_vals.append(float(rho) if np.isfinite(rho) else np.nan)
            else: ic_oos_vals.append(np.nan)
        else: ic_oos_vals.append(np.nan)

        # Update rolling IC per horizon (diagnostic, not used for weighting until next refit)
        for h in horizons:
            if h in fwd_arrs and h in horizon_preds:
                rv = fwd_arrs[h][t]
                vic = np.isfinite(y_hat) & np.isfinite(rv)
                if vic.sum() >= 5:
                    rho, _ = spearmanr(y_hat[vic], rv[vic])
                    ic_rolling[h].append(float(rho) if np.isfinite(rho) else 0.0)
                else:
                    ic_rolling[h].append(0.0)

    if not pred_dates:
        return {"predictions": pd.DataFrame(), "weights": pd.DataFrame(),
                "ic_oos": pd.Series(), "train_sizes": pd.Series()}

    predictions = pd.DataFrame(pred_mat, index=prices.index, columns=prices.columns)
    weights = pd.DataFrame(np.nan, index=pred_dates, columns=factor_names)
    ic_oos = pd.Series(ic_oos_vals, index=pred_dates, name="ic_oos")
    train_sizes = pd.Series(train_size_vals, index=pred_dates, name="train_size")
    return {"predictions": predictions, "weights": weights,
            "ic_oos": ic_oos, "train_sizes": train_sizes}
