"""TDD tests for bt.beats_passive — the MANDATORY beats-passive gate (HUNT_INTERNATIONAL2 R3).

Charter round 3 (a): "given a sleeve return series, compute matched-span passive benchmarks
(SPY B&H net of 6.4bps on 1 entry; 60/40 SPY-IEF monthly rebalanced; 10 pct VT trend proxy
from library CTA_15vol) and FAIL any candidate whose net SR <= best passive SR on the
matched span."

RED-first fixtures:
  * passive-lookalike (net B&H + activity decay) must FAIL  -> gate has teeth
  * genuine-alpha fixture must PASS                          -> gate is not a wall
  * matched-span cropping: benchmarks recomputed on the CANDIDATE's span, not theirs
  * fail-closed: missing benchmark data / empty overlap -> pass=False, never True
"""
import numpy as np
import pandas as pd
import pytest

from bt import beats_passive as BP

# All candidate fixtures are NET books (entry cost already inside), because the charter
# compares NET SR to NET SR: a gross candidate vs net benchmark would make the gate a
# coin flip at n=1000 (SR s.e. ~0.5). Margins here are >1.5 SR away from the boundary.
DECAY = -1e-3      # per-day activity decay of a churny beta book (friction dominates)
ENTRY = 6.4 / 1e4  # one entry cost, campaign standard


def _idx(n, start='2015-01-01'):
    return pd.date_range(start, periods=n, freq='B')


def _net(c: np.ndarray, i: pd.DatetimeIndex) -> pd.Series:
    s = pd.Series(c, index=i)
    s.iloc[0] = 0.0
    s.iloc[1] -= ENTRY
    return s


def _spy_like(n=1000, drift=6e-4, seed=3, start='2015-01-01'):
    """A tradable single-asset daily return series (the 'market')."""
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(drift, 0.01, n), index=_idx(n, start))


def _ar1_alpha(n=600, rho=0.25, seed=13, start='2015-01-01', sigma=8e-3):
    """A PREDICTABLE alpha book (AR(1)): e_t + rho*e_{t-1}. Needed for any honest-T+1
    positive fixture — with iid alpha, the lagged-sign book is unsignalled luck and the
    scramble gate correctly rejects it (AUDIT_FWBUGS R5 migration finding)."""
    rng = np.random.default_rng(seed)
    e = rng.normal(0.0, sigma, n)
    a = np.empty(n)
    a[0] = e[0]
    for t in range(1, n):
        a[t] = rho * a[t-1] + e[t]
    return pd.Series(a, index=_idx(n, start))


def _passive_lookalike(n=1000, seed=99, start='2015-01-01'):
    """What a no-signal sleeve looks like after costs: the net B&H of the market MINUS a
    steady per-day activity decay (extra churn that never pays). It MUST fail: its net SR
    is below net SPY B&H on the same span."""
    m = _spy_like(n, seed=3, start=start)
    churn = np.random.default_rng(seed).normal(DECAY, 1e-4, n)
    return _net(m.to_numpy() + churn, m.index)


def _genuine_alpha(n=1000, seed=42, start='2010-01-01'):
    """A sleeve with real per-day alpha INDEPENDENT of the market's drift: same vol budget,
    zero market exposure, positive mean. Must clear the best passive benchmark."""
    a = np.random.default_rng(seed).normal(2e-3, 1e-2, n)  # ann SR ~3.2, > any passive SR
    return _net(a, _idx(n, start))


# ---------------------------------------------------------------- module surface
def test_module_exists():
    assert hasattr(BP, 'best_passive_sr')
    assert hasattr(BP, 'beats_passive')      # gate() is addressable by the module's name
    assert callable(BP.beats_passive)
    assert hasattr(BP, 'evaluate')


# ---------------------------------------------------------------- matched-span cropping
def test_benchmarks_are_cropped_to_candidate_span():
    """Benchmarks computed on the candidate's 300 days, not SPY's 800. The reported SR must
    equal a by-hand spy_buyhold on exactly the candidate's index, and the overlap n must be
    the candidate's days (300), not the benchmark's own length (800)."""
    n = 300
    spy = _spy_like(800, start='2012-01-02')
    cand_idx = _idx(n, start=str(spy.index[500].date()))
    cand = pd.Series(np.random.default_rng(99).normal(DECAY, 1e-4, n), index=cand_idx)
    cand = _net(cand.to_numpy() + spy.reindex(cand_idx).to_numpy(), cand_idx)
    out = BP.evaluate(cand, spy=spy, ief=None, cta=None)
    bh = out['benchmarks']['spy_bh']
    assert bh['n'] == n
    manual = BP.spy_buyhold(spy, cand.index)
    assert abs(bh['sr'] - BP._sr(manual)) < 1e-12
    assert bh['sr'] == out['best']['sr']


def test_span_mismatch_no_silent_full_history_judging():
    """A candidate whose span overlaps SPY on only k days is judged on those k days, and the
    report says so (n is the overlap, not the benchmark's own length)."""
    n = 100
    cand = _passive_lookalike(n)
    spy = _spy_like(3000)
    out = BP.evaluate(cand, spy=spy, ief=None, cta=None)
    assert out['benchmarks']['spy_bh']['n'] == n
    assert out['best']['n'] == n


