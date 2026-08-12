"""Real Fama-French daily factor data (Ken French Data Library).

Downloaded 2026-08-04 from:
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip
Files cover 1926-07-01 -> 2026-06-30 (202606 CRSP database).

This module implements the user's core research idea: predict the
French-Fama risk-adjusted RESIDUAL return.  Instead of the crude
mimicking-portfolio proxies used by the original `ff3` option in model.py
(price=size, vol=HML), we regress each stock's daily returns on the REAL
published Fama-French factors (Mkt-RF, SMB, HML, UMD, RF) and residualize
the forward return.  Rolling betas are estimated with trailing data only
(look-ahead-safe), and the factor return over the prediction horizon is
realized by the time the training row is used (future-function guard).

Units: factors are stored in decimal (percent / 100).
"""
from __future__ import annotations
import os
from typing import Optional

import numpy as np
import pandas as pd

FF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "ff_factors")

FF3_FILE = "F-F_Research_Data_Factors_daily.csv"      # ,Mkt-RF,SMB,HML,RF
UMD_FILE = "F-F_Momentum_Factor_daily.csv"            # date,MOM (no header)


def load_ff_factors(data_dir: Optional[str] = None) -> pd.DataFrame:
    """Load real FF daily factors -> DataFrame[date, MktRF, SMB, HML, UMD, RF].

    Dates parsed from YYYYMMDD; factor values converted percent -> decimal.
    """
    d = data_dir or FF_DIR
    # FF3 file: 4 description lines + 1 header line, data starts line 6.
    ff3 = pd.read_csv(
        os.path.join(d, FF3_FILE), skiprows=5, index_col=0,
        names=["date", "MktRF", "SMB", "HML", "RF"],
        skipinitialspace=True, na_values=["", "NA"],
    )
    # Momentum file has NO header: 14 description lines, data starts line 15.
    umd = pd.read_csv(
        os.path.join(d, UMD_FILE), skiprows=14, index_col=0, header=None,
        names=["date", "UMD"], skipinitialspace=True, na_values=["", "NA"],
    )
    ff = ff3.join(umd, how="inner")
    ff.index = pd.to_datetime(ff.index, format="%Y%m%d", errors="coerce")
    ff = ff[ff.index.notna()]  # drop copyright/footer text rows
    ff = ff / 100.0
    ff = ff.sort_index()
    return ff[["MktRF", "SMB", "HML", "UMD", "RF"]]


def _rolling_betas(returns_simple: pd.DataFrame, ff: pd.DataFrame,
                   beta_window: int = 60, min_obs: int = 30,
                   factor_cols=("MktRF", "SMB", "HML", "UMD")) -> np.ndarray:
    """Trailing-window OLS betas of each stock's excess return on FF factors.

    returns_simple: DataFrame[T, N] of SIMPLE daily returns aligned to ff.
    ff: DataFrame[T, 5] with columns MktRF, SMB, HML, UMD, RF (decimal).
    factor_cols: subset of [MktRF, SMB, HML, UMD] to regress on.

    Returns ndarray[T, N, K]: beta(t, ticker, factor) (NaN where the
    window is too short).

    Efficiency: the design matrix X_t (intercept + factor returns over the
    trailing window) is identical across tickers, so per date we precompute
    the (K+1) x obs pseudo-inverse ONCE and apply it to every ticker's
    windowed returns with one matmul.
    """
    T, N = returns_simple.shape
    factor_cols = list(factor_cols)
    K = len(factor_cols)
    X_core = ff[factor_cols].values
    rf = ff["RF"].values
    y_excess = returns_simple.values - rf[:, None]  # [T, N]

    # Beta[.., K] for every (t, ticker); beta index order = factor_cols
    betas = np.full((T, N, K), np.nan)

    for t in range(T):
        s0 = max(0, t - beta_window + 1)
        X = np.column_stack([np.ones(t - s0 + 1), X_core[s0:t + 1]])
        if X.shape[0] < min_obs:
            continue
        try:
            M = np.linalg.pinv(X)  # [4+1, obs]
        except np.linalg.LinAlgError:
            continue
        Y = y_excess[s0:t + 1]  # [obs, N]
        coef = M @ Y            # [4+1, N]
        betas[t] = coef[1:].T   # drop intercept
    return betas


def compute_ff3_resid(returns_simple: pd.DataFrame, prices: pd.DataFrame,
                      h: int, ff: pd.DataFrame,
                      beta_window: int = 60, min_obs: int = 30,
                      factors: str = "ff3umd") -> pd.DataFrame:
    """Residual forward return: r_{t,t+h} - beta(t) @ F_{t,t+h}.

    Look-ahead safety:
      - beta(t) uses only returns through t (trailing window).
      - F_{t,t+h} (factor cumulative return over the horizon) is realized at
        t+h; rows with t+h beyond the data end get NaN and are excluded from
        training by the walk-forward guard (train rows end at t-h).
      - No full-sample statistics anywhere.

    factors: 'ff3umd' = strip Mkt/SMB/HML/UMD; 'ff3' = strip Mkt/SMB/HML only
      (keep the momentum premium in the label -- the strategy's core signal);
      'mkt' = strip Mkt-RF only (CAPM alpha -- the purest risk-adjusted
      residual; keeps size/value/momentum cross-sectional signal intact).

    Returns DataFrame[T, N] of residual forward returns (simple, decimal),
    aligned to `returns_simple.index` / `prices.columns`.
    """
    if factors == "mkt":
        factor_cols = ["MktRF"]
    else:
        factor_cols = list(("MktRF", "SMB", "HML") + (("UMD",) if factors != "ff3" else ()))
    ff = ff.reindex(returns_simple.index).ffill().reindex(returns_simple.index)
    ff = ff.reindex(returns_simple.index)  # keep NaN where FF missing
    ff = ff[factor_cols + ["RF"]]
    # Safety: only rows where FF data exists
    ff_valid = ff.notna().all(axis=1)

    betas = _rolling_betas(returns_simple, ff, beta_window=beta_window,
                           min_obs=min_obs, factor_cols=factor_cols)

    # Factor cumulative return over (t, t+h]
    T = len(returns_simple)
    K = len(factor_cols)
    F_cum = np.full((T, K), np.nan)
    fwd_rf = np.full(T, np.nan)
    fwd = (prices.shift(-h) / prices) - 1.0
    fwd = fwd.replace([np.inf, -np.inf], np.nan)
    for t in range(T):
        s1 = t + 1
        s2 = min(t + h, T - 1)
        if s2 <= s1 or not ff_valid.iloc[s1:s2 + 1].all():
            continue
        cum = (1.0 + ff[factor_cols].iloc[s1:s2 + 1]).prod() - 1.0
        F_cum[t] = cum.values
        fwd_rf[t] = (1.0 + ff["RF"].iloc[s1:s2 + 1]).prod() - 1.0

    # residual = (fwd - RF_fwd) - beta @ F_cum
    # NaN propagates: NaN beta or NaN F_cum -> NaN residual (row excluded).
    fc = np.nan_to_num(F_cum, nan=0.0)
    pred = np.einsum("tnk,tk->tn", betas, fc)
    bad = ~np.isfinite(F_cum).all(axis=1)
    pred[bad] = np.nan
    resid = fwd.values - fwd_rf[:, None] - pred
    resid_df = pd.DataFrame(resid, index=returns_simple.index, columns=returns_simple.columns)
    return resid_df
