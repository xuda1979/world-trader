"""HUNT_VOL2 ROUND 5 — TDD tests for the PCR-overlay library (tests FIRST, red→green).

Charter round 5 (a): CBOE put/call archive 1995-2019 as a vol-timing OVERLAY on the
champion, evaluated ONLY over 2006-2019 (frozen archive), era-robustness WITHIN the
window as the gate (TimesFM single-era kill applied). Data: DATA_COTMORE-R3's
pcr_covariates_SPY_daily.csv (PIT strictly-prior, 1-session carry cap, NaN after freeze).
"""
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
R5 = f"{ROOT}/campaign/agents/chief/coord/HUNT_VOL2/work_r5"
for p in (ROOT + "/campaign", R5):
    if p not in sys.path:
        sys.path.insert(0, p)

import pcr5_lib as L  # noqa: E402

ANN = 252.0


# ----------------------------------------------------------------- data layer
def test_covariates_pit_no_same_day_alignment():
    """PIT audit against the SOURCE stitched obs: for a sample of sessions the covariate
    value must equal an observation dated STRICTLY BEFORE the session (and within the
    1-session carry cap), never same-day."""
    pc = L.covariates()
    for col in ("pcr_total", "pcr_equity", "pcr_etp"):
        ser = L.raw_series(col).sort_index()
        sess = pc.index
        prev = np.concatenate([np.array(["NaT"], dtype="datetime64[ns]"), sess.values[:-1]])
        idx = ser.index.searchsorted(sess.values, side="left") - 1
        at = ser.index.values[np.clip(idx, 0, None)]
        valid = (idx >= 0) & (at >= prev) & (at < sess.values)
        got = pc[col].notna().values
        assert (got == valid).all(), f"{col}: PIT mask mismatch vs source"
        # and the VALUES match the strictly-prior observation
        vals = pc[col].values
        src = ser.values[np.clip(idx, 0, None)]
        m = np.isfinite(vals) & np.isfinite(src)
        assert np.allclose(vals[m], src[m], rtol=0, atol=1e-12)


def test_covariates_nan_after_freeze():
    """No 2019 value forward-filled past the 2019-10-04 archive freeze."""
    pc = L.covariates()
    tail = pc.loc["2019-10-08":]
    assert tail.notna().sum().sum() == 0


def test_window_and_coverage():
    """Eval window = champion ∩ [2008-03-31, 2019-10-07]; >=8y span gate; >90% PIT
    coverage on champion sessions."""
    w, champ_w = L.window_frame("pcr_total")
    assert len(w) == len(champ_w) == 3007
    span_y = (champ_w.index.max() - champ_w.index.min()).days / 365.25
    assert span_y >= 8.0, span_y
    cov = w["pcr_total"].notna().mean()
    assert cov > 0.90, cov


# ------------------------------------------------------------- overlay algebra
def test_gate_ident_to_champion():
    """gate==1 everywhere -> net EXACTLY the champion (champion-identical cost conv)."""
    w, champ_w = L.window_frame("pcr_total")
    g = pd.Series(1.0, index=champ_w.index)
    net = L.overlay_net(g, champ_w)
    pd.testing.assert_series_equal(net, champ_w, check_names=False)


def test_gate_zero_costs_exit_and_hold_zero():
    """gate 1->0: day 0 holds p_{-1}=1.0 (champion pays nothing), day 1 holds 0 and pays
    the FULL |dW| entry-to-flat turn (1.6 x 6.4bps), stays 0 afterwards."""
    w, champ_w = L.window_frame("pcr_total")
    g = pd.Series(0.0, index=champ_w.index)
    net = L.overlay_net(g, champ_w)
    cost = 6.4e-4 * 1.6
    assert abs(net.iloc[0] - champ_w.iloc[0]) < 1e-15   # day 0 = champion
    assert abs(net.iloc[1] - (0.0 * champ_w.iloc[1] - cost)) < 1e-15
    assert (net.iloc[2:] == 0).all()


def test_overlay_is_t_plus_1():
    """Changing the gate on day 0 must NOT change day-0 P&L (day 0 holds p_{-1}); it
    MUST change day-1 P&L (day 1 holds g_0)."""
    w, champ_w = L.window_frame("pcr_total")
    g = L.pcr_gate(w["pcr_total"], kind="level", op="gt", thr=1.0, to=0.5)
    g2 = g.copy(); g2.iloc[0] = 0.5 if g2.iloc[0] == 1.0 else 1.0  # flip day-0 decision
    net = L.overlay_net(g, champ_w)
    net2 = L.overlay_net(g2, champ_w)
    assert abs(net.iloc[0] - net2.iloc[0]) < 1e-15
    assert abs(net.iloc[1] - net2.iloc[1]) > 0


