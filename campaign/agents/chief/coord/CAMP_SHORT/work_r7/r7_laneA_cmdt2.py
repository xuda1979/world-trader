#!/usr/bin/env python3
"""CAMP_SHORT ROUND 7 charter (a) - spot-recompute AUDIT_GATES2's Lane A claim
(HUNT_CMDT2 R5 propane, 0/28 honest-negative) with OWN code.

We do NOT import AUDIT_GATES2's r6_recompute.py. We write our own parsers and our
own stats, then compare against (i) the metas themselves and (ii) AUDIT_GATES2's
published r6/recompute.json numbers for the same objects.
"""
import glob
import hashlib
import json
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
S = f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves"
AG2 = f"{ROOT}/campaign/agents/chief/coord/AUDIT_GATES2/r6/r6_recompute.json"
OUT = f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r7/r7_laneA_cmdt2.json"

R = {"tool": "CAMP_SHORT R7 lane A spot-recompute (own code)"}


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


champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True)["ret"]
R["champ_sha16"] = sha16(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
R["champ_n"] = len(champ)

# ---- own meta headline parser (independently written, not AG2's regex)
head_re = re.compile(
    r"^SR=(?P<sr>-?[\d.]+)\s+ann=(?P<ann>-?[\d.]+)%\s+vol=(?P<vol>-?[\d.]+)%\s+"
    r"H1=(?P<h1>-?[\d.]+)\s+H2=(?P<h2>-?[\d.]+)\s+negyrs=(?P<neg>\d+)\s+"
    r"worstyr=(?P<worst>-?[\d.]+)%\s+corr_champ=(?P<corr>-?[\d.]+)\s+n=(?P<n>\d+)\s+"
    r"(?P<start>[\d-]+)->(?P<end>[\d-]+)\s*$", re.M)
v2c_re = re.compile(
    r"v2_corrected:[^\n]*?leak_ok=(?P<leakok>\w+)[^\n]*?bp_ok=(?P<bpok>\w+)[^\n]*?"
    r"best_passive=(?P<bpname>[^:]+):(?P<bpsr>-?[\d.]+)\s+v2sr=(?P<v2sr>-?[\d.]+)\s+"
    r"corr=(?P<corr>-?[\d.]+)\s+pass=(?P<pass>\w+)")

rows, fails = [], []
for mp in sorted(glob.glob(f"{S}/prop_*.csv.meta")):
    name = os.path.basename(mp)[:-9]  # strip ".csv.meta"
    txt = open(mp).read()
    m = head_re.search(txt)
    c = v2c_re.search(txt)
    if not m or not c:
        fails.append((name, "PARSE"))
        continue
    net = pd.read_csv(mp[:-5], index_col=0, parse_dates=True).iloc[:, 0]
    sr, (h1, h2) = sharpe_d(net), halves(net)
    neg, worst = neg_years(net)
    corr_own = float(net.reindex(champ.index).mul(champ, fill_value=0.0).corr(champ))
    # same-span Pearson on the intersection (no fill), for disclosure
    j = pd.concat([net, champ], axis=1, join="inner").dropna()
    corr_inter = float(j.iloc[:, 0].corr(j.iloc[:, 1]))
    ck = {
        "sr_2dp": round(sr, 2) == round(float(m["sr"]), 2),
        "ann_1dp": round(ann_geo(net) * 100, 1) == float(m["ann"]),
        "h1_2dp": round(h1, 2) == float(m["h1"]),
        "h2_2dp": round(h2, 2) == float(m["h2"]),
        "neg": neg == int(m["neg"]),
        "worst_1dp": round(worst * 100, 1) == float(m["worst"]),
        "n": len(net) == int(m["n"]),
        "span": (str(net.index[0].date()) == m["start"] and str(net.index[-1].date()) == m["end"]),
        "corr_champ_3dp": round(corr_inter, 3) == round(float(m["corr"]), 3),
        "v2c_fail": c["pass"].lower() == "false",
        "v2c_bp_false": c["bpok"] == "False",
        "v2c_bp_sixty_forty": c["bpname"] == "sixty_forty",
    }
    rows.append(dict(name=name, sha16_csv=sha16(mp[:-5]), n=len(net),
                     sr_own=round(sr, 4), ann_own=round(ann_geo(net) * 100, 2),
                     h1_own=round(h1, 3), h2_own=round(h2, 3), neg_own=neg,
                     worst_own=round(worst * 100, 1),
                     mdd_own=round(max_dd(net) * 100, 2),
                     corr_inter_own=round(corr_inter, 4), corr_fill0_own=round(corr_own, 4),
                     sr_meta=float(m["sr"]), corr_meta=float(m["corr"]),
                     v2sr_corrected=float(c["v2sr"]), bpsr_corrected=float(c["bpsr"]),
                     checks=ck, all_ok=all(ck.values())))
    if not all(ck.values()):
        fails.append((name, {k: v for k, v in ck.items() if not v}))

df = pd.DataFrame(rows)
R["n_metas"] = len(df)
R["n_all_ok"] = int(df.all_ok.sum())
R["fails"] = [str(f) for f in fails]

# 0/28 adoptable: every v2_corrected line must be pass=false
R["n_v2c_fail"] = sum(1 for r in rows if r["checks"]["v2c_fail"])
R["max_abs_corr_meta"] = float(df.corr_meta.abs().max())

# family bests (held-book SR from CSV, OWN stats)
fam = {"seasonality": df[df.name.str.startswith("prop_seas")].sr_own.max(),
       "trend": df[df.name.str.startswith("prop_trend")].sr_own.max(),
       "spreadmr": df[df.name.str.startswith("prop_spreadmr")].sr_own.max()}
R["family_best_held_book_sr_own"] = {k: round(float(v), 3) for k, v in fam.items()}

# AUDIT_GATES2's three prose-defect quotes -> held-book numbers from CSVs with OWN stats
spots = {}
for nm in ["prop_seas_11-03_vt", "prop_seas_11-03_novt",
           "prop_spreadmr_w63_z2_vt", "prop_trend_w21_lo_vt"]:
    r0 = df[df.name == nm].iloc[0]
    spots[nm] = dict(sr_own=float(r0.sr_own), v2sr_corrected=float(r0.v2sr_corrected),
                     ann_own=float(r0.ann_own), neg_own=int(r0.neg_own))
R["prose_defect_spots"] = spots

# cross-check against AUDIT_GATES2's published recompute.json (their numbers)
try:
    ag2 = json.load(open(AG2))
    a = ag2["lanes"]["A_HUNT_CMDT2"]
    x = {
        "n_metas_theirs": a["n_metas_checked"],
        "n_metas_mine": len(df),
        "their_family_best": a["family_best_sr"],
        "my_family_best": R["family_best_held_book_sr_own"],
        "their_w21_lo_vt_csv_sr": a["w21_lo_vt_csv_sr"],
        "my_w21_lo_vt_sr": spots["prop_trend_w21_lo_vt"]["sr_own"],
        "their_seas12_02_novt_sr": a["seas12-02_novt_sr_csv"],
        "my_seas12_02_novt_sr": float(df[df.name == "prop_seas_12-02_novt"].iloc[0].sr_own),
        "their_max_abs_sr_dev": a["max_abs_sr_dev_csv_vs_meta"],
        "their_n_mismatch_5_note": "theirs reports 5 mismatch entries, all v2c_bpsr_reach tolerance only",
        "their_max_abs_corr": a["max_abs_corr_champ_meta"],
        "my_max_abs_corr_meta": R["max_abs_corr_meta"],
    }
    x["family_best_agree"] = all(
        abs(x["my_family_best"][k] - x["their_family_best"][k]) < 0.002 for k in fam)
    x["max_abs_sr_dev_mine_vs_meta"] = float((df.sr_own - df.sr_meta).abs().max())
    R["cross_vs_AG2"] = x
except Exception as e:  # noqa: BLE001
    R["cross_vs_AG2"] = f"UNAVAILABLE: {e}"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(R, open(OUT, "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in R.items() if k != "fails"}, indent=1, default=str))
print("FAILS:", R["fails"])
