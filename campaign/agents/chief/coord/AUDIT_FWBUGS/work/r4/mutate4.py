"""AUDIT_FWBUGS R4 mutant-injection harness (rebuild on R2's mutate3.py design).

v4 deltas vs mutate3.py (why a rebuild, not reuse):
  - R3's pins (test_fwbugs_audit_r3*.py) hardcode the LIVE campaign path into sys.path[0].
    In a v3 sandbox that sys.path entry still resolves to the LIVE tree, so a test could
    import the UNMUTATED bt and fake a pass. v4 LAUNDERS every hardcoded live path inside
    the sandboxed test files (live campaign dir -> sandbox campaign dir) and SELFCHECKS the
    laundering by planting a `raise RuntimeError('SANDBOX ACTIVE')` sentinel.
  - Sandboxes the WHOLE campaign/ tree (symlinks for results/ + agents/ so the 136M of CSVs
    are not copied) — no skip-list needed; sys.path[0]-style absolute hacks resolve inside.
  - v3 matched mutants to single test files; v4's verdict is CROSS-SUITE: baseline
    (unmutated sandbox) vs mutated sandbox, whole bt/tests dir, new failures = killed.

Usage:  python3 mutate4.py            # full registry, cross-suite verdicts
        python3 mutate4.py <ID>       # one mutant, verbose (prints pytest output)
        python3 mutate4.py --selfcheck-only
"""
import os
import shutil
import subprocess
import sys
import tempfile

WROOT = "/Users/daxu/software/world-trader"
CAMP = f"{WROOT}/campaign"
LIVE = CAMP  # the literal string hardcoded in some test files' sys.path.insert calls

SYMLINK_DIRS = ("results", "agents", "data")   # big / agent-owned: symlink, never copy
COPY_DIRS = ("bt", "scripts")                  # framework + builder chain: real copies


# ------------------------------------------------------------- M22-family mutant registry
# shipped max_dd (campaign/bt/metrics.py:41-43):
#     def max_dd(r: pd.Series) -> float:
#         eq = (1 + r).cumprod()
#         return float((eq / eq.cummax() - 1).min()) if len(r) else np.nan
# Each mutation returns (new_source, applied_bool) on the file's full text.
def _mk(old, new):
    def f(s):
        t = s.replace(old, new)
        return t, t != s
    return f


MUTANTS = [
    ("M22a_literal_nanwrite", _mk(
        "    eq = (1 + r).cumprod()\n    return float((eq / eq.cummax() - 1).min())",
        "    eq = (1 + r).cumprod()\n    eq[r.isna()] = np.nan\n"
        "    return float((eq / eq.cummax() - 1).min())")),
    ("M22b_dropna_compress", _mk(
        "    eq = (1 + r).cumprod()\n    return float((eq / eq.cummax() - 1).min())",
        "    r = r.dropna()\n    eq = (1 + r).cumprod()\n"
        "    return float((eq / eq.cummax() - 1).min())")),
    ("M22d_any_nan_zero", _mk(
        "    eq = (1 + r).cumprod()\n    return float((eq / eq.cummax() - 1).min())",
        "    if r.isna().any():\n        return 0.0\n"
        "    eq = (1 + r).cumprod()\n    return float((eq / eq.cummax() - 1).min())")),
    ("M22e_min_skipna_false", _mk(
        "    return float((eq / eq.cummax() - 1).min()) if len(r) else np.nan",
        "    return float((eq / eq.cummax() - 1).min(skipna=False)) if len(r) else np.nan")),
    ("M22f_cumprod_skipna_false", _mk(
        "    eq = (1 + r).cumprod()\n    return float((eq / eq.cummax() - 1).min())",
        "    eq = (1 + r).cumprod(skipna=False)\n"
        "    return float((eq / eq.cummax() - 1).min()) if len(r) else np.nan")),
    # regression guards: R1/R2 metrics mutants must stay caught by the (now larger) suite
    ("M3_negyears_failopen", _mk(
        "    yr = yr.where(np.isfinite(yr), -1.0)",
        "    pass  # MUTATED: neg_years fail-open")),
    ("M20_sharpe_const_nan", _mk(
        "    if not s or not np.isfinite(s) or s < 1e-12:\n        return 0.0",
        "    pass  # MUTATED: constant series -> divide by zero")),
    ("M21_halfsplit_offby1", _mk(
        "    k = len(r) // 2", "    k = (len(r) + 1) // 2")),
]


def make_sandbox(td, sentinel_file=None):
    """campaign/ MIRROR copy: td/campaign/{bt,scripts} real, results/agents/data
    symlinked, plus td/tools symlink (test_camp_short_r4_lsfix computes ROOT 4 levels up,
    i.e. the WROOT level, and imports tools/quant/hedge_fund_strats). Hardcoded LIVE paths
    in test files are laundered to the sandbox."""
    camp = f"{td}/campaign"
    os.makedirs(camp, exist_ok=True)
    for d in COPY_DIRS:
        shutil.copytree(f"{CAMP}/{d}", f"{camp}/{d}",
                        ignore=shutil.ignore_patterns("__pycache__"))
    for d in SYMLINK_DIRS:
        src = f"{CAMP}/{d}"
        if os.path.exists(src):
            os.symlink(src, f"{camp}/{d}")
    if os.path.exists(f"{WROOT}/tools"):
        os.symlink(f"{WROOT}/tools", f"{td}/tools")
    # git toplevel is /Users/daxu (home IS the repo; world-trader has no .git of its
    # own), so a sandbox in /var/folders has no .git and
    # test_treasfut_r4_v2_rebuild.py::test_pinned_blobs_match_git_c745682
    # (read-only: rev-parse / show c745682 / diff c745682 HEAD) BASELINE-FAILs.
    # Expose the real object DB read-only instead of excluding the file - exclusion
    # would weaken the cross-suite verdict. All git ops used are object-DB reads; none
    # consult the (live) worktree, so sandbox isolation of bt/ is unaffected.
    GITDIR = "/Users/daxu/.git"
    if os.path.exists(GITDIR) and not os.path.exists(f"{td}/.git"):
        os.symlink(GITDIR, f"{td}/.git")
    # strip all pyc caches anywhere in the copied trees
    for root, dirs, files in os.walk(td):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))
    # LAUNDER hardcoded live paths in every test file -> sandbox paths
    laundered = []
    for root, _dirs, files in os.walk(f"{camp}/bt/tests"):
        for fn in files:
            if not (fn.startswith("test_") and fn.endswith(".py")) and fn != "conftest.py":
                continue
            p = os.path.join(root, fn)
            s = open(p).read()
            if LIVE in s:
                open(p, "w").write(s.replace(LIVE, camp))
                laundered.append(fn)
    return laundered


