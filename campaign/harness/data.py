"""Shared data loaders for the campaign. All agents import from here."""
import os
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
PANEL = f"{ROOT}/tools/quant/data/twelve_big"        # 298 names, 2006-09..2026-08 OHLCV
EXT   = f"{ROOT}/tools/quant/data/twelve_extend"     # 440 names (newer listing coverage)
FF    = f"{ROOT}/tools/quant/data/ff_factors"
FRED  = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
STOOQ = f"{ROOT}/tools/quant/hedge_fund_strats/data_stooq"
FX    = f"{ROOT}/tools/quant/data/fx"
SLEEVE_LIB = f"{ROOT}/campaign/results/sleeve_library"
COST = 6.0  # bps one side

def panel(extended=False):
    """dict symbol -> DataFrame close series (adjusted proxy close)."""
    d = EXT if extended else PANEL
    out = {}
    for f in os.listdir(d):
        if f.endswith(".csv"):
            df = pd.read_csv(os.path.join(d, f), parse_dates=["date"], index_col="date")
            out[f[:-4]] = df
    return out

def closes(extended=False):
    ps = panel(extended)
    px = pd.DataFrame({k: v["close"] for k, v in ps.items()})
    px = px.sort_index()
    return px[~px.index.duplicated(keep="last")]

def volumes(extended=False):
    ps = panel(extended)
    return pd.DataFrame({k: v["vol"] for k, v in ps.items()}).sort_index()

def _clean_ff(df):
    df = df.dropna(how="all")
    df = df[df.index.astype(str).str.match(r"^\d{8}$")]
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    return df / 100.0

def ff_factors():
    df = pd.read_csv(f"{FF}/F-F_Research_Data_Factors_daily.csv", skiprows=4,
                     index_col=0)
    return _clean_ff(df)

def ff_mom():
    df = pd.read_csv(f"{FF}/F-F_Momentum_Factor_daily.csv", skiprows=12, index_col=0)
    return _clean_ff(df)

def fred(name):
    df = pd.read_csv(f"{FRED}/{name}.csv", index_col=0, parse_dates=True)
    return df["value"] if "value" in df.columns else df.iloc[:, 0]

def fred_all():
    out = {}
    for f in os.listdir(FRED):
        if f.endswith(".csv"):
            s = fred(f[:-4])
            out[f[:-4]] = s
    return out

def save_sleeve(ret: pd.Series, path: str, meta: str = ""):
    """Save a sleeve per contract; strips pre-first-trade zeros? No: keep all rows."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = ret.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    r = r[~r.index.duplicated(keep="last")].sort_index()
    df = pd.DataFrame({"ret": r.values}, index=r.index)
    df.index.name = "date"
    df.to_csv(path)
    with open(path + ".meta", "w") as fh:
        fh.write(meta or "")
    return path

def apply_cost(ret_gross: pd.Series, turnover_per_day: float = 1.0, cost_bps: float = COST):
    """ret_gross is BEFORE costs; turnover_per_day = one-side notional traded per $nav per day."""
    return ret_gross - turnover_per_day * cost_bps / 1e4
