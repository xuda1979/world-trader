"""bt.leakcheck — same-period lookahead probe (AUDIT_FWBUGS R3, charter item (a)).

Motivation (AUDIT_GATES2's top framework caveat): NOTHING in bt/ detects a same-day leak —
a signal at t that consumes r_t and still earns r_t. That is exactly the defect that put the
archived champion at ann 40.84% vs the honest 39.85% (AUDIT_RECON R1: mean per-day
cross-sectional corr(dW_i, r_i) = +0.7846 leaky vs -0.0277 causal). This module makes the
check first-class: leak_probe(score, ret) correlates the day-t decision quantity with r_t
(same period) and scans neighbor lags to make sure the dependence sits AT lag 0, then hands
back a fail-closed verdict.

Why effect size + peak-lag, not a bare p-value: the champion panel is long (n=4802), so a
genuinely causal book's tiny same-day corr (real: -0.032) is significant (p=2.9e-07) while
carrying no economic leak. Significance alone therefore false-positives the honest champion.
The leak verdict fires only when the same-day dependence is significant (Fisher t, two-sided)
AND material (|corr| >= MIN_ABS_CORR, calibrated: leaky=+0.789 vs causal=-0.032) AND lag 0 is
the argmax of the lag scan (a causal drift book's dependence sits at the PAST lag instead —
reacting to yesterday's return is not a leak).

Inputs (one of):
  score = 1-D Series -> positions on a single asset; ret = aligned 1-D returns.
  score = 2-D DataFrame -> weights across assets; ret = aligned wide frame of per-asset
          returns. Statistic: mean over days of per-day cross-sectional corr(dW_i, r_i)
          (the exact AUDIT_RECON charter statistic).

Fail-closed: unmeasurable (too short, constant, degenerate) => measurable=False, leak=NaN.
Opt-in via bt.gates.run(..., leak_check=True); default OFF so existing callers are unchanged.
"""
from __future__ import annotations

from math import erfc, sqrt

import numpy as np
import pandas as pd

# Same-day |corr| below this is "not a leak" even when significant (long panels make tiny
# corr significant; calibrated on the real champion: causal -0.032, leaky +0.789).
MIN_ABS_CORR = 0.20
SIG_P = 0.05          # two-sided Fisher p threshold for the same-period correlation
LAGS = (-2, -1, 0, 1, 2)
MIN_OBS = 30          # minimum usable observations to call the probe measurable


def _p_two_sided(c: float, n: int) -> float:
    if not np.isfinite(c) or n < 3:
        return np.nan
    if abs(c) >= 1.0:
        return 0.0  # measured perfect corr: t=inf => maximally significant, NOT unmeasurable
    t = c * sqrt((n - 2) / (1.0 - c * c))
    return erfc(abs(t) / sqrt(2))


def _aligned(score: pd.Series, ret: pd.Series) -> pd.DataFrame:
    j = pd.concat([pd.to_numeric(score, errors="coerce").rename("s"),
                   pd.to_numeric(ret, errors="coerce").rename("r")], axis=1).dropna()
    return j


def _scalar_probe(score: pd.Series, ret: pd.Series) -> dict:
    j = _aligned(score, ret)
    if len(j) < MIN_OBS or j.s.std(ddof=1) <= 0 or j.r.std(ddof=1) <= 0:
        return dict(measurable=False, leak=np.nan, same_period_corr=np.nan,
                    same_period_p=np.nan, lag_scan={}, reason="degenerate_or_too_short")
    c0 = float(j.s.corr(j.r))
    lag_scan = {}
    for lag in LAGS:
        js = _aligned(score, ret.shift(-lag))
        lag_scan[lag] = float(js.s.corr(js.r)) if len(js) >= MIN_OBS else np.nan
    leak = _verdict(c0, _p_two_sided(c0, len(j)), lag_scan)
    return dict(measurable=True, leak=leak, same_period_corr=c0,
                same_period_p=_p_two_sided(c0, len(j)), lag_scan=lag_scan, n=len(j))


