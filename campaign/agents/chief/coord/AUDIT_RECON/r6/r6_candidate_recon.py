#!/usr/bin/env python3
"""AUDIT_RECON R6 charter (a): independent reconciliation of the CAMP_COST 14-sleeve
CANDIDATE book (RAWEW14_HOBR) vs the champion of record — own algebra only.

No imports of CAMP_COST scripts or bt/verify_champion: every number below is computed
from the raw 14 sleeve CSVs + the committed champion CSV with THIS file's own code.

Construction under test (documented in rawew13v2_build.py, mirrored verbatim):
  relw_i = max(IS_SR_i,0)^0.55 on <2017-01-01; nav=(1+r).cumprod().shift(1).fillna(1);
  d2 = nav/rowmean * relw, row-normalized to sum 14, Wg = d2*1.6/14;
  net = sum(w*r) - |dW|.sum(1)*6.4bp - (1.6-1)*4.5%/252 ; day-1 entry uncharged.
"""
import hashlib
import json
import math
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/campaign/agents/chief/coord/AUDIT_RECON/r6"

CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
CAND = f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv"
CANDW = f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_weights.csv"
HOBR = f"{ROOT}/campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv"

SLEEVES = {
    "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
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
    "RB_hobr": HOBR[len(ROOT) + 1:],
}
GEAR, RATE, BPS, P = 1.6, 0.045, 6.4, 0.55
IS_END = pd.Timestamp("2017-01-01")
START = "2008-03-31"
MARGIN = (GEAR - 1) * RATE / 252

rep = {"checks": {}, "notes": []}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


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


def build(frame=None, hobr_override=None):
    if frame is None:
        frame = pd.DataFrame({n: load(p).dropna() for n, p in SLEEVES.items()})
        frame = frame[frame.index >= START]
    isr = frame[frame.index < IS_END]
    relw = pd.Series({n: max(is_sr(isr[n]), 0.0) ** P for n in frame.columns})
    if hobr_override is not None:
        relw = relw.copy()
        relw["RB_hobr"] = float(hobr_override)
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(frame.columns)
    Wg = d2 * (GEAR / len(frame.columns))
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    net = pd.Series(port, index=frame.index) - to * BPS / 1e4 - MARGIN
    return net, relw, Wg, to, frame


def sr(x):
    x = x.dropna()
    return x.mean() / x.std(ddof=1) * np.sqrt(252)


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {
        "n": int(len(r)), "start": str(r.index[0].date()), "end": str(r.index[-1].date()),
        "ann_cagr_pct": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
        "sr": float(sr(r)), "mdd_pct": mdd * 100,
        "neg_years": int((yr < 0).sum()), "worst_year_pct": float(yr.min() * 100),
        "n_years": int(len(yr)),
    }


def fisher_p(r, n):
    z = math.atanh(max(-0.999999, min(0.999999, r))) * math.sqrt(n - 3)
    return math.erfc(abs(z) / math.sqrt(2))


def leak_verdict(c, p, lag_scan):
    argmax = max(lag_scan, key=lambda k: lag_scan[k])
    return bool(abs(c) >= 0.20 and p < 0.05 and argmax == "0")


# ---------------------------------------------------------------- inputs + rebuild
net14, relw, Wg, to, frame = build()
cand = load("campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv")
candw = pd.read_csv(CANDW, index_col=0).iloc[:, 0]
champ = load("campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")

rep["input_shas_t0"] = {k: sha16(f"{ROOT}/{v}") for k, v in SLEEVES.items()}
rep["input_shas_t0"]["champion"] = sha16(CHAMP)
rep["input_shas_t0"]["candidate_csv"] = sha16(CAND)
rep["input_shas_t0"]["candidate_weights"] = sha16(CANDW)

# 1. byte/weights repro of the CANDIDATE book
j = pd.concat([cand.rename("csv"), net14.rename("mine")], axis=1, join="inner").dropna()
byte_dev = float((j.csv - j.mine).abs().max())
wr_dev = float((candw - relw).abs().max())
rep["checks"]["candidate_byte_repro"] = {"max_dev": byte_dev, "n": len(j), "ok": byte_dev < 1e-12}
rep["checks"]["candidate_weights_repro"] = {"max_dev": wr_dev, "ok": wr_dev < 1e-9}

