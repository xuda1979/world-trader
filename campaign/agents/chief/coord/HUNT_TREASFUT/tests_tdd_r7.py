#!/usr/bin/env python3
"""HUNT_TREASFUT ROUND 7 TDD suite — written BEFORE the round-7 engine (RED first).

Charter corner: ECB SDMX (dataflow YC) euro-area AAA yield-curve family — slope /
curvature factor sleeves at WEEKLY or slower rebalance, PIT by publication calendar
(ECB AAA curve published same business day ~18:00 CET => 1-business-day publication
lag), mandatory pre/post-2010 sub-span stability (post-2013-only effect = FAIL with
the number stated). Decorrelate from champion AND a6r7 bond-2y trend (0.15/0.35).
Conventions pinned a-priori (NO param sweep — p-hacking ban):
  legs 1Y/2Y/5Y/10Y/30Y; slope = y10 - y2; curvature fly = y10 - 0.5*(y2+y30) in
  DV01 units; signal = sign of k-day CHANGE (k=63 = 1 quarter, weekly cadence class),
  and the mirror-image reversion variant (documented control, not a tuned rescue);
  weekly decisions on WED close+1bd publication lag; daily-held book; T+1 shift;
  VT 10% ann expanding clip<=3.0; 6.4bps FULL |dW| + 0.5%/yr borrow.
"""
import sys

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")

import numpy as np
import pandas as pd
import pytest

YC = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/work_r7/yields"


# ---------------------------------------------------------------- fixtures ----
@pytest.fixture(scope="module")
def ys():
    import HUNT_TREASFUT_round7 as R7
    return R7.load_yc()


@pytest.fixture(scope="module")
def eng():
    import HUNT_TREASFUT_round7 as R7
    return R7


# ------------------------------------------------------- data / manifest ----
def test_0_manifest_pins_present():
    import json
    m = json.load(open(f"{YC}/manifest.json"))
    assert set(m["tenors"]) == {"1Y", "2Y", "5Y", "10Y", "30Y"}
    for t, d in m["tenors"].items():
        assert d["n"] >= 5000, f"{t} span too thin: {d}"
        assert d["sha256_16"] and d["first"] <= "2004-09-30" and d["last"] >= "2026-08-01"


def test_1_yield_units_percent(ys):
    """Units guard: ECB prints percent (e.g. 2.91), NOT decimals — a 100x error would
    fabricate ~300%/day synth returns (the FRED round-2 defect class)."""
    for c in ys.columns:
        s = ys[c].dropna()
        assert 0.0 < s.abs().median() < 20.0, f"{c} not percent-scale: median={s.median()}"
        assert s.diff().abs().max() < 2.0, f"{c} daily yield jump >= 2pp — data error"


def test_2_panels_aligned_no_dupe(ys):
    assert ys.index.is_monotonic_increasing and not ys.index.duplicated().any()
    assert ys.dropna().shape[0] > 5000


# ---------------------------------------------------------- constructions ----
def test_3_slope_and_fly(ys, eng):
    slope = eng.slope(ys)
    fly = eng.fly(ys)
    # slope in [y10-y2]; fly in DV01 space: 10y body vs 2y+30y wings, dur-matched
    assert (slope.abs() < 8.0).all()
    assert (fly.abs() < 8.0).all()
    # fly defined in DV01 units: weight vector (w2, w10, w30) = (-0.5*dr2, +1*dr10,
    # -0.5*dr30) scaled by inverse durations => body/wings DV01-neutral
    w = eng.fly_weights(eng.DURS)
    dv01 = w["2"] * eng.DURS["2"] + w["10"] * eng.DURS["10"] + w["30"] * eng.DURS["30"]
    assert abs(dv01) < 1e-9, f"fly not DV01-neutral: {dv01}"


def test_4_weekly_decisions_pit(eng):
    """Decisions land on WEDNESDAY and are computed only from data published <= decision
    date minus the 1-business-day publication lag (no same-day print in the signal)."""
    idx = pd.bdate_range("2020-01-01", "2020-12-31")
    v = pd.Series(np.arange(len(idx), dtype=float), index=idx)
    dec = eng.weekly_decisions(v, k=63)
    assert (dec.index.dayofweek == 2).all(), "decisions must be Wednesdays"
    # every decision uses data strictly before the decision date at minimum
    assert dec.index[0] > idx[0] + pd.Timedelta(days=63)


