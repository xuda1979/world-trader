#!/usr/bin/env python3
"""AUDIT_RECON round 3 — acceptance driver for bt/verify_champion.py.

Runs the acceptance tool over the three production scenarios and prints a JSON verdict:

  S1 current   : worktree champion + worktree weights + worktree sleeves (the re-emit
                 wave triple the coordinator will accept). EXPECT exit 0.
  S2 leak      : archived same-day-leak champion vs current sleeves. EXPECT exit 1
                 (causality must diagnose mechanism=same_day, truncation violated).
  S3 head      : HEAD (8f98da1) champion + HEAD weights + HEAD sleeves extracted from git
                 (its own vintage). EXPECT exit 0 — proves the R2-audited 39.85% triple was
                 internally exact too, so champion delta work<->HEAD is data-refresh + costfix
                 only, not a mechanism or honesty change.
  S4 drift     : HEAD champion vs CURRENT sleeves (vintage mismatch). EXPECT exit 1
                 (byte_repro/weights_repro must fail — a champion verifies only against its
                 own sleeve vintage).

Usage: python3 campaign/agents/chief/coord/AUDIT_RECON/work/r3_acceptance_driver.py
"""
import json
import os
import subprocess
import sys

REPO = "/Users/daxu/software/world-trader"
CAMP = f"{REPO}/campaign"
TOOL = f"{CAMP}/bt/verify_champion.py"
CHAMP = f"{CAMP}/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
WEIGHTS = f"{CAMP}/results/RAWEW13v2_IS_SR_weights.csv"
LEAK = f"{CAMP}/results/archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_SAMEDAYLEAK_ann40.84.csv"
OUT = f"{CAMP}/agents/chief/coord/AUDIT_RECON/work"


def _manifest():
    """(names, paths) from the builder itself — no hand-copying of the pool."""
    code = (f"import sys; sys.path.insert(0,{CAMP!r});"
            "import importlib.util;"
            f"s=importlib.util.spec_from_file_location('rb',{CAMP!r}+'/scripts/rawew13v2_build.py');"
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m);"
            "print(repr((m.NAMES, m.PATHS)))")
    names, paths = eval(subprocess.run([sys.executable, "-c", code],
                                       capture_output=True, text=True, check=True).stdout)
    return names, paths


def _git_show(rel, out):
    with open(out, "wb") as fh:
        subprocess.run(["git", "-C", REPO, "show", f"HEAD:{rel}"], stdout=fh, check=True)
    return out


def run(tag, champ, weights, sleeve_paths, expect):
    args = [sys.executable, TOOL, "--champion", champ, "--weights", weights]
    for n, p in sleeve_paths.items():
        args.append(f"--sleeve {n}={p}")
    jout = f"{OUT}/r3_accept_{tag}.json"
    args += ["--json", jout]
    r = subprocess.run(args, capture_output=True, text=True, cwd=CAMP)
    rep = json.load(open(jout))
    got = r.returncode
    chk = {k: v.get("ok") for k, v in rep.get("checks", {}).items()}
    mech = rep.get("checks", {}).get("causality", {}).get("matched_mechanism")
    print(f"[{tag}] exit={got} (expect {expect}) {'MATCH' if got == expect else 'MISMATCH'}")
    print(f"      ok={rep['ok']} checks={chk} mechanism={mech} errors={rep['errors'][:3]}")
    if rep.get("stats"):
        s = rep["stats"]
        print(f"      stats: n={s['n_days']} annCAGR={s['ann_cagr_pct']:.2f}% SR={s['sr']:.3f} "
              f"MDD={s['mdd_pct']:.2f}% negyr={s['neg_years']}")
    return got == expect


def main():
    names, rels = _manifest()
    cur = {n: f"{REPO}/{rels[n]}" for n in names}
    # NOTE: the git repo root is /Users/daxu, so HEAD paths carry the software/world-trader/
    # prefix; builder PATHS values already include their own campaign/ segment.
    head_sleeves = {n: _git_show(f"software/world-trader/{rels[n]}",
                                 f"/tmp/ar3_head_sleeve_{n}.csv")
                    for n in names}
    head_champ = _git_show(
        "software/world-trader/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
        "/tmp/ar3_head_champ.csv")
    head_weights = _git_show(
        "software/world-trader/campaign/results/RAWEW13v2_IS_SR_weights.csv",
        "/tmp/ar3_head_weights.csv")
    res = {
        "S1_current": run("S1_current", CHAMP, WEIGHTS, cur, 0),
        "S2_leak_archive": run("S2_leak", LEAK, WEIGHTS, cur, 1),
        "S3_head_vintage": run("S3_head", head_champ, head_weights, head_sleeves, 0),
        "S4_vintage_drift": run("S4_drift", head_champ, head_weights, cur, 1),
    }
    print(json.dumps({"all_expectations_met": all(res.values()), "runs": res}))
    return 0 if all(res.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
