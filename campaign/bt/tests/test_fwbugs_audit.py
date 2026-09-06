"""AUDIT_FWBUGS round-1 adversarial tests. Written RED-first; each targets a suspected bug."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bt.engine import cap_leverage, cost_turnover
from bt import metrics as M


def test_cap_leverage_never_scales_up_underlevered_rows():
    """BUG SUSPECT: when ANY row exceeds the cap, the middle 'fix' block multiplies every
    NON-over row by max_lev/gross (>1), levering up under-levered rows. cap_leverage must be
    a projection (never increase gross)."""
    w = pd.DataFrame({'a': [0.5, 3.0]})
    out = cap_leverage(w, max_lev=1.6)
    g = out.abs().sum(axis=1)
    assert g.iloc[0] <= 0.5 + 1e-12, (
        f"cap_leverage increased an under-levered row: {g.iloc[0]} > 0.5 (silent leverage injection)")
    assert g.iloc[1] <= 1.6 + 1e-12


def test_cap_leverage_is_projection_monotone():
    """For ALL rows: gross(out) <= min(gross(in), max_lev)."""
    rng = np.random.default_rng(7)
    w = pd.DataFrame(rng.normal(0, 1, (200, 4)) * 0.5, columns=list('abcd'))
    out = cap_leverage(w, max_lev=1.6)
    gi = w.abs().sum(axis=1); go = out.abs().sum(axis=1)
    assert (go <= gi + 1e-12).all(), "gross must never increase"
    assert (go <= 1.6 + 1e-12).all(), "gross must never exceed cap"


def test_cost_turnover_charges_day1_establishment():
    """BUG SUSPECT: w.diff() first row is NaN and sum() skips it, so establishing the initial
    book (0 -> w0) trades real notional but is charged ZERO cost. TRADE_RECORD_STANDARD
    qty_notional=|position change| includes 0->w0."""
    w = pd.DataFrame({'a': [1.0, 1.0, 1.0]})
    c = cost_turnover(w, cost_bps=6.4)
    assert c.iloc[0] > 0, f"day-1 establishment turnover must be charged, got {c.iloc[0]}"
    assert abs(c.iloc[0] - 1.0 * 6.4 / 1e4) < 1e-15
    assert abs(c.iloc[1]) < 1e-15 and abs(c.iloc[2]) < 1e-15


def test_metrics_max_dd_nan_safe():
    """NaN in returns must not poison max_dd to NaN (fail-closed, not silent)."""
    r = pd.Series([0.01, np.nan, -0.02, 0.01])
    dd = M.max_dd(r)
    assert np.isfinite(dd), f"max_dd must be NaN-safe, got {dd}"


def test_metrics_ann_geo_nan_input_finite_or_nan_not_crash():
    r = pd.Series([0.01, None, 0.02])
    v = M.ann_geo(r.dropna())
    assert np.isfinite(v)


# ============ AUDIT_FWBUGS ROUND-1 (chief coord) ============

def test_recon_turnover_includes_day1_entry_like_engine_charging():
    """BUG-1 (RED->GREEN): turnover_reconciles compared vs pos.diff() which DROPS day-1
    entry notional, while engine.cost_turnover (AUDIT_FWBUGS R1 fix) CHARGES day-1 entry.
    A compliant ledger (qty includes entry) must reconcile OK."""
    import numpy as np, pandas as pd
    from bt import reconcile
    idx = pd.date_range('2020-01-01', periods=3)
    pos = pd.DataFrame({'a': [1.0, -1.0, -1.0]}, index=idx)   # enters 1.0 on day 1
    led = pd.DataFrame({'sleeve': ['a'] * 3,
                        'date': idx,
                        'qty_notional': [1.0, 2.0, 0.0]})     # entry + flip, honest
    res = reconcile.turnover_reconciles(led, pos)
    assert res['ok'], f"compliant day-1 ledger must reconcile (got {res})"


def test_neg_years_counts_nan_years_fail_closed():
    """BUG-2 (RED->GREEN): a year whose returns are ALL NaN produced prod=NaN and was NOT
    counted negative (fail-open). Honest gate: NaN year must count as a bad year."""
    import numpy as np, pandas as pd
    from bt.metrics import neg_years
    idx = pd.date_range('2019-01-01', '2020-12-31')
    r = pd.Series(-0.01, index=idx)
    r.loc['2019-01-01':'2019-12-31'] = np.nan                # whole 2019 = NaN
    r.loc['2020-01-01':'2020-12-31'] = -0.001                # 2020 slightly negative
    neg, worst = neg_years(r)
    assert neg >= 2, f"NaN year + negative year must both count (got neg={neg})"
