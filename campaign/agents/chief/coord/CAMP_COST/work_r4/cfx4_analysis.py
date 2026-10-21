"""CAMP_COST R4 — CFX4 vestigial-slot decision analysis (charter: ANALYSIS ONLY).

Quantifies, at CHAMPION level under FULL |dW| @ 6.4bps one-side, the three options for the
CFX4 slot (relw == 0.0 exactly because CFX4 data starts 2019-09-10 > IS_END 2017-01-01 ->
IS-SR = 0 -> weight 0 -> the "13-sleeve" champion is a 12-sleeve book):

  OPT-A  keep-as-is   : committed champion of record (reference; no change).
  OPT-B  drop slot    : 12-name POOL+NEW minus CFX4, weights refitted on the SAME IS window.
  OPT-C  OOS-fitted weight rule for late-start sleeves: fit relw from the FIRST 2y of the
         sleeve's own live data AFTER its start (min 500 obs), i.e. a pre-registered rule
         "SR over first 24 months of live sleeve history" that any late-start sleeve could
         have been assigned WITHOUT hindsight; applied to CFX4 only (2019-09-10..2021-09-09).

NO champion/results file is written by this script. Everything is in-memory + stdout.

NOTE ON HONESTY: OPT-C's weight for CFX4 is fitted on data that is OUT-OF-SAMPLE relative to
the champion's IS window but IN the champion's backtest span (2019-2021 inside 2008-2026) —
so OPT-C is a RULE-CHANGE backtest, NOT a like-for-like performance comparison. Its full-window
numbers are optimistic by construction (the weight was seen the data it weights). This is the
exact concern charter flags; we report both the rule's numbers and that caveat, plus a
walk-forward variant (rolling 2y fit, weight applied from day 2y+1) as the honest version.
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")

POOL = {
    "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2": "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7": "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
NEW = {
    "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
NAMES = list(POOL) + list(NEW)
PATHS = {**POOL, **NEW}
GEAR, RATE, BPS = 1.6, 0.045, 6.4
IS_END = pd.Timestamp("2017-01-01")
P = 0.55
SPAN_START = "2008-03-31"


def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return pd.to_numeric(df[c], errors="coerce").astype(float)


def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252))


def build(names, relw, df):
    """rawew13v2 algebra on a given name set/weights. Returns (net, gross, turnover)."""
    nav = (1 + df[names].fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw[names], axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(names)
    Wg = d2 * (GEAR / len(names))
    port = (df[names].fillna(0).values * Wg.values).sum(axis=1)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    net = (pd.Series(port, index=df.index)
           - to * BPS / 1e4
           - np.maximum(GEAR - 1, 0) * RATE / 252)
    return net, Wg.abs().sum(axis=1), to


def stats(r):
    r = r.dropna()
    ann = (1 + r).prod() ** (252 / len(r)) - 1
    sr = r.mean() / r.std(ddof=1) * np.sqrt(252)
    nav = (1 + r).cumprod()
    mdd = (nav / nav.cummax() - 1).min()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    h = len(r) // 2
    h1 = r.iloc[:h].mean() / r.iloc[:h].std(ddof=1) * np.sqrt(252)
    h2 = r.iloc[h:].mean() / r.iloc[h:].std(ddof=1) * np.sqrt(252)
    oos = r[r.index >= IS_END]
    oos_ann = (1 + oos).prod() ** (252 / len(oos)) - 1
    oos_sr = oos.mean() / oos.std(ddof=1) * np.sqrt(252)
    return dict(n=len(r), ann=ann * 100, sr=sr, mdd=mdd * 100, neg=(yr < 0).sum(),
                nyrs=len(yr), worst=yr.min() * 100, h1=h1, h2=h2,
                oos_ann=oos_ann * 100, oos_sr=oos_sr,
                span=f"{r.index.min().date()}..{r.index.max().date()}")


def main():
    df = pd.DataFrame({n: load(PATHS[n]).dropna() for n in NAMES})
    df = df[df.index >= SPAN_START]
    isr = df[df.index < IS_END]
    SR = pd.Series({n: is_sr(isr[n]) for n in NAMES})
    relw_is = np.maximum(SR, 0.0) ** P
    names12 = [n for n in NAMES if n != "CFX4"]

    rows = []

    # ---- OPT-A: keep-as-is (must byte-match the committed champion) ----
    netA, grossA, toA = build(NAMES, relw_is, df)
    sA = stats(netA)
    comm = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                       index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    j = pd.concat([comm.rename("c"), netA.rename("a")], axis=1, join="inner").dropna()
    devA = float((j.c - j.a).abs().max())
    rows.append(("OPT-A keep-as-is (13 slots, CFX4 relw=0)", sA, devA, toA, names12 + ["CFX4"]))

    # ---- OPT-B: drop the CFX4 slot, refit weights on the SAME IS window ----
    relw_b = np.maximum(SR[names12], 0.0) ** P
    netB, grossB, toB = build(names12, relw_b, df)
    sB = stats(netB)
    rows.append(("OPT-B drop CFX4 slot (12 slots, IS refit)", sB, None, toB, names12))

    # ---- OPT-C1: OOS-fitted weight rule (pre-registered: first-24m live SR) ----
    cfx = df["CFX4"].dropna()
    w0 = cfx.index.min()
    fit_end = w0 + pd.DateOffset(months=24)
    cfx_fit = cfx[(cfx.index >= w0) & (cfx.index < fit_end)]
    sr_cfx = is_sr(cfx_fit)
    print(f"OPT-C fit window: {cfx_fit.index.min().date()}..{cfx_fit.index.max().date()} "
          f"n={len(cfx_fit)} SR={sr_cfx:.4f}")
    relw_c = relw_is.copy()
    relw_c["CFX4"] = max(sr_cfx, 0.0) ** P
    netC, grossC, toC = build(NAMES, relw_c, df)
    sC = stats(netC)
    rows.append(("OPT-C1 OOS-fitted 2y-live-SR weight (13 slots)", sC, None, toC, NAMES))

    # ---- OPT-C2: honest walk-forward — weight from live data BEFORE each date, min 500 obs,
    # refit quarterly; weight 0 until 500 obs accrued (no peeking) ----
    names13 = NAMES
    qstarts = pd.date_range(df.index.min(), df.index.max(), freq="QS")
    relw_wf = relw_is.copy()
    wf_sr = {}
    for qs in qstarts:
        obs = cfx[cfx.index < qs]
        if len(obs) >= 500:
            wf_sr[qs] = is_sr(obs)
    # apply: for each date, weight in force = last quarterly refit with >=500 obs
    wser = pd.Series(0.0, index=df.index)
    last = 0.0
    for qs in qstarts:
        if qs in wf_sr:
            last = max(wf_sr[qs], 0.0) ** P
        wser[wser.index >= qs] = last
    relw_wf_mat = pd.DataFrame({n: relw_wf[n] for n in names13},
                               index=df.index).assign(CFX4=wser)
    # re-run algebra with time-varying CFX4 weight
    nav = (1 + df[names13].fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw_wf_mat, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(names13)
    Wg = d2 * (GEAR / len(names13))
    port = (df[names13].fillna(0).values * Wg.values).sum(axis=1)
    toW = Wg.diff().abs().sum(axis=1).fillna(0.0)
    netW = (pd.Series(port, index=df.index) - toW * BPS / 1e4
            - np.maximum(GEAR - 1, 0) * RATE / 252)
    sW = stats(netW)
    rows.append(("OPT-C2 walk-forward live-SR weight (min 500 obs)", sW, None, toW, names13))

    # ---- report ----
    print("=" * 100)
    print(f"{'option':<48} {'ann%':>7} {'SR':>7} {'MDD%':>7} {'neg':>5} {'worst%':>8} "
          f"{'H1SR':>6} {'H2SR':>6} {'OOSann':>7} {'turn bp/y':>9}")
    print("=" * 100)
    for label, s, dev, to, _ in rows:
        print(f"{label:<48} {s['ann']:7.3f} {s['sr']:7.3f} {s['mdd']:7.2f} "
              f"{s['neg']:>2}/{s['nyrs']:<2} {s['worst']:8.2f} {s['h1']:6.2f} {s['h2']:6.2f} "
              f"{s['oos_ann']:7.2f} {to.mean() * 252 * BPS:9.4f}")
    print("=" * 100)
    print(f"OPT-A recon vs committed champion: inner={len(j)} maxdev={devA:.3e} "
          f"{'BYTE-EXACT' if devA < 1e-12 else 'DIFF'}")
    print(f"CFX4 sleeve stats (standalone, its own span): n={len(cfx)} "
          f"span {cfx.index.min().date()}..{cfx.index.max().date()}")
    sc = stats(cfx)
    print(f"  ann={sc['ann']:.2f}% SR={sc['sr']:.3f} MDD={sc['mdd']:.2f}% "
          f"neg={sc['neg']}/{sc['nyrs']}")
    # correlation of CFX4 with the 12-sleeve book (post-2019 overlap only, honest)
    book12 = df[names12].mean(axis=1).dropna()
    jj = pd.concat([cfx.rename("c"), book12.rename("b")], axis=1, join="inner").dropna()
    print(f"  corr(CFX4, eq-w 12-book) on overlap n={len(jj)}: "
          f"{jj.c.corr(jj.b):+.4f}  (charter decorr pref |corr|<0.15)")
    # CFX4 OOS SR (post 2017 = whole life)
    print(f"  CFX4 whole-life SR {sc['sr']:.3f}; first-2y fit SR {sr_cfx:.4f}")
    # net contribution if it had been included at, e.g., equal-ish weight
    for wtest in (0.5, 1.0):
        relw_t = relw_is.copy()
        relw_t["CFX4"] = wtest
        netT, _, _ = build(NAMES, relw_t, df)
        sT = stats(netT)
        print(f"  [ref only] CFX4 relw forced to {wtest}: ann {sT['ann']:.3f}% SR {sT['sr']:.3f} "
              f"MDD {sT['mdd']:.2f}% neg {sT['neg']}/{sT['nyrs']}")


if __name__ == "__main__":
    main()