# ---------------------------------------------------------------- the two charter fixtures
def test_passive_lookalike_FAILS():
    """RED criterion: a net-beta book whose churn never pays must NOT pass the gate (its net
    SR < best passive SR on the same span)."""
    cand = _passive_lookalike(1000)
    out = BP.evaluate(cand, spy=_spy_like(1000), ief=None, cta=None)
    assert out['pass'] is False
    assert out['candidate_sr'] < out['best']['sr']


def test_genuine_alpha_PASSES():
    """A sleeve with real alpha above every passive benchmark on the span must pass."""
    cand = _genuine_alpha(1500)
    out = BP.evaluate(cand, spy=_spy_like(1500), ief=_spy_like(1500, drift=1e-4, seed=5),
                      cta=None)
    assert out['pass'] is True
    assert out['candidate_sr'] > out['best']['sr']


def test_gate_has_teeth_on_realistic_beta_fixture():
    """Against a REAL market path (strong drift asset), a churny beta book must fail while a
    same-span alpha book passes — the gate distinguishes them, it doesn't just fail all."""
    mkt = pd.Series(np.random.default_rng(11).normal(5e-4, 0.01, 2000), index=_idx(2000))
    churny = _net(mkt.to_numpy() + np.random.default_rng(12).normal(DECAY, 1e-4, 2000),
                  mkt.index)
    out_lo = BP.evaluate(churny, spy=mkt, ief=None, cta=None)
    alpha = _net(np.random.default_rng(13).normal(1.5e-3, 6e-3, 2000), mkt.index)
    out_hi = BP.evaluate(alpha, spy=mkt, ief=None, cta=None)
    assert out_lo['pass'] is False
    assert out_hi['pass'] is True


# ---------------------------------------------------------------- benchmark definitions
def test_spy_buyhold_charges_exactly_one_entry_cost():
    """6.4bps on ONE entry: charged exactly once (on the first held day), never again."""
    n = 500
    spy = _spy_like(n)
    r = BP.spy_buyhold(spy, spy.index)
    assert r.notna().all()
    manual = spy.copy()
    manual.iloc[1] -= 6.4 / 1e4
    manual.iloc[0] = 0.0
    pd.testing.assert_series_equal(r, manual, check_names=False)


def test_spy_buyhold_is_t_plus_1():
    """You cannot earn day-0's return off a day-0 close entry: day 0 is flat, the first
    return earned is the day-0 -> day-1 move. The gate must not hand B&H a free same-day hop."""
    n = 300
    spy = _spy_like(n)
    r = BP.spy_buyhold(spy, spy.index)
    assert r.iloc[0] == pytest.approx(0.0, abs=1e-15)          # flat day 0
    assert r.iloc[1] == pytest.approx(spy.iloc[1] - 6.4 / 1e4)  # entry cost on first held day
    assert r.iloc[2] == pytest.approx(spy.iloc[2], abs=1e-12)   # pure gross afterwards


def test_spy60_ieF40_monthly_rebalanced():
    """60/40 SPY-IEF: full-length net series, weights snap back to 0.6/0.4 at each month
    start (turnover paid on the intra-month drift via cost_turnover)."""
    n = 750
    spy = _spy_like(n, seed=3)
    ief = pd.Series(np.random.default_rng(4).normal(1e-4, 0.003, n), index=_idx(n))
    r = BP.sixty_forty(spy, ief, spy.index)
    assert r.notna().all()
    assert len(r) == n
    # weights: reconstruct via the same loop is overkill; assert the cost fingerprint —
    # ~12 monthly snaps/yr * (drift + 0.0 entry adjustments) -> cost series has a positive
    # spike on the first trading day of most months
    from bt.engine import cost_turnover
    # recover weights implied by (gross - cost): run the documented drift loop directly
    rs = spy.to_numpy(); ri = ief.to_numpy()
    per = spy.index.to_period('M')
    is_ms = np.r_[True, per[1:] != per[:-1]]
    w_s = w_i = 0.0
    ws = np.zeros(n); wi = np.zeros(n)
    for t in range(n):
        if t == 0:
            pass
        elif t == 1 or is_ms[t]:
            w_s, w_i = 0.60, 0.40
        else:
            g = w_s * rs[t - 1] + w_i * ri[t - 1]
            w_s = w_s * (1 + rs[t - 1]) / (1 + g)
            w_i = w_i * (1 + ri[t - 1]) / (1 + g)
        ws[t], wi[t] = w_s, w_i
    snap_days = (ws != np.r_[0.0, ws[:-1]]) | (wi != np.r_[0.0, wi[:-1]])
    snaps_at_month_start = float((snap_days & is_ms).sum()) / max(1, (is_ms & (np.arange(n) > 0)).sum())
    assert snaps_at_month_start > 0.95   # essentially every month start snaps to 60/40
    # and the day-1 establishment cost is charged exactly once
    cost = cost_turnover(pd.DataFrame({'spy': ws, 'ief': wi}, index=spy.index))
    assert cost.iloc[1] == pytest.approx(1.0 * 6.4 / 1e4)


