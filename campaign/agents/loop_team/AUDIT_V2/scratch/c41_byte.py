#!/usr/bin/env python3
"""Byte-identity: working tree vs git HEAD for the 3 committed V2 files."""
import subprocess, hashlib
for v in ["SAFE", "BALANCED", "AGGRESSIVE"]:
    fn = f"campaign/results/GOAL100_HONEST13V2_{v}_daily.csv"
    wt = hashlib.sha256(open(fn,'rb').read()).hexdigest()
    gt = subprocess.run(["git", "show", f"HEAD:{fn}"], capture_output=True).stdout
    gh = hashlib.sha256(gt).hexdigest()
    print(f"{v}: worktree {wt[:16]}... git-HEAD {gh[:16]}... {'SAME' if wt==gh else 'DIFF'}")