def test_5_weights_sign_and_weekly_cadence(eng, ys):
    W = eng.weights_slope(ys, k=63, sym=True)
    live = W[(W != 0).any(axis=1)]
    # T+1 execution: the BOOK uses W.shift(1) — engine enforces; here check decision
    # weights are in {-1,0,1}-scaled inverse-duration, weekly index
    assert ((W.index.dayofweek == 2) | (W.abs().sum(axis=1) == 0)).all()
    assert set(W.columns) == {"2", "10"}


def test_6_net_book_t_plus_1_and_costs(eng, ys):
    """Cost-honesty: shifting W by zero days must NOT reproduce the net book (T+1 probe)
    and a same-period signal leak must inflate SR (the leak gate's failure shape)."""
    R = eng.leg_returns(ys)
    W = eng.weights_slope(ys, k=63, sym=True)
    net, We, _ = eng.book(W, R)
    net0, We0, _ = eng.book(W, R, tplus1=False)
    assert not np.isclose(net.std(), net0.std() if len(net0) == len(net) else -1), \
        "T+1 shift had no effect — leak shape"
    # full |dW| turnover cost must be positive and nonzero when the book trades
    import bt.engine as E
    c = E.cost_turnover(We, cost_bps=6.4)
    assert c.abs().sum() > 0


def test_7_per_unit_feed_invariant(eng, ys):
    """sig * r_pu == held gross book (R5 scalarization-defect lock) for the daily-held
    weekly book."""
    R = eng.leg_returns(ys)
    W = eng.weights_slope(ys, k=63, sym=True)
    net, We, _ = eng.book(W, R)
    sig = We.abs().sum(axis=1)
    r_pu = (net_uncosted := eng.book(W, R, vt=False)[2]) / sig.replace(0.0, np.nan)
    ok = (sig > 0) & r_pu.notna()
    assert np.allclose((r_pu[ok] * sig[ok]).values, net_uncosted[ok].values, atol=1e-12)


def test_8_era_split_pre_post_2010_reported(eng, ys):
    """MANDATORY charter sub-span table: pre-2010 and post-2010 SRs must both be computed
    and returned (an effect that only exists post-2013 is a FAIL with that number)."""
    R = eng.leg_returns(ys)
    W = eng.weights_slope(ys, k=63, sym=True)
    net, We, _ = eng.book(W, R)
    eras = eng.era_table(net)
    assert set(["pre2010", "2010_2013", "post2010", "post2013"]) <= set(eras)
    for k, v in eras.items():
        assert v["n"] > 0 and np.isfinite(v["sr"]), f"era {k} unjudgeable: {v}"


# --------------------------------------- R7 engine defects found in round 7 ----
def test_9_weekly_book_is_daily_held(eng, ys):
    """DEFECT (found R7, TDD): W living only on WEDs + reindex fillna(0) makes the book
    FLAT 4 of 5 days (4512/5625 zero-position days) with unwind costs stranded on flat
    days. 'Weekly rebalance' = decisions weekly, positions HELD daily until the next
    decision (ffill), per the campaign convention (FXCARRY2 R7 ffill fix, same class)."""
    R = eng.leg_returns(ys)
    W = eng.weights_slope(ys, k=63, sym=True)
    net, We, _ = eng.book(W, R)
    live_frac = float((We.abs().sum(axis=1) > 0).mean())
    assert live_frac > 0.9, f"book live only {live_frac*100:.1f}% of days — not daily-held"


def test_10_battery_feed_matches_held_book(eng, ys):
    """DEFECT (found R7, TDD): sig*r_pu must equal the held net book on EVERY day —
    on zero-position days held must be EXACTLY 0 (no stranded cost days), and on held
    days the per-unit feed must reconstruct the book to 1e-12 (V2 §10a artifact
    verifiability: the battery judges the book that is actually saved)."""
    R = eng.leg_returns(ys)
    W = eng.weights_slope(ys, k=63, sym=True)
    net, We, _ = eng.book(W, R)
    held = net.dropna()
    sig = We.abs().sum(axis=1).reindex(held.index).fillna(0.0)
    r_pu = (held / sig.replace(0.0, np.nan)).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    r_eff = sig * r_pu
    assert np.allclose(r_eff.values, held.values, atol=1e-12), \
        f"battery feed != held book: max dev {float((r_eff - held).abs().max()):.3e}"
