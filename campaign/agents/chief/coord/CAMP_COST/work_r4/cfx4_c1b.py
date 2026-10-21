"""CAMP_COST R4 — OPT-C1 artifact probe.

cfx4_analysis.py's OPT-C1 applies the fitted CFX4 weight from the champion's first day
(2008-03-31), but CFX4 data starts 2019-09-10 — build()'s fillna(0) then parks capital at
exactly 0 return for 11.5y. This probe separates that artifact from the rule itself:

  OPT-C1  (as run)      weight from champion start; CFX4 ret fillna(0)  <- idle-capital drag
  OPT-C1b (inception)   same fitted weight, but CFX4 weight = 0 before its first data date
  decomposition         ann of the CFX4 zero-ret leg pre-2019-09-10
In-memory only.
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/work_r4")

import cfx4_analysis as CA  # noqa: E402

GEAR, RATE, BPS, P, IS_END = CA.GEAR, CA.RATE, CA.BPS, CA.P, CA.IS_END


def main():
    df = pd.DataFrame({n: CA.load(CA.PATHS[n]).dropna() for n in CA.NAMES})
    df = df[df.index >= CA.SPAN_START]
    isr = df[df.index < IS_END]
    SR = pd.Series({n: CA.is_sr(isr[n]) for n in CA.NAMES})
    relw_is = np.maximum(SR, 0.0) ** P
    cfx = df["CFX4"].dropna()
    first_cfx = cfx.index.min()
    fit_end = first_cfx + pd.DateOffset(months=24)
    sr2y = CA.is_sr(cfx[(cfx.index >= first_cfx) & (cfx.index < fit_end)])
    w_cfx = max(sr2y, 0.0) ** P

    netA, _, _ = CA.build(CA.NAMES, relw_is, df)
    sA = CA.stats(netA)

    # OPT-C1 as-run: weight from day 1 (capital idle pre-2019)
    relw_c1 = relw_is.copy(); relw_c1["CFX4"] = w_cfx
    netC1, _, _ = CA.build(CA.NAMES, relw_c1, df)
    sC1 = CA.stats(netC1)
    # as-run C1 weight matrix -> pre-inception CFX4 capital share (the artifact)
    navA = (1 + df[CA.NAMES].fillna(0)).cumprod().shift(1).fillna(1.0)
    d2A = navA.div(navA.mean(axis=1), axis=0).mul(relw_c1, axis=1)
    d2A = d2A.div(d2A.sum(axis=1), axis=0) * len(CA.NAMES)
    WgC1 = d2A * (GEAR / len(CA.NAMES))

    # OPT-C1b: weight only from CFX4 inception (zero before -> inert per P1 identity)
    wser = pd.Series(0.0, index=df.index)
    wser[wser.index >= first_cfx] = w_cfx
    relw_c1b = pd.DataFrame({n: relw_is[n] for n in CA.NAMES}, index=df.index)
    relw_c1b["CFX4"] = wser
    nav = (1 + df[CA.NAMES].fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw_c1b, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(CA.NAMES)
    Wg = d2 * (GEAR / len(CA.NAMES))
    port = (df[CA.NAMES].fillna(0).values * Wg.values).sum(axis=1)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    netC1b = (pd.Series(port, index=df.index) - to * BPS / 1e4
              - np.maximum(GEAR - 1, 0) * RATE / 252)
    sC1b = CA.stats(netC1b)

    # decomposition: how much of the book did CFX4's zero-return leg hold pre-inception?
    pre = WgC1.loc[WgC1.index < first_cfx, "CFX4"]
    print(f"fitted w_cfx = sr2y^P = {sr2y:.4f}^0.55 = {w_cfx:.4f}")
    print(f"pre-inception ({df.index.min().date()}..{first_cfx.date()}, "
          f"n={len(pre)}): CFX4 capital share mean {pre.mean()/GEAR*100:.3f}% of gross "
          f"(Wg mean {pre.mean():.6f} vs gross {WgC1.abs().sum(axis=1).mean():.4f}), "
          f"earning 0.0000 by fillna(0)")
    print(f"{'option':<28} {'ann%':>8} {'SR':>7} {'MDD%':>7} {'neg':>5}")
    for lbl, s in (("OPT-A keep-as-is", sA), ("OPT-C1 as-run (idle cap)", sC1),
                   ("OPT-C1b inception-fit", sC1b)):
        print(f"{lbl:<28} {s['ann']:8.3f} {s['sr']:7.3f} {s['mdd']:7.2f} "
              f"{s['neg']:>2}/{s['nyrs']:<2}")
    print(f"deltas vs OPT-A: C1 {sC1['ann']-sA['ann']:+.4f}pp  "
          f"C1b {sC1b['ann']-sA['ann']:+.4f}pp  "
          f"(idle-capital artifact = {(sC1b['ann']-sC1['ann']):+.4f}pp)")


if __name__ == "__main__":
    main()
