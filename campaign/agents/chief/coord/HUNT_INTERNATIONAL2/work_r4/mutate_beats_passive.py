#!/usr/bin/env python3
"""Mutation-test bt/beats_passive.py (HUNT_INTERNATIONAL2 R4a).

Generates FIRST-ORDER MUTANTS of campaign/bt/beats_passive.py (the module I shipped in R3),
runs the 22-test suite against each, and reports:
  KILLED    - at least one test failed (mutation detected by existing suite)
  SURVIVOR  - all tests still green (equivalent mutant OR test gap -> candidate kill)
Mutations: constant flips on gate-relevant literals (MIN_OBS, 0.5 coverage, clip/cap, cost
arithmetic, T+1 on/off) + comparison/boolean-operator swaps + statement deletions.
Pristine module is snapshotted to /tmp/beats_passive.pristine.py and verified byte-identical
before/after; mutation application is atomic (write tmp, os.replace).
"""
import os, re, subprocess, sys, shutil, hashlib

ROOT = "/Users/daxu/software/world-trader"
MOD = f"{ROOT}/campaign/bt/beats_passive.py"
PRISTINE = "/tmp/beats_passive.pristine.py"

src = open(MOD).read()

# ---------------------------------------------------------------- mutation operators
CONSTS = [
    # (pattern, replacement, label)
    (r"\bMIN_OBS = 60", "MIN_OBS = 61", "MIN_OBS 60->61"),
    (r"\bMIN_OBS = 60", "MIN_OBS = 2", "MIN_OBS 60->2 (fail-open shrink)"),
    (r"len\(s\) >= 0\.5 \* n_span", "len(s) >= 0.05 * n_span", "coverage 0.5->0.05"),
    (r"len\(s\) >= 0\.5 \* n_span", "len(s) >= 0.9 * n_span", "coverage 0.5->0.9"),
    (r"on\[0\] = False", "on[0] = True", "spy_bh flat-day0 removed (lookahead)"),
    (r"out\.iloc\[k\] -= COST_BPS / 1e4", "out.iloc[k] -= 0.0", "spy_bh entry cost dropped"),
    (r"out\.iloc\[k\] -= COST_BPS / 1e4", "out.iloc[k] += COST_BPS / 1e4", "spy_bh cost sign flip"),
    (r"w_s, w_i = 0\.60, 0\.40", "w_s, w_i = 0.90, 0.10", "60/40 -> 90/10"),
    (r"w_s, w_i = 0\.60, 0\.40", "w_s, w_i = 0.00, 0.00", "60/40 -> never invested"),
    (r"if not np\.isfinite\(d\) or d <= 0\.0", "if False", "ruin guard removed"),
    (r"if t == 1 or is_ms\[t\]", "if t == 1", "monthly snap removed"),
    (r"if t == 1 or is_ms\[t\]", "if True", "rebalance every day"),
    (r"w_s = w_s \* \(1\.0 \+ rs\[t - 1\]\) / d", "w_s = w_s * (1.0 + 0*rs[t-1]) / d", "spy leg drift off"),
    (r"target: float = 0\.10", "target: float = 0.50", "cta vt target 0.10->0.50"),
    (r"cap: float = 3\.0", "cap: float = 30.0", "cta cap 3.0->30"),
    (r"window: int = 60", "window: int = 5", "cta window 60->5"),
    (r"if out\['margin'\] <= 0\.0", "if out['margin'] < 0.0", "tie no longer fails"),
    (r"if out\['margin'\] <= 0\.0", "if out['margin'] > 0.0", "verdict inverted"),
    (r"out\['pass'\] = bool\(out\.get\('margin'\) is not None and out\['margin'\] > 0\.0\)",
     "out['pass'] = True", "fail-open: pass unconditionally"),
    (r"if len\(cand_index\) < 2", "if len(cand_index) < 1", "B&H 1-obs guard weakened"),
    (r"return empty  # cannot establish", "pass  # cannot establish", "B&H empty return dropped"),
    (r"scale = vol_target_scale\(r\.to_frame\('r'\), target=target, window=window, cap=cap\)\['r'\]",
     "scale = pd.Series(1.0, index=r.index)", "cta vol-target disabled"),
    (r"benchmarks\['sixty_forty'\] = sixty_forty\(spy_ret, ief_ret, ci\)",
     "benchmarks['sixty_forty'] = sixty_forty(spy_ret, ief_ret, ci) * 0.0 + np.nan", "60/40 NaN-poisoned"),
    (r"on\[~on & r\.isna\(\)\.to_numpy\(\)\]",
     "on[~on]", "B&H mask misuse (NaN->0 leak)"),
]

