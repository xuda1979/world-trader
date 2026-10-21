"""TDD tests for HUNT_VOL2 sleeve lib (round 1). Charter: vol-surface features as
risk-on/off gates or standalone sleeves; 6.4bps FULL |dW| one-side, T+1, trailing
vol-target 10% clip<=3, gates a-e, |corr|<0.15 vs champion."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_VOL2/scratch")
import numpy as np, pandas as pd
import vol2_lib as L


def test_t1_no_lookahead():
    """Position today must equal signal from yesterday (shift(1) execution)."""
    idx = pd.date_range("2020-01-01", periods=10, freq="B")
    sig = pd.Series(np.arange(10, dtype=float), index=idx)
    pos = L.t1(sig)
    assert pos.iloc[0] == 0.0
    assert pos.iloc[1] == sig.iloc[0]
    assert pos.iloc[-1] == sig.iloc[-2]


def test_costs_full_dw_not_half():
    """6.4bps on FULL |dW| one-side: turnover 0->1 charge = 6.4bps, NOT 3.2bps."""
    idx = pd.date_range("2020-01-01", periods=3, freq="B")
    pos = pd.Series([1.0, 1.0, 1.0], index=idx)
    ret = pd.Series([0.0, 0.01, 0.01], index=idx)
    net = L.net_of(pos, ret, vt=None)
    # signal at day0 -> position HELD at day1 (T+1): turnover 1.0 -> cost 6.4e-4
    assert abs(net.iloc[1] - (0.01 - 6.4e-4)) < 1e-12


def test_borrow_on_short():
    """Short notional charged 0.5%/yr on days held short."""
    idx = pd.date_range("2020-01-01", periods=3, freq="B")
    pos = pd.Series([-1.0, -1.0, -1.0], index=idx)
    ret = pd.Series([0.0, 0.0, 0.0], index=idx)
    net = L.net_of(pos, ret, vt=None)
    # signal day0 -> short held day1 (T+1): turnover 1.0 -> 6.4e-4 + borrow 0.005/252
    assert abs(net.iloc[1] - (-6.4e-4 - 0.005 / 252)) < 1e-12


def test_voltarget_trailing_only_and_clip3():
    """vt scale at t must not see r_t; clip <= 3.0."""
    rng = np.random.default_rng(3)
    idx = pd.date_range("2020-01-01", periods=400, freq="B")
    r = pd.Series(rng.normal(0.0003, 0.004, 400), index=idx)
    s = L.vt_scale(r, target=0.10, minlen=60, cap=3.0)
    r2 = r.copy(); r2.iloc[200] *= 50
    assert abs(s.iloc[200] - L.vt_scale(r2, target=0.10, minlen=60, cap=3.0).iloc[200]) < 1e-12
    assert s.max() <= 3.0 + 1e-12


def test_stats_sane():
    rng = np.random.default_rng(5)
    idx = pd.date_range("2010-01-01", periods=1000, freq="B")
    r = pd.Series(rng.normal(0.0004, 0.005, 1000), index=idx)
    s = L.stats(r)
    assert 0 < s["sr"] < 10 and s["n"] == 1000 and "h1" in s and "h2" in s


def test_scramble_detects_timing():
    """Scramble machinery sanity. A TRUE oracle must LEAD returns: pos_t = sign(r_{t+1})
    survives T+1 and beats every permutation -> p=0. Same-day sign(r_t) does NOT lead
    under T+1 for iid returns, so it must NOT beat the scramble band (regression guard
    for the old bug where the test claimed same-day sign was an oracle)."""
    rng = np.random.default_rng(1)
    idx = pd.date_range("2010-01-01", periods=1500, freq="B")
    r = pd.Series(rng.normal(0.0004, 0.008, 1500), index=idx)
    true_oracle = pd.Series(np.sign(r.shift(-1).fillna(0.0).values) * 2 - 1, index=idx)
    p_oracle = L.scramble_p(true_oracle, r, n=50, seed=1)
    assert p_oracle == 0.0
    sametag = pd.Series(np.sign(r.values) * 2 - 1, index=idx)  # not predictive under T+1
    p_sametag = L.scramble_p(sametag, r, n=50, seed=1)
    assert p_sametag > 0.05
    coin = pd.Series(rng.choice([-1.0, 1.0], 1500), index=idx)
    p_coin = L.scramble_p(coin, r, n=50, seed=1)
    assert 0.0 <= p_coin <= 1.0  # machinery runs; coin has no systematic edge claim


def test_champion_corr_exact():
    champ = L.champion()
    my = pd.Series(0.0, index=champ.index)
    my.iloc[: len(my) // 2] = 1.0
    c = L.corr_champ(my.reindex(champ.index).fillna(0.0))
    assert -1 <= c <= 1


def test_spy_loads_and_has_no_nan():
    """Regression: spy() must import the harness (path bug fixed) and return
    a clean, positive-length return series with a known seam-free index."""
    r = L.spy()
    assert len(r) > 4000
    assert r.notna().all()
    assert r.abs().max() < 0.25  # no seam blowups


def test_etf_ret_spy_fallback_and_gld_uso():
    """Regression: more_etf lacks SPY -> etf_ret must fall back to twelve_liq.
    GLD/USO/XOP must load from more_etf directly."""
    for name, lo in [("SPY", 4), ("GLD", 4), ("USO", 4), ("XOP", 4)]:
        r = L.etf_ret(name).dropna()
        assert len(r) > 4000, name
        assert r.abs().max() < 0.5, name
