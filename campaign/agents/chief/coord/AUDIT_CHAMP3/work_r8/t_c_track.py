#!/usr/bin/env python3
"""AUDIT_CHAMP3 TASK C: batch-9 tracking / freshness gate."""
import subprocess, os
ROOT = "/Users/daxu/software/world-trader"
def git(*a): return subprocess.run(["git"]+list(a), cwd=ROOT, capture_output=True, text=True)
SUBS = ["tools/quant/data/cboe_hist", "tools/quant/data/bund_daily", "tools/quant/data/em_rates", "tools/quant/sources", "tools/quant/data"]
for s in SUBS:
    cp = git("ls-files", s)
    files = [l for l in cp.stdout.splitlines() if l]
    ci = git("check-ignore", "-v", s)
    print("%-30s tracked=%d ignored_rc=%d rule=%s" % (s, len(files), ci.returncode, (ci.stdout.strip() or "-")))
    for f in files: print("      ", f)
    if not files: print("       (none tracked)")
cp = git("status", "--porcelain", "--untracked-files=all", "tools/quant/sources")
print("--- git status --porcelain tools/quant/sources ---")
print(cp.stdout.strip())
for i, l in enumerate(open(os.path.join(ROOT, ".gitignore")).read().splitlines(), 1): print("%3d| %s" % (i, l))
