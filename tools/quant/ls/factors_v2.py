"""V2 Alpha Factors: higher-IC signals backed by academic literature.

All factors are look-ahead-safe (shift/rolling with min_periods).
Computed from price/volume only (no fundamentals needed).

Key additions beyond the base 23 factors:
  Idiosyncratic Volatility (Ang et al. 2006)
  MAX Effect (Bali et al. 2011)
  Beta Arbitrage (Frazzini-Pedersen 2014)
  Trend Efficiency
  Volume-Price Trend
  Short-Term Reversal with Volume Confirmation
  Range-Based Volatility (Parkinson 1980)
  Close Location
  Relative Strength vs Benchmark
  MA Crossover Speed
  Turnover-Adjusted Momentum Quality
  Vol Ratio (adaptive momentum)
"""
import numpy as np
import pandas as pd
from typing import Dict


def _winsorize_cross(s, p):
    lo, hi = s.quantile(p), s.quantile(1 - p)
    return s.clip(lower=lo, upper=hi)


def _zscore_cross(s):
    mu, sd = s.mean(), s.std(ddof=0)
    if sd == 0 or not np.isfinite(sd):
        return s * 0.0
    return (s - mu) / sd


def process_v2_factors(raw, panel, cfg):
    """Apply winsorize, neutralize, zscore to V2 factor dict."""
    processed = {}
    for name, df in raw.items():
        df_w = df.apply(lambda s: _winsorize_cross(s, cfg.factor_winsorize_p), axis=1)
        if hasattr(cfg, 'factor_neutralize') and 'market' in cfg.factor_neutralize:
            row_mean = df_w.mean(axis=1)
            df_w = df_w.sub(row_mean, axis=0)
        if cfg.factor_zscore:
            df_w = df_w.apply(_zscore_cross, axis=1)
        processed[name] = df_w
    return processed


