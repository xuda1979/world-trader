"""AUDIT_GATES2 round 2: procedurally enforce the scramble gate inside run().

R1 caveat: p_max sat in DEFAULTS but run() never computed the scramble — compliance was
procedural (agent discipline), not code. Charter R2(a): a candidate whose scramble is
NaN / unmeasurable / not provided must FAIL CLOSED. A control going RED means run() can
report a composite 'pass' (or a garbage p=0.0 'detected') with the scramble unmeasured.
"""
import numpy as np, pandas as pd
from bt import gates as G

import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ROOT = "/Users/daxu/software/world-trader"


def _idx(n, start='2015-01-01'):
    return pd.date_range(start, periods=n, freq='B')


def _mom_book(n=2000, seed=52, drift=0.0):
    """Genuinely strong momentum-timing book: returns from the timing itself, not drift.

    Fixture repair (coordinator standup 2026-09-07, after the original author died
    mid-round): raw is AR(1) so a LAGGED 5d mean has real forecasting power, and r is the
    PER-UNIT return stream (the scramble engine multiplies sig*r itself). The old fixture
    built sig from the CONTEMPORANEOUS rolling mean of the same raw it then multiplied —
    lookahead (SR 6.07 pure leakage) AND double-counting once the engine applied sig again
    (SR 0.07), which made the scramble controls mutually unsatisfiable. Assertions below
    are unchanged; the fixture now earns them honestly."""
    rng = np.random.default_rng(seed)
    eps = rng.normal(drift, 0.01, n)
    raw = np.empty(n)
    raw[0] = eps[0]
    for t in range(1, n):
        raw[t] = 0.55 * raw[t - 1] + eps[t]
    sig = np.sign(pd.Series(raw).rolling(5).mean().shift(1).fillna(0.0).values)
    r = pd.Series(raw, index=_idx(n))
    return r, sig


# ------------------------------------------------- a) scramble enforced in run()
def test_audit_r2_run_without_sig_fails_closed():
    """Strong sleeve but NO positions passed -> scramble unmeasured -> must NOT gate-pass."""
    r, _ = _mom_book()
    g = G.run(r, ref=pd.Series(np.random.default_rng(53).normal(0, 0.01, len(r)), index=r.index))
    assert 'scr_ok' in g, "run() reports no scramble gate at all (procedural-only compliance)"
    assert g['scr_ok'] is False, f"no-sig candidate passed the scramble gate (scr_p={g.get('scr_p')})"
    assert bool(np.isnan(g['scr_p'])), f"unmeasured scramble p must be NaN, got {g['scr_p']}"
    assert g['pass'] is False, "composite pass with an unmeasured scramble is fail-OPEN"


def test_audit_r2_run_unmeasurable_scramble_fails_closed():
    """Series too short to scramble (hi<=lo -> p=NaN) must fail the gate, not pass."""
    n = 30
    rng = np.random.default_rng(54)
    r = pd.Series(rng.normal(0.002, 0.01, n), index=_idx(n))   # SR would clear sr_min
    g = G.run(r, ref=pd.Series(rng.normal(0, 0.01, n), index=r.index),
              sig=np.ones(n), scramble_n=20)
    assert g['sr_ok'] is True, f"fixture broken: sr={g['sr']:.2f} must clear sr_min for this control"
    assert bool(np.isnan(g['scr_p'])) and g['scr_ok'] is False, \
        f"unmeasurable scramble must fail closed, got scr_p={g['scr_p']} scr_ok={g['scr_ok']}"
    assert g['pass'] is False


def test_audit_r2_scramble_nan_returns_not_garbage_p():
    """NaN-contaminated book: scramble must return an UNMEASURABLE p (NaN), not p=0.0.

    Pre-fix probe: p=0.0 with real_sr=6.44 garbage — a destroyed book reporting 'detected'."""
    rng = np.random.default_rng(55)
    n = 900
    raw = rng.normal(0, 0.01, n)
    sig = np.sign(pd.Series(raw).rolling(5).mean().fillna(0.0).values)
    raw[100:130] = np.nan
    p, real = G.scramble_positions(sig, raw, n=50, block=20, rng=rng)
    assert bool(np.isnan(p)), f"NaN-contaminated book produced a measurable p={p:.3f}"
    assert bool(np.isnan(real)), f"NaN-contaminated book SR must be NaN, got {real}"


