"""Live monitor for the XGB long/short strategies (1y deploy + 1m monthly).

One command -> full live status: price-data freshness, live 1y cohorts
mark-to-market, recent 1m-model monthly L/S realized P&L, next operational
dates (quarterly cohort formations, January refits). No retraining.
"""
from __future__ import annotations
import os, sys, glob, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import union_panel
from xgb_1y_deploy import form_cohort, cohort_slices

ROOT = "/Users/daxu/software/world-trader"
DATA = os.path.join(ROOT, "tools/quant/data")
COST = 0.0006


def data_freshness():
    newest = max((os.path.getmtime(fp) for d in ["twelve_big", "twelve_extend",
                  "twelvedata", "polygon", "polygon_v2", "twelve_liq"]
                  for fp in glob.glob(os.path.join(DATA, d, "*.csv"))), default=0)
    return pd.Timestamp(newest, unit="s")


def live_1y():
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    df["month"] = pd.to_datetime(df["month"])
    px = union_panel.load_union()["close"].resample("ME").last().stack().rename("px_m")
    px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")
    entries = [pd.Timestamp(m) for m in ["2025-11-30", "2026-02-28",
                                         "2026-05-31", "2026-08-31"]]
    print("=== LIVE 1y COHORTS ===")
    for m in entries:
        b = form_cohort(df, m)
        if b is None:
            print(f"  {m.date()}: no book"); continue
        sl = cohort_slices(df, b)
        if not sl:
            print(f"  {m.date()} ({len(b['longs'])}L/{len(b['shorts'])}S): formed, nothing realized")
            continue
        cum = float(np.prod([1 + v for v in sl.values()]) - 1)
        print(f"  {m.date()} ({len(b['longs'])}L/{len(b['shorts'])}S): "
              f"{len(sl)}/12 slices, cum net {cum:+.1%}")


def live_1m():
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb.parquet")
    df["month"] = pd.to_datetime(df["month"])
    print("=== 1m MODEL recent months (monthly decile L/S, net) ===")
    rec = df[df["month"] >= pd.Timestamp("2025-06-30")].copy()
    for m, g in rec.groupby("month"):
        g = g.dropna(subset=["pred", "ret_next"])
        n = len(g)
        if n < 40: continue
        g = g.sort_values("pred", ascending=False)
        nq = max(int(n * 0.1), 5)
        pnl = g["ret_next"].iloc[:nq].mean() - g["ret_next"].iloc[-nq:].mean() - 4 * COST
        print(f"  {m.date()}: {pnl:+.2%} (n={n})")


def live_ens():
    import os.path as _p
    fp = f"{HERE}/data/gkx_preds_ens1m.parquet"
    if not _p.exists(fp):
        return
    df = pd.read_parquet(fp)
    df["month"] = pd.to_datetime(df["month"])
    rec = df[(df["month"] >= pd.Timestamp("2025-06-30")) & df["ens"].notna()]
    print("=== ENSEMBLE (Ridge+XGB) recent months ===")
    for m, g in rec.groupby("month"):
        g = g.dropna(subset=["ens", "ret_next"])
        n = len(g)
        if n < 40: continue
        g = g.sort_values("ens", ascending=False)
        nq = max(int(n * 0.1), 5)
        pnl = g["ret_next"].iloc[:nq].mean() - g["ret_next"].iloc[-nq:].mean() - 4 * COST
        print(f"  {m.date()}: {pnl:+.2%} (n={n})")
    # fresh upcoming book (latest pred month, label not yet realized)
    dmax = df[df["ens"].notna()]["month"].max()
    g = df[(df["month"] == dmax) & df["ens"].notna()].sort_values("ens", ascending=False)
    nq = max(int(len(g) * 0.1), 5)
    print(f"  UPCOMING BOOK {dmax.date()} (UNFILTERED — deploy applies px>=2 + $20M ADV): "
          f"LONG {list(g['ticker'].iloc[:nq])[:10]}")


def live_1y_quarterly():
    """The optimized 1y book (quarterly EW t=0.25, xgb_1y_opt.py): cohorts
    formed Feb/May/Aug/Nov 2026, 3m fixed holds, slices = ret_next."""
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    df["month"] = pd.to_datetime(df["month"])
    print("=== LIVE 1y QUARTERLY (EW t=0.25, optimized book) ===")
    for m0 in [pd.Timestamp("2026-02-28"), pd.Timestamp("2026-05-31"),
               pd.Timestamp("2026-08-31")]:
        g = df[df["month"] == m0].dropna(subset=["pred"])  # form on preds; labels realize later
        if len(g) < 40:
            print(f"  {m0.date()}: no book"); continue
        g = g.sort_values("pred", ascending=False)
        nq = max(int(len(g) * 0.1), 5)
        longs, shorts = set(g["ticker"].iloc[:nq]), set(g["ticker"].iloc[-nq:])
        cum = 1.0; got = 0
        for k in range(0, 3):
            m = m0 + pd.DateOffset(months=k) + pd.offsets.MonthEnd(0)
            gm = df[df["month"] == m]
            lr = gm[gm["ticker"].isin(longs)]["ret_next"].dropna()
            sr_ = gm[gm["ticker"].isin(shorts)]["ret_next"].dropna()
            if len(lr) < 5 or len(sr_) < 5:
                continue
            pnl = 1.25 * lr.mean() - 0.75 * sr_.mean() - (4 * COST if k == 0 else 0)
            cum *= 1 + pnl; got += 1
        print(f"  {m0.date()} ({len(longs)}L/{len(shorts)}S): {got}/3 slices, cum net {cum - 1:+.1%}")


def next_dates():
    today = pd.Timestamp("2026-08-20")
    nxt = [m for m in pd.date_range(today, today + pd.DateOffset(months=8), freq="ME")
           if m.month in (2, 5, 8, 11)][:2]
    refit = pd.Timestamp("2027-01-31")
    print(f"=== NEXT DATES ===\n  formations: {nxt[0].date()}, {nxt[1].date()}"
          f" | next refit: {refit.date()}")


def main():
    fresh = data_freshness()
    print(f"=== DATA ===\n  newest price CSV: {fresh.date()} "
          f"({'STALE >2d' if (pd.Timestamp('2026-08-20') - fresh).days > 2 else 'ok'})")
    live_1y()
    live_1y_quarterly()
    live_1m()
    live_ens()
    next_dates()


if __name__ == "__main__":
    main()
