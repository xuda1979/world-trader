"""Macro regime gates on NEW FRED block."""
import sys, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
from bt import backtest as btb
DATA = os.path.join(ROOT, "tools/quant/data")

def load(sid):
    df = pd.read_csv(os.path.join(DATA, "more_fred", f"{sid}.csv"), parse_dates=["date"])
    s = df.set_index("date")["value"].astype(float)
    return s[~s.index.duplicated()].sort_index()

def load_px(sym):
    df = pd.read_csv(os.path.join(DATA, "more_etf", f"{sym}.csv"), parse_dates=["date"])
    s = df.set_index("date")["close"].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

def zsig(s, win=252, minp=126, invert=False):
    m = s.rolling(win, min_periods=minp).mean()
    sd = s.rolling(win, min_periods=minp).std(ddof=0)
    z = (s - m) / sd.replace(0.0, np.nan)
    out = np.sign(z).fillna(0.0)
    return -out if invert else out

def longflat(s, win=252, minp=126, thr=0.0):
    """1 when level above its rolling median, else 0."""
    med = s.rolling(win, min_periods=minp).median()
    return (s > med + thr).astype(float)

def mom_gate(s, lb=63):
    return np.sign(s.pct_change(lb)).fillna(0.0)

def run(sig, sym="QQQ"):
    px = load_px(sym)
    r = px.pct_change()
    sig_a = sig.reindex(r.index).ffill().fillna(0.0)
    return btb.sleeve(sig_a, r.to_frame("a"))
