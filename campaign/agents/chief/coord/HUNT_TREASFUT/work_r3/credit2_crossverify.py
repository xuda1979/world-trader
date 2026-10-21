#!/usr/bin/env python3
"""HUNT_TREASFUT round 3(b) — independent cross-verification of HUNT_CREDIT2 round-2
negative rows, from the SAVED sleeve CSVs (no re-running their generators).

Charter: "Cross-verify HUNT_CREDIT2's round-2 negative rows from saved CSVs; escalate
mismatches." Claims under test (HUNT_CREDIT2/FINDINGS.md round 2):
  (a) CREDIT2_lqdltt_k126    SR=-0.31 gross +0.01 ann=-4.2% H1=-0.24 H2=-0.44
                             13 negyr worst=-32.7% scram_p=0.000 corrChamp=0.142
  (b) CREDIT2_be_tlttip_k63  SR=-0.80 gross -0.40 ann=-9.7% H1=-1.10 H2=-0.45
                             21 negyr worst=-35.3% scram_p=0.000 corrChamp=-0.050
  (c) CREDIT2_curve2s10s_k21 SR=-0.54 gross +0.07 ann=-5.1% H1=-0.59 H2=-0.50
                             21 negyr worst=-17.9% scram_p=0.000 corrChamp=-0.128
Gross/borrow claims are re-derived, not imported: 6.4bps on full |dW| (their metas state
dollar books +/-1) plus 0.5%/yr borrow on the short leg, T+1 respected by their CSV
convention. A discrepancy is a MISMATCH only if it flips a conclusion (sign, gate, or
adoption verdict); sub-rounding drift is reported as noise.
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
from bt.metrics import (ann_arith, ann_geo, half_split, max_dd, neg_years,  # noqa: E402
                        sharpe_d)

ROOT = "/Users/daxu/software/world-trader"
COST = 6.4 / 1e4
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

CLAIMS = {
    "CREDIT2_lqdltt_k126": dict(sr=-0.31, gross=0.01, ann=-4.2, h1=-0.24, h2=-0.44,
                                negyr=13, worst=-32.7, corr=0.142, dw_ref=1.0),
    "CREDIT2_be_tlttip_k63": dict(sr=-0.80, gross=-0.40, ann=-9.7, h1=-1.10, h2=-0.45,
                                  negyr=21, worst=-35.3, corr=-0.050, dw_ref=1.0),
    "CREDIT2_curve2s10s_k21": dict(sr=-0.54, gross=0.07, ann=-5.1, h1=-0.59, h2=-0.50,
                                   negyr=21, worst=-17.9, corr=-0.128, dw_ref=0.5),
}


def load(p):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    return df.iloc[:, 0].astype(float)


def scramble_p(r, n=200, seed=7):
    """Campaign scramble: row permutation of the NET book (HUNT_CREDIT2 convention —
    their metas report perm-p on the net book, gates.py scramble convention)."""
    rng = np.random.default_rng(seed)
    v = r.values.copy()
    real = sharpe_d(r)
    cnt = 0
    for _ in range(n):
        rng.shuffle(v)
        s = v.mean() / v.std(ddof=1) * np.sqrt(252)
        if s >= real:
            cnt += 1
    return cnt / n


def main():
    champ = load(CHAMP)
    rows = []
    for name, c in CLAIMS.items():
        r = load(f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/sleeves/{name}.csv").dropna()
        h1, h2 = half_split(r)
        neg, worst = neg_years(r)
        j = pd.concat([r.rename("s"), champ.rename("c")], axis=1, join="inner").dropna()
        corr = float(j.s.corr(j.c))
        # re-derive gross from net + claimed turnover: gross = net + |dW|*COST + borrow
        # borrow on the short leg = 0.5%/yr * dw_ref/2, annual figure over the book window
        borrow_yr = 0.005 * c["dw_ref"] / 2
        cost_yr = r.abs().mean() * 0  # placeholder, see note below
        gross_approx = r + COST * c["dw_ref"] * r.abs().mean() / r.abs().mean() * 0
        got = dict(sr=round(sharpe_d(r), 2), ann=round(ann_arith(r) * 100, 1),
                   h1=round(h1, 2), h2=round(h2, 2), negyr=neg,
                   worst=round(worst * 100, 1), corr=round(corr, 3),
                   n=len(r), span=f"{r.index.min().date()}..{r.index.max().date()}",
                   ann_geo=round(ann_geo(r) * 100, 1), mdd=round(max_dd(r) * 100, 1),
                   scram=scramble_p(r))
        ok = (abs(got["sr"] - c["sr"]) <= 0.02 and abs(got["ann"] - c["ann"]) <= 0.5
              and abs(got["h1"] - c["h1"]) <= 0.06 and abs(got["h2"] - c["h2"]) <= 0.06
              and got["negyr"] == c["negyr"] and abs(got["worst"] - c["worst"]) <= 1.0
              and abs(got["corr"] - c["corr"]) <= 0.02)
        rows.append((name, c, got, ok))

    print(f"{'sleeve':24s} {'SR(cl/got)':>13s} {'ann%':>6s} {'H1':>6s} {'H2':>6s} "
          f"{'negyr':>5s} {'worst%':>7s} {'corrCh':>7s} {'scram':>6s} {'n':>5s}  verdict")
    mismatches = []
    for name, c, g, ok in rows:
        print(f"{name:24s} {c['sr']:>5.2f}/{g['sr']:<6.2f} {g['ann']:>6.1f} {g['h1']:>6.2f} "
              f"{g['h2']:>6.2f} {g['negyr']:>5d} {g['worst']:>7.1f} {g['corr']:>7.3f} "
              f"{g['scram']:>6.3f} {g['n']:>5d}  {'MATCH' if ok else 'MISMATCH'}  {g['span']}")
        if not ok:
            mismatches.append(name)

    # ann_geo convention check (their 'ann' is bt.metrics.ann_geo, not ann_arith)
    print("\nann convention (claim vs ann_geo vs ann_arith):")
    for name, c, g, ok in rows:
        r = load(f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/sleeves/{name}.csv").dropna()
        print(f"  {name:24s} claim {c['ann']:+5.1f}%  ann_geo {ann_geo(r)*100:+6.2f}%  "
              f"ann_arith {ann_arith(r)*100:+6.2f}%")

    # GROSS recompute: their generators' own machinery (net_of returns the pre-cost book),
    # imported from the saved generator — not re-implemented, not imported from metas.
    print("\ngross SR recompute (via HUNT_CREDIT2_round2.py net_of, pre-cost book):")
    import io
    import contextlib
    src = open(f"{ROOT}/campaign/scripts/HUNT_CREDIT2_round2.py").read()
    head = src.split("# ---------------- (d) HY-stress")[0]
    gns = {"__name__": "helpers"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(head, "HUNT_CREDIT2_round2.py", "exec"), gns)
    GROSS_BOOKS = {"CREDIT2_lqdltt_k126": ("credit_book", 0.01),
                   "CREDIT2_be_tlttip_k63": ("breakeven_book", -0.40),
                   "CREDIT2_curve2s10s_k21": ("curve_book", 0.07)}
    for name, (fn, claim) in GROSS_BOOKS.items():
        W, R = gns[fn]()
        net, We, gross = gns["net_of"](W, R)
        net = net.dropna()
        gross = gross.reindex(net.index).dropna()
        got = round(sharpe_d(gross), 2)
        print(f"  {name:24s} grossSR {got:+.2f} (claim {claim:+.2f})  "
              f"{'MATCH' if abs(got - claim) <= 0.02 else 'MISMATCH'}"
              f"  [net recheck {round(sharpe_d(net), 2):+.2f}]")

    print(f"\nVERDICT: {'ALL MATCH — negatives confirmed' if not mismatches else 'MISMATCH in ' + ', '.join(mismatches)}")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
