"""ROUND 4 (HUNT_TREASFUT): CHAMPION20Y_V2 rebuild path — TDD.

R3 found champion20y_build.py --verify DIFFs its own committed V2 books
(BAL 3.107e-03 / SAFE 6.160e-03 / AGGR 6.206e-03) because commit b268e52
("champion costfix re-emit") re-emitted 3 of the 13 pool sleeves
(E1_QAxasts_tsmom189_2006, QA_dualmom_band121, E1_brwt_spread_rev15_2000).

These tests pin the REPAIR: a rebuild path that uses the committed V2-era
(git c745682) blobs for those 3 sleeves must reproduce all 3 committed V2
books to <= 1e-12, and must NOT silently succeed if any pool sleeve drifts.

RED first: fails (ImportError/FileNotFoundError) until
campaign/scripts/HUNT_TREASFUT_champion20y_v2_rebuild.py exists.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../world-trader
SCRIPT = ROOT / "campaign/scripts/HUNT_TREASFUT_champion20y_v2_rebuild.py"
PRE_DIR = (
    ROOT
    / "campaign/agents/chief/coord/HUNT_TREASFUT/work_r4/pre_costfix_sleeves"
)
BAR = 1e-12
BOOKS = {
    "GOAL100_CHAMPION20Y_V2_BALANCED_daily.csv",
    "GOAL100_CHAMPION20Y_V2_SAFE_daily.csv",
    "GOAL100_CHAMPION20Y_V2_AGGRESSIVE_daily.csv",
}


def _load(path: Path) -> pd.Series:
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df.iloc[:, 0].astype(float)


@pytest.fixture(scope="module")
def rebuilt(tmp_path_factory):
    """Run the rebuild script once; return {book_name: (committed, rebuilt)}."""
    assert SCRIPT.exists(), (
        f"rebuild script missing: {SCRIPT} (write it to make this suite GREEN)"
    )
    assert PRE_DIR.exists(), f"pre-costfix blob dir missing: {PRE_DIR}"
    outdir = tmp_path_factory.mktemp("v2_rebuild")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--outdir", str(outdir)],
        capture_output=True, text=True, timeout=900,
    )
    assert r.returncode == 0, f"rebuild failed:\n{r.stdout}\n{r.stderr}"
    out = {}
    for fn in sorted(BOOKS):
        committed = _load(ROOT / "campaign/results" / fn)
        new = _load(outdir / fn)
        j = pd.concat([committed.rename("c"), new.rename("n")], axis=1,
                      join="inner").dropna()
        assert len(j) >= 4000, f"{fn}: only {len(j)} overlapping rows"
        out[fn] = (committed, new, float((j.c - j.n).abs().max()), len(j))
    return out


@pytest.mark.parametrize("fn", sorted(BOOKS))
def test_v2_book_rebuilds_exact(rebuilt, fn):
    committed, _new, maxdev, n = rebuilt[fn]
    assert maxdev <= BAR, (
        f"{fn}: max|rebuilt-committed| = {maxdev:.3e} > {BAR:.0e} (n={n})"
    )


def test_rebuild_calendar_matches_committed(rebuilt):
    for fn, (committed, new, _md, _n) in rebuilt.items():
        assert new.index.equals(committed.index), (
            f"{fn}: rebuilt index != committed index"
        )


def test_pre_costfix_blobs_differ_from_live_tree():
    """Guard: the 3 pinned blobs must be the OLD (pre-costfix) bytes, i.e.
    actually different from the live sleeves — else the pin is vacuous."""
    pairs = [
        ("E1_QAxasts_tsmom189_2006.csv",
         "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv"),
        ("QA_dualmom_band121.csv",
         "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"),
        ("E1_brwt_spread_rev15_2000.csv",
         "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv"),
    ]
    n_diff = 0
    for pinned, live_rel in pairs:
        a = _load(PRE_DIR / pinned)
        b = _load(ROOT / live_rel)
        j = pd.concat([a.rename("a"), b.rename("b")], axis=1,
                      join="inner").dropna()
        dev = float((j.a - j.b).abs().max())
        if dev > 0:
            n_diff += 1
    assert n_diff >= 2, (
        "pinned pre-costfix blobs are byte-equal to the live sleeves — the "
        "pin no longer reflects the costfix divergence it was created for"
    )


def test_guard_trips_on_unpinned_drift():
    """The fail-closed guard must EXIT if an unpinned pool sleeve differs
    c745682 -> HEAD. Exercise it against a path we know drifted (a pinned
    sleeve's live path, declared unpinned here) — it must SystemExit."""
    spec = importlib.util.spec_from_file_location(
        "v2rebuild", str(ROOT / "campaign/scripts/"
                               "HUNT_TREASFUT_champion20y_v2_rebuild.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    drifted = mod.POOL20["QAxasts"]  # live path of a costfix-drifted sleeve
    mod.POOL20 = {"notpinned": drifted}  # declared unpinned on purpose
    mod.PINNED = {}
    with pytest.raises(SystemExit):
        mod.guard_unpinned_sleeves_unchanged(mod.git_root())


def test_pinned_blobs_match_git_c745682():
    """Every pinned blob must be byte-identical to the committed V2-era blob
    (git c745682) — protects against silent edits of pre_costfix_sleeves/."""
    spec = importlib.util.spec_from_file_location(
        "v2rebuild", str(ROOT / "campaign/scripts/"
                               "HUNT_TREASFUT_champion20y_v2_rebuild.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    gitroot = mod.git_root()
    for key, rel in mod.PINNED.items():
        pool_rel = mod.POOL20[key]
        r = subprocess.run(
            ["git", "show", f"c745682:software/world-trader/{pool_rel}"],
            cwd=gitroot, capture_output=True)
        assert r.returncode == 0, r.stderr
        on_disk = (mod.PRE_DIR / rel).read_bytes()
        assert on_disk == r.stdout, f"pinned blob for {key} != c745682 bytes"


def test_live_pool_still_breaks_committed_books():
    """Sanity: the LIVE (post-costfix) sleeves must still produce the known
    break on at least one V2 book — proves the divergence is real and this
    suite has teeth (if the campaign ever re-commits V2-era sleeves, this
    test's premise changes and it should be revisited)."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "campaign/scripts/champion20y_build.py"),
         "--verify"],
        capture_output=True, text=True, timeout=900, cwd=str(ROOT),
    )
    assert r.returncode == 0, r.stderr
    assert "DIFF" in r.stdout, (
        f"expected live-pool DIFF on committed V2 books, got:\n{r.stdout}"
    )
