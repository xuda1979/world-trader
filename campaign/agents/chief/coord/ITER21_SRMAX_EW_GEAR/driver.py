#!/usr/bin/env python3
# ITER21 driver: gear sweep + EW12v2 candidate through the REAL rawew13v2_build mechanics.
# Pre-commit: FINDINGS_PRECOMMIT.md (written before this run). Anchor must reproduce
# champion bytes <1e-12 before any candidate number is trusted.
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import rawew13v2_build as rb

CHAMP = rb.ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    ann = nav.iloc[-1] ** (252 / len(r)) - 1
    sr = r.mean() / r.std(ddof=1) * np.sqrt(252)
    dd = nav / nav.cummax() - 1
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return dict(n=len(r), ann=ann, sr=sr, mdd=float(dd.min()),
                neg=int((yr < 0).sum()), nyrs=len(yr), worst=float(yr.min()))

def wmax_x_equal(relw_vec, gear):
    # replicate build() Wg to get max weight in equal-weight units (share * len(NAMES))
    df = pd.DataFrame({n: rb.load(rb.PATHS[n]).dropna() for n in rb.NAMES})
    df = df[df.index >= "2008-03-31"]
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw_vec, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(rb.NAMES)
    Wg = d2 * (gear / len(rb.NAMES))
    return float(Wg.abs().max().max()) / (gear / len(rb.NAMES))

w_commit = pd.read_csv(rb.ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv",
                       index_col=0).iloc[:, 0].reindex(rb.NAMES).fillna(0.0)

# ---- ANCHOR: committed vector @ gear 1.6 must reproduce champion bytes ----
rb.fit_relw = lambda isr, shrink_d=rb.SHRINK_D: w_commit
net_a, relw_a, gross_a, to_a, _ = rb.build(gear=1.6)
old = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([old.rename("old"), net_a.rename("new")], axis=1, join="inner").dropna()
anchor_dev = float((j.old - j.new).abs().max())
print("ANCHOR champion-vector @1.6: n=%d maxdev=%.3e %s" % (
    len(j), anchor_dev, "IDENTICAL" if anchor_dev < 1e-12 else "DIFF"))
s = stats(net_a)
print("ANCHOR stats: ann=%.4f%% SR=%.6f MDD=%.4f%% neg=%d/%d worst=%.4f%%" % (
    s["ann"] * 100, s["sr"], s["mdd"] * 100, s["neg"], s["nyrs"], s["worst"] * 100))

# ---- candidates ----
uni = pd.Series(0.0, index=rb.NAMES)
uni[[n for n in rb.NAMES if n != "CFX4"]] = 1.0 / 11  # EW12v2: 11 tradeable, CFX4=0

BOOKS = [("A_EW12v2", uni), ("B_ITER20vec", w_commit)]
GEARS = [1.6, 1.3, 1.1, 1.05, 1.02, 1.0, 0.95, 0.90, 0.85]
for label, wvec in BOOKS:
    rb.fit_relw = (lambda w: (lambda isr, shrink_d=rb.SHRINK_D: w))(wvec)
    for g in GEARS:
        if label == "B_ITER20vec" and abs(g - 1.6) < 1e-12:
            net, gross, to = net_a, gross_a, to_a  # reuse anchor build
        else:
            net, relw, gross, to, _ = rb.build(gear=g)
        st = stats(net)
        si = stats(net[net.index < rb.IS_END])
        print("%s g=%4.2f: FS ann=%7.4f%% SR=%.4f MDD=%7.4f%% neg=%d/%d worst=%7.4f%%"
              " | IS ann=%6.4f%% SR=%.4f MDD=%7.4f%% | grossmax=%.6f to=%.2fbp/yr" % (
              label, g, st["ann"] * 100, st["sr"], st["mdd"] * 100, st["neg"], st["nyrs"],
              st["worst"] * 100, si["ann"] * 100, si["sr"], si["mdd"] * 100,
              float(gross.max()), float(to.mean() * 252 * rb.BPS)))

# ---- Wmax RULE check (fit shares, max relw vs 1/12 equal; cap 2.0x) ----
for label, wvec in BOOKS:
    print("Wmax(fit-share x equal) %s: %.4fx (cap 2.0x)" % (
        label, float(wvec.max()) / (1.0 / len(rb.NAMES))))

# ---- OOS 2-yr bins: candidates vs incumbent champion ----
bins = [(2017, 2018), (2019, 2020), (2021, 2022), (2023, 2024), (2025, 2026)]
def binsr(r):
    out = []
    for a, b in bins:
        w = r[(r.index.year >= a) & (r.index.year <= b)].dropna()
        out.append(w.mean() / w.std(ddof=1) * np.sqrt(252) if len(w) > 50 else np.nan)
    return out
print("OOS dSR per 2-yr bin (cand - incumbent):")
for label, wvec in BOOKS:
    rb.fit_relw = (lambda w: (lambda isr, shrink_d=rb.SHRINK_D: w))(wvec)
    net, _, _, _, _ = rb.build(gear=1.05)
    d = [c - i for c, i in zip(binsr(net), binsr(old))]
    print("  %s @1.05: %s | all>0: %s" % (label, " ".join("%+.3f" % x for x in d),
                                          all(x > 0 for x in d)))

# ---- exact floor search for A: largest 2dp gear below the 20% ann floor ----
rb.fit_relw = (lambda w: (lambda isr, shrink_d=rb.SHRINK_D: w))(uni)
for g in [1.10, 1.08, 1.06, 1.04, 1.02, 1.00]:
    net, _, _, _, _ = rb.build(gear=g)
    a = stats(net)["ann"]
    print("A g=%.2f: ann=%.4f%% %s" % (g, a * 100, ">=20% PASS" if a >= 0.20 else "BELOW floor"))
rb.fit_relw = (lambda w: (lambda isr, shrink_d=rb.SHRINK_D: w))(w_commit)
for g in [0.92, 0.90, 0.88, 0.86]:
    net, _, _, _, _ = rb.build(gear=g)
    a = stats(net)["ann"]
    print("B g=%.2f: ann=%.4f%% %s" % (g, a * 100, ">=20% PASS" if a >= 0.20 else "BELOW floor"))
