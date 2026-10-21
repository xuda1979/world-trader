#!/usr/bin/env python3
"""TDD round 2 — SPY/EWH/EWM 126d RS rotation + VIXCLS de-risk gate.

Fails until HUNT_INTL2_round2.py exists with the required semantics.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd

FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


def fresh():
    import importlib
    import campaign.scripts.HUNT_INTL2_round2 as m  # noqa
    importlib.reload(m)
    return m


# ---- fixtures ----
def fake_px(n=800, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    cols = {}
    for c, drift in [("SPY", 0.0004), ("EWH", 0.0), ("EWM", -0.0002)]:
        r = rng.normal(drift, 0.012, n)
        cols[c] = pd.Series(100 * np.cumprod(1 + r), index=idx)
    return pd.DataFrame(cols)


def test_rs_signal_no_lookahead():
    """RS signal at t must be invariant to truncating future prices."""
    m = fresh()
    px = fake_px()
    probe = px.index[500]
    s_full = m.rs_signal(px, 126)
    s_cut = m.rs_signal(px.loc[:probe], 126)
    check("rs_signal no-lookahead",
          s_full.loc[:probe].round(10).equals(s_cut.round(10)))


def test_rs_uses_only_past_prices():
    """rs_signal must equal px.shift(k)/px.shift(2k)-1 form (data <= t only, T+1-safe feed)."""
    m = fresh()
    px = fake_px()
    s = m.rs_signal(px, 126)
    spy_rel = px["SPY"] / px[["EWH", "EWM"]].mean(axis=1)
    manual = spy_rel.shift(126) / spy_rel.shift(252) - 1
    check("rs_signal trailing form (uses shifted prices only)",
          np.allclose(s.dropna().values, manual.reindex(s.dropna().index).values))


def test_vix_gate_trailing_only():
    """Gate state at t must be computable from VIX up to t-1; a change in future VIX must not
    alter past gate state."""
    m = fresh()
    idx = pd.bdate_range("2015-01-01", periods=500)
    vix = pd.Series(15.0, index=idx)
    g = m.vix_gate(vix, threshold=20.0, window=21)
    vix2 = vix.copy()
    vix2.iloc[400:] = 99.0          # shock the future only
    g2 = m.vix_gate(vix2, threshold=20.0, window=21)
    check("vix_gate no-lookahead", g.loc[:idx[398]].round(10).equals(g2.loc[:idx[398]].round(10)))
    # after the shock is in the trailing window, gate must react
    check("vix_gate reacts to high vix", g2.iloc[-1] < g.iloc[-1])


def test_gate_scales_exposure():
    """Gated weights must have smaller or equal gross than ungated, strictly smaller when VIX high."""
    m = fresh()
    idx = pd.bdate_range("2015-01-01", periods=400)
    W = pd.DataFrame({"SPY": 1.0, "EWH": -0.5, "EWM": -0.5}, index=idx)
    vix = pd.Series(14.0, index=idx)
    vix.iloc[300:] = 35.0
    Wg = m.apply_vix_gate(W, vix, threshold=20.0, window=21, floor=0.25)
    gross0 = W.abs().sum(axis=1)
    gross1 = Wg.abs().sum(axis=1)
    check("gate leaves calm-regime weights unchanged",
          np.allclose(gross1.iloc[:280].values, gross0.iloc[:280].values))
    check("gate de-risks in high-VIX regime", (gross1.iloc[330:] < gross0.iloc[330:] * 0.9).all())


def test_weights_tplus1_effective():
    """net_of must apply T+1: effective weights = target.shift(1). W set at t-0 can only
    earn the return of day +1 — so We is W shifted forward by one row."""
    m = fresh()
    idx = pd.bdate_range("2015-01-01", periods=120)
    W = pd.DataFrame({"SPY": 1.0, "EWH": 0.0, "EWM": 0.0}, index=idx)
    R = pd.DataFrame({"SPY": 0.01, "EWH": 0.0, "EWM": 0.0}, index=idx)
    net, We, _ = m.net_of(W, R, vt=False)
    # We[0]=0 (nothing decided yet), We[1]=W[0], We[2]=W[1]=1.0
    check("T+1 effective weights are shifted",
          We["SPY"].iloc[0] == 0.0 and We["SPY"].iloc[1] == 1.0 and We["SPY"].iloc[2] == 1.0)
    check("first-day return is zero under T+1", net.iloc[0] == 0.0)


def test_scramble_needs_positive_sr():
    """Scramble gate: SR<0 book can never pass (significance of being BAD is not a pass)."""
    m = fresh()
    idx = pd.bdate_range("2015-01-01", periods=300)
    rng = np.random.default_rng(1)
    W = pd.DataFrame({"SPY": 0.6, "EWH": -0.2, "EWM": -0.2}, index=idx)
    R = pd.DataFrame(rng.normal(0, 0.01, (300, 3)), index=idx, columns=W.columns)
    net, We, _ = m.net_of(W, R, vt=False)
    neg_net = -net.abs() * 0.01   # deterministic negative book
    p = m.scramble_p(We, R, neg_net, n=20, seed=5)
    sr = m.metrics.sharpe_d(neg_net)
    check("negative-SR book fails scramble gate even with small p",
          (p <= 0.05 and sr > 0) is False)


def test_rotation_weights_actually_trade():
    """REGRESSION (round-2 run crash): rotation_weights must produce a LIVE book.
    `i in reb` compared an int position to a set of Timestamps -> W stayed all-zero,
    net was empty, and the no-lookahead test passed vacuously (0s == 0s)."""
    m = fresh()
    px = fake_px(900, seed=3)
    W = m.rotation_weights(px, lookback=126, gross=1.0, mode="LS")
    live_frac = (W.fillna(0.0) != 0).any(axis=1).mean()
    check("rotation book goes live after warmup (>50% of days)", live_frac > 0.5)
    # from the first live row on, the book must stay fully invested every single day
    # (magic row constants are wrong for a monthly book: first *usable* rebalance is the
    #  first month-start after the 2*lookback signal warmup, up to ~22 extra bdays)
    live_from = (W.fillna(0.0) != 0).any(axis=1).idxmax()
    tail = W.loc[live_from:]
    check("book fully invested every day once live", (tail != 0).all().all())
    # LS mode: always net-long one side, short the other -> gross == 1.0 exactly
    gross = tail.abs().sum(axis=1)
    check("LS gross == 1.0 (half long, half short)", np.allclose(gross.values, 1.0))
    # weights only take the two legal LS patterns
    legal = ((np.isclose(tail["SPY"], 0.5) & np.isclose(tail["EWH"], -0.25)
              & np.isclose(tail["EWM"], -0.25)) |
             (np.isclose(tail["SPY"], -0.5) & np.isclose(tail["EWH"], 0.25)
              & np.isclose(tail["EWM"], 0.25)))
    check("LS weights only take legal rotation patterns", bool(legal.all().all()))
    # evaluate() must fail LOUD on a never-live book instead of crashing downstream
    import pandas as pd
    idx = pd.bdate_range("2015-01-01", periods=50)
    Wz = pd.DataFrame(0.0, index=idx, columns=["SPY", "EWH", "EWM"])
    netz = pd.Series(0.0, index=idx)
    try:
        m.trim_warmup(netz, Wz)
        empty_ok = False
    except AssertionError:
        empty_ok = True
    check("empty/never-live book raises AssertionError (fail-closed)", empty_ok)


def test_no_leakage_in_rotation_choice():
    """Rotation weights through probe must be identical with future truncated (end-to-end)."""
    m = fresh()
    px = fake_px(600, seed=9)
    probe = px.index[450]
    W_full = m.rotation_weights(px, lookback=126, gross=1.0)
    px_cut = px.loc[:probe]
    W_cut = m.rotation_weights(px_cut, lookback=126, gross=1.0)
    check("end-to-end rotation no-lookahead",
          W_full.loc[:probe].round(10).equals(W_cut.round(10)))


if __name__ == "__main__":
    test_rotation_weights_actually_trade()
    test_rs_signal_no_lookahead()
    test_rs_uses_only_past_prices()
    test_vix_gate_trailing_only()
    test_gate_scales_exposure()
    test_weights_tplus1_effective()
    test_scramble_needs_positive_sr()
    test_no_leakage_in_rotation_choice()
    print(f"\n{7-len(FAILS)}/7 green" + (f"  FAILURES: {FAILS}" if FAILS else ""))
    sys.exit(1 if FAILS else 0)