# 2. cost reconciliation: implied cost from csv vs my FULL |dW|*6.4bp
port = (frame.fillna(0).values * Wg.values).sum(axis=1)
port = pd.Series(port, index=frame.index)
implied_cost = port - j.csv - MARGIN          # cost the committed csv actually charges
my_cost_full = to.reindex(j.index) * BPS / 1e4
my_cost_half = my_cost_full * 0.5
d_full = float((implied_cost - my_cost_full).abs().max())
d_half = float((implied_cost - my_cost_half).abs().max())
ratio = float((implied_cost / my_cost_full).replace([np.inf, -np.inf], np.nan).mean())
bp_yr = float(to.mean() * 252 * BPS)
day1_implied = float(implied_cost.iloc[0])
rep["checks"]["cost_reconciliation"] = {
    "model": "full_dw", "max_dev_full": d_full, "max_dev_half": d_half,
    "implied_over_full_ratio": ratio, "charged_bp_per_year": bp_yr,
    "day1_entry_charged_bp": day1_implied * 1e4,
    "day1_entry_uncharged_convention": abs(day1_implied) < 1e-9,
    "full_wins": d_full < d_half,
}

# 3. causality: same-day rebuild must MISMATCH; truncation invariance must hold
nav_sameday = (1 + frame.fillna(0)).cumprod().fillna(1.0)
d2s = nav_sameday.div(nav_sameday.mean(axis=1), axis=0).mul(relw, axis=1)
d2s = d2s.div(d2s.sum(axis=1), axis=0) * len(frame.columns)
Wg_sameday = d2s * (GEAR / len(frame.columns))
sameday_dev = float((Wg_sameday - Wg).abs().max().max())

