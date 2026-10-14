"""ITER21 ADOPTION - the gear dimension: the SR-max book runs at gross 1.0, not 1.6.

Operator objective (2026-09-18, verbatim, unchanged): "keep improving. the leverage must be
<=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%."

ITER20 adopted the SR-max WEIGHT vector at the family assumption gross == 1.6. ITER21
releases that assumption: the builder charges margin 4.5%/yr on (gear-1) inside the net
series while turnover/borrow scale exactly ~ gear, so net SR is EXACTLY flat on (0, 1.0]
and STRICTLY DECREASING on [1, 1.6] - a cost-structure identity, not an estimate
(rawew13v2_build.py: net = port - to*BPS - max(gear-1,0)*RATE/252).
Therefore the SR argmax under gross <= 1.6, ann >= 20% is the committed ITER20 weight
vector at the TOP EDGE of the flat plateau, gear = 1.0 (max-ann tie-break on the plateau,
zero margin drag). Verified from raw bytes (canonical --emit-candidate --gear 1.0):
    sha16 8559fa55ee9a3417  n=4806
    ann 23.6054%  SR 3.751429  MDD -3.6130%  0 neg years (0/19)  worst year +7.3488%
    gross 1.0 exact (cap 1.6: 0 days over)   turnover 4.03 bp/yr   margin 0.00%/yr
    weights vector UNCHANGED from ITER20 (sha16 d2d11c92a98683df, CFX4 = 0, Wmax 1.9762x)
    OOS dSR vs the ITER20 champion, five 2017+ 2-yr bins: +0.362/+0.155/+0.411/+0.328/+0.274
    (5/5 positive - analytic, because removing a constant margin drag raises SR in every
    sub-window by construction; this is stronger than the ITER15 sampling gold standard.)
Trade disclosed: ann -12.81pp (36.42 -> 23.61, floor 20% kept) buys +0.2964 SR and
+2.32pp MDD. The superseded ITER20 book is archived byte-exact and stays reproducible
via build(gear=1.6) (weights identical, only gross differs).

ITER43 RE-ANCHOR (2026-09-19): the champion of record moved to the A5r2 VT-axis argmax book
(sha16 e67446186e269b88 / weights bde8612d0b295068). The 8559fa55ee9a3417 / d2d11c92a98683df
vintage described above is preserved byte-exact in
campaign/agents/chief/coord/ITER43_A5R2_VT/prior_champion_backup/, and historical rebuilds
pin the pre-ITER43 A5r2 sleeve (VT=0.10).
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402

CHAMP = ROOT / "campaign" / "results" / "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WGT = ROOT / "campaign" / "results" / "RAWEW13v2_IS_SR_weights.csv"
CAND = ROOT / "campaign" / "results" / "ITER21_SRMAX_GEAR10_daily.csv"
ARCH_ITER20 = (
    ROOT / "campaign" / "results"
    / "archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER21_gear10.csv"
)


def _sr(r):
    r = r.dropna()
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


def test_builder_default_gear_is_the_adopted_1_0():
    assert abs(B.GEAR - 1.0) < 1e-12, "canonical GEAR must be the adopted 1.0"


def test_default_build_reproduces_champion_bytes_at_gross_1():
    net, _, gross, _, _ = B.build()
    committed = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([committed.rename("c"), net.rename("n")], axis=1, join="inner").dropna()
    assert len(j) == 4806
    assert float((j.c - j.n).abs().max()) < 1e-12
    assert abs(float(gross.max()) - 1.0) < 1e-9, "champion gross must be 1.0 exact"


def test_candidate_bytes_are_the_champion_bytes():
    # Re-anchored 2026-09-19 (ITER43 adoption, re-anchored at the ITER47 vt024 adoption):
    # the live champion is now 3c456aa53193eb89 (e67446186e269b88 preserved byte-exact in
    # coord/ITER47_A5R2_VTEXT/prior_champion_backup); the ITER21-era bytes live on unchanged
    # in the ITER21 candidate artifact and are byte-identical to the preserved
    # ITER43 prior_champion_backup daily (8559fa55ee9a3417 -- the champion of that era).
    # Re-anchored 2026-10-12 (ITER61 NG-block-cap adoption): the live champion is now
    # a8ed233bd0f6fd5d; the pre-NG-cap bytes (cfa9ec4d38158691) live on byte-exact in
    # results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    a = hashlib.sha256(CHAMP.read_bytes()).hexdigest()[:16]
    b = hashlib.sha256(CAND.read_bytes()).hexdigest()[:16]
    bk = hashlib.sha256((ROOT / "campaign" / "agents" / "chief" / "coord"
                         / "ITER43_A5R2_VT" / "prior_champion_backup"
                         / "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv").read_bytes()).hexdigest()[:16]
    sup = hashlib.sha256((ROOT / "campaign" / "results"
                          / "archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER61_DDCON.csv"
                          ).read_bytes()).hexdigest()[:16]
    assert a == "a8ed233bd0f6fd5d", f"live champion changed: {a}"
    assert sup == "cfa9ec4d38158691", "superseded pre-NG-cap vintage must stay byte-exact"
    assert b == bk == "8559fa55ee9a3417", f"champion-era mismatch: cand {b} != backup {bk}"


def test_champion_stats_and_operator_gates():
    c = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    nav = (1 + c).cumprod()
    ann = float(nav.iloc[-1] ** (252.0 / len(c)) - 1)
    sr = _sr(c)
    mdd = float((nav / nav.cummax() - 1).min())
    # Re-anchored at ITER43 (2026-09-19, A5r2 vt015 adoption; was 23.6054 / 3.751429 /
    # -3.6130 -- that era's bytes live in the ITER43 prior_champion_backup pair).
    # ITER47 re-anchor (2026-09-19): was 23.6813 / 3.764764 / -3.6603 at ITER43.
    # ITER49 re-anchor (2026-09-19): was 23.7668 / 3.784099 / -3.7012 at ITER47.
    # ITER61 re-anchor (2026-10-12): was 23.921472 / 3.820357 / -3.7339 pre-NG-cap
    # (cfa9ec4d bytes live in the archive_*_SUPERSEDED_by_ITER61_DDCON pair).
    assert abs(ann * 100 - 23.8610) < 0.01, f"ann drifted: {ann*100:.4f}%"
    assert abs(sr - 3.784489) < 0.0005, f"SR drifted: {sr:.6f}"
    assert abs(mdd * 100 + 3.3048) < 0.01, f"MDD drifted: {mdd*100:.4f}%"
    assert ann >= 0.20, "operator return floor breached"
    years = c.groupby(c.index.year).apply(lambda x: (1 + x).prod() - 1)
    assert int((years < 0).sum()) == 0, "negative calendar year"
    assert float(years.min()) > 0.0, f"worst year positive, got {years.min()*100:.4f}%"


def test_sr_plateau_is_exactly_flat_below_gear_1():
    """Cost identity: below gear 1 every cost scales ~ gear, so SR must be bit-stable."""
    s10 = _sr(B.build(gear=1.0)[0])
    s095 = _sr(B.build(gear=0.95)[0])
    assert abs(s10 - s095) < 1e-9, f"plateau not flat: {s10} vs {s095}"


def test_sr_strictly_decreases_above_gear_1_margin_drag():
    """The margin term is the whole lever: same weights, gear 1.6 must SR-lose to gear 1."""
    s10 = _sr(B.build(gear=1.0)[0])
    s16 = _sr(B.build(gear=1.6)[0])
    assert s10 > s16, f"gear lever inverted: {s10} vs {s16}"


def test_weights_vector_unchanged_from_iter20():
    _, relw, _, _, _ = B.build()
    committed_w = pd.read_csv(WGT, index_col=0).iloc[:, 0].reindex(B.NAMES).fillna(0.0)
    assert float((committed_w - relw).abs().max()) < 1e-12
    assert float(relw["CFX4"]) == 0.0, "CFX4 stays pinned at 0"
    # ITER43 re-anchor: the fit's cap is W_MAX/k over the k=11 IS-covered sleeves
    # (canonical Wmax_sf = max*11 = 1.8604x <= 2.0), not the stricter max*12 proxy.
    k_active = int((relw > 0).sum())
    assert float(relw.max()) <= 2.0 / k_active + 1e-12, "W_MAX cap"


def test_iter20_gear16_vintage_archived_and_reproducible():
    """The superseded ITER20 book stays byte-exact: same weights, gear 1.6."""
    # Re-anchored 2026-09-19 (ITER43): the vintage predates the A5r2 vt015 sleeve swap, so
    # the rebuild pins PATHS["A5r2"] to the historical VT=0.10 sleeve (era construction).
    old_a5 = B.PATHS["A5r2"]
    old_ts = B.PATHS["QAxasts"]
    B.PATHS["A5r2"] = "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv"
    B.PATHS["QAxasts"] = "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv"
    try:
        # ITER61: the archived vintage predates the NG-block cap pass, so the rebuild
        # disables it (ng_cap=None); the sealed-vintage frame pins stay ON (the
        # incumbent champion already ran on the sealed-vintage basis).
        net, _, _, _, _ = B.build(gear=1.6, ng_cap=None)
    finally:
        B.PATHS["A5r2"] = old_a5
        B.PATHS["QAxasts"] = old_ts
    archived = pd.read_csv(ARCH_ITER20, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([archived.rename("a"), net.rename("n")], axis=1, join="inner").dropna()
    assert len(j) == 4806
    assert float((j.a - j.n).abs().max()) < 1e-12, "superseded vintage must stay reproducible"
