"""TFF trader-category engines: z-scores, category differentials, crowd fades."""
import sys, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
from bt import backtest as btb
DATA = os.path.join(ROOT, "tools/quant/data")

def load_tff(fam, cat):
    df = pd.read_csv(os.path.join(DATA, "more_cot", f"tff_{fam}_{cat}.csv"), parse_dates=["date"])
    s = df.set_index("date")["pct_of_oi"].astype(float)
    return s[~s.index.duplicated()].sort_index()

def load_px(sym):
    p = os.path.join(DATA, "twelvedata", f"{sym}.csv")
    if not os.path.exists(p):
        p = os.path.join(DATA, "more_etf", f"{sym}.csv")
    df = pd.read_csv(p, parse_dates=["date"])
    s = df.set_index("date")["close"].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

def z(s, win=26, minp=13):
    m = s.rolling(win, min_periods=minp).mean()
    sd = s.rolling(win, min_periods=minp).std(ddof=0)
    return (s - m) / sd.replace(0.0, np.nan)

def diff_series(fam, c1, c2):
    """c1 - c2 in pct-of-oi space (needs OI to renormalize; approximate via net/OI files)."""
    a = load_tff(fam, c1)
    b = load_tff(fam, c2)
    return a - b   # both are pct of same OI -> difference valid

def live_daily(sig_w, px_index, lag_days=3):
    """COT 3-day lag + daily ffill onto px calendar."""
    s = sig_w.copy()
    s.index = s.index + pd.Timedelta(days=lag_days)
    daily = pd.date_range(px_index[0], px_index[-1], freq="D")
    return s.reindex(daily).ffill().reindex(px_index).ffill().fillna(0.0)

def fade(zs, entry=1.0):
    """crowd fade: short when crowd long (z>entry), long when crowd short."""
    sig = pd.Series(0.0, index=zs.index)
    sig[zs >= entry] = -1.0
    sig[zs <= -entry] = 1.0
    return sig

def mom_sig(zs, entry=1.0):
    sig = pd.Series(0.0, index=zs.index)
    sig[zs >= entry] = 1.0
    sig[zs <= -entry] = -1.0
    return sig

def run(sig_w, sym, lag_days=3, target=0.10):
    px = load_px(sym)
    r = px.pct_change()
    sig_live = live_daily(sig_w, r.index, lag_days)
    return btb.sleeve(sig_live, r.to_frame("a"), target=target)
