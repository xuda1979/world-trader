#!/usr/bin/env python3
"""AUDIT_CHAMP2 R6 — blend-convention root-cause + placebo probes (own code, own rng).

Root-causes the coordinator's +4.21pp / rung-grid dAnn>0 / 169-200 placebo numbers (fill-0
native-units convention) vs the certifiable 14-slot re-solve (dAnn -0.907pp). Also runs my
own B1-style block bootstrap + C-style circular shift in BOTH machineries.
"""
import json

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/AUDIT_CHAMP2/work/"
import importlib.util
spec = importlib.util.spec_from_file_location(
    "own", ROOT + "/campaign/agents/chief/coord/AUDIT_CHAMP2/work/r6_audit_champ2_candidate14.py")

# ---- reload the pieces I need from my own verifier module (no CAMP_COST imports) ----
SLEEVES13 = {k: v for k, v in
             {"brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
              "brwt10": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
              "brwt7": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
              "brwt5": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
              "C5ng": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
              "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
              "A5r2": "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
              "a6r7": "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
              "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
              "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
              "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
              "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
              "CFX4": "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
              "RB_hobr": "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv",
              }.items()}
GEAR, RATE, BPS, P = 1.6, 0.045, 6.4, 0.55
IS_END, START = "2017-01-01", "2008-03-31"


def load(p):
    d = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    d.index = pd.to_datetime(d.index)
    c = "ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float)


def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


def book(relw, df):
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
    Wg = d2 * (GEAR / len(relw))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = pd.Series(Wg.diff().abs().sum(axis=1), index=df.index).fillna(0.0)
    net = port - to * BPS / 1e4 - max(GEAR - 1, 0) * RATE / 252
    return pd.Series(net, index=df.index), Wg


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    return {"cagr_pct": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
            "arith_pct": float(r.mean() * 252 * 100),
            "sr": float(r.mean() / r.std(ddof=1) * np.sqrt(252)), "mdd_pct": mdd * 100}


sr_ = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(252)

