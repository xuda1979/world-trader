
"""S3: HOBR (RAWEW14-R7) — is there ANY admissible (gross<=1.6) construction with dAnn>0?

Admissibility is V2 s8e: blend gross <= 1.6, full |dW| @ 6.4bps one-side.
Also quantifies the vol-matched counterfactual (what the rejection actually gives up).
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
import rawew13v2_build as B13

CH = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
PATHS = dict(B13.PATHS)
PATHS["RB_hobr"] = "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv"
NAMES = list(B13.NAMES) + ["RB_hobr"]


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {"n": len(r), "ann": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
            "sr": float(r.mean() / r.std(ddof=1) * 252 ** 0.5),
            "vol": float(r.std(ddof=1) * 252 ** 0.5) * 100,
            "mdd": float((nav / nav.cummax() - 1).min()) * 100,
            "neg": int((yr < 0).sum())}


champ = pd.read_csv(CH, index_col=0, parse_dates=True).iloc[:, 0]
cs = stats(champ)

df = pd.DataFrame({n: B13.load(PATHS[n]).dropna() for n in NAMES})
df = df[df.index >= "2008-03-31"]

isr = df[df.index < B13.IS_END]
relw_nat = pd.Series({n: max(B13.is_sr(isr[n]), 0.0) ** B13.P for n in df.columns})


def book(rw, gear=B13.GEAR):
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(rw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(df.columns)
    Wg = d2 * (gear / len(df.columns))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=df.index) - to * B13.BPS / 1e4
           - np.maximum(gear - 1, 0) * B13.RATE / 252)
    return net, Wg


print("CHAMPION: ann %.4f  sr %.4f  vol %.4f  mdd %.4f  neg %d" % (
    cs["ann"], cs["sr"], cs["vol"], cs["mdd"], cs["neg"]))
sh = stats(df["RB_hobr"].dropna())
print("RB_hobr sleeve standalone (raw): SR %.4f  ann %.4f  vol %.4f  n %d" % (
    sh["sr"], sh["ann"], sh["vol"], sh["n"]))

# --- A. fine w grid, relw-scaled, gross held at 1.6 (admissible) ---
_, _, Wg_nat0 = None, None, None
net_nat, Wg_nat = book(relw_nat)
mean_share = float((Wg_nat["RB_hobr"].abs() / Wg_nat.abs().sum(axis=1)).mean())
print("\n[A] admissible w-grid at gross 1.6 (relw-scaled HOBR, their 8g machinery)")
print("    natural HOBR mean share %.6f" % mean_share)
print("    %-8s %-9s %-10s %-9s %-9s %-9s %-9s" % (
    "w", "grossMean", "grossMax", "dAnn_pp", "dSR", "dMDD_pp", "neg"))
best = (-9e9, None)
for w in [0.0, 0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]:
    rw = relw_nat.copy()
    rw["RB_hobr"] = relw_nat["RB_hobr"] * (1.0 if w == 0 else 1.0)
    if w > 0:
        fac = w / mean_share
        for _ in range(6):
            nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
            rw2 = relw_nat.copy()
            rw2["RB_hobr"] = relw_nat["RB_hobr"] * fac
            d2 = nav.div(nav.mean(axis=1), axis=0).mul(rw2, axis=1)
            d2 = d2.div(d2.sum(axis=1), axis=0) * len(df.columns)
            W = d2 * (B13.GEAR / len(df.columns))
            s_ = (W["RB_hobr"].abs() / W.abs().sum(axis=1)).mean()
            fac *= w / s_
        rw = rw2
    else:
        rw = relw_nat.copy()
        rw["RB_hobr"] = 0.0
    net, W = book(rw)
    j = pd.concat([champ.rename("c"), net.rename("b")], axis=1, join="inner").dropna()
    sb, sc = stats(j.b), stats(j.c)
    d = sb["ann"] - sc["ann"]
    gm = float(W.abs().sum(axis=1).mean())
    gx = float(W.abs().sum(axis=1).max())
    print("    %-8s %-9.6f %-10.9f %+10.4f %+9.4f %+9.4f %-9d" % (
        w, gm, gx, d, sb["sr"] - sc["sr"], sb["mdd"] - sc["mdd"], sb["neg"]))
    if d > best[0] and gx <= 1.6 + 1e-9:
        best = (d, w)
print("    BEST admissible dAnn: %+.4f pp at w=%s" % (best[0], best[1]))

# --- B. vol-matched counterfactual: how much gross would HOBR need? ---
print("\n[B] vol-matched counterfactual (what the s8e gross cap actually costs)")
for w in [0.05758, 0.15]:
    fac = w / mean_share
    for _ in range(6):
        nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
        rw2 = relw_nat.copy()
        rw2["RB_hobr"] = relw_nat["RB_hobr"] * fac
        d2 = nav.div(nav.mean(axis=1), axis=0).mul(rw2, axis=1)
        d2 = d2.div(d2.sum(axis=1), axis=0) * len(df.columns)
        W = d2 * (B13.GEAR / len(df.columns))
        fac *= w / (W["RB_hobr"].abs() / W.abs().sum(axis=1)).mean()
    net, W = book(rw2)
    j = pd.concat([champ.rename("c"), net.rename("b")], axis=1, join="inner").dropna()
    sb, sc = stats(j.b), stats(j.c)
    k = sc["vol"] / sb["vol"]
    print("    w=%.5f: 14-book vol %.4f%% vs champ %.4f%%  -> vol-match factor k=%.4f (gross would be %.4f)"
          % (w, sb["vol"], sc["vol"], k, k * B13.GEAR))
    # analytic re-lever of the 14-book to champ vol
    netk, Wk = book(rw2, gear=k * B13.GEAR)
    jk = pd.concat([champ.rename("c"), netk.rename("b")], axis=1, join="inner").dropna()
    sk = stats(jk.b)
    print("           vol-matched 14-book: ann %.4f vs champ %.4f  -> dAnn %+.4f pp   grossMax %.4f"
          % (sk["ann"], cs["ann"], sk["ann"] - cs["ann"], float(Wk.abs().sum(axis=1).max())))
