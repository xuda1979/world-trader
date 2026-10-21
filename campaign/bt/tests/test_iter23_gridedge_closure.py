"""ITER23 GRID-EDGE CLOSURE - the weight family's edges are invariant boundaries.

Operator objective (2026-09-18, re-sent 2026-09-19, verbatim): "keep improving. the leverage
must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%."

ITER22 re-solved the ITER20 grid under the corrected gear-1.0 pure-IS-SR objective
(argmax = the incumbent, IS-SR 4.1986) but left both grid EDGES unresolved. ITER23 extended
past them (pre-committed: campaign/agents/chief/coord/ITER23_GRIDEDGE_REFIT/
FINDINGS_PRECOMMIT.md, sealed before the reveal; driver log beside it):

    cap axis, shrink 0.70:  cap 0.29 -> Wmax 2.0044x (crossing between 0.29 and 0.30)
    shrink axis, cap 0.30:  shrink 0.60 -> Wmax 2.0108x (crossing between 0.70 and 0.60)
    -> ALL 7 extended points are Wmax-INADMISSIBLE; argmax over admissible = the INCUMBENT
       (shrink 0.70, cap 0.30), IS-SR 4.1986 reproduced exactly (ITER22 continuity).

The grid edges were therefore TRUE concentration boundaries (the Wmax 2.0x-equal invariant),
not truncation artifacts: beyond the corner IS-SR rises to 4.2234 and FS-SR to 3.7751, but
every such point violates the invariant. The frontier statement "weight axis exhausted" now
holds WITH its edges explained. No adoption; champion of record unchanged (sha16
8559fa55ee9a3417, weights d2d11c92a98683df, ann 23.6054% / SR 3.751429 / MDD -3.6130%).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402

CHAMP = ROOT / "campaign" / "results" / "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
# Re-anchor (2026-09-19, ITER43 A5r2 vt015 adoption): the ITER23 grid verdict below is a
# HISTORICAL verdict, adjudicated against the champion OF THAT ERA -- the fixture pins
# PATHS["A5r2"] to the pre-ITER43 VT=0.10 sleeve, whose incumbent point byte-matches the
# preserved prior_champion_backup pair (8559fa55ee9a3417); the live champion is pinned
# separately in test_anchor_default_build_reproduces_champion_bytes. ITER49 re-anchor
# (2026-09-19, tsmom vt015 adoption): the fixture also pins PATHS["QAxasts"] to the
# pre-ITER49 VT=0.10 tsmom sleeve for the same reason.
ERA_A5R2 = "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv"
ERA_TSMOM = "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv"
BACKUP = (ROOT / "campaign" / "agents" / "chief" / "coord" / "ITER43_A5R2_VT"
          / "prior_champion_backup")

EXTENDED = [  # (shrink_d, brwt_cap) -- the 7 pre-committed ITER23 points
    (0.70, 0.29), (0.70, 0.28), (0.70, 0.27), (0.70, 0.26),
    (0.60, 0.30), (0.50, 0.30), (0.40, 0.30),
]
INCUMBENT = (0.70, 0.30)


def _stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return dict(
        sr=float(r.mean() / r.std(ddof=1) * np.sqrt(252)),
        mdd=float((nav / nav.cummax() - 1).min()),
        neg=int((yr < 0).sum()),
    )


@pytest.fixture(scope="module")
def grid():
    """Build all 8 pre-committed points once (gear 1.0, canonical mechanics)."""
    # ERA construction (see re-anchor note at CHAMP): historical A5r2 sleeve, restored after.
    out = {}
    old = B.PATHS["A5r2"]
    old_ts = B.PATHS["QAxasts"]
    B.PATHS["A5r2"] = ERA_A5R2
    B.PATHS["QAxasts"] = ERA_TSMOM
    try:
        for sd, cap in EXTENDED + [INCUMBENT]:
            net, relw, gross, _, _ = B.build(shrink_d=sd, brwt_cap=cap, gear=1.0)
            out[(sd, cap)] = dict(
                net=net, relw=relw, gross=gross,
                wmax=float(relw.max()) * len(B.NAMES),
                cfx4=float(relw.get("CFX4", 0.0)),
                grossmax=float(gross.max()),
            )
    finally:
        B.PATHS["A5r2"] = old
        B.PATHS["QAxasts"] = old_ts
    return out


def test_anchor_default_build_reproduces_champion_bytes():
    # LIVE-champion identity (re-anchored 2026-09-19, ITER43): the default build reproduces
    # the current champion of record bytes (the grid fixture is the ERA construction).
    net, _, _, _, _ = B.build()
    committed = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([committed.rename("c"), net.rename("n")], axis=1, join="inner").dropna()
    assert len(j) == 4806
    assert float((j.c - j.n).abs().max()) < 1e-12


def test_anchor_era_incumbent_is_the_backup_champion(grid):
    """The ERA grid incumbent is byte-exactly the champion of the ITER23 era, preserved in
    the ITER43 prior_champion_backup pair (sha16 8559fa55ee9a3417).

    RE-PINNED 2026-09-28 (E1/DHHNGSP refresh landing, commit 17e5be6): the backup
    champion pair (frozen, ends 2026-08-28) now sees the E1 sleeve's 19 appended
    marks (2026-08-25..09-21) inside its window. Attribution verified: pre-08-25
    maxdev 9.996e-17 (byte-exact through 08-24); all new drift is the appended-marks
    class, maxdev 1.727e-3 at 2026-08-26. Old pin: <1e-12 (held through 2026-09-27)."""
    net = grid[INCUMBENT]["net"]
    committed = pd.read_csv(BACKUP / "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                            index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([committed.rename("c"), net.rename("n")], axis=1, join="inner").dropna()
    assert len(j) == 4806
    pre = j[j.index < "2026-08-25"]
    assert float((pre.c - pre.n).abs().max()) < 1e-12, \
        "pre-refresh history drifted — NOT the appended-marks class; re-audit"
    assert float((j.c - j.n).abs().max()) < 2.5e-3, \
        "appended-marks drift grew beyond the pinned 1.727e-3 (cap 2.5e-3); re-attribute"


def test_incumbent_is_sr_reproduces_iter22(grid):
    """Definitional continuity with ITER22: IS-SR at (0.70, 0.30) = 4.1986."""
    net = grid[INCUMBENT]["net"]
    isr = net[net.index < B.IS_END]
    assert abs(_stats(isr)["sr"] - 4.1986) < 5e-4


def test_every_extended_point_is_wmax_inadmissible(grid):
    """The one honest negative of ITER23: the 2.0x invariant forbids the whole extension."""
    for key in EXTENDED:
        wmax = grid[key]["wmax"]
        assert wmax > 2.0, (
            f"(shrink {key[0]}, cap {key[1]}) unexpectedly admissible: wmax={wmax:.4f}x")


def test_wmax_crossings_bracket_the_incumbent(grid):
    """Both edges cross IMMEDIATELY outside the incumbent: it is the last admissible point."""
    assert grid[(0.70, 0.29)]["wmax"] > 2.0 >= grid[INCUMBENT]["wmax"]
    assert grid[(0.60, 0.30)]["wmax"] > 2.0 >= grid[INCUMBENT]["wmax"]
    assert grid[INCUMBENT]["wmax"] == pytest.approx(1.9762, abs=5e-4)


def test_extension_is_blocked_only_by_wmax(grid):
    """Document WHY the points die: every one passes IS-MDD and 0-IS-neg-yrs -- the invariant
    is the ONLY binding filter. (Their IS-SR is also higher, i.e. the forbidden direction is
    genuinely tempting -- that is the ITER22 tight-cap law, now reproduced on fresh points.)"""
    for key in EXTENDED:
        isr = grid[key]["net"][grid[key]["net"].index < B.IS_END]
        st = _stats(isr)
        assert st["mdd"] >= -0.06, key
        assert st["neg"] == 0, key
        assert st["sr"] > 4.1986, key  # the corner is IS-attractive; the invariant stops it


def test_all_points_keep_champion_invariants(grid):
    """CFX4 pinned 0 and gross <= cap everywhere, inadmissible points included."""
    for key, r in grid.items():
        assert r["cfx4"] == 0.0, key
        assert r["grossmax"] <= 1.6 + 1e-9, key


def test_argmax_over_admissible_points_is_the_incumbent(grid):
    """The pre-committed selection rule: argmax IS-SR over admissible points UNION incumbent."""
    def is_sr(key):
        net = grid[key]["net"]
        return _stats(net[net.index < B.IS_END])["sr"]

    admissible = [k for k in grid if grid[k]["wmax"] <= 2.0 + 1e-12]
    assert admissible == [INCUMBENT], f"unexpected admissible set: {admissible}"
    best = max(admissible, key=lambda k: is_sr(k))
    assert best == INCUMBENT
