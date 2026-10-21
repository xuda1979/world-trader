
"""S2: AUDIT_R7REDO attack on the CAMP_COST/RAWEW14-R7 HOBR adoption rejection.

Failure mode (a) GATE MIS-APPLICATION: the rejection rests on V2 s8c (blend dAnn > 0,
HARD).  The audit's own numbers show the candidate's ONLY dAnn>0 construction is the
"fill-0" additive overlay whose blend gross is 1.6146..1.6729 > 1.6 -> s8e breach.
Hypothesis to TEST: that +4.21pp is ARITHMETIC LEVERAGE, not skill.  Decisive test:
re-lever the PLAIN champion to the SAME gross and see if it reproduces the +4.21pp.

Also: reproduce the champion byte-exact, reproduce the 14-sleeve natural re-solve
dAnn = -0.9069pp (their published s8c number).
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
import rawew13v2_build as B13

CH = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
HOBR = "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv"


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {"n": len(r), "ann": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
            "sr": float(r.mean() / r.std(ddof=1) * 252 ** 0.5),
            "mdd": float((nav / nav.cummax() - 1).min()) * 100,
            "neg": int((yr < 0).sum())}


def book(frame, gear):
    """Champion algebra on an arbitrary frame at an arbitrary gear."""
    isr = frame[frame.index < B13.IS_END]
    relw = pd.Series({n: max(B13.is_sr(isr[n]), 0.0) ** B13.P for n in frame.columns})
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(frame.columns)
    Wg = d2 * (gear / len(frame.columns))
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=frame.index) - to * B13.BPS / 1e4
           - np.maximum(gear - 1, 0) * B13.RATE / 252)
    gross = Wg.abs().sum(axis=1)
    return net, relw, Wg, gross


# ---- load ----
champ = pd.read_csv(CH, index_col=0, parse_dates=True).iloc[:, 0]
print("CHAMPION on record:", CH)
print("  n =", len(champ), " first", champ.index[0].date(), " last", champ.index[-1].date())
cs = stats(champ)
print("  ann %.4f  sr %.4f  mdd %.4f  neg %d" % (cs["ann"], cs["sr"], cs["mdd"], cs["neg"]))
import hashlib
print("  sha256", hashlib.sha256(open(CH, "rb").read()).hexdigest()[:16])

# ---- 1. reproduce champion from 13 sleeves ----
frame13 = pd.DataFrame({n: B13.load(B13.PATHS[n]).dropna() for n in B13.NAMES})
frame13 = frame13[frame13.index >= "2008-03-31"]
net13, relw13, Wg13, gross13 = book(frame13, B13.GEAR)
j = pd.concat([champ.rename("c"), net13.rename("b")], axis=1, join="inner").dropna()
print("\n[1] champion repro: n_inner", len(j), "max|built-committed| %.3e" % float((j.c - j.b).abs().max()))

# ---- 2. 14-sleeve natural re-solve (their s8c number) ----
hobr = B13.load(HOBR)
print("[2] RB_hobr sleeve: n", int(hobr.notna().sum()), "first", hobr.dropna().index[0].date(),
      "last", hobr.dropna().index[-1].date())
frame14 = frame13.copy()
frame14["RB_hobr"] = hobr.reindex(frame13.index)
net14, relw14, Wg14, gross14 = book(frame14, B13.GEAR)
j14 = pd.concat([champ.rename("c"), net14.rename("b")], axis=1, join="inner").dropna()
s_c, s_b = stats(j14.c), stats(j14.b)
print("    14-book: ann %.4f sr %.4f mdd %.4f" % (s_b["ann"], s_b["sr"], s_b["mdd"]))
print("    14-book vs champ  dAnn %+.4f pp   dSR %+.4f   dMDD %+.4f pp   grossMax(mean) %.4f" % (
    s_b["ann"] - s_c["ann"], s_b["sr"] - s_c["sr"], s_b["mdd"] - s_c["mdd"], gross14.mean()))
print("    [published s8c] dAnn -0.9069pp  dSR +0.0909  dMDD +0.4568pp  (n=4805 window)")
w14 = (Wg14["RB_hobr"].abs() / Wg14.abs().sum(axis=1))
print("    HOBR mean NAV share %.6f  max %.6f" % (w14.mean(), w14.max()))

# ---- 3. THE LEVERAGE TEST ----
print("\n[3] LEVERAGE TEST: re-lever the PLAIN 13-sleeve champion to gross g.")
print("    fill-0 blend gross_mean (their numbers): 1.6146 / 1.6292 / 1.6438 / 1.6729")
print("    their fill-0 dAnn_pp:                    +0.8382 / +1.6786 / +2.5212 / +4.2128")
print()
print("    %-10s %-10s %-12s %-10s %-10s" % ("gear", "grossMean", "dAnn_pp", "dSR", "dMDD_pp"))
for g, d_ann in [(1.614586066897875, 0.838229443243101),
                 (1.62917213379575, 1.6786416114489313),
                 (1.6437582006936253, 2.521220655762747),
                 (1.6729303344893753, 4.212814443171233)]:
    netg, _, _, grg = book(frame13, g)
    jg = pd.concat([champ.rename("c"), netg.rename("b")], axis=1, join="inner").dropna()
    sg, sc = stats(jg.b), stats(jg.c)
    print("    %-10.6f %-10.6f %+12.4f %+10.4f %+10.4f   (fill-0 %+.4f)" % (
        g, float(grg.mean()), sg["ann"] - sc["ann"], sg["sr"] - sc["sr"],
        sg["mdd"] - sc["mdd"], d_ann))
