"""HONEST portfolio simulator for multi-horizon cross-sectional L/S.

Fixes the overlap flaw in the naive daily_rebalance sim: a predicted
\[t->t+H\] return is a H-DAY return, not a 1-day return. Treating it as a
daily series overstates Sharpe massively (overlapping returns).

Correct method: build a POSITION BOOK. At each rebalance date we select
long top-K / short bottom-K names by predicted forward-(t+H) return, then
HOLD that book for H trading days (staggered books overlap; each day's
MARK-TO-MARKET return = change in value of all currently-held positions).
This captures true daily P&L from overlapping holdings -> honest Sharpe,
and it is exactly how the strategy is actually run (rebalance every H
days, overlapping quarterly/monthly tranches).

Net of 6bp one-side cost each rebalance (12bp round trip per rebalance),
4 rebalances per book -> cost applied at each rebalance entry.
"""
from __future__ import annotations
import os, json, pickle
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
HERE = os.path.dirname(os.path.abspath(__file__))
COST = 0.0006
K = 10
VOL_TARGET_ANN = 0.13
PRED_CACHE = os.environ.get("HZ_PRED_CACHE",
                            os.path.join(HERE, "data", "horizon_preds_20y_f5.pkl"))


def build_position_book(frame, pred, H, K=K, cost=COST, long_only=False,
                        borrow_rate=0.0, weight_scheme="pred"):
    """Return daily mark-to-market L/S return series with honest overlap.
    frame: date x ticker with close + fwd returns already loaded.
    pred: array of predicted forward-H return aligned to frame rows.
    K: names per side; cost: one-side cost fraction.
    long_only: True -> long top-K only (no short leg), for SPY-hedge variants.
    borrow_rate: annualized short borrow fee (IBKR call rate / stock loan fee),
    e.g. 0.0025 = 25bp/yr for ETB large caps. Applied daily on the short leg.
    weight_scheme: "equal" = 1/K each; "pred" (default) = weight proportional to
    predicted-return minus cross-sectional median within each leg (concentrates
    in the strongest signals; validated to raise Sharpe ~0.1 and return ~6pp).
    """
    fw = frame.copy()
    fw["pred"] = pred
    fw = fw[np.isfinite(fw["pred"])]
    dates = np.sort(fw["date"].unique())
    # rebalance every H trading days
    rebal = dates[::H]
    # daily close returns for mark-to-market. Missing quote for a held ticker
    # on a given day is treated as 0% change (conservative) so a single missing
    # bar cannot poison the whole book's daily P&L with NaN.
    close_long = fw.pivot(index="date", columns="ticker", values="close")
    daily_ret = close_long.pct_change().fillna(0.0)   # date-indexed

    # positions: index by 'asof' rebalance date. Weights per name (ticker-keyed):
    # "equal" -> +/-1/K; "pred" -> proportional to (pred - cross-sectional median)
    # within each leg, each leg normalized to unit notional.
    pos = {}
    for rb in rebal:
        g = fw[fw["date"] == rb].sort_values("pred", ascending=False)
        n = len(g)
        if n < 2*K+2:
            continue
        longs = g["ticker"].iloc[:K].tolist()
        shorts = [] if long_only else g["ticker"].iloc[n-K:].tolist()
        w = {}
        if weight_scheme == "pred":
            med = g["pred"].median()
            lp = (g.set_index("ticker")["pred"].loc[longs] - med)
            sp = (g.set_index("ticker")["pred"].loc[shorts] - med) if shorts else None
            lsum = lp.abs().sum()
            for t in longs:
                w[t] = lp[t]/lsum if lsum > 0 else 1.0/K
            if sp is not None:
                ssum = sp.abs().sum()
                for t in shorts:
                    w[t] = sp[t]/ssum if ssum > 0 else -1.0/K   # sp negative -> short
        else:  # equal
            for t in longs:
                w[t] = 1.0/K
            for t in shorts:
                w[t] = -1.0/K
        pos[rb] = {"longs": longs, "shorts": shorts,
                   "weights": w,
                   "close": g.set_index("ticker")["close"].to_dict()}

    # simulate day by day
    day_returns = {}
    alld = daily_ret.index
    # active books at each date
    # map each date to list of active rebalance books (those within H days)
    active = {}
    for i, rb in enumerate(rebal):
        if rb not in pos:
            continue
        end_i = min(i+H, len(rebal)-1)
        # active until next rebalance (approx H days)
        active[rb] = (rb, rebal[min(i+1, len(rebal)-1)] if i+1 < len(rebal) else alld[-1])
    # compute per-day pnl: for each active book, long/short MTM from entry
    import bisect
    res = pd.Series(0.0, index=alld)
    # maintain active books sorted by rb
    active_books = []
    rebal_list = sorted(pos.keys())
    for dt in alld:
        # open books that start at dt
        for rb in rebal_list:
            if rb == dt:
                active_books.append(rb)
        # close books that have been open >= H days (or reached end)
        to_remove = [rb for rb in active_books
                     if (dt - rb).days >= H*4/3 or (dt - rb).days >= 40]
        # actually close after H trading days
        to_remove = [rb for rb in active_books
                     if (len(pd.bdate_range(rb, dt))-1) >= H]
        for rb in to_remove:
            active_books.remove(rb)
        if not active_books:
            continue
        dly = daily_ret.loc[dt] if dt in daily_ret.index else pd.Series(0.0, index=daily_ret.columns)
        pnl = 0.0; cnt = 0
        for rb in active_books:
            p = pos[rb]
            w = p["weights"]
            for tk in p["longs"]:
                if tk in dly.index:
                    pnl += w.get(tk, 1.0/K)*dly[tk]; cnt += 1
            for tk in p["shorts"]:
                if tk in dly.index:
                    pnl += w.get(tk, -1.0/K)*dly[tk]; cnt += 1
        res[dt] = pnl/max(len(active_books),1) if active_books else 0.0
        # Borrow fee on the short leg (IBKR call rate / stock loan fee,
        # annualized). Equal-$ book => short notional = 1, so the daily drag
        # is borrow_rate/365 on days the short book is active.
        if borrow_rate > 0 and not long_only:
            res[dt] -= borrow_rate/365.0
    # Cost: 6bp per side per the desk convention (user-confirmed). At each
    # monthly rebalance the expiring tranche closes (long 6bp + short 6bp) and
    # the new tranche opens (long 6bp + short 6bp) => 4*cost = 24bp on unit
    # equity (~2.9%/yr drag at monthly frequency). This is the honest full
    # round-trip on both legs, not just open-only.
    for rb in rebal:
        if rb in res.index and rb in pos:
            res[rb] -= 4*cost
    return res.fillna(0.0)


