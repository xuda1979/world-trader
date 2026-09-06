"""AUDIT_CHAMP2 round 1 — adversarial tests for the audit harness itself + the champion.

TDD (charter): failing tests FIRST, then fix. Two targets:

  A) campaign/audit_harness_newconstraints.py C2/C6 are vacuous:
     - audit_C2 reconstructs `port` FROM net itself (net + costs + margin_const), so the
       residual is margin_const for ANY net — even one with zero margin charged (proven by
       counterexample: no-margin series -> ok=True, residual 3.5e-19).
     - audit_C6 is `return True` — the T+1 no-lookahead gate tests nothing.
     Tests A1/A2 fail against the vacuous harness; the harness fix makes them green.

  B) FIXED BY RE-EMIT WAVE 2026-09-07 (coordinator-approved): rawew13v2_build built Wg_t from
     nav_t = cumprod(1+r)_t which contains r_t, then earns Wg_t * r_t. Same-day perturbation
     ratios 0.980-1.047 (must be 1.0 under T+1); corr(dW_t, r_t) = 0.78; honest lagged-weight
     rebuild: ann 40.84% -> 39.85% (-0.99pp), SR 3.34 -> 3.30, MDD -6.80% -> -6.84%, 0 neg yrs.
     (strict-xfail pin held until the coordinator re-emit wave: builder nav.shift(1),
     champion re-emitted at the honest ann 39.85% / SR 3.30 / MDD -6.84% / 0 neg yrs.
     B1 is now an unmarked regression lock on the causal construction.)
"""
import os, sys
import numpy as np, pandas as pd
import pytest
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

ROOT = "/Users/daxu/software/world-trader"
HARNESS = f"{ROOT}/campaign/audit_harness_newconstraints.py"
BUILDER = f"{ROOT}/campaign/scripts/rawew13v2_build.py"

GEAR, RATE, BPS = 1.6, 0.045, 6.4


def _harness():
    spec = importlib.util.spec_from_file_location("audh", HARNESS)
    h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
    return h


def _champ_builder():
    spec = importlib.util.spec_from_file_location("rawew13v2rb1", BUILDER)
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    return b