def test_pcr_gate_semantics():
    """op/thr/to semantics: gt trims when ABOVE; lt trims when BELOW; NaN->NaN."""
    idx = pd.date_range("2010-01-04", periods=5, freq="B")
    s = pd.Series([0.8, 0.9, 1.2, 1.1, 0.7], index=idx)
    g = L.pcr_gate(s, kind="level", op="gt", thr=1.0, to=0.5)
    assert list(g.round(6)) == [1.0, 1.0, 0.5, 0.5, 1.0]
    g2 = L.pcr_gate(s, kind="level", op="lt", thr=0.85, to=0.5)
    assert list(g2.round(6)) == [0.5, 1.0, 1.0, 1.0, 0.5]  # 0.8 and 0.7 are BELOW 0.85
    s2 = s.copy(); s2.iloc[2] = np.nan
    assert np.isnan(L.pcr_gate(s2, kind="level", op="gt", thr=1.0, to=0.5).iloc[2])


def test_zscore_gate_is_causal_expanding():
    """z-gate uses expanding mean/sd (ddof=0, min_periods) — z_t recomputable from the
    prefix s[0..t] alone."""
    rng = pd.date_range("2010-01-04", periods=300, freq="B")
    s = pd.Series(np.random.default_rng(7).normal(size=300), index=rng)
    z = L.expanding_z(s, minp=120)
    t = 200
    pre = s.iloc[: t + 1]
    z_manual = (pre.iloc[-1] - pre.mean()) / pre.std(ddof=0)
    assert abs(z.iloc[t] - z_manual) < 1e-12


# ------------------------------------------------------------ reporting gates
def test_delta_stats_fields():
    w, champ_w = L.window_frame("pcr_total")
    g = pd.Series(1.0, index=champ_w.index)
    d = L.delta_stats(L.overlay_net(g, champ_w), champ_w)
    assert d["champ"]["n"] == d["net"]["n"] == 3007
    assert abs(d["d_ann"]) < 1e-12 and abs(d["d_sr"]) < 1e-12
    for k in ("ann", "sr", "mdd", "neg_yrs", "worst_yr", "h1", "h2"):
        assert k in d["champ"] and k in d["net"]


def test_era_splits_are_contiguous_and_long_enough():
    """Era-robustness: contiguous thirds + 5 sub-eras; each >= ~2y (TimesFM bar)."""
    w, champ_w = L.window_frame("pcr_total")
    eras = L.era_splits(champ_w, n=3)
    assert len(eras) == 3
    for name, (a, b) in eras.items():
        assert (b - a).days / 365.25 > 1.9, name
    eras5 = L.era_splits(champ_w, n=5)
    assert len(eras5) == 5
    for name, (a, b) in eras5.items():
        assert (b - a).days / 365.25 > 1.5, name


def test_placebo_matches_trim_frequency():
    """Adversarial control (§8h): frequency-matched random trims produce finite dSR draws
    with a fixed seed."""
    w, champ_w = L.window_frame("pcr_total")
    g = L.pcr_gate(w["pcr_total"], kind="level", op="gt", thr=0.80, to=0.0)
    freq = L.trim_frequency(g, 0.0)
    assert 0.0 < freq < 1.0
    dsr = L.random_trim_null(champ_w, freq=freq, to=0.0, n=50, seed=3)
    assert len(dsr) == 50 and np.isfinite(dsr).all()


def test_leak_probe_wired():
    """Mandatory V2 §6 Step-1: gate_run passes sig= + leak_check=True; the result carries
    leak/leak_ok. sig omitted must RAISE (fail-closed)."""
    w, champ_w = L.window_frame("pcr_total")
    g = L.pcr_gate(w["pcr_total"], kind="level", op="gt", thr=0.80, to=0.0)
    net = L.overlay_net(g, champ_w)
    sig = g.shift(1).fillna(1.0).values  # the T+1 positions actually held
    res = L.gate_run(net, L.champion(), sig=sig)
    assert "leak" in res and "leak_ok" in res and res["leak"] is not None
    assert res["leak"]["measurable"] is True
    with pytest.raises(ValueError):
        L.gate_run(net, L.champion(), sig=None)