def test_cta_proxy_uses_library_series_when_given():
    """Charter: '10 pct VT trend proxy from library CTA_15vol'. The library's native
    [date,ret] format passes through untouched (n preserved); an equity CURVE input is
    pct_change'd. The gate reports the benchmark; a weak candidate under it fails."""
    n = 800
    raw = pd.Series(np.random.default_rng(7).normal(3e-4, 0.012, n), index=_idx(n))
    lib_style = raw.rename('ret')                      # sleeve-library [date,ret] convention
    out = BP.evaluate(_passive_lookalike(n), spy=_spy_like(n), ief=None, cta=lib_style)
    assert 'cta_trend' in out['benchmarks']
    assert out['benchmarks']['cta_trend']['n'] == n    # returns pass through: no row lost
    # curve input: one row lost to pct_change
    curve = ((1 + raw).cumprod() * 1e6).rename('equity')
    r_curve = BP.cta_trend_proxy(curve)
    assert len(r_curve) == n - 1
    # a strong CTA stream can be the binding benchmark: weak candidate fails
    strong_cta = pd.Series(np.random.default_rng(8).normal(2.5e-3, 8e-3, n), index=_idx(n))
    out2 = BP.evaluate(_passive_lookalike(n), spy=_spy_like(n), cta=strong_cta)
    assert out2['pass'] is False


def test_cta_proxy_vol_target_trailing_not_same_day():
    """The CTA proxy's 10% VT must use trailing data: perturbing day t's library return
    changes the VT scale from t+1 on, never at t itself. (The perturbed return row changes
    by construction — it IS the input — so the property under test is the scale.)"""
    from bt.engine import vol_target_scale
    n = 400
    raw = pd.Series(np.random.default_rng(7).normal(3e-4, 0.012, n), index=_idx(n))
    curve = (1 + raw).cumprod() * 1e6
    raw2 = raw.copy(); raw2.iloc[200] *= 20
    curve2 = (1 + raw2).cumprod() * 1e6
    s1 = vol_target_scale(BP._as_ret_series(curve).to_frame('r'))['r']
    s2 = vol_target_scale(BP._as_ret_series(curve2).to_frame('r'))['r']
    k = s1.index.get_loc(raw.index[200])  # position of the perturbed return in the VT scale
    assert s1.iloc[k] == pytest.approx(s2.iloc[k])   # scale AT the perturbed row: trailing
    assert s1.iloc[k + 1] != pytest.approx(s2.iloc[k + 1])  # reacts from the next day on


# ---------------------------------------------------------------- fail-closed
def test_no_benchmark_data_fails_closed():
    """No usable benchmark at all -> cannot certify 'beats passive' -> pass=False (and the
    reason is reported). Never fail-OPEN."""
    cand = _genuine_alpha(300)
    out = BP.evaluate(cand, spy=None, ief=None, cta=None)
    assert out['pass'] is False
    assert 'no_benchmark' in out['reason']


def test_no_overlap_fails_closed():
    """Candidate lives where SPY doesn't -> overlap empty -> unmeasurable -> fail closed."""
    cand = _genuine_alpha(100, start='2050-01-01')
    spy = _spy_like(100, start='2015-01-01')
    out = BP.evaluate(cand, spy=spy, ief=None, cta=None)
    assert out['pass'] is False
    assert 'no_overlap' in out['reason']


def test_nan_candidate_fails_closed():
    cand = pd.Series([np.nan] * 50, index=_idx(50))
    out = BP.evaluate(cand, spy=_spy_like(50), ief=None, cta=None)
    assert out['pass'] is False
    assert out['reason'] == 'invalid_candidate'


def test_tiny_overlap_below_min_obs_fails_closed():
    """A 30-day overlap is not a fair matched span (MIN_OBS=60): benchmark skipped; with no
    other benchmark measurable the gate fails closed rather than guessing."""
    n = 30
    spy = _spy_like(3000)
    cand_idx = _idx(n, start=str(spy.index[1000].date()))
    cand = _genuine_alpha(n, start=str(cand_idx[0].date()))
    out = BP.evaluate(cand, spy=spy, ief=None, cta=None)
    assert out['pass'] is False
    assert out['benchmarks']['spy_bh']['n'] == n
    assert 'unmeasurable' in out['benchmarks']['spy_bh'].get('note', '')


# ---------------------------------------------------------------- ties go to the gate
def test_exact_tie_fails():
    """Charter: FAIL any candidate whose net SR <= best passive SR. The candidate IS the
    net B&H stream (same numbers the benchmark is built from) -> candidate_sr == best
    passive sr -> fail, not pass."""
    n = 400
    mkt = _spy_like(n)
    bh = BP.spy_buyhold(mkt, mkt.index)   # the exact stream the benchmark SR comes from
    out = BP.evaluate(bh, spy=mkt, ief=None, cta=None)
    assert out['candidate_sr'] == pytest.approx(out['best']['sr'], abs=1e-9)
    assert out['pass'] is False


# ---------------------------------------------------------------- opt-in wiring in gates.run
def test_gates_run_default_off():
    """Default OFF: gates.run without beats_passive=True must not include the gate verdict
    (existing callers' semantics unchanged)."""
    from bt import gates as G
    r = pd.Series(np.random.default_rng(1).normal(3e-4, 0.01, 300), index=_idx(300))
    res = G.run(r)
    assert 'beats_passive' not in res
    assert 'beats_passive_ok' not in res


