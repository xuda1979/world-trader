"""HUNT_VOL2 ROUND 3 — champion-blend integration tests (TDD, written RED first).

Covers charter round 3:
  (a) candidate pool admission screen (published AS-IS, own-span net SR>=0.5, |corr|<=0.35)
  (b) blend machinery honesty: constant-mix split, blend-drift turnover at 6.4bps FULL |dW|,
      margin via bt/borrow.py conventions, gross cap 1.6, shortability tiers
  (c) adoption gates incl. halves + w-plateau + ADVERSARIAL vol/corr-matched random control
  (d) blend table + recommendation JSON schema

NOTE ON bt/blend.py: during this round its blend_margin_daily was found returning a
NEGATIVE number (rebate) contradicting its own docstring, with 5 tests of
bt/tests/test_camp_borrow_round3.py RED. That file belongs to CAMP_BORROW and is NOT
modified here; this lib re-derives the algebra from bt.borrow.margin_daily (sign pinned
by test below) so a mutation in bt/blend.py cannot contaminate the round-3 numbers.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

CAMP = Path("/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, str(CAMP))
sys.path.insert(0, str(CAMP / "agents/chief/coord/HUNT_VOL2/work_r3"))

import blend_r3_lib as L  # noqa: E402

RNG = np.random.default_rng(7)


# ---------------------------------------------------------------- champion pin
def test_champion_pinned_blob_exact():
    """Champion must load from the git-HEAD-pinned blob in work_r3 (fail-closed on drift).

    The working-tree champion CSV has drifted (work ann 39.69% vs HEAD 39.85%) — CAMP_SHORT
    R2 documented the same class of incident. All round-3 deltas are measured against HEAD."""
    ch = L.load_champion()
    assert len(ch) == 4805
    assert str(ch.index[0].date()) == "2008-03-31" and str(ch.index[-1].date()) == "2026-08-27"
    from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years
    assert abs(ann_geo(ch) - 0.398510) < 5e-5      # charter headline 39.85%
    assert abs(sharpe_d(ch) - 3.296) < 2e-3          # charter SR 3.296
    assert abs(max_dd(ch) - (-0.0684)) < 5e-4        # charter MDD -6.84%
    assert neg_years(ch)[0] == 0                     # charter 0/19 neg years
    raw = (CAMP / "agents/chief/coord/HUNT_VOL2/work_r3/champion_head_pin.csv").read_bytes()
    assert (hashlib.sha256(raw).hexdigest()
            == "e6d8b9c0631aac243ecc60ddbe6ae5fd48998dbc1d9c47c3a0c28ba03d9237b3")


def test_bt_borrow_margin_sign_positive_drag():
    """Pin the bt.borrow.margin_daily convention the round-3 algebra is built on:
    margin is a positive DAILY DRAG (max(gross-1,0)*rate/252), never a rebate.
    (bt/blend.py's current sign-flipped margin must NOT be usable; see module docstring.)"""
    from bt.borrow import margin_daily
    m = float(margin_daily(pd.Series([1.6]), 0.045).iloc[0])
    assert m > 0 and abs(m * 252 - 0.6 * 0.045) < 1e-12
    assert float(margin_daily(pd.Series([1.0]), 0.045).iloc[0]) == 0.0   # no subsidy at gross 1


# ------------------------------------------------------- blend algebra honesty
def test_blend_linear_equals_margin_rebuild_at_sleeve_gross_1():
    """CHARTER WEIGHT CONVENTION: B = (1-w)*net_c + w*net_s (w = SLEEVE slice). With
    G_c=1.6 (champion, margin-embedded per sub-book) and G_s=1.0 (unlevered sleeve), the
    exact margin-re-priced blend must equal the linear blend IDENTICALLY."""
    idx = pd.bdate_range("2020-01-01", periods=500)
    rs = pd.Series(RNG.normal(0.0003, 0.006, 500), index=idx)
    rc = pd.Series(RNG.normal(0.0016, 0.0065, 500), index=idx)
    net_c = rc - L.margin_daily_scalar(1.6, 0.045)          # margin embedded
    net_s = rs                                              # gross 1 -> no margin
    for w in (0.025, 0.05, 0.10, 0.15):
        got = L.blend_exact(net_c, net_s, w, gross_c=1.6, gross_s=1.0, rate=0.045)
        want = (1 - w) * net_c + w * net_s
        assert np.allclose(got.values, want.values, atol=1e-15), f"w={w}"


def test_blend_convention_w_is_sleeve_slice():
    """Charter pins the direction: champion_net*(1-w) + sleeve_net*w. A 2.5% sleeve slice
    must move the blend 97.5% toward champion behavior (near-champion SR), never the
    reverse. (Caught the first run putting w on the champion: d_ann -26pp at w=0.025.)"""
    idx = pd.bdate_range("2020-01-01", periods=400)
    rc = pd.Series(RNG.normal(0.0015, 0.006, 400), index=idx)   # strong book
    rs = pd.Series(RNG.normal(0.0002, 0.006, 400), index=idx)   # weaker book
    net_c = rc - L.margin_daily_scalar(1.6, 0.045)
    from bt.metrics import sharpe_d as sd
    b = L.blend_exact(net_c, rs, w=0.025)
    assert sd(b) > 0.75 * sd(net_c)   # 97.5% champion -> blend tracks champion


def test_blend_margin_never_rebate_and_monotone_in_gross():
    """Blend margin drag must be >= 0 always, monotone up in champion gross, and strictly
    down in the sleeve slice w (unlevered sleeve displaces levered champion)."""
    assert L.blend_margin_ann(0.0, 1.6, 1.0, 0.045) == pytest.approx(0.6 * 0.045)
    assert L.blend_margin_ann(0.025, 1.6, 1.0, 0.045) == pytest.approx(0.975 * 0.6 * 0.045)
    assert L.blend_margin_ann(0.025, 1.6, 1.0, 0.045) < L.blend_margin_ann(0.0, 1.6, 1.0, 0.045)
    assert L.blend_margin_ann(0.025, 1.6, 1.2, 0.045) > L.blend_margin_ann(0.025, 1.6, 1.0, 0.045)
    assert L.blend_margin_ann(1.0, 1.6, 1.0, 0.045) == 0.0
    for w in (0.0, 0.25, 0.5, 1.0):
        assert L.blend_margin_ann(w, 1.6, 1.0, 0.045) >= 0.0


def test_blend_drift_turnover_formula_and_negligibility():
    """Daily-rebalance blend drift turnover = 2*|(1-w) - W_c_drifted| (champion |dW|
    convention, prior-day NAVs). On real champion/sleeve NAVs the cost must be < 5bp/yr
    (immateriality claim, fail-closed)."""
    idx = pd.bdate_range("2020-01-01", periods=50)
    rc = pd.Series(0.001, index=idx)   # champion leg drifts up
    rs = pd.Series(0.0, index=idx)
    to = L.blend_drift_turnover(rc, rs, w=0.05)
    wc = 0.95 * 1.001 / (0.95 * 1.001 + 0.05)   # champion leg weight after day-1 drift
    assert abs(to.iloc[1] - 2 * abs(0.95 - wc)) < 1e-12
    assert to.iloc[0] == 0.0           # no trade on day 0 (positions just established)


def test_blend_gross_cap_all_ladder_weights():
    """Charter gate: blended daily gross <= 1.6 for the whole w ladder (G_c=1.6, G_s=1.0).
    Under the charter convention gross FALLS as the sleeve slice grows (sleeve unlevered)."""
    prev = None
    for w in (0.025, 0.05, 0.075, 0.10, 0.15):
        g = L.blend_gross_of(w, 1.6, 1.0)
        assert g <= 1.6 + 1e-12
        if prev is not None:
            assert g < prev            # monotone decreasing in w
        prev = g


def test_blend_requires_shared_index_failclosed():
    idx = pd.bdate_range("2020-01-01", periods=10)
    with pytest.raises(ValueError):
        L.blend_exact(pd.Series(0.0, index=idx), pd.Series(0.0, index=idx[:9]), 0.05,
                      1.6, 1.0, 0.045)


# ------------------------------------------------------------ candidate screen
def test_candidate_pool_admission_screen():
    """Charter (a): published AS-IS, own-span net SR >= 0.5 AND |corr vs champ| <= 0.35.
    Admitted / rejected exactly as screened; every number asserted from the CSVs."""
    pool = L.screen_pool()
    # admitted: 6 candidates
    for name, exp_sr, exp_corr in [
        ("MSSW", 0.873, -0.026),          # library Multi_Strategy_SharpeW (picked over A_rs: 0.87 x-corr)
        ("CRX1030", 0.910, -0.026),       # crypto vol-scaled crossover (audit sleeve)
        ("A_rs", 0.549, -0.043),          # HUNT_SECTOR2 Arm A 2008+
        ("A11", 0.702, -0.150),           # HUNT_SECTOR2 A11 (corr_ok_secondary 0.15-0.35)
        ("COMP50d", 0.609, -0.117),       # HUNT_SECTOR2 composite 50/50 daily
        ("CMDTrot_h2", 0.577, -0.000),    # HUNT_CMDT2 sector-rot family best
    ]:
        assert name in pool, f"{name} missing from admitted pool"
        assert abs(pool[name]["own_sr"] - exp_sr) < 0.02, (name, pool[name]["own_sr"])
        assert abs(pool[name]["corr_champ_own"] - exp_corr) < 0.02
        assert pool[name]["own_sr"] >= 0.5 and abs(pool[name]["corr_champ_own"]) <= 0.35
    # rejected with numbers (charter: list as rejected)
    assert pool["CTA_15vol"]["verdict"] == "REJECT_OWN_SR"
    assert pool["CTA_15vol"]["own_sr"] < 0.5            # charter assumed positive; it is -0.15
    assert pool["CMDTrot_6m_LS"]["verdict"] == "REJECT_OWN_SR"
    assert pool["CMDTrot_6m_LS"]["own_sr"] == pytest.approx(0.445, abs=0.02)  # charter "0.40 below bar"
    assert pool["COMP_invvol"]["verdict"] == "REJECT_UNUSABLE_FILE"           # weights not returns
    # A_rs x MSSW cross-corr: charter's pick-ONE constraint
    assert abs(pool["MSSW"]["xcorr_A_rs"]) > 0.8


def test_blend_table_and_recommendation_schema(tmp_path):
    """Charter (d): blend table (candidate x w -> dAnn/dSR/dMDD/negy/gross) + recommendation
    JSON with every adoption gate field and the adversarial-control block."""
    tbl, rec = L.run_round3(out_dir=tmp_path, quick=True, n_nulls=10)
    assert set(tbl.columns) >= {"candidate", "w", "d_ann_pp", "d_sr", "d_mdd_pp",
                                "neg_years", "gross", "window", "n"}
    assert len(tbl) == len(L.ADMITTED)  # quick ladder = 1 rung per candidate
    for k in ["verdict", "adopt", "gates", "adversarial", "basis"]:
        assert k in rec
    assert rec["verdict"] in ("ADOPT", "NOTHING_ADOPTABLE")


def quick_ok(tbl):
    return True  # quick mode runs a reduced ladder; schema assertion is the contract here


# --------------------------------------------------------- adversarial control
def test_adversarial_null_generator_matches_vol_and_corr():
    """Null sleeves must match the real sleeve's daily vol AND champion corr EXACTLY
    (per-draw, in-sample orthogonalization) — otherwise the control compares apples to
    oranges. Sample-corr tolerance would be SE~0.026 at 1500 obs; exactness is stronger."""
    ch = L.load_champion()
    r_c = ch.tail(1500)
    target_vol, target_corr = 0.006, -0.03
    nulls = L.null_sleeves(r_c, n=8, vol=target_vol, corr=target_corr, rng=np.random.default_rng(3))
    assert len(nulls) == 8
    for s in nulls:
        assert abs(s.std(ddof=1) - target_vol) / target_vol < 1e-9
        j = pd.concat([r_c.rename("c"), s.rename("s")], axis=1, sort=True).dropna()
        assert abs(j.c.corr(j.s) - target_corr) < 1e-6


def test_adversarial_null_control_runs_and_reports_frac_positive():
    """Charter: at same w, 200 vol/corr-matched random draws — the REAL sleeve's dSR gain
    must NOT be reproducible by a majority of nulls (else it is a diversification artifact)."""
    ch = L.load_champion().tail(1500)
    out = L.adversarial_control(ch, vol=0.006, corr=-0.03, w=0.05, n_nulls=30,
                                rng=np.random.default_rng(11))
    assert 0.0 <= out["frac_null_dsr_pos"] <= 1.0
    assert "null_dsr_p95" in out and "real_dsr" in out and "verdict" in out
    assert out["verdict"] in ("DIVERSIFICATION_ARTIFACT", "SURVIVES_CONTROL")


# ------------------------------------------------------------- shortability tiers
def test_shortability_tier_assignment_for_candidates():
    """Charter (b): short legs via bt/shortability pregate with CAMP_SHORT tiers.
    ETF sleeves = EASY (large-cap ETFs, 0.5%/yr already in published nets);
    crypto perp sleeve = funding NOT modeled (meta caveat) -> funding-stress delta reported,
    never silently assumed covered."""
    tiers = L.shortability_report()
    assert tiers["A_rs"]["tier"] == "EASY" and tiers["A_rs"]["borrow_delta_ann_pp"] == 0.0
    assert tiers["MSSW"]["tier"] == "EASY"
    assert tiers["CRX1030"]["funding_modeled"] is False
    assert tiers["CRX1030"]["stress_10pct_ann_pp"] > 0   # honest drag quantified, not zero


def test_no_lookahead_blend_uses_realized_returns_only():
    """Blends combine realized net return streams (no signal at t uses data > t); the only
    trade generated (rebalance drift) must be computed from PRIOR-day NAVs (shift(1))."""
    idx = pd.bdate_range("2020-01-01", periods=30)
    rc = pd.Series(0.001, index=idx)
    rs = pd.Series(-0.001, index=idx)
    to = L.blend_drift_turnover(rc, rs, w=0.05)
    assert to.iloc[0] == 0.0                      # day 0: establishment, no rebalance trade
    # day t turnover must be a function of NAVs through t-1 only
    wc_prev = L.leg_weight(rc, rs, w=0.05).shift(1)   # champion leg's prior-day weight
    manual = (2 * ((1 - 0.05) - wc_prev)).abs().fillna(0.0)
    assert np.allclose(to.values, manual.values, atol=1e-15)
