"""Add point-in-time EDGAR growth/margin features to the GKX monthly panel.

The panel's growth features (rev_growth, eps_growth) were Finnhub CURRENT
snapshots — a lookahead leak, dropped from the PIT set. These new features
are built from the EDGAR as-of quarterly panel (edgar_chars.parquet, the
same filing-dated source as bm/size/roe) with per-ticker lags:
  rev_g_1y / rev_g_3y (PIT revenue growth), ni_g_1y, cfo_g_1y,
  margin (ni/rev) + margin_d1y, omargin_d1y (oper_income/rev), debt_d1y,
  inv_3y (3y asset growth)
Adds columns to gkx_monthly_panel.parquet + names to gkx_names.json.
"""
from __future__ import annotations
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

NEW = ["rev_g_1y", "rev_g_3y", "ni_g_1y", "cfo_g_1y", "margin",
       "margin_d1y", "omargin_d1y", "debt_d1y", "inv_3y"]


def main():
    chars = pd.read_parquet(f"{HERE}/data/edgar_chars.parquet")
    chars["month"] = pd.to_datetime(chars["month"])
    chars = chars.sort_values(["ticker", "month"])
    rev = chars["revenue"].replace(0, np.nan)
    chars["margin"] = chars["net_income"] / rev
    chars["omargin"] = chars["oper_income"] / rev
    g = chars.groupby("ticker")
    c = chars.copy()
    c["rev_g_1y"] = g["revenue"].pct_change(4)
    c["rev_g_3y"] = g["revenue"].pct_change(12)
    c["ni_g_1y"] = g["net_income"].pct_change(4)
    c["cfo_g_1y"] = g["cfo"].pct_change(4)
    c["margin_d1y"] = c["margin"] - g["margin"].shift(4)
    c["omargin_d1y"] = c["omargin"] - g["omargin"].shift(4)
    c["debt_d1y"] = g["lt_debt"].pct_change(4)
    c["inv_3y"] = g["assets"].pct_change(12)
    # merge into panel
    panel = pd.read_parquet(f"{HERE}/data/gkx_monthly_panel.parquet")
    panel["month"] = pd.to_datetime(panel["month"])
    add = c[["month", "ticker"] + NEW]
    panel = panel.merge(add, on=["month", "ticker"], how="left")
    panel.to_parquet(f"{HERE}/data/gkx_monthly_panel.parquet")
    names = json.load(open(f"{HERE}/data/gkx_names.json"))
    names = names + [n for n in NEW if n not in names]
    json.dump(names, open(f"{HERE}/data/gkx_names.json", "w"))
    cov = panel[NEW].notna().mean()
    print("panel now:", panel.shape, "| new feature coverage:")
    print({k: round(float(v), 2) for k, v in cov.items()})


if __name__ == "__main__":
    main()
