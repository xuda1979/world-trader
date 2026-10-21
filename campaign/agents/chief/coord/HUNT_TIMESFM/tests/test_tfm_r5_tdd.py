"""HUNT_TIMESFM ROUND 5 TDD suite — RED before work_r5/tfm_r5_lib.py exists.

Contract under test (pre-registered in FINDINGS.md R5 section, before any result):
  weekly decision dates (last trading day of ISO week, asset's own calendar),
  TimesFM h in {1,5} direction sign -> pos, VT FROZEN at decision date (trailing-only),
  held weights w_t = pos_j * v_j for t in (D_j, D_{j+1}] (strict T+1),
  costs 6.4bps full |dW| + borrow 0.5%/yr + margin 4.5%/yr,
  per-unit net r_pu with sig * r_pu == net exactly (gates.run contract),
  NKY holiday rows dropped (never filled).
"""
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r5")

import tfm_r5_lib as L  # noqa: E402


def _cal(n=40, start="2020-01-06"):
    """Business-day calendar (Mon-Fri), no holidays."""
    return pd.bdate_range(start, periods=n)


# ---------------------------------------------------------------- weekly decisions

def test_weekly_decision_dates_last_trading_day_of_iso_week():
    idx = _cal(20)  # 4 full Mon-Fri weeks
    d = L.weekly_decisions(idx)
    # last bdate of each ISO week
    exp = pd.DatetimeIndex([idx[idx.isocalendar().week == w][-1] for w in
                            sorted(set(idx.isocalendar().week))])
    assert list(d) == list(exp)


def test_weekly_decision_dates_holiday_friday_promotes_thursday():
    # _cal(10) = 2020-01-06..01-17; delete Friday 01-17 -> that ISO week's last trading
    # day must promote to Thursday 01-16
    idx = _cal(10).delete(9)
    d = L.weekly_decisions(idx)
    assert pd.Timestamp("2020-01-16") in d
    assert pd.Timestamp("2020-01-17") not in d


# ---------------------------------------------------------------- T+1 held weights

def test_t1_weight_starts_day_after_decision_and_covers_to_next_decision():
    idx = _cal(15)
    dec = L.weekly_decisions(idx)          # 01-10, 01-17, 02-07? (3 Fridays)
    pos = pd.Series({d: (+1 if i % 2 else -1) for i, d in enumerate(dec)})
    v = pd.Series(1.0, index=dec)
    w = L.held_weights(idx, pos, v)
    # on the decision day itself the PRIOR decision is held (w=0 before first decision,
    # because no prior decision exists); on dec[0]+1 the new sign appears.
    assert w.iloc[0] == 0.0
    first = dec[0]
    i0 = idx.get_loc(first)
    assert w.iloc[i0] == 0.0               # decision day holds prior (none)
    assert w.iloc[i0 + 1] == pos.iloc[0]   # T+1
    # every day t uses last decision strictly BEFORE t
    for t in idx[1:]:
        prior = [d for d in dec if d < t]
        if not prior:
            assert w.loc[t] == 0.0
        else:
            assert w.loc[t] == pos.loc[prior[-1]]


def test_zero_signal_gives_flat_book():
    idx = _cal(30)
    dec = L.weekly_decisions(idx)
    pos = pd.Series(0.0, index=dec)
    v = pd.Series(1.0, index=dec)
    w = L.held_weights(idx, pos, v)
    assert (w == 0).all()
    r = pd.Series(0.001, index=idx)
    net, rpu, sig = L.book_net(w, r)
    assert (net == 0).all() and float(sig.abs().sum()) == 0.0


# ---------------------------------------------------------------- VT freeze PIT