def _synth_df(n=400, k=3, seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-01", periods=n)
    return pd.DataFrame(rng.normal(0.0004, 0.008, (n, k)), index=idx,
                        columns=[f"s{i}" for i in range(k)])


def _weights(df, relw, lag):
    """NAV-drift weights, optionally lagged 1 day (T+1-correct)."""
    nav = (1 + df.fillna(0)).cumprod()
    if lag:
        nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(df.columns)
    return d2 * (GEAR / len(df.columns))


def _fake_builder(df, lag, charge_margin):
    """Build a builder-like module exposing build() -> (net, relw, gross, to, df)."""
    relw = pd.Series(1.0, index=df.columns)
    Wg = _weights(df, relw, lag)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    net = port - to * BPS / 1e4
    if charge_margin:
        net = net - (GEAR - 1) * RATE / 252
    import types
    fb = types.SimpleNamespace()
    fb.build = lambda: (net, relw, Wg.abs().sum(axis=1), to, df)
    return fb


# ---------- A: the audit harness itself ----------

def test_harness_C2_rejects_no_margin_builder():
    """audit_C2 must FAIL a builder that charges costs but NO margin (counterexample to the
    old tautology, which passed this exact series with residual 3.5e-19)."""
    h = _harness()
    fb = _fake_builder(_synth_df(), lag=True, charge_margin=False)
    ok, msg = h.audit_C2(fb)
    assert not ok, f"audit_C2 must reject a no-margin builder (it said: {msg})"


def test_harness_C2_accepts_margin_charged_builder():
    h = _harness()
    fb = _fake_builder(_synth_df(), lag=True, charge_margin=True)
    ok, msg = h.audit_C2(fb)
    assert ok, f"audit_C2 must accept a correctly-charged builder (it said: {msg})"


def test_harness_C6_rejects_same_day_weight_builder():
    """audit_C6 must FAIL a builder whose day-t weights embed day-t returns (the committed
    champion construction). The old audit_C6 was `return True` and caught nothing."""
    h = _harness()
    fb = _fake_builder(_synth_df(), lag=False, charge_margin=True)  # same-day NAV weights
    ok, msg = h.audit_C6(fb)
    assert not ok, f"audit_C6 must reject same-day-weight construction (it said: {msg})"


def test_harness_C6_accepts_causal_builder():
    h = _harness()
    fb = _fake_builder(_synth_df(), lag=True, charge_margin=True)  # nav.shift(1): T+1-correct
    ok, msg = h.audit_C6(fb)
    assert ok, f"audit_C6 must accept a causal builder (it said: {msg})"


def test_harness_C6_accepts_real_causal_champion_builder():
    """RE-EMIT WAVE 2026-09-07: the real builder is now T+1-causal (nav.shift(1)), so
    audit_C6's honest verdict must be PASS (was FAIL against the leaked construction —
    that pin did its job: it forced this test to flip before the fix could ship silently)."""
    h = _harness()
    ok, msg = h.audit_C6(_champ_builder())
    assert ok, f"audit_C6 on the (causal) champion builder must PASS (it said: {msg})"


# ---------- B: the champion's T+1 leak (blocked on coordinator re-emit) ----------

def test_champion_weights_are_t_plus_1_causal():
    """Same-day perturbation: port_t may respond to a delta in r_t ONLY via Wg_{t-1}*delta
    (weight formed at t-1). Any excess = same-day knowledge in weights = lookahead."""
    b = _champ_builder()
    net, relw, gross, to, df = b.build()
    k = len(relw)

    def port_of(frame):
        # lag=True mirrors the COMMITTED causal construction (nav.shift(1), re-emit 2026-09-07)
        Wg = _weights(frame, relw, lag=True)
        return pd.Series((frame.fillna(0).values * Wg.values).sum(axis=1), index=frame.index), Wg

    p0, Wg = port_of(df)
    ti = len(df) // 2
    worst = 0.0
    for si, delta in [(0, 0.010), (k - 1, -0.020), (k // 2, 0.050)]:
        df2 = df.copy(); df2.iat[ti, si] += delta
        p1, _ = port_of(df2)
        t = df.index[ti]
        obs = float(p1.loc[t] - p0.loc[t])
        # Wg is built with lag=True, so Wg[ti] is already formed from data through ti-1;
        # the only T+1-legal response at ti is Wg[ti, si] * delta (NOT Wg[ti-1] — that
        # double-lags and the assertion would fail at exactly 0 response... on a causal
        # builder; pre-wave it passed only because Wg[ti] itself embedded r_ti).
        exp = float(Wg.iloc[ti, si] * delta)
        # excess response in weight units (0 under T+1; handles zero-weight sleeves)
        worst = max(worst, abs(obs - exp) / (abs(delta) * (GEAR / k)))
    assert worst < 1e-6, f"T+1 violation: max excess response = {worst:.4f} weight-units (want <1e-6)"


def test_harness_C1_C5_reconstructions_are_causal_post_reemit():
    """Regression lock (standup 2026-09-07 01:0x): after the C6 re-emit made the builder
    causal (nav.shift(1)), audit_harness_newconstraints.audit_C1 still reconstructed Wg
    with the PRE-re-emit non-causal nav — its reference turnover mismatched the builder's
    charged FULL |dW| by 3.76% (ratio 1.0376) and the real-time battery false-FAILED C1
    on an honestly-costed champion. The harness must audit the construction it ships."""
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("b", f"{ROOT}/campaign/scripts/rawew13v2_build.py")
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    sys.path.insert(0, f"{ROOT}/campaign")
    import audit_harness_newconstraints as H
    ok, msg = H.audit_C1(b)
    assert ok, f"audit_C1 must PASS on the causal builder; got: {msg}"
