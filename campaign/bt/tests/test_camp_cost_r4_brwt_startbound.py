"""CAMP_COST ROUND 4 — brwt_ens_build.py start-bound hardening (charter: fixture test).

R4 probes on the R3 generator found SILENT-EMPTY failure modes at the min_start boundary:
  P2  min_start after the last spread date  -> returns an EMPTY series (n=0), no error;
      --emit would then write a 0-valid-row CSV and --verify would "pass" vacuously.
  P3  min_start inside the last few days    -> returns an ALL-NaN series (notna=0), no error.
Both are the same defect class: an impossible start window is indistinguishable, downstream,
from a real sleeve that happens to have no valid rows yet. Fail-closed contract (GATES
CONTRACT 3) says these must RAISE.

Pins (must not move — the committed bytes depend on them):
  P1  boundary inclusion is >= : a min_start that IS a spread date is included.
  P4  warmup floor             : 59 leading NaN rows (vol_target min_days=60: row 0 NaN from
      sp.diff() + 59 rows below min_periods), first valid at 0-based row 60; committed
      files show leadNaN=59, first valid 2000-03-30 (min_start 2000) / 2008-03-31 (2008).
  P5  min_start before all data is legal (clamp, no error).
Fails-closed WITHOUT touching any computation for valid configs (byte-recon tests in
test_camp_cost_r3_brwt.py must stay green).
"""
import os
import sys

import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))  # campaign/ for `campaign.scripts`


def _gen():
    import campaign.scripts.brwt_ens_build as g
    return g


def _spread():
    br, wt = _gen().load_inputs("fred_plus_eia_tail")
    import numpy as np
    return (np.log(br) - np.log(wt)).dropna()


# ------------------------------------------------------------------ P1: boundary pin
def test_min_start_boundary_is_inclusive_ge():
    """min_start exactly on a spread date must INCLUDE that date (committed semantics)."""
    g = _gen()
    sp = _spread()
    day = sp.index[3000]
    *_, pos, sp2, _s = g.build(10, 1.0, str(day.date()), spread_override=sp)
    assert sp2.index.min() == day, (
        f"min_start {day.date()} must be included (>=), got first={sp2.index.min().date()}")
    # and the day BEFORE it must not leak in
    assert sp2.index.min() > sp.index[2999]


# ------------------------------------------------------------------ P2/P3: fail-closed
def test_min_start_after_data_end_raises_not_silent_empty():
    """RED (R4 probe P2): min_start past the last spread date silently returned n=0.
    Must raise ValueError naming both dates."""
    g = _gen()
    sp = _spread()
    with pytest.raises(ValueError, match="after"):
        g.build(10, 1.0, "2027-01-01", spread_override=sp)


def test_min_start_too_late_for_any_valid_row_raises_not_all_nan():
    """RED (R4 probe P3): a window too short for ONE valid vol-target row (< 61 obs =
    min_days 60 + the diff-consumed first row) silently returned all-NaN. Must raise."""
    g = _gen()
    sp = _spread()
    too_late = str(sp.index[-20].date())  # only 20 obs remain -> 0 valid rows possible
    with pytest.raises(ValueError, match="obs"):
        g.build(10, 1.0, too_late, spread_override=sp)


def test_min_start_just_enough_for_one_valid_row_is_legal():
    """62 obs = 1 valid scaled row -> must NOT raise (that is a real, if tiny, sleeve).
    Valid-row arithmetic: row 0 lost to sp.diff(), last row lost to shift(-1), then
    vol_target min_days=60 needs 60 valid net rows -> valid = n_obs - 61."""
    g = _gen()
    sp = _spread()
    start = str(sp.index[-62].date())
    *_, pos, sp2, scaled = g.build(10, 1.0, start, spread_override=sp)
    assert len(sp2) == 62
    assert int(scaled.notna().sum()) == 1, "62 obs must yield exactly 1 valid row"


