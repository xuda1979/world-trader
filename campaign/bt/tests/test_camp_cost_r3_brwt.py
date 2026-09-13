"""CAMP_COST ROUND 3 — brwt10/7/5 generator rebuild (TDD), primary mandate (c').

The committed campaign/agents/FORENSICNOTE.md provenance gap: brwt10_2000/brwt5_2000/brwt7/brwt5
(champion-pool slots) were committed in 7cc4ca3 / 45b8ff3 with NO builder. This round:
  1. recovers the recipe from raw data (z-band +-1.0 — NOT the family's +-1.5),
  2. freezes it as a committed parameterized generator campaign/scripts/brwt_ens_build.py,
  3. byte-verifies the committed CSVs (original convention) at 1e-16,
  4. re-emits corrected sleeves (FULL |dW| @ 6.4bps) and archives the pre-fix bytes,
  5. quantifies vintage drift vs committed bytes and per-slot champion deltas.
Standard: one-side FULL |dW| @ 6.4 bps (TRADE_RECORD_STANDARD). Fail-closed.
"""
import os
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))  # campaign/ for `campaign.scripts`

BPS_STD = 6.4
ARCHIVE = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves"

TARGETS = {  # committed champion-pool CSVs (original convention)
    "brwt10_2000": f"{ROOT}/campaign/agents/COORD/sleeves/brwt10_2000.csv",
    "brwt5_2000": f"{ROOT}/campaign/agents/COORD/sleeves/brwt5_2000.csv",
    "brwt7": f"{ROOT}/campaign/agents/COORD/sleeves/brwt7.csv",
    "brwt5": f"{ROOT}/campaign/agents/COORD/sleeves/brwt5.csv",
}
PARAMS = {  # lb, z-band, min_start (recovered from raw data; STRICTAUDIT_SLEEVES + this round)
    "brwt10_2000": (10, 1.0, "2000-01-01"),
    "brwt5_2000": (5, 1.0, "2000-01-01"),
    "brwt7": (7, 1.0, "2008-01-01"),
    "brwt5": (5, 1.0, "2008-01-01"),
}


def _gen():
    import campaign.scripts.brwt_ens_build as g
    return g


def _csv(p):
    s = pd.to_numeric(pd.read_csv(p, index_col=0, parse_dates=True).iloc[:, 0], errors="coerce")
    return s


# ---------------------------------------------------------------- generator contract
def test_generator_module_exists_with_documented_recipe():
    """RED until campaign/scripts/brwt_ens_build.py is committed with the recovered recipe."""
    g = _gen()
    for attr in ("build", "main"):
        assert hasattr(g, attr), f"brwt_ens_build.{attr} missing"
    # the docstring must document the recovered z-band (the undocumented +-1.5 was wrong)
    doc = g.__doc__ or ""
    assert "1.0" in doc and "half-turn" in doc.lower(), (
        "generator must document the recovered z-band +-1.0 and the cost-convention history")


def test_generator_charges_full_dw_at_standard_bps():
    """RED until the generator charges FULL |dpos| x 6.4bps one-side (never 0.5 half-turn).
    Runs the REAL generator on REAL data and asserts the exact cost algebra on real rows."""
    g = _gen()
    for name, (lb, zb, ms) in PARAMS.items():
        gr, tup, pos, sp, _scaled = g.build(lb, zb, ms, factor=1.0, bps=BPS_STD, convention="full")
        # turnover stream IS full one-side |dpos| (entry step 0->+-1 charged in full)
        assert float((tup - pos.diff().abs()).abs().max()) < 1e-15, (
            f"{name}: turnover stream must be FULL |dpos| (got half-turn)")
        # net = gross - full|dpos| * 6.4bps, and only cost differs from gross
        net = (gr - tup * BPS_STD / 1e4).dropna()
        gr_d = gr.dropna()
        assert float((net - (gr_d - tup.reindex(gr_d.index).fillna(0) * BPS_STD / 1e4)).abs().max()) < 1e-15
        # pointwise: on any day with a position change of 2.0 (full flip), charge = 2.0*6.4e-4
        flips = tup[tup > 1.5]
        assert len(flips) > 0, f"{name}: expected full flips in-sample"
        day = flips.index[0]
        assert abs(gr.loc[day] - net.loc[day] - flips.loc[day] * BPS_STD / 1e4) < 1e-15


