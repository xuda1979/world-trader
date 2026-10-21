"""Curve-feature engines on sovereign curve data. T+1 via bt; costs/margin in bt.backtest.book."""
import sys, os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
from bt.engine import lag_signal, vol_target_scale, cap_leverage, cost_turnover, borrow_cost, margin_cost

DATA = os.path.join(ROOT, "tools/quant/data")

def load_jgb():
    df = pd.read_csv(os.path.join(DATA, "mof_jgb", "jgb_curve.csv"), parse_dates=["date"])
    return df.set_index("date").sort_index()

def load_fx(sym):
    df = pd.read_csv(os.path.join(DATA, "fx", f"{sym}.csv"))
    dc = [c for c in df.columns if c.lower() in ("date", "datetime", "time")][0]
    pc = [c for c in df.columns if c.lower() in ("close", "adj_close", "price", "value")][0]
    s = pd.Series(df[pc].astype(float).values, index=pd.to_datetime(df[dc]))
    return s[~s.index.duplicated(keep="last")].sort_index()

def load_etf(sym):
    df = pd.read_csv(os.path.join(DATA, "more_etf", f"{sym}.csv"), parse_dates=["date"])
    s = df.set_index("date")["close"].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

def slope_spread(df, short="2Y", long="10Y"):
    return df[long] - df[short]

def zscore(s, win=252, minp=126):
    m = s.rolling(win, min_periods=minp).mean()
    sd = s.rolling(win, min_periods=minp).std(ddof=0)
    return (s - m) / sd.replace(0.0, np.nan)

def curve_signal(z, entry=1.0, mode="mom"):
    """+1 long-carry-direction; mom = trade in slope direction; rev = against."""
    sgn = np.sign(z).fillna(0.0)
    sig = sgn if mode == "mom" else -sgn
    return sig

def run_curve_sleeve(feature: pd.Series, px: pd.Series, entry: float = 0.0,
                     mode: str = "mom", win: int = 252, target: float = 0.10,
                     max_lev: float = 1.6) -> pd.Series:
    z = zscore(feature, win=win)
    sig = curve_signal(z, entry=entry, mode=mode)
    r = px.pct_change()
    rets = r.to_frame("a")
    # daily-level: z is daily already (curves are daily) -> plain T+1 via bt.sleeve
    net = __import__("bt").backtest.sleeve(sig, rets, target=target, max_lev=max_lev)
    return net
