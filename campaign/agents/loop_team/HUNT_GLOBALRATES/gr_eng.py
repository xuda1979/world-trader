"""Global rates regime engines."""
import sys, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
from bt import backtest as btb
DATA = os.path.join(ROOT, "tools/quant/data")

CTYS = ["USM156N","DEM156N","JPM156N","GBM156N","CAM156N","AUM156N","CHM156N","KRM156N"]

def load_lt(ccy_suffix):
    df = pd.read_csv(os.path.join(DATA, "more_fred", f"IRLTLT01{ccy_suffix}.csv"), parse_dates=["date"])
    s = df.set_index("date")["value"].astype(float)
    return s[~s.index.duplicated()].sort_index()

def panel():
    cols = {}
    for c in CTYS:
        try:
            cols[c.replace("M156N","")] = load_lt(c)
        except FileNotFoundError:
            pass
    return pd.DataFrame(cols).dropna(how="all").ffill()

def synchrony_signal(panel_df, lb=63, up_q=0.6, lag_days=35):
    """Fraction of countries with rising LT yields (lb-day change); trade SPY longflat:
    in when synchrony up-fraction > up_q."""
    chg = panel_df.pct_change(lb, fill_method=None)
    up = (chg > 0).mean(axis=1)
    sig = (up > up_q).astype(float)
    sig.index = sig.index + pd.Timedelta(days=lag_days)
    return sig

def us_lead_signal(panel_df, lb=63, lag_days=35, confirm=True):
    """US yield momentum direction; optionally require majority confirm."""
    us = panel_df["US"].pct_change(lb, fill_method=None)
    sig = np.sign(us)
    if confirm:
        others = panel_df.drop(columns=["US"]).pct_change(lb, fill_method=None)
        conf = np.sign(others.mean(axis=1))
        sig = sig.where(np.sign(sig) == np.sign(conf), 0.0)
    sig.index = sig.index + pd.Timedelta(days=lag_days)
    return sig

def load_px(sym):
    df = pd.read_csv(os.path.join(DATA, "twelvedata", f"{sym}.csv"), parse_dates=["date"])
    s = df.set_index("date")["close"].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

def run(sig_daily, sym="SPY"):
    px = load_px(sym)
    r = px.pct_change()
    sig_a = sig_daily.reindex(r.index).ffill().fillna(0.0)
    return btb.sleeve(sig_a, r.to_frame("a"))
