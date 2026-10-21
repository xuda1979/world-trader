
"""S6: attack on HUNT_FXCARRY2-R7 (daily PIT overnight-rate FX carry) rejection.

Row: SR 0.073, H1 +0.29/H2 -0.22, 12 neg years, worst -26.7%, post-2004 SR -0.198.

Attacks:
 (b) SIGN / CONSTRUCTION: is the reported direction the ACTUAL tested direction?
 (a) GATE/COST: is the published headline SR the COSTED SR? (their `net = tot` is
     spot pnl + carry accrual; no transaction cost term is visible)
 (c) SPAN/DATA: the EUR leg is capped at 2021-12-29 by EONIA. ECBDFR (1999-2026) is
     on disk. Does extending the EUR leg past 2021 change the verdict?
"""
import json
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT + "/campaign")
import HUNT_FXCARRY2_round7 as F
from bt import engine as E


def stats(r):
    r = pd.Series(r).dropna()
    nav = (1 + r).cumprod()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    def sr(x):
        x = pd.Series(x).dropna()
        return float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if len(x) > 30 and x.std(ddof=1) > 0 else float("nan")
    half = len(r) // 2
    return {"n": len(r), "sr": sr(r), "ann": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
            "h1": sr(r[:half]), "h2": sr(r[half:]), "neg": int((yr < 0).sum()),
            "worst": float(yr.min()), "vol": float(r.std(ddof=1) * np.sqrt(252) * 100)}


spot = pd.read_csv(F.SPOTW, index_col=0, parse_dates=True).astype(float)[["USD", "GBP"]]

def build(eur_series="EONIA+ESTER"):
    rates = pd.DataFrame({"USD": F.load_rate("USD_DFF"),
                          "GBP": F.load_rate("GBP_SONIA"),
                          "EUR": F.load_rate("EUR_EONIA")}).dropna()
    if eur_series == "EONIA+ESTER":
        ester = F.load_rate("EUR_ESTER")
        re_ = rates["EUR"].copy()
        re_.loc[re_.index >= ester.index[0]] = ester.reindex(re_.index[re_.index >= ester.index[0]])
        rates["EUR"] = re_
    elif eur_series == "ECBDFR":
        rates["EUR"] = F.load_rate("EUR_ECBDFR")
    rates = rates.dropna()
    We, W, meta = F.build_carry_book(rates, spot)
    tot, accr, We_d = F.fx_total_returns_daily(W, rates, spot)
    return rates, W, tot, accr, We_d


print("=== [0] reproduce the published book ===")
rates, W, tot, accr, We_d = build("EONIA+ESTER")
s = stats(tot)
print("  rates panel n=%d %s->%s" % (len(rates), rates.index[0].date(), rates.index[-1].date()))
print("  held book n=%d SR %+.4f (published +0.0731)  H1 %+.2f H2 %+.2f  neg %d  worst %.1f%%"
      % (s["n"], s["sr"], s["h1"], s["h2"], s["neg"], s["worst"] * 100))

print()
print("=== [1] ATTACK (a) COST: is the published headline COSTED? ===")
sig = F.held_gross_units(We_d).reindex(tot.index).fillna(0.0)
dW = sig.diff().abs().fillna(0.0)
dW.iloc[0] = abs(sig.iloc[0])
cost = dW * 6.4 / 1e4 + (-sig).clip(lower=0.0) * 0.005 / 252.0
net = tot - cost
sn = stats(net)
print("  costed: SR %+.4f  ann %+.4f%%  vol %.4f%%   (uncosted SR %+.4f)" % (
    sn["sr"], sn["ann"], sn["vol"], s["sr"]))
print("  mean cost drag: %.2f bp/yr   mean borrow: %.2f bp/yr   mean gross |sig| %.4f" % (
    float((dW * 6.4).mean() * 252), float(((-sig).clip(lower=0.0) * 0.005 / 252.0).mean() * 252 * 1e4),
    float(sig.abs().mean())))

print()
print("=== [2] ATTACK (b) SIGN: invert the decision sign ===")
rates2, W2, tot2, accr2, We_d2 = build("EONIA+ESTER")
W2i = -W2
tot_i, _, _ = F.fx_total_returns_daily(W2i, rates2, spot)
si = stats(tot_i)
print("  inverted book: SR %+.4f  ann %+.4f%%  H1 %+.2f H2 %+.2f  neg %d" % (
    si["sr"], si["ann"], si["h1"], si["h2"], si["neg"]))
print("  -> reported direction is %s" % ("the tested direction (no sign bug)" if abs(si["sr"] + s["sr"]) < 0.05 else "AMBIGUOUS"))

print()
print("=== [3] ATTACK (c) SPAN: extend EUR leg with ECBDFR (1999-2026) ===")
rates3, W3, tot3, accr3, We_d3 = build("ECBDFR")
s3 = stats(tot3)
print("  rates panel n=%d %s->%s" % (len(rates3), rates3.index[0].date(), rates3.index[-1].date()))
print("  ECBDFR-EUR book n=%d SR %+.4f  H1 %+.2f H2 %+.2f  neg %d  worst %.1f%%" % (
    s3["n"], s3["sr"], s3["h1"], s3["h2"], s3["neg"], s3["worst"] * 100))

print()
print("=== [4] ERA STABILITY (the +1.83 n=259 tail: gain or artifact?) ===")
print("  %-10s %-8s %-10s" % ("era", "n", "SR"))
for lbl, a in (("1999+", None), ("2004+", "2004-01-01"), ("2008+", "2008-01-01"),
               ("2015+", "2015-01-01"), ("2019+", "2019-01-01"), ("2021+", "2021-01-01"),
               ("2024+", "2024-01-01")):
    e = tot if a is None else tot[tot.index >= pd.Timestamp(a)]
    if len(e) < 40:
        print('  %-10s %-8d %s' % (lbl, len(e), 'n/a'))
        continue
    ee = stats(e)
    print("  %-10s %-8d %+.4f" % (lbl, ee["n"], ee["sr"]))
