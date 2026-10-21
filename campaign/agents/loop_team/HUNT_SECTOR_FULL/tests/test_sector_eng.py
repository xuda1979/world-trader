"""HUNT_SECTOR_FULL TDD tests (failing-test-first)."""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, '/Users/daxu/software/world-trader')

from campaign.agents.loop_team.HUNT_SECTOR_FULL.sector_eng import (  # noqa: E402
    load_etf, mkbook, build_weights, compute_costs, ew_books,
)


def test_data_premise_lint():
    """Charter premise: full SPDR set exists, REAL closes, >4800 rows, no dup idx, closes>0."""
    for t in ['XLB', 'XLF', 'XLI', 'XLK', 'XLY', 'XLP', 'XLU', 'XLV',
              'KBE', 'KRE', 'ITB', 'XHB', 'SMH', 'IGV', 'XME']:
        px = load_etf(t)
        assert len(px) > 4800, (t, len(px))
        assert str(px.index.min().date()) == '2006-10-17' or len(px) > 4990
        assert (px > 0).all()
        assert not px.index.duplicated().any()
        assert px.index.max() >= pd.Timestamp('2026-08-01')


def test_T1_no_same_day_leak():
    """pos must equal signal shift(1): day t book uses ONLY t-1 close info."""
    rng = np.random.default_rng(7)
    n = 500
    idx = pd.bdate_range('2015-01-01', periods=n)
    a = pd.Series(100 * np.cumprod(1 + rng.normal(0, .01, n)), index=idx)
    b = pd.Series(100 * np.cumprod(1 + rng.normal(0, .01, n)), index=idx)
    lb, cap = 10, 1.5
    w = build_weights(a, b, lb=lb, cap=cap)
    sp = np.log(a / b)
    z = (sp - sp.rolling(lb).mean()) / sp.rolling(lb).std()
    expect = (-z / cap).clip(-0.5, 0.5)
    expect.name = 'A'
    pd.testing.assert_series_equal(w['A'], expect.shift(1).fillna(0.0))


def test_cap_semantics_anti_saturates_short():
    """SEC3 family: |w| <= 0.5; z saturated positive => w_A = -0.5 (anti: short the
    overperformer). Steeper trend drives z past cap so clip pins at -0.5 exactly."""
    n = 300
    t = pd.bdate_range('2010-01-01', periods=n)
    a = pd.Series(np.exp(np.linspace(0, 3.0, n)) * 100, index=t)  # exp trend: z pins at cap
    b = pd.Series(100.0, index=t)
    w = build_weights(a, b, lb=10, cap=1.5)
    assert w['A'].abs().max() <= 0.5 + 1e-12
    nz = w['A'][w['A'] != 0.0]
    assert len(nz) > 200
    assert (nz == -0.5).all()                          # saturated: pinned short-A


def test_zero_leg_flat():
    rng = np.random.default_rng(3)
    idx = pd.bdate_range('2015-01-01', periods=200)
    a = pd.Series(100 * np.cumprod(1 + rng.normal(0, .01, 200)), index=idx)
    b = pd.Series(0.0, index=idx)
    w = build_weights(a, b, lb=10, cap=1.5)
    assert w.abs().to_numpy().sum() == 0.0


def test_costs_charged_on_all_legs():
    """reconciliation: charged cost == 6.4bps * (|dw_A| + |dw_B|) each day; borrow 0.5%/yr shorts."""
    rng = np.random.default_rng(11)
    idx = pd.bdate_range('2015-01-01', periods=300)
    a = pd.Series(100 * np.cumprod(1 + rng.normal(0, .01, 300)), index=idx)
    b = pd.Series(100 * np.cumprod(1 + rng.normal(0, .01, 300)), index=idx)
    w = build_weights(a, b, lb=10, cap=1.5)
    net, cost, borrow = compute_costs(w, pd.DataFrame({'A': a.pct_change().fillna(0),
                                                       'B': b.pct_change().fillna(0)}))
    oneside = w.diff().abs().sum(axis=1).fillna(0.0)
    assert cost.equals(oneside * 6.4 / 1e4)
    shorts = -w.clip(upper=0.0).sum(axis=1)
    assert borrow.equals(shorts * 0.005 / 252)
    exp_net = (w * pd.DataFrame({'A': a.pct_change().fillna(0),
                                 'B': b.pct_change().fillna(0)})).sum(axis=1) - cost - borrow
    pd.testing.assert_series_equal(net, exp_net)


def test_ew():
    rng = np.random.default_rng(5)
    idx = pd.bdate_range('2015-01-01', periods=200)
    s = [pd.Series(rng.normal(0, .001, 200), index=idx) for _ in range(3)]
    r = ew_books(s)
    pd.testing.assert_series_equal(r, sum(s) / 3.0)
