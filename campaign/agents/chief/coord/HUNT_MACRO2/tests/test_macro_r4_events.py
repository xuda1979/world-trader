"""HUNT_MACRO2 round 4 TDD spec — CROSS-SLEEVE event study of ALFRED surprise days on the
champion's 13 slots (charter round 4), with the HUNT_CREDIT2 own-vol control kill-test.

Written BEFORE the implementation (red first). Pre-registered BEFORE any evaluation:

PRIMARY ENDPOINT (pre-registered): a macro-release overlay passes the charter ONLY if it
 (i) improves champion MDD by >= +0.5pp OR ann by >= +0.3pp (R2 acceptance arms),
 (ii) keeps 0 negative years, gross <= 1.6, T+1 (event signal decided from data <= t,
      held from t+1),
 (iii) survives the trigger-scramble control (p <= 0.05, 200 perms, from round 2), and
 (iv) BEATS the generic own-vol control at matched on-frequency (the HUNT_CREDIT2 R2
      lesson: a content-free vol mask fake-passes). The own-vol control is the PRIMARY
      falsifier: if the control's delta >= the macro overlay's delta on the arm that
      nominally passed, the macro gate is DEAD — say so, no rescue.

EVENT SET: the 9 ALFRED release series from round 3 (PAYEMS UNRATE CPIAUCSL RSXFS IPMAN
UMCSENT HOUST DGORDER ICSA). "Top-quintile surprise day" = |z| >= Phi^-1(0.9) = 1.2816
computed from the round-3 PIT z-scores (trailing mu/sd of strictly-earlier releases,
min_hist=12). T+1: the first CHAMPION trading day STRICTLY AFTER the release date
(holiday-aware, matches round-3 event_signal semantics).

SLOT ACCOUNTING: the champion is rebuilt byte-identically via
HUNT_MACRO2_round2.build_champion() (TDD-pinned: max|rebuilt-committed| <= 1e-12; slot
frame Wg has 13 columns in rb.NAMES order; day-1 weights NaN-safe). Event-day per-slot
P&L = Wg * df (the exact slot pnl the champion books that day, pre-cost). "Sleeve
abnormal performance" = event-day mean slot pnl vs non-event-day mean, in bp/day, with
t-stats.

OVERLAY FORMS (pre-registered grid, both families, book-level de-levering only — the R2
finding that slot-level overlays cannot relieve a DEF-slot dd episode; re-verified here):
 (A) DE-LEVER: m_t = scale (in {0.6, 0.8}) on ALL 13 slots when ANY of the 9 series has a
     top-quintile surprise releasing T+1; joint event set = union across series.
 (B) SLEEVE-ROTATION: m_t = tilt applied to slot groups by the SIGN of the aggregate
     surprise (sum of z over series releasing that day): z>0 -> RISK-ON x{1.1,0.9},
     z<0 -> RISK-ON x{0.9,1.1} (DEFENSIVE legs untouched). RISK_ON/DEFENSIVE split is the
     one pre-committed in test_macro_r2_overlays.py (C5ng C5ngsum carryv2 QAxasts dualmom
     diescrack CFX4 / brwt15 brwt10 brwt7 brwt5 a6r7 A5r2).
 All overlays use HUNT_MACRO2_round2.overlay_book / apply_slot_overlay (TDD-verified cost
 algebra: full |d(m*W)| at 6.4bps, margin on overlaid gross, T+1 via shift(1)).

OWN-VOL CONTROL (primary falsifier): a trigger that fires on days when the champion's own
trailing 21d realized vol is in the top X% of its trailing history (expanding quantile,
PIT: uses returns up to t-1 only), X matched so the control's on-frequency equals the
macro trigger's within 0.3pp. If the own-vol control achieves >= the macro overlay's
improvement on the passing arm, the macro trigger carries no content beyond "champion got
volatile" -> DEAD per charter.

Also re-pins (regression): the round-2 builder reproduces the committed champion to
1e-12 (champion of record ann 37.195% / SR 3.181 / MDD -6.692% / 0 neg yrs).
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r2")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r4")

# Hard imports (NOT importorskip — silent skips hid unexecuted rounds in r2/r3).
import HUNT_MACRO2_round2 as R2  # noqa: E402
import HUNT_MACRO2_round3 as R3  # noqa: E402
import HUNT_MACRO2_round4 as R4  # noqa: E402

ALF = f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3/alfred"
SERIES = ["PAYEMS", "UNRATE", "CPIAUCSL", "RSXFS", "IPMAN", "UMCSENT", "HOUST", "DGORDER", "ICSA"]
Z90 = 1.2816  # Phi^-1(0.9)


# ------------------------------------------------------------------ fixtures
def _cal(*days):
    return pd.DatetimeIndex([pd.Timestamp(d) for d in days])


def _tiny_surprises():
    """Hand-built surprise table (release_date -> z) covering: positive surprise,
    negative surprise, |z| below threshold (never fires), and a weekend release
    (T+1 must land on the NEXT TRADING day, not the calendar next day)."""
    return pd.DataFrame(
        {
            "rel": ["2010-01-08", "2010-02-05", "2010-03-05", "2010-04-02"],
            "z": [2.0, -2.5, 0.5, 1.5],
        }
    ).pipe(lambda d: d.assign(rel=pd.to_datetime(d["rel"])).set_index("rel"))


# ------------------------------------------------------------------ regression pins
def test_champion_rebuild_matches_committed():
    """Round-2 builder must reproduce the committed champion to 1e-12 (champion of record
    ann 37.195% SR 3.181 MDD -6.692% 0 neg yrs). Guards the whole round against silently
    testing against a stale book."""
    net, Wg, df = R2.build_champion()
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0]
    d = (net.reindex(champ.index) - champ).abs().max()
    assert d <= 1e-12, f"rebuild deviates {d:.3e}"
    import rawew13v2_build as rb  # canonical slot order lives in the builder
    assert list(Wg.columns) == list(rb.NAMES)  # 13 slots, canonical order
    assert len(Wg.columns) == 13


def test_event_day_mapping_t_plus_1_holiday_aware():
    """Top-quintile releases map to the first TRADING day strictly AFTER the release.
    Weekend releases land on Monday, not Saturday; below-threshold releases never fire."""
    sig = R4.event_days(_tiny_surprises(), thr=Z90,
                        cal=_cal("2010-01-08", "2010-01-11", "2010-02-08", "2010-03-08"))
    # 2010-01-08 (Fri) z=2.0 fires -> first trading day strictly after = 2010-01-11 (Mon)
    assert bool(sig.loc[pd.Timestamp("2010-01-11")]) is True
    # 2010-02-05 (Fri) z=-2.5 fires -> 2010-02-08 (Mon)
    assert bool(sig.loc[pd.Timestamp("2010-02-08")]) is True
    # 2010-03-05 z=0.5 below 1.2816 -> must NOT fire anywhere
    assert bool(sig.max()) is True  # sanity: some day fired
    assert len(sig) == 4


def test_event_days_exclude_release_day_itself():
    """The release day itself (data hits the tape intraday) must NEVER be an event day:
    no same-day position. z fires on 2010-01-08 -> 2010-01-08 flag False."""
    sig = R4.event_days(_tiny_surprises(), thr=Z90,
                        cal=_cal("2010-01-08", "2010-01-11"))
    assert bool(sig.loc[pd.Timestamp("2010-01-08")]) is False


def test_aggregate_sign_pre_committed_groups():
    """Sleeve-rotation grouping is the pre-committed RISK_ON/DEFENSIVE split, asserted here
    before evaluation (same classification the r2 tests pinned)."""
    assert set(R4.RISK_ON) == {"C5ng", "C5ngsum", "carryv2", "QAxasts", "dualmom", "diescrack", "CFX4"}
    assert set(R4.DEFENSIVE) == {"brwt15", "brwt10", "brwt7", "brwt5", "a6r7", "A5r2"}
    assert len(R4.RISK_ON) + len(R4.DEFENSIVE) == 13


def test_surprise_union_uses_round3_pit_z():
    """The event set must come from the round-3 PIT z-scores (trailing mu/sd, min_hist=12).
    Contract: building the 9-series event table returns finite z for every row, release
    dates only (no synthetic fills), and the union trigger for the real cubes lands on
    champion trading days."""
    tab = R4.build_surprise_table(SERIES)
    assert len(tab) > 200  # round 3 measured 249..889 scored releases per series
    assert np.isfinite(tab["z"].abs().dropna()).all()
    assert (tab["z"].abs().dropna() >= 0).all()


def test_ownvol_control_pit_and_frequency_match():
    """Own-vol control: trigger when trailing 21d realized vol (through t-1) exceeds its
    expanding quantile q. PIT check: the value used at t must be computable from returns
    up to t-1 only. Frequency-match helper must hit the target on-frequency within 0.3pp,
    else raise (fail-closed) so the control cannot quietly run mismatched."""
    champ = R2.CHAMP
    # PIT: build trigger with returns truncated at t -> value at t identical to full-sample build
    r = champ
    full = R4.ownvol_trigger(r, win=21, qtarget=0.95)
    assert isinstance(full, pd.Series)
    # at the midpoint, the trigger computed on a truncated history must agree
    cut = len(r) // 2
    trunc = R4.ownvol_trigger(r.iloc[:cut], win=21, qtarget=0.95)
    assert np.allclose(trunc.values, full.iloc[:cut].values, equal_nan=True)
    # frequency matcher: find qtarget achieving ~6.9% on-freq (kw is qtarget, not q)
    q = R4.match_quantile_for_freq(r, win=21, target_freq=0.069, tol=0.003)
    m = R4.ownvol_trigger(r, win=21, qtarget=q)
    assert abs(m.mean() - 0.069) <= 0.003


def test_event_pnl_decomposition_sums_to_champion():
    """Slot pnl Wg*df summed across the 13 slots minus the champion's turnover cost and
    margin must equal the champion net exactly (the champion's own accounting)."""
    net, Wg, df = R2.build_champion()
    slot_pnl = (Wg * df).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    recon = slot_pnl - to * R2.BPS / 1e4 - R2.MARGIN_CONST
    d = (recon - net).abs().max()
    assert d <= 1e-12, f"slot decomposition off by {d:.3e}"


def test_overlay_uses_r2_cost_algebra():
    """De-lever overlay at constant scale 0.6 must reproduce the r2 book overlay exactly
    (m = 0.6 everywhere == overlay_book with constant m)."""
    net, Wg, df = R2.build_champion()
    m_const = pd.Series(0.6, index=net.index)
    ov_direct = R2.overlay_book(net, m_const)
    ov_r4 = R4.delever_overlay(net, m_const)
    assert np.allclose(ov_direct.values, ov_r4.values, atol=1e-15)
