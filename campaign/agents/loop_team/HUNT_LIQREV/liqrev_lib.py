"""HUNT_LIQREV engine library. twelve_liq 123-name liquid large-cap panel.
Signal at t close -> position w_t -> EARN r_{t+1} (T+1, no same-day leak).
Costs: 6.4 bps/side on |w_t - w_{t-1}| summed over names. Borrow 0.5%/yr on short notional.
Vol target 10% ann, trailing EXPANDING window min 60d, cap 3.0, scale known at t (uses r<=t-1)."""
import numpy as np, pandas as pd

COST = 6.4e-4
ROOT = "/Users/daxu/software/world-trader"
LIQ = f"{ROOT}/tools/quant/data/twelve_liq"

def load_panel():
    import os
    closes, opens, vols = {}, {}, {}
    for f in sorted(os.listdir(LIQ)):
        if not f.endswith(".csv"): continue
        df = pd.read_csv(os.path.join(LIQ, f), parse_dates=["date"], index_col="date")
        closes[f[:-4]] = df["close"]; opens[f[:-4]] = df["open"]; vols[f[:-4]] = df["vol"]
    cl = pd.DataFrame(closes).sort_index(); op = pd.DataFrame(opens).sort_index()
    vl = pd.DataFrame(vols).sort_index()
    cl = cl[~cl.index.duplicated(keep="last")]; op = op[~op.index.duplicated(keep="last")]
    return cl, op, vl

def universe_mask(cl, min_rows=4900):
    return cl.notna().sum() >= min_rows

def simulate(w, rets, borrow_daily=0.5e-4/252):
    """w: DataFrame name->position (decided at close of date index t).
    rets: DataFrame of same-date returns (close_t/close_{t-1}-1).
    PnL day t+1 = sum_n w[t,n]*rets[t+1,n] - cost(|w_t - w_{t-1}|) - borrow.
    Returns net series indexed by EARNING day (shifted), aligned to rets index."""
    if isinstance(w, pd.Series):
        w = w.to_frame("A")
    if isinstance(w, pd.Series):
        w = w.to_frame("A")
    wprev = w.shift(1).fillna(0.0)                # position before first day = FLAT (w_{-1}=0)
    gross_t = (wprev * rets).sum(axis=1)          # earned on day t from position decided t-1
    turn_t = (w - wprev).abs().sum(axis=1)        # turnover executed at close of day t
    cost_t = turn_t * COST
    short_t = wprev.where(wprev < 0, 0.0).abs().sum(axis=1)
    borrow_t = short_t * borrow_daily
    net_t = gross_t - cost_t - borrow_t
    parts = {"gross": gross_t, "turn": turn_t, "cost": cost_t, "borrow": borrow_t}
    return net_t, parts

def run_book(w, rets, borrow_ann=0.5, vt=True, tgt=0.10):
    """Full book: vol-target the (unscaled) weight path using only trailing info, then
    simulate T+1 PnL with costs+borrow. Returns net series, parts dict."""
    s = vt_scale_from_w(w, rets, tgt=tgt)
    w = w.mul(s, axis=0)
    return simulate(w, rets, borrow_daily=borrow_ann / 1e4 / 252)

def vt_scale_from_w(w, rets, tgt=0.10, min_days=60, cap=3.0):
    """Vol estimate at t uses UNSCALED book return earned at t, but the estimate for the
    scale applied to w_t must use STRICTLY PAST book returns (<= t-1). book_t is earned
    from w_{t-1}; so build book series, shift(1) inside vt_scale."""
    book = (w.shift(1) * rets).sum(axis=1)     # unscaled book return EARNED at t
    return vt_scale(book, tgt=tgt, min_days=min_days, cap=cap)

def vt_scale(ret, tgt=0.10, min_days=60, cap=3.0):
    """scale_t = clip(tgt / expanding_std(r_{<t}), 0, cap). Uses ONLY r up to t-1 (strict).
    rv at row t (position i) = std(ret[0..i-1]) — expanding on shift(1) with min count = min_days-?
    expanding(min_periods=m).std() at row i counts up to i+1 values of `past`; `past` at
    position i holds ret_{i-1}; notna starts at i=1. So rv at position i uses ret_{0..i-1},
    i values, for i>=m. std of ret[:i] (i values, ddof=1)."""
    past = ret.shift(1)
    rv = past.expanding(min_periods=min_days).std() * np.sqrt(252)
    return (tgt / rv).clip(upper=cap).fillna(0.0)

def xs_weights(rets, lb=5, direction=-1, bucket="tercile", mask=None):
    """Cross-sectional reversal/continuation: signal = trailing lb-day return.
    direction=-1 => short recent winners (reversal). Vol-normalize optional via volnorm.
    Returns weights DataFrame (gross ~1 per side for L/S)."""
    sig = rets.rolling(lb).sum()
    if direction == 1: sig = -sig
    if mask is not None: sig = sig.where(mask)
    w = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    if bucket == "tercile":
        q = sig.rank(axis=1, pct=True)
        lo = (q <= 1/3) & sig.notna(); hi = (q >= 2/3) & sig.notna()
    elif bucket == "decile":
        q = sig.rank(axis=1, pct=True)
        lo = (q <= 0.1) & sig.notna(); hi = (q >= 0.9) & sig.notna()
    n_lo, n_hi = lo.sum(axis=1), hi.sum(axis=1)
    w = w.mask(lo, -1.0); w = w.mask(hi, 1.0)
    w = w.div(n_lo.where(n_lo > 0), axis=0).where(lo, w)
    w = w.div(n_hi.where(n_hi > 0), axis=0).where(hi, w)
    return w.fillna(0.0)