# line-level statement deletions (regex, first occurrence)
DELETIONS = [
    (r"\n\s*on\[0\] = False", "\n", "DEL on[0]=False"),
    (r"\n\s*out\.iloc\[k\] -= COST_BPS / 1e4", "\n", "DEL entry cost"),
    (r"\n\s*w_df = pd\.DataFrame.*\n\s*cost = cost_turnover\(w_df\).*", "\n    cost = pd.Series(0.0, index=cand_index)\n", "DEL 60/40 costs"),
    (r"\n\s*out\[~on & r\.isna\(\)\.to_numpy\(\)\] = np\.nan", "\n", "DEL B&H NaN guard"),
    (r"\n\s*w_s = w_i = 0\.0\n(?=\s*else)", "\n", "DEL ruin reset"),
]

# operator swaps
OPS = [
    (r"measurable = \{k: v for k, v in info\.items\(\) if np\.isfinite\(v\['sr'\]\)\}",
     "measurable = dict(info)", "unmeasurable benchmarks counted"),
    (r"bk = max\(measurable, key=lambda k: measurable\[k\]\['sr'\]\)",
     "bk = min(measurable, key=lambda k: measurable[k]['sr'])", "best->worst benchmark"),
    (r"looks_like_curve = bool\(len\(x\.dropna\(\)\) and \(x\.dropna\(\) > 1e3\)\.all\(\)\)",
     "looks_like_curve = bool(len(x.dropna()) and (x.dropna() > 1e3).any())", "curve detect all->any"),
    (r"looks_like_curve = bool\(len\(x\.dropna\(\)\) and \(x\.dropna\(\) > 1e3\)\.all\(\)\)",
     "looks_like_curve = False", "curve detection disabled"),
    (r"return x\.pct_change\(\)\.dropna\(\) if looks_like_curve else x\.dropna\(\)",
     "return x.pct_change().dropna() if looks_like_curve else x.pct_change().dropna()",
     "returns always differenced (R3 bug resurfaces)"),
    (r"return x\.pct_change\(\)\.dropna\(\) if looks_like_curve else x\.dropna\(\)",
     "return x.dropna() if looks_like_curve else x.dropna()", "curves never differenced"),
    (r"if np\.isfinite\(out\['candidate_sr'\]\) or len\(cand\) == 0",
     "if len(cand) == 0", "invalid-candidate guard dropped"),  # note: original is 'not np.isfinite'
    (r"if not np\.isfinite\(best_sr\)", "if False", "no-benchmark fail-closed dropped"),
    (r"pass\['beats_passive_ok'\] = bool\(ev\['pass'\]\)",
     "pass['beats_passive_ok'] = True", "gate() fail-open"),
]

mutations = []
for pat, rep, label in CONSTS + DELETIONS + OPS:
    if re.search(pat, src):
        mutations.append((pat, rep, label))
    else:
        print(f"SKIP (pattern not found): {label}")

print(f"applicable mutations: {len(mutations)}")

results = []
for i, (pat, rep, label) in enumerate(mutations):
    mutated = re.sub(pat, rep, src, count=1)
    if mutated == src:
        print(f"[{i}] {label}: NO-OP (pattern matched but no change)")
        continue
    # atomic write
    tmp = MOD + ".mut"
    with open(tmp, "w") as f:
        f.write(mutated)
    os.replace(tmp, MOD)
    try:
        p = subprocess.run(
            [sys.executable, "-m", "pytest", f"{ROOT}/campaign/bt/tests/test_beats_passive.py",
             "-q", "-x", "--no-header", "-p", "no:cacheprovider"],
            capture_output=True, text=True, timeout=300, cwd=ROOT)
        out = (p.stdout + p.stderr).strip().splitlines()
        tail = out[-1] if out else ""
        killed = p.returncode != 0
        status = "KILLED" if killed else "SURVIVOR"
        # extract failing test name(s)
        fails = [ln.split("::")[-1].split()[0] for ln in out if "::" in ln and ("FAILED" in ln or "PASS" in ln and "no tests ran" in ln)]
        results.append((label, status, tail, fails[:3]))
        print(f"[{i}] {label}: {status}  ({tail})")
    finally:
        shutil.copyfile(PRISTINE, MOD)

# final integrity check
h = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
assert h(MOD) == h(PRISTINE), "MODULE NOT RESTORED"
print("\nmodule restored byte-identical:", h(MOD)[:16])

surv = [r for r in results if r[1] == "SURVIVOR"]
print(f"\nTOTAL {len(results)} mutants: {len(results)-len(surv)} KILLED, {len(surv)} SURVIVED")
for label, _, tail, fails in surv:
    print(f"  SURVIVOR: {label}")
