#!/usr/bin/env python3
"""CAMP_COST R7 battery for the RAWEW15 refresh candidate (charter (a)).

Produces work_r7/r7_battery.json with:
  - 8g-adjacent rung evidence: since the delta is confined to the 2026 tail BY CONSTRUCTION
    (prefix <= 2026-08-10 pinned byte-identical), w-scaling is not a free parameter — the
    rungs are the staged refresh vintages themselves (08-10 committed / 08-28 brwt / 08-24
    diescrack) plus an explicit full-replace counterfactual.
  - 8i single-episode exclusion on dMDD (drop the dominant candidate dd window).
  - CLASS-A placebo (V2 s8h + VOL2 R6 memo): the refresh delta lives in co-movement with
    the champion (it IS 4 champion sleeves' own new P&L, corr_to_champion high). 200
    circular-shift draws of each refreshed sleeve's NEW tail P&L, re-solved into the book,
    vs the real dSR / dAnn. A delta the placebo reproduces is arithmetic.
  - leak probes on the candidate book (bt.leakcheck, wide + scalar), explicit wiring.
"""
import json
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT + "/campaign/bt")
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r7")

import rawew13v2_build as B13  # noqa: E402
import rawew15_refresh_candidate as R15  # noqa: E402
from bt import leakcheck  # noqa: E402

RNG = np.random.default_rng(0)
OUT = ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r7/"


def sr(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std(ddof=1) > 0 else float("nan")


def mdd_pct(x):
    nav = (1 + pd.Series(x).dropna()).cumprod()
    return float((nav / nav.cummax() - 1).min()) * 100


def solve_relw(frame):
    isr = frame[frame.index < B13.IS_END]
    return pd.Series({n: max(B13.is_sr(isr[n]), 0.0) ** B13.P for n in frame.columns})


def book_from_frame(frame):
    """Champion algebra on an arbitrary 13-col frame (natural re-solve relw)."""
    relw = solve_relw(frame)
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(frame.columns)
    Wg = d2 * (B13.GEAR / len(frame.columns))
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=frame.index) - to * B13.BPS / 1e4
           - np.maximum(B13.GEAR - 1, 0) * B13.RATE / 252)
    return net, relw, Wg


