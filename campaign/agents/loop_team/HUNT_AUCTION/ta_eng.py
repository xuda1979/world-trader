"""Treasury-auction demand regime engines."""
import sys, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
from bt import backtest as btb
DATA = os.path.join(ROOT, "tools/quant/data")

def load_auctions():
    df = pd.read_csv(os.path.join(DATA, "treasury_auctions", "tauctions.csv"), parse_dates=["auction_date"])
    return df.sort_values("auction_date")

def daily_btc(df, kind=None):
    """Forward-fill bid-to-cover onto daily calendar (published auction evening)."""
    d = df if kind is None else df[df["type"] == kind]
    s = d.dropna(subset=["bid_to_cover"]).set_index("auction_date")["bid_to_cover"]
    s = s[~s.index.duplicated(keep="last")].sort_index()
    daily = pd.date_range(s.index[0], s.index[-1], freq="D")
    return s.reindex(daily).ffill()

def indirect_share(df, kind="Note"):
    d = df[(df["type"] == kind)].dropna(subset=["indirect_accepted_mmn", "competitive_accepted_mmn"])
    d = d[d["competitive_accepted_mmn"] > 0]
    s = (d["indirect_accepted_mmn"] / d["competitive_accepted_mmn"]).clip(0, 1)
    s.index = d["auction_date"]
    s = s[~s.index.duplicated(keep="last")].sort_index()
    daily = pd.date_range(s.index[0], s.index[-1], freq="D")
    return s.reindex(daily).ffill()

def zgate(s, win=252, invert=False):
    m = s.rolling(win, min_periods=126).mean()
    sd = s.rolling(win, min_periods=126).std(ddof=0)
    z = (s - m) / sd.replace(0.0, np.nan)
    sig = np.sign(z)
    return -sig if invert else sig

def run_on_equity(sig, sym="QQQ"):
    df = pd.read_csv(os.path.join(DATA, "more_etf", f"{sym}.csv"), parse_dates=["date"])
    px = df.set_index("date")["close"].astype(float)
    px = px[~px.index.duplicated(keep="last")].sort_index()
    r = px.pct_change()
    sig_a = sig.reindex(r.index).ffill().fillna(0.0)
    return btb.sleeve(sig_a, r.to_frame("a"))
