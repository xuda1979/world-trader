#!/usr/bin/env python3
"""TDD tests for HUNT_CRYPTO2 round-3 independent verification lib.

Contract (charter R3a): my OWN code must recompute SR / halves / neg-years / corr
from saved sleeve CSVs and reproduce the published metas within tolerance.
Independence: this lib re-implements the metrics (does NOT import bt.*) so a bug in
bt/metrics.py cannot hide behind itself. bt's conventions are pinned by the tests
below (ANN=252 annualization, ddof=1 daily Sharpe, geometric ann, T+1-indexed).

Charter R3b2 (submission integrity): the R1 crypto TS-mom sleeve submitted to
HUNT_VOL2's blend lane must carry HONEST own-span stats recomputed from the CSV,
not copy-pasted from the meta — so a stale meta can't travel with the sleeve.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r3")
import r3lib

ROOT = "/Users/daxu/software/world-trader"
CHAMP_PATH = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
CHAMP_HEAD = "/tmp/champ_head.csv"
SECTOR2 = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/sleeves"
MINE = f"{ROOT}/campaign/agents/chief/coord/HUNT_CRYPTO2/sleeves"


def _ser(dates, rets):
    return pd.Series(rets, index=pd.DatetimeIndex(dates))


# ---------------------------------------------------------------- metrics parity
def test_sharpe_matches_bt_convention():
    r = _ser(pd.date_range("2020-01-01", periods=500, freq="B"), np.random.default_rng(1).normal(0.0004, 0.01, 500))
    got = r3lib.sharpe_d(r)
    want = r.mean() / r.std(ddof=1) * np.sqrt(252)
    assert abs(got - want) < 1e-12, (got, want)


def test_half_split_matches_bt_convention():
    r = _ser(pd.date_range("2020-01-01", periods=101, freq="B"), np.random.default_rng(2).normal(0.0005, 0.01, 101))
    h1, h2 = r3lib.half_split(r)
    k = 101 // 2
    assert abs(h1 - r3lib.sharpe_d(r.iloc[:k])) < 1e-12
    assert abs(h2 - r3lib.sharpe_d(r.iloc[k:])) < 1e-12
    # bt uses len//2 for the split: H1 gets 50 rows, H2 gets 51
    assert len(r.iloc[:k]) == 50 and len(r.iloc[k:]) == 51


def test_neg_years_fail_closed_on_nan_year():
    # a whole year of NaN must COUNT as negative (bt R1 fix), not vanish
    idx = pd.date_range("2020-01-01", "2021-12-31", freq="B")
    r = _ser(idx, np.full(len(idx), 0.001))
    r["2021"] = np.nan
    neg, worst = r3lib.neg_years(r)
    assert neg == 1, (neg, worst)
    assert worst < 0


def test_ann_geo_ruin_guard():
    # product <= 0 => NaN (undefined), not a fake negative/positive number
    r = _ser(pd.date_range("2020-01-01", periods=250, freq="B"),
             np.full(250, -0.10))  # (1-0.1)^250 > 0, fine
    assert np.isfinite(r3lib.ann_geo(r))
    r2 = _ser(pd.date_range("2020-01-01", periods=250, freq="B"), np.full(250, -1.0))
    assert not np.isfinite(r3lib.ann_geo(r2))  # product == 0 -> NaN


def test_corr_uses_inner_join_dropna():
    a = _ser(pd.date_range("2020-01-01", periods=100, freq="B"), np.random.default_rng(3).normal(size=100))
    b = a.copy()
    b.iloc[:10] = np.nan
    got = r3lib.corr_to(a, b)
    manual = pd.concat([a.rename("r"), b.rename("s")], axis=1).dropna().corr().iloc[0, 1]
    assert abs(got - manual) < 1e-12


# ---------------------------------------------------------------- verbatim checks
def test_champion_head_stats_reproduce_published_numbers():
    """HEAD champion (git) must stay the published 39.85%/SR 3.296 blob.
    The worktree is a moving target (coordinator re-emits) and is governed by
    test_worktree_champion_matches_documented_reemit, not by hard bands here."""
    head = r3lib.load_ret(CHAMP_HEAD)
    work = r3lib.load_ret(CHAMP_PATH)
    a, sr = r3lib.ann_geo(head), r3lib.sharpe_d(head)
    assert 0.395 < a < 0.405, a
    assert 3.25 < sr < 3.35, sr
    neg, worst = r3lib.neg_years(head)
    assert neg == 0, (neg, worst)
    # they must differ (re-emits happened 07:28 and 11:41)
    assert not np.allclose(head.values, work.values), "re-emit did not change bytes?"


def test_evaluate_arm_matches_meta_within_tolerance():
    """Every published stat in a meta must be reproduced by MY code from the CSV alone."""
    checks = [  # (path, stat, published, tol)
        (f"{SECTOR2}/A11_rs_ratio#lb126k4.csv", "sr", 0.679, 0.005),
        # R3a FINDING: SECTOR2 metas report ARITHMETIC ann (= sr*vol exactly in all 5
        # metas), not bt's geometric ann. Verified: geo 7.05% vs arith 7.40% for A11.
        (f"{SECTOR2}/A11_rs_ratio#lb126k4.csv", "ann_arith", 0.074, 0.001),
        (f"{SECTOR2}/A11_rs_ratio#lb126k4.csv", "h1", 0.55, 0.005),
        (f"{SECTOR2}/A11_rs_ratio#lb126k4.csv", "h2", 0.95, 0.005),
        (f"{SECTOR2}/A_rs_ratio.csv", "sr", 0.534, 0.005),
        (f"{SECTOR2}/A_rs_ratio.csv", "h2", 0.70, 0.005),
        (f"{SECTOR2}/B_barbell.csv", "sr", 0.613, 0.005),
        (f"{SECTOR2}/C_xle_crud.csv", "sr", 0.154, 0.005),
        (f"{SECTOR2}/D_xlu_ief.csv", "sr", 0.585, 0.005),
        # my own R1 sleeve: meta says SR 0.910 / H1 1.35 / H2 0.24 / negyr 2
        (f"{MINE}/CRYPTO_VolX_10-30_EW12_audit.csv", "sr", 0.910, 0.005),
        (f"{MINE}/CRYPTO_VolX_10-30_EW12_audit.csv", "h1", 1.35, 0.005),
        (f"{MINE}/CRYPTO_VolX_10-30_EW12_audit.csv", "h2", 0.24, 0.005),
    ]
    for path, stat, pub, tol in checks:
        m = r3lib.evaluate_arm(r3lib.load_ret(path), r3lib.load_ret(CHAMP_HEAD))
        got = m[stat]
        assert abs(got - pub) <= tol, (path, stat, got, pub)
        # corr must be reproduced against the HEAD champion (what the metas used)
    m = r3lib.evaluate_arm(r3lib.load_ret(f"{SECTOR2}/A_rs_ratio.csv"), r3lib.load_ret(CHAMP_HEAD))
    assert abs(m["corr"] - (-0.042)) <= 0.005, m["corr"]


def test_evaluate_arm_negyr_and_yearly_reproduce():
    m = r3lib.evaluate_arm(r3lib.load_ret(f"{SECTOR2}/A11_rs_ratio#lb126k4.csv"), r3lib.load_ret(CHAMP_HEAD))
    assert m["neg"] == 2, m
    assert m["years"][2018] == 0.0887 or abs(m["years"][2018] - 0.0887) < 0.0005, m["years"].get(2018)
    assert abs(m["years"][2020] - (-0.0124)) < 0.0005


# ---------------------------------------------------------------- champion provenance (R3 hardening)
def test_champion_head_autoregenerates_from_git():
    """/tmp/champ_head.csv is ephemeral; ensure_champ_head() must (re)build it from
    git HEAD byte-exactly so every R3a claim reproduces from the saved script alone."""
    import os, subprocess
    p = r3lib.ensure_champ_head()
    assert os.path.exists(p)
    want = subprocess.run(
        ["git", "show", "HEAD:software/world-trader/campaign/results/"
         "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"],
        cwd="/Users/daxu/software/world-trader", capture_output=True, check=True).stdout
    with open(p, "rb") as f:
        assert f.read() == want, "ensure_champ_head() bytes != git HEAD champion"
    # and it must be idempotent + self-healing
    os.remove(p)
    p2 = r3lib.ensure_champ_head()
    with open(p2, "rb") as f:
        assert f.read() == want


# ---------------------------------------------------------------- R3 hardening (this session)
def test_load_ret_handles_index_col_csv():
    """R3b census false-negative: AP_gold.csv is a VALID return stream (ac1 0.005,
    2/19 neg yrs) but uses an index date column instead of a 'date' column, so
    load_ret raised and the census logged it UNREADABLE + counted it as a meta gap.
    The loader must fall back to index-column parsing; the census must then report
    its real stats and its real gap (NO_META)."""
    p = f"{ROOT}/campaign/results/sleeve_library/AP_gold.csv"
    r = r3lib.load_ret(p)
    assert len(r) == 4663, len(r)
    assert abs(r3lib.sharpe_d(r) - 0.941) < 0.01, r3lib.sharpe_d(r)
    assert r.index.has_duplicates is False


def test_worktree_champion_matches_documented_reemit():
    """The worktree champion is a MOVING target (coordinator re-emits; the 11:41
    brwtcostfix re-emit took it to SR 3.1810 / ann 37.195%, documented in
    coord/coord_accept_r3_brwtcostfix.json). The test must (a) keep HEAD pinned to
    the published champion, (b) require the worktree to match SOME documented
    acceptance JSON — so any future unexplained drift fails loud instead of stale
    band-guessing."""
    import glob, json
    work = r3lib.load_ret(CHAMP_PATH)
    sr, ann = r3lib.sharpe_d(work), r3lib.ann_geo(work)
    documented = []
    for jf in sorted(glob.glob(f"{ROOT}/campaign/agents/chief/coord/coord_accept_*.json")):
        with open(jf) as f:
            d = json.load(f)
        st = d.get("stats") or {}
        if "sr" in st and "ann_cagr_pct" in st:
            documented.append((jf, float(st["sr"]), float(st["ann_cagr_pct"]) / 100.0))
    assert documented, "no acceptance JSON found — cannot pin worktree champion"
    hits = [jf for jf, s, a in documented
            if abs(s - sr) < 2e-3 and abs(a - ann) < 2e-3]
    assert hits, f"worktree champ SR={sr:.4f} ann={ann:.4f} matches no documented re-emit: {documented}"
    # HEAD remains the published champion, immutable
    head = r3lib.load_ret(r3lib.ensure_champ_head())
    assert abs(r3lib.sharpe_d(head) - 3.2964) < 0.005
    assert abs(r3lib.ann_geo(head) - 0.3985) < 0.002
