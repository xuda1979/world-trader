"""TDD RED-first tests for RES_VOL R1 hunt lib (vol-surface engines).

Pins: data loading/trim rules, slope construction w/ trailing-shift stats (no lookahead),
VRP definition, net-book convention (sig*rpu == held book), T+1 causality, calendar lint.
"""
import os, sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
from team.agents.RES_VOL.vol_r1 import (  # noqa: E402
    load_vol, load_px, vrp_series, slope_series, realized_vol, long_book, TRIM_VVIX)


# --- data layer -----------------------------------------------------------
def test_vvix_trimmed_to_2007():
    v = load_vol('VVIX')
    assert v.index[0] >= pd.Timestamp('2007-01-01')
    assert v.notna().all() and v.index.is_monotonic_increasing and not v.index.duplicated().any()
    assert (v > 30).all(), "2006 pilot junk prints (71.7/15.7) must be excluded"


def test_all_vol_series_clean():
    for sym in ('VIX', 'VIX9D', 'VIX3M', 'VIX6M', 'VVIX', 'RVX'):
        v = load_vol(sym)
        assert v.notna().all() and len(v) > 3000, sym


def test_px_loads_and_positive():
    for sym in ('SPY', 'IWM', 'USO', 'GLD'):
        p = load_px(sym)
        assert p.notna().all() and (p > 0).all() and p.index.is_monotonic_increasing


# --- signal layer: no-lookahead ------------------------------------------
def test_slope_uses_trailing_shifted_stats():
    v9 = load_vol('VIX9D'); v3 = load_vol('VIX3M')
    s_full = slope_series(v9, v3)
    s2 = slope_series(v9.iloc[:-10], v3.iloc[:-10])
    pd.testing.assert_series_equal(s_full.reindex(s2.index).iloc[:-1], s2.iloc[:-1])
    # last value of the truncated sample must equal the (n-2)th of full: no future info
    assert np.isclose(s2.iloc[-2], s_full.reindex(s2.index).iloc[-2])


def test_vrp_uses_prior_close_realized_vol():
    px = load_px('SPY')
    vix = load_vol('VIX')
    rv = realized_vol(px, lb=21)
    vrp = vrp_series(vix, rv)
    # vrp at t must not depend on prices AFTER t; the perturbed day's 21d RV window
    # (21 obs incl. r_t) contaminates t..t+20, so rows up to t-21 must be invariant
    t = len(px) - 5
    px2 = px.copy(); px2.iloc[t] = px2.iloc[t] * 3.0
    vrp2 = vrp_series(vix, realized_vol(px2, lb=21))
    j = pd.concat([vrp[:t - 21], vrp2[:t - 21]], axis=1).dropna()
    assert np.allclose(j.iloc[:, 0], j.iloc[:, 1])


def test_realized_vol_window_strictly_prior():
    px = load_px('SPY')
    rv = realized_vol(px, lb=21)
    assert rv.notna().sum() > 3000
    # rv_t uses returns up to t (pct_change at t is close t vs t-1; used for NEXT day pos)


# --- book layer: V2 sec-0 convention + T+1 -------------------------------
def test_book_sig_times_rpu_equals_held_book():
    px = load_px('SPY'); vix = load_vol('VIX'); rv = realized_vol(px, 21)
    vrp = vrp_series(vix, rv)
    net, We, rpu = long_book(vrp, px, thr=0.0, hold=5, to_zero=False, return_rpu=True)
    a = We['a'].fillna(0.0); r = px.pct_change().reindex(We.index).fillna(0.0)
    held = (We * pd.concat({'a': r, 'b': 0 * r}, axis=1)).sum(axis=1)
    assert np.allclose((a * rpu).fillna(0.0), held, atol=1e-12)


def test_t1_flip_changes_next_day_not_same_day():
    px = load_px('SPY'); vix = load_vol('VIX'); rv = realized_vol(px, 21)
    vrp = vrp_series(vix, rv)
    n1, W1, _ = long_book(vrp, px, thr=10.0, hold=5, return_rpu=True)
    # decision day = the day the hold lapses (2017-07-19); move the lapse one day later
    k = W1.index.get_loc(pd.Timestamp('2017-07-20'))  # first flat day
    vrp_hold = vrp.copy(); vrp_hold.iloc[k - 1] = 20.0  # keep ON through day k-1
    n2, W2, _ = long_book(vrp_hold, px, thr=10.0, hold=5, return_rpu=True)
    a1, a2 = W1['a'], W2['a']
    d = np.where(~np.isclose(a1, a2, atol=1e-15))[0]
    assert len(d) > 0 and d[0] == k + 1, \
        f"decision at {W1.index[k-1].date()} must first move position at T+1={W1.index[k+1].date()}"
    assert np.isclose(a1.iloc[:k], a2.iloc[:k]).all(), \
        "positions strictly before the perturbed decision must be identical"


