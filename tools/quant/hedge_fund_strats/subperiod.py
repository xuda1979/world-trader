"""Sub-period Sharpe decomposition for all strategy equity curves.

Uses the CSV convention (geometric Sharpe, cost-inclusive pct_change
series) consistent with strategy_comparison.csv. Runs on whatever
results/ currently contains (set TRADING_COST_BPS in core.py first).

Usage:
    python tools/quant/hedge_fund_strats/subperiod.py [--periods 4]
"""

import glob
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
RISK_FREE = 0.02
TRADING_DAYS = 252

PERIODS = [
    ("2008-2012", "2008-01-01", "2012-12-31"),
    ("2013-2017", "2013-01-01", "2017-12-31"),
    ("2018-2022", "2018-01-01", "2022-12-31"),
    ("2023-2026", "2023-01-01", "2026-12-31"),
]

SKIP = {"equity_6stream", "equity_Multi_Strategy_EW"}  # composites handled separately


def geom_sharpe(daily_rets: pd.Series) -> float:
    """Geometric (annualized-log) Sharpe, matching strategy_comparison.csv."""
    daily_rets = daily_rets.dropna()
    if len(daily_rets) < 30:
        return np.nan
    g = np.log1p(daily_rets)
    mu, sigma = g.mean() * TRADING_DAYS, g.std() * np.sqrt(TRADING_DAYS)
    return (mu - RISK_FREE) / sigma if sigma > 0 else np.nan


def main():
    rows = []
    for path in sorted(glob.glob(os.path.join(RESULTS, "equity_*.csv"))):
        name = os.path.basename(path).replace("equity_", "").replace(".csv", "")
        if any(s in name for s in SKIP):
            continue
        eq = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        r = eq.pct_change()
        row = {"strategy": name}
        for label, start, end in PERIODS:
            sub = r.loc[start:end]
            row[label] = geom_sharpe(sub)
        row["All"] = geom_sharpe(r)
        rows.append(row)
    df = pd.DataFrame(rows).set_index("strategy")
    df = df.sort_values("All", ascending=False)
    print(df.round(2).to_string())
    df.round(4).to_csv(os.path.join(RESULTS, "subperiod_sharpe_12rt.csv"))
    print("\nsaved -> results/subperiod_sharpe_12rt.csv")


if __name__ == "__main__":
    main()
