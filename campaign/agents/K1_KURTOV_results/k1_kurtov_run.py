"""K1-KURTOV runner — implements PREREGISTRATION.md exactly (locked 2026-09-30).
Inverse-trailing-kurtosis scaling overlay on the V7.1 champion's 20 sleeves.
3 arms (K=126/252/378), T+1 causal, 6.4bps on overlay rebalance turnover, gates
G1-G6 on OOS (>=2017). Reads weights + 20 sleeve CSVs + V7.1 ledger."""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.abspath(os.path.join(CAMPAIGN, ".."))
OD = os.path.join(CAMPAIGN, "work_backtest_oos")
LEDGER = os.path.join(OD, "OPT_20V71_FULL_LEDGER.csv")
WEIGHTS = os.path.join(OD, "OPT_20V71_weights.csv")
IS_END = pd.Timestamp("2017-01-01")
LEV = 1.6
BPS = 6.4e-4
SR_EDGE = 0.10
ANN_DROP_MAX = 0.010
TO_MAX = 6.0
KCAP = 20.0
KS = (126, 252, 378)


def load_sleeve(rel):
    d = pd.read_csv(os.path.join(CAMPAIGN, rel), index_col=0)
    d.index = pd.to_datetime(d.index)
    c = "ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()


def mon(s):
    return (1 + s).resample("ME").prod() - 1


def srm(x):
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(12)


def mdd(x):
    x = (1 + x.dropna()).cumprod()
    return (x / x.cummax() - 1).min()


def neg_years(daily):
    m = mon(daily)
    yrs = (1 + m).groupby(m.index.year).prod() - 1
    return int((yrs < 0).sum())


# ---------------------------------------------------------------- load
w = pd.read_csv(WEIGHTS, index_col=0).iloc[:, 0].astype(float)
assert abs(w.sum() - 1.0) < 1e-9 and len(w) == 20
sleeves = list(w.index)
rets = pd.DataFrame({s: load_sleeve(s) for s in sleeves})
rets = rets[rets.index >= "2009-01-01"].fillna(0.0)
rets = rets[rets.index <= "2026-09-30"]

led = pd.read_csv(LEDGER, parse_dates=["date"])
g = led.groupby("date")[["pnl", "cost"]].sum().sort_index()
r_champ = (g["pnl"] - g["cost"]).astype(float)
r_champ = r_champ[(r_champ.index >= rets.index.min()) &
                  (r_champ.index <= rets.index.max())]
common = r_champ.index.intersection(rets.index)
r_champ = r_champ.loc[common]
rets = rets.loc[common]
assert len(common) > 4000

wv = w.values  # (20,)
zeroed = wv == 0.0

# champion reference
champ_full_sr = srm(mon(r_champ))
champ_oos = r_champ[r_champ.index >= IS_END]
champ_oos_sr = srm(mon(champ_oos))
champ_oos_ann = float((1 + champ_oos).prod() ** (252 / len(champ_oos)) - 1)
champ_oos_mdd = float(mdd(champ_oos))
champ_neg_oos = neg_years(champ_oos)
assert champ_neg_oos == 0

