"""Decision-level IC audit: d3 vs d2 (champion) at the honest screen.

For each run's saved walk-forward predictions (results/*/predictions.csv),
compute the RANK IC between prediction and ACTUAL forward return at each
refit date, for horizons 5/10/20d — the horizons the strategy actually
holds.  This is the audit that confirmed the d2 champion's alpha was real
(+0.024 at 20d); if d3's decision-level IC is higher, its 1.31 Sharpe is
signal, not noise.

Usage: python tools/quant/ls/audit_decision_ic.py
"""
from __future__ import annotations
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd
from scipy import stats

from tools.quant.ls import data
from tools.quant.ls.config import Config

RUNS = [
    ("d2_champion", "tools/quant/ls/results/sharpe_campaign/champion_trail_screen"),
    ("d3_tw160", "tools/quant/ls/results/deep_retune/d3"),
    ("d3r10", "tools/quant/ls/results/sharpe_campaign/d3_refit10"),
]
CFG_JSON = "tools/quant/ls/results/validation_test/mkt_full/config.json"
HORIZONS = (5, 10, 20)


def main() -> int:
    with open(os.path.join(ROOT, CFG_JSON)) as f:
        import json
        d = json.load(f)
    cfg = Config(**{**d, "screen_trailing_only": True})
    panel = data.load_panel(cfg)
    prices = panel["prices"]

    rows = []
    for label, rel in RUNS:
        pred = pd.read_csv(os.path.join(ROOT, rel, "predictions.csv"),
                           index_col=0, parse_dates=True)
        out = {"run": label}
        for h in HORIZONS:
            fwd = prices.shift(-h) / prices - 1.0
            ics, n_obs = [], []
            for t, date in enumerate(prices.index):
                if date not in pred.index:
                    continue
                pv = pred.loc[date]
                fv = fwd.loc[date]
                m = np.isfinite(pv.values) & np.isfinite(fv.values)
                if m.sum() >= 10:
                    rho, _ = stats.spearmanr(pv.values[m], fv.values[m])
                    ics.append(rho)
                    n_obs.append(int(m.sum()))
            ics = np.array(ics)
            out[f"ic{h}"] = round(float(np.nanmean(ics)), 4)
            out[f"icir{h}"] = round(float(np.nanmean(ics) / np.nanstd(ics))
                                    if np.nanstd(ics) > 0 else np.nan, 3)
            out[f"pos{h}"] = round(float(np.mean(ics > 0)), 2)
            out[f"n{h}"] = int(len(ics))
        rows.append(out)
        print(out)

    df = pd.DataFrame(rows)
    out_csv = os.path.join(ROOT, "results/ic_audit/decision_ic_d2_vs_d3.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"\nSaved -> {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
