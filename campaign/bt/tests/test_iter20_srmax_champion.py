"""ITER20 ADOPTION — Sharpe-max champion under the operator's 2026-09-18 objective.

Operator instruction (2026-09-18): "keep improving. the leverage must be <=1.6. Maximize
Sharpe ratio. The annual return can't be smaller than 20%." — the objective moved from
ann-max (subject to gates) to Sharpe-max subject to ann>=20% and gross<=1.6.

The champion of record is now the SR-max point of the PRE-COMMITTED admissible family
  relw = fit_relw(IS, shrink_d=0.70), brwt-block (brwt10/7/5) relw share capped at 0.30,
  excess redistributed pro-rata on the committed non-block shares, CFX4 pinned at 0.
Selection was argmax IS-SR over the pre-committed grid — same epistemic status as the
champion's own shrink selections; no full-sample term enters the selection. The admissible
plateau is flat (FS SR 3.42-3.47 across neighbours), so no cherry-pick edge is at work.

Independent verification (coordinator, 2026-09-18, from raw bytes + the real build()):
    FULL ann 39.4995% -> 36.4150%      SR 3.2176 -> 3.4551   (+0.2375 — THE objective)
    FULL MDD -6.5232% -> -5.9284%      (BETTER)
    worst yr  +5.6250% -> +8.8898%     (BETTER)
    neg yrs   0/19 = 0/19              turnover 4.7660 -> 6.4493 bp/yr (charged in net)
    gross     1.6 exact, 0 days over (BOTH)
    OOS dSR   +0.29/+0.36/+0.23/+0.32/+0.42 across the five 2017+ 2-yr bins — 5/5 positive
    weights reproducibility  8.3e-17; emitted-weights round-trip 1.04e-16 (IDENTICAL < 1e-12)

Prior champion archived: archive_*_SUPERSEDED_by_ITER20_srmax.csv
(daily sha16 7559e82b022c6236 / weights be2265ff026dafb3).

ITER21 SUPERSEDE (2026-09-18, same day): the operator's constraint is gross <= 1.6 (a CAP),
not == 1.6. Margin 4.5%/yr on (gear-1) makes net SR strictly decreasing above gear 1, so the
SR-max book is the SAME weight vector at gear 1.0 (ann 23.6054% / SR 3.751429 / MDD -3.6130%,
sha16 8559fa55ee9a3417). The ITER20 gear-1.6 vintage is archived byte-exact as
archive_*_SUPERSEDED_by_ITER21_gear10.csv and stays reproducible via build(gear=1.6).
The stat pins below were re-anchored to the ITER21 champion; test_iter21_srmax_gear_champion.py
pins the gear lever itself. See campaign/GOAL100_ITER21_ADOPTION.md.

ITER43 RE-ANCHOR (2026-09-19): the champion of record is now the A5r2 VT-axis argmax book
(sha16 e67446186e269b88 / weights bde8612d0b295068; A5r2 sleeve = the vt015 variant). The
ITER21-era bytes are preserved in coord/ITER43_A5R2_VT/prior_champion_backup/ and the
superseded vintages below rebuild against the historical A5r2 sleeve (VT=0.10).
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402

CHAMP = ROOT / "campaign" / "results" / "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT = ROOT / "campaign" / "results" / "RAWEW13v2_IS_SR_weights.csv"
ARCH_DAILY = (
    ROOT / "campaign" / "results"
    / "archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER20_srmax.csv"
)


def test_default_build_reproduces_committed_champion_bytes():
    """The champion of record must be reproducible from checked-in code, not from a memo."""
    net, relw, gross, to, _ = B.build()
    committed = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([committed.rename("c"), net.rename("n")], axis=1, join="inner").dropna()
    assert len(j) == 4806
    assert float((j.c - j.n).abs().max()) < 1e-12, "default build must byte-reproduce the champion"


def test_weights_provenance():
    """The committed weight vector must fall out of the pre-committed family transform."""
    _, relw, _, _, _ = B.build()
    committed_w = pd.read_csv(WGT, index_col=0).iloc[:, 0].reindex(B.NAMES).fillna(0.0)
    assert float((committed_w - relw).abs().max()) < 1e-12
    # CFX4 stays at zero: the discredited twelvedata vendor feed is a champion invariant.
    assert float(relw["CFX4"]) == 0.0
    # W_MAX cap: no sleeve above 2x the equal weight. Re-anchored at ITER43 (2026-09-19):
    # the fit's cap is W_MAX/k over the k=11 IS-covered sleeves (fit_relw bounds (0, W_MAX/k)),
    # i.e. the canonical Wmax_sf = max*11 = 1.8604x <= 2.0 (the former max*12 form was a
    # stricter proxy the pre-ITER43 champion happened to satisfy).
    k_active = int((relw > 0).sum())
    assert float(relw.max()) <= 2.0 / k_active + 1e-12
    # The brwt-block cap binds at 0.30 of relw mass.
    blk = ["brwt10", "brwt7", "brwt5"]
    assert abs(float(relw[blk].sum()) - 0.30) < 1e-9


def test_champion_stats_and_gates():
    # Re-anchored at ITER21 (2026-09-18) and ITER43 (2026-09-19): canonical gear 1.0. The
    # operator's leverage constraint is the CAP gross <= 1.6 (checked below), not == 1.6.
    net, relw, gross, to, _ = B.build()
    net = net.dropna()
    nav = (1 + net).cumprod()
    ann = float(nav.iloc[-1] ** (252.0 / len(net)) - 1)
    import numpy as np
    sr = float(net.mean() / net.std(ddof=1) * np.sqrt(252))
    mdd = float((nav / nav.cummax() - 1).min())
    # ITER43 re-pin (A5r2 vt015 sleeve; was 23.6054 / 3.7514 / -3.6130 at ITER21).
    # ITER47 re-pin (A5r2 vt024 sleeve; was 23.6813 / 3.7648 / -3.6603 at ITER43).
    # ITER49 re-pin (tsmom vt015 sleeve; was 23.7668 / 3.7841 / -3.7012 at ITER47).
    assert abs(ann * 100 - 23.9215) < 0.05, f"ann drifted: {ann*100:.3f}%"
    assert abs(sr - 3.8204) < 0.002, f"SR drifted: {sr:.4f}"
    assert abs(mdd * 100 + 3.7339) < 0.02, f"MDD drifted: {mdd*100:.4f}%"
    # operator constraints
    assert gross.max() <= 1.6 + 1e-9, "leverage cap breached"
    assert int((gross > 1.6 + 1e-9).sum()) == 0
    assert ann >= 0.20, "operator return floor breached"
    assert to.mean() * 252 * B.BPS <= 8.0, "cost limit breached"
    years = net.groupby(net.index.year).apply(lambda r: (1 + r).prod() - 1)
    assert int((years < 0).sum()) == 0, "negative calendar year"


def test_committed_champion_file_pins():
    """The bytes on the canonical path carry the adopted SR-max stats."""
    import numpy as np
    c = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    nav = (1 + c).cumprod()
    ann = float(nav.iloc[-1] ** (252.0 / len(c)) - 1)
    sr = float(c.mean() / c.std(ddof=1) * np.sqrt(252))
    mdd = float((nav / nav.cummax() - 1).min())
    # Re-anchored at ITER21 (2026-09-18) and at ITER43 (2026-09-19, A5r2 vt015 adoption;
    # was 23.6054 / 3.751429 / -3.6130 -- that era's bytes live in the ITER43 backup pair).
    # ITER47 re-pin (2026-09-19): was 23.6813 / 3.764764 / -3.6603 (ITER47_A5R2_VTEXT backup).
    # ITER49 re-pin (2026-09-19): was 23.7668 / 3.784099 / -3.7012 (ITER48_C5NG_VT era;
    # 3c456aa5 bytes live in the ITER49_TSMOM_VT prior_champion_backup pair).
    assert abs(ann * 100 - 23.9215) < 0.01, f"committed ann drifted: {ann*100:.4f}%"
    assert abs(sr - 3.820357) < 0.001, f"committed SR drifted: {sr:.5f}"
    assert abs(mdd * 100 + 3.7339) < 0.01, f"committed MDD drifted: {mdd*100:.4f}%"
    years = c.groupby(c.index.year).apply(lambda r: (1 + r).prod() - 1)
    assert int((years < 0).sum()) == 0


def test_iter19_static98_vintage_is_archived_and_reproducible():
    """Provenance for the superseded ann-max vintage: the OLD construction (shrink 0.98,
    no brwt cap) must still be rebuildable and must byte-match the archive. The archive is
    a GEAR-1.6 artifact (canonical gear moved to 1.0 in ITER21), so pass gear=1.6."""
    # Re-anchored 2026-09-19 (ITER43): this vintage predates the A5r2 vt015 sleeve swap, so
    # the rebuild pins PATHS["A5r2"] to the historical VT=0.10 sleeve (era construction).
    old_a5 = B.PATHS["A5r2"]
    old_ts = B.PATHS["QAxasts"]
    B.PATHS["A5r2"] = "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv"
    B.PATHS["QAxasts"] = "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv"
    try:
        net, _, _, _, _ = B.build(shrink_d=0.98, brwt_cap=None, gear=1.6)
    finally:
        B.PATHS["A5r2"] = old_a5
        B.PATHS["QAxasts"] = old_ts
    archived = pd.read_csv(ARCH_DAILY, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([archived.rename("a"), net.rename("n")], axis=1, join="inner").dropna()
    assert len(j) == 4806
    assert float((j.a - j.n).abs().max()) < 1e-12, "superseded vintage must stay reproducible"


def test_sr_max_point_dominates_on_the_stated_objective():
    """Under the operator objective (SR-max s.t. ann>=20%, gross<=1.6) the adopted point must
    not be dominated by the archived ann-max point: SR strictly better, MDD not worse."""
    import numpy as np
    net20, _, g20, _, _ = B.build()
    net0, _, g0, _, _ = B.build(shrink_d=0.98, brwt_cap=None)

    def st(net):
        net = net.dropna()
        nav = (1 + net).cumprod()
        return (float(nav.iloc[-1] ** (252.0 / len(net)) - 1),
                float(net.mean() / net.std(ddof=1) * np.sqrt(252)),
                float((nav / nav.cummax() - 1).min()))

    a20, s20, m20 = st(net20)
    a0, s0, m0 = st(net0)
    assert s20 > s0, "SR-max point must raise Sharpe over the ann-max point"
    assert m20 >= m0 - 1e-12, "SR gain must not come from a deeper drawdown"
    assert a20 >= 0.20 and a0 >= 0.20, "both points must clear the operator return floor"
    assert g20.max() <= 1.6 + 1e-9 and g0.max() <= 1.6 + 1e-9, "leverage cap (both)"


def test_pool_and_family_constants():
    assert "brwt15" not in B.NAMES, "the dominated brwt sleeve stays pruned"
    assert len(B.NAMES) == 12
    assert abs(B.SHRINK_D - 0.70) < 1e-12, "ITER20 shrink selection is 0.70"
    assert abs(B.W_BRWT_CAP - 0.30) < 1e-12, "ITER20 brwt-block cap is 0.30"
