#!/usr/bin/env python3
"""CAMP_SHORT R6 — resolve the scalar leak-probe discrepancy (mine +0.2034 vs theirs +0.0156).

Tries every plausible reading of CAMP_COST's "scalar: aggregate |dWg| vs champion
same-period ret" and reports which (if any) reproduces their published
corr=+0.015600155730274267 (p=0.2795726814471842, n=4805). Also prints my lag scan.
"""
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
NAMES = ["brwt15", "brwt10", "brwt7", "brwt5", "C5ng", "C5ngsum", "A5r2", "a6r7",
         "QAxasts", "carryv2", "dualmom", "diescrack", "CFX4"]
PATHS = {
    "brwt15": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2": f"{ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2": f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": f"{ROOT}/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": f"{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}


def load_ret(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


THEIR = 0.015600155730274267
champ = load_ret(CHAMP)

for label, start in (("full-history", None), ("champ-span", "2008-03-31")):
    df = pd.DataFrame({n: load_ret(PATHS[n]).dropna() for n in NAMES})
    if start:
        df = df[df.index >= start]
    isr = df[df.index < pd.Timestamp("2017-01-01")]
    SR = pd.Series({n: is_sr(isr[n]) for n in NAMES})
    relw = np.maximum(SR, 0.0) ** 0.55
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (1.6 / len(NAMES))
    dWg = Wg.diff()
    variants = {
        "sum_absdW_fill0": dWg.abs().sum(axis=1).fillna(0.0),
        "sum_absdW_nankeep": dWg.abs().sum(axis=1),           # NaN row kept
        "mean_absdW": dWg.abs().mean(axis=1),
        "abs_of_sum_dW": dWg.sum(axis=1).abs(),
        "rel_turnover(sumabs/gross)": (dWg.abs().sum(axis=1) / Wg.abs().sum(axis=1)),
        "sumabs_of_relw_d2": (d2 * (1.6 / len(NAMES))).diff().abs().sum(axis=1),
        "sumabs_ungeared_d2": d2.diff().abs().sum(axis=1),
        "sqrt_dW2(l2)": np.sqrt((dWg ** 2).sum(axis=1)),
    }
    for vn, sc in variants.items():
        j = pd.concat([sc.rename("s"), champ.rename("r")], axis=1, join="inner").dropna()
        if len(j) < 30:
            print(f"[{label}] {vn:30s} n={len(j)} (too short)")
            continue
        c0 = float(j.s.corr(j.r))
        rho = float(j.s.rank().corr(j.r.rank()))
        lags = {}
        for lag in (-2, -1, 0, 1, 2):
            jj = pd.concat([j.s, j.r.shift(-lag)], axis=1).dropna()
            lags[lag] = float(jj.s.corr(jj.r))
        hit = "  <== MATCHES THEIRS" if abs(c0 - THEIR) < 1e-9 else ""
        argmax = max(lags.items(), key=lambda kv: abs(kv[1]))[0]
        print(f"[{label}] {vn:30s} n={len(j)} pearson={c0:+.6f} spearman={rho:+.4f} "
              f"argmax|corr| lag={argmax}{hit} lags={ {k: round(v,4) for k,v in lags.items()} }")
    print()
