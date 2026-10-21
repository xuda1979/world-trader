"""CAMP_SHORT R4 — strat_ls_equity neg-branch flip fix (charter R4, TDD).

BUG (found in CAMP_SHORT R3 census, fixed here): run_long_short_equity line 134
multiplied the already-negative short weights by -1 AFTER normalization
(`neg / neg.abs().sum() * short_scale * -1`), landing every intended short leg
LONG. 130/30 was really 160/0; Dollar Neutral was really 200/0.

CONVENTION CHOSEN (charter: "pick the convention that matches the docstring, cite it"):
short weights stay NEGATIVE. Citations:
  - strat_ls_equity.py module docstring: "130/30 (130% long, 30% short, 100% net)"
    and "Market neutral (dollar neutral)" — the product IS defined by signed legs;
  - core.py BacktestEngine.run docstring: target_weights are
    "(positive=long, negative=short, sum=net exposure)";
  - compute_ls_signals (this module, line ~80) already emits negative short weights;
    the neg-branch rescale must preserve, not flip, that sign.

Fixture: deterministic 12-name momentum panel (drift sorted N00..N11) so the
top-momentum quintile is knowable a priori — the short book must be the LOW-drift
names with NEGATIVE weights summing to -gross*(1-net)/2.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
for p in (ROOT, os.path.join(ROOT, "tools", "quant")):
    if p not in sys.path:
        sys.path.insert(0, p)

from hedge_fund_strats.strat_ls_equity import run_long_short_equity  # noqa: E402


def momentum_panel(n_names: int = 12, n_days: int = 400, seed: int = 42):
    """Deterministic panel: name i has daily drift (0.0015 - i*0.0003), so
    cross-sectional momentum ranks N00..N11 monotonically with huge separation
    (drift spread 3.3%/day cumulative vs ~15% noise over the 231d window)."""
    rng = np.random.default_rng(seed)
    drift = np.linspace(0.0015, -0.0015, n_names)
    rets = rng.normal(0.0005, 0.01, size=(n_days, n_names)) + drift
    prices = 100.0 * np.cumprod(1.0 + rets, axis=0)
    idx = pd.bdate_range("2024-01-02", periods=n_days)
    cols = [f"N{i:02d}" for i in range(n_names)]
    pr = pd.DataFrame(prices, index=idx, columns=cols)
    return pr, pr.pct_change()


def signal_rows(W: pd.DataFrame):
    """Rows where the book expresses any position."""
    return W.loc[(W.abs().sum(axis=1) > 0)]


# ---------------------------------------------------------------- the flip test
def test_short_legs_are_actually_short():
    """THE FIX: intended short legs carry NEGATIVE weights (docstring convention)."""
    pr, rt = momentum_panel()
    perf, W = run_long_short_equity(pr, rt, gross_leverage=1.6, net_exposure=0.625,
                                    n_long=5, n_short=5, rebalance_freq=21)
    S = signal_rows(W)
    assert len(S) > 0, "fixture produced no signal rows"
    # (a) the book expresses shorts at all
    assert (S.values < 0).any(), \
        "no negative weights anywhere — short legs flipped long (the R3 flip bug)"
    # (b) short notional per signal day == -gross*(1-net)/2 = -0.3
    short_sum = S.clip(upper=0.0).sum(axis=1)
    long_sum = S.clip(lower=0.0).sum(axis=1)
    assert np.allclose(short_sum, -0.3, atol=1e-9), \
        f"short notional {short_sum.iloc[0]:.6f} != -0.3"
    assert np.allclose(long_sum, 1.3, atol=1e-9), \
        f"long notional {long_sum.iloc[0]:.6f} != 1.3"
    # (c) docstring cross-check: net exposure (L-|S|)/gross == 0.625, gross == 1.6
    gross = long_sum + short_sum.abs()
    net = (long_sum + short_sum) / gross
    assert np.allclose(gross, 1.6, atol=1e-9)
    assert np.allclose(net, 0.625, atol=1e-9), \
        f"net exposure {net.iloc[0]:.4f} != 0.625 — book is not 130/30 as documented"


def test_dollar_neutral_book_is_actually_neutral():
    """Dollar Neutral (gross 2.0, net 0.0): |long| == |short| == 1.0, sum ~ 0."""
    pr, rt = momentum_panel()
    perf, W = run_long_short_equity(pr, rt, gross_leverage=2.0, net_exposure=0.0,
                                    n_long=5, n_short=5, rebalance_freq=21)
    S = signal_rows(W)
    assert (S.values < 0).any(), "dollar-neutral book has no short leg (flipped long)"
    long_sum = S.clip(lower=0.0).sum(axis=1)
    short_sum = S.clip(upper=0.0).sum(axis=1)
    assert np.allclose(long_sum, 1.0, atol=1e-9)
    assert np.allclose(short_sum, -1.0, atol=1e-9)
    assert np.allclose((long_sum + short_sum).abs(), 0.0, atol=1e-9), \
        "dollar-neutral book is not neutral — net != 0"


def test_shorts_are_the_low_momentum_names():
    """Economic sanity: the book is oriented correctly — the short book skews to
    LOW-drift names and the long book to HIGH-drift names. Exact membership is NOT
    asserted: the composite signal is 70% momentum + 30% 5-day reversal
    (strat_ls_equity.py), so on days when a high-drift name just ran up, the
    reversal term legitimately sends it to the short book."""
    pr, rt = momentum_panel()
    perf, W = run_long_short_equity(pr, rt, gross_leverage=1.6, net_exposure=0.625,
                                    n_long=5, n_short=5, rebalance_freq=21)
    S = signal_rows(W)
    drift_rank = {f"N{i:02d}": i for i in range(12)}  # higher = lower drift
    short_ranks, long_ranks = [], []
    for _, r in S.iterrows():
        short_ranks += [drift_rank[n] for n in r.index[r < 0]]
        long_ranks += [drift_rank[n] for n in r.index[r > 0]]
    assert len(short_ranks) and len(long_ranks)
    assert np.mean(short_ranks) > np.mean(long_ranks), \
        f"book inverted: short mean rank {np.mean(short_ranks):.2f} " \
        f"<= long mean rank {np.mean(long_ranks):.2f}"
    # and the skew is decisive, not a coin flip: shorts sit in the bottom half
    # (rank >= 6) far more often than longs do
    assert np.mean([r >= 6 for r in short_ranks]) > 0.7, \
        f"short book not low-momentum skewed: {np.mean([r >= 6 for r in short_ranks]):.2f}"
    assert np.mean([r < 6 for r in long_ranks]) > 0.7, \
        f"long book not high-momentum skewed: {np.mean([r < 6 for r in long_ranks]):.2f}"


def test_variants_convention_120_20():
    """120/20 config (gross 1.2, net 0.833): long 1.1 / short -0.1 — not 120/0."""
    pr, rt = momentum_panel()
    perf, W = run_long_short_equity(pr, rt, gross_leverage=1.2, net_exposure=0.8333,
                                    n_long=5, n_short=5, rebalance_freq=21)
    S = signal_rows(W)
    assert (S.values < 0).any(), "120/20 book has no short leg (flipped long)"
    short_sum = S.clip(upper=0.0).sum(axis=1)
    long_sum = S.clip(lower=0.0).sum(axis=1)
    assert np.allclose(short_sum, -1.2 * (1 - 0.8333) / 2, atol=1e-6)
    assert np.allclose(long_sum, 1.2 * (1 + 0.8333) / 2, atol=1e-6)
