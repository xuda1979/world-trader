#!/usr/bin/env python3
"""R6(a) RED-run driver: execute tests_tdd_r6.py against the HEAD (pre-fix)
wt.sources.nasdaq_history WITHOUT touching the working tree.

Why this exists: the working tree's tools/wt/sources.py already carries the R6(a)
fix (from the interrupted first half of this round) PLUS unrelated concurrent
hunks from other agents (kr_history, _stooq_symbol, polygon date normalization)
that must not be disturbed or attributed to this round. So the RED side of the
TDD sequence is demonstrated by exec'ing `git show HEAD:./tools/wt/sources.py`
into a fresh module object registered as wt.sources, then running the same test
file in-process via pytest.main.

Expected RED result: 2 passed (the healthy-window regression guards pass under
both semantics BY DESIGN - a fix may not change healthy behavior), 3 failed
(the defect tests). Expected GREEN result (working-tree module): 5 passed.

Run: python3 red_run_head.py    # from anywhere; paths are absolute
"""
import subprocess
import sys
import types

ROOT = "/Users/daxu/software/world-trader"
TESTS = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/tests_tdd_r6.py"

head_src = subprocess.run(
    ["git", "show", "HEAD:./tools/wt/sources.py"],
    cwd=ROOT, capture_output=True, text=True, check=True).stdout

pkg = types.ModuleType("wt")
pkg.__path__ = [f"{ROOT}/tools/wt"]
pkg.__package__ = "wt"
sys.modules["wt"] = pkg

mod = types.ModuleType("wt.sources")
mod.__file__ = f"{ROOT}/tools/wt/_head_sources.py (git HEAD, exec'd, not on disk)"
mod.__package__ = "wt"
exec(compile(head_src, "_head_sources.py", "exec"), mod.__dict__)
sys.modules["wt.sources"] = mod

print("=" * 100)
print("RED RUN: tests_tdd_r6.py against HEAD sources.py (defect present, fix absent)")
print("module under test:", mod.__file__)
print("=" * 100)

import pytest  # noqa: E402
rc = pytest.main(["-q", "-p", "no:cacheprovider", TESTS])
print(f"\nRED RUN pytest exit code: {rc} (expected 1 = failures present)")
sys.exit(0 if rc == 1 else 2)