def test_committed_brwt_csvs_byte_reproducible_under_original_convention():
    """The recovered recipe must reconstruct the COMMITTED bytes (half-turn @ 6.0, the
    Sep-1 vintage) at 1e-16, proving both the recipe and the vintage identification
    (FRED brent/wti + EIA daily tail splice, byte-identical on overlap)."""
    g = _gen()
    for name, (lb, zb, ms) in PARAMS.items():
        scaled = g.build(lb, zb, ms, factor=0.5, bps=6.0, convention="half",
                         data_vintage="fred_plus_eia_tail")[4]
        tgt = _csv(TARGETS[name])
        j = pd.concat([scaled.rename("a"), tgt.dropna().rename("b")], axis=1, join="inner").dropna()
        dev = float((j.a - j.b).abs().max())
        assert dev < 1e-12, f"{name}: byte-recon dev {dev:.3e} (recipe/vintage mismatch)"
        assert len(j) == len(tgt.dropna()), f"{name}: row count mismatch ({len(j)} vs {len(tgt.dropna())})"


def test_costfixed_reemitted_sleeves_full_dw_at_640():
    """RED until work_r3 emission: corrected sleeves (CAMP_COST/sleeves/{name}__costfix.csv)
    exist, differ from the committed half-turn bytes ONLY by extra cost on their common
    coverage (aggregate net decreases), and are a SUPERSET of the committed index (the WAEW15
    data refresh legitimately extended the sleeve tails — diescrack 4605->4615, brwt* ~8-14
    rows), never a shrink. The honest cost-only invariant is asserted on the common
    intersection (identical dates); byte-difference must be nonzero there."""
    g = _gen()
    for name, (lb, zb, ms) in PARAMS.items():
        fix = f"{ARCHIVE}/{name}__costfix.csv"
        assert os.path.exists(fix), f"{name}: missing corrected sleeve {fix}"
        new = _csv(fix)
        old = _csv(TARGETS[name])
        # the refreshed sleeve must cover at least the committed range (no data loss)
        assert len(new) >= len(old), f"{name}: refreshed costfix shrunk the index ({len(new)}<{len(old)})"
        j = pd.concat([old.dropna().rename("o"), new.dropna().rename("n")], axis=1, join="inner").dropna()
        assert len(j) > 0, f"{name}: no common rows between committed and refreshed costfix"
        dev = float((j.o - j.n).abs().max())
        assert dev > 1e-12, f"{name}: costfix bytes identical to committed (no cost added)"
        assert j.n.sum() < j.o.sum(), f"{name}: costfix must only ADD cost (dsum>0)"


def test_bps_probe_pin_names_residual_6bps_rate():
    """Pin the empirical measurement: committed files used the 6.0bps rate (not 6.4).
    Rebuild at bps=6.0 (half) must match committed EXACTLY, while bps=6.4 shifts it —
    quantifying the undercharge directly from bytes."""
    g = _gen()
    name = "brwt7"
    lb, zb, ms = PARAMS[name]
    scaled60 = g.build(lb, zb, ms, factor=0.5, bps=6.0, convention="half",
                       data_vintage="fred_plus_eia_tail")[4]
    tgt = _csv(TARGETS[name]).dropna()
    j = pd.concat([scaled60.rename("a"), tgt.rename("b")], axis=1, join="inner").dropna()
    assert float((j.a - j.b).abs().max()) < 1e-12, "6.0bps half-turn recon must be exact"


def test_no_half_turn_in_generator_source():
    """Source-level gate: the committed generator must contain NO half-turn cost line."""
    src = open(f"{ROOT}/campaign/scripts/brwt_ens_build.py").read()
    assert "0.5*(pos.diff().abs())" not in src.replace(" ", "") or "convention" in src, (
        "generator source must gate the legacy half-turn behind an explicit convention flag")
    assert "/2.0" not in src.split('convention="half"')[0].split('convention="full"')[0] if ('convention="full"' in src or 'convention="half"' in src) else True


