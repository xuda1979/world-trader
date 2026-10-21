"""
features.py
-----------
Constructs the input feature tensor Z_t = { Z_i^{(t)} } following the AlphaPortfolio
paper's input construction.

Per the paper (Section 2.3 / Appendix B):
  - For each asset i, the state is the sequence Z_i^{(t)} = ( z_{i,t-K}, ..., z_{i,t} )
    of the firm-level + market characteristics over a K=11 lagged lookback (12 months).
  - Characteristics are built from raw firm/accounting/market data (Appendix B lists 51;
    our synthetic panel provides a representative subset, constructed in the same style).
  - No look-ahead: features at month t use only information available at or before t,
    and targets (returns) are the NEXT-month realized returns.
"""

import numpy as np
import pandas as pd


def build_characteristics(df):
    """Construct a rich set of characteristics from the synthetic raw panel.

    Mirrors the spirit of Appendix B: z-scores, ratios, log-changes, per past-month
    statistics. Returns a DataFrame with columns = characteristics (float).
    """
    d = df.sort_values(["id", "date"]).copy()

    # market cap proxy already logged in `size`; recover level
    d["mktcap"] = np.exp(d["size"])
    d["a2me"] = 1.0 / (d["mktcap"] + 1e-9)          # assets-to-market (proxy)
    d["bm"] = d["bm"]
    d["mom_12_1"] = d["mom_12_1"]
    d["mom_1"] = d["mom_1"]
    d["size"] = d["size"]
    d["vol"] = d["vol"]
    d["log_vol"] = np.log(d["vol"])
    d["roe"] = d["roe"]
    d["acc"] = d["acc"]
    d["liq"] = d["liq"]
    d["illiq"] = 1.0 / (d["liq"] + 1e-9)
    d["std_turn"] = np.abs(d["liq"])               # turnover dispersion proxy
    d["tot_vol"] = d["vol"]

    # within-month cross-sectional ranks (importance: rank transforms are standard)
    def xrank(x):
        return x.groupby(d["date"]).rank(pct=True)

    for col in ["mktcap", "a2me", "bm", "mom_12_1", "mom_1", "size",
                "vol", "log_vol", "roe", "acc", "liq", "illiq"]:
        d[f"r_{col}"] = xrank(d[col])

    # interactions / non-linear terms (model-discovered structure)
    d["mom_x_size"] = d["r_mom_12_1"] * d["r_size"]
    d["mom_x_vol"] = d["r_mom_12_1"] * d["r_vol"]
    d["value_x_size"] = d["r_bm"] * d["r_size"]

    feature_cols = [
        "a2me", "bm", "mom_12_1", "mom_1", "size", "vol", "log_vol",
        "roe", "acc", "liq", "illiq",
        "r_mktcap", "r_a2me", "r_bm", "r_mom_12_1", "r_mom_1", "r_size",
        "r_vol", "r_log_vol", "r_roe", "r_acc", "r_liq", "r_illiq",
        "mom_x_size", "mom_x_vol", "value_x_size",
    ]
    return d, feature_cols


def build_lagged_tensor(df, features, K=11):
    """Return, per (date,id), a (K+1, F) lagged feature array and next-month target.

    z_i^{(t)} [t-K:t+1] are ordered oldest->newest. Aligned so no look-ahead:
      - features at month t are from window ending t
      - target = realized return in month t+1
    """
    d = df.sort_values(["id", "date"]).copy()
    d["tnext"] = d.groupby("id")["ret"].shift(-1)   # next-month return (target)
    d = d.dropna(subset=["tnext"])

    rows = []
    for (date, id_), g in d.groupby(["date", "id"]):
        # get the trailing K+1 months of features for this stock (oldest->newest)
        hist = d[(d["id"] == id_) & (d["date"] <= date)].tail(K + 1)
        if len(hist) < K + 1:
            continue  # not enough history (listing filter already handles >=24)
        arr = hist[features].to_numpy(dtype=np.float32)  # (K+1, F)
        rows.append(dict(
            date=date, id=id_,
            seq=arr,
            target=float(g["tnext"].iloc[0]),
            sect=int(g["sector"].iloc[0]),
        ))
    return pd.DataFrame(rows)