def weight_path(frame_x, relw_x):
    """Weight path only, relw FROZEN (mirrors verify_champion: weights are an input,
    not recomputed from the perturbed frame's ISR)."""
    nav = (1 + frame_x.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw_x, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(frame_x.columns)
    return d2 * (GEAR / len(frame_x.columns))

probes = [0, 1, 2, 1201, 2402, 3603, 4804]
trunc = []
for t in probes:
    fz2 = frame.copy()
    fz2.iloc[t:] = 0.0
    Wz = weight_path(fz2, relw)
    dev = float((Wz.iloc[t] - Wg.iloc[t]).abs().max())
    trunc.append({"t": t, "date": str(frame.index[t].date()), "dev": dev})
max_trunc = max(x["dev"] for x in trunc)
rep["checks"]["causality"] = {
    "mechanism": "nav.shift(1)", "sameday_max_dev": sameday_dev,
    "sameday_rejected": sameday_dev > 1e-6,
    "truncation_probes": trunc, "truncation_max_dev": max_trunc,
    "truncation_ok": max_trunc < 1e-15,
}

# 4. leak probes (own implementation of V2 s6b rule)
dW = Wg.diff()
book = j.csv  # committed candidate daily ret
fz = frame.fillna(0)
# scalar |dWg|
s_abs = dW.abs().sum(axis=1).reindex(j.index)
c_abs = float(np.corrcoef(s_abs, book)[0, 1]); n_abs = int(len(j))
ls_abs = {}
for k in range(-2, 3):
    ls_abs[str(k)] = float(np.corrcoef(s_abs, book.shift(k))[0, 1])
# scalar signed dWg
s_sig = dW.sum(axis=1).reindex(j.index)
c_sig = float(np.corrcoef(s_sig, book)[0, 1])
ls_sig = {str(k): float(np.corrcoef(s_sig, book.shift(k))[0, 1]) for k in range(-2, 3)}
# wide per-slot: mean over 14 cols of corr(dW_i, r_i)
cols = list(frame.columns)
per_col_lag = {str(k): [] for k in range(-2, 3)}
for cname in cols:
    dw_c = dW[cname].reindex(j.index)
    r_c = fz[cname].reindex(j.index)
    for k in range(-2, 3):
        pair = pd.concat([dw_c, r_c.shift(k)], axis=1).dropna()
        per_col_lag[str(k)].append(float(np.corrcoef(pair.iloc[:, 0], pair.iloc[:, 1])[0, 1]))
wide_meas = {k: [x for x in v if np.isfinite(x)] for k, v in per_col_lag.items()}
wide_lag = {k: float(np.mean(v)) for k, v in wide_meas.items()}  # zero-weight slots (dW==0) excluded: corr undefined
c_wide = wide_lag["0"]
p_wide = fisher_p(c_wide, n_abs)
# cross-sectional per-day corr (R2 leak signature: +0.78 leaked / -0.03 causal)
xsec = []
dWj = dW.reindex(j.index); fzj = fz.reindex(j.index)
for t in range(len(j)):
    a, b = dWj.iloc[t].values, fzj.iloc[t].values
    if np.std(a) > 1e-12 and np.std(b) > 1e-12:
        xsec.append(float(np.corrcoef(a, b)[0, 1]))
rep["checks"]["leak_probes"] = {
    "scalar_abs_dWg": {"corr": c_abs, "p": fisher_p(c_abs, n_abs), "lag_scan": ls_abs,
                       "leak": leak_verdict(c_abs, fisher_p(c_abs, n_abs), ls_abs)},
    "scalar_signed_dWg": {"corr": c_sig, "lag_scan": ls_sig,
                          "leak": leak_verdict(c_sig, fisher_p(c_sig, n_abs), ls_sig)},
    "wide14_per_slot_mean": {"corr_lag0": c_wide, "p": p_wide, "lag_scan": wide_lag,
                             "leak": leak_verdict(c_wide, p_wide, wide_lag),
                             "n_slots_measurable": len(wide_meas["0"]),
                             "n_slots_excluded_zero_weight": 14 - len(wide_meas["0"])},
    "xsec_mean_per_day_corr_dW_r": float(np.mean(xsec)),
    "xsec_note": "R2 pins: +0.7846 leaked vintage / -0.0277 causal champion",
}

# 5. gates on the candidate book
gross = Wg.abs().sum(axis=1)
yr = book.groupby(book.index.year).apply(lambda x: (1 + x).prod() - 1)
nav_c = (1 + book).cumprod()
mdd = float((nav_c / nav_c.cummax() - 1).min())
share = (Wg["RB_hobr"] / gross)
rep["checks"]["gates"] = {
    "gross_max": float(gross.max()), "gross_mean": float(gross.mean()),
    "n_over_1p6": int((gross > GEAR + 1e-9).sum()),
    "margin_implied_pct_yr": float((port - j.csv - (to * BPS / 1e4)).mean() * 252 * 100 * -1),
    "neg_years": int((yr < 0).sum()), "worst_year_pct": float(yr.min() * 100),
    "mdd_pct": mdd * 100,
    "hobr_share_min_mean_max": [float(share.min()), float(share.mean()), float(share.max())],
    "hobr_share_cap_015_ok": bool(share.max() <= 0.15),
}

# 6. deltas vs champion of record (inner span), book SR halves + IS/OOS
jc = pd.concat([champ.rename("c13"), j.csv.rename("c14")], axis=1, join="inner").dropna()
s13, s14 = stats(jc.c13), stats(jc.c14)
mid = jc.index[len(jc) // 2]
h1o, h2o = sr(jc.c13[jc.index < mid]), sr(jc.c13[jc.index >= mid])
h1n, h2n = sr(jc.c14[jc.index < mid]), sr(jc.c14[jc.index >= mid])
isc, oos = jc.c14[jc.c14.index < IS_END], jc.c14[jc.c14.index >= IS_END]
corr_champ = float(np.corrcoef(jc.c13, jc.c14)[0, 1])
# hobr sleeve itself vs champion
hb = fz["RB_hobr"]
ji = pd.concat([champ.rename("c"), hb.rename("h")], axis=1, join="inner").dropna()
corr_hobr_champ = float(np.corrcoef(ji.c, ji.h)[0, 1])
midh = ji.index[len(ji) // 2]
rep["deltas_vs_champion"] = {
    "span": {"n": len(jc), "start": str(jc.index[0].date()), "end": str(jc.index[-1].date())},
    "c13": s13, "c14": s14,
    "dSR": s14["sr"] - s13["sr"],
    "dAnn_pp": s14["ann_cagr_pct"] - s13["ann_cagr_pct"],
    "dMDD_pp": s14["mdd_pct"] - s13["mdd_pct"],
    "book_halves": {"split": str(mid.date()), "c13_H1": h1o, "c13_H2": h2o,
                    "c14_H1": h1n, "c14_H2": h2n,
                    "dH1": h1n - h1o, "dH2": h2n - h2o},
    "c14_IS_SR": float(sr(isc)), "c14_IS_n": len(isc),
    "c14_OOS_SR": float(sr(oos)), "c14_OOS_n": len(oos),
    "corr_c14_vs_c13": corr_champ,
    "hobr_sleeve": {
        "n": int(len(hb.dropna())), "first": str(hb.dropna().index[0].date()),
        "last": str(hb.dropna().index[-1].date()),
        "corr_vs_champ": corr_hobr_champ,
        "halves_H1": float(sr(ji.h[ji.index < midh])), "halves_H2": float(sr(ji.h[ji.index >= midh])),
        "halves_split": str(midh.date()),
    },
}
rep["blend_w025_reference"] = {
    "note": "coordinator preamble construction: fixed 25% fill-0 blend of the hobr sleeve with the champion",
    "hb_aligned": float(hb.reindex(jc.index).fillna(0.0).sum() != 0),
}
hb_n = hb.dropna()
hb_ann = float(((1 + hb_n).prod() ** (252 / len(hb_n)) - 1) * 100)
hb_vol = float(hb_n.std(ddof=1) * np.sqrt(252) * 100)
champ_vol = float(jc.c13.std(ddof=1) * np.sqrt(252) * 100)
isoos = {}
for lbl, msk in [("IS(<2017-01-01)", jc.index < IS_END), ("OOS(>=2017-01-01)", jc.index >= IS_END)]:
    isoos[lbl] = float(sr(ji.h[msk]))
cal_mid = hb_n.index[0] + (hb_n.index[-1] - hb_n.index[0]) / 2
rep["blend_w025_reference"]["hobr_sleeve_conventions"] = {
    "ann_cagr_pct": hb_ann, "vol_pct": hb_vol, "champ_vol_pct": champ_vol,
    "vol_ratio_champ_over_hobr": champ_vol / hb_vol,
    "halves_index_midpoint": {"H1": float(sr(ji.h[ji.index < midh])),
                              "H2": float(sr(ji.h[ji.index >= midh])),
                              "split": str(midh.date())},
    "halves_calendar_midpoint": {"H1": float(sr(ji.h[ji.index < cal_mid])),
                                 "H2": float(sr(ji.h[ji.index >= cal_mid])),
                                 "split": str(pd.Timestamp(cal_mid).date())},
    "is_oos_at_2017": isoos,
}

w = 0.25
blend = (1 - w) * jc.c13 + w * hb.reindex(jc.index).fillna(0.0)
sb = stats(blend)
sc = champ_vol / hb_vol
hb_vm = hb * sc
bl_vm = (1 - w) * jc.c13 + w * hb_vm.reindex(jc.index).fillna(0.0)
sb_vm = stats(bl_vm)
rep["blend_w025_reference"]["vol_matched_w025"] = {
    "scale": sc, "blend": sb_vm,
    "dSR": sb_vm["sr"] - s13["sr"],
    "dAnn_pp": sb_vm["ann_cagr_pct"] - s13["ann_cagr_pct"],
    "dMDD_pp": sb_vm["mdd_pct"] - s13["mdd_pct"],
    "neg_years": sb_vm["neg_years"],
}
rep["blend_w025_reference"].update({
    "w": w, "blend": sb,
    "dSR": sb["sr"] - s13["sr"], "dAnn_pp": sb["ann_cagr_pct"] - s13["ann_cagr_pct"],
    "dMDD_pp": sb["mdd_pct"] - s13["mdd_pct"], "neg_years": sb["neg_years"],
})

# 7. rung grid (8g): bisection on hobr relw override to hit target mean capital share
def hobr_mean_share(ov):
    _, _, Wx, _, _ = build(frame, hobr_override=ov)
    gx = Wx.abs().sum(axis=1)
    return float((Wx["RB_hobr"] / gx).mean())

rungs = []
for target in [0.05, 0.10, 0.15]:
    lo, hi = 0.0, 5.0
    for _ in range(40):
        midv = (lo + hi) / 2
        if hobr_mean_share(midv) < target:
            lo = midv
        else:
            hi = midv
    ov = (lo + hi) / 2
    nx, _, _, _, _ = build(frame, hobr_override=ov)
    jj = pd.concat([jc.c13.rename("c13"), nx.rename("c14")], axis=1, join="inner").dropna()
    sx = stats(jj.c14)
    nav_x = (1 + jj.c14).cumprod()
    mddx = float((nav_x / nav_x.cummax() - 1).min())
    yrx = jj.c14.groupby(jj.c14.index.year).apply(lambda v: (1 + v).prod() - 1)
    rungs.append({"target_share": target, "achieved_share": hobr_mean_share(ov),
                  "relw_override": ov, "dAnn_pp": sx["ann_cagr_pct"] - s13["ann_cagr_pct"],
                  "dSR": sx["sr"] - s13["sr"], "dMDD_pp": mddx * 100 - s13["mdd_pct"],
                  "neg_years": int((yrx < 0).sum())})
nat_share = float(share.mean())
rungs.append({"target_share": "natural(adopted)", "achieved_share": nat_share,
              "relw_override": float(relw["RB_hobr"]),
              "dAnn_pp": s14["ann_cagr_pct"] - s13["ann_cagr_pct"],
              "dSR": s14["sr"] - s13["sr"], "dMDD_pp": s14["mdd_pct"] - s13["mdd_pct"],
              "neg_years": s14["neg_years"]})
rep["rung_grid_8g"] = rungs

# 8. placebo convention split (8h reconciliation: coordinator 169/200 vs CAMP_COST 0/200)
rng = np.random.default_rng(0)
NDRAW = 200
hb_full = fz["RB_hobr"].copy()
base_vals = hb_full.values
n_h = len(base_vals)
real_fixed = rep["blend_w025_reference"]["dSR"]
real_natural = rep["deltas_vs_champion"]["dSR"]
cnt_fixed_ge = cnt_fixed_pos = 0
cnt_nat_ge = cnt_nat_pos = 0
null_fixed, null_nat = [], []
for d in range(NDRAW):
    sh = np.roll(base_vals, int(rng.integers(1, n_h)))
    hs = pd.Series(sh, index=hb_full.index)
    # (a) fixed w=0.25 fill-0 blend
    bl = (1 - w) * jc.c13 + w * hs.reindex(jc.index).fillna(0.0)
    d0 = sr(bl) - s13["sr"]
    null_fixed.append(d0)
    cnt_fixed_ge += d0 >= real_fixed
    cnt_fixed_pos += d0 > 0
    # (b) full re-solve (natural relw recomputed from shifted stream)
    fn = pd.DataFrame({n: load(p).dropna() for n, p in SLEEVES.items()})
    fn = fn[fn.index >= START]
    fn.loc[fn.index >= hb_full.index[0], "RB_hobr"] = hs.reindex(
        fn.index[fn.index >= hb_full.index[0]]).values
    nx, _, _, _, _ = build(fn)
    jj = pd.concat([jc.c13.rename("c13"), nx.rename("c14")], axis=1, join="inner").dropna()
    d1 = sr(jj.c14) - s13["sr"]
    null_nat.append(d1)
    cnt_nat_ge += d1 >= real_natural
    cnt_nat_pos += d1 > 0
rep["placebo_reconciliation"] = {
    "instrument": f"circular shift of RB_hobr stream, {NDRAW} draws, seed 0",
    "fixed_w025_blend": {"null_dSR_p50": float(np.median(null_fixed)),
                         "real_dSR": real_fixed,
                         "frac_null_ge_real": cnt_fixed_ge / NDRAW,
                         "frac_null_positive": cnt_fixed_pos / NDRAW},
    "full_resolve_natural": {"null_dSR_p50": float(np.median(null_nat)),
                             "real_dSR": real_natural,
                             "frac_null_ge_real": cnt_nat_ge / NDRAW,
                             "frac_null_positive": cnt_nat_pos / NDRAW},
    "note": "reconciles coordinator 169/200 (w=0.25 fixed blend) vs CAMP_COST 0/200 (re-solve)",
}

with open(f"{OUT}/r6_candidate_recon.json", "w") as f:
    json.dump(rep, f, indent=1, default=float)

p = rep["checks"]
print(f"T0 champion sha {rep['input_shas_t0']['champion']}  candidate csv {rep['input_shas_t0']['candidate_csv']}")
print(f"1. candidate byte_repro max_dev {p['candidate_byte_repro']['max_dev']:.3e} (n={p['candidate_byte_repro']['n']}) ok={p['candidate_byte_repro']['ok']}")
print(f"   weights_repro  max_dev {p['candidate_weights_repro']['max_dev']:.3e} ok={p['candidate_weights_repro']['ok']}")
c = p["cost_reconciliation"]
print(f"2. cost: full_dw max_dev {c['max_dev_full']:.3e} | half max_dev {c['max_dev_half']:.3e} | ratio {c['implied_over_full_ratio']:.12f} | {c['charged_bp_per_year']:.4f} bp/yr | day1 charged {c['day1_entry_charged_bp']:.2e} bp")
ca = p["causality"]
print(f"3. causality: sameday dev {ca['sameday_max_dev']:.3e} (rejected={ca['sameday_rejected']}) truncation max {ca['truncation_max_dev']:.1e} ok={ca['truncation_ok']}")
lk = p["leak_probes"]
print(f"4. leak: |dWg| corr {lk['scalar_abs_dWg']['corr']:+.4f} leak={lk['scalar_abs_dWg']['leak']} | signed {lk['scalar_signed_dWg']['corr']:+.4f} leak={lk['scalar_signed_dWg']['leak']} | wide14 {lk['wide14_per_slot_mean']['corr_lag0']:+.4f} leak={lk['wide14_per_slot_mean']['leak']} | xsec {lk['xsec_mean_per_day_corr_dW_r']:+.4f}")
g = p["gates"]
print(f"5. gates: gross max {g['gross_max']:.13f} n_over {g['n_over_1p6']} negyr {g['neg_years']} worst {g['worst_year_pct']:.4f}% MDD {g['mdd_pct']:.4f}% hobr share {g['hobr_share_min_mean_max']} cap_ok={g['hobr_share_cap_015_ok']}")
d = rep["deltas_vs_champion"]
print(f"6. deltas: dSR {d['dSR']:+.4f} dAnn {d['dAnn_pp']:+.4f}pp dMDD {d['dMDD_pp']:+.4f}pp | book halves c13 {d['book_halves']['c13_H1']:.3f}/{d['book_halves']['c13_H2']:.3f} c14 {d['book_halves']['c14_H1']:.3f}/{d['book_halves']['c14_H2']:.3f} | IS {d['c14_IS_SR']:.4f} OOS {d['c14_OOS_SR']:.4f} | corr14 {d['corr_c14_vs_c13']:+.4f}")
print(f"   hobr sleeve: n={d['hobr_sleeve']['n']} {d['hobr_sleeve']['first']}..{d['hobr_sleeve']['last']} corr {d['hobr_sleeve']['corr_vs_champ']:+.4f} halves H1 {d['hobr_sleeve']['halves_H1']:.3f} H2 {d['hobr_sleeve']['halves_H2']:.3f}")
b = rep["blend_w025_reference"]
print(f"   blend w=0.25 fill-0 reference: dSR {b['dSR']:+.4f} dAnn {b['dAnn_pp']:+.4f}pp dMDD {b['dMDD_pp']:+.4f}pp negyr {b['neg_years']}")
print("7. rung grid:")
for r in rungs:
    print(f"   {str(r['target_share']):>17s} achieved {r['achieved_share']:.5f} dAnn {r['dAnn_pp']:+.3f}pp dSR {r['dSR']:+.4f} dMDD {r['dMDD_pp']:+.3f}pp negyr {r['neg_years']}")
pr = rep["placebo_reconciliation"]
print(f"8. placebo: fixed w025 null p50 {pr['fixed_w025_blend']['null_dSR_p50']:.4f} real {pr['fixed_w025_blend']['real_dSR']:.4f} frac>=real {pr['fixed_w025_blend']['frac_null_ge_real']:.3f} | re-solve null p50 {pr['full_resolve_natural']['null_dSR_p50']:.4f} real {pr['full_resolve_natural']['real_dSR']:.4f} frac>=real {pr['full_resolve_natural']['frac_null_ge_real']:.3f}")
cv = b["hobr_sleeve_conventions"]
print(f"   hobr conventions: ann {cv['ann_cagr_pct']:.2f}% vol {cv['vol_pct']:.2f}% (champ {cv['champ_vol_pct']:.2f}%, ratio {cv['vol_ratio_champ_over_hobr']:.2f}x)")
print(f"     halves idx-mid {cv['halves_index_midpoint']['H1']:.3f}/{cv['halves_index_midpoint']['H2']:.3f} (split {cv['halves_index_midpoint']['split']}) | cal-mid {cv['halves_calendar_midpoint']['H1']:.3f}/{cv['halves_calendar_midpoint']['H2']:.3f} (split {cv['halves_calendar_midpoint']['split']}) | IS {isoos['IS(<2017-01-01)']:.3f} OOS {isoos['OOS(>=2017-01-01)']:.3f}")
vm = b["vol_matched_w025"]
print(f"   vol-matched w=0.25 blend: scale {vm['scale']:.2f}x dSR {vm['dSR']:+.4f} dAnn {vm['dAnn_pp']:+.4f}pp dMDD {vm['dMDD_pp']:+.4f}pp negyr {vm['neg_years']}")
print("relw14:", {k: round(v, 4) for k, v in relw.items()})