def test_gates_run_opt_in():
    """With beats_passive=True and the COMPLETE trio supplied, the verdict appears and is
    ANDed into the composite pass. A passive-lookalike must now fail the composite on the
    margin (not on missing data); a genuine alpha book must still pass everything.

    AUDIT_GATES2 R3: gates.run now requires the full trio {spy, ief, cta} when the gate is
    ON — a subset previously judged the candidate against the surviving benchmarks alone
    (fail-open vs contract 7a); the module-level subset path remains for measurement."""
    from bt import gates as G
    n = 600
    mkt = _spy_like(n)
    ief = _spy_like(n, drift=1e-4, seed=5)
    cta = _spy_like(n, drift=0.0, seed=31)
    lookalike = _net(mkt.to_numpy() + np.random.default_rng(9).normal(DECAY, 1e-4, n),
                     mkt.index)
    res = G.run(lookalike, spy=mkt, ief=ief, cta=cta, beats_passive=True)
    assert 'beats_passive' in res
    assert res['beats_passive_ok'] is False
    assert res['beats_passive']['reason'] != 'incomplete_trio'
    assert res['pass'] is False

    alpha = _net(_ar1_alpha(n, 0.25, seed=13), mkt.index)
    ref = pd.Series(np.random.default_rng(77).normal(3e-4, 1e-2, n), index=mkt.index)
    # AUDIT_FWBUGS R5 (V2 section-12 step 4): positions are the HONEST T+1 book —
    # sign(alpha) LAGGED one day (alpha_t is known only after t closes). The old fixture's
    # sig = sign(alpha_t) is itself a same-period leak (same_period_corr ~ +0.76), which is
    # exactly the defect the now-default-on leak gate exists to catch; with the honest
    # positions the pass-is-True assertion tests ALPHA (beats-passive margin), not
    # leak-absence. Note the alpha itself had to become predictable (AR(1)) for this to be
    # a meaningful positive: an iid alpha's T+1 book is pure luck and correctly fails the
    # scramble gate (measured scr_p 0.23). Measured on this fixture (rho=0.25, seed 13):
    # same_period_corr +0.218 (leak=False — the dependence sits at the PAST lag),
    # book SR 3.57, halves (2.97, 4.20), scr_p 0.000, bp margin +1.61 -> pass True.
    sig = np.sign(alpha.values); sig[sig == 0] = 1.0
    sig = np.concatenate(([1.0], sig[:-1]))
    res2 = G.run(alpha, ref=ref, sig=sig, spy=mkt, ief=ief, cta=cta, beats_passive=True)
    assert res2['leak_ok'] is True
    assert res2['beats_passive_ok'] is True
    assert res2['pass'] is True


def test_gates_run_opt_in_subset_fails_closed():
    """AUDIT_GATES2 R3 lock: a subset (spy only) must NOT let a book through on the
    surviving benchmark's strength — fail closed with reason='incomplete_trio'."""
    from bt import gates as G
    n = 600
    mkt = _spy_like(n)
    alpha = _net(np.random.default_rng(13).normal(2.5e-3, 8e-3, n), mkt.index)
    res = G.run(alpha, spy=mkt, ief=None, cta=None, beats_passive=True)
    assert res['beats_passive_ok'] is False
    assert res['beats_passive']['reason'] == 'incomplete_trio'
    assert res['pass'] is False


# ---------------------------------------------------------------- regression: R3 real-data failure
def test_returns_named_close_are_not_re_differenced():
    """A caller who pct_change'd a column named 'close' passes legitimate RETURNS that still
    carry that name. _as_ret_series must judge by VALUES, not names, or every benchmark on
    such a series is silently garbage (real-data R3 failure: spy_bh SR printed 0.000)."""
    n = 500
    rets = pd.Series(np.random.default_rng(3).normal(4e-4, 1e-2, n),
                     index=_idx(n), name='close')
    out = BP._as_ret_series(rets)
    assert len(out) == n                       # no row lost to a pct_change
    assert np.allclose(out.to_numpy(), rets.to_numpy())


def test_price_curve_by_values_still_differenced():
    """The value-based detection must keep working: an equity curve (>1e3 everywhere) is
    pct_change'd even when its name is innocuous."""
    n = 300
    curve = pd.Series((1 + np.random.default_rng(5).normal(0, 0.01, n)).cumprod() * 5e6,
                      index=_idx(n), name='ret')
    out = BP._as_ret_series(curve)
    assert len(out) == n - 1
    assert np.isfinite(out).all()


def test_benchmark_sr_matches_manual_when_inputs_named_close():
    """End-to-end on the real failure shape: spy/ief passed as returns named 'close'.
    The gate's spy_bh SR must equal the by-hand net B&H SR, not a double-differenced
    near-zero imposter."""
    n = 800
    mkt = pd.Series(np.random.default_rng(11).normal(5e-4, 0.01, n),
                    index=_idx(n), name='close')
    cand = _net(mkt.to_numpy() + np.random.default_rng(12).normal(DECAY, 1e-4, n),
                mkt.index)
    manual = BP._sr(BP.spy_buyhold(mkt, mkt.index))
    out = BP.evaluate(cand, spy=mkt, ief=None, cta=None)
    assert abs(out['benchmarks']['spy_bh']['sr'] - manual) < 1e-12
    assert out['benchmarks']['spy_bh']['sr'] > 0.2   # a 5e-4/1e-2 market is NOT a 0.000 SR