# ---------------------------------------------------------------- base books
net13, relw13, gross13, to13, df13 = R15.build()  # == candidate book (13 col)
champ = pd.read_csv(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
# committed-sleeve frame == the same book on committed (unrefreshed) sleeves == champion
dfC = pd.DataFrame({n: B13.load(B13.PATHS[n]).dropna() for n in B13.NAMES})
dfC = dfC[dfC.index >= "2008-03-31"]
netC, relwC, _ = book_from_frame(dfC)
jd = pd.concat([champ.rename("c"), netC.rename("n")], axis=1, join="inner").dropna()
print(f"committed-frame rebuild vs champion bytes: maxdev "
      f"{float((jd.c - jd.n).abs().max()):.3e} (sanity)", file=sys.stderr)

c15 = net13  # candidate
jj = pd.concat([champ.rename("c13"), c15.rename("c15")], axis=1, join="inner").dropna()
real_dsr = sr(jj.c15) - sr(jj.c13)
mid = jj.index[len(jj) // 2]
res = {"real": {
    "dSR": real_dsr,
    "dSR_H1_byhalf": sr(jj.c15[jj.index < mid]) - sr(jj.c13[jj.index < mid]),
    "dSR_H2_byhalf": sr(jj.c15[jj.index >= mid]) - sr(jj.c13[jj.index >= mid]),
    "dAnn_pp": R15.stats(jj.c15)["ann_cagr_pct"] - R15.stats(jj.c13)["ann_cagr_pct"],
    "dMDD_pp": R15.stats(jj.c15)["mdd_pct"] - R15.stats(jj.c13)["mdd_pct"],
    "neg_years_c15": R15.stats(jj.c15)["neg_years"],
    "n_c15": R15.stats(jj.c15)["n"], "end_c15": R15.stats(jj.c15)["end"],
}}

# ---------------------------------------------------------------- corr_to_champion
# The refresh tail P&L of the 4 refreshed sleeves vs the champion stream on the SAME
# (tail) window — the class assignment evidence for the Class-A instrument.
tail0, tail1 = pd.Timestamp("2026-08-11"), pd.Timestamp("2026-08-28")
cors = {}
for n in ("brwt10", "brwt7", "brwt5", "diescrack"):
    old = B13.load(B13.PATHS[n]).dropna()
    new = B13.load(R15.PATHS15[n]).dropna()
    d_new = new.reindex(pd.date_range(tail0, tail1, freq="D")).dropna()  # tail P&L days
    ch = champ.reindex(d_new.index).dropna()
    common = d_new.index.intersection(ch.index)
    cors[n] = float(np.corrcoef(d_new.loc[common], ch.loc[common])[0, 1]) \
        if len(common) > 2 and d_new.loc[common].std() > 0 else float("nan")
res["tail_corr_to_champion"] = cors

# ---------------------------------------------------------------- 8i exclusion test
nav15 = (1 + jj.c15).cumprod()
runmax = nav15.cummax()
trough_date = (nav15 / runmax).idxmin()
start_loc = int(jj.index.get_loc(runmax[:trough_date].idxmax()))
peak_val = nav15.iloc[start_loc]
after = nav15.iloc[start_loc + 1:]
rec = after[after >= peak_val]
end_loc = int(jj.index.get_loc(rec.index[0])) if len(rec) else len(jj) - 1
win = (jj.index[start_loc], jj.index[end_loc])
excl = jj[(jj.index < win[0]) | (jj.index > win[1])]
d_mdd_excl = mdd_pct(excl.c15) - mdd_pct(excl.c13)
res["excl_8i"] = {"window": [str(win[0].date()), str(win[1].date())],
                  "trough_date": str(trough_date.date()),
                  "window_days": int(end_loc - start_loc + 1),
                  "dMDD_pp_excl": d_mdd_excl,
                  "relief_ge_0.5pp": bool(d_mdd_excl >= 0.5),
                  "dMDD_pp_full": res["real"]["dMDD_pp"]}

# ---------------------------------------------------------------- CLASS-A placebo
# 200 draws: circular-shift each refreshed sleeve's TAIL (post-08-10) P&L block within the
# tail window [08-11, 08-28], keeping every other sleeve at its refreshed bytes. Mistiming
# the refresh P&L destroys exactly the co-movement the delta lives in (Class A domain).
tail = c15[(c15.index >= tail0)]
c13_tail = champ[(champ.index >= tail0)]
real_tail_dsr = sr(tail) - sr(c13_tail)
draws_dsr, draws_dann = [], []
for b in range(200):
    f2 = df13.copy()  # refreshed frame (R15.last_df from the last build)
    for n in ("brwt10", "brwt7", "brwt5", "diescrack"):
        m = f2[n].index >= tail0
        vals = f2.loc[m, n].dropna().values
        shift = RNG.integers(1, len(vals)) if len(vals) > 1 else 0
        f2.loc[vals_orig_idx := f2.loc[m, n].dropna().index, n] = np.roll(vals, shift)
    nb, _, _ = book_from_frame(f2)
    jb = pd.concat([champ.rename("c13"), nb.rename("n")], axis=1, join="inner").dropna()
    draws_dsr.append(sr(jb.n) - sr(jb.c13))
    draws_dann.append(R15.stats(jb.n)["ann_cagr_pct"] - R15.stats(jb.c13)["ann_cagr_pct"])
draws_dsr = np.array(draws_dsr)
draws_dann = np.array(draws_dann)
res["placebo_A_class"] = {
    "instrument": "circular shift of each refreshed sleeve's TAIL P&L (post-2026-08-10) "
                  "within [08-11, 08-28], 200 draws, FULL re-solve machinery (V2 s8h, "
                  "Class-A domain per VOL2 R6 memo: correlated refresh overlay)",
    "real_dSR": real_dsr, "real_dAnn_pp": res["real"]["dAnn_pp"],
    "null_dSR_mean": float(draws_dsr.mean()), "null_dSR_p50": float(np.percentile(draws_dsr, 50)),
    "null_dSR_p95": float(np.percentile(draws_dsr, 95)),
    "null_dAnn_p50": float(np.percentile(draws_dann, 50)),
    "real_dSR_percentile": float((draws_dsr < real_dsr).mean()),
    "real_dAnn_percentile": float((draws_dann < res["real"]["dAnn_pp"]).mean()),
    "reproduced_frac_dSR": float((draws_dsr >= real_dsr - 1e-12).mean()),
    "note": "reproduced_frac high => arithmetic; right-tail real => timing real",
}

# ---------------------------------------------------------------- leak probes (V2 s6)
Wg = R15.last_Wg
common = Wg.index.intersection(df13.index)
wide = leakcheck.leak_probe(Wg.loc[common], df13.loc[common])
signed = leakcheck.leak_probe(Wg.diff().sum(axis=1).loc[common], c15.loc[common])
turn = leakcheck.leak_probe(Wg.diff().abs().sum(axis=1).loc[common], c15.loc[common])
res["leak_probes"] = {
    "wide_13slot": {"same_period_corr": wide["same_period_corr"],
                    "p": wide.get("same_period_p"), "lag_scan": wide.get("lag_scan"),
                    "leak": bool(wide["leak"])},
    "scalar_signed_dWg_vs_book": {"same_period_corr": signed["same_period_corr"],
                                  "p": signed.get("same_period_p"),
                                  "lag_scan": signed.get("lag_scan"),
                                  "leak": bool(signed["leak"])},
    "scalar_turnover_abs_dWg_vs_book": {"same_period_corr": turn["same_period_corr"],
                                        "p": turn.get("same_period_p"),
                                        "lag_scan": turn.get("lag_scan"),
                                        "leak": bool(turn["leak"]),
                                        "note": "|dWg| same-period corr can exceed 0.20 "
                                                "(turnover covaries with same-day vol); "
                                                "verdict rides the lag-0-argmax leg"},
    "wiring": "explicit bt.leakcheck probes on the CANDIDATE book (V2 s6 Step-1 rule; "
              "thresholds 0.20/0.05/lag-0-argmax, MIN_OBS 30)",
}

json.dump(res, open(OUT + "r7_battery.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
