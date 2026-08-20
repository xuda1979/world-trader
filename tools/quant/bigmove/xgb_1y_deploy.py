"""Deployment-style portfolio backtest for the 1y-target PIT XGB signal.

The annual-cohort stats (iter1-3) measure each cohort in isolation. This
backtest simulates actually RUNNING the strategy: every quarter (Feb/May/
Aug/Nov) a fresh decile L/S cohort is formed from the latest predictions
(book fixed at formation, 12m hold), capital split equally across the 4
simultaneous cohorts. Monthly portfolio P&L = mean of active cohorts'
monthly return slices (ret_next), net of 24bp full-cycle cost at formation
and at exit. No reconstitution mid-hold; names missing a monthly slice
(delistings) drop out of that slice's average.

Also reports the portfolio's beta to SPY (is the L/S actually neutral?).
Reuses gkx_preds_xgb_1y_pit.parquet — no retraining.
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import union_panel

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(HERE, "..", "reports", "xgb_horizons")
COST = 0.0006
ENTRY_MONTHS = [2, 5, 8, 11]
FIRST_ENTRY = (2009, 2)
LAST_ENTRY = (2025, 8)   # needs 12m of ret_next slices (data through 2026-08)
MIN_PRICE = 2.0          # point-in-time investable floor at formation


def load():
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    df["month"] = pd.to_datetime(df["month"])
    px = union_panel.load_union()["close"].resample("ME").last().stack().rename("px_m")
    px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")
    return df


def form_cohort(df, m):
    """Fixed book: top/bottom decile names at month m (pred + px floor)."""
    g = df[df["month"] == m].dropna(subset=["pred"])
    g = g[g["px_m"] >= MIN_PRICE]
    g = g.sort_values("pred", ascending=False)
    n = len(g)
    if n < 40:
        return None
    nq = max(int(n * 0.1), 5)
    return {"entry": m, "longs": list(g["ticker"].iloc[:nq]),
            "shorts": list(g["ticker"].iloc[-nq:])}


def cohort_slices(df, book):
    """Monthly net P&L slices over the 12m hold, fixed membership.

    Book formed at close(m0): the hold window (close m0 -> close m0+12) is
    exactly ret_next(m0)..ret_next(m0+11) -> slices k = 0..11. Month-ends
    are preserved via MonthEnd normalization (DateOffset alone maps Feb-28
    to Mar-28, missing the panel rows)."""
    m0 = book["entry"]
    out = {}
    for k in range(0, 12):
        m = m0 + pd.DateOffset(months=k) + pd.offsets.MonthEnd(0)
        g = df[df["month"] == m]
        lr = g[g["ticker"].isin(book["longs"])]["ret_next"].dropna()
        sr = g[g["ticker"].isin(book["shorts"])]["ret_next"].dropna()
        if len(lr) < 5 or len(sr) < 5:   # cohort effectively dead
            continue
        pnl = lr.mean() - sr.mean()
        if k == 0:    pnl -= 4 * COST    # formation full cycle
        if k == 11:   pnl -= 4 * COST    # exit full cycle
        out[m] = pnl
    return out


def stats(s):
    s = s.dropna()
    if len(s) < 12 or s.std() == 0: return None
    eq = (1 + s).cumprod()
    sr = s.mean() / s.std() * np.sqrt(12)
    ann = (1 + s).prod() ** (12 / len(s)) - 1
    dd = (eq / eq.cummax() - 1).min()
    return {"sr": round(float(sr), 2), "ann": round(float(ann), 4),
            "dd": round(float(dd), 4), "n": int(len(s)),
            "win": round(float((s > 0).mean()), 3)}


def main():
    df = load()
    entries = pd.date_range(pd.Timestamp(*FIRST_ENTRY, 28),
                            pd.Timestamp(*LAST_ENTRY, 31), freq="ME")
    entries = [m for m in entries if m.month in ENTRY_MONTHS]
    books = [b for b in (form_cohort(df, m) for m in entries) if b]
    print(f"{len(books)}/{len(entries)} cohorts formed ({books[0]['entry'].date()}..{books[-1]['entry'].date()})")

    def slice_portfolio(bs):
        port = {}
        for b in bs:
            for m, pnl in cohort_slices(df, b).items():
                port.setdefault(m, []).append(pnl)
        return pd.Series({m: np.mean(v) for m, v in sorted(port.items())})

    port = slice_portfolio(books)
    print(f"\n=== STAGGERED PORTFOLIO (quarterly entry, 12m hold, {len(books)} cohorts) ===")
    print(f"  monthly: {stats(port)}")
    py = port.groupby(port.index.year).apply(lambda s: (1 + s).prod() - 1)
    print("  by year:", {int(k): round(float(v), 3) for k, v in py.items()})

    # cross-check: Feb-only entries via slices vs fwd12 booking (should agree)
    feb = slice_portfolio([b for b in books if b["entry"].month == 2])
    print(f"  Feb-only slice book: {stats(feb)}")

    # beta to SPY
    spy = pd.read_csv(f"{ROOT}/tools/quant/data/twelve_big/SPY.csv",
                      parse_dates=["date"]).set_index("date")["close"]
    sm = spy.resample("ME").last().pct_change().reindex(port.index)
    both = pd.concat([port.rename("ls"), sm.rename("mkt")], axis=1).dropna()
    beta = np.cov(both["ls"], both["mkt"])[0, 1] / np.var(both["mkt"])
    corr = np.corrcoef(both["ls"], both["mkt"])[0, 1]
    print(f"\n=== MARKET EXPOSURE ({len(both)} months) ===")
    print(f"  beta {beta:.2f}  corr {corr:.2f}  ls ann {stats(both['ls'])['ann']:+.1%} "
          f" mkt ann {(1+sm).prod()**(12/len(both))-1:+.1%}")
    port.to_frame("ls_net").to_csv(os.path.join(OUT, "gkx_1y_deploy_monthly.csv"))
    print("saved gkx_1y_deploy_monthly.csv")


if __name__ == "__main__":
    main()
