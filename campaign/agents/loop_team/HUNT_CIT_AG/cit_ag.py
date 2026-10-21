"""CIT-ags engines: COT CIT/noncomm positioning + PCPS spot + climate on ag ETFs.
Framework: campaign/bt. Honesty: T+1 via bt.lag_signal, COT 3-calendar-day lag,
6.4bps/side, borrow 0.5%, margin 4.5% on (gross-1), cap 1.6."""
import sys, os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, "campaign"))
from bt import backtest as btb
from bt.engine import lag_signal

DATA = os.path.join(ROOT, "tools/quant/data")

def load_close(sym):
    df = pd.read_csv(os.path.join(DATA, "more_etf", f"{sym}.csv"), parse_dates=["date"])
    s = df.set_index("date")["close"].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()

def load_cot(family, kind="cit"):
    if kind == "cit":
        f = os.path.join(DATA, "more_cot", f"cit_{family}.csv")
        df = pd.read_csv(f, parse_dates=["date"])
        return df.set_index("date")["cit_pct_oi"].astype(float).sort_index()
    f = os.path.join(DATA, "more_cot", f"{family}_cot.csv")
    df = pd.read_csv(f, parse_dates=["date"])
    return df.set_index("date")["net_noncomm_pct_oi"].astype(float).sort_index()

def zscore_26w(s: pd.Series) -> pd.Series:
    """Trailing 26-observation z-score (weekly input), expanding before 26. Uses only past."""
    m = s.rolling(26, min_periods=13).mean()
    sd = s.rolling(26, min_periods=13).std(ddof=0)
    return (s - m) / sd.replace(0.0, np.nan)

def cot_lag(s: pd.Series, days: int = 3) -> pd.Series:
    """COT report date -> live date: shift index forward by `days` calendar days."""
    out = s.copy()
    out.index = out.index + pd.Timedelta(days=days)
    return out

def cit_signal(z: pd.Series, entry: float = 1.5, exit_z: float = 0.5) -> pd.Series:
    """+1 when z >= entry, -1 when z <= -entry; hold until |z| < exit_z (hysteresis)."""
    sig = pd.Series(0.0, index=z.index)
    pos = 0.0
    for i, (t, zv) in enumerate(z.items()):
        if pd.isna(zv):
            sig.iloc[i] = 0.0
            continue
        if pos == 0.0:
            if zv >= entry:
                pos = 1.0
            elif zv <= -entry:
                pos = -1.0
        else:
            if pos == 1.0 and zv < exit_z:
                pos = 0.0
            elif pos == -1.0 and zv > -exit_z:
                pos = 0.0
        sig.iloc[i] = pos
    return sig

def _apply_cot_lag(sig: pd.Series, px_index: pd.DatetimeIndex, days: int = 3) -> pd.Series:
    """Push signal live date forward by `days` calendar days, then ffill onto px calendar.
    This models the CFTC Tuesday-report -> tradeable-Monday delay conservatively."""
    shifted = sig.copy()
    shifted.index = shifted.index + pd.Timedelta(days=days)
    # daily reindex + ffill, restricted to px range
    daily = pd.date_range(px_index[0], px_index[-1], freq="D")
    shifted = shifted.reindex(daily).ffill()
    return shifted.reindex(px_index).ffill().fillna(0.0)

def run_sleeve(cot_series: pd.Series, px: pd.Series, entry: float = 1.5, exit_z: float = 0.5,
               target: float = 0.10, max_lev: float = 1.6, lag_days: int = 3) -> pd.Series:
    z = zscore_26w(cot_series)
    sig = cit_signal(z, entry=entry, exit_z=exit_z)
    sig_live = _apply_cot_lag(sig, px.index, days=lag_days)
    r = px.pct_change()
    rets = r.to_frame("a")
    # bt.sleeve lags again internally (T+1) => total lag = COT 3d + T+1 execution
    net = btb.sleeve(sig_live, rets, target=target, max_lev=max_lev)
    return net
