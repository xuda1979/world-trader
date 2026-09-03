"""Acceptance gates for a candidate sleeve (honest, TDD-tested, all numbers explicit)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from bt.metrics import sharpe_d, half_split, neg_years

# campaign-standard acceptance thresholds
DEFAULTS = dict(sr_min=0.6, h_min=0.3, neg_max=2, neg_floor=-0.05,
                corr_max=0.15, ac1_max=0.5, uniq_min=0.08, p_max=0.05)


def lag1_autocorr(r: pd.Series) -> float:
    return float(r.autocorr(1)) if len(r) > 2 else 0.0


def uniq_ratio(r: pd.Series) -> float:
    """Fraction of distinct daily values (flattening gate: XGB1y trap)."""
    r = r.round(10)
    return float(r.nunique() / len(r)) if len(r) else 0.0


def zero_runs_long(r: pd.Series, min_run: int = 20):
    """Indices of interior exact-zero runs >= min_run (design-explained or red flag)."""
    z = r.eq(0.0)
    # drop only the boundary bookends if they are NOT part of an interior run; simplest: count runs
    # over the FULL series (including leading/trailing), which is the honest 'interior>=min' semantics
    out = []
    if z.any():
        groups = (z & ~z.shift(1, fill_value=False)).cumsum()
        cnt = z.groupby(groups).sum()
        for k, v in cnt.items():
            if v >= min_run:
                out.append(int(v))
    return out


def corr_to(ref: pd.Series, r: pd.Series) -> float:
    j = pd.concat([ref.rename('r'), r.rename('s')], axis=1).dropna()
    return float(j.r.corr(j.s)) if len(j) > 2 else np.nan


def run(r: pd.Series, ref=None, **kw) -> dict:
    """Outer acceptance gate. Returns per-gate result dict + a boolean PASS (all True).
    The position-lag scramble is NOT computed here (needs positions); call separately via
    scramble() and combine. Provide it as g['scramble_p']."""
    p = {**DEFAULTS, **kw}
    sr = sharpe_d(r); h1, h2 = half_split(r); neg, worst = neg_years(r)
    res = dict(
        sr=sr, sr_ok=sr >= p['sr_min'],
        h1=h1, h2=h2, halves_ok=(h1 >= p['h_min'] and h2 >= p['h_min']),
        neg_years=neg, worst=worst,
        neg_ok=(neg <= p['neg_max'] and worst > p['neg_floor']),
        ac1=lag1_autocorr(r), ac1_ok=lag1_autocorr(r) < p['ac1_max'],
        uniq=uniq_ratio(r), uniq_ok=uniq_ratio(r) >= p['uniq_min'],
        corr=(corr_to(ref, r) if ref is not None else np.nan),
        corr_ok=(abs(corr_to(ref, r)) < p['corr_max'] if ref is not None else True),
        zruns=zero_runs_long(r),
    )
    res['pass'] = all(res[k + '_ok'] for k in ['sr', 'halves', 'neg', 'ac1', 'uniq', 'corr'])
    return res


def scramble_positions(sig, r, side=0, n=200, block=10, rng=None):
    """Position-lag scramble p-value for a 2-leg book. Rolls POSITIONS by a random lag in
    [block, len-block]; returns fraction of scrambled-book SR >= real SR. Returns (p, real_sr)."""
    rng = rng or np.random.default_rng(0)
    sig = np.asarray(sig, dtype=float); r = np.asarray(r, dtype=float)
    # FIX (VERIFY_BEST §4c): baseline must be the REAL BOOK's SR (positions x returns),
    # NOT the raw-return SR (which would accept a destroyed book and spuriously fail real ones).
    real_sr = sharpe_d(pd.Series(sig * r))
    T = len(r)
    lo, hi = block, T - block
    if hi <= lo:
        return (np.nan, real_sr)
    cnt = 0
    for _ in range(n):
        lag = rng.integers(lo, hi + 1)
        s = np.roll(sig, lag)
        # re-costs not applied here (positions only) — conservative for positive-SR
        book = s * r
        if sharpe_d(pd.Series(book)) >= real_sr:
            cnt += 1
    return (cnt / n, real_sr)
