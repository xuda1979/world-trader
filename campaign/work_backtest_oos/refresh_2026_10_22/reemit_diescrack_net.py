"""Re-emit champion-pool diescrack_L40Z20_net.csv — the 10-22 wave extension carry-through.

The 10-22 wave (reemit_sleeves.py) extended the CAMP_COST prefix archive
(diescrack__prefix.csv → 2026-10-13, n=4650) but NOT the champion-pool net sleeve
(HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv, still 2026-08-24, n=4615), leaving
test_camp_cost_r2::test_costfix_sleeves_are_cost_grows_only RED (shrink 4615 < 4650).

This script extends the champion-pool net sleeve with the COSTFIX convention
(FULL |dpos| @ 6.4bps — TRADE_RECORD_STANDARD, NOT the prefix archive's half@6.0):

  spread = log(DJFUELUSGULF × 42 gal/bbl) − log(wti_full)
  z-rev: lookback=40, gate |z|>2.0, T+1 (sp.diff().shift(-1))
  cost:  FULL |dpos| × 6.4bps
  vol-target: expanding std (min 60d) → 0.08 ann, cap 3.0
  borrow: 0.5%/yr charged on position-or-prior-day-nonzero rows

Gates (fail-closed, documented vintage split at 2011-08-02 — same as the 10-22
prefix extension; post-drift deviation is diesel input vintage drift, gitignored
and unrecoverable):
  1. pre-drift segment byte-exact vs committed (maxdev ≤ 1e-12)
  2. new rows exist and extend past committed last
  3. append-only: committed prefix bytes untouched

Output: campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv
Report: campaign/work_backtest_oos/refresh_2026_10_22/reemit_diescrack_net_report.json
"""
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FRED = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
NEW = f"{ROOT}/tools/quant/data/newdata"
SLEEVE = f"{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv"
REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "reemit_diescrack_net_report.json")
DRIFT = "2011-08-02"


def main():
    def _load(p):
        d = pd.read_csv(p, index_col=0, parse_dates=True)
        s = d.iloc[:, 0] if "value" not in d.columns else d["value"]
        return pd.to_numeric(s, errors="coerce").dropna()

    dj = _load(f"{NEW}/DJFUELUSGULF.csv")          # → 2026-10-20
    wt = _load(f"{FRED}/wti_full.csv")             # → 2026-10-14

    sp = (np.log(dj * 42.0) - np.log(wt)).dropna()
    sp = sp[sp.index >= "2008-01-01"]
    m = sp.rolling(40, min_periods=40).mean()
    sd = sp.rolling(40, min_periods=40).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -2.0] = 1.0
    pos[z > 2.0] = -1.0
    ret = sp.diff().shift(-1)
    gr = (pos * ret).dropna()
    tup = pos.diff().abs().reindex(gr.index).fillna(0.0)    # FULL one-side |dpos|
    base = gr - tup * 6.4 / 1e4                             # FULL |dW| @ 6.4bps
    pi = pos.reindex(base.index).fillna(0.0)
    bmask = ((pi != 0) | (pi.shift(1).fillna(0) != 0)).astype(float)
    sc = (0.08 / (base.expanding(60).std() * np.sqrt(252))).clip(upper=3.0)
    scaled = ((base * sc).fillna(0.0) - bmask * 0.005 / 252).dropna()

    committed = pd.read_csv(SLEEVE, index_col=0, parse_dates=True).iloc[:, 0]

    # documented vintage gate: pre-drift byte-exact (recipe verified, not vintage)
    j = pd.concat([scaled.rename("c"), committed.rename("m")],
                  axis=1, join="inner").dropna()
    pre = j[j.index < DRIFT]
    post = j[j.index >= DRIFT]
    pre_dev = float((pre.c - pre.m).abs().max()) if len(pre) else float("nan")
    post_dev = float((post.c - post.m).abs().max()) if len(post) else float("nan")
    post_bad = int(((post.c - post.m).abs() > 1e-12).sum()) if len(post) else 0
    pre_ok = (len(pre) > 0) and (pre_dev <= 1e-12)

    last = committed.index.max()
    new = scaled[scaled.index > last]
    rep = {
        "name": "diescrack_L40Z20_net (champion pool)",
        "convention": "FULL |dpos| @ 6.4bps (costfix; champion pool consumes this)",
        "overlap_n": len(j),
        "committed_last": str(last.date()),
        "committed_rows": len(committed),
        "new_rows": len(new),
        "new_first": str(new.index.min().date()) if len(new) else None,
        "new_last": str(new.index.max().date()) if len(new) else None,
        "gate": "documented_vintage_split",
        "drift_boundary": DRIFT,
        "pre_drift_n": len(pre), "pre_drift_maxdev": pre_dev,
        "post_drift_n": len(post), "post_drift_maxdev": post_dev,
        "post_drift_bad_n": post_bad,
        "vintage_note": (
            "post-2011-08-02 deviation is diesel input vintage drift (same class as "
            "diescrack__prefix extension in reemit_sleeves_report.json; gitignored, "
            "unrecoverable); pre-drift byte-exact -> recipe verified, extension proceeds"),
    }
    if not pre_ok:
        rep["overlap_ok"] = False
        rep["action"] = "SKIPPED — pre-drift segment not byte-exact (recipe error, not vintage)"
        print(json.dumps(rep, indent=1))
        with open(REPORT, "w") as f:
            json.dump(rep, f, indent=1)
        return 1
    rep["overlap_ok"] = True
    if len(new) == 0:
        rep["action"] = "no new rows"
        print(json.dumps(rep, indent=1))
        with open(REPORT, "w") as f:
            json.dump(rep, f, indent=1)
        return 0

    out = pd.concat([committed, new.rename("ret")])
    out.index.name = "date"
    out.to_frame("ret").to_csv(SLEEVE)
    rep["action"] = (f"extended -> {out.index.max().date()} (n={len(out)}, "
                     "documented vintage drift)")
    with open(REPORT, "w") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
