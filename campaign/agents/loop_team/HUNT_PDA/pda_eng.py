"""Primary-dealer absorption / SOMA / FIMA flow engines (fixed tauctions.csv)."""
import sys, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
from bt import backtest as btb
DATA = os.path.join(ROOT, "tools/quant/data")

def load_a():
    df = pd.read_csv(os.path.join(DATA, "treasury_auctions", "tauctions.csv"), parse_dates=["date"])
    return df.sort_values("date")

def share_daily(df, num_col, den_col="total_accepted_mmn", types=("Note", "Bond"), lag=1):
    d = df[df["type"].isin(types)].dropna(subset=[num_col, den_col])
    d = d[d[den_col] > 0]
    s = (d[num_col] / d[den_col]).clip(0, 1.5)
    s.index = d["date"]
    s = s[~s.index.duplicated(keep="last")].sort_index()
    daily = pd.date_range(s.index[0], s.index[-1], freq="D")
    out = s.reindex(daily).ffill()
    out.index = out.index + pd.Timedelta(days=lag)
    return out

def z(s, win=252, minp=126):
    m = s.rolling(win, min_periods=minp).mean()
    sd = s.rolling(win, min_periods=minp).std(ddof=0)
    return (s - m) / sd.replace(0.0, np.nan)

def run_gate(sig_daily, sym="SPY"):
    df = pd.read_csv(os.path.join(DATA, "twelvedata", f"{sym}.csv"), parse_dates=["date"])
    px = df.set_index("date")["close"].astype(float)
    px = px[~px.index.duplicated(keep="last")].sort_index()
    r = px.pct_change()
    sig_a = sig_daily.reindex(r.index).ffill().fillna(0.0)
    return btb.sleeve(sig_a, r.to_frame("a"))
