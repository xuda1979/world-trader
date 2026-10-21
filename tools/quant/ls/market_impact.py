"""Market impact model (Almgren-Chriss 2005 square-root impact).

Temporary impact = eta * sigma_daily * sqrt(|Q| / ADV)
where ADV = 21d avg dollar volume, Q = shares traded.
Retail orders (< 1% ADV) incur negligible impact on liquid stocks.
"""
import numpy as np
import pandas as pd


def estimate_market_impact(trade_values, prices, volumes, daily_vol,
                           eta=0.10, min_adv=1e6):
    if len(volumes.shape) == 1:
        adv = np.abs(volumes * prices)
    else:
        lookback = min(21, volumes.shape[0])
        adv = np.nanmean(volumes[-lookback:] * prices[-lookback:], axis=0)
    valid = np.isfinite(adv) & (adv > min_adv) & np.isfinite(trade_values) & (trade_values > 0)
    impact = np.zeros_like(trade_values)
    if not valid.any():
        return impact
    participation = trade_values[valid] / adv[valid]
    if len(daily_vol.shape) <= 1:
        sigma = daily_vol[valid]
    else:
        sigma = daily_vol[-1, valid] if daily_vol.shape[0] > 0 else daily_vol[valid]
    sigma = np.where(np.isfinite(sigma) & (sigma > 0), sigma, 0.01 / np.sqrt(252))
    impact_bps = eta * sigma * np.sqrt(np.clip(participation, 0, 0.10)) * 10000
    impact[valid] = trade_values[valid] * np.clip(impact_bps, 0, 100) / 10000
    return impact
