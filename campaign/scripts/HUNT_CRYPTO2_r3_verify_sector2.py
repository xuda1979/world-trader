#!/usr/bin/env python3
"""HUNT_CRYPTO2 ROUND 3 (a): independent cross-verification of HUNT_SECTOR2 round-2.

Recomputes SR / ann / halves / neg-years / worst-year / corr-vs-champion for each of
HUNT_SECTOR2's five published round-2 sleeves with MY OWN code (work_r3/r3lib.py, a
re-implementation that does NOT import bt), re-derives the verdict from the
GATES_CONTRACT gate definitions (SR>=1.0, H1&H2>=0.5, negyr<=2 or worst>-5% ...
contract wording: <=2 negative years each > -5%), and compares against the verdict
string they published in the .meta. Mismatches are escalated, not edited.

Usage: python3 campaign/scripts/HUNT_CRYPTO2_r3_verify_sector2.py
Output: stdout table + campaign/agents/chief/coord/HUNT_CRYPTO2/work_r3/R3a_verify_report.txt
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r3")
import r3lib  # noqa: E402

CHAMP_HEAD = "/tmp/champ_head.csv"          # git HEAD champion (what their metas used)
CHAMP_WT = os.path.join(ROOT, "results", "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
S2 = os.path.join(ROOT, "agents", "chief", "coord", "HUNT_SECTOR2", "sleeves")
OUT = os.path.join(ROOT, "agents", "chief", "coord", "HUNT_CRYPTO2", "work_r3",
                   "R3a_verify_report.txt")

# the five ROUND-2 verdict sleeves (their round-3 COMP_* composites are out of scope)
ARMS = {
    "A_rs_ratio":           dict(sr=0.534, ann=5.99, h1=0.38, h2=0.70, neg=3, worst=-10.1, corr=-0.042, verdict="FAIL_SR|FAIL_HALVES|FAIL_NEGYR"),
    "A11_rs_ratio#lb126k4": dict(sr=0.679, ann=7.40, h1=0.55, h2=0.95, neg=2, worst=-1.3,  corr=-0.147, verdict="FAIL_SR"),
    "B_barbell":            dict(sr=0.613, ann=5.47, h1=0.74, h2=0.55, neg=3, worst=-15.5, corr=-0.076, verdict="FAIL_SR|FAIL_NEGYR"),
    "C_xle_crud":           dict(sr=0.154, ann=1.76, h1=0.33, h2=-0.01, neg=8, worst=-18.7, corr=0.029, verdict="FAIL_SR|FAIL_HALVES|FAIL_NEGYR|FAIL_PLATEAU"),
    "D_xlu_ief":            dict(sr=0.585, ann=4.70, h1=0.55, h2=0.62, neg=3, worst=-6.6,  corr=-0.089, verdict="FAIL_SR|FAIL_NEGYR"),
}


def parse_meta_verdict(path):
    with open(path) as f:
        for line in f:
            if line.startswith("verdict="):
                return line.strip().split("=", 1)[1]
    return None


def derive_verdict(m):
    """Re-derive the gates that SECTOR2's verdict string encodes (SR/halves/negyr only;
    plateau+scramble need their scan machinery and are taken from the meta as-is)."""
    fails = []
    if m["sr"] < 1.0:
        fails.append("FAIL_SR")
    if m["h1"] < 0.5 or m["h2"] < 0.5:
        fails.append("FAIL_HALVES")
    # contract 3d: <=2 negative years each > -5%
    if m["neg"] > 2 or m["worst"] <= -0.05:
        fails.append("FAIL_NEGYR")
    return "|".join(fails) if fails else "PASS_NUMS"


def main():
    champ = r3lib.load_ret(r3lib.ensure_champ_head(CHAMP_HEAD))  # self-healing: rebuild from git HEAD if stale/missing
    lines = []
    lines.append(f"# R3a cross-verify of HUNT_SECTOR2 round-2 sleeves "
                 f"(my code, champ HEAD n={len(champ)} {champ.index[0].date()}..{champ.index[-1].date()})")
    lines.append("NOTE: their metas' `ann` is ARITHMETIC (== sr*vol exactly in all 5); "
                 "geo shown for honesty.\n")
    n_mismatch = 0
    for name, pub in ARMS.items():
        m = r3lib.evaluate_arm(r3lib.load_ret(os.path.join(S2, f"{name}.csv")), champ)
        meta_v = parse_meta_verdict(os.path.join(S2, f"{name}.csv.meta"))
        derived = derive_verdict(m)
        checks = [
            ("sr", round(m["sr"], 3), pub["sr"], 0.005),
            ("ann_arith", round(100 * m["ann_arith"], 2), pub["ann"], 0.011),
            ("h1", round(m["h1"], 2), pub["h1"], 0.005),
            ("h2", round(m["h2"], 2), pub["h2"], 0.005),
            ("negyr", m["neg"], pub["neg"], 0),
            ("worst%", round(100 * m["worst"], 1), pub["worst"], 0.05),
            ("corr", round(m["corr"], 3), pub["corr"], 0.0005),
        ]
        bad = [(k, g, p) for k, g, p, tol in checks if abs(g - p) > tol]
        v_ok = all(f in meta_v.split("|") for f in fails_in(meta_v, derived)) if fails_in(meta_v, derived) else True
        verdict_consistent = (derived == "PASS_NUMS") == (meta_v.startswith("PASS"))
        status = "OK" if not bad else "MISMATCH"
        if bad or not verdict_consistent:
            n_mismatch += 1
        lines.append(
            f"{name:22s} n={m['n']:4d} {m['start']}..{m['end']} "
            f"sr={m['sr']:+.3f}(pub {pub['sr']:+.3f}) geo={100*m['ann']:+6.2f}% arith={100*m['ann_arith']:+6.2f}% "
            f"H1={m['h1']:+.2f}(pub {pub['h1']:+.2f}) H2={m['h2']:+.2f}(pub {pub['h2']:+.2f}) "
            f"negyr={m['neg']}(pub {pub['neg']}) worst={100*m['worst']:+.1f}% corr={m['corr']:+.3f}(pub {pub['corr']:+.3f}) "
            f"meta_v={meta_v} derived_v={derived} -> {status}"
        )
        if bad:
            lines.append(f"    !! stat mismatches: {bad}")
        if not verdict_consistent:
            lines.append(f"    !! VERDICT mismatch: meta={meta_v} vs derived-from-my-numbers={derived}")
    lines.append("")
    lines.append(f"SUMMARY: {len(ARMS)} arms cross-verified, {n_mismatch} mismatches.")
    txt = "\n".join(lines)
    print(txt)
    with open(OUT, "w") as f:
        f.write(txt + "\n")
    return 0 if n_mismatch == 0 else 1


def fails_in(meta_v, derived):
    return [f for f in derived.split("|") if f != "PASS_NUMS"]


if __name__ == "__main__":
    sys.exit(main())
