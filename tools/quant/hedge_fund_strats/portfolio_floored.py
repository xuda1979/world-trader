"""Deployment artifact for the FLOORED flagship (the no-losing-year book).

Construction (RESEARCH_REPORT / DISCOVERIES P15/P19):
  h3+AP 50/50 (monthly-cadence sleeves), floored 50% in T-bills (4%/yr
  assumed; guarantee holds while the T-bill >= 3.4% — P21).

Outputs:
  results/portfolio_floored_daily.csv  — daily returns of the floored book
  results/portfolio_floored.json      — stats card + yearly table + guarantee

Usage: python tools/quant/hedge_fund_strats/portfolio_floored.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from blend_6stream import load_ap_gold, load_hedge_streams  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
TBILL = 0.04 / 252  # 4% annual T-bill, daily


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--lev", type=float, default=1.0,
                    help="leverage (P23: x1.10 preserves zero losing years at 3 pct funding; x1.5/x2 break the guarantee)")
    ap.add_argument("--funding", type=float, default=0.03)
    a = ap.parse_args()
    h = load_hedge_streams()
    h3 = pd.concat([h["ls"], h["cta"], h["macro"]], axis=1).mean(axis=1)
    ap_gold = load_ap_gold()
    flag = pd.concat({"h3": h3, "ap": ap_gold}, axis=1).mean(axis=1)
    floored = 0.5 * flag + 0.5 * TBILL
    if a.lev != 1.0:
        floored = a.lev * floored - (a.lev - 1) * a.funding / 252

    out = pd.DataFrame({"floored_flag": floored})
    out.index.name = "date"
    out.to_csv(os.path.join(RESULTS, "portfolio_floored_daily.csv"))

    r = floored.dropna()
    eq = (1 + r).cumprod()
    g = np.log1p(r)
    # monthly-sampled stats (matches FLOORED_FLAGSHIP_REPORT.md convention)
    rm = r.resample("ME").apply(lambda x: (1 + x).prod() - 1).dropna()
    gm = np.log1p(rm)
    eqm = (1 + rm).cumprod()
    yearly = {}
    for y in range(2008, 2027):
        sub = r.loc[str(y)]
        if len(sub):
            yearly[str(y)] = round(float((1 + sub).prod() - 1), 4)
    card = {
        "construction": "h3+AP 50/50, floored 50% in T-bills (4%/yr)",
        "cost_bps_one_side": 6.0,
        "window": [str(r.index.min().date()), str(r.index.max().date())],
        "n_days": int(len(r)),
        "sharpe_daily": round(float((g.mean() * 252 - 0.02) / (g.std() * np.sqrt(252))), 3),
        "ann_return_pct": round(float((1 + r).prod() ** (252 / len(r)) - 1) * 100, 2),
        "max_drawdown_pct": round(float((eq / eq.cummax() - 1).min()) * 100, 2),
        "sharpe_monthly": round(float((gm.mean() * 12 - 0.02) / (gm.std() * np.sqrt(12))), 3),
        "max_drawdown_monthly_pct": round(float((eqm / eqm.cummax() - 1).min()) * 100, 2),
        "negative_years": [y for y, v in yearly.items() if v < 0],
        "worst_year": min(yearly, key=yearly.get),
        "worst_year_pct": round(min(yearly.values()) * 100, 2),
        "yearly_returns_pct": {y: round(v * 100, 2) for y, v in yearly.items()},
        "guarantee": "0.5*year + 2% >= 0 iff year >= -4%; historical worst -3.4% "
                     "(2022); T-bill must stay >= 3.4% (current 3.73% — P21)",
    }
    with open(os.path.join(RESULTS, "portfolio_floored.json"), "w") as fh:
        json.dump(card, fh, indent=2)
    print(json.dumps({k: card[k] for k in
                      ("sharpe_daily", "ann_return_pct", "max_drawdown_pct",
                       "negative_years", "worst_year", "worst_year_pct")}, indent=2))
    print("saved -> results/portfolio_floored_daily.csv + portfolio_floored.json")


if __name__ == "__main__":
    main()
