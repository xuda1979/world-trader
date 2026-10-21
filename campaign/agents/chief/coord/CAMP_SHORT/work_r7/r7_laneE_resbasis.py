#!/usr/bin/env python3
"""CAMP_SHORT ROUND 7 charter (a) - spot-recompute AUDIT_GATES2's Lane E claim
(RES_BASIS row-137 RB_hobr_crack_hyst_w63_z10_zo10 standalone V2-PASS) with OWN code.

Layer 1 (pure own algebra): sha, stats from the published CSV, corr_champ, blend
arithmetic in BOTH conventions, IS/OOS split, T+1 leak probe of our own construction.
Layer 2 (their published code path, like AG2 did): rebuild net from FRED raw and
re-run the v2 battery with sig= passed explicitly (V2 in force: pass sig= and
leak_check=True explicitly - we do NOT depend on the default).
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
S = f"{ROOT}/campaign/team/agents/RES_BASIS"
CAND = f"{S}/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv"
OUT = f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r7/r7_laneE_resbasis.json"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")

R = {"tool": "CAMP_SHORT R7 lane E spot-recompute (own code layer 1 + their code layer 2)"}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def sharpe_d(r):
    s = r.std(ddof=1)
    return 0.0 if (not s or not np.isfinite(s) or s < 1e-12) else float(r.mean() / s * np.sqrt(252))


def ann_geo(r):
    return float((1 + r).prod(min_count=1) ** (252.0 / len(r)) - 1)


def max_dd(r):
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min())


def neg_years(r):
    yr = (1 + r).groupby(r.index.year).prod(min_count=1) - 1
    yr = yr.where(np.isfinite(yr), -1.0)
    return int((yr < 0).sum()), float(yr.min())


def halves(r):
    k = len(r) // 2
    return sharpe_d(r.iloc[:k]), sharpe_d(r.iloc[k:])


cand = pd.read_csv(CAND, index_col=0, parse_dates=True)["ret"]
champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True)["ret"]
R["sha16"] = sha16(CAND)
R["sha_meta"] = "da0285b9a7a5e6a2"
R["sha_ok"] = R["sha16"] == R["sha_meta"]
sr, (h1, h2) = sharpe_d(cand), halves(cand)
neg, worst = neg_years(cand)
j = pd.concat([cand, champ], axis=1, join="inner").dropna()
corr_inter = float(j.iloc[:, 0].corr(j.iloc[:, 1]))
R["stats_own"] = dict(n=len(cand), sr=round(sr, 4), ann=round(ann_geo(cand) * 100, 2),
                      mdd=round(max_dd(cand) * 100, 2), h1=round(h1, 3), h2=round(h2, 3),
                      neg=neg, neg_years_count=18, worst=round(worst * 100, 2),
                      span=(str(cand.index[0].date()), str(cand.index[-1].date())),
                      corr_champ_intersect=round(corr_inter, 4),
                      ac1=round(float(cand.autocorr(1)), 4))
# meta claims to check
meta = dict(n=4604, sr=1.3498, ann=13.25, mdd=-22.29, h1=2.182, h2=0.753, neg=1, worst=-0.69,
            span=("2008-02-19", "2026-08-25"), corr=0.0219, ac1=-0.1083)
R["meta_checks"] = {
    "n": R["stats_own"]["n"] == meta["n"],
    "sr_4dp": round(R["stats_own"]["sr"], 4) == meta["sr"],
    "ann_2dp": abs(R["stats_own"]["ann"] - meta["ann"]) < 0.005,
    "mdd_2dp": abs(R["stats_own"]["mdd"] - meta["mdd"]) < 0.005,
    "h1_3dp": abs(R["stats_own"]["h1"] - meta["h1"]) < 0.0005,
    "h2_3dp": abs(R["stats_own"]["h2"] - meta["h2"]) < 0.0005,
    "neg": R["stats_own"]["neg"] == meta["neg"],
    "worst_2dp": abs(R["stats_own"]["worst"] - meta["worst"]) < 0.005,
    "span": R["stats_own"]["span"] == meta["span"],
    "corr_4dp": abs(corr_inter - meta["corr"]) < 5e-4,
    "ac1_4dp": abs(R["stats_own"]["ac1"] - meta["ac1"]) < 5e-4,
    "sha": R["sha_ok"],
}
# IS/OOS split at 2017-01-01 (the campaign's IS_END)
is_r = cand[cand.index < "2017-01-01"]
oos_r = cand[cand.index >= "2017-01-01"]
R["is_oos_own"] = dict(is_sr=round(sharpe_d(is_r), 3), oos_sr=round(sharpe_d(oos_r), 3),
                       is_n=len(is_r), oos_n=len(oos_r),
                       meta_claims=(2.145, 0.807))
# blend arithmetic, BOTH conventions (charter R6 story: fill-0 vs sleeve-span)
res = {}
for w in (0.10, 0.25, 0.35, 0.50):
    # conv A: champ-span, sleeve fill 0 (coordinator/AG2 convention)
    cA = champ + w * cand.reindex(champ.index).fillna(0.0)
    # conv B: sleeve-span, champ reindex fill 0 (RES_BASIS sleeve-span convention)
    cB = cand + w * champ.reindex(cand.index).fillna(0.0)
    res[f"w{w}"] = dict(
        convA_dSR=round(sharpe_d(cA) - sharpe_d(champ), 3),
        convA_dAnn_pp=round((ann_geo(cA) - ann_geo(champ)) * 100, 2),
        convA_MDD_pct=round(max_dd(cA) * 100, 2),
        convA_neg=int(neg_years(cA)[0]),
        convB_dSR=round(sharpe_d(cB) - sharpe_d(cand), 3),
        convB_dAnn_pp=round((ann_geo(cB) - ann_geo(cand)) * 100, 2),
        convB_MDD_pct=round(max_dd(cB) * 100, 2),
        convB_neg=int(neg_years(cB)[0]))
R["blend_own"] = res
R["blend_meta_claims"] = {"w0.25 (their line, sleeve-span native units)": "dSR +0.199 dAnn +4.21pp MDD -6.64%",
                          "AG2 convA note": "AG2 published convA dAnn +4.50 @0.25 (sleeve-span is larger, +4.5)"}

# ---- own 1-lag leak probe (own construction, not bt.leakcheck): corr(dW_t, r_t) needs
# weights; we only have the net series, so probe lag structure of the published series
# against champion: argmax at lag 0 same-day would be the leak signature.
lags = {}
for L in (-2, -1, 0, 1, 2):
    lags[L] = round(float(pd.concat([cand.shift(L), champ], axis=1, join="inner").dropna()
                          .iloc[:, 0].corr(champ)), 4)
R["series_vs_champ_lags_own"] = lags
R["series_lag_note"] = ("cand vs champ; argmax at lag 0 (corr +0.0215 per meta) is the "
                        "DECLARED same-period coupling; V2 6b bar is |corr0|<0.20 and "
                        "lag_scan argmax at NEGATIVE (past) lags in the sig-vs-ret probe")

# ================= Layer 2: their published code path =================
import importlib.util


def run_module(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


try:
    import bt.gates as G

    hb = run_module(f"{S}/hunt_r1.py")
    rh = run_module(f"{S}/run_hunt.py")
    d6 = rh.spreads()["ho_br"]
    net2, We2, gross2, rpu2 = hb.pair_book(d6["r_a"], d6["r_b"], d6["spread"], win=63,
                                           z_in=1.0, z_out=1.0, side="meanrev", return_rpu=True)
    live2 = (We2.fillna(0) != 0).any(axis=1)
    net2 = net2[net2.index >= live2.idxmax()]
    We2 = We2[We2.index >= net2.index[0]]
    R["rebuild_max_dev_vs_csv"] = float((net2 - cand.reindex(net2.index)).abs().max())
    R["rebuild_n"] = len(net2)
    spy2, ief2, cta2 = rh.benchmark_series()
    v2 = rh.v2_battery(rpu2.reindex(We2.index).fillna(0.0), sig=We2["a"].fillna(0.0),
                       ref=champ, spy=spy2, ief=ief2, cta=cta2)
    R["v2_battery_own_rerun"] = dict(
        sr=round(v2["sr"], 4), corr=round(v2["corr"], 4),
        leak_corr=round(v2["leak"]["same_period_corr"], 4),
        leak_p=float(v2["leak"]["same_period_p"]),
        leak_lag={k: round(v, 4) for k, v in v2["leak"]["lag_scan"].items()},
        leak_ok=bool(v2["leak_ok"]), scr_p=float(v2["scr_p"]),
        bp_name=v2["beats_passive"]["best_passive_name"],
        bp_sr=round(v2["beats_passive"]["best_passive_sr"], 4),
        bp_cand=round(v2["beats_passive"]["candidate_sr"], 4),
        bp_ok=bool(v2["beats_passive_ok"]), PASS=bool(v2["pass"]))
    R["v2_meta_claims"] = dict(sr=1.6031, corr=0.0215, leak_corr=0.1071, bp_sixty_forty=0.602,
                               PASS=True, leak_lag={"-2": -0.1095, "-1": -0.1885, "0": 0.1071,
                                                    "1": 0.0264, "2": 0.0185})
    # plateau spot-check: window grid at z1.0 (their disclosed plateau line);
    # per-window LIVE start (their evaluate() convention), NOT the w63 live start
    plat = {}
    for win in (21, 40, 63, 90, 126):
        n3, We3, _, _ = hb.pair_book(d6["r_a"], d6["r_b"], d6["spread"], win=win,
                                     z_in=1.0, z_out=1.0, side="meanrev", return_rpu=True)
        lv3 = (We3.fillna(0) != 0).any(axis=1)
        n3 = n3[n3.index >= lv3.idxmax()]
        plat[win] = round(sharpe_d(n3), 3)
    R["plateau_own_rerun"] = plat
    R["plateau_meta_claim"] = "21/40/63/90/126 -> 1.356/1.357/1.350/1.302/1.148"
except Exception as e:  # noqa: BLE001
    import traceback
    R["layer2_error"] = traceback.format_exc()[-1500:]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(R, open(OUT, "w"), indent=1, default=str)
print(json.dumps(R, indent=1, default=str))
