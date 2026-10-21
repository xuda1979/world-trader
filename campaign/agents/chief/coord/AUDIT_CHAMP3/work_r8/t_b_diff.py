#!/usr/bin/env python3
"""AUDIT_CHAMP3 TASK B: HEAD champion blob vs on-disk champion, day by day.
git root is /Users/daxu, so HEAD paths carry the software/world-trader/ prefix."""
import subprocess, os, io
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
REL  = "software/world-trader/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
DISK = os.path.join(ROOT, "campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
def git(*a): return subprocess.run(["git"]+list(a), cwd=ROOT, capture_output=True, text=True).stdout
head = git("show", "HEAD:" + REL).splitlines()
disk = open(DISK).read().splitlines()
hd = {l.split(",")[0]: l for l in head[1:]}
dd = {l.split(",")[0]: l for l in disk[1:]}
print("HEAD rows", len(hd), head[1].split(",")[0], "..", head[-1].split(",")[0])
print("DISK rows", len(dd), disk[1].split(",")[0], "..", disk[-1].split(",")[0])
print("only HEAD", sorted(set(hd)-set(dd)), "only DISK", sorted(set(dd)-set(hd)))
diff = [d for d in sorted(set(hd) & set(dd)) if hd[d] != dd[d]]
print("REWRITTEN", len(diff))
for d in diff:
    h = float(hd[d].split(",")[1]); k = float(dd[d].split(",")[1])
    print("  ", d, "HEAD=%.10g" % h, "DISK=%.10g" % k, "delta=%.4g" % abs(k-h))
def stats(txt, label):
    s = pd.read_csv(io.StringIO(txt), index_col=0, parse_dates=True).iloc[:, 0]
    nav = (1 + s).cumprod()
    print(label, "n=%d" % len(s), "cagr=%.4f%%" % (((1+s).prod()**(252/len(s))-1)*100), "sr=%.4f" % (s.mean()/s.std(ddof=1)*np.sqrt(252)), "mdd=%.4f%%" % ((nav/nav.cummax()-1).min()*100))
stats(chr(10).join(head), "HEAD")
stats(chr(10).join(disk), "DISK")
