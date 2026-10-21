"""AUDIT_GATES2 ROUND 3 — gates-audit regression tests (contract v2 additive sections).

Scope: the beats_passive wiring in bt.gates.run must be fail-closed on INCOMPLETE
benchmark data. GATES_CONTRACT v2 draft section 7a defines the gate as beating the best
of the TRIO {spy_bh, sixty_forty, cta_trend}; a run() call that supplies only spy would
judge the candidate against SPY alone — a candidate that beats SPY but loses to 60/40
would read beats_passive_ok=True (fail-OPEN vs the contract). Same fail-closed rule as
corr (R1: ref=None => corr_ok=False) and scr/leak (R2/FWBUGS-R3: absent sig => False).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bt import gates as G


def _idx(n: int) -> pd.DatetimeIndex:
    return pd.bdate_range("2020-01-01", periods=n)


def _mkt(n: int, drift: float = 3.5e-4, seed: int = 5) -> pd.Series:
    """Synthetic 'market' return series (positive drift, SPY-like vol)."""
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(drift, 0.01, n), index=_idx(n))


def _alpha_book(n: int, seed: int = 13) -> pd.Series:
    """A genuine-alpha book: SR comfortably above any passive benchmark here."""
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(2.5e-3, 8e-3, n), index=_idx(n))


def test_r3_bp_subset_spy_only_fails_closed():
    """beats_passive=True with SPY only must NOT pass the gate on the strength of one
    benchmark: the contract gate is the best of the trio, and the unmeasured two are
    unmeasured evidence. Fail closed with an explicit reason."""
    n = 600
    spy = _mkt(n)
    alpha = _alpha_book(n)          # beats SPY B&H AND 60/40 AND cta on this span
    res = G.run(alpha, ref=None, sig=None, spy=spy, ief=None, cta=None,
                beats_passive=True)
    assert res['beats_passive_ok'] is False, (
        "run() judged beats_passive on an incomplete trio (spy-only) and PASSED it — "
        f"fail-open vs contract 7a: {res.get('beats_passive')}")
    assert res['pass'] is False


def test_r3_bp_missing_ieF_only_fails_closed():
    """spy+cta without ief is still an incomplete trio -> fail closed."""
    n = 600
    spy, cta = _mkt(n), _mkt(n, drift=0.0, seed=21)
    res = G.run(_alpha_book(n), ref=None, sig=None, spy=spy, ief=None, cta=cta,
                beats_passive=True)
    assert res['beats_passive_ok'] is False
    assert res['pass'] is False
    bp = res.get('beats_passive') or {}
    assert bp.get('reason') == 'incomplete_trio', bp.get('reason')


def test_r3_bp_full_trio_still_passes_genuine_alpha():
    """The control: with the complete trio supplied, a genuine-alpha book still passes
    the gate and the composite (the fix must not break the positive case).

    AUDIT_FWBUGS R5 (V2 section-12 step 4): sig is the HONEST T+1 book — sign(alpha)
    lagged one day. The prior sig = sign(alpha_t) is itself a same-period leak (the
    defect the now-default-on leak gate catches), so pass-is-True here means ALPHA
    (trio margin), not leak-absence. Measured: same_period_corr +0.0277, p 0.497,
    leak=False on these exact fixtures."""
    n = 600
    spy = _mkt(n)
    ief = _mkt(n, drift=1.0e-4, seed=5)          # bonds: low drift
    cta = _mkt(n, drift=0.0, seed=31)            # flat trend proxy
    # AUDIT_FWBUGS R5 (V2 section-12 step 4): an AR(1) PREDICTABLE alpha (the honest-T+1
    # book must be a real signal — with iid alpha the lagged-sign book is luck and the
    # scramble gate correctly rejects it, measured scr_p 0.23) with HONEST T+1 positions:
    # sign(alpha) lagged one day. Measured on this exact fixture: book SR 3.57,
    # halves (2.97, 4.20), 0 neg, scr_p 0.000, same_period_corr +0.218 -> leak=False
    # (dependence at the PAST lag), bp margin +1.61 over spy_bh.
    rng = np.random.default_rng(13)
    e = rng.normal(0.0, 8e-3, n)
    a = np.empty(n); a[0] = e[0]
    for t in range(1, n):
        a[t] = 0.25 * a[t-1] + e[t]
    alpha = pd.Series(a, index=_idx(n))
    sig = np.sign(alpha.values)
    sig[sig == 0] = 1.0
    sig = np.concatenate(([1.0], sig[:-1]))      # T+1: position at t saw only r_{<t}
    ref = _mkt(n, drift=3e-4, seed=77)
    res = G.run(alpha, ref=ref, sig=sig, spy=spy, ief=ief, cta=cta, beats_passive=True)
    assert res['beats_passive_ok'] is True, res.get('beats_passive')
    assert res['leak_ok'] is True, res.get('leak')
    assert res['pass'] is True


def test_r3_bp_no_data_at_all_fails_closed():
    """beats_passive=True with no benchmark series: fail-closed (uniform incomplete_trio
    reason at the acceptance layer — the module-level 'no_benchmark' case is unreachable
    once the trio check is in place)."""
    res = G.run(_alpha_book(300), ref=None, sig=None, spy=None, ief=None, cta=None,
                beats_passive=True)
    assert res['beats_passive_ok'] is False
    assert res['pass'] is False
    assert (res.get('beats_passive') or {}).get('reason') == 'incomplete_trio'
