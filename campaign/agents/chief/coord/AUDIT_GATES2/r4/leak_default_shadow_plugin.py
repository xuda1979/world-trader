"""AUDIT_GATES2 R4 — SHADOW EXPERIMENT: leak_check DEFAULT-ON migration-cost measurement.

Question (charter R4): should bt.gates.run's leak gate flip from opt-in to DEFAULT-on?
Method: measure the blast radius WITHOUT touching bt/gates.py — a pytest plugin patches
bt.gates.run so that, when the caller did not pass leak_check explicitly, the call is made
with leak_check=True. pytest_configure runs before test modules are collected/imported, so
every `from bt.gates import run` in the suite sees the patched callable.

Run:
  cd /Users/daxu/software/world-trader
  python3 -m pytest campaign/bt/tests -q \
      -p campaign.agents.chief.coord.AUDIT_GATES2.r4.leak_default_shadow_plugin
(The -p module path requires the repo root on sys.path — conftest.py does that; for -p the
plugin is imported by fully-qualified name after rootdir insertion, which pytest does.)

Read the failures: each one is a test that PINS default-OFF semantics and must be
consciously migrated when the flip is ratified. Zero failures on a test means that test is
indifferent to the flip.
"""
from __future__ import annotations

import os
import sys

# pytest imports -p plugins BEFORE rootdir conftest.py runs, so bootstrap the path that
# conftest.py would have added (the `campaign` dir, 5 levels up from this file).
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[os.pardir] * 5))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import bt.gates as _G

_orig_run = _G.run
PATCHED = {"n": 0}


def run_leak_default_on(*args, **kw):
    if "leak_check" not in kw:
        kw["leak_check"] = True
        PATCHED["n"] += 1
    return _orig_run(*args, **kw)


def pytest_configure(config):
    _G.run = run_leak_default_on
    # rebind any symbol already imported into bt's package namespace map (bt/__init__ imports
    # the MODULE bt.gates, not the function, so module attr rebinding is sufficient)


def pytest_sessionfinish(session, exitstatus):
    tr = getattr(session.config, "_pluginmanager", None)
    print(f"\nSHADOW: leak_check default applied to {PATCHED['n']} run() calls that did not "
          f"pass it explicitly")
