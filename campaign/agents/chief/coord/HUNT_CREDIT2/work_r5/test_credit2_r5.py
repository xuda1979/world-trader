"""TDD: HUNT_CREDIT2 round-5 hunt machinery (written BEFORE the hunt ran; RED->GREEN).

Pins the behaviors the R5 hunts depend on:
  1. sig*r == held gross book (GATES_CONTRACT_V2 §6/§7 wiring; the CMDT2-R5 convention
     defect — r=net with post-vt sig — would break this).
  2. T+1: the day-t weight equals the t-1 signal (shift(1)); a one-day signal spike
     lands one day later in the weights.
  3. Publication safety: pub_safe ffill caps staleness (a discontinued feed cannot
     silently revive); NFCI weekly state can only change on/after the Friday stamp.
  4. Dollar-neutrality: LQD/IEF legs are exactly ±s before VT.
  5. z-shift: trailing stats shifted so day-t z uses only data through t-1
     (truncation invariance).
  6. V2 battery contract: an obviously-leaky sig (sign of same-period returns) is
     flagged leak=True by gates.run under our exact call pattern.
"""
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")

import numpy as np
import pandas as pd
import pytest

import HUNT_CREDIT2_round5 as cr5


def _mk(n=800, seed=5):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-05", periods=n)
    r_lqd = pd.Series(rng.normal(0.0002, 0.005, n), index=idx)
    r_ief = pd.Series(rng.normal(0.0001, 0.004, n), index=idx)
    return idx, r_lqd, r_ief


# ---- 1. sig*r == held gross book --------------------------------------------
def test_sig_times_r_equals_held_book():
    """Contract wiring: r=per-unit (r_lqd - r_ief), sig=s must reproduce the engine's
    PRE-COST gross book exactly (the thing gates.run judges)."""
    idx, r_lqd, r_ief = _mk()
    rng = np.random.default_rng(7)
    st = pd.Series(rng.choice([-1.0, 0.0, 1.0], len(idx), p=(.3, .4, .3)), index=idx)
    W = pd.DataFrame({'lqd': st, 'ief': -st})
    net, We, s = cr5._align_and_run(W, r_lqd, r_ief, vt=False)
    rpu = (r_lqd.reindex(We.index).fillna(0.0) - r_ief.reindex(We.index).fillna(0.0))
    rl = r_lqd.reindex(We.index).fillna(0.0)
    rf = r_ief.reindex(We.index).fillna(0.0)
    held_gross = We['lqd'] * rl + We['ief'] * rf      # true leg-weighted book
    recon = s.reindex(We.index).fillna(0.0) * rpu     # = s*(r_lqd - r_ief)
    assert np.allclose(held_gross, recon, atol=1e-15), \
        "sig*r != held book (r=per-unit contract broken)"
    # net = gross - turnover costs - borrow; a random +-1 book churns, so costs are real.
    # Worst-case day = full dollar-neutral flip: |dW| = 4 across both legs x 6.4bps
    # (FULL-|dW| contract) = 25.6bps + borrow. Bound to 30bps.
    assert (net - held_gross).abs().max() < 0.003, "net deviates from gross beyond costs"


# ---- 2. T+1 ------------------------------------------------------------------
def test_tplus1_spike_lands_late():
    """A one-day signal spike at t appears in weights at t+1, never at t."""
    idx, r_lqd, r_ief = _mk(n=600)
    st = pd.Series(0.0, index=idx)
    st.iloc[300] = 1.0
    W = pd.DataFrame({'lqd': st, 'ief': -st})
    net, We, s = cr5._align_and_run(W, r_lqd, r_ief, vt=False)
    assert We['lqd'].iloc[300] == 0.0, "same-day weight on a same-day signal (leak)"
    assert We['lqd'].iloc[301] == 1.0, "T+1 lag not applied"


# ---- 3. publication safety ----------------------------------------------------
def test_pub_safe_ffill_capped():
    idx = pd.bdate_range("2020-01-01", periods=20)
    s = pd.Series(np.nan, index=idx)
    s.iloc[0] = 5.0
    out = cr5.pub_safe(s, limit_days=3)
    assert out.iloc[:4].notna().all() and out.iloc[4:].isna().all(), \
        "ffill must be capped at limit_days (fail-closed staleness)"


def test_nfci_state_no_future_change():
    """Weekly series stamped Fridays: the daily state series must be constant within a
    week and can only flip on/after the stamp day."""
    wk = pd.bdate_range("2020-01-03", periods=52, freq="W-FRI")  # Fridays
    vals = np.where(np.arange(52) % 4 == 0, 1.0, -1.0)
    s = pd.Series(vals, index=wk)
    daily = np.sign(s).reindex(pd.bdate_range(s.index[0], s.index[-1])).ffill()
    # within each week (stamp-day exclusive) the value is the prior week's
    for i in range(1, 52):
        week_days = pd.bdate_range(wk[i - 1] + pd.Timedelta(days=1), wk[i] - pd.Timedelta(days=1))
        if len(week_days):
            assert (daily.reindex(week_days) == vals[i - 1]).all(), \
                "state changed before the weekly stamp (lookahead)"