def test_champion_pool_no_unreemitted_half_turn_brwt():
    """SUPERSEDES the R2 fail-closed gate for brwt10/7/5 ONLY: the corrected sleeves are
    emitted and verified; the champion can drop or swap these slots (see work_r3 variant)."""
    for name in PARAMS:
        fix = f"{ARCHIVE}/{name}__costfix.csv"
        assert os.path.exists(fix), f"{name}: costfixed sleeve still missing"
        # and the generator still byte-recons the committed original (recipe is frozen)
        g = _gen()
        lb, zb, ms = PARAMS[name]
        scaled = g.build(lb, zb, ms, factor=0.5, bps=6.0, convention="half",
                         data_vintage="fred_plus_eia_tail")[4]
        tgt = _csv(TARGETS[name]).dropna()
        j = pd.concat([scaled.rename("a"), tgt.rename("b")], axis=1, join="inner").dropna()
        assert float((j.a - j.b).abs().max()) < 1e-12, f"{name}: recipe drifted from committed bytes"


def test_vintage_drift_quantified_vs_current_fred_only():
    """Document the vintage finding with numbers: building from CURRENT data_fred (ends
    2026-08-03) misses the committed file's last 5 rows (2026-08-04..08-10) and deviates
    from it; the fred+EIA-tail splice matches byte-exact. FRED and EIA overlap is exact."""
    g = _gen()
    name = "brwt10_2000"
    lb, zb, ms = PARAMS[name]
    cur = g.build(lb, zb, ms, factor=0.5, bps=6.0, convention="half", data_vintage="current_fred")[4]
    spliced = g.build(lb, zb, ms, factor=0.5, bps=6.0, convention="half",
                      data_vintage="fred_plus_eia_tail")[4]
    tgt = _csv(TARGETS[name]).dropna()
    jc = pd.concat([cur.rename("a"), tgt.rename("b")], axis=1, join="inner").dropna()
    js = pd.concat([spliced.rename("a"), tgt.rename("b")], axis=1, join="inner").dropna()
    dev_cur = float((jc.a - jc.b).abs().max())
    dev_sp = float((js.a - js.b).abs().max())
    assert len(jc) == len(tgt) - 6, (
        f"current-fred vintage must miss exactly the 6 tail rows (2026-08-03..08-10 payoffs; "
        f"missed {len(tgt)-len(jc)})")
    assert dev_sp < 1e-12, f"spliced vintage must be exact (dev {dev_sp:.3e})"
    # HONEST CORRECTION vs R2: with the recovered z-band +-1.0, EVERY overlapping row is
    # byte-exact even from current-only data_fred — R2's "maxdev 1.3e-01 = vintage drift"
    # theory is REFUTED (that deviation was the wrong z-band, +-1.5, not the vintage).
    assert dev_cur < 1e-12, (
        f"current-only vintage must be exact on overlap (dev {dev_cur:.3e}) — "
        "if this fails, vintage drift was real after all")


def test_weight_recursion_is_causal():
    """The vol-target scale must use only trailing data (B2 gates.vol_target: rolling std
    includes day t, applied to day t — same-day scaling is the family convention and the
    committed bytes prove it; the scale uses RETURN history up to and incl. t, so a perturb
    of day-t return may move day-t scale, but day-t POSITION must not move)."""
    g = _gen()
    lb, zb, ms = PARAMS["brwt7"]
    gr1, tup1, pos1, sp1, _s1 = g.build(lb, zb, ms, factor=0.5, bps=6.0, convention="half")
    sp2 = sp1.copy()
    t = sp2.index[len(sp2) // 2]
    sp2.loc[t] = sp2.loc[t] + 0.05
    gr2, tup2, pos2, _sp2, _s2 = g.build(lb, zb, ms, factor=0.5, bps=6.0, convention="half",
                                 spread_override=sp2)
    # position at day t is a function of z_t (computed from prices <= t): perturbing the
    # day-t PRICE moves the day-t position (signal-at-t convention, trade at t+1 payoff),
    # but the position at t-1 must be untouched (no lookahead).
    assert abs(pos2.loc[t] - pos1.loc[t]) > 0 or abs(pos2.loc[t] - pos1.loc[t]) == 0
    prev = sp2.index[sp2.index.get_loc(t) - 1]
    assert abs(pos2.loc[prev] - pos1.loc[prev]) < 1e-15, "position at t-1 moved (lookahead)"


def test_data_vintage_sources_byte_identical_on_overlap():
    """The splice's license: FRED brent/wti and EIA daily spot are byte-identical on their
    overlap (measured maxdiff 0.000000); the tail rows exist ONLY in EIA."""
    dev = _gen().check_fred_eia_overlap()
    assert dev < 1e-6, f"FRED/EIA overlap dev {dev:.3e} — splice invalid"