def compute_v2_factors(panel, cfg) -> Dict[str, pd.DataFrame]:
    """Compute 15 additional alpha factors backed by academic literature."""
    prices = panel['prices']
    returns = panel['returns']
    volumes = panel['volumes']
    highs = panel['highs']
    lows = panel['lows']
    bench_col = cfg.benchmark if cfg.benchmark in returns.columns else None

    raw = {}

    # 1. Idiosyncratic Volatility (Ang et al. 2006, JF)
    # Low IVOL predicts higher returns. Residual vol after market regression.
    if bench_col:
        bench_ret = returns[bench_col]
        roll_cov = returns.rolling(60, min_periods=30).cov(bench_ret)
        roll_var = bench_ret.rolling(60, min_periods=30).var()
        beta = roll_cov.div(roll_var, axis=0)
        resid = returns - beta.mul(bench_ret, axis=0)
        ivol = resid.shift(5).rolling(60, min_periods=30).std(ddof=0)
        raw['ivol_60d'] = ivol * np.sqrt(252)

    # 2. MAX Effect (Bali et al. 2011, JFE)
    # Stocks with extreme max daily returns in past month underperform.
    max_ret_21d = returns.rolling(21, min_periods=10).max().shift(5)
    raw['max_ret_21d'] = max_ret_21d

    # 3. MIN Effect (symmetry of MAX)
    min_ret_21d = returns.rolling(21, min_periods=10).min().shift(5)
    raw['min_ret_21d'] = min_ret_21d

    # 4. Beta Arbitrage (Frazzini-Pedersen 2014, JFE)
    # Low-beta stocks outperform on risk-adjusted basis.
    if bench_col:
        raw['beta_60d'] = beta

    # 5. Trend Efficiency
    # Efficiency = |cumulative return| / sum of absolute returns
    # Smoother trends are more persistent (higher SR within the trend).
    abs_ret = returns.abs()
    sum_abs_60d = abs_ret.rolling(60, min_periods=30).sum().shift(5)
    cum_ret_60d = (1 + returns).rolling(60, min_periods=30).apply(
        lambda x: np.prod(1 + x) - 1, raw=True
    ).shift(5)
    trend_eff = cum_ret_60d.abs() / sum_abs_60d.replace(0, np.nan)
    raw['trend_efficiency_60d'] = trend_eff.replace([np.inf, -np.inf], np.nan)

    # 6. Volume-Price Trend (OBV-style accumulation/distribution)
    signed_vol = volumes * np.sign(returns)
    obv_20d = signed_vol.rolling(20, min_periods=10).sum().shift(5)
    avg_vol_60d = volumes.rolling(60, min_periods=30).mean().shift(5)
    obv_norm = obv_20d / avg_vol_60d.replace(0, np.nan)
    raw['obv_norm_20d'] = obv_norm.replace([np.inf, -np.inf], np.nan)

    # 7. Short-Term Reversal with Volume Confirmation
    # Reversal stronger when volume confirms the move (capitulation).
    rev_5d = returns.rolling(5, min_periods=3).sum().shift(1)
    vol_ratio = volumes.rolling(5, min_periods=3).sum() / volumes.rolling(20, min_periods=10).sum().replace(0, np.nan)
    rev_vol = -rev_5d * vol_ratio
    raw['rev_vol_5d'] = rev_vol

    # 8. Gap Persistence
    gap_5d = returns.rolling(5, min_periods=3).sum()
    raw['gap_5d'] = gap_5d

    # 9. Kurtosis (tail risk proxy)
    ret_centered = returns - returns.rolling(60, min_periods=30).mean()
    mom4 = (ret_centered ** 4).rolling(60, min_periods=30).mean()
    mom2_sq = (ret_centered ** 2).rolling(60, min_periods=30).mean() ** 2
    kurt = mom4 / mom2_sq.replace(0, np.nan) - 3.0
    raw['kurtosis_60d'] = kurt.replace([np.inf, -np.inf], np.nan).shift(5)

    # 10. Turnover-Adjusted Momentum Quality
    # Quality = return achieved per unit of churn (higher = cleaner trend).
    mom_6m = (prices.shift(5) / prices.shift(126 + 5)) - 1.0
    abs_sum_6m = abs_ret.rolling(126, min_periods=60).sum().shift(5)
    mom_quality = mom_6m / abs_sum_6m.replace(0, np.nan)
    raw['mom_quality_6m'] = mom_quality.replace([np.inf, -np.inf], np.nan)

    # 11. Range-Based Volatility (Parkinson 1980)
    hl_range = (highs - lows) / prices
    range_vol_20d = hl_range.rolling(20, min_periods=10).mean().shift(5)
    raw['range_vol_20d'] = range_vol_20d

    # 12. Close Location (day-end bias)
    hl_diff = highs - lows
    close_loc = (prices - lows) / hl_diff.replace(0, np.nan)
    close_loc_5d = close_loc.rolling(5, min_periods=3).mean().shift(1)
    raw['close_location_5d'] = close_loc_5d.replace([np.inf, -np.inf], np.nan)

    # 13. Relative Strength vs Benchmark
    if bench_col:
        bench_sum = returns[bench_col].rolling(20, min_periods=10).sum()
        rel_str_20d = returns.rolling(20, min_periods=10).sum().sub(bench_sum, axis=0).shift(5)
        raw['rel_strength_20d'] = rel_str_20d

    # 14. MA Crossover Speed
    ma_20 = prices.rolling(20, min_periods=10).mean()
    ma_50 = prices.rolling(50, min_periods=25).mean()
    ma_cross = (ma_20 - ma_50) / ma_50.replace(0, np.nan)
    raw['ma_cross_20_50'] = ma_cross.replace([np.inf, -np.inf], np.nan)

    # 15. Adaptive Momentum (volatility ratio for Hurst-style tuning)
    vol_20d = returns.rolling(20, min_periods=10).std(ddof=0).shift(5)
    vol_120d = returns.rolling(120, min_periods=60).std(ddof=0).shift(5)
    vol_ratio_hurst = vol_20d / vol_120d.replace(0, np.nan)
    raw['vol_ratio_20_120'] = vol_ratio_hurst.replace([np.inf, -np.inf], np.nan)

    return raw
