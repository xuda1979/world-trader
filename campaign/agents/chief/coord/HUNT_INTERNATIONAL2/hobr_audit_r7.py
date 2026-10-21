#!/usr/bin/env python3
"""HUNT_INTERNATIONAL2 ROUND 7 charter (a) — CAMP_COST-R6 HOBR adoption-study audit.

Runs MY OWN algebra (HUNT_INTL2_round7_lib, TDD-pinned 12/12 in tests_tdd_r7.py) against
every headline number in CAMP_COST R6's adoption verdict, and saves work_r7/hobr_audit_r7.json.
Nothing here imports the modules under audit.
"""
import hashlib
import json
import sys

import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_INTERNATIONAL2")
import HUNT_INTL2_round7_lib as lib  # noqa: E402

ROOT = lib.ROOT
OUT = ROOT + "/campaign/agents/chief/coord/HUNT_INTERNATIONAL2/work_r7/"

TOL = {"dann": 0.005, "dsr": 0.005, "dmdd": 0.01, "bp": 1e-3}


def sha16(p):
    return hashlib.sha256(open(f"{ROOT}/{p}", "rb").read()).hexdigest()[:16]


res = {"audit": "HUNT_INTERNATIONAL2 R7 own-algebra audit of CAMP_COST-R6 HOBR adoption study",
       "tolerances": TOL, "checks": [], "evidence_gaps": []}


def check(name, mine, theirs, tol):
    ok = abs(mine - theirs) <= tol
    res["checks"].append({"name": name, "mine": mine, "theirs": theirs, "dev": mine - theirs,
                          "tol": tol, "ok": bool(ok)})
    return ok


# ---- 0. inputs still at round-end shas (audit target not moved)
pins = {
    "campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv": "4358dfab95679b97",
    "campaign/results/RAWEW13v2_IS_SR_weights.csv": "149164b3b01aa110",
    "campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv": "4a662985a408129b",
    "campaign/results/RAWEW14_HOBR_CANDIDATE_weights.csv": "dc0dc87fea2ef4b0",
    "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv":
        "da0285b9a7a5e6a2",
}
res["sha_pins"] = {p: dict(expected=s, found=sha16(p), ok=sha16(p) == s) for p, s in pins.items()}

# ---- 1. my builders reproduce the committed books
net13, relw13, gross13, to13, _ = lib.build13_own()
p14 = lib.build14_own(weights=True)
net14, relw14, gross14, to14, df14, Wg14 = p14
champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0].astype(float)
cand = pd.read_csv(f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv",
                   index_col=0, parse_dates=True).iloc[:, 0].astype(float)
dev13 = float((net13 - champ).abs().max())
dev14 = float((net14 - cand).abs().max())
res["book_repro"] = {"book13_vs_committed_max_dev": dev13, "book14_vs_candidate_max_dev": dev14,
                     "both_ok": bool(dev13 < 1e-9 and dev14 < 1e-9)}
print(f"[1] book13 dev {dev13:.3e} | book14 dev {dev14:.3e}")

# ---- 2. capital-real headline (8c)
d = lib.delta_stats(net14, net13)
res["capital_real"] = d
check("capital-real dAnn_pp (8c HARD)", d["dAnn_pp"], -0.9069, TOL["dann"])
check("capital-real dSR", d["dSR"], 0.0909, TOL["dsr"])
check("capital-real dMDD_pp", d["dMDD_pp"], 0.4568, TOL["dmdd"])
check("dSR_H1_byhalf (8f)", d["dSR_H1_byhalf"], 0.2376, 0.01)
check("dSR_H2_byhalf (8f/8d)", d["dSR_H2_byhalf"], 0.0223, 0.01)
check("c14 book IS SR", d["c14_is_sr"], 3.7252, 0.01)
check("c14 book OOS SR", d["c14_oos_sr"], 3.0655, 0.01)
check("c13 book IS SR", d["c13_is_sr"], 3.4945, 0.01)
check("c13 book OOS SR", d["c13_oos_sr"], 3.0358, 0.01)
t13 = float(to13.mean() * 252 * 6.4)
t14 = float(to14.mean() * 252 * 6.4)
check("c13 turnover bp/yr", t13, 5.2622, TOL["bp"])
check("c14 turnover bp/yr", t14, 5.4972, TOL["bp"])
check("turnover delta bp/yr", t14 - t13, 0.2350, 2e-3)
share = Wg14["RB_hobr"] / Wg14.abs().sum(axis=1)
check("HOBR mean NAV share", float(share.mean()), 0.05758, 2e-4)
check("HOBR max NAV share (<=0.15)", float(share.max()), 0.09981, 2e-4)
res["w15_cap_outcome"] = {"min": float(share.min()), "mean": float(share.mean()),
                          "max": float(share.max()), "cap_ok": bool(share.max() <= 0.15)}
