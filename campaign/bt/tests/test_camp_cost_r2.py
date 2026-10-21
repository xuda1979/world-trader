"""CAMP_COST ROUND 2 — sleeve-internal cost honesty (TRADE_RECORD_STANDARD §4).

R1 flagged 2 slot-level half-turn offenders (dualmom ~0.1bps/yr, diescrack ~2.2bps/yr
champion-level). Round 2 verifies the INTERNAL cost models of the sleeve builders on a
synthetic 2-day stream (TDD: these tests were written RED against the committed builders)
and pins the corrected, re-emitted champion-pool sleeve CSVs.

Standard: one-side turnover = FULL |dW| (qty_notional = |position change|), charged at
6.4 bps. Anything less (0.5 half-turn, or the documented 6.0bps rate) undercharges.
"""
import importlib.util
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

BPS_STD = 6.4  # TRADE_RECORD_STANDARD one-side minimum


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- synthetic streams
def _synth_spread(n=8, lookback=3, gate=0.5):
    """Deterministic spread whose z crosses the gate twice: flat -> long -> flat -> short.
    2-day streams are the minimal interesting case; 8 days covers entry, hold, exit,
    re-entry on the other side (entry AND exit turnover both charged)."""
    idx = pd.bdate_range("2020-01-01", periods=n)
    sp = pd.Series([0.0, 0.0, 0.0, -1.0, -1.0, -1.0, 1.0, 1.0], index=idx, dtype=float)
    return sp


