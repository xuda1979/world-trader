"""Idea 1 SAVE: a6_r7_bond2y_trend — verify gate d on all plateau pts, then save sleeve."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L

DUR2 = 1.9
def tr2y():
    y = L.fnew("DGS2") / 100.0
    return (-DUR2 * y.diff() + y / 252.0).dropna()

def build(k, cad):
    tr = tr2y()
    sig = (tr.rolling(k).mean() > 0).astype(float)
    W = L.freeze(pd.DataFrame({"d2": sig}), cad)
    return W, pd.DataFrame({"d2": tr})

print("=== gate-d check on all 12 plateau points ===")
for k in [252, 315, 378, 441]:
    row = []
    for cad in [21, 42, 63]:
        W, rets = build(k, cad)
        r, _ = L.from_W(W, rets, vt=0.12)
        yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
        neg = {int(y): round(v*100,1) for y,v in yr.items() if v<0}
        row.append(f"c{cad}:SR{r.mean()/r.std()*np.sqrt(252):.2f},ny{len(neg)},w{min(neg.values()) if neg else 0:.1f}")
    print(f"k{k}: " + " | ".join(row))

# chosen config final report + save
W, rets = build(378, 42)
r, _ = L.from_W(W, rets, vt=0.12)
rep = L.report(r, "FINAL a6_r7_bond2y_trend")
p = L.scramble(r, W, rets, vt=0.12)
print(f"scramble p={p:.3f}")
assert p < 0.05
ok = all([rep["gates"]["a_SR>=0.6"], rep["gates"]["c_H1>=0.3"], rep["gates"]["c_H2>=0.3"],
          rep["gates"]["d_negYr<=2"], rep["gates"]["d_worst>-5%"], abs(rep["c6"]) < 0.25, p < 0.05])
if ok:
    out = f"/Users/daxu/software/world-trader/campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv"
    meta = f"""name: a6_r7_bond2y_trend
agent: A6_reversal (round r7, charter mission 1 — bond rate-trend)
construction: synthetic 2y Treasury total return TR(t) = -1.9*dDGS2(t) + y(t-1)/252 (par-bond
  approx: duration 1.9, carry accrual); signal = trailing 378-bday mean TR > 0 -> LONG else FLAT
  (long-flat, no shorting of bonds); decision frozen at 42-bday cadence; T+1 (W.shift(1)); costs
  6bps/side on |dW|; vol-target 12% ann trailing expanding min-60d, lev cap 5 (realized vol 6.5%,
  cap binds — cap10 disclosure variant: SR 1.52 ann 14.6%).
rationale (economic): the 2y yield is the market's expected policy path; Fed cycles are long and
  persistent (hike/cut sequences run years), so 18-month trailing excess return predicts next-month
  excess return (policy-rate momentum). Always-long 2y term premium alone is SR 1.15 (2007-26) but
  loses -18.9% in 2022; the trend overlay's one in-window action (flat Nov-2021..Sep-2023) is the
  economically correct call (hiking cycles = negative 2y excess returns) and flips 2022 to 0.0%.
  Data: FRED DGS2 daily, 1990+, no lookahead (ffill on bday calendar, signal at t, earn t+1).
validation (r7): FULL SR 1.43 (net VT12, 2007-01..2026-08) | H1 1.14 / H2 1.81 | neg years 2/20
  (2014 -0.5%, 2021 -4.1%) | worst -4.1% | scramble p=0.005 (200x circular shift of weight path,
  costs+VT repriced) | plateau: 12-pt grid k252..k441 x cad21..63 all SR 1.31-1.43, neighbor-min
  1.33 vs 0.8*peak 1.14; gate d holds at all 12 points | corr to 6-leg champion corrM=-0.00
  (corr5=+0.02) — genuinely de-correlated (first A6 engine outside equity books).
caveats: synthetic TR from constant duration (convexity ignored — small at 2y tenor); carry accrued
  at spot yield/252; DGS2 is a H.15 quote series (level, no bid/ask); k504 (2y lookback) fails 2022
  (-13.2%) because the window still contains 2019-20 cut-driven positive TR — documented edge of
  the plateau; leverage cap means realized vol (6.5%) sits below the 12% target.
"""
    with open(out, "w") as f:
        rr = r.dropna()
        df = pd.DataFrame({"ret": rr.values}, index=rr.index); df.index.name = "date"
        df.to_csv(out)
    with open(out + ".meta", "w") as f:
        f.write(meta)
    print("SAVED", out)
else:
    print("NOT SAVED — gates failed:", rep["gates"])