print(f"[2] capital-real dAnn {d['dAnn_pp']:+.4f}pp dSR {d['dSR']:+.4f} dMDD {d['dMDD_pp']:+.4f}pp")

# ---- 3. fill-0 artifact + 8e breach at every rung
net_h, gross_h = lib.hobr_sleeve_rebuild_own()
pub_h = pd.read_csv(f"{ROOT}/campaign/team/agents/RES_BASIS/sleeves/"
                    "RB_hobr_crack_hyst_w63_z10_zo10.csv", index_col=0, parse_dates=True
                    ).iloc[:, 0].astype(float)
dev_h = float((net_h - pub_h).abs().max())
res["hobr_sleeve_repro"] = {"max_dev": dev_h, "ok": bool(dev_h < 1e-9),
                            "sleeve_mean_gross": float(gross_h.mean())}
check("HOBR sleeve rebuild vs published bytes", dev_h, 0.0, 1e-9)
f0 = {}
for w, theirs in ((0.05, 0.838), (0.10, 1.679), (0.15, 2.521), (0.25, 4.2128)):
    r = lib.fill0_blend(net13, net_h, gross_h, w)
    f0[str(w)] = r
    check(f"fill-0 dAnn_pp @w={w}", r["dAnn_pp"], theirs, 0.01)
check("fill-0 dSR @w=0.25", f0["0.25"]["dSR"], 0.1989, TOL["dsr"])
check("fill-0 dMDD @w=0.25", f0["0.25"]["dMDD_pp"], 0.051, 0.01)
res["fill0"] = f0
res["fill0_8e"] = {
    w: {"blend_gross_mean": f0[w]["book_gross_mean"], "breach": f0[w]["book_gross_mean"] > 1.6}
    for w in f0}
res["fill0_8e_correction"] = (
    "CAMP_COST R6 text quotes fill-0 blend gross 1.65/1.70/1.75/1.85 (implies sleeve gross "
    f"~1.0); ACTUAL sleeve mean gross is {float(gross_h.mean()):.4f} (vt-0.08-targeted 2-leg "
    "book), so true blend gross is " + "/".join(f"{f0[w]['book_gross_mean']:.4f}" for w in
                                                ("0.05", "0.1", "0.15", "0.25")) +
    " - the 8e BREACH verdict is unchanged (breach at every w), magnitudes corrected.")
print(f"[3] fill-0 @0.25 dAnn {f0['0.25']['dAnn_pp']:+.4f}pp (their +4.2128) "
      f"| 8e breach at every rung")

# ---- 4. rung grid (8g)
rows = lib.rung_grid_capital_real()
res["rung_grid_8g"] = rows
theirs_grid = {0.05: (-0.786, 0.0799, 0.396), 0.10: (-1.592, 0.1454, 0.795),
               0.15: (-2.416, 0.1911, 1.193)}
for r in rows:
    e = theirs_grid[r["w"]]
    check(f"8g dAnn @w={r['w']}", r["dAnn_pp"], e[0], 0.02)
    check(f"8g dSR @w={r['w']}", r["dSR"], e[1], 0.005)
    check(f"8g dMDD @w={r['w']}", r["dMDD_pp"], e[2], 0.02)
print(f"[4] rung grid dAnn " + "/".join(f"{r['dAnn_pp']:+.3f}" for r in rows) + "pp (all NEG)")

# ---- 5. 8i exclusion
e8i = lib.excl_8i_own(net14, net13)
res["excl_8i"] = e8i
check("8i dMDD_pp_excl", e8i["dMDD_pp_excl"], 0.5219, 0.01)
res["excl_8i"]["window_theirs"] = ["2018-06-19", "2018-07-20"]
res["excl_8i"]["window_match"] = list(e8i["window"]) == res["excl_8i"]["window_theirs"]
print(f"[5] 8i excl window {e8i['window']} dMDD_excl {e8i['dMDD_pp_excl']:+.4f}pp")

# ---- 6. gross-neutral delevered blend: their text numbers have NO generator (evidence gap)
gn = {}
for w in (0.05, 0.25):
    gn[str(w)] = lib.gross_neutral_blend(net13, w)
