"""TDD tests for HUNT_VOL2 round-2 lib (champion-integrated vol gates).

Charter round 2: conditional VVIX-spike de-risk / SKEW 5d tail-gate / VIX9D>3M
inversion / VIXMO OOS. Bar: ann delta > +0.3pp net of costs vs committed champion.
Costs: incremental 6.4bps one-side on FULL |1.6*dGate| (champion gross is exactly 1.6).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_VOL2/scratch")
import numpy as np, pandas as pd
import vol2_lib2 as L2


def _idx(n):
    return pd.date_range("2015-01-01", periods=n, freq="B")


def test_overlay_t1_and_incremental_cost_exact():
    """Overlay pos = g at t0, then g.shift(1). Incremental cost 6.4e-4*1.6*|p_t-p_{t-1}|
    with p_{-1}=1 (champion built flat 1.6 on day 0)."""
    idx = _idx(4)
    r = pd.Series([0.0, 0.01, -0.02, 0.005], index=idx)
    g = pd.Series([1.0, 1.0, 0.0, 1.0], index=idx)
    net = L2.overlay_net(g, r)
    c = 6.4e-4 * 1.6
    exp = pd.Series([0.0, 0.01, -0.02, -c], index=idx)  # t3: gate trim -> cost, no ret
    assert np.allclose(net.values, exp.values, atol=1e-15), (net.values, exp.values)


def test_overlay_identity_gate1_equals_champion():
    """gate == 1 everywhere -> overlay net EXACTLY the champion (no phantom cost)."""
    idx = _idx(50)
    r = pd.Series(np.random.default_rng(2).normal(0.0005, 0.006, 50), index=idx)
    g = pd.Series(1.0, index=idx)
    net = L2.overlay_net(g, r)
    assert np.allclose(net.values, r.values, atol=1e-15)


def test_overlay_entry_uses_flat_1p6_like_champion():
    """Day-0 gate value CANNOT act (T+1: pos at t is g_{t-1}); day-0 position is the
    champion's own flat-1.6 build. So g0=0.5 must NOT produce a half entry — day0 net
    == champion day0 exactly; the 0.5 gate first bites at t=1 (trim + turnover cost)."""
    idx = _idx(3)
    r = pd.Series([0.02, 0.01, -0.01], index=idx)
    g = pd.Series([0.5, 0.5, 0.5], index=idx)
    net = L2.overlay_net(g, r)
    c = 6.4e-4 * 1.6 * 0.5
    exp = pd.Series([1.0 * 0.02, 0.5 * 0.01 - c, 0.5 * -0.01], index=idx)
    assert np.allclose(net.values, exp.values, atol=1e-15)


def test_overlay_no_lookahead_in_gate_or_costs():
    """Perturbing champion returns/gate AFTER t must not change net up to t+1."""
    rng = np.random.default_rng(4)
    idx = _idx(200)
    r = pd.Series(rng.normal(0.0004, 0.005, 200), index=idx)
    g = (pd.Series(rng.normal(0, 1, 200), index=idx) > 0).astype(float)
    n1 = L2.overlay_net(g, r)
    r2 = r.copy(); r2.iloc[150:] *= 3
    g2 = g.copy(); g2.iloc[150:] = 1.0
    n2 = L2.overlay_net(g, r2)
    n3 = L2.overlay_net(g2, r)
    # net up to t=149 depends only on data <=149 (position at t uses g_{t-1})
    assert np.allclose(n1.values[:150], n2.values[:150], atol=1e-15)
    # cost at t uses p_t vs p_{t-1} = g_{t-1}, g_t -> net at t=150 may differ via g_149
    assert np.allclose(n1.values[:150], n3.values[:150], atol=1e-15)


def test_expanding_q_causal_no_future_leak():
    """Threshold at t = quantile of d[0..t] ONLY; future rows must not move it."""
    idx = _idx(10)
    d = pd.Series(np.arange(1, 11, dtype=float), index=idx)
    q1 = L2.expanding_q(d, q=0.5, minp=3)
    d2 = d.copy(); d2.iloc[8:] = 999.0
    q2 = L2.expanding_q(d2, q=0.5, minp=3)
    assert np.allclose(q1.values[:8], q2.values[:8], atol=1e-15, equal_nan=True)
    assert abs(q1.iloc[4] - 3.0) < 1e-12  # median of 1..5
    assert np.isnan(q1.iloc[1])           # min_periods respected


def test_sustained_k_runs():
    """sustained(cond,3): True only when last 3 rows all True."""
    idx = _idx(6)
    c = pd.Series([True, True, False, True, True, True], index=idx)
    s = L2.sustained(c, 3)
    # windows (backward, size 3): pos2 [T,T,F]=F pos3 [T,F,T]=F pos4 [F,T,T]=F
    # pos5 [T,T,T]=T; pos0/1 warmup -> F
    assert list(s.astype(bool).values) == [False, False, False, False, False, True]


def test_hold_after_k():
    """hold_after(trigger,2): trigger day + 2 more days on."""
    idx = _idx(5)
    t = pd.Series([False, True, False, False, False], index=idx)
    h = L2.hold_after(t, 2)
    assert list(h.values) == [False, True, True, True, False]


def test_champ_trailing_gate_uses_past_only():
    """Trailing-20d champ return at t uses rows t-19..t (no future)."""
    idx = _idx(120)
    r = pd.Series(np.random.default_rng(6).normal(0.0004, 0.006, 120), index=idx)
    m1 = L2.trail_ret(r, 20)
    r2 = r.copy(); r2.iloc[100] *= -10
    m2 = L2.trail_ret(r2, 20)
    assert np.allclose(m1.values[:100], m2.values[:100], atol=1e-15, equal_nan=True)
    assert not np.isclose(m1.iloc[100], m2.iloc[100])


def test_null_trim_p_oracle_beats_frequency_matched_noise():
    """Oracle gate (trim exactly the negative-next-day champ days) must beat >=95% of
    frequency-matched random trims; a seeded noise gate of same freq must NOT."""
    ch = L2.champion()
    r = ch[ch.index >= "2015-01-01"]
    fut = r.shift(-1).fillna(0.0)
    oracle = (fut >= 0).astype(float)          # stay in on up days, trim down days
    p_or = L2.null_trim_p(oracle, r, n=100, seed=1)
    assert p_or <= 0.05, p_or
    rng = np.random.default_rng(3)
    noise = pd.Series(rng.random(len(r)) < oracle.mean(), index=r.index).astype(float)
    p_no = L2.null_trim_p(noise, r, n=100, seed=1)
    assert 0.2 <= p_no <= 1.0, p_no


def test_deltas_exact_vs_base():
    """deltas(): geo ann delta in pp, MDD delta, worst-year delta vs champion base."""
    idx = _idx(400)
    rng = np.random.default_rng(8)
    r = pd.Series(rng.normal(0.001, 0.006, 400), index=idx)
    net = r * 0.9  # crude scaled book
    d = L2.deltas(net, r)
    assert "d_ann_geo_pp" in d and "d_mdd_pp" in d and "d_worst_pp" in d
    # sanity: geo ann of r*0.9 < geo ann of r here (drift 0.001/day dominates)
    assert d["d_ann_geo_pp"] < 0


def test_vixmo_full_history_not_5y():
    """CHARTER PREMISE CHECK: VIXMO is old-form VIX with 1990+ history (n>9000),
    and tracks modern VIX closely in the overlap (corr>0.97 since 2007)."""
    v = L2.vol("VIXMO")
    assert len(v) > 9000 and v.index.min().year == 1990
    vi = L2.vol("VIX")
    j = pd.concat([v.rename("a"), vi.rename("b")], axis=1, join="inner").dropna()
    j = j[j.index >= "2007-01-01"]
    assert len(j) > 3000 and j.corr().iloc[0, 1] > 0.97


def test_winner_gate_stats_and_triggers_reported():
    """gate_stats returns trigger fraction + n_triggers alongside deltas.
    Lib convention: g = position MULTIPLIER (1.0 = full champion exposure,
    <1.0 = de-risked/trimmed). A trigger is any day g < 1."""
    idx = _idx(300)
    rng = np.random.default_rng(11)
    r = pd.Series(rng.normal(0.001, 0.006, 300), index=idx)
    raw = pd.Series(rng.random(300), index=idx) < 0.03   # ~3% of days trimmed
    g = (~raw).astype(float)                              # 1.0 full, 0.0 trimmed
    st = L2.gate_stats(g, r)
    assert 0.0 < st["trigger_frac"] < 0.15
    assert st["n_trig"] >= 1
    # g == 1 everywhere -> zero triggers
    st1 = L2.gate_stats(pd.Series(1.0, index=idx), r)
    assert st1["trigger_frac"] == 0.0 and st1["n_trig"] == 0
