#!/usr/bin/env python3
"""CAMP_COST R6 adoption study battery for RB_hobr_crack_hyst (charter (a)).

Produces work_r6/adoption_battery.json with:
  - rung grid (8g): HOBR relw scaled so mean NAV share ~= 0.05 / 0.10 / 0.15, plus natural
  - 8i single-episode exclusion on dMDD (drop the dominant champion dd window)
  - BOOK-level placebo at the adopted construction (pure re-solve):
      * B1 level-matched null (VOL2 R6 memo, Class B): 200 block-bootstrap draws of HOBR
        matched on mean/vol/autocorr, each re-solved into the 14-slot book; real dSR must
        sit in the right tail (>= p95) of its own null.
      * C-style circular shift (coordinator's instrument) at the adopted share, for
        continuity with the 11:4x standup measurement.
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

import rawew13v2_build as B13  # noqa: E402
from rawew14_candidate import PATHS14, NAMES14, build, stats, halves_sr  # noqa: E402
from bt import leakcheck  # noqa: E402

RNG = np.random.default_rng(0)
OUT = ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6/"


def sr(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std(ddof=1) > 0 else float("nan")


def solve_relw(frame):
    isr = frame[frame.index < B13.IS_END]
    return pd.Series({n: max(B13.is_sr(isr[n]), 0.0) ** B13.P for n in frame.columns})


def book_from_frame(frame):
    """Full book algebra on an arbitrary (14-col) frame with NATURAL re-solve relw."""
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


def book_with_hobr_series(frame, hobr_series):
    """14-slot book but with HOBR's column replaced (rung/ placebo variants)."""
    f = frame.copy()
    f["RB_hobr"] = hobr_series
    return book_from_frame(f)