def _xsec_stats(Wg: pd.DataFrame, R: pd.DataFrame) -> tuple:
    """Per-day cross-sectional corr(dW_i, r_i) at each lag; returns {lag: corr} + n_days."""
    dW = Wg.diff()
    out = {}
    n_days = 0
    for lag in LAGS:
        rr = R.shift(-lag) if lag != 0 else R
        cs = []
        for i in range(len(R)):
            a = dW.iloc[i].to_numpy(dtype=float)
            b = rr.iloc[i].to_numpy(dtype=float)
            m = np.isfinite(a) & np.isfinite(b)
            a, b = a[m], b[m]
            if len(a) >= 3 and a.std() > 0 and b.std() > 0:
                cs.append(np.corrcoef(a, b)[0, 1])
        out[lag] = np.array(cs, dtype=float)
    return out


def _wide_probe(score: pd.DataFrame, ret: pd.DataFrame) -> dict:
    if score.shape[1] != ret.shape[1]:
        return dict(measurable=False, leak=np.nan, same_period_corr=np.nan,
                    same_period_p=np.nan, lag_scan={},
                    reason=f"column_mismatch(score={score.shape[1]}, ret={ret.shape[1]})")
    score, ret = score.align(ret, join="inner")
    if len(score) < MIN_OBS:
        return dict(measurable=False, leak=np.nan, same_period_corr=np.nan,
                    same_period_p=np.nan, lag_scan={}, reason="too_few_common_days")
    stats = _xsec_stats(score, ret)
    n_days = min(len(v) for v in stats.values())
    if n_days < MIN_OBS:
        return dict(measurable=False, leak=np.nan, same_period_corr=np.nan,
                    same_period_p=np.nan, lag_scan={}, reason="degenerate_or_too_short")
    lag_scan = {lag: float(v.mean()) for lag, v in stats.items() if len(v)}
    c0 = lag_scan[0]
    # t-stat on the mean of daily corr (n = days), two-sided Fisher-free normal approx
    v0 = stats[0]
    t0 = float(v0.mean() / (v0.std(ddof=1) / sqrt(len(v0)))) if v0.std(ddof=1) > 0 else np.nan
    p0 = erfc(abs(t0) / sqrt(2)) if np.isfinite(t0) else np.nan
    leak = _verdict(c0, p0, lag_scan)
    return dict(measurable=True, leak=leak, same_period_corr=c0, same_period_p=p0,
                lag_scan=lag_scan, n=len(v0))


def _verdict(c0: float, p0: float, lag_scan: dict) -> bool:
    """leak=True requires significance AND material effect AND lag0 being the profile peak."""
    if not (np.isfinite(c0) and np.isfinite(p0)):
        return False
    others = [abs(v) for k, v in lag_scan.items() if k != 0 and np.isfinite(v)]
    return bool(abs(c0) >= MIN_ABS_CORR and p0 < SIG_P
                and (not others or abs(c0) >= max(others)))


def leak_probe(score, ret) -> dict:
    """Same-period lookahead probe. Returns dict(measurable, leak, same_period_corr,
    same_period_p, lag_scan{lag: corr}, n[, reason]). Fail-closed: unmeasurable => leak=NaN."""
    if isinstance(score, pd.DataFrame) or isinstance(ret, pd.DataFrame):
        score = score if isinstance(score, pd.DataFrame) else pd.DataFrame(score)
        ret = ret if isinstance(ret, pd.DataFrame) else pd.DataFrame(ret)
        return _wide_probe(score, ret)
    return _scalar_probe(pd.Series(score), pd.Series(ret))


def gates_flag(probe: dict) -> bool:
    """Boolean for bt.gates.run composite: True only when measurable AND not a leak."""
    return bool(probe.get("measurable") is True and probe.get("leak") is False)