# ------------------------------------------------------------------ P4: warmup floor pin
def test_warmup_floor_59_leading_nans_matches_committed_bytes():
    """Pin the emission warmup contract: 59 leading NaN rows, first valid 2000-03-30 /
    2008-03-31 — exactly what the four committed champion-pool CSVs carry (leadNaN=59)."""
    g = _gen()
    expect = {"brwt10_2000": ("2000-03-30", 59), "brwt7": ("2008-03-31", 59)}
    for name, (first_valid, lead) in expect.items():
        lb, zb, ms = {"brwt10_2000": (10, 1.0, "2000-01-01"),
                      "brwt7": (7, 1.0, "2008-01-01")}[name]
        *_, scaled = g.build(lb, zb, ms)
        # raw build carries 60 leading NaNs (spread starts 2000-01-04; committed index
        # starts 2000-01-05) — --emit reindexes to the committed index, dropping one,
        # leaving exactly 59. Pin the EMITTED view (that is what bytes carry).
        tgt_idx = pd.read_csv(
            f"{ROOT}/campaign/agents/COORD/sleeves/{name}.csv",
            index_col=0, parse_dates=True).index
        emitted = scaled.reindex(tgt_idx)
        n_lead = 0
        for v in emitted.values:
            if pd.isna(v):
                n_lead += 1
            else:
                break
        assert n_lead == lead, f"{name}: emitted leading NaN rows {n_lead} != committed {lead}"
        assert str(scaled.dropna().index.min().date()) == first_valid
        # and the committed file agrees (fixture cross-check)
        tgt = pd.to_numeric(pd.read_csv(
            f"{ROOT}/campaign/agents/COORD/sleeves/{name}.csv",
            index_col=0, parse_dates=True).iloc[:, 0], errors="coerce")
        tl = 0
        for v in tgt.values:
            if pd.isna(v):
                tl += 1
            else:
                break
        assert tl == lead, f"{name}: committed leading NaNs {tl} != generator {lead}"


# ------------------------------------------------------------------ P5: early start clamp
def test_min_start_before_all_data_is_legal_clamp():
    """min_start before the first spread date clamps to the data (no error, full span)."""
    g = _gen()
    sp = _spread()
    *_, sp2, _scaled = g.build(10, 1.0, "1990-01-01", spread_override=sp)
    assert sp2.index.min() == sp.index.min()
    assert sp2.index.max() == sp.index.max()


# ------------------------------------------------------------------ no silent-empty CLI
def test_verify_judgment_rejects_leading_generator_rows_diescrack_class():
    """RED (R4 probe P6). --verify's judgment is dev < 1e-12 AND len(inner) == len(target);
    the inner join HIDES generator-valid rows at dates the target index does not contain.
    LEADING extras are the R2 diescrack incident class (59 spurious leading vol-warmup rows
    emitted where the archive index had dropped them; inner join still said BYTE-EXACT).
    TRAILING extras are benign: the committed index is a fixed vintage artifact and the
    live EIA tail keeps accruing past its end, so newer tail rows must NOT fail a recon —
    they are disclosed instead. The judgment is therefore DATE-DIRECTIONAL: fail on any
    generator-valid row BEFORE the target's first date; disclose (not fail) trailing."""
    g = _gen()
    tgt = g._load_csv_ret(f"{ROOT}/campaign/agents/COORD/sleeves/brwt7.csv")
    *_, scaled = g.build(7, 1.0, "2008-01-01", factor=0.5, bps=6.0, convention="half")
    gen_valid = scaled.dropna()
    j = pd.concat([gen_valid.rename("a"), tgt.rename("b")], axis=1, join="inner").dropna()
    dev = float((j.a - j.b).abs().max())

    # probe setup: real run has perfect overlap + benign trailing extras only
    assert dev < 1e-12 and len(j) == len(tgt), "real recon broken"
    n_leading = int((gen_valid.index < tgt.index.min()).sum())
    n_trailing = int((gen_valid.index > tgt.index.max()).sum())
    assert n_leading == 0 and n_trailing > 0, (
        f"expected vintage-tail shape, got leading={n_leading} trailing={n_trailing}")

    # (i) trailing extras (live vintage growth): recon stays BYTE-EXACT, extras disclosed
    assert g.verify_judgment(dev=dev, n_inner=len(j), n_tgt=len(tgt),
                             n_gen_leading=n_leading) is True

    # (ii) LEADING extras = diescrack class: simulate an archive that DROPPED the first 10
    # valid generator dates (index-only change; values on shared dates stay byte-perfect).
    # Old inner-join logic: inner == len(trimmed target) -> vacuous BYTE-EXACT. Must FAIL.
    tgt_trim = tgt.iloc[10:]
    j2 = pd.concat([gen_valid.rename("a"), tgt_trim.rename("b")], axis=1,
                   join="inner").dropna()
    dev2 = float((j2.a - j2.b).abs().max())
    lead2 = int((gen_valid.index < tgt_trim.index.min()).sum())
    assert dev2 < 1e-12 and len(j2) == len(tgt_trim) and lead2 == 10, "trim probe broken"
    assert g.verify_judgment(dev=dev2, n_inner=len(j2), n_tgt=len(tgt_trim),
                             n_gen_leading=lead2) is False, (
        "verify judgment accepted 10 generator-valid rows BEFORE the target start "
        "(diescrack leading-rows incident class)")

    # (iii) empty target can never be BYTE-EXACT (vacuous pass)
    assert g.verify_judgment(dev=0.0, n_inner=0, n_tgt=0, n_gen_leading=0) is False
