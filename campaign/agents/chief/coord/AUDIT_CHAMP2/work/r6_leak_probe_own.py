#!/usr/bin/env python3
"""AUDIT_CHAMP2 R6 — own leak probe (no bt.leakcheck import) on the 14-slot candidate.

V2 6b thresholds: leak=True requires |same_period_corr|>=0.20 AND Fisher p<0.05 AND
lag 0 = argmax of lag scan -2..+2. Probes: wide (14 weight cols vs 14 sleeve rets),
scalar turnover |dWg| vs book ret, scalar signed dWg vs book ret.
"""
import json

import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/AUDIT_CHAMP2/work/"
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
    "RB_hobr": "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv",
}
GEAR, RATE, BPS, P, IS_END, START = 1.6, 0.045, 6.4, 0.55, "2017-01-01", "2008-03-31"


def load(p):
    d = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    d.index = pd.to_datetime(d.index)
    return d["ret" if "ret" in d.columns else d.columns[0]].astype(float)


def is_sr(r):
    r = r.dropna()
    return 0.0 if len(r) < 200 or r.std(ddof=1) <= 1e-12 else float(
        r.mean() / r.std(ddof=1) * np.sqrt(252))


df = pd.DataFrame({n: load(p).dropna() for n, p in SLEEVES.items()})
df = df[df.index >= START]
isr = df[df.index < IS_END]
relw = pd.Series({n: max(is_sr(isr[n]), 0.0) ** P for n in df.columns})
nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * len(relw)
Wg = d2 * (GEAR / len(relw))
port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
to = Wg.diff().abs().sum(axis=1).fillna(0.0)
net = port - to * BPS / 1e4 - max(GEAR - 1, 0) * RATE / 252


def probe(score, r):
    wide = isinstance(score, pd.DataFrame)
    s = score
    if wide:
        j = pd.concat([s, r.add_suffix("_r")], axis=1, join="inner").dropna()
        out = {"n": int(len(j))}
        for lag in (-2, -1, 0, 1, 2):
            rr = r.shift(-lag)
            jj = pd.concat([s, rr.add_suffix("_r")], axis=1, join="inner").dropna()
            cs = [float(jj[c_].corr(jj[c_ + "_r"])) for c_ in s.columns
                  if jj[c_].std() > 0 and jj[c_ + "_r"].std() > 0]
            out[f"corr_lag{lag}"] = float(np.mean(cs)) if cs else float("nan")
        per = [float(j[c_].corr(j[c_ + "_r"])) for c_ in s.columns]
        ok = [x for x in per if np.isfinite(x)]
        out["n_valid_cols"] = len(ok)
        out["const_cols_skipped"] = int(len(per) - len(ok))
        c = float(np.mean(ok))
        ps = [sps.pearsonr(j[c_], j[c_ + "_r"])[1] for c_ in s.columns
              if np.isfinite(j[c_].std()) and j[c_].std() > 0]
        p = float(np.mean(ps))
    else:
        j = pd.concat([s.rename("s"), r.rename("r")], axis=1, join="inner").dropna()
        out = {"n": int(len(j))}
        for lag in (-2, -1, 0, 1, 2):
            rr = r.shift(-lag)
            jj = pd.concat([j.s, rr.rename("r")], axis=1, join="inner").dropna()
            out[f"corr_lag{lag}"] = float(jj.s.corr(jj.r))
        c, p = sps.pearsonr(j.s, j.r)
    out["same_period_corr"], out["same_period_p"] = float(c), float(p)
    argmax = max((-2, -1, 0, 1, 2), key=lambda L: abs(out[f"corr_lag{L}"]))
    out["argmax_lag"] = argmax
    out["leak"] = bool(abs(c) >= 0.20 and p < 0.05 and argmax == 0)
    return out


res = {
    "wide_14col": probe(Wg.copy(), df.fillna(0.0)),
    "scalar_turnover_absdWg_vs_book": probe(to, net),
    "scalar_signed_dWg_vs_book": probe(Wg.diff().sum(axis=1), net),
    "thresholds": "V2 6b: |corr|>=0.20 AND p<0.05 AND lag0=argmax",
}
json.dump(res, open(OUT + "r6_leak_probe_own.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
