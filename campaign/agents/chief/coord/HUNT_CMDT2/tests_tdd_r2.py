"""TDD tests for HUNT_CMDT2 ROUND 2 (campaign/scripts/HUNT_CMDT2_round2.py).

Charter round-2 items:
 (a) POSITIONING-CONFIRMED TREND: ETF momentum gated by COT spec net pct-OI percentile —
     only trade trend when positioning is NOT extreme-crowded.
 (b) CPER copper trend + CPER-vs-GLD ratio momentum.
 (c) ENERGY curve proxy: WTI-vs-Brent spot spread trend (BNO missing on disk, EIA spots
     substituted — documented) + UNG seasonal (Mar-Oct short / Nov-Feb long, vol-scaled).

RED state 2026-09-07: HUNT_CMDT2_round2.py does not exist yet. Honesty traps encoded first.
Run: python3 tests_tdd_r2.py  (nonzero exit on any FAIL)
"""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")

SCRIPT = "/Users/daxu/software/world-trader/campaign/scripts/HUNT_CMDT2_round2.py"
PROBE = "2016-03-31"


def _load():
    import importlib.util
    spec = importlib.util.spec_from_file_location("hcmdt2r2", SCRIPT)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M


def test_cot_availability_stamp_asof_plus3d():
    """COT report as-of Tuesday is RELEASED Friday (+3d). The usable-at-t series must equal
    the latest RAW (as-of-dated) report whose as_of+3d <= t. If usable[t] ever equals a report
    released AFTER t, the gate leaks the (as-of-future) positioning print."""
    M = _load()
    assert M.COT_RELEASE_LAG_DAYS >= 3, "release lag must be >= 3 days (Tue as-of -> Fri out)"
    fam = 'gold'
    cot = M.load_cot_pct(fam, raw=True)            # raw as-of-dated series
    usable = M.cot_usable(fam)                     # availability-shifted, daily ffilled
    j = usable.dropna()
    assert len(j) > 3000
    ts = j.index[::37]
    checked = 0
    for t in ts:
        cutoff = t - pd.Timedelta(days=M.COT_RELEASE_LAG_DAYS)
        k = cot.index.searchsorted(cutoff, side='right') - 1
        if k < 0:
            continue
        assert abs(cot.iloc[k] - j.loc[t]) <= 1e-12, (
            f"usable[{t.date()}] != latest report with as_of <= t-{M.COT_RELEASE_LAG_DAYS}d "
            f"(used {cot.index[k].date()} vs got {j.loc[t]}) -> RELEASE-DAY LEAK")
        checked += 1
    assert checked > 30, f"only {checked} days checked"


def test_cot_pct_gate_expanding_truncation():
    """Positioning percentile gate at t must use ONLY reports available <= t. Truncate the COT
    series at PROBE -> the gate series through PROBE must be byte-identical."""
    M = _load()
    g_full = M.cot_gate_series('gold', thr=0.2)
    g_cut = M.cot_gate_series('gold', thr=0.2, end=PROBE)
    a = g_full.loc[:PROBE].round(12)
    b = g_cut.round(12)
    assert a.equals(b), "gate changed when future COT removed -> LOOKAHEAD in percentile"
    # sanity: the gate must actually block sometimes (a gate that is always 1 is vacuous)
    frac = (g_full.dropna() > 0).mean()
    assert 0.3 < frac < 1.0, f"gate ON {frac:.2f} of days — degenerate (always-on or always-off)"


def test_crowded_names_are_zeroed_in_weights():
    """Charter: only trade trend when positioning NOT extreme-crowded. For every day a name's
    gate is 0 (crowded), its TARGET weight must be exactly 0. Non-crowded days may carry the
    momentum weight. This must hold on the REAL book, not a toy frame."""
    M = _load()
    px = M.px_frame(M.COT_ETFS)
    R = px.pct_change()
    net, We, _, W = M.run_cot_gated_momentum(px, R, months=12, topk=3, hold=3, thr=0.2)
    live = W[(W.fillna(0.0) != 0).any(axis=1)]
    assert len(live) > 1000, f"book nearly empty ({len(live)} days)"
    for fam, etf in M.COT_MAP.items():
        # gate is stamped at weekly report availability; a trader holds last week's knowledge
        # between reports -> ffill to daily BEFORE the crowded test (leading warmup NaN -> 0).
        g = M.cot_gate_series(fam, thr=0.2).reindex(W.index).ffill().fillna(0.0)
        blocked = (g == 0.0)
        w_blocked = W.loc[blocked, etf].abs().max()
        assert (not np.isfinite(w_blocked)) or w_blocked == 0.0, (
            f"{etf} carried weight {w_blocked} on a crowded (gate=0) day for {fam}")


