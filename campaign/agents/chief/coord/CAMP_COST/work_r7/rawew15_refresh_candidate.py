#!/usr/bin/env python3
"""RAWEW15 REFRESH CANDIDATE builder (CAMP_COST R7 charter (a), refresh adoption).

13-sleeve PURE re-solve of rawew13v2_build with the 4 R6-staged refreshed sleeves
(brwt10/7/5 -> 2026-08-28, diescrack -> 2026-08-24; work_r6/refresh/*__refresh.csv)
swapped into PATHS. relw = max(IS_SR,0)^0.55 on the SAME IS window (<2017-01-01); the
refresh appends only post-2026-08-10 tail rows, all post-IS, so the re-solve weights are
identical to the committed ones (maxdev 2.22e-16, pinned by test) and the book's rows
<= 2026-08-10 are byte-identical to the champion of record (no history relabel — the
refresh protocol's own invariant).

Construction mirrors rawew13v2_build.build() exactly: same load+dropna, same
>=2008-03-31 filter, same nav.shift(1) causal NAV-drift weights row-normalized to sum K
then scaled to gross 1.6 exactly, same FULL |dW| @ 6.4bps one-side cost + 4.5%/yr margin
on (1.6-1), day-1 entry uncharged.

Usage:
  python3 rawew15_refresh_candidate.py --verify   # pins vs committed champion (no writes)
  python3 rawew15_refresh_candidate.py --emit     # writes results/RAWEW15_REFRESH_CANDIDATE_*
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/scripts")

import rawew13v2_build as B13  # noqa: E402

RF = "campaign/agents/chief/coord/CAMP_COST/work_r6/refresh"  # B13.load prepends ROOT
REFRESHED = {  # staged sleeves (R6, byte-pinned; recon maxdev <= 9.999e-17 vs committed)
    "brwt10": f"{RF}/brwt10__refresh.csv",
    "brwt7": f"{RF}/brwt7__refresh.csv",
    "brwt5": f"{RF}/brwt5__refresh.csv",
    "diescrack": f"{RF}/diescrack__refresh.csv",
}
# ITER19 (2026-09-13): the main builder PRUNED brwt15. This candidate predates that,
# so pin the historical 13-sleeve pool it was actually built on — otherwise it
# silently rebuilds a different book and every archived pin breaks.
_HIST_BRWT15 = "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv"
NAMES15 = list(B13.NAMES) + ([] if "brwt15" in B13.NAMES else ["brwt15"])
PATHS15 = {n: REFRESHED.get(n, B13.PATHS.get(n, _HIST_BRWT15)) for n in NAMES15}

GEAR, RATE, BPS = B13.GEAR, B13.RATE, B13.BPS
IS_END, P, START = B13.IS_END, B13.P, "2008-03-31"
CUT = pd.Timestamp("2026-08-10")  # last committed end across the refreshed sleeves

last_Wg = None  # module-global weights frame of the most recent build() (test access)
last_df = None  # module-global sleeve-return frame of the most recent build()


def build(frame=None):
    """Return (net, relw, gross, to, df). Sets module globals last_Wg / last_df."""
    global last_Wg, last_df
    if frame is None:
        frame = pd.DataFrame({n: B13.load(PATHS15[n]).dropna() for n in NAMES15})
        frame = frame[frame.index >= START]
    isr = frame[frame.index < IS_END]
    SR = pd.Series({n: B13.is_sr(isr[n]) for n in frame.columns})
    relw = np.maximum(SR, 0.0) ** P
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(frame.columns)
    Wg = d2 * (GEAR / len(frame.columns))
    last_Wg, last_df = Wg, frame
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=frame.index)
           - to * BPS / 1e4
           - np.maximum(GEAR - 1, 0) * RATE / 252)
    gross = Wg.abs().sum(axis=1)
    return net, relw, gross, to, frame


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {
        "n": int(len(r)), "start": str(r.index[0].date()), "end": str(r.index[-1].date()),
        "ann_cagr_pct": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
        "ann_arith_pct": float(r.mean() * 252 * 100),
        "sr": float(r.mean() / r.std(ddof=1) * np.sqrt(252)),
        "mdd_pct": mdd * 100,
        "neg_years": int((yr < 0).sum()), "worst_year_pct": float(yr.min() * 100),
        "n_years": int(len(yr)),
    }


def halves_sr(r):
    mid = r.index[len(r) // 2]
    sr = lambda x: (x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std(ddof=1) > 0 else float("nan")
    return sr(r[r.index < mid]), sr(r[r.index >= mid]), mid


def year_table(r):
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return yr


def main_emit():
    net, relw, gross, to, df = build()
    relw.sort_index().to_frame("relw").to_csv(
        ROOT + "/campaign/results/RAWEW15_REFRESH_CANDIDATE_weights.csv")
    net.to_frame("ret").to_csv(
        ROOT + "/campaign/results/RAWEW15_REFRESH_CANDIDATE_daily.csv")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--verify"
    net, relw, gross, to, df = build()
    champ = pd.read_csv(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([champ.rename("c13"), net.rename("c15")], axis=1, join="inner").dropna()
    s13, s15 = stats(j.c13), stats(j.c15)
    pre = net[net.index <= CUT]
    jp = pd.concat([champ.rename("c13"), pre.rename("c15")], axis=1, join="inner").dropna()
    pre_dev = float((jp.c13 - jp.c15).abs().max())
    # capital-real per-day weight delta (same-day book vs book) for turnover attribution
    print(f"frame: n={len(df)} sleeves={len(df.columns)} "
          f"{df.index.min().date()}..{df.index.max().date()}")
    print(f"prefix<={CUT.date()}: inner={len(jp)} maxdev={pre_dev:.3e} "
          f"{'IDENTICAL (no history relabel)' if pre_dev < 1e-12 else 'DIFF'}")
    print(f"gross: mean {gross.mean():.9f} max {gross.max():.12f} days>1.6 "
          f"{int((gross > 1.6 + 1e-9).sum())}")
    print(f"turnover {to.mean()*252*BPS:.4f} bp/yr  margin {np.maximum(GEAR-1,0)*RATE*100:.2f}%/yr")
    print(f"c13: {s13}")
    print(f"c15: {s15}")
    print(f"DELTA: dAnn {s15['ann_cagr_pct']-s13['ann_cagr_pct']:+.4f}pp "
          f"dSR {s15['sr']-s13['sr']:+.4f} dMDD {s15['mdd_pct']-s13['mdd_pct']:+.4f}pp "
          f"neg {s15['neg_years']}")
    h1o, h2o, mid = halves_sr(j.c13)
    h1n, h2n, _ = halves_sr(j.c15)
    print(f"halves book SR: c13 H1 {h1o:.3f} H2 {h2o:.3f} | c15 H1 {h1n:.3f} H2 {h2n:.3f} "
          f"(dH1 {h1n-h1o:+.4f} dH2 {h2n-h2o:+.4f}, split {mid.date()})")
    isc, oos = net[net.index < "2017-01-01"], net[net.index >= "2017-01-01"]
    sro = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(252)
    jc = pd.concat([champ.rename("c13"), net.rename("c15")], axis=1, join="inner")
    sro2 = lambda s: sro(jc[s][jc[s].index < "2017-01-01"].dropna())
    sro3 = lambda s: sro(jc[s][jc[s].index >= "2017-01-01"].dropna())
    print(f"IS/OOS SR: c13 {sro2('c13'):.3f}/{sro3('c13'):.3f} | "
          f"c15 {sro2('c15'):.3f}/{sro3('c15'):.3f}")
    yr13, yr15 = year_table(j.c13), year_table(j.c15)
    diff = pd.DataFrame({"c13": yr13, "c15": yr15})
    diff["d"] = diff.c15 - diff.c13
    print("yearly deltas (only years with |d|>1e-12 printed):")
    print(diff[diff.d.abs() > 1e-12].to_string())
    if mode == "--emit":
        main_emit()
        print("emitted RAWEW15_REFRESH_CANDIDATE_daily.csv + _weights.csv")


if __name__ == "__main__":
    main()