df = pd.DataFrame({n: load(p).dropna() for n, p in SLEEVES13.items()})
df = df[df.index >= START]
champ = pd.read_csv(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
hobr = df["RB_hobr"]
res = {}

# ---------------------------------------------------------------- FILL-0 blends
# Convention A: inner join (hobr days only, n~4604). Convention B: reindex hobr onto
# champ's 4805 days, fillna(0) (RES_BASIS "champ+s*w" may use the champ index).
for tag, idx in (("inner_join", None), ("champ_index_fill0", champ.index)):
    h = hobr if idx is None else hobr.reindex(idx).fillna(0.0)
    c = champ if idx is None else champ.reindex(idx).dropna()
    cc = c.index
    h = h.reindex(cc)
    d = {}
    for w in (0.05, 0.10, 0.15, 0.25):
        bl = c + w * h
        sb, sc = stats(bl), stats(c)
        d[f"w{w}"] = {"dSR": sb["sr"] - sc["sr"], "dAnn_cagr_pp": sb["cagr_pct"] - sc["cagr_pct"],
                      "dAnn_arith_pp": sb["arith_pct"] - sc["arith_pct"],
                      "dMDD_pp": sb["mdd_pct"] - sc["mdd_pct"]}
    res[f"fill0_{tag}"] = d
    if tag == "champ_index_fill0":
        res["fill0_n"] = int(len(cc))

# ---------------------------------------------------------------- gross bound (8e)
# Champion gross == 1.6 exactly every day (my verifier). The fill-0 blend adds
# w*hobr gross on top -> blend gross = 1.6 + w*gross_hobr(t) > 1.6 for ANY w>0.
# Reconstruct hobr's approximate gross from its declared construction: dollar-neutral
# 1/-1 units (gross 2.0) scaled by trailing vt toward 8% ann vol. Lower-bound the extra
# gross conservatively by assuming the most favorable (smallest) plausible hobr gross.
res["gross_8e"] = {
    "champ_gross": "1.6 exact daily (my verifier: weights_max 1.600000000000001)",
    "fill0_blend_gross_lower_bound_at_w0.25": "1.6 + 0.25*min_t(gross_hobr_t) > 1.6 strictly",
    "hobr_gross_if_vt_untouched": 2.0,
    "note": "any additive overlay on a book AT the cap breaches the cap; the only "
            "8e-compliant constructions fund the new leg from the old book (re-solve) "
            "-> dAnn -0.907pp, or cut the champ leg (renormalize) -> measured below",
}
for hg in (2.0, 1.5, 1.0):
    k = GEAR / (GEAR + 0.25 * hg)
    c = champ
    h = hobr.reindex(c.index).fillna(0.0)
    bl = k * (c + 0.25 * h)
    sb, sc = stats(bl), stats(c)
    res[f"renorm16_hobrgross{hg}"] = {"champ_leg_mult": k, "dSR": sb["sr"] - sc["sr"],
                                      "dAnn_cagr_pp": sb["cagr_pct"] - sc["cagr_pct"],
                                      "dMDD_pp": sb["mdd_pct"] - sc["mdd_pct"]}

# ---------------------------------------------------------------- C-shift, fill-0
rng = np.random.default_rng(12345)
c = champ
h = hobr.reindex(c.index).fillna(0.0).values
real = stats(c + 0.25 * pd.Series(h, index=c.index))["sr"] - stats(c)["sr"]
nulls = []
for _ in range(200):
    s = pd.Series(np.roll(h, rng.integers(200, len(h) - 200)), index=c.index)
    nulls.append(stats(c + 0.25 * s)["sr"] - stats(c)["sr"])
nulls = np.array(nulls)
res["cshift_fill0_w025"] = {
    "real_dSR": real, "null_median": float(np.median(nulls)),
    "null_p05": float(np.percentile(nulls, 5)), "null_p95": float(np.percentile(nulls, 95)),
    "frac_null_ge_0.9x_real": float((nulls >= 0.9 * real).mean()),
    "frac_null_ge_real_minus_1e-9": float((nulls >= real - 1e-9).mean()),
    "interpretation": "circular shift preserves the mean EXACTLY -> fill-0 delta is "
                      "mean-injection-dominated (coordinator's 169/200)",
}

# ---------------------------------------------------------------- B1 block boot, re-solve
relw14 = pd.Series({n: max(is_sr(df[df.index < IS_END][n]), 0.0) ** P for n in df.columns})
net14, _ = book(relw14, df)
jj = pd.concat([champ.rename("c13"), net14.rename("c14")], axis=1, join="inner").dropna()
real_rs = sr_(jj.c14) - sr_(jj.c13)
hh = hobr.dropna()
mu, sd = hh.mean(), hh.std(ddof=1)
nulls2 = []
rng2 = np.random.default_rng(777)
for b in range(120):
    idx = rng2.integers(0, len(hh) - 20, size=int(np.ceil(len(hh) / 20)))
    draw = np.concatenate([hh.values[i:i + 20] for i in idx])[:len(hh)]
    draw = mu + (draw - draw.mean()) * (sd / draw.std(ddof=1))
    dfb = df.copy()
    dfb["RB_hobr"] = pd.Series(draw, index=hh.index)
    rl = pd.Series({n: max(is_sr(dfb[dfb.index < IS_END][n]), 0.0) ** P for n in dfb.columns})
    nb, _ = book(rl, dfb)
    jb = pd.concat([champ.rename("c13"), nb.rename("n")], axis=1, join="inner").dropna()
    nulls2.append(sr_(jb.n) - sr_(jb.c13))
nulls2 = np.array(nulls2)
res["b1_blockboot_resolve"] = {
    "real_dSR": real_rs, "n_draws": 120, "L": 20,
    "null_median": float(np.median(nulls2)), "null_p95": float(np.percentile(nulls2, 95)),
    "frac_null_ge_real": float((nulls2 >= real_rs).mean()),
    "real_percentile": float((nulls2 < real_rs).mean()),
}

json.dump(res, open(OUT + "r6_blend_probes.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
