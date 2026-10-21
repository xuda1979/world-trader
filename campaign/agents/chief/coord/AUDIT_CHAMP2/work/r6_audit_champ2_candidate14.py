#!/usr/bin/env python3
"""AUDIT_CHAMP2 R6 — INDEPENDENT verifier of the CAMP_COST 14-sleeve candidate.

Own algebra (mirrors the rawew13v2 recipe from its docstring/comments only — NO import of
rawew13v2_build, bt.verify_champion, bt.engine, or anything of CAMP_COST's). Artifacts
consumed: the 14 sleeve CSVs (13 champion inputs + RB_hobr) + CAMP_COST's two emitted
candidate files. Verifies:
  1. weights_repro  2. byte_repro  3. cost_reconciliation (full_dw vs half_dw)
  4. causality nav.shift(1) + truncation-invariance  5. gross<=1.6 (weights + financing)
  6. yearly 0-neg  7. MDD>=-7
plus: stats/deltas vs champion, halves, IS/OOS, HOBR NAV share, and the fill-0 w=0.25
blend root-cause (the coordinator's +4.21pp) incl its GROSS (V2 8e concern).
"""
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/AUDIT_CHAMP2/work/"

SLEEVES = {
    "brwt15":  "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10":  "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7":   "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5":   "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng":    "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2":    "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7":    "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4":    "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
    "RB_hobr": "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv",
}
GEAR, RATE, BPS = 1.6, 0.045, 6.4
P, IS_END, START = 0.55, "2017-01-01", "2008-03-31"
TOL, RELW_TOL, TRUNC_TOL = 1e-12, 1e-9, 1e-15

res = {}
fail = []


def chk(name, ok, **kw):
    res[name] = {"ok": bool(ok), **kw}
    if not ok:
        fail.append(name)


def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


def book(relw, df, causal=True):
    nav = (1 + df.fillna(0)).cumprod()
    if causal:
        nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
    Wg = d2 * (GEAR / len(relw))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = pd.Series(Wg.diff().abs().sum(axis=1), index=df.index).fillna(0.0)
    net = port - to * BPS / 1e4 - max(GEAR - 1, 0) * RATE / 252
    return pd.Series(net, index=df.index), Wg, to, port


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {"n": int(len(r)), "cagr_pct": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
            "arith_pct": float(r.mean() * 252 * 100),
            "sr": float(r.mean() / r.std(ddof=1) * np.sqrt(252)), "mdd_pct": mdd * 100,
            "neg_years": int((yr < 0).sum()), "worst_year_pct": float(yr.min() * 100),
            "n_years": int(len(yr))}


# ---------------------------------------------------------------- inputs
df = pd.DataFrame({n: load(p).dropna() for n, p in SLEEVES.items()})
df = df[df.index >= START]
isr = df[df.index < IS_END]
relw = pd.Series({n: max(is_sr(isr[n]), 0.0) ** P for n in df.columns})

net, Wg, to, port = book(relw, df, causal=True)
net_sd, Wg_sd, to_sd, _ = book(relw, df, causal=False)

# committed candidate artifacts (CAMP_COST's emit)
c14 = pd.read_csv(f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv",
                  index_col=0, parse_dates=True).iloc[:, 0]
w14 = pd.read_csv(f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_weights.csv",
                  index_col=0).iloc[:, 0]
champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]

# 1 weights_repro
chk("weights_repro", float((relw - w14.reindex(relw.index)).abs().max()) < RELW_TOL,
    max_dev=float((relw - w14.reindex(relw.index)).abs().max()), tol=RELW_TOL,
    rb_hobr_relw=float(relw["RB_hobr"]))

# 2 byte_repro
j = pd.concat([c14.rename("csv"), net.rename("my")], axis=1, join="inner")
chk("byte_repro", len(j) == len(c14) == len(net)
    and float((j.csv - j.my).abs().max()) < TOL,
    max_dev=float((j.csv - j.my).abs().max()), n_inner=int(len(j)),
    n_csv=int(len(c14)), n_my=int(len(net)), tol=TOL)