def test_audit_r2_scramble_nan_sig_fails_closed():
    """NaN in the POSITION series is equally unmeasurable."""
    rng = np.random.default_rng(56)
    n = 900
    raw = rng.normal(0, 0.01, n)
    sig = np.sign(pd.Series(raw).rolling(5).mean().fillna(0.0).values)
    sig[400:430] = np.nan
    p, real = G.scramble_positions(sig, raw, n=50, block=20, rng=rng)
    assert bool(np.isnan(p)), f"NaN positions produced a measurable p={p:.3f}"


def test_audit_r2_run_strong_book_with_sig_passes_all():
    """Positive control: a genuinely strong book WITH its positions must clear the whole
    battery including the now-enforced scramble gate."""
    r, sig = _mom_book(n=2000, seed=57)
    p, real = G.scramble_positions(sig, r.values, n=200, block=20,
                                   rng=np.random.default_rng(58))
    assert real > 1.0, f"fixture broken: real book SR {real:.2f}"
    assert p < 0.05, f"fixture broken: strong book scramble p={p:.3f}"
    g = G.run(r, ref=pd.Series(np.random.default_rng(59).normal(0, 0.01, len(r)), index=r.index),
              sig=sig, scramble_n=200)
    assert g['scr_ok'] is True, f"strong book failed enforced scramble: scr_p={g['scr_p']}"
    assert g['pass'] is True, {k: v for k, v in g.items() if not str(k).endswith('_ok')}


def test_audit_r2_run_weak_book_with_sig_fails_scramble():
    """Negative control at the run() level: noise positions on a strong series -> scr fails,
    composite fails, even though every return-level gate clears."""
    r, _ = _mom_book(n=2000, seed=57)
    rng = np.random.default_rng(60)
    noise_sig = rng.normal(0, 1, len(r))                 # positions unrelated to returns
    g = G.run(r, ref=pd.Series(rng.normal(0, 0.01, len(r)), index=r.index),
              sig=noise_sig, scramble_n=200)
    assert g['scr_ok'] is False, f"noise positions passed scramble gate: scr_p={g['scr_p']}"
    assert g['pass'] is False


def test_audit_r2_defaults_p_max_still_locked():
    """Contract e) threshold unchanged: p < 0.05."""
    assert G.DEFAULTS['p_max'] == 0.05


# --------------------- b) noise-scramble recalibration (AUDIT_GATES2 R2b) --------------------
# Recalibrated on the NEW champion scale (SR 3.296, n=4805, campaign/results/
# GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv): noise false-pass 3.50% [7/200], KS D=0.055
# (p=0.56); on the champion's own 13 sleeve streams pooled 5.08% [66/1300], KS D=0.019.
# Strong timing books down to 10% skill-mix (book SR 0.79) are DETECTED (p=0.0000).
# These tests use fewer draws (runtime) but the same fail-open tripwire: a broken scramble
# (garbage p, or gate stuck at pass) lands FAR outside the binomial band below.
def test_audit_r2b_noise_false_pass_stays_nominal():
    """Noise positions (no skill) must not spuriously 'pass' the scramble more than a loose
    binomial band around the nominal 5% would allow."""
    rng = np.random.default_rng(7)
    n = 2000
    draws = 40
    fp = 0
    for k in range(draws):
        r = np.random.default_rng(11_000 + k).normal(0, 0.01, n)
        sig = np.random.default_rng(12_000 + k).normal(0, 1, n)
        p, _ = G.scramble_positions(sig, r, n=100, block=20,
                                    rng=np.random.default_rng(13_000 + k))
        fp += int(p < 0.05)
    # P(X>=7) under Binomial(40, 0.05) ~ 1.2e-3: RED long before a fail-open regression.
    assert fp <= 6, f"noise false-pass {fp}/{draws} = {fp/draws:.2%} >> nominal 5% (fail-open?)"


def test_audit_r2b_strong_book_detected_at_champion_scale():
    """Positive control at champion length: real timing skill must be detected (p<0.05)."""
    n = 4805  # exact champion length
    rng = np.random.default_rng(77)
    eps = rng.normal(0, 0.01, n)
    raw = np.empty(n); raw[0] = eps[0]
    for t in range(1, n):
        raw[t] = 0.55 * raw[t - 1] + eps[t]
    sig = np.sign(pd.Series(raw).rolling(5).mean().shift(1).fillna(0.0).values)
    p, real = G.scramble_positions(sig, raw, n=200, block=20,
                                   rng=np.random.default_rng(78))
    assert real > 1.0, f"fixture broken: book SR {real:.2f}"
    assert p < 0.05, f"strong book NOT detected: p={p:.3f}"
