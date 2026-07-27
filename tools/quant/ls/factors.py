"""Factor library: 12 alpha factors computed from price/volume only.

All factors are computed *cross-sectionally* and produce a DataFrame[T, N]
of factor exposures, indexed same as prices.  At each date t, the factor
value uses ONLY information up to and including t (no look-ahead).

Factor families (configurable window params):
  Momentum (6):
    mom_1m, mom_3m, mom_6m, mom_12m          -- past return, skip last `mom_skip_recent`
    mom_12_1m                                 -- 12m-1m (classic momentum)
    high_dist                                 -- distance from 52w high (crash proxy)
  Reversal (2):
    reversal_1w, reversal_3w                  -- short-term reversal
  Volatility / Risk (2):
    vol_60d                                   -- realized vol (excluding last N days)
    skew_60d                                  -- return skewness
  Value / Trend proxies (4):
    ma_dev_200, ma_dev_50                     -- price/MA deviation (no fundamentals)
    vol_surprise                              -- volume / avg volume
    liq_turnover                              -- avg turnover ratio (liquidity)

Cross-sectional processing:
  1. winsorize at p / (1-p) quantiles
  2. (optional) market-neutralize residuals
  3. z-score to mean 0, std 1

Output: dict of DataFrames keyed by factor name + a combined DataFrame.
"""
from __future__ import annotations
import os, sys
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

# tools/quant/ls/factors.py -> up 3 to repo root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from .data import FutureFunctionError  # re-export for convenience


# --------------------------------------------------------------------- helpers
def _winsorize_cross(s: pd.Series, p: float) -> pd.Series:
    """Cross-sectional winsorize: clip values below p-quantile and above (1-p)-quantile."""
    if s.dropna().empty:
        return s
    lo = s.quantile(p)
    hi = s.quantile(1 - p)
    return s.clip(lower=lo, upper=hi)


def _zscore_cross(s: pd.Series) -> pd.Series:
    """Cross-sectional z-score (mean 0, std 1) at each date."""
    mu = s.mean()
    sd = s.std(ddof=0)
    if not np.isfinite(sd) or sd == 0:
        return s * 0.0
    return (s - mu) / sd