def test_vt_freeze_uses_only_returns_up_to_decision_date():
    idx = _cal(120)
    r = pd.Series(0.001, index=idx)
    dec = L.weekly_decisions(idx)
    v_full = L.vt_frozen(r, dec, target=0.10, minlen=60, cap=3.0)
    # corrupt the future AFTER a cut decision date -> values at/before it unchanged
    cut = dec[len(dec) // 2]
    r2 = r.copy()
    r2.loc[r2.index > cut] = 0.05
    v_cut = L.vt_frozen(r2, dec, target=0.10, minlen=60, cap=3.0)
    assert (v_full.loc[v_full.index <= cut] == v_cut.loc[v_cut.index <= cut]).all()
    # trailing-only: v at a decision date depends on returns <= that date (incl. its own)
    # and NOT on later data -> verified by the equality above.


def test_vt_frozen_scales_inverse_to_vol_and_clips():
    idx = _cal(300)
    rng = np.random.default_rng(7)
    lo = pd.Series(rng.normal(0, 0.002, len(idx)), index=idx)
    hi = pd.Series(rng.normal(0, 0.020, len(idx)), index=idx)
    dec = L.weekly_decisions(idx)
    vl = L.vt_frozen(lo, dec, 0.10, 60, 3.0).iloc[-1]
    vh = L.vt_frozen(hi, dec, 0.10, 60, 3.0).iloc[-1]
    assert vl > vh
    # vol so low the scale would exceed cap
    tiny = pd.Series(rng.normal(0, 1e-6, len(idx)), index=idx)
    vt = L.vt_frozen(tiny, dec, 0.10, 60, 3.0)
    assert vt.max() <= 3.0 + 1e-12


# ---------------------------------------------------------------- book net + per-unit

def test_book_net_cost_stack_and_per_unit_identity():
    idx = _cal(30)
    dec = L.weekly_decisions(idx)
    pos = pd.Series({d: 1.0 for d in dec})
    v = pd.Series(0.5, index=dec)  # constant half exposure, flips? no: always +1
    w = L.held_weights(idx, pos, v)
    r = pd.Series(0.001, index=idx)
    net, rpu, sig = L.book_net(w, r)
    # identity: sig * rpu == net exactly
    assert np.allclose(sig.values * rpu.values, net.values, atol=1e-15, rtol=0)
    # entry turnover charged on the first nonzero day: day after dec[0] pays 0.5*6.4bps
    i0 = w.index.get_loc(w[w != 0].index[0])
    exp_cost0 = 0.5 * 6.4e-4
    assert abs((w.iloc[i0] * r.iloc[i0] - net.iloc[i0]) - exp_cost0) < 1e-12
    # weekly turnover only: interior days have zero |dw| while exposure constant
    interior = [t for t in w.index[1:] if any(d < t for d in dec)
                and t not in [d + pd.Timedelta(days=1) for d in dec]]
    # (interior = days whose previous day had the same weight); verify directly:
    dw = w.diff().abs()
    same = [(dw.loc[t] == 0) for t in w.index if w.loc[t] != 0
            and w.index.get_loc(t) > 0 and w.iloc[w.index.get_loc(t) - 1] == w.loc[t]]
    assert all(same)


def test_book_net_short_borrow_and_margin():
    idx = _cal(30)
    dec = L.weekly_decisions(idx)
    pos = pd.Series({d: -1.0 for d in dec})
    v = pd.Series(1.0, index=dec)
    w = L.held_weights(idx, pos, v)
    r = pd.Series(0.000, index=idx)
    net, rpu, sig = L.book_net(w, r)
    # borrow 0.5%/yr on short notional; ENTRY day additionally pays 1.0*6.4bps turnover
    # (FWBUGS-R1: entry charged)
    act = w[w != 0]
    daily = -(0.005 / 252)
    exp = [daily + (-1.0) * 6.4e-4] + [daily] * (len(act) - 1)
    assert np.allclose(net.loc[act.index].values, exp, atol=1e-15)
    # gross == 1 -> no margin. With leverage 2x margin kicks in:
    v2 = pd.Series(2.0, index=dec)
    w2 = L.held_weights(idx, pos, v2)
    net2, rpu2, sig2 = L.book_net(w2, r)
    act2 = w2[w2 != 0]
    daily2 = -(0.005 / 252) * 2.0 - (1.0) * 0.045 / 252  # borrow on 2.0 short + margin (2-1)
    exp2 = [daily2 + (-2.0) * 6.4e-4] + [daily2] * (len(act2) - 1)
    assert np.allclose(net2.loc[act2.index].values, exp2, atol=1e-15)
    assert np.allclose(sig2.values * rpu2.values, net2.values, atol=1e-15, rtol=0)


# ---------------------------------------------------------------- NKY loader

def test_nky_loader_drops_nan_rows_never_fills(tmp_path):
    f = tmp_path / "NIKKEI225.csv"
    f.write_text("observation_date,NIKKEI225\n"
                 "2020-01-06,100\n2020-01-07,\n2020-01-08,101\n"
                 "2020-01-09,102\n2020-01-10,103\n")
    s = L.load_index_csv(str(f))
    assert len(s) == 4 and not s.isna().any()
    assert pd.Timestamp("2020-01-07") not in s.index
    assert s.index.is_monotonic_increasing


def test_load_index_csv_rejects_nonpositive_and_dups(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("d,v\n2020-01-06,100\n2020-01-06,101\n2020-01-07,0\n2020-01-08,102\n")
    s = L.load_index_csv(str(f))
    assert len(s) == 2 and list(s.index) == [pd.Timestamp("2020-01-06"),
                                             pd.Timestamp("2020-01-08")]


# ---------------------------------------------------------------- gates battery wiring

def test_battery_publishes_leak_dict_and_beats_passive_block():
    """V2 6/7: acceptance call must be sig= + leak_check=True + beats_passive=True trio,
    r = PER-UNIT so sig*r_pu IS the book."""
    rng = np.random.default_rng(3)
    n = 260
    idx = pd.bdate_range("2020-01-01", periods=n)
    w = pd.Series(rng.choice([-1.0, 1.0], n) * 0.5, index=idx)
    r = pd.Series(rng.normal(0, 0.01, n), index=idx)
    net, rpu, sig = L.book_net(w, r)
    from bt import gates as G
    spy = pd.Series(rng.normal(0.0002, 0.01, n), index=idx)
    ief = pd.Series(rng.normal(0.0001, 0.002, n), index=idx)
    cta = pd.Series(rng.normal(0.0003, 0.008, n), index=idx)
    res = L.run_battery(net, rpu, sig, ref=r, spy=spy, ief=ief, cta=cta)
    assert "leak" in res and "leak_ok" in res
    assert "beats_passive" in res and "beats_passive_ok" in res
    assert np.isfinite(res["scr_p"])
    # per-unit contract: gates-internal book == our net
    jr = pd.concat([rpu.rename("pu"), net.rename("net")], axis=1)
    manual = (sig * rpu).dropna()
    assert np.allclose(manual.values, net.loc[manual.index].values, atol=1e-15)


def test_exit_cost_folds_into_last_active_day_identity_exact_on_flat_days():
    """V2 gates.run contract: sig*r_pu must equal the TRUE book on EVERY day. An exit
    (w: !=0 -> 0) charges 6.4bps on the flat day where sig=0 — the battery would miss
    that cost (fail-open). Exit turnover must fold back into the last active day."""
    idx = _cal(15)
    dec = L.weekly_decisions(idx[:5])       # ONE decision only
    pos = pd.Series({dec[0]: 1.0})
    v = pd.Series(0.8, index=dec)
    w = L.held_weights(idx, pos, v)
    # force a manual exit: zero the weight after 5 active days
    w.iloc[8:] = 0.0
    r = pd.Series(0.001, index=idx)
    net, rpu, sig = L.book_net(w, r)
    # identity must hold on ALL days, including the exit day and the flat tail
    assert np.allclose(sig.values * rpu.values, net.values, atol=1e-15, rtol=0)
    # exit day itself: no cost lands there
    assert net.iloc[8] == 0.0
    # exit turnover lands on the LAST ACTIVE day (folded from the flat exit day);
    # the entry charge stays on the entry day. Total book cost unchanged.
    last_active = w[w != 0].index[-1]
    exp_cost = 0.8 * 6.4e-4          # exit only
    drag = w.loc[last_active] * r.loc[last_active] - net.loc[last_active]
    assert abs(drag - exp_cost) < 1e-12
    entry_day = w[w != 0].index[0]
    drag_in = w.loc[entry_day] * r.loc[entry_day] - net.loc[entry_day]
    assert abs(drag_in - 0.8 * 6.4e-4) < 1e-12   # entry charged (FWBUGS-R1)
    # total cost conserved: sum of drags == 2 * 0.8 * 6.4bps
    total_drag = (w * r - net).sum()
    assert abs(total_drag - 2 * 0.8 * 6.4e-4) < 1e-12


def test_battery_explicit_leak_check_true_is_passed():
    import inspect
    src = inspect.getsource(L.run_battery)
    assert "leak_check=True" in src, "acceptance call must pass leak_check=True explicitly"
    assert "beats_passive=True" in src
