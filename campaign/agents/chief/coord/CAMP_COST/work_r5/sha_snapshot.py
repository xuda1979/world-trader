#!/usr/bin/env python3
"""R5 guard: sha256 snapshot of champion-of-record artifacts + all 13 sleeve inputs.
Usage: python3 sha_snapshot.py <outfile.json>
Round-start / end-of-round comparison for byte-stability (charter R5-a).
"""
import hashlib, json, sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/scripts')
from rawew13v2_build import PATHS, NAMES

ROOT = "/Users/daxu/software/world-trader"
ARTIFACTS = {
    "champion_csv": "campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
    "weights_csv":  "campaign/results/RAWEW13v2_IS_SR_weights.csv",
    "builder":      "campaign/scripts/rawew13v2_build.py",
}

def sha16(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]

out = {}
for k, rel in ARTIFACTS.items():
    out[k] = {"path": rel, "sha256_16": sha16(f"{ROOT}/{rel}")}
for n in NAMES:
    rel = PATHS[n]
    out[f"sleeve:{n}"] = {"path": rel, "sha256_16": sha16(f"{ROOT}/{rel}")}

if len(sys.argv) > 1:
    with open(sys.argv[1], 'w') as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print(f"wrote {sys.argv[1]}")
for k in sorted(out):
    print(f"{out[k]['sha256_16']}  {k}  {out[k]['path']}")
