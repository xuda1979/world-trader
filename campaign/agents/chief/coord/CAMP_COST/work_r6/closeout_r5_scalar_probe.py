#!/usr/bin/env python3
"""R6 closeout of the CAMP_SHORT-R6 escalated flag on work_r5/leak_probe_r5.json.

CAMP_SHORT-R6 found that the R5 scalar probe (labeled 'aggregate |dWg| vs champion
same-period ret', corr +0.0156) is not reproducible from a faithful |dWg| and suspected
it was fed a degenerate signed series. This script re-runs the probe with the faithful
convention score = Wg.diff().abs().sum(axis=1) on the champion of record, from own
algebra (weights rebuilt from the 13 sleeves; NOT imported from any builder), and writes
closeout_r5_scalar_probe.json.

Expected (confirmed 2026-09-08): faithful corr +0.2034 champ-span (matches CAMP_SHORT's
independent +0.2034), lag -1 argmax +0.4613 (causal T+1 signature) -> leak=False.
The R5 mislabeled probe stands corrected by this artifact; verdict (leak=False) was and
remains unchanged in every convention tried.

Usage: python3 closeout_r5_scalar_probe.py
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/bt")

from bt import leakcheck  # noqa: E402

PATHS = {
    "brwt15": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    "brwt10": ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    "A5r2": ROOT + "/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
    "a6r7": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    "QAxasts": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
    "carryv2": ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": ROOT + "/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": ROOT + "/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": ROOT + "/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
GEAR, P, IS_END = 1.6, 0.55, pd.Timestamp("2017-01-01")


def champion_weights():
    names = list(PATHS)
    df = pd.DataFrame({n: pd.read_csv(PATHS[n], index_col=0, parse_dates=True)
                       .iloc[:, 0].astype(float).dropna() for n in names})
    df = df[df.index >= "2008-03-31"]
    isr = df[df.index < IS_END]

    def sr1(r):
        r = r.dropna()
        if len(r) < 200 or r.std(ddof=1) <= 1e-12:
            return 0.0
        return float(r.mean() / r.std(ddof=1) * np.sqrt(252))

    relw = pd.Series({n: max(sr1(isr[n]), 0.0) ** P for n in names})
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    return d2.div(d2.sum(axis=1), axis=0) * len(names) * (GEAR / len(names))


def main():
    Wg = champion_weights()
    champ = pd.read_csv(
        ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
        index_col=0, parse_dates=True).iloc[:, 0]
    common = Wg.index.intersection(champ.index)
    out = {
        "note": "R6 closeout of CAMP_SHORT-R6 escalated flag on work_r5/leak_probe_r5.json "
                "scalar probe. Faithful |dWg| = Wg.diff().abs().sum(1) from own-algebra "
                "champion weights. Generator: closeout_r5_scalar_probe.py (this file).",
        "faithful_abs_dWg_vs_champ": leakcheck.leak_probe(
            Wg.diff().abs().sum(axis=1).loc[common], champ.loc[common]),
        "signed_dWg_vs_champ": leakcheck.leak_probe(
            Wg.diff().sum(axis=1).loc[common], champ.loc[common]),
    }
    print(__import__("json").dumps(out, indent=1, default=float))
    with open(ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6/"
                   "closeout_r5_scalar_probe.json", "w") as fh:
        __import__("json").dump(out, fh, indent=1, default=float)


if __name__ == "__main__":
    main()