def test_trim_vvix_constant():
    assert TRIM_VVIX == pd.Timestamp('2007-01-01')


# --- R3 RED proofs: two R2 defects (spliced returns-as-prices; rpu reconstruction) ---
def test_spliced_spx_returns_prices_not_returns():
    from team.agents.RES_VOL.vol_r2 import spliced_spx
    px = spliced_spx()
    assert (px > 50).all() and (px < 5000).all(), \
        "spliced series must be a sane PRICE LEVEL, not +-pct returns"
    assert abs(px.pct_change().mean()) < 0.01, "levels, not second-differences of returns"
    r = px.pct_change().dropna()
    assert r.abs().max() < 0.25, f"impossible daily move {r.abs().max():.3f}"


def test_evaluate_rpu_reconstruction_is_per_unit():
    from team.agents.RES_VOL.vol_r1 import load_px, load_vol, realized_vol, vrp_series, long_book
    from team.agents.RES_VOL import run_hunt
    px = load_px('SPY'); vrp = vrp_series(load_vol('VIX'), realized_vol(px, 21))
    net, We, rpu = long_book(vrp, px, thr=0.0, hold=5, return_rpu=True)
    # the helper must recover PER-UNIT r, not the book; pin via public reconstructor
    r2 = run_hunt.reconstruct_rpu(net, We)
    live = We['a'].fillna(0.0) != 0.0   # rpu is only DEFINED where a position is held
    assert np.allclose(r2[live], rpu[live], atol=1e-9), \
        "rpu reconstruction must invert net+costs to per-unit returns (V2 sec-0)"


def test_gates_run_book_equals_reported_net():
    "gates.run(rpu, sig=W) book must equal the held book W*rpu (no W^2)."
    from team.agents.RES_VOL.vol_r1 import load_px, load_vol, realized_vol, vrp_series, long_book
    from bt.gates import run as gates_run
    from bt.metrics import sharpe_d
    px = load_px('SPY'); vrp = vrp_series(load_vol('VIX'), realized_vol(px, 21))
    net, We, rpu = long_book(vrp, px, thr=0.0, hold=5, return_rpu=True)
    m = We['a'].reindex(rpu.index).fillna(0.0)
    res = gates_run(rpu, sig=m, leak_check=False, scramble_n=20)
    held = sharpe_d((m * rpu).dropna())
    assert np.isclose(res['sr'], held, atol=1e-9), "gates.run must judge the held book"


def test_evaluate_passes_true_rpu_to_gates():
    "evaluate() must feed gates.run PER-UNIT r, else r_eff=W^2*rpu (bias -0.14 SR here)."
    from team.agents.RES_VOL.vol_r1 import load_px, load_vol, realized_vol, vrp_series, long_book
    from team.agents.RES_VOL import run_hunt
    from bt.engine import cost_turnover, borrow_cost
    from bt.metrics import sharpe_d
    px = load_px('SPY'); vrp = vrp_series(load_vol('VIX'), realized_vol(px, 21))
    net, We, rpu = long_book(vrp, px, thr=0.0, hold=5, return_rpu=True)
    live = (We.fillna(0.0) != 0.0).any(axis=1)
    net = net[net.index >= live.idxmax()]          # evaluate judges the LIVE window only
    m = We['a'].reindex(net.index).fillna(0.0)
    r = rpu.reindex(net.index)
    res = run_hunt.evaluate('_t', net, We, run_hunt.champ_rets(), *run_hunt.benchmark_series(),
                            rpu=rpu, verbose=False)
    import pytest as _pytest
    with _pytest.raises(ValueError):
        run_hunt.evaluate('_t', net, We, run_hunt.champ_rets(), *run_hunt.benchmark_series(),
                          verbose=False)
    held_sr = sharpe_d((m * r).dropna())
    assert res is not None and np.isclose(res['v2']['sr'], held_sr, atol=1e-6), \
        f"v2 sr {res['v2']['sr']:.4f} != held-book sr {held_sr:.4f} (W^2 bias)"
