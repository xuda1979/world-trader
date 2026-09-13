"""CAMP_COST R6 — adoption-study pins for the RAWEW14 HOBR candidate (charter (a)).

The candidate is a PURE 14-sleeve re-solve of rawew13v2_build (relw = max(IS_SR,0)^0.55
incl. RB_hobr_crack_hyst_w63_z10_zo10), because bt/verify_champion.py weights_repro
hardcodes that exact form — a hand-capped weight file could never pass 7/7. The w<=15%
NAV charter cap must therefore hold as an OUTCOME of the re-solve; these tests pin it.

TDD: written RED first (collection failure — work_r6/rawew14_candidate.py did not exist);
GREEN after the builder landed.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6")

CAND_CSV = ROOT + "/campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv"
CAND_W = ROOT + "/campaign/results/RAWEW14_HOBR_CANDIDATE_weights.csv"
CHAMP_CSV = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
# pre-ITER15 SR^P champion of record (13-slot), which the 0-weight-HOBR 14-slot build folds
# back into byte-exactly — the honest reference for the rawew14_candidate SR^P builder.
ARCH_CHAMP = (ROOT + "/campaign/results/"
              "archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER15_minsharpe_ann37.49.csv")

if not os.path.exists(ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6/rawew14_candidate.py"):
    pytest.fail("work_r6/rawew14_candidate.py does not exist yet (RED-first contract)")
raw14 = pytest.importorskip("rawew14_candidate")


# ------------------------------------------------------------------ invariants
def test_relw_zero_recovers_committed_champion_exactly():
    """The only change vs the committed book is HOBR's entry: force its relw to 0 and the
    14-slot algebra must reproduce the champion bytes exactly (row-normalization cancels the
    extra column; scale 14*(1.6/14)==13*(1.6/13)==1.6). Re-based (ITER15): the committed
    champion now uses the correlation-aware minsharpe weight rule, so the SR^P candidate
    builder reproduces the ARCHIVED pre-ITER15 SR^P champion of record (ann 37.49%), which is
    the 13-slot SR^P book the 0-weight slot folds back into — verified byte-exact at 1.4e-16."""
    net, relw, gross, to, df = raw14.build(hobr_relw_override=0.0)
    arch = pd.read_csv(ARCH_CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([arch.rename("old"), net.rename("new")], axis=1, join="inner").dropna()
    assert len(j) == len(arch) == 4806
    assert float((j.old - j.new).abs().max()) < 1e-12


def test_costs_full_dw_64bps_and_margin():
    """Candidate charges FULL |dW| @ 6.4bps one-side (no 0.5 half-turn) + 4.5% margin on
    (1.6-1); day-1 entry uncharged."""
    net, relw, gross, to, df = raw14.build()
    port = (df.fillna(0).values * raw14.last_Wg.values).sum(axis=1)
    implied = port - net - np.maximum(1.6 - 1, 0) * 0.045 / 252  # cost stream in the net
    cost_full = to * 6.4 / 1e4
    assert float((implied - cost_full).abs().max()) < 1e-15
    assert float((implied - 0.5 * cost_full).abs().max()) > 1e-6  # half-turn decisively wrong


def test_hobr_nav_share_under_15pct_every_day():
    """Charter w<=15% NAV cap holds as an OUTCOME of the pure re-solve (not enforced)."""
    raw14.build()
    share = raw14.hobr_nav_share()
    assert share.max() <= 0.15 + 1e-12
    assert share.min() >= 0.0


def test_gross_rides_cap_exactly_never_over():
    net, relw, gross, to, df = raw14.build()
    assert gross.max() <= 1.6 + 1e-9
    assert abs(gross.mean() - 1.6) < 1e-9  # 8e: re-levered to the cap EXACTLY
    assert int((gross > 1.6 + 1e-9).sum()) == 0


def test_candidate_index_matches_committed_champion():
    net, relw, gross, to, df = raw14.build()
    old = pd.read_csv(CHAMP_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    assert net.index.equals(old.index)  # no date drift vs champion of record


def test_causality_weights_use_only_prior_nav():
    """Truncation probe: zero all sleeve returns from day t onward -> day-t weights
    unchanged (nav.shift(1) causal)."""
    _, _, _, _, dfA = raw14.build()
    WA = raw14.last_Wg.copy()
    t = len(dfA) // 2
    dfz = dfA.copy()
    dfz.iloc[t:] = 0.0
    raw14.build(frame=dfz)
    WB = raw14.last_Wg
    assert float((WA.iloc[t] - WB.iloc[t]).abs().max()) < 1e-15


def test_emitted_candidate_files():
    """The RAWEW14 candidate is a frozen, NON-ADOPTED R6 artifact (see test_audit_champ2_round6).
    Its emission and input sleeves predate RAWEW15 (which extended the live sleeve tails), so a
    fresh byte-equality against `raw14.build()` on the CURRENT sleeves is no longer achievable
    (frozen 4805 rows vs live-rebuilt 4806). The durable invariants — candidate row count,
    the 14-slot weights file matching the SR^P re-solve, and RB_hobr's presence — still hold."""
    assert os.path.exists(CAND_CSV) and os.path.exists(CAND_W)
    net = pd.read_csv(CAND_CSV, index_col=0, parse_dates=True).iloc[:, 0]
    assert len(net) == 4805
    w = pd.read_csv(CAND_W, index_col=0).iloc[:, 0]
    assert len(w) == 14 and "RB_hobr" in w.index
    _, relw, _, _, _ = raw14.build()
    assert float((w.reindex(relw.index) - relw).abs().max()) < 1e-12  # weights file == re-solve relw


def test_verify_champion_77_on_candidate_json():
    """The acceptance gate verdict, from the saved --json artifact (subprocess run logged
    in FINDINGS): ok must be true with all 7 checks ok."""
    j = ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6/verify_champion_r6_candidate.json"
    assert os.path.exists(j)
    rep = __import__("json").load(open(j))
    assert rep["ok"] is True, rep["errors"]
    assert len(rep["checks"]) == 7 and all(v["ok"] for v in rep["checks"].values())
    assert rep["inputs"]["sleeves"]["RB_hobr"].endswith("RB_hobr_crack_hyst_w63_z10_zo10.csv")
