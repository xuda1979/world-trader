"""HUNT_INTERNATIONAL2 ROUND 6 TDD suite — MY OWN battery implementations.

Charter R6(a): reproduce HUNT_TIMESFM's R5 verdicts with MY OWN battery code. These tests
pin my implementations (metrics, leak probe, scramble, beats-passive trio, book rebuild)
to the GATES_CONTRACT_V2 semantics BEFORE any real-data evaluation runs.

Run from campaign/ root: python3 -m agents.chief.coord.HUNT_INTERNATIONAL2.tests_tdd_r6
(or python3 tests_tdd_r6.py with sys.path bootstrapped below).
"""
import sys
import os

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

import importlib

MOD = None  # imported lazily so the RED phase is a clean ModuleNotFoundError


def _lib():
    global MOD
    if MOD is None:
        MOD = importlib.import_module("HUNT_INTL2_round6_lib")
    return MOD


PASS = []


def check(name, cond):
    if cond:
        PASS.append(name)
        print(f"PASS {name}")
    else:
        print(f"FAIL {name}")
        raise AssertionError(name)


def t_sr_known():
    r = pd.Series([0.01, -0.005, 0.02, 0.0, -0.01, 0.03, 0.005, -0.002] * 25,
                  index=pd.bdate_range("2020-01-01", periods=200))
    m, s = r.mean(), r.std(ddof=1)
    check("sr_known_series", abs(_lib().sr_d(r) - m / s * np.sqrt(252)) < 1e-12)


def t_halves():
    a = pd.Series([0.001] * 100)
    b = pd.Series([-0.001] * 100)
    r = pd.concat([a, b], ignore_index=True)
    h1, h2 = _lib().halves(r)
    check("halves_split", abs(h1 - _lib().sr_d(a)) < 1e-12 and abs(h2 - _lib().sr_d(b)) < 1e-12)


def t_neg_years():
    idx = pd.date_range("2020-01-01", periods=504, freq="D")
    r = pd.Series(0.001, index=idx)
    r[r.index.year == 2021] = -0.0005
    neg, worst = _lib().neg_years(r)
    n21 = int((r.index.year == 2021).sum())          # 504 calendar days span into 2021 only
    check("neg_years_counts", neg == 1 and abs(worst - ((1 - 0.0005) ** n21 - 1)) < 1e-9)


def t_leak_flags_same_period():
    rng = np.random.default_rng(7)
    r = pd.Series(rng.normal(0, 0.01, 600))
    sig = pd.Series(np.sign(r.values))          # same-period leak by construction
    p = _lib().leak_probe_own(sig, r)
    check("leak_flags_same_period", p["measurable"] and p["leak"] is True)


def t_leak_clears_causal():
    rng = np.random.default_rng(7)
    r = pd.Series(rng.normal(0, 0.01, 600))
    sig = pd.Series(np.sign(r.shift(1).fillna(0.0).values))  # reacts to PAST only
    p = _lib().leak_probe_own(sig, r)
    check("leak_clears_causal", p["measurable"] and p["leak"] is False)


def t_scramble_signal_vs_noise():
    rng = np.random.default_rng(11)
    # genuinely persistent structure: AR(1) returns, position = sign of YESTERDAY'S return
    eps = rng.normal(0, 0.01, 1500)
    r_arr = np.zeros(1500)
    for t in range(1, 1500):
        r_arr[t] = 0.6 * r_arr[t - 1] + eps[t]
    r = pd.Series(r_arr)
    sig = pd.Series(np.sign(r.shift(1).fillna(0.0).values))
    real = _lib().sr_d(sig * r)
    check("scramble_fixture_has_signal", real > 1.0)   # fixture sanity: real structure
    p_sig, _ = _lib().scramble_p_own(sig, r, n=120, seed=3)
    noise = pd.Series(rng.choice([-1.0, 1.0], 1500))
    p_noise, _ = _lib().scramble_p_own(noise, r, n=120, seed=3)
    check("scramble_signal_low_p", p_sig < 0.2)
    check("scramble_noise_high_p", p_noise > 0.2)


def _spy_fixture(idx):
    rng = np.random.default_rng(5)
    px = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, len(idx)))), index=idx)
    return _lib()._as_ret_series_own(px)          # documented caller convention: dropna'd returns


def t_spy_bh_day0_flat_entry_cost():
    idx = pd.bdate_range("2020-01-01", periods=10)
    spy = _spy_fixture(idx)
    bh = _lib().spy_buyhold_own(spy, idx)
    r = spy.reindex(idx)
    check("spy_bh_day0_flat", bh.iloc[0] == 0.0)
    check("spy_bh_entry_cost_on_first_held_day",
          abs(bh.iloc[1] - (r.iloc[1] - 6.4e-4)) < 1e-15)
    check("spy_bh_body", abs(bh.iloc[5] - r.iloc[5]) < 1e-15)