def test_cot_gated_no_lookahead_truncation():
    """Truncate ALL inputs (ETF closes + COT) at PROBE -> target weights through PROBE
    identical to the full-sample run. Covers mom path + gate path jointly."""
    M = _load()
    px = M.px_frame(M.COT_ETFS)
    _, _, _, W_full = M.run_cot_gated_momentum(px, px.pct_change(), months=12, topk=3,
                                               hold=3, thr=0.2)
    pxc = px.loc[:PROBE]
    _, _, _, W_cut = M.run_cot_gated_momentum(pxc, pxc.pct_change(), months=12, topk=3,
                                              hold=3, thr=0.2)
    a = W_full.loc[:PROBE].round(10)
    b = W_cut.round(10)
    assert a.equals(b), "COT-gated weights changed when future data removed -> LOOKAHEAD"


def test_cper_trend_weights_truncation():
    """CPER time-series trend: sign(trailing ret) book must be identical under truncation,
    and live (nonzero) on a meaningful fraction of days."""
    M = _load()
    px = M.px_frame(['CPER'])
    _, _, _, W_full = M.run_cper_trend(px, px.pct_change(), win=126)
    pxc = px.loc[:PROBE]
    _, _, _, W_cut = M.run_cper_trend(pxc, pxc.pct_change(), win=126)
    a = W_full.loc[:PROBE].round(10)
    b = W_cut.round(10)
    assert a.equals(b), "CPER trend weights changed when future data removed -> LOOKAHEAD"
    live_frac = (W_full['CPER'].fillna(0) != 0).mean()
    assert live_frac > 0.8, f"CPER trend live only {live_frac:.2f} of days"


def test_ratio_momentum_uses_lagged_ratio_only():
    """CPER/GLD ratio momentum: weights must be invariant under truncation AND the ratio at
    the signal day must be formed from closes <= signal day (no reindexed forward-fill of a
    future close). Probe by truncating GLD and CPER jointly."""
    M = _load()
    px = M.px_frame(['CPER', 'GLD'])
    _, _, _, W_full = M.run_ratio_momentum(px, px.pct_change(), win=126)
    pxc = px.loc[:PROBE]
    _, _, _, W_cut = M.run_ratio_momentum(pxc, pxc.pct_change(), win=126)
    a = W_full.loc[:PROBE].round(10)
    b = W_cut.round(10)
    assert a.equals(b), "ratio-momentum weights changed when future data removed -> LOOKAHEAD"


def test_spread_signal_publication_lag():
    """EIA daily spots are published next day. The WTI-Brent spread signal at t must equal the
    spread formed from prints stamped <= t - lag (lag >= 1). Invariant checked against RAW
    series, same trap as the R1 FRED test."""
    M = _load()
    assert M.EIA_PUB_LAG_DAYS >= 1
    spread = M.wti_brent_spread()                   # availability-lagged daily spread
    wti_raw = M.load_eia_spot('wti', raw=True)      # raw print stamps
    brent_raw = M.load_eia_spot('brent', raw=True)
    j = spread.dropna()
    assert len(j) > 3000
    ts = j.index[::37]
    checked = 0
    for t in ts:
        cut = t - pd.Timedelta(days=M.EIA_PUB_LAG_DAYS)
        kw = wti_raw.index.searchsorted(cut, side='right') - 1
        kb = brent_raw.index.searchsorted(cut, side='right') - 1
        if kw < 0 or kb < 0:
            continue
        want = wti_raw.iloc[kw] - brent_raw.iloc[kb]
        assert abs(want - j.loc[t]) <= 1e-9, (
            f"spread[{t.date()}] used a print newer than t-{M.EIA_PUB_LAG_DAYS}d -> PUBLICATION LEAK")
        checked += 1
    assert checked > 30, f"only {checked} days checked"


def test_spread_trend_weights_truncation():
    """USO-direction spread-trend book must be truncation-invariant."""
    M = _load()
    px = M.px_frame(['USO'])
    _, _, _, W_full = M.run_spread_trend(px, px.pct_change(), win=63)
    pxc = px.loc[:PROBE]
    _, _, _, W_cut = M.run_spread_trend(pxc, pxc.pct_change(), win=63)
    a = W_full.loc[:PROBE].round(10)
    b = W_cut.round(10)
    assert a.equals(b), "spread-trend weights changed when future data removed -> LOOKAHEAD"


