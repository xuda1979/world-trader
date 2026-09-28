"""ITER19 — the committed brwt15 costs what the champion thinks it costs.

Found 2026-09-13 while auditing the pool for a cost-convention gap. The pool takes CAMP_COST
costfix variants for brwt10/7/5 but the LEGACY path for brwt15, and
`campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv.meta` advertises
"6bps half-turn" — the exact undercharge convention that `brwt_ens_build.py` documents as
`convention="half", bps=6.0` = "a HALF-TURN at 3.0bps-equivalent -- the undercharge defect",
and which cost the campaign a headline downgrade at audit A1. The gate test that would catch it,
`test_camp_cost_r3_brwt::test_champion_pool_no_unreemitted_half_turn_brwt`, covers
"brwt10/7/5 ONLY", so brwt15 looked uncovered.

**It is not a live defect — the meta text is stale.** Rebuilt from the same generator with the
same parameters and vintage, differing ONLY in the cost convention:

    committed bytes          ann 27.960%
    convention="half" 6.0bp  ann 29.336%   (+1.056%/yr embedded undercharge)
    convention="full" 6.4bp  ann 27.978%   <- the bytes match THIS

So the champion is charged in full, and the sleeve must NOT be "corrected": subtracting the
half-vs-full delta double-charges a sleeve that was already paying (measured: it costs the
champion 0.064pp of headline for nothing). This test pins the measured truth so a future
iteration cannot repeat that mistake on the strength of a stale provenance note.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402

BRWT15 = "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv"
_GEN = ROOT / "campaign" / "scripts" / "brwt_ens_build.py"


def _gen():
    spec = importlib.util.spec_from_file_location("brwt_ens_build", str(_GEN))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _convention_series(conv, factor, bps):
    return _gen().build(15, 1.5, "2000-01-01", factor=factor, bps=bps,
                        convention=conv, data_vintage="fred_plus_eia_tail")[4]


def test_is_best_brwt_grid_cell_is_not_oos_supported():
    """ITER19 honest negative: scanning the brwt (lookback, band) grid and taking the best IS
    cell finds (lb=15, zb=1.0) at IS SR 3.814 -- above every incumbent -- and adding it to the
    pool PASSES gate 8c (capital-real dAnn +1.118pp, FULL 38.114% -> 39.232%, every other gate
    green). It is still an artifact: the cell is the MAXIMUM of a 32-point IS grid, so its IS
    edge is upward-biased, and it has the WORST IS->OOS degradation in its own family.

    Operator ruling 2026-09-13: REJECT as in-sample. Pinned here so the same scan cannot be
    re-run and re-adopted as a fresh gain.
    """
    def sr(x):
        x = x.dropna()
        return float(x.mean() / x.std(ddof=1) * np.sqrt(252))

    def variant(lb, zb):
        return _gen().build(lb, zb, "2000-01-01", factor=1.0, bps=6.4,
                            convention="full", data_vintage="fred_plus_eia_tail")[4]

    new = variant(15, 1.0)
    inc = {"brwt15": B.load(BRWT15),
           "brwt10": B.load("campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv"),
           "brwt7": B.load("campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv")}

    def drop(s):
        return sr(s[s.index < B.IS_END]) - sr(s[s.index >= B.IS_END])

    assert sr(new[new.index < B.IS_END]) > max(sr(v[v.index < B.IS_END]) for v in inc.values()), \
        "the grid cell is no longer the IS-best -- re-run the scan before reusing this pin"
    assert drop(new) > max(drop(v) for v in inc.values()), \
        "the IS-best cell must remain the worst IS->OOS case; if not, the rejection needs review"
    assert sr(new[new.index >= B.IS_END]) < sr(inc["brwt7"][inc["brwt7"].index >= B.IS_END]), \
        "OOS, the grid-selected cell must remain weaker than an incumbent"


def test_committed_brwt15_charges_full_costs_despite_the_stale_meta():
    committed = B.load(BRWT15)
    full = _convention_series("full", 1.0, 6.4)
    half = _convention_series("half", 0.5, 6.0)

    def mean_ann(x, y):
        j = pd.concat([x.rename("a"), y.rename("b")], axis=1).dropna()
        return float((j.a - j.b).mean()) * 252 * 100  # %/yr

    d_full = mean_ann(committed, full)
    d_half = mean_ann(committed, half)

    # measured: committed - full = +0.0000 %/yr ; committed - half = -1.0564 %/yr
    assert abs(d_full) < 0.05, f"committed bytes drifted from FULL-cost convention ({d_full:+.4f}%/yr)"
    assert d_half < -0.5, ("committed bytes now look half-turn -- the undercharge would be REAL and "
                           f"the champion must be re-emitted ({d_half:+.4f}%/yr)")
    # the two conventions really are distinguishable on this sleeve (~1.06%/yr apart)
    assert abs(d_half - d_full) > 0.5
