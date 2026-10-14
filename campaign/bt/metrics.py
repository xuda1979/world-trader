"""Statistics/metrics on a return series. All short + testable + honest."""
from __future__ import annotations
import numpy as np
import pandas as pd

ANN = 252.0
ANN_M = 12.0


def ann_geo(r: pd.Series) -> float:
    if not len(r):
        return np.nan
    # min_count=1 (AUDIT_FWBUGS R2): an all-NaN series prods to 1.0 under pandas skipna,
    # which sailed both ruin guards and reported a clean 0.0% — same fail-open class as the
    # R1 neg_years bug. Zero finite observations => undefined => NaN (ann_arith agrees).
    prod = (1 + r).prod(min_count=1)
    if not np.isfinite(prod) or prod <= 0:
        return np.nan  # ruin guard: negative/zero product => undefined geometric ann
    return float(prod ** (1.0 / len(r) * ANN) - 1)


def ann_arith(r: pd.Series) -> float:
    return float(r.mean() * ANN) if len(r) else np.nan


def sharpe_d(r: pd.Series) -> float:
    s = r.std(ddof=1)
    if not s or not np.isfinite(s) or s < 1e-12:
        return 0.0
    return float(r.mean() / s * np.sqrt(ANN))


def sharpe_m(r: pd.Series) -> float:
    m = r.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    s = m.std(ddof=1)
    if not s or not np.isfinite(s) or s < 1e-12:
        return 0.0
    return float(m.mean() / s * np.sqrt(ANN_M))


def max_dd(r: pd.Series) -> float:
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min()) if len(r) else np.nan


def neg_years(r: pd.Series) -> tuple:
    if len(r) == 0:
        return (0, np.nan)
    if not isinstance(r.index, pd.DatetimeIndex):
        raise ValueError("neg_years: r.index must be a DatetimeIndex (no .year to group on)")
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod(min_count=1) - 1)
    # fail-closed (AUDIT_FWBUGS R1): a NaN/inf year return (whole missing year, ruined
    # product) must COUNT as a negative year, not silently pass the gate.
    yr = yr.where(np.isfinite(yr), -1.0)
    neg = int((yr < 0).sum())
    return (neg, float(yr.min()) if len(yr) else np.nan)


def half_split(r: pd.Series):
    k = len(r) // 2
    return (sharpe_d(r.iloc[:k]) if k else np.nan,
            sharpe_d(r.iloc[k:]) if k else np.nan)


def report(r: pd.Series) -> dict:
    neg, worst = neg_years(r)
    return dict(ann_geo=round(ann_geo(r), 4), ann_arith=round(ann_arith(r), 4),
                sr_d=round(sharpe_d(r), 3), sr_m=round(sharpe_m(r), 3),
                max_dd=round(max_dd(r), 4), vol=round(r.std(ddof=1) * np.sqrt(ANN), 4),
                neg_years=neg, worst_year=round(worst, 4), n=len(r))