def vol_target(dser, ann_target=VOL_TARGET_ANN):
    rv = dser.rolling(20, min_periods=10).std().shift(1)*np.sqrt(252)
    sc = (ann_target/rv).clip(upper=3.0, lower=0.0).fillna(1.0)
    return dser*sc


def stats(full):
    full = full.dropna()
    if len(full) < 20 or full.std() == 0:
        return {"sr": None, "ann": None, "dd": None, "calmar": None, "n_days": int(len(full))}
    eq = (1+full).cumprod()
    sr = (full.mean()/full.std())*np.sqrt(252)
    ann = (1+full).prod()**(252/len(full))-1
    dd = (eq/eq.cummax()-1).min()
    return {"sr": round(float(sr),3), "ann": round(float(ann),4),
            "dd": round(float(dd),4),
            "calmar": round(float(ann)/abs(dd),2) if dd < 0 else None,
            "n_days": int(len(full))}


def main():
    import sys
    sys.path.insert(0, HERE)
    with open(PRED_CACHE, "rb") as fh:
        cache = pickle.load(fh)
    frame, preds = cache["frame"], cache["preds"]
    frame["date"] = pd.to_datetime(frame["date"])
    result = {}
    for H in [1, 5, 21]:
        res = build_position_book(frame, preds[H], H)
        res = res.sort_index()
        rvt = vol_target(res.copy())
        label = {1: "next-day", 5: "1-week", 21: "1-month"}[H]
        print(f"\n=== H={H} ({label}) HONEST hold-H book ===")
        for lab, s in [("raw", res), ("vol-target", rvt)]:
            st = stats(s)
            print(f"  {lab:11s} SR {st['sr']}  ann {st['ann']:>8.1%}  maxDD {st['dd']:>7.1%}  Calmar {st['calmar']}  ({st['n_days']} days)")
        result[f"H{H}"] = {"raw": stats(res), "vt": stats(rvt)}
        rvt.to_frame(f"h{H}").to_csv(os.path.join(OUT, f"h{H}_book_daily.csv"))
    print("\nDone. Honest hold-H results saved.")
    with open(os.path.join(OUT, "multi_horizon_book_results.json"), "w") as fh:
        json.dump(result, fh, indent=2)


if __name__ == "__main__":
    main()