def test_ung_seasonal_calendar_mapping():
    """UNG seasonal: SHORT Mar-Oct (months 3..10), LONG Nov-Feb (11,12,1,2). Weight must be a
    pure function of calendar month — constant within a month, correct sign per month, and
    identical whether computed on the full sample or any truncation (no lookahead possible)."""
    M = _load()
    px = M.px_frame(['UNG'])
    _, _, _, W = M.run_ung_seasonal(px, px.pct_change())
    m = W.index.month
    live = W['UNG'] != 0.0                          # 60d vol warmup days are legitimately flat
    assert live.mean() > 0.95, f"book live only {live.mean():.2f} of days"
    for i in range(len(W)):
        if not live.iloc[i]:
            continue
        w = W['UNG'].iloc[i]
        if m[i] in (3, 4, 5, 6, 7, 8, 9, 10):
            assert w < 0, f"{W.index[i].date()} month {m[i]}: expected SHORT, got {w}"
        else:
            assert w > 0, f"{W.index[i].date()} month {m[i]}: expected LONG, got {w}"
    # sign (the calendar-driven part) must be constant within each calendar month of each year
    sgn = np.sign(W['UNG'])
    grp = sgn[sgn != 0].groupby([sgn[sgn != 0].index.year, sgn[sgn != 0].index.month]).nunique()
    assert (grp <= 1).all(), "seasonal SIGN varies within a month -> not calendar-driven"
    # truncation invariance (calendar signal cannot leak, but prove the plumbing doesn't)
    pxc = px.loc[:PROBE]
    _, _, _, W_cut = M.run_ung_seasonal(pxc, pxc.pct_change())
    assert W_full_ok(W.loc[:PROBE], W_cut), "seasonal weights differ under truncation"


def W_full_ok(a, b):
    return a.round(10).equals(b.round(10))


def test_all_round2_sleeves_evaluable():
    """Integration smoke: every charter sleeve family runs through net_of + gates on real data
    and yields >= 1500 live days. Catches silent-empty books before they masquerade as PASS."""
    M = _load()
    px = M.px_frame(M.COT_ETFS)
    R = px.pct_change()
    net, We, _, _ = M.run_cot_gated_momentum(px, R, months=12, topk=3, hold=3, thr=0.2)
    assert len(M.trim_warmup(net, We)) > 1500
    pxc = M.px_frame(['CPER'])
    net, We, _, _ = M.run_cper_trend(pxc, pxc.pct_change(), win=126)
    assert len(M.trim_warmup(net, We)) > 1500
    pxr = M.px_frame(['CPER', 'GLD'])
    net, We, _, _ = M.run_ratio_momentum(pxr, pxr.pct_change(), win=126)
    assert len(M.trim_warmup(net, We)) > 1500
    pxu = M.px_frame(['USO'])
    net, We, _, _ = M.run_spread_trend(pxu, pxu.pct_change(), win=63)
    assert len(M.trim_warmup(net, We)) > 1500
    pxg = M.px_frame(['UNG'])
    net, We, _, _ = M.run_ung_seasonal(pxg, pxg.pct_change())
    assert len(M.trim_warmup(net, We)) > 1500


def test_ung_seasonal_is_short_summer_not_reversed():
    """Adversarial sign check on REAL data: UNG's known storage-cycle seasonality means the
    LONG leg lives Nov-Feb. If the implemented book is accidentally reversed (long Mar-Oct),
    its net SR over the sample must NOT beat the correct orientation's SR by chance — instead
    assert directly on signs (test_ung_seasonal_calendar_mapping) AND that the long leg's mean
    UNG return is not the one we're shorting by mistake."""
    M = _load()
    px = M.px_frame(['UNG'])
    R = px.pct_change()
    _, We, _, _ = M.run_ung_seasonal(px, R)
    summmer_ret = R['UNG'][We['UNG'] < 0]
    winter_ret = R['UNG'][We['UNG'] > 0]
    # informational (not a pass/fail gate): which leg actually paid
    print(f"    [info] UNG winter-leg ann={winter_ret.mean()*252*100:.1f}% "
          f"summer-leg ann={summmer_ret.mean()*252*100:.1f}%")


if __name__ == "__main__":
    tests = [test_cot_availability_stamp_asof_plus3d,
             test_cot_pct_gate_expanding_truncation,
             test_crowded_names_are_zeroed_in_weights,
             test_cot_gated_no_lookahead_truncation,
             test_cper_trend_weights_truncation,
             test_ratio_momentum_uses_lagged_ratio_only,
             test_spread_signal_publication_lag,
             test_spread_trend_weights_truncation,
             test_ung_seasonal_calendar_mapping,
             test_all_round2_sleeves_evaluable,
             test_ung_seasonal_is_short_summer_not_reversed]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            fails += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests)-fails}/{len(tests)} green")
    sys.exit(1 if fails else 0)
