"""HUNT_MACRO2 round 3 TDD spec — macro-SURPRISE standalone sleeve (charter 3b).

Written BEFORE the implementation (red first). Semantics fixed here:

Vintage cube: rows (obs_date, vintage_date, value). realtime_start == the
publication date of that value (verified vs known PAYEMS anchors: obs
2009-11-01 first visible 2009-12-04). PIT rule: at date t the signal may use
only cube rows with vintage_date <= t.

CLAMPED VINTAGES (found round 3, test_cube_clamped_vintages_dropped): the fetch
window (realtime_start=2005-01-01) and each series' ALFRED birth both PIN the
first vintage of early obs periods to the window floor (PAYEMS obs 2003-01-01
shows first vintage 2005-01-01; ICSA obs 2004-01-03 shows 2009-05-28). Those
are NOT release dates. Fail-closed rule: any obs period whose FIRST vintage
equals the cube's global minimum vintage date is dropped from the release
calendar (a true release never lands on Jan-1; the one genuinely-lost ICSA week
2009-05-23 is accepted collateral, 1/1183, dropped = conservative).

Surprise: standardized jump of the FIRST-PRINT vs trailing expectation proxy.
Expectation proxy = the then-latest vintage value of the PREVIOUS obs period
(chained revision history). z = (jump - mean(past jumps)) / sd(past jumps),
where "past" = STRICTLY EARLIER scored releases (PIT). min_hist = number of
prior scored releases required before mu is defined; sd additionally requires
>= 2 (with 1 observation sd is undefined).

Event-time positioning: T+1 on the TRADING calendar (position at the first
trading day strictly after the release), NOT a champion overlay: standalone
book on a tradable ETF with 6.4bps FULL |dW| on |d(held)| (book starts flat ->
day-1 seed = first held position, not 1.0), borrow 0.5%/yr on shorts, 10% VT
trailing-only clip<=3.0.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3")

# Hard import (NOT importorskip — silent skips hid an unexecuted round in r2).
import HUNT_MACRO2_round3 as AL  # noqa: E402


# ---------------------------------------------------------------- cube helpers
def _cube():
    return pd.DataFrame({
        "obs_date":     ["2024-01-01", "2024-01-01", "2024-02-01", "2024-02-01", "2024-03-01"],
        "vintage_date": ["2024-02-02", "2024-03-01", "2024-03-15", "2024-04-12", "2024-04-15"],
        "value":        [100.0, 101.0, 102.0, 102.5, 103.0],
    })


def _cal(*days):
    """Explicit trading calendar from ISO dates (positions land on these)."""
    return pd.DatetimeIndex([pd.Timestamp(d) for d in days])


def test_cube_pit_snapshot_no_leak():
    """At t the snapshot must contain ONLY rows with vintage_date <= t.
    The classic leak: snapshot at t=2024-02-05 must NOT see the 2024-02-01 obs
    (published 2024-02-02) at its LATER revised value 101.0 — at t it holds 100.0."""
    snap = AL.snapshot_at(_cube(), pd.Timestamp("2024-02-05"))
    assert snap.loc["2024-01-01"] == 100.0          # first print, not the revision
    assert "2024-02-01" not in snap.index           # not yet published
    snap2 = AL.snapshot_at(_cube(), pd.Timestamp("2024-03-20"))
    assert snap2.loc["2024-01-01"] == 101.0         # revision visible by 2024-03-01
    assert snap2.loc["2024-02-01"] == 102.0         # first print visible 2024-03-15


def test_first_prints_and_releases():
    """Release calendar = first vintage per obs_date, MINUS clamped obs.

    SPEC FIX (round 3, was never executed): the clamp rule (module header +
    test_cube_clamped_vintages_dropped) drops ANY obs period whose first vintage
    equals the cube's global min — in _cube() that is obs 2024-01-01 (first
    vintage 2024-02-02 == min), so the old cal.loc[2024-01-01] raised KeyError.
    first_prints stays clamp-free (all 3 obs; it is a value map, not a calendar).
    The calendar conservatively drops the earliest release of EVERY cube; accepted
    collateral, real-cube-verified (PAYEMS: 23 floor-pinned obs dropped, obs
    2004-12 with a true 2005-01-07 release kept)."""
    fp = AL.first_prints(_cube())
    assert list(fp.index) == [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01"),
                              pd.Timestamp("2024-03-01")]
    assert list(fp.values) == [100.0, 102.0, 103.0]
    cal = AL.release_calendar(_cube())
    assert pd.Timestamp("2024-01-01") not in cal.index      # global-min obs -> clamped
    assert cal.loc[pd.Timestamp("2024-02-01")] == pd.Timestamp("2024-03-15")
    assert cal.loc[pd.Timestamp("2024-03-01")] == pd.Timestamp("2024-04-15")


def test_payems_release_anchor_real_data():
    """Charter 3(a) honesty: the real cube must reproduce verified release anchors.

    SPEC FIX (round 3, was never executed): the prior expectation pinned obs
    2009-12-01 -> 2010-02-05 ('Dec released in Feb'); the cube fact is
    2009-12-01 -> 2010-01-08 (first Friday of Jan, the normal NFP schedule).
    2010-02-05 is the release of obs 2010-01-01. Verified from the on-disk
    cube: vintages for 2009-12-01 = [2010-01-08, 2010-02-05, 2010-03-05, ...].
    """
    df = pd.read_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3/alfred/PAYEMS.csv",
                     parse_dates=["obs_date", "vintage_date"])
    cal = AL.release_calendar(df)
    assert cal.loc[pd.Timestamp("2009-11-01")] == pd.Timestamp("2009-12-04")
    assert cal.loc[pd.Timestamp("2009-12-01")] == pd.Timestamp("2010-01-08")
    assert cal.loc[pd.Timestamp("2010-01-01")] == pd.Timestamp("2010-02-05")


def test_cube_clamped_vintages_dropped():
    """Fetch-boundary clamp: an obs period whose FIRST vintage equals the cube's
    global min vintage date has a clamped (non-)release date and must be dropped
    from the release calendar — using it would place T+1 positions on the wrong
    days for every early observation.

    SPEC FIX (round 3, was never executed): (1) the fixture pinned BOTH 2023-09
    and 2023-11 at the floor 2024-01-01 but expected only 2023-09 dropped — the
    documented rule drops BOTH (any obs whose first vintage == global min);
    (2) the real-cube assertions compared obs dates with vintage thresholds:
    the cube fact is that obs 2004-12-01 carries a TRUE release date 2005-01-07
    (verified from disk: its first vintage is 2005-01-07, not the 2005-01-01
    floor), so it is KEPT and cal.index.min() == 2004-12-01. The 23 floor-pinned
    obs (2003-01..2004-11, plus annual revisions) are the dropped collateral."""
    cube = pd.DataFrame({
        "obs_date":     pd.to_datetime(["2023-09-01", "2023-11-01", "2023-12-01"]),
        "vintage_date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-05"]),
        "value":        [100.0, 101.0, 102.0],
    })
    cal = AL.release_calendar(cube)
    assert pd.Timestamp("2023-09-01") not in cal.index      # clamped -> dropped
    assert pd.Timestamp("2023-11-01") not in cal.index      # also pinned at the floor
    assert cal.loc[pd.Timestamp("2023-12-01")] == pd.Timestamp("2024-01-05")
    # PAYEMS real cube: 23 floor-pinned obs dropped; obs 2004-12-01 has a TRUE
    # release (2005-01-07, first Friday of Jan 2005) and must survive.
    df = pd.read_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3/alfred/PAYEMS.csv",
                     parse_dates=["obs_date", "vintage_date"])
    cal = AL.release_calendar(df)
    assert cal.index.min() == pd.Timestamp("2004-12-01")
    assert cal.loc[pd.Timestamp("2004-12-01")] == pd.Timestamp("2005-01-07")
    assert (cal == pd.Timestamp("2005-01-01")).sum() == 0   # no floor-pinned dates survive


def test_surprise_units_and_pit():
    """Surprise = (log(print/prev-obs latest-known)) - trailing mean of past such
    log-jumps, scaled by their trailing std. PIT: the scaling stats use only
    surprises STRICTLY BEFORE the current release.

    SPEC FIX (round 3, was never executed): the prior probe hit the 3rd release
    with only ONE prior scored jump and expected a z from 'two prior jumps',
    one of which was the CURRENT jump. min_hist counts PRIOR scored releases:
    release k needs >= min_hist earlier scored jumps for mu (>=2 for sd)."""
    cube = pd.DataFrame({
        "obs_date":     pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01",
                                        "2023-04-01", "2023-05-01", "2023-06-01"]),
        "vintage_date": pd.to_datetime(["2023-02-01", "2023-03-01", "2023-04-03",
                                        "2023-05-01", "2023-06-01", "2023-07-01"]),
        "value":        [100.0, 102.0, 101.0, 105.0, 104.0, 108.0],
    })
    s = AL.release_surprises(cube, min_hist=2)
    # scored rows start at the 2nd release (first release has no prior obs at all)
    assert len(s) == 5
    # warmup: z undefined until 2 prior scored jumps exist -> rows 0,1 NaN, rows 2+ finite
    assert s["z"].iloc[:2].isna().all()
    assert s["z"].iloc[2:].notna().all()
    # release 2023-05-01 (obs 2023-04-01): PIT prev-known is obs 2023-03-01 = 101.0.
    # SPEC FIX (round 3): the old expectation used 104.0 as prev — but 104 is the
    # value of obs 2023-05-01, which is NOT PUBLISHED until 2023-06-01; comparing
    # against it at the 05-01 release is lookahead. jump = log(105/101);
    # history = [log(102/100), log(101/102)] -> mu, sd from exactly those two.
    r = s.loc[pd.Timestamp("2023-05-01")]
    hist = np.array([np.log(102.0 / 100.0), np.log(101.0 / 102.0)])
    assert r["obs"] == pd.Timestamp("2023-04-01")
    assert r["jump"] == pytest.approx(np.log(105.0 / 101.0), abs=1e-12)
    assert r["mu"] == pytest.approx(hist.mean(), abs=1e-12)
    assert r["sd"] == pytest.approx(hist.std(ddof=1), abs=1e-12)
    assert r["z"] == pytest.approx((np.log(105.0 / 101.0) - hist.mean()) / hist.std(ddof=1),
                                   abs=1e-12)


def test_surprise_uses_latest_known_not_final():
    """The jump must be computed vs the LATEST KNOWN value of the previous obs
    period AS OF the release date — e.g. if the prior month was revised between
    its own release and today, the release-day comparison is vs the revision."""
    cube = pd.DataFrame({
        "obs_date":     pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01"]),
        "vintage_date": pd.to_datetime(["2023-02-01", "2023-02-20", "2023-03-01"]),
        "value":        [100.0, 101.0, 103.0],   # Jan revised to 101 on 2023-02-20
    })
    s = AL.release_surprises(cube, min_hist=0)
    r = s.loc[pd.Timestamp("2023-03-01")]
    assert r["jump"] == pytest.approx(np.log(103.0 / 101.0), abs=1e-9)  # vs revised, not 100


def test_no_position_before_first_release_and_t1():
    """Signal series: 0 before any release, and the event position is held at the
    first TRADING day strictly after the release (T+1) — including the holiday
    case: a Friday release with Monday a market holiday must hold TUESDAY.

    SPEC FIX (round 3, was never executed): the prior cube had 2 obs -> ZERO
    scoreable releases (release 1 has no prior obs; release 2 has < 2 prior
    jumps) yet expected a fire; and positions were built on a bday grid that
    ignores market holidays."""
    cube = pd.DataFrame({
        "obs_date":     pd.to_datetime(["2023-04-01", "2023-05-01", "2023-06-01",
                                        "2023-07-01"]),
        "vintage_date": pd.to_datetime(["2023-05-05", "2023-06-02", "2023-07-03",
                                        "2023-08-04"]),
        "value":        [100.0, 102.0, 103.0, 104.0],
    })
    # Clamp drops obs 2023-04-01 (first vintage 2023-05-05 = cube global min).
    # Scored releases: 2023-06-02 (no history -> z NaN), 2023-07-03 (1 prior jump ->
    # sd NaN -> z NaN), 2023-08-04 (2 prior -> z = (log(104/103)-mu)/sd = -0.72).
    # Fri 2023-08-04 release -> Mon 2023-08-07 absent from the calendar (holiday)
    # -> the T+1 position must land on TUESDAY 2023-08-08.
    cal = _cal("2023-08-03", "2023-08-04", "2023-08-08", "2023-08-09")
    sig = AL.event_signal(cube, z=1.5, hold=1, min_hist=2, cal=cal)
    assert float(sig.reindex(cal).fillna(0.0).abs().sum()) == 0.0  # |z|=0.72 < 1.5
    # thr 0: fires exactly once, at the single scored release; held at the NEXT
    # TRADING day 08-08, NOT on the missing Monday 08-07, NOT on release day.
    sig2 = AL.event_signal(cube, z=0.0, hold=1, min_hist=2, cal=cal)
    s2 = sig2.reindex(cal).fillna(0.0)
    assert s2.loc[pd.Timestamp("2023-08-04")] == 0.0     # release day: not yet held
    assert s2.loc[pd.Timestamp("2023-08-08")] == -1.0    # T+1 holiday shift; z<0
    # (jump log(104/103)=+0.97% < trailing mu +1.47% -> negative surprise -> short)
    assert float(s2.drop(index=pd.Timestamp("2023-08-08")).abs().sum()) == 0.0


def test_hold_window_decays_to_flat():
    """hold=2 means the event position is held on the first 2 trading days after
    the release, then flat (no carry into the next event unless it re-fires).

    SPEC FIX (round 3, was never executed): z=-1e9 does NOT 'fire all' — NaN z
    (warmup rows) compares False against any threshold, and with a 3-obs cube
    every row was warmup. Use 6 obs with min_hist=2 so the last 3 releases score;
    thr=-1e9 then fires every SCORED release (|NaN| >= thr is False, and that is
    the honest warmup semantics)."""
    cube = pd.DataFrame({
        "obs_date":     pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01",
                                        "2023-04-01", "2023-05-01", "2023-06-01"]),
        "vintage_date": pd.to_datetime(["2023-02-01", "2023-03-01", "2023-04-03",
                                        "2023-05-01", "2023-06-01", "2023-07-03"]),
        "value":        [100.0, 102.0, 101.0, 105.0, 104.0, 108.0],
    })
    cal = pd.bdate_range("2023-01-25", "2023-07-21")        # all trading weekdays here
    sig = AL.event_signal(cube, z=-1e9, hold=2, min_hist=2, cal=cal).reindex(cal).fillna(0.0)
    # first two releases are warmup (z NaN) -> nothing held before 2023-05-02
    assert float(sig.loc[:pd.Timestamp("2023-05-01")].abs().sum()) == 0.0
    # release 2023-05-01 (Mon): held Mon+1=05-02 and 05-03, flat from 05-04
    assert sig.loc[pd.Timestamp("2023-05-02")] != 0.0
    assert sig.loc[pd.Timestamp("2023-05-03")] != 0.0
    assert sig.loc[pd.Timestamp("2023-05-04")] == 0.0
    # release 2023-06-01 (Thu): held 06-02, 06-05 (Fri+Mon), flat 06-06
    assert sig.loc[pd.Timestamp("2023-06-02")] != 0.0
    assert sig.loc[pd.Timestamp("2023-06-05")] != 0.0
    assert sig.loc[pd.Timestamp("2023-06-06")] == 0.0
    # last release 2023-07-03 (Mon): cal is a plain bday grid (07-04 is in it), so
    # the 2 bday holds are 07-04 AND 07-05.
    # SPEC FIX (round 3, was never executed): the old assertion pinned 07-05 == 0
    # while its own comment said the bday grid holds 07-04+07-05 — self-contradictory.
    # hold=2 exactly -> 07-04, 07-05 held; flat again 07-06 (the grid ends 07-21).
    assert sig.loc[pd.Timestamp("2023-07-04")] != 0.0
    assert sig.loc[pd.Timestamp("2023-07-05")] != 0.0
    assert sig.loc[pd.Timestamp("2023-07-06")] == 0.0


def test_vt_trailing_only_and_clip():
    """VT scale uses returns up to t-1 only, clip <=3.0, 10% target."""
    r = pd.Series(0.001, index=pd.bdate_range("2020-01-01", periods=300))
    sc = AL.vt_scale(r, target=0.10)
    assert sc.max() <= 3.0 + 1e-12
    # scale at t must not change if r[t] changes (trailing-only)
    r2 = r.copy(); r2.iloc[150] = 0.05
    assert sc.iloc[150] == AL.vt_scale(r2, target=0.10).iloc[150]


def test_net_costs_full_dw_and_borrow():
    """net = ps*r - 6.4bps*|d ps| - 0.5%/yr*short, where ps = held positions
    (T+1 applied) and the day-1 seed is |ps[0]| — the book STARTS FLAT, so the
    first day's cost is the first ENTRY, not a full 1.0 notional.

    SPEC FIX (round 3, was never executed): prior version (a) treated the tuple
    return of net_of() as a Series, and (b) seeded day-1 cost with 1.0 while its
    own weights start at 0.0 — the first held position is 0, so day-1 cost is 0
    and the entry is charged on the day the position actually appears."""
    w = pd.Series([0.0, 1.0, 1.0, -1.0, 0.0], index=pd.bdate_range("2020-01-06", periods=5))
    r = pd.Series([0.01, 0.01, 0.01, 0.01, 0.01], index=w.index)
    net, ps = AL.net_of(w, r, vt=False)
    exp_ps = w.shift(1).fillna(0.0)                          # T+1
    to = exp_ps.diff().abs()
    to.iloc[0] = abs(exp_ps.iloc[0])                         # seed = first held position
    exp = exp_ps * r - to * 6.4e-4 - (-exp_ps.clip(upper=0.0)) * 0.005 / 252.0
    pd.testing.assert_series_equal(net, exp, check_names=False)
    pd.testing.assert_series_equal(ps, exp_ps, check_names=False)
    assert net.iloc[0] == pytest.approx(0.0, abs=1e-15)      # flat day 0: no cost seeded


def test_gate_battery_passes_fail_closed():
    """evaluate() must FAIL any sleeve missing ANY contract gate (fail-closed),
    and must ALWAYS report the verdict under the same key ('pass') — including
    the too-short-book path (the old n<500 branch returned 'pass_', a key nothing
    read: fail-open reporting)."""
    res = AL.evaluate("t", pd.Series([0.0, 0.0]), verbose=False)
    assert res["pass"] is False
    assert "why" in res
    # ENGINE FIX (round 3): the too-short / missing-scramble paths used to report
    # under 'pass_' (fail-open reporting — a verdict key nothing read). Pinned here.
    res_short = AL.evaluate("t_short", pd.Series([0.0, 0.0]), verbose=False)
    res_nosc = AL.evaluate("t_nosc", pd.Series(np.zeros(800)), verbose=False)
    assert res_short["pass"] is False and "why" in res_short
    assert res_nosc["pass"] is False and "why" in res_nosc
    # a real-length book must come back with the full gate set, finite scramble p
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2015-01-01", periods=800)
    r_pu = pd.Series(rng.normal(0.0004, 0.011, 800), index=idx)
    sig = pd.Series(np.where(rng.random(800) > 0.97, 1.0, 0.0), index=idx)
    res2 = AL.evaluate("t2", *AL.net_of(sig, r_pu), ps_of=None, verbose=False) \
        if False else AL.evaluate("t2", AL.net_of(sig, r_pu)[0],
                                  ps=AL.net_of(sig, r_pu)[1], r_pu=r_pu, verbose=False)
    assert np.isfinite(res2["p"]), "scramble must be measured, not skipped"
    for k in ["sr", "h1", "h2", "neg", "worst", "corr", "ann", "n"]:
        assert k in res2, k
    for k in ["a_sr", "c_halves", "d_yearly", "f_corr", "e_scramble"]:
        assert k in res2["ok"], k
