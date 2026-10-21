"""Run a grid of (G, WD, EPOCHS, D_MODEL) configs, each over N seeds via
subprocess (fresh env per config), and rank by mean OOS Sharpe.
Compares against the 35-feature baseline.
"""
import os, subprocess, re

GRID = [
    {"G": "0.15"},
    {"G": "0.25"},   # baseline
    {"G": "0.35"},
    {"G": "0.20"},
    {"G": "0.30"},
    {"G": "0.25", "WD": "1e-3"},
    {"G": "0.25", "WD": "1e-4"},
    {"G": "0.25", "EPOCHS": "40"},
    {"G": "0.25", "EPOCHS": "80"},
    {"G": "0.25", "PATIENCE": "40"},
]
SEEDS = os.environ.get("SEEDS", "0 1 2").split()
HERE = os.path.dirname(os.path.abspath(__file__))
results = []

for cfg in GRID:
    srs = []
    for s in SEEDS:
        env = dict(os.environ)
        env.update(cfg)
        env["SEEDS"] = s
        out = subprocess.run(["python3", "run_multiseed.py"],
                             env=env, cwd=HERE,
                             capture_output=True, text=True, timeout=300)
        # parse "seed X: OOS Sharpe = Y"
        m = re.search(r"seed \d+: OOS Sharpe = ([-\d.]+)", out.stdout)
        srs.append(float(m.group(1)) if m else float("nan"))
    mean = float(sum(srs)/len(srs))
    results.append((mean, srs, dict(cfg)))
    print(f"{dict(cfg)}  -> mean SR {mean:.3f}  {[round(x,2) for x in srs]}", flush=True)

print("\n=== RANKED ===")
for mean, srs, cfg in sorted(results, key=lambda x: -x[0]):
    print(f"  {cfg}: mean {mean:.3f}  {[round(x,2) for x in srs]}")
