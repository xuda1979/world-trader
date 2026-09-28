"""Shared measurement harness for HUNT_BINANCE_AXES (GATES_CONTRACT-compliant).

Conventions (pre-registered in ../CHARTER.md):
- T+1: signal uses data <= t, position applied to return t+1.
- Costs: 6.4bps one-side on FULL |dW| traded notional (0.00064 * |w_t - w_{t-1}|),
  borrow 0.5%/yr on short notional (|min(w,0)| * 0.005 / 252).
- Vol-target: 10% ann, trailing 63d realized vol (expanding fallback), scale clip <= 3.0.
- Scramble: 200x signal-permutation, real daily SR > 95th pctile.
"""
import numpy as np
import pandas as pd

COST_SIDE = 0.00064          # 6.4 bps one-side on full |dW|
BORROW = 0.005 / 252.0       # 0.5%/yr on short notional, daily
VT_TARGET = 0.10             # 10% ann vol target
VT_WIN = 63                  # trailing window for realized vol
CLIP = 3.0                   # max vol-scale multiplier
ANN = 252.0

D = "/Users/daxu/software/world-trader/tools/quant/data"


def load_csv(path):
    df = pd.read_csv(path, parse_dates=["date"], index_col="date").sort_index()
    return df[~df.index.duplicated(keep="last")]


def prices(asset):
    return load_csv(f"{D}/more_crypto/{asset}.csv")


def metrics(asset):
    return load_csv(f"{D}/binance_metrics/{asset}USDT-metrics.csv")


def bookdepth(asset):
    return load_csv(f"{D}/binance_bookdepth/{asset}USDT-bookdepth.csv")


def zscore(s, win):
    m = s.rolling(win, min_periods=max(5, win // 3)).mean()
    sd = s.rolling(win, min_periods=max(5, win // 3)).std()
    return (s - m) / sd.replace(0.0, np.nan)


def pct_change_safe(s, n):
    return s.pct_change(n)


def apply_costs(ret, w):
    """ret: next-day simple return series (aligned to signal day t, payoff t+1).
    w: target weight series. Returns net daily return series indexed like w."""
    w = w.fillna(0.0)
    gross = w * ret
    turn = w.diff().abs().fillna(w.abs())
    cost = COST_SIDE * turn
    borrow = BORROW * w.clip(upper=0.0).abs()
    return gross - cost - borrow


def vol_target(net, raw_w=None):
    """Vol-target the NET stream to 10% ann using trailing 63d vol of the net.
    Scale = target / realized, clipped to [0, 3.0]. Uses only trailing info."""
    vol = net.rolling(VT_WIN, min_periods=20).std() * np.sqrt(ANN)
    scale = (VT_TARGET / vol.replace(0.0, np.nan)).clip(upper=CLIP).fillna(0.0)
    # apply scale to weights BEFORE costs (re-run costs on scaled weights):
    return scale


def run_signal(signal, next_ret, scale_from_weights=None):
    """signal: target weight at t (uses data <= t). next_ret: return t -> t+1.
    Returns net daily return series (vol-targeted, costed)."""
    w = signal.shift(0).copy()
    # vol-target on gross stream: use trailing vol of (w*next_ret)
    gross = (w * next_ret).fillna(0.0)
    vol = gross.rolling(VT_WIN, min_periods=20).std() * np.sqrt(ANN)
    scale = (VT_TARGET / vol.replace(0.0, np.nan)).clip(upper=CLIP)
    w_vt = (w * scale.shift(1)).fillna(0.0)  # scale uses info <= t
    net = w_vt * next_ret
    turn = w_vt.diff().abs().fillna(w_vt.abs())
    net = net - COST_SIDE * turn - BORROW * w_vt.clip(upper=0.0).abs()
    return net.fillna(0.0)


def sr(net):
    net = net[net != 0.0]
    if len(net) < 60:
        return np.nan
    sd = net.std()
    return np.nan if sd == 0 else net.mean() / sd * np.sqrt(ANN)


def halves_sr(net):
    n = net[net != 0.0]
    if len(n) < 60:
        return (np.nan, np.nan)
    h = len(n) // 2
    return sr(n.iloc[:h]), sr(n.iloc[h:])


def neg_years(net):
    y = net.groupby(net.index.year).sum()
    return int((y < 0).sum()), y


def corr_vs(net, other):
    a = net[net != 0.0]
    j = pd.concat([a, other], axis=1, join="inner").dropna()
    if len(j) < 60:
        return np.nan
    return j.iloc[:, 0].corr(j.iloc[:, 1])


def scramble_pvalue(signal, next_ret, n=200, seed=7):
    """Signal-permutation scramble: shuffle signal dates (blocks of 1 day),
    re-run pipeline, compare real SR to null dist."""
    rng = np.random.default_rng(seed)
    real = sr(run_signal(signal, next_ret))
    s = signal.values.copy()
    null = np.empty(n)
    mask = ~np.isnan(s)
    for i in range(n):
        perm = s.copy()
        perm[mask] = rng.permutation(s[mask])
        null[i] = sr(run_signal(pd.Series(perm, index=signal.index), next_ret))
    null = null[~np.isnan(null)]
    if len(null) < 50:
        return np.nan, real
    return float((real <= np.nanpercentile(null, 95))), real


def plateau(cand):  # cand: dict param -> net SR
    vals = {k: v for k, v in cand.items() if not np.isnan(v)}
    if not vals:
        return False, {}
    peak_k = max(vals, key=vals.get)
    peak = vals[peak_k]
    # neighbors within 20% of peak SR and >= 0.5 abs
    ok = {k: v for k, v in vals.items() if v >= 0.8 * peak and v >= 0.5}
    return len(ok) >= 2, ok
