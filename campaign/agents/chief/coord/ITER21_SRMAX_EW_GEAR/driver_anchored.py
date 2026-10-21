#!/usr/bin/env python3
# ITER21 driver v2 (anchored): baselines pinned to IMMUTABLE files so every dev line is
# meaningful post-swap. Original driver.py preserved untouched for the pre-commit record.
#   ANCHOR-1.6: committed vector @ gear 1.6 == archived ITER20 vintage bytes (766fc0ce...)
#   ANCHOR-1.0: canonical default build()  == champion-of-record bytes   (8559fa55...)
# OOS comparisons run against BOTH incumbents, labeled.
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import rawew13v2_build as rb

CHAMP = rb.ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
ARCH_ITER20 = (rb.ROOT + "/campaign/results/"
               "archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER21_gear10.csv")

def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    ann = nav.iloc[-1] ** (252 / len(r)) - 1
    sr = r.mean() / r.std(ddof=1) * np.sqrt(252)
    dd = nav / nav.cummax() - 1
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return dict(n=len(r), ann=ann, sr=sr, mdd=float(dd.min()),
                neg=int((yr < 0).sum()), nyrs=len(yr), worst=float(yr.min()))

w_commit = pd.read_csv(rb.ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv",
                       index_col=0).iloc[:, 0].reindex(rb.NAMES).fillna(0.0)

def dev_vs(series, path):
    ref = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([ref.rename("ref"), series.rename("s")], axis=1, join="inner").dropna()
    return len(j), float((j.ref - j.s).abs().max())

# ---- ANCHOR-1.6: committed vector @1.6 vs ARCHIVED ITER20 vintage ----
rb.fit_relw = lambda isr, shrink_d=rb.SHRINK_D: w_commit
net_a, relw_a, gross_a, to_a, _ = rb.build(gear=1.6)
n, d16 = dev_vs(net_a, ARCH_ITER20)
print("ANCHOR-1.6 vs archive 766fc0ce: n=%d maxdev=%.3e %s" % (
    n, d16, "IDENTICAL" if d16 < 1e-12 else "DIFF"))
s = stats(net_a)
print("ANCHOR-1.6 stats: ann=%.4f%% SR=%.6f MDD=%.4f%% neg=%d/%d" % (
    s["ann"] * 100, s["sr"], s["mdd"] * 100, s["neg"], s["nyrs"]))

# ---- ANCHOR-1.0: canonical default build vs champion-of-record bytes ----
rb_sav = rb.fit_relw
net_d, relw_d, gross_d, to_d, _ = rb.build()
n, d10 = dev_vs(net_d, CHAMP)
print("ANCHOR-1.0 vs champion 8559fa55: n=%d maxdev=%.3e %s grossmax=%.6f" % (
    n, d10, "IDENTICAL" if d10 < 1e-12 else "DIFF", float(gross_d.max())))

# ---- candidates on the gear grid ----
uni = pd.Series(0.0, index=rb.NAMES)
uni[[n for n in rb.NAMES if n != "CFX4"]] = 1.0 / 11  # EW12v2: 11 tradeable, CFX4=0
BOOKS = [("A_EW12v2", uni), ("B_ITER20vec", w_commit)]
GEARS = [1.6, 1.3, 1.1, 1.05, 1.02, 1.0, 0.95, 0.90]
for label, wvec in BOOKS:
    rb.fit_relw = (lambda w: (lambda isr, shrink_d=rb.SHRINK_D: w))(wvec)
    for g in GEARS:
        if label == "B_ITER20vec" and abs(g - 1.6) < 1e-12:
            net, gross, to = net_a, gross_a, to_a
        else:
            net, relw, gross, to, _ = rb.build(gear=g)
        st = stats(net)
        print("%s g=%4.2f: FS ann=%7.4f%% SR=%.4f MDD=%7.4f%% neg=%d/%d | grossmax=%.6f" % (
              label, g, st["ann"] * 100, st["sr"], st["mdd"] * 100, st["neg"], st["nyrs"],
              float(gross.max())))

# ---- Wmax (fit-share x equal, cap 2.0x) ----
for label, wvec in BOOKS:
    print("Wmax %s: %.4fx (cap 2.0x)" % (label, float(wvec.max()) / (1.0 / len(rb.NAMES))))

# ---- OOS 2-yr bins vs BOTH incumbents ----
bins = [(2017, 2018), (2019, 2020), (2021, 2022), (2023, 2024), (2025, 2026)]
old16 = pd.read_csv(ARCH_ITER20, index_col=0, parse_dates=True).iloc[:, 0]
old10 = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
def binsr(r):
    out = []
    for a, b in bins:
        w = r[(r.index.year >= a) & (r.index.year <= b)].dropna()
        out.append(w.mean() / w.std(ddof=1) * np.sqrt(252) if len(w) > 50 else np.nan)
    return out
rb.fit_relw = rb_sav
net_c10, _, _, _, _ = rb.build()
print("OOS dSR per 2017+ 2-yr bin (cand - incumbent):")
for label, wvec in BOOKS:
    rb.fit_relw = (lambda w: (lambda isr, shrink_d=rb.SHRINK_D: w))(wvec)
    net, _, _, _, _ = rb.build(gear=1.0)
    d = [c - i for c, i in zip(binsr(net), binsr(old10))]
    print("  %s @1.0 vs CHAMP@1.0: %s | all>0: %s" % (
        label, " ".join("%+.3f" % x for x in d), all(x > 0 for x in d)))
    d = [c - i for c, i in zip(binsr(net), binsr(old16))]
    print("  %s @1.0 vs ARCH@1.6 : %s | all>0: %s" % (
        label, " ".join("%+.3f" % x for x in d), all(x > 0 for x in d)))
rb.fit_relw = rb_sav
d = [c - i for c, i in zip(binsr(net_c10), binsr(old16))]
print("  CHAMP@1.0 vs ARCH@1.6: %s | all>0: %s (the analytic de-gear gain)" % (
    " ".join("%+.3f" % x for x in d), all(x > 0 for x in d)))

# ---- ann floor search at 2dp gears ----
rb.fit_relw = (lambda w: (lambda isr, shrink_d=rb.SHRINK_D: w))(uni)
for g in [1.04, 1.00, 0.95, 0.90]:
    net, _, _, _, _ = rb.build(gear=g)
    print("A g=%.2f: ann=%.4f%% %s" % (g, stats(net)["ann"] * 100,
          ">=20%% PASS" if stats(net)["ann"] >= 0.20 else "BELOW floor"))
rb.fit_relw = (lambda w: (lambda isr, shrink_d=rb.SHRINK_D: w))(w_commit)
for g in [0.92, 0.90, 0.88, 0.86]:
    net, _, _, _, _ = rb.build(gear=g)
    print("B g=%.2f: ann=%.4f%% %s" % (g, stats(net)["ann"] * 100,
          ">=20%% PASS" if stats(net)["ann"] >= 0.20 else "BELOW floor"))