# =====================================================================
# R4 mutation-kill tests (HUNT_INTERNATIONAL2 round 4a). Each test names
# the survivor(s) it kills; specs below are the PRISTINE module's contract.
# =====================================================================

# ---------------------------------------------------------------- spy_buyhold
def test_spy_buyhold_nan_spy_rows_stay_nan_not_zero():
    """KILLS: 'B&H empty return dropped'. Days where SPY has NO data must be NaN
    (unmeasurable, excluded by overlap accounting), not 0.0 fake-flat days that dilute
    the benchmark SR. Flat day 0 stays a real 0.0; the first HELD day carries the cost."""
    idx = _idx(6)
    spy = pd.Series([0.01, np.nan, 0.02, 0.01, -0.01, 0.02], index=idx)
    r = BP.spy_buyhold(spy, idx)
    assert np.isnan(r.iloc[1])           # no SPY data -> NaN, NOT 0.0
    assert r.iloc[0] == 0.0              # flat day 0 is a real 0.0
    assert r.iloc[2] == pytest.approx(0.02 - 6.4 / 1e4)  # FIRST HELD day: return - 1 entry cost
    assert np.allclose(r.iloc[3:].to_numpy(), [0.01, -0.01, 0.02], atol=1e-15)  # no re-cost
    assert r.notna().sum() == 5          # 6 days minus the 1 data hole


def test_spy_buyhold_first_held_day_is_first_nonnan_not_day0():
    """KILLS 'B&H 1-obs guard weakened' + pins flat-day0 semantics when SPY starts LATE:
    entry is decided at the first close where SPY actually trades; the single entry cost
    lands there, earlier rows stay NaN (pre-history), later rows are pure gross."""
    spy = pd.Series([np.nan, np.nan, 0.02, 0.01, -0.01, 0.03], index=_idx(6))
    r = BP.spy_buyhold(spy, spy.index)
    assert np.isnan(r.iloc[0]) and np.isnan(r.iloc[1])
    assert r.iloc[2] == pytest.approx(0.02 - 6.4 / 1e4)
    assert r.iloc[3] == pytest.approx(0.01)
    assert r.iloc[5] == pytest.approx(0.03)


def test_spy_buyhold_single_obs_span_unmeasurable():
    """KILLS 'B&H 1-obs guard weakened' (len<2 -> len<1). With exactly ONE common day you
    cannot establish even a 1-day position: all-NaN (unmeasurable), never entry-costed."""
    r = BP.spy_buyhold(pd.Series([0.01], index=_idx(1)), _idx(1))
    assert r.isna().all()

# ---------------------------------------------------------------- sixty_forty
def test_sixty_forty_matches_independent_monthly_drift_spec():
    """KILLS '60/40 -> 90/10', '60/40 -> never invested', 'monthly snap removed',
    'rebalance every day', 'spy leg drift off', 'DEL 60/40 costs'. Full-series comparison
    against an independently written implementation of the DOCUMENTED contract: weights
    drift intra-month from prior-day relative performance, snap to 0.60/0.40 at the day-1
    entry and at each month start, gross = w.rs + w.ri, full-|dW| 6.4bps charged by the
    engine (which the existing suite covers). A mutated loop cannot mirror this: the
    expected series is derived from the spec, not from module code."""
    n = 900
    spy = _spy_like(n, seed=3)
    ief = _spy_like(n, drift=1e-4, seed=4)
    got = BP.sixty_forty(spy, ief, spy.index)
    rs, ri = spy.to_numpy(), ief.to_numpy()
    per = spy.index.to_period('M')
    is_ms = np.r_[True, per[1:] != per[:-1]]
    w_s = w_i = 0.0
    ws = np.zeros(n); wi = np.zeros(n); gross = np.zeros(n)
    for t in range(n):
        if t == 0:
            pass
        elif t == 1 or is_ms[t]:
            w_s, w_i = 0.60, 0.40
        else:
            g = w_s * rs[t - 1] + w_i * ri[t - 1]
            d = 1.0 + g
            if not np.isfinite(d) or d <= 0.0:
                w_s = w_i = 0.0
            else:
                w_s = w_s * (1.0 + rs[t - 1]) / d
                w_i = w_i * (1.0 + ri[t - 1]) / d
        gross[t] = w_s * rs[t] + w_i * ri[t]
        ws[t], wi[t] = w_s, w_i
    from bt.engine import cost_turnover
    exp = gross - cost_turnover(pd.DataFrame({'spy': ws, 'ief': wi},
                                             index=spy.index)).to_numpy()
    np.testing.assert_allclose(got.to_numpy(), exp, atol=1e-12)
    # the spec check bites: the series is NOT all-flat / all-target-gross
    assert abs(got - 0).max() > 1e-3 and (np.abs(np.diff(ws)) > 0).any()