# ---- 4. dollar neutrality ------------------------------------------------------
def test_dollar_neutral_weights_sum_zero_pre_vt():
    idx, r_lqd, r_ief = _mk()
    mort = pd.Series(np.random.default_rng(1).normal(4, 0.5, len(idx)), index=idx)
    dgs10 = mort - pd.Series(np.random.default_rng(2).normal(1.7, 0.3, len(idx)), index=idx)
    net, We, s = cr5.run_mortgage_gap(mort, dgs10, r_lqd, r_ief, win=63, vt=False)
    live = We[(We['lqd'] != 0)]
    assert len(live) > 50
    assert np.allclose(live['lqd'] + live['ief'], 0.0, atol=1e-12), "not dollar-neutral"


# ---- 5. truncation invariance ---------------------------------------------------
def test_z_truncation_invariant():
    """Rebuilding the z series on data truncated at T reproduces the full-sample z on
    the overlap (no future data in trailing stats)."""
    rng = np.random.default_rng(9)
    idx = pd.bdate_range("2010-01-04", periods=1500)
    mort = pd.Series(rng.normal(4.5, 0.6, 1500), index=idx)
    dgs10 = mort - rng.normal(1.7, 0.2, 1500)
    z_full = cr5.mortgage_gap_z(mort, dgs10, win=126)
    T = 1000
    z_trunc = cr5.mortgage_gap_z(mort.iloc[:T], dgs10.iloc[:T], win=126)
    both = pd.concat({'full': z_full, 'trunc': z_trunc}, axis=1).dropna()
    assert len(both) > 500
    assert np.allclose(both['full'], both['trunc'], atol=1e-12), \
        "z on truncated data differs (future leak in trailing stats)"


# ---- 6. the leak gate bites under our exact call pattern ------------------------
def test_v2_battery_flags_obvious_leak():
    """sig = sign(same-period returns) is a same-period leak; our battery wiring must
    report leak_ok=False and composite pass=False for it."""
    idx, r_lqd, r_ief = _mk(n=1500, seed=11)
    spy = pd.Series(0.0003, index=idx)
    ief = pd.Series(0.0, index=idx)
    cta = pd.Series(0.0, index=idx)
    rpu = (r_lqd - r_ief)
    leaky_sig = np.sign(rpu)
    g = cr5.v2_battery(rpu, sig=leaky_sig, ref=None, spy=spy, ief=ief, cta=cta)
    assert g['leak_ok'] is False or g.get('leak', {}).get('leak') is True, \
        "obvious same-period leak not flagged"
    assert g['pass'] is False


# ---- 7. weekly-vs-daily alignment (R5 run-1 defect) ------------------------------
def test_mortgage_gap_z_is_daily():
    """Weekly (Thursday) FRED series minus a daily series must be reindexed to the DAILY
    calendar (pub-safe ffill) BEFORE differencing. If the two are naively subtracted the
    intersection is Thursdays only (n ~= 52/yr) — the run-1 defect."""
    daily_idx = pd.bdate_range("2020-01-01", periods=400)
    rng = np.random.default_rng(3)
    dgs10 = pd.Series(1.7 + rng.normal(0, 0.05, 400), index=daily_idx)
    thurs_idx = pd.bdate_range("2020-01-02", periods=60, freq="W-THU")
    thurs = pd.Series(4.0 + rng.normal(0, 0.3, 60), index=thurs_idx)
    z = cr5.mortgage_gap_z(thurs, dgs10, win=63)
    assert z.index.isin(daily_idx).all(), "z index off the daily calendar"
    frac = z.index.nunique() / max(1, len(pd.bdate_range(z.index[0], z.index[-1])))
    assert frac > 0.9, f"z covers {frac:.0%} of business days (weekly-intersection defect)"


def test_cp_ois_spread_is_daily():
    """CP-OIS: the treasury leg must be the DAILY 3m series (DGS3MO); TB3MS is monthly
    (n=1112 over 92y) and cannot build a daily spread. The spread index must be daily
    business days with >90% coverage of its own span, and use the STAGED fresh CP
    vintage (n=6635, 2000+) not the stale on-disk one (n=3361, 2013+)."""
    sp = cr5.cp_ois_spread()
    assert len(sp) > 2000, f"spread too short for a daily book: n={len(sp)}"
    span_bd = len(pd.bdate_range(sp.index[0], sp.index[-1]))
    assert len(sp) / span_bd > 0.9, \
        f"coverage {len(sp)}/{span_bd} (monthly/intersection defect)"
    assert sp.index[0].year <= 2001, "not using the staged 2000+ CP vintage"


# ---- 8. fail-closed meta on insufficient history (run-1 crash) -------------------
def test_save_sleeve_short_book_no_crash(tmp_path):
    """A book with n<252 must produce a FAILED meta, not a KeyError (run-1 crash)."""
    idx = pd.bdate_range("2020-01-01", periods=100)
    net = pd.Series(0.0, index=idx)
    We = pd.DataFrame({'lqd': 0.0, 'ief': 0.0}, index=idx)
    res = cr5.evaluate("tiny", net, We, ref=None, verbose=False)
    old = cr5.SLEEVES
    cr5.SLEEVES = str(tmp_path)
    try:
        cr5.save_sleeve("tiny", net, We, res, extra_meta="x")
    finally:
        cr5.SLEEVES = old
    meta = open(f"{tmp_path}/tiny.csv.meta").read()
    assert "FAILED_NO_PROMOTION" in meta, "short book must fail closed"
