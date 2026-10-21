#!/usr/bin/env python3
"""AUDIT_CHAMP2 R7 (a): seeded spot-check of AUDIT_FWBUGS R6 commit-wave appendix.
Seed 20260908, sample 20 rows from commit_wave_appendix.txt; verify each path
EXISTS on disk and its git classification (MODIFIED/UNTRACKED) matches the appendix.
Also exhaustively verifies ALL 31 MODIFIED rows and diffs the MODIFIED set vs live git.
Run: python3 r7_spotcheck.py  (from anywhere; absolute ROOT below)."""
import random, subprocess, os
ROOT = "/Users/daxu/software/world-trader"
APP = f"{ROOT}/campaign/agents/chief/coord/AUDIT_FWBUGS/work_r6/commit_wave_appendix.txt"
random.seed(20260908)  # RECORDED SEED
os.chdir(ROOT)

lines = [l.rstrip('\n') for l in open(APP) if l.startswith(('MODIFIED\t', 'UNTRACKED\t'))]
print('appendix rows:', len(lines))

def gitcls(p):
    out = subprocess.run(['git', 'status', '--porcelain', '-uall', '--', p],
                         capture_output=True, text=True).stdout.strip()
    if not out:
        return 'CLEAN-TRACKED' if subprocess.run(
            ['git', 'ls-files', '--error-unmatch', p], capture_output=True).returncode == 0 \
            else 'MISSING'
    return 'MODIFIED' if out.split()[0] in ('M', 'MM', 'AM') else 'UNTRACKED'

def norm(rel):
    # normalize repo-root-relative (porcelain at /Users/daxu) vs appendix
    # ('software/world-trader/...' prefix from its own cwd) to 'campaign/...'
    return rel.split('world-trader/', 1)[1] if 'world-trader/' in rel else rel

def path_of(row):
    return norm(row.split('\t', 1)[1])

sample = random.sample(lines, 20)
ok = 0
for row in sample:
    cls, p = row.split('\t', 1)[0], path_of(row)
    exists = os.path.exists(p)
    g = gitcls(p)
    v = 'OK' if (exists and g in (cls, 'CLEAN-TRACKED')) else 'MISMATCH'
    ok += v == 'OK'
    print(f"{v:8s} {cls:9s} git_now={g:13s} exists={exists} {p}")
print(f"SEED=20260908 sample=20 ok={ok} mismatch={20-ok}")

mod = [l for l in lines if l.startswith('MODIFIED\t')]
okm = sum(1 for row in mod if os.path.exists(path_of(row)) and gitcls(path_of(row)) == 'MODIFIED')
print(f"exhaustive MODIFIED rows: {okm}/{len(mod)} tracked+modified now")

r = subprocess.run(['git', 'status', '--porcelain', '-uall', '--', 'campaign/'],
                   capture_output=True, text=True)
cur = [norm(l[3:]) for l in r.stdout.splitlines() if l.split()[0] in ('M', 'MM', 'AM')]
appset = {path_of(l) for l in mod}
curset = {c for c in cur}
print('live tracked-modified under campaign/:', len(curset))
print('modified now but NOT in appendix-MODIFIED:', sorted(curset - appset))
print('appendix-MODIFIED but NOT modified now:', sorted(appset - curset))