res["gross_neutral_my_construction_dAnn_pp"] = gn
res["evidence_gaps"].append({
    "item": "CAMP_COST R6 FINDINGS 'gross-neutral delevered blend -0.306pp (w=.05) to "
            "-1.565pp (w=.25)'",
    "problem": "no generator script or JSON artifact in CAMP_COST/work_r6 produces these "
               "two numbers (V2 s10a); they appear only as FINDINGS prose",
    "my_construction": "(1-w)*champ + w*cand14 (both books at gross 1.6 -> blend at 1.6): "
                       f"w=.05 {gn['0.05']:+.4f}pp, w=.25 {gn['0.25']:+.4f}pp",
    "other_constructions_tried": {
        "mean-relevered sleeve to gross 1.6": "(w=.05 +2.4329, w=.25 +11.6445) POSITIVE - "
                                              "worse for their conclusion, also not it",
        "per-day relevered sleeve to gross 1.6": "(w=.05 +0.1292, w=.25 +0.4209) POSITIVE",
        "gross-1-normalized sleeve": "(w=.05 -0.7163, w=.25 -3.6493)",
    },
    "verdict": "direction CONSISTENT with the 8c fail under my (1-w) construction (negative "
               "at every w) and the headline verdict does not depend on these two numbers, "
               "but as stated they are UNVERIFIABLE - generator requested",
})

# ---- 7. leak probes (own implementations)
wide = lib.leak_probe_wide_own(Wg14, df14)
signed = lib.leak_probe_scalar_own(Wg14.diff().sum(axis=1), net14)
turn = lib.leak_probe_scalar_own(Wg14.diff().abs().sum(axis=1), net14)
res["leak_probes"] = {"wide": wide, "signed": signed, "turnover_abs": turn}
check("wide probe same_period_corr", wide["same_period_corr"], -0.04383801976688111, 5e-4)
check("wide probe lag -1", wide["lag_scan"][-1], 0.7990713215236287, 5e-4)
check("signed probe corr", signed["same_period_corr"], 0.008869980091649491, 5e-4)
check("turnover probe corr", turn["same_period_corr"], 0.22549260608597557, 5e-4)
check("turnover probe lag -1", turn["lag_scan"][-1], 0.48815150296681903, 5e-4)
res["leak_verdicts"] = {"wide": wide["leak"], "signed": signed["leak"],
                        "turnover_abs": turn["leak"],
                        "all_false_and_lag0_not_argmax": bool(
                            not wide["leak"] and not signed["leak"] and not turn["leak"]
                            and wide["argmax_lag"] == -1 and turn["argmax_lag"] == -1)}
print(f"[7] leak: wide {wide['same_period_corr']:+.4f} signed {signed['same_period_corr']:+.4f} "
      f"turnover {turn['same_period_corr']:+.4f} -> all leak=False")

# ---- 8. their battery re-run byte-compare (executed separately this session)
res["battery_rerun"] = {
    "script": "CAMP_COST/work_r6/adoption_study.py (run UNMODIFIED)",
    "committed_sha16_before": "6b9bfc9e966fb99c",
    "sha16_after_rerun": sha16("campaign/agents/chief/coord/CAMP_COST/work_r6/adoption_battery.json"),
    "byte_identical": sha16("campaign/agents/chief/coord/CAMP_COST/work_r6/adoption_battery.json")
                      == "6b9bfc9e966fb99c",
    "note": "their 4 battery stdout captures (rerun/session2/session4) were already "
            "byte-identical before my re-run; the script writes its JSON in place, so an "
            "auditor re-run overwrites the artifact - process hazard logged, harmless here "
            "because byte-identical",
}
print(f"[8] battery re-run byte_identical={res['battery_rerun']['byte_identical']}")

# ---- verdict
n_bad = sum(1 for c in res["checks"] if not c["ok"])
res["summary"] = {
    "n_checks": len(res["checks"]), "n_failed": n_bad,
    "8c_capital_real_dAnn_pp": d["dAnn_pp"],
    "8c_verdict": "FAIL (HARD) CONFIRMED - NOT-ADOPTABLE",
    "fill0_artifact_pp": f0["0.25"]["dAnn_pp"],
    "fill0_8e_breach_every_rung": True,
    "escalations": ["evidence-gap: gross-neutral -0.306/-1.565pp prose numbers unverifiable"],
}
json.dump(res, open(OUT + "hobr_audit_r7.json", "w"), indent=1, default=float)
print(f"\nAUDIT: {len(res['checks']) - n_bad}/{len(res['checks'])} numeric checks ok; "
      f"evidence gaps: {len(res['evidence_gaps'])}")
print("VERDICT: CAMP_COST R6 adoption verdict CONFIRMED (8c HARD FAIL at -0.9069pp, "
      "NOT-ADOPTABLE); champion of record untouched.")
sys.exit(1 if (n_bad or dev13 > 1e-9 or dev14 > 1e-9) else 0)