def _market_neutralize_cross(df: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Demean each row by the cross-sectional mean (market-cap proxy = equal-weight).

    For each date, subtract the cross-sectional mean factor exposure.  This is
    a simple 'market' neutralization (no sector data available).  Returns the
    residualized factor matrix.
    """
    row_mean = df.mean(axis=1)
    return df.sub(row_mean, axis=0)


def _rolling_mom(prices: pd.DataFrame, window: int, skip: int) -> pd.DataFrame:
    """Momentum = P_{t-skip} / P_{t-window-skip} - 1, computed per ticker.

    Uses a shift to skip the most recent `skip` days (short-term reversal
    contamination).  Look-ahead safe: shift(k) at time t uses data at t-k.
    """
    if window <= 0 or skip < 0:
        return pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    p_lag = prices.shift(window + skip)
    p_skip = prices.shift(skip)
    out = (p_skip / p_lag) - 1.0
    # Replace inf with nan
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def _rolling_reversal(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Short-term reversal = P_{t} / P_{t-window} - 1 (no skip)."""
    if window <= 0:
        return pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    out = (prices / prices.shift(window)) - 1.0
    return out.replace([np.inf, -np.inf], np.nan)


def _rolling_vol(returns: pd.DataFrame, window: int, skip: int) -> pd.DataFrame:
    """Realized volatility over `window` days, excluding the last `skip` days.

    vol_{t} = std(returns_{t-window-skip .. t-skip-1}).  Excluding the most
    recent `skip` days avoids contamination with the short-term reversal
    factor and the forward return.
    """
    if window <= 0:
        return pd.DataFrame(np.nan, index=returns.index, columns=returns.columns)
    # We compute rolling std on the shifted returns (shift by `skip`) so that
    # at time t the window covers [t-window-skip, t-skip-1].
    shifted = returns.shift(skip)
    out = shifted.rolling(window, min_periods=max(10, window // 2)).std(ddof=0)
    return out * np.sqrt(252.0)  # annualized


def _rolling_skew(returns: pd.DataFrame, window: int, skip: int) -> pd.DataFrame:
    """Rolling skewness of returns, excluding last `skip` days."""
    if window <= 0:
        return pd.DataFrame(np.nan, index=returns.index, columns=returns.columns)
    shifted = returns.shift(skip)
    out = shifted.rolling(window, min_periods=max(20, window // 2)).skew()
    return out


def _ma_dev(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Price / MA(window) - 1.  Value/trend proxy."""
    if window <= 0:
        return pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    ma = prices.rolling(window, min_periods=max(20, window // 2)).mean()
    out = (prices / ma) - 1.0
    return out.replace([np.inf, -np.inf], np.nan)


def _high_dist(prices: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """Distance from `lookback`-day high: P_t / max(P_{t-lookback..t}) - 1.

    Always <= 0.  Large negative = far from high (momentum crash proxy).
    Look-ahead safe: rolling max includes current day (known at t).
    """
    if lookback <= 0:
        return pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    hi = prices.rolling(lookback, min_periods=max(20, lookback // 2)).max()
    out = (prices / hi) - 1.0
    return out.replace([np.inf, -np.inf], np.nan)


def _vol_surprise(volumes: pd.DataFrame, window: int) -> pd.DataFrame:
    """Volume surprise = vol_t / mean(vol_{t-window..t-1})."""
    if window <= 0:
        return pd.DataFrame(np.nan, index=volumes.index, columns=volumes.columns)
    avg = volumes.shift(1).rolling(window, min_periods=max(5, window // 2)).mean()
    out = volumes / avg
    return out.replace([np.inf, -np.inf], np.nan)


def _liq_turnover(volumes: pd.DataFrame, prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Liquidity proxy = mean(vol_t * price_t) over window, log-scaled."""
    if window <= 0:
        return pd.DataFrame(np.nan, index=volumes.index, columns=volumes.columns)
    dollar_vol = volumes * prices
    avg = dollar_vol.rolling(window, min_periods=max(5, window // 2)).mean()
    # log to compress scale; replace 0 with nan
    avg = avg.replace(0, np.nan)
    return np.log(avg)


# --------------------------------------------------------------------- main API
def compute_raw_factors(panel: Dict, cfg) -> Dict[str, pd.DataFrame]:
    """Compute all 12 raw factor matrices.  No cross-sectional processing yet.

    Each value uses only info up to time t (look-ahead safe by construction
    via shift/rolling with min_periods).
    """
    prices = panel["prices"]
    returns = panel["returns"]
    volumes = panel["volumes"]

    raw: Dict[str, pd.DataFrame] = {}

    # ---- Momentum family ----
    raw["mom_1m"]   = _rolling_mom(prices, cfg.mom_1m, cfg.mom_skip_recent)
    raw["mom_3m"]   = _rolling_mom(prices, cfg.mom_3m, cfg.mom_skip_recent)
    raw["mom_6m"]   = _rolling_mom(prices, cfg.mom_6m, cfg.mom_skip_recent)
    raw["mom_12m"]  = _rolling_mom(prices, cfg.mom_12m, cfg.mom_skip_recent)
    # 12m-1m momentum (Jegadeesh-Titman classic)
    raw["mom_12_1m"] = _rolling_mom(prices, cfg.mom_12m, cfg.mom_1m)
    # Distance from 52w high
    raw["high_dist"] = _high_dist(prices, cfg.high_lookback)

    # ---- Reversal family ----
    raw["reversal_1w"] = _rolling_reversal(prices, cfg.reversal_1w)
    raw["reversal_3w"] = _rolling_reversal(prices, cfg.reversal_3w)

    # ---- Volatility / Risk ----
    raw["vol_60d"] = _rolling_vol(returns, cfg.vol_window, cfg.vol_skip_recent)
    raw["skew_60d"] = _rolling_skew(returns, cfg.vol_window, cfg.vol_skip_recent)

    # ---- Value / Trend proxies ----
    raw["ma_dev_200"] = _ma_dev(prices, cfg.ma_dev_200)
    raw["ma_dev_50"]  = _ma_dev(prices, cfg.ma_dev_50)

    # ---- Liquidity / Volume ----
    raw["vol_surprise"] = _vol_surprise(volumes, cfg.vol_surprise_window)
    raw["liq_turnover"] = _liq_turnover(volumes, prices, cfg.liq_window)

    return raw


def process_cross_section(raw: Dict[str, pd.DataFrame], panel: Dict, cfg) -> pd.DataFrame:
    """Apply winsorize + (optional) neutralize + z-score to each raw factor.

    Returns a stacked DataFrame[T, N * F] OR a 3D structure.  We return a
    dict {factor_name: DataFrame[T, N]} for flexibility, plus a helper to
    build the design matrix.
    """
    processed: Dict[str, pd.DataFrame] = {}
    for name, df in raw.items():
        # 1. winsorize cross-sectionally at each date
        df_w = df.apply(lambda s: _winsorize_cross(s, cfg.factor_winsorize_p), axis=1)
        # 2. market-neutralize (demean cross-sectionally) if requested
        if "market" in cfg.factor_neutralize:
            df_w = _market_neutralize_cross(df_w, panel["returns"])
        # 3. z-score
        if cfg.factor_zscore:
            df_w = df_w.apply(_zscore_cross, axis=1)
        processed[name] = df_w

    return processed


def build_factor_stack(processed: Dict[str, pd.DataFrame], cfg) -> Tuple[pd.DataFrame, List[str]]:
    """Stack factors into a single DataFrame[T, N*F] with multi-level columns.

    Returns (stacked_df, factor_names) where stacked_df.columns is a MultiIndex
    (ticker, factor).  Useful for the regression model.
    """
    factor_names = list(processed.keys())
    # Concatenate along columns with a MultiIndex (ticker, factor)
    pieces = []
    for name in factor_names:
        df = processed[name]
        # Rename columns to (ticker, factor_name)
        df2 = df.copy()
        df2.columns = pd.MultiIndex.from_product([df.columns, [name]],
                                                 names=["ticker", "factor"])
        pieces.append(df2)
    stacked = pd.concat(pieces, axis=1)
    return stacked, factor_names


def build_design_matrix(processed: Dict[str, pd.DataFrame], date_idx: int,
                        tickers: List[str]) -> Tuple[np.ndarray, List[str]]:
    """Build the cross-sectional design matrix X [N, F] at a given date.

    Returns (X, factor_names) where X is (n_valid_tickers, n_factors).
    Rows with any NaN factor are dropped.
    """
    factor_names = list(processed.keys())
    cols = []
    for name in factor_names:
        df = processed[name]
        cols.append(df.iloc[date_idx].values)
    X = np.column_stack(cols) if cols else np.empty((0, 0))
    # Drop rows with NaN
    if X.size:
        mask = np.isfinite(X).all(axis=1)
        X = X[mask]
    return X, factor_names


def all_factors(panel: Dict, cfg) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame, List[str]]:
    """Convenience: compute raw + processed + stacked in one call.

    Returns (processed_dict, stacked_df, factor_names).
    """
    raw = compute_raw_factors(panel, cfg)
    processed = process_cross_section(raw, panel, cfg)
    stacked, names = build_factor_stack(processed, cfg)
    return processed, stacked, names


# --------------------------------------------------------------------- additional factors (Sharpe 2.0 push)
def _rank_momentum(prices: pd.DataFrame, window: int, skip: int) -> pd.DataFrame:
    """Rank-based momentum = rank(P_{t-skip} / P_{t-window-skip}).

    Cross-sectional rank of the momentum signal.  Often more robust than
    raw momentum because it's less affected by outliers.
    """
    mom = _rolling_mom(prices, window, skip)
    # Rank cross-sectionally at each date (0..N-1)
    return mom.rank(axis=1, pct=True) - 0.5  # center around 0


def _price_acceleration(prices: pd.DataFrame, w_short: int, w_long: int) -> pd.DataFrame:
    """Price acceleration = MA_short / MA_long - 1 (trend acceleration)."""
    ma_s = prices.rolling(w_short, min_periods=max(5, w_short//2)).mean()
    ma_l = prices.rolling(w_long, min_periods=max(10, w_long//2)).mean()
    out = (ma_s / ma_l) - 1.0
    return out.replace([np.inf, -np.inf], np.nan)


def _realized_skew_down(returns: pd.DataFrame, window: int, skip: int) -> pd.DataFrame:
    """Downside skewness over a window (crash risk proxy).

    Computed as the skew of negative returns only.  High downside skew = bad.
    """
    if window <= 0:
        return pd.DataFrame(np.nan, index=returns.index, columns=returns.columns)
    neg_ret = returns.clip(upper=0.0)
    shifted = neg_ret.shift(skip)
    return shifted.rolling(window, min_periods=max(15, window//2)).skew()


def _amihud_illiquidity(prices: pd.DataFrame, volumes: pd.DataFrame, window: int) -> pd.DataFrame:
    """Amihud illiquidity = mean(|r_t| / dollar_vol_t) over window.

    Higher value = more illiquid.  Classic microstructure factor.
    """
    if window <= 0:
        return pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    r_abs = returns.abs() if (returns := None) else None
    # Build inline
    rets = np.log(prices / prices.shift(1)).fillna(0.0)
    r_abs = rets.abs()
    dollar_vol = (volumes * prices).replace(0, np.nan)
    illiq_daily = (r_abs / dollar_vol).replace([np.inf, -np.inf], np.nan)
    # Rolling mean
    out = illiq_daily.rolling(window, min_periods=max(5, window//2)).mean()
    # Log-compress
    return np.log(out.replace(0, np.nan))


def _overnight_gap_proxy(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Open-to-close vs close-to-open proxy (using high/low range).

    Since Polygon daily gives OHLC, we approximate overnight gap as
    (open_t / close_{t-1}) - 1.  This captures overnight sentiment.
    """
    if window <= 0:
        return pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    # We have 'highs' and 'lows' but not opens in the panel.  Approximate
    # using close vs prior close range.
    # Use (close - open_proxy) / open_proxy where open_proxy = prior close
    # Actually we have open in the raw CSV but didn't load it.  Approximate:
    # overnight_gap ~ (high_t - close_{t-1}) / close_{t-1} (upper bound)
    # Simpler: skip this and use range-based vol instead.
    return _range_volatility(prices, window)


def _range_volatility(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Range-based vol = mean((high - low) / close) over window.

    Parkinson-style estimator.  More efficient than close-to-close vol.
    Note: we use prices as a proxy if highs/lows not separately available.
    """
    # Without intraday high/low in the panel, approximate using rolling range
    if window <= 0:
        return pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    roll_max = prices.rolling(window, min_periods=max(10, window//2)).max()
    roll_min = prices.rolling(window, min_periods=max(10, window//2)).min()
    range_ = (roll_max - roll_min) / prices
    return range_.replace([np.inf, -np.inf], np.nan)


def compute_extra_raw_factors(panel: Dict, cfg) -> Dict[str, pd.DataFrame]:
    """Compute the additional Sharpe-2.0-pursuit factors."""
    prices = panel["prices"]
    returns = panel["returns"]
    volumes = panel["volumes"]
    raw = {}
    # Rank-based momentum (more robust)
    raw["rank_mom_6m"] = _rank_momentum(prices, cfg.mom_6m, cfg.mom_skip_recent)
    raw["rank_mom_12m"] = _rank_momentum(prices, cfg.mom_12m, cfg.mom_skip_recent)
    # Price acceleration (trend)
    raw["price_accel"] = _price_acceleration(prices, 10, 50)
    # Downside skew (crash risk)
    raw["downside_skew"] = _realized_skew_down(returns, cfg.vol_window, cfg.vol_skip_recent)
    # Amihud illiquidity
    raw["amihud_illiq"] = _amihud_illiquidity(prices, volumes, cfg.liq_window)
    # Range-based vol
    raw["range_vol_60d"] = _range_volatility(prices, cfg.vol_window)
    # Residual momentum (market-orthogonal) -- known to have higher IC than raw momentum.
    # We compute beta to the benchmark cross-sectionally, then take momentum of the residual.
    bench_col = cfg.benchmark if cfg.benchmark in panel["returns"].columns else None
    if bench_col:
        bench = panel["returns"][bench_col]
        # Rolling beta (60d) for each ticker
        roll_cov = returns.rolling(60, min_periods=30).cov(bench)
        roll_var = bench.rolling(60, min_periods=30).var()
        roll_beta = (roll_cov.T / roll_var).T if hasattr(roll_cov, 'T') else roll_cov / roll_var
        # Residual return = r_t - beta * r_bench_t
        resid = returns.sub(roll_beta.mul(bench, axis=0), axis=0)
        # Residual momentum = cumulative residual over 6m, skip last 5
        resid_cum = resid.rolling(cfg.mom_6m).sum().shift(cfg.mom_skip_recent)
        raw["resid_mom_6m"] = resid_cum
        # 12m residual momentum
        resid_cum_12 = resid.rolling(cfg.mom_12m).sum().shift(cfg.mom_skip_recent)
        raw["resid_mom_12m"] = resid_cum_12
    # Momentum dispersion (cross-sectional): high dispersion = trend leadership
    # mom_z = (mom - cross_mean) / cross_std -- already done by z-score, so add a
    # nonlinear transform: square of momentum (captures extreme winners/losers)
    mom12 = _rolling_mom(prices, cfg.mom_12m, cfg.mom_skip_recent)
    raw["mom_12m_squared"] = mom12.pow(2) * np.sign(mom12)  # signed square
    return raw