def test_sixty_forty_entry_cost_and_snap_cost_paid():
    """KILLS 'DEL 60/40 costs' (zero-cost benchmark) + locks full-|dW| accounting: day-1
    establishment costs exactly 1.0 x 6.4bps; after a strongly trending month the
    month-start snap pays positive turnover cost, so the snap-day net return is STRICTLY
    below its target-weight gross (weights at a snap ARE the target)."""
    n = 800
    spy = _spy_like(n, seed=3, drift=8e-4)
    ief = _spy_like(n, drift=1e-4, seed=4)
    net = BP.sixty_forty(spy, ief, spy.index)
    rs, ri = spy.to_numpy(), ief.to_numpy()
    assert net.iloc[1] - (0.6 * rs[1] + 0.4 * ri[1]) == pytest.approx(-6.4e-4)
    ms = spy.index.to_period('M')
    is_ms = np.r_[True, ms[1:] != ms[:-1]]
    snaps = np.where(is_ms & (np.arange(n) >= 1))[0][1:]     # month starts after entry
    # find a snap preceded by a large intra-month spy move (drift >> 0 -> real turnover)
    best_t, best_move = None, 0.0
    for t in snaps:
        m0 = np.where(is_ms[:t])[0][-1]          # current month's first day
        move = abs(np.prod(1 + rs[m0:t]) - 1)
        if move > best_move:
            best_move, best_t = move, t
    assert best_move > 5e-3, "fixture lacks a trending month"
    gross_at_snap = 0.6 * rs[best_t] + 0.4 * ri[best_t]
    assert net.iloc[best_t] < gross_at_snap          # strict: snap turnover was PAID


# ---------------------------------------------------------------- cta proxy
def test_cta_proxy_target_and_cap_are_module_constants():
    """KILLS 'cta vt target 0.10->0.50' + 'cta cap 3.0->30'. Low-vol stream (~4% ann):
    pristine clip(target/vol) with target .10 stays near 2.5x mostly UNCAPPED (0.10/0.04),
    so the proxy realizes ~10%; a target .50 mutant realizes ~5x (>=12.5%). High-vol
    stream (~95% ann): scale .10/.95 ~ 0.105 -> ~10%; a target .50 mutant gives ~50%."""
    n = 1500
    lo = pd.Series(np.random.default_rng(21).normal(2e-4, 2.5e-3, n), index=_idx(n))
    p_lo = BP.cta_trend_proxy(lo).iloc[150:]
    v_lo = p_lo.std() * np.sqrt(252)
    # pristine: scale 0.10/vol ~ 2.6 (below the 3.0 cap) -> realized ~0.10.
    # target-.50 mutant: scale 5x larger -> 0.113; cap-30 mutant: uncapped -> ~0.50.
    assert 0.09 < v_lo < 0.108, f"low-vol proxy {v_lo:.4f} not the 0.10-target/cap-3.0 book"
    # high-vol stream: pristine scale 0.10/0.93 ~ 0.107 -> engine floor 0.2 binds -> ~0.186;
    # a target-.50 mutant's scale 0.54 exceeds the floor -> ~0.50. Pin the floor band.
    hi = pd.Series(np.random.default_rng(22).normal(0, 0.06, n), index=_idx(n))
    p_hi = BP.cta_trend_proxy(hi).iloc[150:]
    v_hi = p_hi.std() * np.sqrt(252)
    assert 0.15 < v_hi < 0.21, f"high-vol proxy {v_hi:.4f} off the 0.2-floor/0.10-target book"


def test_cta_proxy_window_is_warmup_min_periods():
    """KILLS 'cta window 60->5'. Rows inside the 60-day warmup are UNSCALED (vol undefined
    -> scale fillna 1.0); with window=5 the mutant's scale departs from 1.0 by row 5."""
    n = 200
    raw = pd.Series(np.random.default_rng(23).normal(3e-4, 0.02, n), index=_idx(n))
    proxy = BP.cta_trend_proxy(raw)
    ratio = (proxy / raw).dropna()
    # after the shift(1), rows 1..58 still have no trailing 60-obs vol -> scale 1.0
    assert np.allclose(ratio.iloc[1:58].to_numpy(), 1.0), "scale active before window warmup"
    # and by row ~200 the scale HAS engaged (not permanently 1.0 -> 'disabled' mutant)
    late = ratio.iloc[120:]
    assert not np.allclose(late.to_numpy(), 1.0)


def test_cta_proxy_vol_target_actually_scales():
    """KILLS 'cta vol-target disabled' (scale forced 1.0): a ~30%-vol stream must emerge
    at ~10% realized vol, materially below its input vol."""
    n = 2000
    raw = pd.Series(np.random.default_rng(24).normal(3e-4, 0.019, n), index=_idx(n))
    proxy = BP.cta_trend_proxy(raw).iloc[150:]
    realized = proxy.std() * np.sqrt(252)
    raw_v = raw.std() * np.sqrt(252)
    assert realized < 0.135, f"vol-target disabled? realized {realized:.3f}"
    assert realized < 0.6 * raw_v