def run_pytest(td, tag):
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-rf",
         "-p", "no:cacheprovider", f"{td}/campaign/bt/tests/"],
        capture_output=True, text=True, cwd=td, timeout=2400)
    out = r.stdout + r.stderr
    fails = set()
    for ln in out.splitlines():
        if ln.startswith("FAILED "):
            t = ln.split("FAILED ", 1)[1].split()[0]
            if "::" in t:
                f, n = t.rsplit("::", 1)
                fails.add(f.rsplit("/", 1)[-1] + "::" + n)
    return r.returncode, fails, out


def selfcheck():
    """Prove (1) sandbox isolation: a poisoned metrics.py propagates; (2) path laundering:
    a test file's sys.path hack resolves INSIDE the sandbox (poison detected, not live)."""
    with tempfile.TemporaryDirectory() as td:
        laundered = make_sandbox(td)
        # poison metrics and confirm the sandboxed suite blows up (not silently green).
        # Insert AFTER line 1: prepending before `from __future__ import annotations`
        # is a SyntaxError, which would prove isolation only accidentally.
        mp = f"{td}/campaign/bt/metrics.py"
        s = open(mp).read()
        lines = s.splitlines(keepends=True)
        fut = next(i for i, ln in enumerate(lines)
                   if ln.startswith("from __future__"))
        lines.insert(fut + 1, "raise RuntimeError('SANDBOX ACTIVE')\n")
        open(mp, "w").write("".join(lines))
        rc, _fails, out = run_pytest(td, "selfcheck-poison")
        iso_ok = "SANDBOX ACTIVE" in out
        # laundering probe: does ANY sandboxed test file still reference the live path?
        live_refs = []
        for root, _d, files in os.walk(f"{td}/campaign/bt/tests"):
            for fn in files:
                if fn.endswith(".py"):
                    t = open(os.path.join(root, fn)).read()
                    if LIVE in t:
                        live_refs.append(fn)
        return {"isolation_ok": iso_ok, "laundered": laundered,
                "live_refs_remaining": live_refs}


def run_one(mid, verbose=False):
    """Verdict = mutant INTRODUCED failures vs the same sandbox's baseline (cross-suite).
    A non-zero baseline (e.g. a concurrent fleet agent's in-flight RED in an unrelated
    doc-scan test) no longer aborts the run: such tests are orthogonal to the mutation,
    and the fails1-fails0 diff isolates exactly what the mutant killed. Baseline failures
    are reported so a baseline that HIDES a kill (mutant 'fixes' a baseline failure) is
    still visible: that shows up as fails0-fails1 and is flagged BASELINE-SENSITIVE."""
    fn = dict((m[0], m[1]) for m in MUTANTS)[mid]
    with tempfile.TemporaryDirectory() as td:
        make_sandbox(td)
        rc0, fails0, _ = run_pytest(td, f"{mid}-baseline")
        mp = f"{td}/campaign/bt/metrics.py"
        s = open(mp).read()
        s2, applied = fn(s)
        if not applied:
            return "MUTATION_DID_NOT_APPLY", [], "", sorted(fails0)
        open(mp, "w").write(s2)
        rc1, fails1, out = run_pytest(td, mid)
        new = sorted(fails1 - fails0)
        gone = sorted(fails0 - fails1)
        if new:
            verdict = "CAUGHT"
        elif gone:
            verdict = "BASELINE-SENSITIVE"
        elif fails0:
            verdict = "VACUOUS(+BASELINE-NOISE)"
        else:
            verdict = "VACUOUS"
        if verbose:
            print(out[-3000:])
        return verdict, new, out, sorted(fails0)


def main():
    if "--selfcheck-only" in sys.argv:
        print(selfcheck())
        return
    sc = selfcheck()
    print(f"SELFCHECK isolation={sc['isolation_ok']} "
          f"laundered={len(sc['laundered'])}files "
          f"live_refs_remaining={sc['live_refs_remaining']}", flush=True)
    if not sc["isolation_ok"] or sc["live_refs_remaining"]:
        print("HARNESS BROKEN — aborting")
        sys.exit(2)
    args = [a for a in sys.argv[1:] if a != "--cross"]
    only = args[0] if args else None
    n_vac = 0
    for mid, _fn in MUTANTS:
        if only and only not in mid:
            continue
        verdict, new, out = run_one(mid)[:3]
        if verdict in ("VACUOUS", "MUTATION_DID_NOT_APPLY", "BASELINE-FAIL"):
            n_vac += 1
        print(f"{verdict:24s} {mid:28s} | {new if new else ''}", flush=True)
    print(f"\nPROBLEM count (VACUOUS+DID_NOT_APPLY+BASELINE-FAIL): {n_vac}")


if __name__ == "__main__":
    main()
