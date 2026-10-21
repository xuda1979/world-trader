#!/usr/bin/env python3
"""R7 rung ladder generator (charter (a) 8g-adjacent evidence).

Rungs = the constructible refresh vintages themselves (the delta is confined to the
2026 tail BY CONSTRUCTION: prefix <= 2026-08-10 is pinned byte-identical, so w-scaling
is not a free parameter here). Each rung re-solves the full 13-sleeve book with the
named subset refreshed and reports the inner-join delta vs the champion of record.

Usage: python3 rung_ladder.py   # writes rung_ladder.json + prints the ladder table
"""
import json
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/scripts")
sys.path.insert(0, ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r7")

import rawew13v2_build as B13  # noqa: E402
import rawew15_refresh_candidate as R15  # noqa: E402

RF = "campaign/agents/chief/coord/CAMP_COST/work_r6/refresh"
SUBSETS = {
    "none": {},
    "diescrack": {"diescrack"},
    "brwt10": {"brwt10"},
    "brwt7": {"brwt7"},
    "brwt5": {"brwt5"},
    "brwt10+brwt7+brwt5": {"brwt10", "brwt7", "brwt5"},
    "brwt10+brwt7+brwt5+diescrack": {"brwt10", "brwt7", "brwt5", "diescrack"},
}
OUT = ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r7/"


def sr(x):
    x = pd.Series(x).dropna()
    return float(x.mean() / x.std(ddof=1) * np_sqrt252(x)) if x.std(ddof=1) > 0 else float("nan")


def np_sqrt252(_):
    return 252 ** 0.5


def book_from_frame(frame):
    """Champion algebra on an arbitrary 13-col frame (natural re-solve relw)."""
    isr = frame[frame.index < B13.IS_END]
    relw = pd.Series({n: max(B13.is_sr(isr[n]), 0.0) ** B13.P for n in frame.columns})
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(frame.columns)
    Wg = d2 * (B13.GEAR / len(frame.columns))
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=frame.index) - to * B13.BPS / 1e4
           - np.maximum(B13.GEAR - 1, 0) * B13.RATE / 252)
    return net, relw, Wg


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {"ann": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
            "sr": float(r.mean() / r.std(ddof=1) * 252 ** 0.5),
            "mdd": mdd * 100, "neg": int((yr < 0).sum()), "end": str(r.index[-1].date())}


champ = pd.read_csv(ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
rows = []
for name, sub in SUBSETS.items():
    paths = {n: (f"{RF}/{n}__refresh.csv" if n in sub else B13.PATHS[n]) for n in B13.NAMES}
    frame = pd.DataFrame({n: B13.load(paths[n]).dropna() for n in B13.NAMES})
    frame = frame[frame.index >= "2008-03-31"]
    net, relw, Wg = book_from_frame(frame)
    j = pd.concat([champ.rename("c13"), net.rename("c")], axis=1, join="inner").dropna()
    s13, sc = stats(j.c13), stats(j.c)
    gross_max = float(Wg.abs().sum(axis=1).max())
    to_bp = float((Wg.diff().abs().sum(axis=1).mean()) * 252 * B13.BPS)
    neg_new = sc["neg"]
    rows.append({
        "subset": name, "dAnn_pp": sc["ann"] - s13["ann"], "dSR": sc["sr"] - s13["sr"],
        "dMDD_pp": sc["mdd"] - s13["mdd"], "neg_years": neg_new,
        "grossMax": gross_max, "to_bp_yr": to_bp, "end": sc["end"],
        "st_dAnn_pp": sc["ann"] - s13["ann"], "st_SR": sc["sr"],
    })

hdr = (f"{'subset':30s} {'dAnn_pp':>9s} {'dSR':>8s} {'dMDD_pp':>8s} {'neg':>4s} "
       f"{'grossMax':>13s} {'to_bp':>7s} {'end':>11s} {'st_dAnn':>8s} {'st_SR':>7s}")
print(hdr)
for r in rows:
    print(f"{r['subset']:30s} {r['dAnn_pp']:+9.4f} {r['dSR']:+8.4f} {r['dMDD_pp']:+8.4f} "
          f"{r['neg_years']:4d} {r['grossMax']:13.10f} {r['to_bp_yr']:7.4f} "
          f"{r['end']:>11s} {r['st_dAnn_pp']:+8.4f} {r['st_SR']:7.4f}")
json.dump(rows, open(OUT + "rung_ladder.json", "w"), indent=1)
print(f"\nwrote {OUT}rung_ladder.json")