# ---------------------------------------------------------------- arms
rows = []
for K in KS:
    kurt = rets.rolling(K).kurt().shift(1)          # T+1 causal
    s = 1.0 / (1.0 + kurt.clip(0.0, KCAP))          # (n, 20)
    eff = (wv * s).div((wv * s).sum(axis=1), axis=0)  # renorm to gross 1
    eff = eff.where(~pd.DataFrame(np.tile(zeroed, (len(eff), 1)),
                                  index=eff.index, columns=eff.columns),
                    0.0)
    # re-renormalize after zeroing (sum != 1 on the rare day kurt is NaN->0)
    eff = eff.div(eff.sum(axis=1), axis=0).fillna(0.0)
    dev = eff.sub(wv, axis=1)                        # overlay deviation vs champion
    r_ov = LEV * (dev * rets).sum(axis=1)
    d_eff = eff.diff().abs().sum(axis=1).fillna(0.0)
    cost_ov = BPS * LEV * d_eff
    daily = r_champ + r_ov - cost_ov
    daily = daily[daily.index >= "2009-01-01"]
    # stats
    is_d = daily[daily.index < IS_END]
    oos_d = daily[daily.index >= IS_END]
    is_sr, oos_sr = srm(mon(is_d)), srm(mon(oos_d))
    oos_ann = float((1 + oos_d).prod() ** (252 / len(oos_d)) - 1)
    oos_mdd = float(mdd(oos_d))
    neg_o = neg_years(oos_d)
    to_yr = float(d_eff.sum() / (len(daily) / 252))
    oos_edge = oos_sr - champ_oos_sr
    is_edge = is_sr - champ_full_sr  # informational only
    rows.append(dict(
        K=K, is_sr=is_sr, oos_sr=oos_sr, oos_ann=oos_ann, oos_mdd=oos_mdd,
        neg_yrs_oos=neg_o, to_yr=to_yr, oos_edge=oos_edge, is_edge=is_edge,
        G1=bool(oos_edge >= SR_EDGE),
        G2=bool(oos_mdd >= champ_oos_mdd - 1e-12),
        G3=bool(oos_ann >= champ_oos_ann - ANN_DROP_MAX),
        G4=bool(neg_o == 0),
        G5=bool(to_yr <= TO_MAX),
        G6=bool(oos_edge >= 0),
    ))

res = pd.DataFrame(rows)
res.to_csv(os.path.join(HERE, "k1_kurtov_results.csv"), index=False)

# ---------------------------------------------------------------- report
lines = []
A = lines.append
A("# K1-KURTOV — inverse-kurtosis scaling overlay on the V7.1 champion (2026-09-30)")
A("")
A("GOAL5DIR action D. Pre-registered (PREREGISTRATION.md): 3 arms K=126/252/378,")
A("s=1/(1+clip(kurt_K,0,20)), renormalized to gross 1 (zeroed sleeves stay 0),")
A("T+1 causal, overlay cost 6.4bps x LEV on |d(w_eff)| turnover, gates G1-G6 OOS.")
A("Champion OOS reference: SR %.4f ann %.2f%% DD %.2f%% neg-yrs %d"
  % (champ_oos_sr, champ_oos_ann * 100, champ_oos_mdd * 100, champ_neg_oos))
A("")
A("## Results (all 3 pre-registered arms)")
A(res.to_string(index=False))
A("")
best = res.sort_values("is_sr", ascending=False).iloc[0]
gates = {g: bool(best[g]) for g in ("G1", "G2", "G3", "G4", "G5", "G6")}
ok = all(gates.values())
A("## IS-best arm K=%d -> OOS verdict" % int(best["K"]))
A("- OOS SR %.4f (edge %+.4f), ann %.2f%%, DD %.2f%%, neg-yrs %d, overlay to/yr %.2f"
  % (best["oos_sr"], best["oos_edge"], best["oos_ann"] * 100,
     best["oos_mdd"] * 100, best["neg_yrs_oos"], best["to_yr"]))
A("- gates: %s -> **%s**" % (gates, "PROCEED" if ok else "REJECT"))
A("")
A("## VERDICT")
if ok:
    A("**PROCEED — pre-registered gates cleared; escalate to operator (adoption bar")
    A("is high: champion is system of record).**")
else:
    A("**REJECT — inverse-kurtosis overlay fails the pre-registered OOS gates.**")
    A("GOAL5DIR action D closed: kurtosis scaling does not lift the champion book")
    A("either standalone (K1: 0.26 vs 0.43 on trend) or as a 20-sleeve overlay.")
    A("With A (H1 harness, live), B (F2-DDC, REJECT) and C (DEAD_IDEAS discipline,")
    A("ongoing) also actioned, GOAL5DIR is now FULLY closed.")
A("")
A("## Honesty notes")
A("- 3 arms only (pre-registered, no post-hoc grid added).")
A("- The overlay reallocates within the book (gross stays 1): any de-grossing")
A("  variant is a DD-control policy and was already REJECTED by F2-DDC (this")
A("  session); not re-tested here by design.")
A("- Expected outcome per K1-standalone + F2-DDC prior: REJECT.")
A("")
A("DONE K1_KURTOV")

report = "\n".join(lines)
with open(os.path.join(HERE, "K1_KURTOV_REPORT.md"), "w") as f:
    f.write(report + "\n")
print(report)
sys.exit(2 if ok else 0)
