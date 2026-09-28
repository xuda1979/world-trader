#!/usr/bin/env python3
"""CHAMPION20Y_V2 provenance repair — reproducible rebuild path (HUNT_TREASFUT R4).

WHY THIS EXISTS
---------------
R3/R4 forensics: commit b268e52 (2026-09-07, "champion costfix re-emit") re-emitted
3 of the 13 champion-pool sleeves (E1_QAxasts_tsmom189_2006, QA_dualmom_band121,
E1_brwt_spread_rev15_2000) under the full-|dW|@6.4bps cost convention. The committed
CHAMPION20Y_V2 books (d5fa3a2, 2026-09-01) were built from the PRE-costfix sleeve
bytes (git c745682 blobs). champion20y_build.py reads the live tree, so --verify
now DIFFs its own committed books (BAL 3.107e-03 / SAFE 6.160e-03 / AGGR 6.206e-03).

THE FINDING (TDD-verified, test_treasfut_r4_v2_rebuild.py)
----------------------------------------------------------
CHAMPION20Y_V2 is NOT unreproducible — it reproduces EXACTLY (<= 1e-16) from the
committed V2-era sleeve blobs. The canonical builder's math is fine; the tree
drifted under it. Proof: in a clean worktree at c745682 (ROOT repointed), the
UNMODIFIED builder verifies all 3 books:
    BALANCED  9.986e-17   SAFE  9.996e-17   AGGRESSIVE  9.991e-17

WHAT THIS SCRIPT DOES
---------------------
Reconstitutes the V2-era pool in a temp dir: the 3 pre-costfix blobs (extracted
from git c745682 into pre_costfix_sleeves/, sha256-checked vs the worktree at
build time) replace their live-tree counterparts; the other 10 sleeves are read
from the LIVE tree — legal because they are byte-identical c745682 -> HEAD
(verified this round via `git diff --shortstat c745682 HEAD -- <13 paths>`, and
re-checked fail-closed at every run below). construct()/main() logic is imported
VERBATIM from campaign/scripts/champion20y_build.py (single source of truth —
this script contains no math of its own).

Usage:
  python3 campaign/scripts/HUNT_TREASFUT_champion20y_v2_rebuild.py [--verify] [--outdir DIR]
    --verify          compare rebuilt vs the 3 committed books; exit 1 if any maxdev > 1e-12.
    default           write rebuilt books to --outdir (never touches the tree unless you
                      pass --outdir campaign/results explicitly).
  python3 -m pytest campaign/bt/tests/test_treasfut_r4_v2_rebuild.py   (TDD suite)

Re-check after any future sleeve re-emit:
  git diff --stat c745682 HEAD -- campaign/agents/*/sleeves campaign/results/sleeve_library
  If a 4th pool sleeve drifts, extract it into pre_costfix_sleeves/ the same way and
  extend PINNED below — the guard will refuse to run until you do.
"""
import argparse
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAIN_ROOT = HERE.parent.parent          # .../world-trader
PRE_DIR = (MAIN_ROOT / "campaign/agents/chief/coord/HUNT_TREASFUT/"
           "work_r4/pre_costfix_sleeves")
BAR = 1e-12

# pool sleeve (builder key) -> pinned pre-costfix file in PRE_DIR
PINNED = {
    "QAxasts": "E1_QAxasts_tsmom189_2006.csv",
    "dualmom": "QA_dualmom_band121.csv",
    "brwt": "E1_brwt_spread_rev15_2000.csv",
    # 2026-09-30: C5ngsum drifted (append-only E1_C5ng_summer_weekday refresh
    # +19 rows 2026-08-25..2026-09-21, DHHNGSP 9/30 fetch). Pinned per the
    # documented protocol (header above): extracted the PRE-EXTENSION blob
    # (= HEAD@2026-09-26, sha256 ccfe3a4bc8706161... tail 2026-08-24).
    "C5ngsum": "E1_C5ng_summer_weekday.csv",
}
POOL20 = {
    "A5r7":    "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
    "a6r7":    "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "A1inf":   "campaign/agents/E1_20yspan/sleeves/E1_A1inf_GLD_2006.csv",
    "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "A1credit": "campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
    "XGB1y":   "campaign/results/sleeve_library/XGB1y_deploy.csv",
    "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "brwt":    "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "B3momhml": "campaign/agents/B3_antiregime/ref_momhml_composite.csv",
    "C5ng":    "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "MHX":     "campaign/agents/COORD/sleeves/MHX_multihorizon_xgb.csv",
}
BOOKS = [
    "GOAL100_CHAMPION20Y_V2_BALANCED_daily.csv",
    "GOAL100_CHAMPION20Y_V2_SAFE_daily.csv",
    "GOAL100_CHAMPION20Y_V2_AGGRESSIVE_daily.csv",
]


