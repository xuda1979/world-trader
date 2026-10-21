
"""S5: attack (d) P-HACKING-THE-OTHER-WAY on HUNT_TREASFUT-R7 (ECB AAA curve).

Row: SLOPE_mom SR 0.394, CURV_mom SR 0.272 -> dead.  Attack: was a legitimate
positive result discarded because of ONE badly-chosen parameterization?  k=63 was
"a-priori, NOT chosen from any scan".  Sweep k for a PLATEAU above sr_min 1.0.
Engine = their own module, unmodified; only k varies.
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/scripts")
import HUNT_TREASFUT_round7 as T  # their engine, unmodified


def stats(r):
    r = pd.Series(r).dropna()
    if len(r) < 50:
        return None
    nav = (1 + r).cumprod()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    half = len(r) // 2
    def sr(x):
        x = pd.Series(x).dropna()
        return float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std(ddof=1) > 0 else float("nan")
    return {"n": len(r), "sr": sr(r), "ann": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
            "h1": sr(r[:half]), "h2": sr(r[half:]),
            "neg": int((yr < 0).sum()), "mdd": float((nav / nav.cummax() - 1).min()) * 100,
            "pre2010": sr(r[r.index < "2010-01-01"]), "post2010": sr(r[r.index >= "2010-01-01"]),
            "post2013": sr(r[r.index >= "2013-01-01"])}


ys = T.load_yc()
R = T.leg_returns(ys)
print("ECB AAA panel: n=%d %s..%s  tenors %s" % (len(ys), ys.index[0].date(), ys.index[-1].date(),
                                                 list(ys.columns)))

def run(wfun, k, **kw):
    W = wfun(ys, k=k, **kw)
    net, We, gross = T.book(W, R)
    return stats(net)

print()
print("=== [verify] reproduce their published k=63 ===")
for fam, wfun, flip, pub in [("SLOPE_mom", T.weights_slope, False, 0.3938),
                             ("SLOPE_rev", T.weights_slope, True, -0.4211),
                             ("CURV_mom", T.weights_fly, False, 0.2724),
                             ("CURV_rev", T.weights_fly, True, -0.3020)]:
    s = run(wfun, T.K, flip=flip)
    print("  %-10s k=%d  SR %+.4f (published %+.4f)  n=%d" % (fam, T.K, s["sr"], pub, s["n"]))

print()
print("=== [ATTACK d] lookback sweep, SLOPE momentum (gate sr_min = 1.0) ===")
print("  %-6s %-8s %-9s %-9s %-9s %-9s %-6s %-9s %-9s" % (
    "k", "n", "SR", "ann%", "h1", "h2", "neg", "pre2010", "post2010"))
best = (-9, None)
for k in (10, 21, 42, 63, 84, 126, 189, 252, 378, 504):
    s = run(T.weights_slope, k)
    if s is None:
        continue
    print("  %-6d %-8d %+9.4f %+9.4f %+9.4f %+9.4f %-6d %+9.4f %+9.4f" % (
        k, s["n"], s["sr"], s["ann"], s["h1"], s["h2"], s["neg"], s["pre2010"] or float("nan"),
        s["post2010"] or float("nan")))
    if s["sr"] > best[0]:
        best = (s["sr"], k)
print("  best SLOPE momentum SR = %+.4f at k=%s" % best)

print()
print("=== [ATTACK d] lookback sweep, CURV momentum ===")
bestc = (-9, None)
for k in (10, 21, 42, 63, 84, 126, 189, 252, 378, 504):
    s = run(T.weights_fly, k)
    if s is None:
        continue
    print("  %-6d %-8d %+9.4f %+9.4f %+9.4f %+9.4f %-6d %+9.4f %+9.4f" % (
        k, s["n"], s["sr"], s["ann"], s["h1"], s["h2"], s["neg"],
        s["pre2010"] or float("nan"), s["post2010"] or float("nan")))
    if s["sr"] > bestc[0]:
        bestc = (s["sr"], k)
print("  best CURV momentum SR = %+.4f at k=%s" % bestc)

print()
print("=== [ATTACK d] VT target + clip sweep at k=63 SLOPE ===")
import bt.engine as E
for tgt in (0.05, 0.10, 0.15, 0.20, 0.30):
    W = T.weights_slope(ys, k=T.K)
    Wd = W.reindex(index=R.index, columns=R.columns).ffill().fillna(0.0)
    We = Wd.shift(1).fillna(0.0)
    g = (We * R.fillna(0.0)).sum(axis=1)
    s_ = E.vol_target_scale(g.to_frame("g"), target=tgt)["g"]
    We2 = We.mul(s_, axis=0)
    port = (We2 * R.fillna(0.0)).sum(axis=1)
    net = port - E.cost_turnover(We2, cost_bps=6.4) - E.borrow_cost(We2)
    st = stats(net)
    print("  target %-6.2f  SR %+.4f  ann %+7.4f%%  h1 %+.3f h2 %+.3f  neg %d" % (
        tgt, st["sr"], st["ann"], st["h1"], st["h2"], st["neg"]))