def t_sixty_forty_snap_and_entry():
    idx = pd.bdate_range("2020-01-01", periods=12)  # Jan 2020: one month-start at index 0
    spy = _spy_fixture(idx)
    ief = _spy_fixture(idx) * 0.1
    sf = _lib().sixty_forty_own(spy, ief, idx)
    check("sixty_forty_day0_flat", sf.iloc[0] == 0.0)
    # day 1: gross = .6*r_s + .4*r_i, cost = entry notional 1.0 * 6.4bps
    gross1 = 0.6 * spy.reindex(idx).iloc[1] + 0.4 * ief.reindex(idx).iloc[1]
    check("sixty_forty_entry_cost", abs(sf.iloc[1] - (gross1 - 6.4e-4)) < 1e-15)


def t_cta_vt_trailing_only():
    rng = np.random.default_rng(9)
    r = pd.Series(rng.normal(0.0004, 0.01, 400),
                  index=pd.bdate_range("2020-01-01", periods=400))
    base = _lib().vt_scale_own(r)
    r2 = r.copy()
    r2.iloc[200] = r2.iloc[200] + 0.05       # perturb day 200's return
    pert = _lib().vt_scale_own(r2)
    # trailing-only invariant on the SCALE path: scale_200 uses returns through 199
    # (unchanged), scale_201 picks up the perturbation
    check("cta_vt_trailing", abs(base.iloc[200] - pert.iloc[200]) < 1e-15
          and abs(base.iloc[201] - pert.iloc[201]) > 1e-9)


def t_book_rebuild_identity():
    """net = w*r - |dw|*6.4bps - borrow - margin; sig*rpu == net EXACTLY; flat rpu=1.0."""
    idx = pd.bdate_range("2020-01-01", periods=8)
    r = pd.Series([0.01, -0.02, 0.005, 0.0, 0.03, -0.01, 0.002, 0.004], index=idx)
    w = pd.Series([0.0, 0.5, 0.5, -0.5, -0.5, 0.0, 0.0, 0.25], index=idx)
    net, rpu = _lib().book_net_own(w, r)
    # hand-computed: entry cost at first held day (idx 1, |0.5|*6.4e-4), flip at idx 3
    # (|dw|=1.0), exit at idx 5 (|dw|=0.5) folded into last active day idx 4,
    # re-entry at idx 7 (|0.25|).
    exp_cost = pd.Series(0.0, index=idx)
    exp_cost.iloc[1] = 0.5 * 6.4e-4
    exp_cost.iloc[3] = 1.0 * 6.4e-4
    exp_cost.iloc[4] = 0.5 * 6.4e-4   # folded exit
    exp_cost.iloc[5] = 0.0            # flat day: cost folded back
    exp_cost.iloc[7] = 0.25 * 6.4e-4
    borrow = (-w.clip(upper=0.0)) * 0.005 / 252
    exp_net = w * r - exp_cost - borrow
    check("book_net_rebuild", np.abs(net.values - exp_net.values).max() < 1e-15)
    check("book_sig_rpu_identity", np.abs((w * rpu - net).values).max() < 1e-15)
    check("book_flat_rpu_is_one", rpu[w == 0].eq(1.0).all())


def t_held_weights_t1():
    cal = pd.bdate_range("2020-01-01", periods=10)
    dec = pd.DatetimeIndex([cal[2], cal[6]])
    pos = pd.Series([1.0, -1.0], index=dec)
    v = pd.Series([0.5, 0.8], index=dec)
    w = _lib().held_weights_own(cal, pos, v)
    check("held_t1_flat_before_first_decision",
          (w.iloc[:2] == 0.0).all())
    check("held_t1_decision_day_holds_prior", w.iloc[2] == 0.0)   # first decision day: prior = none
    check("held_t1_day_after_decision", w.iloc[3] == 0.5)
    check("held_t1_held_through_week", w.iloc[5] == 0.5)
    check("held_t1_second_decision_day_holds_prior", w.iloc[6] == 0.5)
    check("held_t1_day_after_second_decision", w.iloc[7] == -0.8)


def t_pos_from_forecast():
    fc = pd.DataFrame({"f1": [1.0, 2.0, 0.5], "last": [1.0, 1.9, 0.6]})
    p = _lib().pos_from_forecast(fc, "f1")
    check("pos_from_forecast_sign", list(p.values) == [0.0, 1.0, -1.0])


def t_gate_composite():
    """The composite applies contract thresholds to the BOOK and must fail a passive-lookalike."""
    idx = pd.bdate_range("2010-01-01", periods=1000)
    rng = np.random.default_rng(2)
    r = pd.Series(rng.normal(0.0001, 0.01, 1000), index=idx)   # SR ~ 0.16 << 1.0
    res = _lib().run_battery_own(net=r, rpu=r, sig=pd.Series(1.0, index=idx),
                                 ref=pd.Series(0.0, index=idx))
    check("gate_composite_fails_weak_sr", res["pass"] is False and res["sr_ok"] is False)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
    print(f"{len(PASS)}/{len(tests)} green")


if __name__ == "__main__":
    main()
