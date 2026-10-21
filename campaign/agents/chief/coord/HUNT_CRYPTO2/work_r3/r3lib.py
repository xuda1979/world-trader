"""HUNT_CRYPTO2 round-3 independent metrics lib.

Charter R3a: cross-verify HUNT_SECTOR2's round-2 verdicts with MY OWN code.
This is a deliberate RE-IMPLEMENTATION of the bt metrics conventions (NOT an
import of bt.*) so that a bug in campaign/bt/metrics.py cannot validate itself.
Conventions are pinned by test_r3_verify.py and were read off
campaign/bt/metrics.py @ HEAD:
  - ANN = 252 daily annualization
  - Sharpe = mean/std(ddof=1) * sqrt(252), std==0 -> 0.0
  - geometric ann = prod(1+r)^(252/n) - 1, prod<=0 or no finite obs -> NaN
  - halves: k = len//2, H1 = r.iloc[:k], H2 = r.iloc[k:]
  - neg_years: yearly prod(1+r)-1, NaN/inf year COUNTS as negative (fail-closed)
  - corr: inner-join + dropna Pearson on the two daily return series
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ANN = 252.0


def load_ret(path: str) -> pd.Series:
    """Load a [date,ret] sleeve CSV as a float Series on a DatetimeIndex, sorted.

    Falls back to an index-column date (AP_gold.csv style) so a differently-shaped
    but VALID return stream is measured, not misreported as UNREADABLE. A stream
    that parses to nothing, has duplicate dates, or still looks like a weights
    stream (|ac1|>0.99) is rejected fail-closed."""
    try:
        df = pd.read_csv(path, parse_dates=["date"]).dropna(subset=["date", "ret"])
        s = pd.Series(df["ret"].astype(float).values,
                      index=pd.DatetimeIndex(df["date"]))
    except ValueError:
        df = pd.read_csv(path, index_col=0, parse_dates=True).dropna()
        if df.shape[1] != 1:
            raise ValueError(f"{path}: fallback parse needs exactly 1 data column, "
                             f"got {df.shape[1]}")
        s = pd.Series(df.iloc[:, 0].astype(float).values, index=df.index)
    if len(s) == 0:
        raise ValueError(f"{path}: no parsable returns")
    if s.index.has_duplicates:
        raise ValueError(f"{path}: duplicate dates in sleeve CSV")
    ac1 = s.autocorr(1)
    if ac1 is not None and np.isfinite(ac1) and abs(ac1) > 0.99:
        raise ValueError(f"{path}: autocorr {ac1:.3f} > 0.99 — weights stream, not returns")
    return s.sort_index()


def sharpe_d(r: pd.Series) -> float:
    s = r.std(ddof=1)
    if not s or not np.isfinite(s) or s < 1e-12:
        return 0.0
    return float(r.mean() / s * np.sqrt(ANN))


def ann_geo(r: pd.Series) -> float:
    if not len(r):
        return np.nan
    prod = (1 + r).prod(min_count=1)
    if not np.isfinite(prod) or prod <= 0:
        return np.nan
    return float(prod ** (1.0 / len(r) * ANN) - 1)


def ann_arith(r: pd.Series) -> float:
    return float(r.mean() * ANN) if len(r) else np.nan


def half_split(r: pd.Series):
    k = len(r) // 2
    return (sharpe_d(r.iloc[:k]) if k else np.nan,
            sharpe_d(r.iloc[k:]) if k else np.nan)


def neg_years(r: pd.Series) -> tuple:
    if len(r) == 0:
        return (0, np.nan)
    if not isinstance(r.index, pd.DatetimeIndex):
        raise ValueError("neg_years: r.index must be a DatetimeIndex")
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod(min_count=1) - 1)
    yr = yr.where(np.isfinite(yr), -1.0)  # fail-closed: NaN year == negative year
    neg = int((yr < 0).sum())
    return (neg, float(yr.min()) if len(yr) else np.nan)


def max_dd(r: pd.Series) -> float:
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min()) if len(r) else np.nan


def corr_to(r: pd.Series, bench: pd.Series) -> float:
    j = pd.concat([r.rename("r"), bench.rename("b")], axis=1, sort=True).dropna()
    return float(j["r"].corr(j["b"]))


def yearly_returns(r: pd.Series) -> pd.Series:
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod(min_count=1) - 1)
    return yr.where(np.isfinite(yr), -1.0)


def evaluate_arm(r: pd.Series, champ: pd.Series) -> dict:
    """Full independent stat block for one sleeve vs a champion series."""
    h1, h2 = half_split(r)
    neg, worst = neg_years(r)
    return dict(
        n=len(r), start=str(r.index[0].date()), end=str(r.index[-1].date()),
        sr=sharpe_d(r), ann=ann_geo(r), ann_arith=ann_arith(r),
        vol=float(r.std(ddof=1) * np.sqrt(ANN)),
        h1=h1, h2=h2, neg=neg, worst=worst,
        corr=corr_to(r, champ), years=yearly_returns(r).to_dict(),
        mdd=max_dd(r),
    )


# ---------------------------------------------------------------- champion provenance
def ensure_champ_head(path: str = "/tmp/champ_head.csv") -> str:
    """(Re)build /tmp/champ_head.csv from git HEAD, byte-exact.

    SECTOR2's R2 metas were computed against the committed champion (SR 3.2964);
    the working-tree file is an in-progress re-emit (SR 3.2887), so verification
    must pin the committed version. The /tmp cache is ephemeral, so auto-regen
    from git makes every R3a claim reproducible from the saved script alone.
    """
    import os
    import subprocess

    want = subprocess.run(
        ["git", "show", "HEAD:software/world-trader/campaign/results/"
         "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"],
        cwd="/Users/daxu/software/world-trader", capture_output=True, check=True).stdout
    need = True
    if os.path.exists(path):
        with open(path, "rb") as f:
            need = f.read() != want
    if need:
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(want)
        os.replace(tmp, path)  # atomic
    return path