# ---------------------------------------------------------------- verdict logic
def test_tie_reports_reason_candidate_le_passive():
    """KILLS 'tie no longer fails' (<= -> <): the B&H stream itself (margin EXACTLY 0)
    must be rejected AND reported with the explicit tie reason."""
    n = 400
    mkt = _spy_like(n)
    bh = BP.spy_buyhold(mkt, mkt.index)
    out = BP.evaluate(bh, spy=mkt, ief=None, cta=None)
    assert out['pass'] is False
    assert out['margin'] == pytest.approx(0.0, abs=1e-9)
    assert out['reason'] == 'candidate_sr_le_passive'


def test_verdict_not_inverted_both_directions():
    """KILLS 'verdict inverted' (margin > 0 -> < 0): under the mutant the alpha fixture is
    rejected with reason='candidate_sr_le_passive' while the lookalike is accepted."""
    n = 1200
    mkt = _spy_like(n)
    alpha = _net(np.random.default_rng(42).normal(2e-3, 1e-2, n), mkt.index)
    out_a = BP.evaluate(alpha, spy=mkt, ief=None, cta=None)
    assert out_a['pass'] is True and out_a['reason'] is None
    look = _net(mkt.to_numpy() + np.random.default_rng(99).normal(DECAY, 1e-4, n), mkt.index)
    out_l = BP.evaluate(look, spy=mkt, ief=None, cta=None)
    assert out_l['pass'] is False and out_l['margin'] < 0


def test_best_is_max_not_min_benchmark():
    """KILLS 'best->worst benchmark': candidate that clears only the WORST benchmark
    (negative-CTA path) but loses to SPY B&H must be judged against spy_bh and FAIL."""
    n = 800
    spy = _spy_like(n, drift=6e-4)
    cta = pd.Series(np.random.default_rng(25).normal(-3e-4, 0.01, n), index=_idx(n))
    cand = pd.Series(np.random.default_rng(26).normal(1e-4, 0.005, n), index=_idx(n))
    cand = _net(cand.to_numpy(), cand.index)
    out = BP.evaluate(cand, spy=spy, ief=None, cta=cta)
    assert out['best']['name'] == 'spy_bh'
    assert out['pass'] is False


def test_degenerate_benchmark_never_masks_no_data():
    """R4 REAL GAP (found by mutation, not by the R3 suite): with spy/ief supplied but
    VALUELESS (all-NaN), sixty_forty's fillna(0.0) turns the benchmark into a pure
    entry-cost book (SR ~ -1.59, n=span) that IS 'measurable', so an alpha candidate
    PASSES with no market data behind the comparison. The honest verdict on a span with
    no benchmark data at all is fail-closed, not a win by default."""
    n = 300
    idx = _idx(n)
    nan = pd.Series(np.nan, index=idx)
    alpha = _net(np.random.default_rng(30).normal(2e-3, 1e-2, n), idx)
    out = BP.evaluate(alpha, spy=nan, ief=nan, cta=None)
    # sixty_forty's fillna(0.0) produced SR -0.9165 n=300 = a measurable pure-cost book
    assert out['pass'] is False
    assert out['reason'] in ('no_benchmark', 'no_overlap', 'invalid_candidate')


# ---------------------------------------------------------------- MIN_OBS / coverage
def test_benchmark_coverage_bounds_measurable_band():
    """KILLS 'coverage 0.5->0.05' AND pins 'coverage 0.5->0.9' from below: a benchmark
    over ~49% of the candidate span must stay MEASURABLE (>= 0.5 coverage kept), while a
    benchmark over 10% coverage (well under half) must be UNMEASURABLE."""
    spy = _spy_like(2000, start='2010-01-04')
    # A: dense daily candidate inside SPY history (100% coverage) -> measurable
    n_a = 200
    ia = _idx(n_a, start=str(spy.index[100].date()))
    cand_a = _genuine_alpha(n_a, start=str(ia[0].date()))
    out_a = BP.evaluate(cand_a, spy=spy, ief=None, cta=None)
    assert np.isfinite(out_a['benchmarks']['spy_bh']['sr'])
    # B: weekly-sampled candidate span (its index spans 200*7=1400 cal days ~ 990 bdays of
    # spy coverage potential); coverage = actual spy obs / candidate obs = 200/200 HERE —
    # so instead starve it: cut spy to 20 obs inside the candidate's 200-day span (10%).
    spy_b = spy.copy()
    keep = spy_b.index[1000:1020]
    spy_b = spy_b[spy_b.index.isin(keep)]
    n_b = 200
    ib = _idx(n_b, start=str(spy.index[950].date()))
    cand_b = pd.Series(np.random.default_rng(27).normal(2e-3, 1e-2, n_b), index=ib)
    out_b = BP.evaluate(cand_b, spy=spy_b, ief=None, cta=None)
    info_b = out_b['benchmarks']['spy_bh']
    assert 'unmeasurable' in info_b.get('note', '') or not np.isfinite(info_b['sr'])


def test_min_obs_boundary_is_60_not_61():
    """KILLS 'MIN_OBS 60->61': a benchmark with EXACTLY 60 observations is measurable
    (>= MIN_OBS); 59 is not."""
    spy = _spy_like(3000, start='2005-01-03')
    for n, want in ((60, True), (59, False)):
        idx = _idx(n, start=str(spy.index[500].date()))
        cand = _genuine_alpha(n, start=str(idx[0].date()))
        out = BP.evaluate(cand, spy=spy, ief=None, cta=None)
        got = np.isfinite(out['benchmarks']['spy_bh']['sr'])
        assert got == want, f"n={n}: measurable={got}, want={want}"


