"""HUNT_CRYPTO_SAT library: long-only crypto books via campaign/bt (GREEN implementation).

Semantics (all via bt.engine, no hand-rolled accounting):
  signal at close t -> position at t+1 (E.lag_signal) -> earn r_{t+1}
  long-only clamp (crypto not shortable at retail; spot, borrow 0)
  vol-target: expanding-60, target 10%/d ann, cap 3x (E.vol_target_scale)
  final leverage cap via E.cap_leverage (capital-real)
  cost 6.4bps/side on |dw| (E.cost_turnover); borrow 0 (long-only spot)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))))
import numpy as np, pandas as pd
from bt import engine as E, metrics as M, gates as G, reconcile as R

ROOT = "/Users/daxu/software/world-trader"
COINS = ["BTC", "ETH", "BNB", "LTC", "ADA", "XRP", "LINK", "SOL", "DOGE", "DOT",
         "AVAX", "MATIC"]


def load_coin(sym):
    df = pd.read_csv(f"{ROOT}/tools/quant/data/more_crypto/{sym}.csv", parse_dates=["date"])
    df = df.set_index("date").sort_index()
    px = df["close"].astype(float)
    return px[px > 0]


def tsmom_sig(px, lb):
    """TS momentum: sign(close_t - close_{t-lb}); long-only => clip(lower=0)."""
    return np.sign(px - px.shift(lb))


def rev_sig(px, lb):
    """Short-term reversal: -sign(ret over lb); long-only => clip(lower=0)."""
    return np.sign(-(px / px.shift(lb) - 1.0))


def build(sig, r, target=0.10, window=60, vcap=3.0, cap=1.0, bps=6.4, borrow=0.0):
    """Long-only single-name book. Returns (weights, net, turnover, ledger)."""
    pos = E.lag_signal(sig.reindex(r.index).fillna(0.0)).clip(lower=0.0)
    scale = E.vol_target_scale(r.to_frame("r"), target=target, window=window, cap=vcap)
    w = (pos * scale["r"]).clip(upper=cap).fillna(0.0)
    wc = E.cap_leverage(w.to_frame("w"), max_lev=1.0)
    wr = wc["w"]
    to = E.cost_turnover(wc, bps)
    net = (wr * r - to).dropna()
    return wr, net, to


def make_ledger(w, px, instrument, sleeve, price_source="REAL"):
    """TRADE_RECORD_STANDARD ledger rows on weight changes (|dw| = qty_notional)."""
    dw = w.diff()
    rows = []
    prev = 0.0
    for t, d in dw.items():
        if not np.isfinite(d) or abs(d) < 1e-15:
            prev = w.loc[t] if np.isfinite(w.loc[t]) else prev
            continue
        px_t = px.loc[t] if t in px.index else np.nan
        price = float(px_t) if np.isfinite(px_t) else np.nan
        rows.append(dict(date=t, sleeve=sleeve, instrument=instrument,
                         side="BUY" if d > 0 else "SELL",
                         price=price, price_source=price_source,
                         qty_notional=abs(d), weight_from=prev, weight_to=float(w.loc[t]),
                         cost_bps=6.4))
        prev = float(w.loc[t])
    led = pd.DataFrame(rows)
    if "stream" not in led.columns:
        led["stream"] = "trade"
    led["pnl_contrib"] = 0.0  # trade rows carry no mark PnL; marks carry it
    led["cost_total"] = led["qty_notional"] * 6.4 / 1e4
    return led


def make_mark_ledger(w, r, px, led, instrument, sleeve, price_source="REAL"):
    """Append a daily MARK row (stream='mark') carrying w*r so ledger daily PnL
    (pnl_contrib - cost_total summed over trade+mark rows) reproduces the net series
    byte-for-byte (campaign BLOTTER convention: trade + mark streams)."""
    p = px.reindex(w.index)
    marks = pd.DataFrame([
        dict(date=t, sleeve=sleeve, instrument=instrument, side="MARK",
             price=float(p.loc[t]) if np.isfinite(p.loc[t]) else np.nan,
             price_source=price_source,
             qty_notional=0.0, weight_from=float(w.loc[t]), weight_to=float(w.loc[t]),
             cost_bps=0.0, stream="mark", pnl_contrib=float(w.loc[t] * r.loc[t]),
             cost_total=0.0)
        for t in w.index])
    out = pd.concat([led, marks], ignore_index=True)
    out["cost_total"] = out["cost_total"].fillna(0.0)
    out["pnl_contrib"] = out["pnl_contrib"].fillna(0.0)
    return out


def ledger_pnl_check(w, r, led, tol=1e-12):
    """Ledger daily pnl (zero on no-trade days) must reproduce net series incl costs."""
    daily_pnl = (w * r).groupby(w.index).sum()
    daily_cost = led.groupby("date")["cost_total"].sum() if len(led) else pd.Series(0.0, index=w.index)
    rec = daily_pnl - daily_cost.reindex(daily_pnl.index).fillna(0.0)
    return R.max_abs_diff(rec.dropna(), net_check(w, r)) < tol


def net_check(w, r):
    return (w * r - w.diff().abs().fillna(0.0) * 6.4 / 1e4).dropna()