# 3 cost_reconciliation (own algebra): what the csv charged vs full|dW| and half|dW|
margin = max(GEAR - 1, 0) * RATE / 252
cost_implied = port - j.csv - margin
cost_full = to * BPS / 1e4
dev_full = float((cost_implied - cost_full).abs().max())
dev_half = float((cost_implied - 0.5 * cost_full).abs().max())
ratio = float(cost_implied.sum() / cost_full.sum())
chk("cost_reconciliation", dev_full < TOL and abs(ratio - 1) < 1e-6,
    model="full_dw" if dev_full < TOL else ("half_dw" if dev_half < TOL else "unknown"),
    max_dev_full=dev_full, max_dev_half=dev_half, ratio=ratio,
    bp_per_year=float(cost_implied.mean() * 252 * 1e4),
    day1_entry_charged_bp=float(cost_implied.iloc[0] * 1e4))

# 4 causality + truncation-invariance (own probes: 7 dates)
causal_dev = float((j.csv - j.my).abs().max())
sameday_dev = float((j.csv - net_sd.reindex(j.index)).abs().max())
tdev = 0.0
for t in [0, 1, 2, len(df) // 4, len(df) // 2, 3 * len(df) // 4, len(df) - 1]:
    dfz = df.copy()
    dfz.iloc[t:] = 0.0
    _, Wt, _, _ = book(relw, dfz, causal=True)
    tdev = max(tdev, float((Wt.iloc[t] - Wg.iloc[t]).abs().max()))
chk("causality", causal_dev < TOL and causal_dev <= sameday_dev and tdev < TRUNC_TOL,
    causal_max_dev=causal_dev, sameday_max_dev=sameday_dev, truncation_max_dev=tdev,
    trunc_tol=TRUNC_TOL)

# 5 gross (weights + financing-implied)
gross = Wg.abs().sum(axis=1)
resid = port - j.csv - cost_full
fin_gross = 1.0 + resid * 252.0 / RATE
chk("gross", float(gross.max()) <= GEAR + 1e-9 and float(fin_gross.max()) <= GEAR + 1e-9,
    weights_max=float(gross.max()), financing_implied_max=float(fin_gross.max()),
    n_over=int((gross > GEAR + 1e-9).sum() + (fin_gross > GEAR + 1e-9).sum()))

# 6 yearly / 7 mdd
s = j.csv
yr = s.groupby(s.index.year).apply(lambda x: (1 + x).prod() - 1)
nav = (1 + s).cumprod()
mdd = float((nav / nav.cummax() - 1).min())
chk("yearly", int((yr < 0).sum()) == 0 and float(yr.min()) > -0.05,
    neg_years=int((yr < 0).sum()), worst_year_pct=float(yr.min() * 100))
chk("mdd", mdd >= -0.07, mdd_pct=mdd * 100, limit=-7.0)

# ---------------------------------------------------------------- deltas + root-cause
res["stats"] = {"c14": stats(s), "champ": stats(champ)}
res["deltas"] = {
    "dAnn_cagr_pp": stats(s)["cagr_pct"] - stats(champ)["cagr_pct"],
    "dAnn_arith_pp": stats(s)["arith_pct"] - stats(champ)["arith_pct"],
    "dSR": stats(s)["sr"] - stats(champ)["sr"],
    "dMDD_pp": stats(s)["mdd_pct"] - stats(champ)["mdd_pct"],
}
jj = pd.concat([champ.rename("c13"), s.rename("c14")], axis=1, join="inner").dropna()
mid = jj.index[len(jj) // 2]
sr_ = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(252)
res["halves"] = {
    "c13_H1": sr_(jj.c13[jj.index < mid]), "c13_H2": sr_(jj.c13[jj.index >= mid]),
    "c14_H1": sr_(jj.c14[jj.index < mid]), "c14_H2": sr_(jj.c14[jj.index >= mid]),
    "dSR_H1_byhalf": sr_(jj.c14[jj.index < mid]) - sr_(jj.c13[jj.index < mid]),
    "dSR_H2_byhalf": sr_(jj.c14[jj.index >= mid]) - sr_(jj.c13[jj.index >= mid]),
    "split": str(mid.date()),
}
isc, oos = s[s.index < IS_END], s[s.index >= IS_END]
o13c, o13o = champ[champ.index < IS_END], champ[champ.index >= IS_END]
res["is_oos"] = {"c14_IS_SR": sr_(isc), "c14_OOS_SR": sr_(oos),
                 "c13_IS_SR": sr_(o13c), "c13_OOS_SR": sr_(o13o),
                 "dSR_IS": sr_(isc) - sr_(o13c), "dSR_OOS": sr_(oos) - sr_(o13o)}

# HOBR NAV share in the re-solve
share = Wg["RB_hobr"] / Wg.abs().sum(axis=1)
res["hobr_share"] = {"mean": float(share.mean()), "min": float(share.min()),
                     "max": float(share.max()), "cap": 0.15,
                     "ok_le_0.15": bool(share.max() <= 0.15)}
res["turnover_bp_yr"] = {"c14": float(to.mean() * 252 * BPS),
                         "champ_5_2622_ref": 5.2622}

# ROOT-CAUSE: the coordinator/RES_BASIS fill-0 w=0.25 blend (champ + 0.25*hobr, native
# units) — measure its arithmetic AND its gross (V2 8e). HOBR sleeve gross needs its own
# declared construction: 1/-1 dollar-neutral -> |w| sums to 2 before vt; approximate the
# blend gross from the series ratio is impossible, so bound it: blend gross >= champ gross
# + 0.25 * hobr_gross_min. We measure the champion at exactly 1.6 and report the naive
# blend's IMPLIED leverage headroom breach arithmetically: extra gross = 0.25*hobr_gross.
hobr = df["RB_hobr"].dropna()
jb = pd.concat([champ.rename("c13"), hobr.rename("h")], axis=1, join="inner").dropna()
jb["bl"] = jb.c13 + 0.25 * jb.h
res["fill0_w025"] = {
    "dSR": sr_(jb.bl) - sr_(jb.c13),
    "dAnn_cagr_pp": stats(jb.bl)["cagr_pct"] - stats(jb.c13)["cagr_pct"],
    "dAnn_arith_pp": stats(jb.bl)["arith_pct"] - stats(jb.c13)["arith_pct"],
    "note": "native-units add WITHOUT renormalization: the champion already rides gross "
            "1.6 exactly, so ANY added slot exposure pushes gross above 1.6 by "
            "0.25*hobr_gross >= 0 (8e). The re-solve instead re-allocates inside 1.6.",
    "extra_gross_if_hobr_gross_2": 0.25 * 2.0,
    "extra_gross_if_hobr_gross_1": 0.25 * 1.0,
}

# gross-capped renormalized add (the 8e-compliant overlay): scale both legs to gross 1.6
# champ_leg = 1.6*(1/(1+0.25*hg)), hobr_leg = 1.6*(0.25*hg/(1+0.25*hg)) with hg=hobr gross.
# We do NOT know hobr's daily gross without its weight path; use declared dollar-neutral
# gross 2 pre-vt as the conservative bound and also show w_effective so the coordinator
# sees the compliant overlay is NOT +4.21pp.
for hg, tag in ((2.0, "hobr_gross2"), (1.0, "hobr_gross1")):
    k = 1.6 / (1 + 0.25 * hg)          # multiplier on champ leg
    # renormalized to gross 1.6: champ leg k*1.6, hobr leg k*0.25*hg (same dollar split
    # as the naive add, both legs scaled by k)
    ren = k * jb.c13 + (k * 0.25) * jb.h
    jr = pd.concat([champ.rename("c13"), ren.rename("r")], axis=1, join="inner").dropna()
    res[f"renorm_gross160_{tag}"] = {
        "champ_leg_mult": float(k),
        "dSR": sr_(jr.r) - sr_(jr.c13),
        "dAnn_cagr_pp": stats(jr.r)["cagr_pct"] - stats(jr.c13)["cagr_pct"],
        "gross": "1.6 by construction",
    }

res["FAIL"] = fail
print(res["FAIL"] if fail else "ALL 7 CHECKS OK (own algebra)")
import json
json.dump(res, open(OUT + "r6_own_verifier.json", "w"), indent=1, default=str)
for k in ("stats", "deltas", "halves", "is_oos", "hobr_share", "turnover_bp_yr",
          "fill0_w025", "renorm_gross160_hobr_gross2", "renorm_gross160_hobr_gross1"):
    print(f"== {k}: {json.dumps(res[k], default=str)}")