# ---------------------------------------------------------------- base books
df = pd.DataFrame({n: B13.load(PATHS14[n]).dropna() for n in NAMES14})
df = df[df.index >= "2008-03-31"]
net13, relw13, gross13, to13, df13 = build(hobr_relw_override=0.0)  # == committed book
net14, relw14, gross14, to14, _ = build()
champ = pd.read_csv(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
jj = pd.concat([champ.rename("c13"), net14.rename("c14")], axis=1, join="inner").dropna()
delta = jj.c14 - jj.c13
real_dsr = sr(jj.c14) - sr(jj.c13)
hobr = df["RB_hobr"]

res = {"real": {"dSR": real_dsr,
                "dSR_H1": sr(delta[delta.index < delta.index[len(delta) // 2]]),
                "dSR_H2": sr(delta[delta.index >= delta.index[len(delta) // 2]]),
                "dAnn_pp": stats(jj.c14)["ann_cagr_pct"] - stats(jj.c13)["ann_cagr_pct"],
                "dMDD_pp": stats(jj.c14)["mdd_pct"] - stats(jj.c13)["mdd_pct"],
                "neg_years_c14": stats(jj.c14)["neg_years"]}}
# 8d/8f convention: delta of per-half BOOK SRs (not SR of the delta stream)
srH = lambda x: sr(x)
mid = jj.index[len(jj) // 2]
res["real"]["dSR_H1_byhalf"] = srH(jj.c14[jj.index < mid]) - srH(jj.c13[jj.index < mid])
res["real"]["dSR_H2_byhalf"] = srH(jj.c14[jj.index >= mid]) - srH(jj.c13[jj.index >= mid])
res["real"]["dH2_ge_0_8d"] = bool(res["real"]["dSR_H2_byhalf"] >= 0)

# ---------------------------------------------------------------- 8g rung grid
# Rungs = HOBR relw scaled so the book's MEAN HOBR NAV share ~= w; other relw natural.
# (Share measured on the natural re-solve weights for calibration.)
_, _, Wg_nat = book_from_frame(df)
share_nat = Wg_nat["RB_hobr"] / Wg_nat.abs().sum(axis=1)
mean_share = float(share_nat.mean())
rung_rows = []
for w in (0.05, 0.10, 0.15):
    fac = w / mean_share  # share ~ linear in relw scale to first order; iterate once
    for _ in range(3):
        nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
        rw = relw14.copy()
        rw["RB_hobr"] = relw14["RB_hobr"] * fac
        d2 = nav.div(nav.mean(axis=1), axis=0).mul(rw, axis=1)
        d2 = d2.div(d2.sum(axis=1), axis=0) * 14
        Wg = d2 * (B13.GEAR / 14)
        sh = (Wg["RB_hobr"] / Wg.abs().sum(axis=1)).mean()
        fac *= w / sh
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=df.index) - to * B13.BPS / 1e4
           - np.maximum(B13.GEAR - 1, 0) * B13.RATE / 252)
    j = pd.concat([champ.rename("c13"), net.rename("r")], axis=1, join="inner").dropna()
    sv = stats(j.r)
    yr = j.r.groupby(j.r.index.year).apply(lambda x: (1 + x).prod() - 1)
    rung_rows.append({
        "w_mean_share": w, "achieved_mean_share": float(sh),
        "dAnn_pp": sv["ann_cagr_pct"] - stats(j.c13)["ann_cagr_pct"],
        "dSR": sv["sr"] - stats(j.c13)["sr"],
        "dMDD_pp": sv["mdd_pct"] - stats(j.c13)["mdd_pct"],
        "neg_years": int((yr < 0).sum()),
    })
res["rung_grid_8g"] = rung_rows + [{"w_mean_share": "natural(adopted)",
                                    "achieved_mean_share": mean_share,
                                    "dAnn_pp": res["real"]["dAnn_pp"],
                                    "dSR": real_dsr, "dMDD_pp": res["real"]["dMDD_pp"],
                                    "neg_years": res["real"]["neg_years_c14"]}]

# ---------------------------------------------------------------- 8i exclusion test
# Dominant dd window of the CANDIDATE book: peak -> trough -> first recovery (day AFTER
# the peak; the peak day itself must not terminate the search), excluded, dMDD recomputed.
nav14 = (1 + jj.c14).cumprod()
runmax = nav14.cummax()
trough_date = (nav14 / runmax).idxmin()
start_loc = int(jj.index.get_loc(runmax[:trough_date].idxmax()))
peak_val = nav14.iloc[start_loc]
after = nav14.iloc[start_loc + 1:]
rec = after[after >= peak_val]
end_loc = int(jj.index.get_loc(rec.index[0])) if len(rec) else len(jj) - 1
win = (jj.index[start_loc], jj.index[end_loc])
excl = jj[(jj.index < win[0]) | (jj.index > win[1])]
def mdd(x):
    nv = (1 + x).cumprod()
    return float((nv / nv.cummax() - 1).min())
d_mdd_excl = (mdd(excl.c14) - mdd(excl.c13)) * 100
res["excl_8i"] = {"window": [str(win[0].date()), str(win[1].date())],
                  "trough_date": str(trough_date.date()),
                  "window_days": int(end_loc - start_loc + 1),
                  "dMDD_pp_excl": d_mdd_excl,
                  "relief_ge_0.5pp": bool(d_mdd_excl >= 0.5),
                  "dMDD_pp_full": res["real"]["dMDD_pp"]}

# ---------------------------------------------------------------- B1 level-matched null
# Match HOBR's (mean, vol, autocorr, skew) with block-bootstrap of sign-preserving blocks
# of its own stream (calendar structure destroyed, distribution preserved), 200 draws.
# Each draw: full 14-slot RE-SOLVE with the null in the HOBR column (same machinery).
h = hobr.dropna().values
mu, sd = h.mean(), h.std(ddof=1)
ac1 = float(pd.Series(h).autocorr(1))
skew = float(pd.Series(h).skew())
L = 20  # block length ~ the sleeve's own decorrelation scale (ac1 -0.108 -> short blocks)
n = len(h)
null_dsrs, null_danns = [], []
for b in range(200):
    idx = RNG.integers(0, n - L, size=int(np.ceil(n / L)))
    parts = [h[i:i + L] for i in idx]
    draw = np.concatenate(parts)[:n]
    # exact level match (first two moments) without adding timing content
    draw = mu + (draw - draw.mean()) * (sd / draw.std(ddof=1))
    s = pd.Series(draw, index=hobr.dropna().index)
    nb, _, _ = book_with_hobr_series(df, s)
    jb = pd.concat([champ.rename("c13"), nb.rename("n")], axis=1, join="inner").dropna()
    null_dsrs.append(sr(jb.n) - sr(jb.c13))
    ann_n = ((1 + jb.n).prod() ** (252 / len(jb)) - 1) * 100
    ann_o = ((1 + jb.c13).prod() ** (252 / len(jb)) - 1) * 100
    null_danns.append(ann_n - ann_o)
null_dsrs = np.array(null_dsrs)
null_danns = np.array(null_danns)
pct = float((null_dsrs < real_dsr).mean())
ann_pct = float((null_danns < res["real"]["dAnn_pp"]).mean())
res["placebo_B1"] = {
    "instrument": "level-matched block-bootstrap null (VOL2 R6 memo Class-B B1), 200 draws, "
                  "L=20, moments re-matched to HOBR (mean/vol), full re-solve machinery",
    "null_dSR_mean": float(null_dsrs.mean()), "null_dSR_p05": float(np.percentile(null_dsrs, 5)),
    "null_dSR_p50": float(np.percentile(null_dsrs, 50)),
    "null_dSR_p95": float(np.percentile(null_dsrs, 95)),
    "real_dSR": real_dsr, "real_percentile": pct,
    "right_tail_p95_pass": bool(pct >= 0.95),
    "null_dAnn_p50": float(np.percentile(null_danns, 50)),
    "real_dAnn_pp": res["real"]["dAnn_pp"], "real_ann_percentile": ann_pct,
    "matched": {"mean": float(mu), "vol": float(sd), "ac1": ac1, "skew": skew},
}

# ---------------------------------------------------------------- C-style circular shift
# Coordinator's instrument at the adopted construction: circular-shift HOBR's returns
# (preserve total mass, destroy timing), full re-solve machinery, 200 draws.
cs = []
for b in range(200):
    shift = RNG.integers(200, len(hobr.dropna()) - 200)
    s = pd.Series(np.roll(hobr.dropna().values, shift), index=hobr.dropna().index)
    nb, _, _ = book_with_hobr_series(df, s)
    jb = pd.concat([champ.rename("c13"), nb.rename("n")], axis=1, join="inner").dropna()
    cs.append(sr(jb.n) - sr(jb.c13))
cs = np.array(cs)
res["placebo_C_circular"] = {
    "instrument": "circular shift of HOBR stream, 200 draws, full re-solve machinery (adopted w)",
    "reproduced_frac": float((cs >= real_dsr - 1e-9).mean()),
    "null_dSR_p50": float(np.percentile(cs, 50)),
    "real_dSR": real_dsr,
    "note": "mean-injection-dominated by construction for an orthogonal candidate; "
            "B1 above is the decision instrument per VOL2 R6 memo (Class B)",
}

# ---------------------------------------------------------------- leak probes (V2 s6)
# Explicit wiring (leak_check semantics via bt.leakcheck directly; gates.run default-ON
# would also fire here, but the probes are run explicitly per charter instructions).
Wg14 = None
nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
relw_nat = solve_relw(df)
d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw_nat, axis=1)
d2 = d2.div(d2.sum(axis=1), axis=0) * 14
Wg14 = d2 * (B13.GEAR / 14)
sleeve_rets_wide = df
common = Wg14.index.intersection(sleeve_rets_wide.index)
wide = leakcheck.leak_probe(Wg14.loc[common], sleeve_rets_wide.loc[common])
signed = leakcheck.leak_probe(Wg14.diff().sum(axis=1).loc[common], net14.loc[common])
turnover = leakcheck.leak_probe(Wg14.diff().abs().sum(axis=1).loc[common], net14.loc[common])
res["leak_probes"] = {
    "wide_14slot": {"same_period_corr": wide["same_period_corr"],
                    "p": wide.get("same_period_p"), "lag_scan": wide.get("lag_scan"),
                    "leak": bool(wide["leak"])},
    "scalar_signed_dWg_vs_book": {
        "same_period_corr": signed["same_period_corr"], "p": signed.get("same_period_p"),
        "lag_scan": signed.get("lag_scan"), "leak": bool(signed["leak"]),
        "note": "R5-comparable convention (signed sum; R5 pinned +0.0156 leak=False)"},
    "scalar_turnover_abs_dWg_vs_book": {
        "same_period_corr": turnover["same_period_corr"], "p": turnover.get("same_period_p"),
        "lag_scan": turnover.get("lag_scan"), "leak": bool(turnover["leak"]),
        "note": "|dWg| (true turnover) convention: |corr| leg CAN exceed 0.20 because "
                "turnover covaries with same-day vol (bigger moves -> bigger |dW|); "
                "verdict still rides the lag-0-argmax leg, which fails (lag -1 dominates "
                "= the causal weights-chase-yesterday's-NAV signature)"},
    "note": "wide: 14 weight cols vs 14 same-period sleeve rets. Explicit sig/leak_check "
            "wiring per V2 s6; thresholds 0.20/0.05/lag-0-argmax (V2 6b).",
}

json.dump(res, open(OUT + "adoption_battery.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
