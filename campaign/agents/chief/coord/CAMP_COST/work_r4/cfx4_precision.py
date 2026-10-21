"""CAMP_COST R4 — precision probes behind CFX4_SLOT_DECISION.md.

Complements cfx4_analysis.py (headline table). Answers, exactly:
  P1  Is OPT-B (drop slot) IDENTICAL to OPT-A to machine precision? Why? (algebra: a
      zero-relw slot cancels out of the row-normalized NAV-drift weights, because
      nav.mean(axis=1) is a per-row SCALAR that divides out of d2/d2.sum()).
  P2  Exact deltas ann/SR/MDD/neg for OPT-C1/C2 vs OPT-A (not 3-dp display).
  P3  CFX4 yearly returns (charter gate d: <=2 neg years each > -5%).
  P4  First date + magnitude of a nonzero CFX4 weight under OPT-C2, and its final weight.
  P5  Rule generality: apply the SAME walk-forward live-SR rule to the two youngest POOL
      sleeves (QAxasts 2006, carryv2 2006) as a pseudo-validation: does the rule track
      their committed IS-fitted weights sanely? (n=2 honesty probe, not a gate.)
In-memory only. No champion/results file touched.
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/work_r4")

import cfx4_analysis as CA  # noqa: E402  (single source of PATHS/algebra)

GEAR, RATE, BPS, P, IS_END = CA.GEAR, CA.RATE, CA.BPS, CA.P, CA.IS_END


def wg_matrix(names, relw_mat):
    """NAV-drift weights for a (possibly time-varying) relw matrix. Returns Wg, df."""
    df = pd.DataFrame({n: CA.load(CA.PATHS[n]).dropna() for n in CA.NAMES})
    df = df[df.index >= CA.SPAN_START]
    nav = (1 + df[names].fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw_mat[names], axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(names)
    return d2 * (GEAR / len(names)), df


def main():
    df = pd.DataFrame({n: CA.load(CA.PATHS[n]).dropna() for n in CA.NAMES})
    df = df[df.index >= CA.SPAN_START]
    isr = df[df.index < IS_END]
    SR = pd.Series({n: CA.is_sr(isr[n]) for n in CA.NAMES})
    relw_is = np.maximum(SR, 0.0) ** P
    names12 = [n for n in CA.NAMES if n != "CFX4"]
    cfx = df["CFX4"].dropna()

    # ---- P1: OPT-A vs OPT-B to machine precision + the cancellation identity ----
    netA, _, toA = CA.build(CA.NAMES, relw_is, df)
    netB, _, toB = CA.build(names12, np.maximum(SR[names12], 0.0) ** P, df)
    j = pd.concat([netA.rename("a"), netB.rename("b")], axis=1).dropna()
    print(f"P1  max|netA-netB| = {float((j.a-j.b).abs().max()):.3e}  "
          f"max|toA-toB| = {float((toA-toB).abs().max()):.3e}  "
          f"n={len(j)}  -> drop-slot is EXACT no-op when relw_CFX4=0")
    # identity check: Wg_i == nav_i*relw_i / sum_12(nav_j*relw_j) * GEAR
    WgA, _ = wg_matrix(CA.NAMES, pd.DataFrame({n: relw_is[n] for n in CA.NAMES},
                                              index=df.index))
    nav = (1 + df[names12].fillna(0)).cumprod().shift(1).fillna(1.0)
    ident = nav.mul(relw_is[names12], axis=1)
    ident = ident.div(ident.sum(axis=1), axis=0) * GEAR
    print(f"    identity max|WgA - nav*relw/sum*GEAR| = "
          f"{float((WgA[names12] - ident).abs().max().max()):.3e}  "
          f"(mean(nav) cancels -> zero-weight slot is algebraically inert)")

    # ---- P2: exact deltas vs OPT-A ----
    sA = CA.stats(netA)
    # OPT-C1
    fit_end = cfx.index.min() + pd.DateOffset(months=24)
    sr_cfx2y = CA.is_sr(cfx[(cfx.index >= cfx.index.min()) & (cfx.index < fit_end)])
    relw_c1 = relw_is.copy(); relw_c1["CFX4"] = max(sr_cfx2y, 0.0) ** P
    netC1, _, toC1 = CA.build(CA.NAMES, relw_c1, df)
    sC1 = CA.stats(netC1)
    # OPT-B net (12 slots, IS refit) for the delta table
    netB12 = netB
    # OPT-C2 (same loop as cfx4_analysis, kept byte-identical in spirit)
    qstarts = pd.date_range(df.index.min(), df.index.max(), freq="QS")
    wser = pd.Series(0.0, index=df.index)
    last = 0.0
    first_date, first_w = None, None
    for qs in qstarts:
        obs = cfx[cfx.index < qs]
        if len(obs) >= 500:
            last = max(CA.is_sr(obs), 0.0) ** P
            if first_date is None:
                first_date, first_w = qs, last
        wser[wser.index >= qs] = last
    relw_wf = pd.DataFrame({n: relw_is[n] for n in CA.NAMES}, index=df.index)
    relw_wf["CFX4"] = wser
    WgC2, _ = wg_matrix(CA.NAMES, relw_wf)
    port = (df[CA.NAMES].fillna(0).values * WgC2.values).sum(axis=1)
    toC2 = WgC2.diff().abs().sum(axis=1).fillna(0.0)
    netC2 = (pd.Series(port, index=df.index) - toC2 * BPS / 1e4
             - np.maximum(GEAR - 1, 0) * RATE / 252)
    sC2 = CA.stats(netC2)

    print("P2  exact deltas vs OPT-A (ann pp / SR / MDD pp / neg-yrs):")
    for lbl, s, n, to in (("OPT-B", sA, netB12, toB), ("OPT-C1", sC1, netC1, toC1),
                          ("OPT-C2", sC2, netC2, toC2)):
        jj = pd.concat([netA.rename("a"), n.rename("x")], axis=1).dropna()
        print(f"    {lbl:<8} dAnn {s['ann']-sA['ann']:+.4f}pp  dSR {s['sr']-sA['sr']:+.5f}  "
              f"dMDD {s['mdd']-sA['mdd']:+.4f}pp  neg {s['neg']}/{s['nyrs']}  "
              f"max|dNet| {float((jj.a-jj.x).abs().max()):.3e}  "
              f"turn {float(to.mean()*252*BPS):.4f} bp/y")

    # ---- P3: CFX4 yearly returns (gate d) ----
    yr = cfx.groupby(cfx.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = yr[yr < 0]
    print(f"P3  CFX4 yearly: {len(yr)} yrs {yr.index.min()}-{yr.index.max()}, "
          f"neg {len(neg)}/{len(yr)}, worst {yr.min()*100:.2f}% ({yr.idxmin()})")
    print("    " + "  ".join(f"{y}:{v*100:+.2f}" for y, v in yr.items()))
    print(f"    gate-d verdict: {'PASS' if len(neg) <= 2 and (neg > -0.05).all() else 'FAIL'} "
          f"(<={min(2,len(neg))} neg yrs, each > -5%)")
    # halves + full contract view on its OWN span
    sc = CA.stats(cfx)
    print(f"    standalone: SR {sc['sr']:.3f} H1 {sc['h1']:.2f} H2 {sc['h2']:.2f} "
          f"n={sc['n']} ({sc['span']}) -> n<19y span, charter '19y intent' NOT met (disclosed)")

    # ---- P4: CFX4 weight path under OPT-C2 ----
    print(f"P4  OPT-C2 CFX4 weight: first nonzero {first_date.date()} w={first_w:.4f}; "
          f"final {wser.iloc[-1]:.4f}; mean over nonzero days "
          f"{wser[wser > 0].mean():.4f}; nonzero days {int((wser > 0).sum())}/{len(wser)}")
    w12 = pd.Series({n: relw_is[n] for n in names12})
    print(f"    committed 12-sleeve relw range: {w12.min():.3f}..{w12.max():.3f} "
          f"(CFX4 walk-fwd weight sits {'inside' if w12.min() <= wser.max() <= w12.max() else 'outside'})")

    # ---- P5: rule generality probe on 2 youngest POOL sleeves ----
    print("P5  same walk-forward rule applied to QAxasts / carryv2 (youngest POOL sleeves):")
    for nm in ("QAxasts", "carryv2"):
        s = df[nm].dropna()
        ws = pd.Series(0.0, index=df.index)
        last = 0.0
        for qs in qstarts:
            obs = s[s.index < qs]
            if len(obs) >= 500:
                last = max(CA.is_sr(obs), 0.0) ** P
            ws[ws.index >= qs] = last
        committed = relw_is[nm]
        print(f"    {nm:<9} data from {s.index.min().date()}: rule weight now {ws.iloc[-1]:.3f} "
              f"vs committed IS-fit {committed:.3f} (ratio {ws.iloc[-1]/committed:.2f})")


if __name__ == "__main__":
    main()
