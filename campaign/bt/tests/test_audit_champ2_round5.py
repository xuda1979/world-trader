"""AUDIT_CHAMP2 ROUND 5 (b) — champion_card.py bare-invocation footgun.

R4 finding (FINDINGS.md flags item 2): campaign/scripts/champion_card.py line 23 does
`from scripts.rawew13v2_build import ...`, which only resolves when the CWD (or
PYTHONPATH) contains the `campaign/` package parent — i.e. it requires
`PYTHONPATH=campaign` (or cwd=world-trader with campaign on sys.path). Bare
`python3 campaign/scripts/champion_card.py` from anywhere else crashes with
ModuleNotFoundError AFTER the file has already been fully resolved, which means the
card-reproduce step in CHAMPION_CARD.md fails for any cold replicator who follows the
docstring literally.

The fix contract: the generator must be runnable from ANY cwd with a CLEAN
environment (no PYTHONPATH reliance), because a docstring is not an environment.
Byte-identity with the committed card is already pinned by
test_audit_champ2_round3.py::test_c_...; this module only pins INVOCABILITY.
"""
import os
import subprocess
import sys

ROOT = "/Users/daxu/software/world-trader"
CARD = f"{ROOT}/campaign/CHAMPION_CARD.md"
GEN = f"{ROOT}/campaign/scripts/champion_card.py"


def _clean_env():
    env = {
        k: v for k, v in os.environ.items()
        if k not in ("PYTHONPATH", "PYTHONSTARTUP")
    }
    return env


def test_card_generator_runs_bare_from_repo_root_without_pythonpath():
    """RED 2026-09-08: ModuleNotFoundError: No module named 'scripts'."""
    r = subprocess.run(
        [sys.executable, "campaign/scripts/champion_card.py", "--stdout"],
        cwd=ROOT, env=_clean_env(), capture_output=True, text=True)
    assert r.returncode == 0, (
        f"bare invocation failed rc={r.returncode}\nSTDERR:\n{r.stderr[-2000:]}")
    assert r.stdout.startswith("# GOAL100 CHAMPION CARD"), (
        f"unexpected stdout head: {r.stdout[:200]!r}")


def test_card_generator_runs_bare_from_tmp_cwd_without_pythonpath():
    """Harsher face: cwd NOT on any path that contains campaign/ (tmp), env clean.
    The generator must self-locate, not depend on the caller's cwd."""
    r = subprocess.run(
        [sys.executable, GEN, "--stdout"],
        cwd="/tmp", env=_clean_env(), capture_output=True, text=True)
    assert r.returncode == 0, (
        f"tmp-cwd invocation failed rc={r.returncode}\nSTDERR:\n{r.stderr[-2000:]}")
    assert r.stdout.startswith("# GOAL100 CHAMPION CARD"), (
        f"unexpected stdout head: {r.stdout[:200]!r}")


def test_card_generator_stdout_matches_committed_card_from_clean_env():
    """The clean-env stdout must stay byte-identical to the committed card —
    the fix must not change the artifact, only the invocability."""
    r = subprocess.run(
        [sys.executable, GEN, "--stdout"],
        cwd="/tmp", env=_clean_env(), capture_output=True, text=True)
    assert r.returncode == 0
    committed = open(CARD, "rb").read()
    assert r.stdout.encode() == committed, (
        "clean-env regeneration is not byte-identical to the committed card")
