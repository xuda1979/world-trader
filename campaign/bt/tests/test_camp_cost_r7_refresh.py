"""CAMP_COST R7 — refresh-adoption pins for the RAWEW15 candidate (charter (a)).

The candidate is the 13-sleeve committed book with the 4 R6-staged refreshed sleeves
(brwt10/7/5 -> 2026-08-28, diescrack -> 2026-08-24) taken through a PURE re-solve
(rawew13v2_build algebra, relw = max(IS_SR,0)^0.55 on the UNCHANGED IS window). The
refresh appends only post-2026-08-10 tail rows, so: rows <= 2026-08-10 must equal the
committed champion bytes (no history relabel), the IS re-solve weights must equal the
committed weights (tail is post-IS), and every cost/gross/causality invariant of the
champion algebra must hold on the candidate.

TDD: written RED first (collection failure — work_r7/rawew15_refresh_candidate.py does
not exist yet); GREEN after the builder lands.
"""
import os
import sys

import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r7")

CAND_CSV = ROOT + "/campaign/results/RAWEW15_REFRESH_CANDIDATE_daily.csv"
CAND_W = ROOT + "/campaign/results/RAWEW15_REFRESH_CANDIDATE_weights.csv"
CHAMP_CSV = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
W_CSV = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
# ITER15 (2026-09-11): the RAWEW15 candidate was ADOPTED as the champion of record
# (2026-09-09) and then superseded by the correlation-aware weight rule. It is now
# byte-identical to the ARCHIVED pre-ITER15 champion (verified: maxdev 0.000e+00 on both
# the daily series and the weights), so the candidate-vs-*current*-champion comparisons
# below are re-pointed at that archived generation — which is what this candidate IS.
ARCH_CSV = (ROOT + "/campaign/results/"
            "archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_"
            "SUPERSEDED_by_ITER15_minsharpe_ann37.49.csv")
ARCH_W = (ROOT + "/campaign/results/"
          "archive_RAWEW13v2_IS_SR_weights_SUPERSEDED_by_ITER15_minsharpe.csv")

if not os.path.exists(
    ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r7/rawew15_refresh_candidate.py"
):
    pytest.fail("work_r7/rawew15_refresh_candidate.py does not exist yet (RED-first contract)")
raw15 = pytest.importorskip("rawew15_refresh_candidate")


# ------------------------------------------------------------------ invariants
def test_refresh_prefix_identity_no_history_relabel():
    """Rows on/before 2026-08-10 (last committed end of any refreshed sleeve) must equal
    the committed champion bytes exactly — the refresh adds P&L only AFTER the committed
    sleeve ends, never relabels history."""
    net, relw, gross, to, df = raw15.build()
    old = pd.read_csv(ARCH_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    pre = net[net.index <= "2026-08-10"]
    j = pd.concat([old.rename("old"), pre.rename("new")], axis=1, join="inner").dropna()
    assert len(j) == len(pre)  # candidate covers every archived row up to the cut
    assert float((j.old - j.new).abs().max()) < 1e-12


def test_relw_identical_to_committed_weights():
    """The refreshed tails are all post-IS (2017+), so the IS re-solve weights must equal
    the committed weights to float noise."""
    net, relw, gross, to, df = raw15.build()
    oldw = pd.read_csv(ARCH_W, index_col=0).iloc[:, 0]
    assert float((relw.sort_index() - oldw.sort_index()).abs().max()) < 1e-9


def test_costs_full_dw_64bps_and_margin():
    """Candidate charges FULL |dW| @ 6.4bps one-side (no 0.5 half-turn) + 4.5%/yr margin
    on (1.6-1); day-1 entry uncharged."""
    net, relw, gross, to, df = raw15.build()
    port = (df.fillna(0).values * raw15.last_Wg.values).sum(axis=1)
    implied = pd.Series(port, index=df.index) - net - 0.6 * 0.045 / 252  # embedded cost stream
    cost_full = to * 6.4 / 1e4
    assert float((implied - cost_full).abs().max()) < 1e-15
    assert float((implied - 0.5 * cost_full).abs().max()) > 1e-6  # half-turn decisively wrong


def test_gross_rides_cap_exactly_never_over():
    net, relw, gross, to, df = raw15.build()
    assert gross.max() <= 1.6 + 1e-9
    assert abs(gross.mean() - 1.6) < 1e-9  # 8e: constructed AT the cap exactly
    assert int((gross > 1.6 + 1e-9).sum()) == 0


def test_candidate_covers_the_adopted_generation():
    """The refresh candidate was ADOPTED (2026-09-09), so it no longer EXTENDS anything —
    it IS the pre-ITER15 champion generation. Pin that coverage instead of the retired
    'candidate extends champion' premise."""
    net, relw, gross, to, df = raw15.build()
    old = pd.read_csv(ARCH_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    assert net.index.is_unique and net.index.is_monotonic_increasing
    assert net.index.equals(old.index), "candidate must cover the adopted generation exactly"
    assert (net.index > pd.Timestamp("2026-08-10")).any(), "refreshed tail rows must be present"


def test_causality_weights_use_only_prior_nav():
    """Truncation probe: zero all sleeve returns from day t onward -> day-t weights
    unchanged (nav.shift(1) causal)."""
    raw15.build()
    dfA = raw15.last_df
    WA = raw15.last_Wg.copy()
    t = len(dfA) // 2
    dfB = dfA.copy()
    dfB.iloc[t:] = 0.0
    raw15.build(frame=dfB)
    WB = raw15.last_Wg
    dev = float((WA.iloc[t] - WB.iloc[t]).abs().max())
    assert dev < 1e-15


def test_emitted_bytes_deterministic():
    """--emit twice produces byte-identical files (both charter-named results/ files),
    and the emitted index is the champion index + the refresh tail (no gaps)."""
    import hashlib
    def sha(p):
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    raw15.main_emit()
    s1 = (sha(CAND_CSV), sha(CAND_W))
    raw15.main_emit()
    s2 = (sha(CAND_CSV), sha(CAND_W))
    assert s1 == s2
    net, relw, gross, to, df = raw15.build()
    emitted = pd.read_csv(CAND_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    assert len(emitted) == len(net)
    assert emitted.index.equals(net.index)


def test_emitted_weights_rows_match_13_sleeves():
    w = pd.read_csv(CAND_W, index_col=0)
    assert len(w) == 13
    assert (w.iloc[:, 0] >= 0).all()