def git_root() -> str:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       cwd=str(MAIN_ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"not a git work tree? {r.stderr}")
    return r.stdout.strip()


def guard_unpinned_sleeves_unchanged(gitroot: str) -> None:
    """Fail-closed: every pool sleeve NOT in PINNED must still be byte-identical
    to its V2-era blob (c745682). If one drifted, this rebuild path is silently
    wrong — refuse to run."""
    for key, rel in POOL20.items():
        if key in PINNED:
            continue
        r = subprocess.run(
            ["git", "diff", "--shortstat", "c745682", "HEAD", "--",
             f"software/world-trader/{rel}"],
            cwd=gitroot, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"git diff failed for {rel}: {r.stderr}")
        if r.stdout.strip():
            sys.exit(
                f"GUARD TRIPPED: pool sleeve '{key}' ({rel}) differs "
                f"c745682 -> HEAD but is not pinned in PINNED. Extend "
                f"pre_costfix_sleeves/ + PINNED from the new pre-drift blob, "
                f"then re-verify. git said: {r.stdout.strip()}")


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "champion20y_build",
        str(HERE / "champion20y_build.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def materialize_pool(tmp: Path, gitroot: str) -> dict:
    """Return a pool dict {key: relpath-from-ROOT} pointing at a temp tree that
    mirrors campaign/ layout, with PINNED entries swapped for the pre-costfix
    blobs and everything else copied (verbatim bytes) from the live tree."""
    for key, fn in PINNED.items():
        src = PRE_DIR / fn
        if not src.exists():
            sys.exit(f"pinned blob missing: {src}")
    pool = {}
    for key, rel in POOL20.items():
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if key in PINNED:
            shutil.copyfile(PRE_DIR / PINNED[key], dst)
        else:
            shutil.copyfile(MAIN_ROOT / rel, dst)
        pool[key] = rel
    return pool


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    gitroot = git_root()
    guard_unpinned_sleeves_unchanged(gitroot)

    import pandas as pd  # after guard, so failures are provenance failures
    b = load_builder()

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        materialize_pool(tmp, gitroot)
        # point the imported builder at the temp tree
        b.ROOT = str(tmp)
        b.POOL20 = materialize_pool(tmp, gitroot)
        A = b.construct(b.POOL20, 0.090, 0.030, "2006-10-01")
        B = b.construct(b.POOL20, 0.106, 0.0255, "2006-10-01")
        BAL = ((A + B) / 2).dropna()
        rebuilt = {
            "GOAL100_CHAMPION20Y_V2_BALANCED_daily.csv": BAL,
            "GOAL100_CHAMPION20Y_V2_SAFE_daily.csv": A,
            "GOAL100_CHAMPION20Y_V2_AGGRESSIVE_daily.csv": B,
        }
        worst = 0.0
        for fn, r in rebuilt.items():
            out = tmp / fn
            r.to_frame("ret").to_csv(out)
            if args.verify:
                old = pd.read_csv(MAIN_ROOT / "campaign/results" / fn,
                                  index_col=0, parse_dates=True).iloc[:, 0]
                j = pd.concat([old.rename("old"), r.rename("new")],
                              axis=1, join="inner").dropna()
                md = float((j.old - j.new).abs().max())
                worst = max(worst, md)
                print(f"{fn}: max|rebuilt-committed| = {md:.3e}  "
                      f"{'IDENTICAL' if md <= BAR else 'DIFF'} (n={len(j)})")
            if args.outdir:
                dest = Path(args.outdir)
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(out, dest / fn)
                print(f"copied -> {dest / fn}")
    if args.verify:
        if worst > BAR:
            print(f"VERIFY FAILED: worst maxdev {worst:.3e} > {BAR:.0e}")
            return 1
        print(f"VERIFY OK: all 3 books <= {BAR:.0e} (worst {worst:.3e})")
    else:
        print("wrote rebuilt books (pass --verify to compare against committed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