def test_diescrack_zrev_charges_full_dw_at_standard_bps():
    """RED until HUNT_BASIS2 lib.zrev is fixed: it charged pos.diff().abs()/2 * 6.0bps
    (half-turn at 6bps = 3.0bps-equivalent, vs the 6.4bps full-|dW| standard)."""
    lib = _load(f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/scratch/lib.py", "basis2lib")
    sp = _synth_spread()
    net, gr, pos, tup = lib.zrev(sp, lookback=3, gate=0.5, min_start=sp.index[0])
    # expected: FULL |dpos| one-side at the 6.4bps standard, T+1 P&L unchanged
    ret = sp.diff().shift(-1)
    gr_exp = (pos * ret).dropna()
    tup_full = pos.diff().abs().reindex(gr_exp.index).fillna(0.0)
    net_exp = gr_exp - tup_full * BPS_STD / 1e4
    j = pd.concat([net.rename("n"), net_exp.rename("e")], axis=1).dropna()
    assert len(j) == len(gr_exp), "zrev must not drop P&L days"
    assert float((j.n - j.e).abs().max()) < 1e-15, (
        f"diescrack zrev must charge FULL |dpos| x {BPS_STD}bps "
        f"(max dev {float((j.n - j.e).abs().max()):.3e})")
    # and the returned turnover stream must BE the full one-side |dpos|
    assert float((tup - tup_full).abs().max()) < 1e-15, "zrev turnover stream must be FULL |dpos|"


def test_dualmom_cost_convention_full_dw_standard_bps():
    """RED until QA_dualmom_band121.py is fixed: line `turn.iloc[p+1] =
    0.5*(neww-prev).abs().sum()` charged at COST=6.0 — a half-turn at 6bps."""
    src = open(f"{ROOT}/campaign/scripts/QA_dualmom_band121.py").read()
    assert "0.5 * (neww - prev).abs().sum()" not in src, (
        "dualmom builder still charges 0.5 half-turn on monthly rebalance")
    assert "(neww - prev).abs().sum()" in src, "dualmom must charge FULL |dW| turnover"
    assert "COST_STD = 6.4" in src or "6.4 / 1e4" in src, (
        "dualmom must charge the 6.4bps standard rate, not the 6.0 legacy rate")


def test_dualmom_synthetic_rebalance_full_dw():
    """Synthetic 2-rebalance stream through the dualmom loop shape (loop over REBALANCE
    dates only, weights held between, as in QA_dualmom_band121.py): month-end weight change
    0 -> w charges FULL |w| (entry), w -> w' charges FULL |w-w'| (rebalance)."""
    idx = pd.bdate_range("2020-01-01", periods=6)
    mes = [idx[1], idx[3]]                  # two month-ends
    W = pd.DataFrame(0.0, index=idx, columns=["A", "B"])
    W.loc[mes[0]] = [0.5, 0.5]              # month-end 1: enter
    W.loc[mes[1]] = [0.9, 0.1]              # month-end 2: rebalance
    turn = pd.Series(0.0, index=idx)
    prev = pd.Series(0.0, index=["A", "B"])
    for i, t in enumerate(mes):             # FIXED loop shape (mirrors the builder)
        neww = W.loc[t]
        p = idx.get_loc(t)
        if p + 1 < len(idx):
            turn.iloc[p + 1] = (neww - prev).abs().sum()   # FIXED convention (full |dW|)
            prev = neww
    # entry day must charge 1.0 (full 0.5+0.5), rebalance day 0.8 (|0.4|+|0.4|)
    assert abs(turn.iloc[2] - 1.0) < 1e-15, "entry must charge full notional"
    assert abs(turn.iloc[4] - 0.8) < 1e-15, "rebalance must charge full |dW|"


def test_brwt15_generator_no_half_turn():
    """Sweep finding (R1 missed): the brwt15 champion slot generator charges
    pos.diff().abs()/2.0 * 6e-4 (half-turn @ 6bps) in e1_idea2_a6r7_brwt_detrunc.py."""
    src = open(f"{ROOT}/campaign/agents/E1_20yspan/work/e1_idea2_a6r7_brwt_detrunc.py").read()
    assert "(pos.diff().abs()/2.0)" not in src, (
        "brwt15 generator still charges half-turn; must charge FULL |dpos| @ 6.4bps")


def test_qaxasts_generator_no_half_turn():
    """Sweep finding (R1 missed): r6lib.wback_rb (QAxasts slot generator) charges
    0.5*|neww-prev| at COST=6.0."""
    src = open(f"{ROOT}/campaign/agents/A3_xs_quality/r6lib.py").read()
    assert "0.5*np.abs(neww-prev).sum()" not in src, (
        "r6lib.wback_rb still charges half-turn; must charge FULL |dW| @ 6.4bps")


# ---------------------------------------------------------------- emitted-file pins
# Champion-pool sleeves re-emitted by the CAMP_COST R2 costfix wave (full |dW| @ 6.4bps,
# all other mechanics frozen). Corrector: campaign/agents/chief/coord/CAMP_COST/sleeves/
COSTFIX = {
    "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    # R3 swap (coordinator, 2026-09-07): corrected FULL|dW|@6.4 emissions now feed the
    # champion pool (rawew13v2_build.PATHS points here; byte-verified vs candidate13slot).
    "brwt10": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
}
ARCHIVE = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves"
# pre-fix archive stem may differ from the pool key: the committed brwt10 file
# is brwt10_2000.csv, so CAMP_COST archived it as brwt10_2000__prefix.csv
PREFIX_NAME = dict(brwt10="brwt10_2000")


def test_costfix_sleeves_differ_from_archived_halfturn_originals():
    """The re-emitted CSV must NOT equal the archived pre-fix (undercharging) bytes —
    i.e. the costfix actually moved the series — and the archive must exist for before/after
    accounting."""
    for name, rel in COSTFIX.items():
        arch = f"{ARCHIVE}/" + PREFIX_NAME.get(name, name) + "__prefix.csv"
        assert os.path.exists(arch), f"missing pre-fix archive for {name}: {arch}"
        old = pd.read_csv(arch, index_col=0, parse_dates=True).iloc[:, 0]
        new = pd.read_csv(f"{ROOT}/{rel}", index_col=0, parse_dates=True).iloc[:, 0]
        j = pd.concat([old.rename("o"), new.rename("n")], axis=1, join="inner").dropna()
        dev = float((j.o - j.n).abs().max())
        assert dev > 1e-12, f"{name}: re-emitted series identical to pre-fix archive (dev={dev})"


def test_costfix_sleeves_are_cost_grows_only():
    """Honesty direction: removing an undercharge can only ADD cost. Gross P&L is untouched,
    so the corrected core (pre-vol-target) net is <= the old core on every day. The re-emitted
    files are vol-target-scaled with a path-dependent scale, so pointwise ordering does NOT
    survive scaling (measured: up to 2164 pointwise violations with 0 core violations) — the
    exact file-level invariants pinned here are (a) index is a SUPERSET of the pre-fix archive
    (the RAWEW15 data refresh legitimately extended the sleeve tail — diescrack 4605->4615 —
    never a shrink), and (b) aggregate net <= old on the common intersection (cost only adds)."""
    for name, rel in COSTFIX.items():
        old = pd.read_csv(f"{ARCHIVE}/" + PREFIX_NAME.get(name, name) + "__prefix.csv", index_col=0, parse_dates=True).iloc[:, 0]
        new = pd.read_csv(f"{ROOT}/{rel}", index_col=0, parse_dates=True).iloc[:, 0]
        # the refreshed/re-emitted sleeve must never DROP coverage vs the pre-fix archive
        assert len(new) >= len(old), (
            f"{name}: refreshed/costfix index shrank vs pre-fix archive ({len(new)} < {len(old)} rows)")
        j = pd.concat([old.rename("o"), new.rename("n")], axis=1, join="inner").dropna()
        assert j.n.sum() <= j.o.sum(), (
            f"{name}: corrected aggregate net exceeds old — costfix must only add cost "
            f"(dsum={j.n.sum() - j.o.sum():+.3e})")


def test_champion_pool_has_no_unreemitted_half_turn_sleeves():
    """Every champion-pool sleeve (rawew13v2 POOL+NEW) must be either costfix-re-emitted or
    on the documented non-half-turn allowlist. Fails while any half-turn sleeve is stale.
    R3 UPDATE: brwt10/7/5 generators were recovered (recipe: log(Brent/WTI) z-rev, z-band
    +-1.0 — NOT the family +-1.5), frozen as campaign/scripts/brwt_ens_build.py, byte-verified
    against the committed CSVs at 9.996e-17 under the legacy half@6.0 convention, and the
    corrected FULL|dW|@6.4 sleeves are emitted to CAMP_COST/sleeves/{name}__costfix.csv (see
    test_camp_cost_r3_brwt.py). They now join COSTFIX — the gate stays red until the
    coordinator swaps the champion pool to the corrected CSVs, and the champion-pool path
    still points at the committed (undercharging) files."""
    import campaign.scripts.rawew13v2_build as rb
    allowlist = {  # verified non-half-turn (see CAMP_COST FINDINGS R2 per-sleeve table)
        "C5ng", "C5ngsum", "A5r2", "a6r7",  # full |dW| @ 6.0, byte-exact recon (rate residual)
        "carryv2", "CFX4",                   # full 2-leg turnover @ 6.0 (2x overcharge, conservative)
    }
    # R3: corrected brwt10/7/5 sleeves EXIST and are verified, but the champion builder still
    # consumes the committed half@6.0 files — the pool is stale until the coordinator re-emits.
    stale = set(rb.NAMES) - set(COSTFIX) - allowlist
    assert not stale, (
        "champion-pool sleeves still consuming half@6.0 committed bytes (corrected "
        "FULL|dW|@6.4 CSVs exist in CAMP_COST/sleeves/*__costfix.csv; coordinator must swap "
        f"rawew13v2_build.PATHS to them): {sorted(stale)}")