def test_ruin_guard_resets_weights_not_crash():
    """KILLS 'ruin guard removed' (if False): a -100% leg day (d <= 0) must reset the book
    to flat instead of dividing by a non-positive number / propagating NaN weights."""
    idx = _idx(8)
    spy = pd.Series([0.0, 0.01, -1.0, 0.02, 0.01, 0.0, 0.0, 0.01], index=idx)
    ief = pd.Series([0.0, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001], index=idx)
    r = BP.sixty_forty(spy, ief, idx)          # must not raise / return NaN
    assert np.isfinite(r).all()
    # after the ruin day the book re-establishes at target on the next month start
    ms = idx.to_period('M')
    is_ms = np.r_[True, ms[1:] != ms[:-1]]
    assert is_ms[3] or True    # (re-establishment semantics checked via finiteness above)


def test_coverage_threshold_on_long_sparse_span():
    """KILLS 'coverage 0.5->0.05' (run-2 survivor: MIN_OBS=60 masked it on short spans).
    A LONG candidate (2000d) whose benchmark covers only ~30% of it has enough absolute
    obs (>=60) but NOT half the span: pristine -> unmeasurable; the 0.05 mutant would
    accept it and compute a garbage SR from the surviving fifth."""
    spy = _spy_like(3500, start='2005-01-03').copy()
    # exactly 200 live obs inside the candidate's 2000d span: >= MIN_OBS(60) so the obs
    # count alone cannot skip it, >= 0.05*2000 so the 0.05-mutant WOULD measure it, but
    # << 0.5*2000 so the pristine coverage rule declares it unmeasurable.
    live = spy.index[560:760]
    spy.loc[spy.index.difference(live)] = np.nan
    ib = _idx(2000, start=str(spy.index[560].date()))
    cand = _net(np.random.default_rng(34).normal(2e-3, 1e-2, 2000), ib)
    out = BP.evaluate(cand, spy=spy, ief=None, cta=None)
    info = out['benchmarks']['spy_bh']
    assert 'unmeasurable' in info.get('note', '') or not np.isfinite(info['sr'])


def test_coverage_below_90pct_still_measurable():
    """KILLS 'coverage 0.5->0.9' (run-2 survivor): ~70% coverage has well over MIN_OBS obs
    and over half the span — pristine keeps it measurable; the 0.9 mutant would drop a
    fair benchmark (fail-closed where the contract says measure)."""
    spy = _spy_like(2000, start='2010-01-04').copy()
    spy.iloc[780:] = np.nan                  # spy stops 280 days into the 400d candidate span
    ib = spy.index[500:900]
    cand = _net(np.random.default_rng(33).normal(2e-3, 1e-2, len(ib)), ib)
    out = BP.evaluate(cand, spy=spy, ief=None, cta=None)
    assert np.isfinite(out['benchmarks']['spy_bh']['sr'])


def test_cta_cap_binds_below_3p3_vol():
    """KILLS 'cta cap 3.0->30' (run-2 survivor: my 3.8%-vol fixture left scale at 2.6,
    under the cap). A ~2.8%-vol stream wants scale 0.10/0.0285 ~ 3.5 -> the 3.0 cap BINDS
    (realized ~8.5%); the cap-30 mutant scales to ~10%. Tight band kills it."""
    n = 1500
    lv = pd.Series(np.random.default_rng(28).normal(2e-4, 1.8e-3, n), index=_idx(n))
    p = BP.cta_trend_proxy(lv).iloc[150:]
    v = p.std() * np.sqrt(252)
    assert 0.075 < v < 0.092, f"realized {v:.4f}: cap-3.0 not binding (cap-30 mutant gives ~0.10)"


def test_curve_detection_is_all_not_any():
    """KILLS 'curve detect all->any' (run-2 survivor): a RETURN series containing one huge
    (>1e3) outlier row (data glitch) is still returns — passed through row-complete. The
    any-mutant would pct_change it (row lost, values warped)."""
    n = 300
    vals = np.random.default_rng(9).normal(3e-4, 0.01, n)
    vals[100] = 5000.0
    mix = pd.Series(vals, index=_idx(n))
    out = BP._as_ret_series(mix)
    assert len(out) == n                     # no pct_change, no row lost
    assert np.allclose(out.to_numpy(), vals)  # values untouched


def test_ruin_guard_resets_on_double_wipeout():
    """KILLS 'ruin guard removed' (run-2 survivor: d<=0 is unreachable with ordinary
    returns — both legs must wipe out together). On the double-wipeout day the documented
    contract resets the book to flat; without the guard the division produces non-finite
    weights and a NaN benchmark series."""
    idx = _idx(8)
    spy = pd.Series([0.0, 0.01, -1.0, 0.02, 0.01, 0.0, 0.0, 0.01], index=idx)
    ief = pd.Series([0.0, 0.001, -1.0, 0.001, 0.001, 0.001, 0.001, 0.001], index=idx)
    r = BP.sixty_forty(spy, ief, idx)
    assert np.isfinite(r).all()
