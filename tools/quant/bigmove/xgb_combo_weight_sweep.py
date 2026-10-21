"""COMBO WEIGHT SWEEP for the champion stack: 1y quarterly-ex1st book + 1m
ensemble book, on a common MONTHLY basis, sweeps the capital weight on the
1y leg to find the optimal blend.

The current deployed combo weights are 50/50 (defensive, 1.15) and 40/60
(aggressive, 1.21) via ens-1y 40/60. This is a FINER, principled sweep of
that weight on actual return series, aligned monthly (the 1m book is monthly
via ret_next; the 1y ex1st book monthly via staggered 12m-hold cohorts over
quarterly entries). No retraining -- reuses saved OOS predictions.

Reporting: per-weight Sharpe/ann/dd/Calmar + rank correlation of the two legs.
Weights swept coarsely 0..1 then finely around the argmax. Honest note: this
is an in-sample choice of the blend weight (the champion book was already
picked), so treat it as guidance not a fresh backtest claim.
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import union_panel

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
COST = 0.0006
MIN_PRICE = 2.0
ENTRY_MONTHS = [2, 5, 8, 11]


def stats_monthly(s):
    s = s.dropna()
    if len(s) < 12 or s.std() == 0:
        return None
    eq = (1 + s).cumprod()
    sr = s.mean() / s.std() * np.sqrt(12)
    ann = (1 + s).prod() ** (12 / len(s)) - 1
    dd = (eq / eq.cummax() - 1).min()
    return {"sr": round(float(sr), 3), "ann": round(float(ann), 4),
            "dd": round(float(dd), 4),
            "calmar": round(float(ann / abs(dd)), 2) if dd < 0 else None,
            "n": int(len(s)), "win": round(float((s > 0).mean()), 3)}


def load_1y_ex1st_monthly():
    """Quarterly-ex1st EW t=0.25 book, staggered 12m-hold cohorts -> monthly P&L.
    (Matches the champion construction/deploy in xgb_1y_deploy.py.)"""
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    df["month"] = pd.to_datetime(df["month"])
    mclose = union_panel.load_union()["close"].resample("ME").last()
    px = mclose.stack().rename("px_m"); px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")

    def form(m):
        g = df[df["month"] == m].dropna(subset=["pred"])
        g = g[g["px_m"] >= MIN_PRICE]
        g = g.sort_values("pred", ascending=False)
        if len(g) < 40:
            return None
        nq = max(int(len(g) * 0.1), 5)
        return {"entry": m, "longs": list(g["ticker"].iloc[:nq]),
                "shorts": list(g["ticker"].iloc[-nq:])}

    books = []
    for m in df["month"].unique():
        if m.month in ENTRY_MONTHS and 2009 <= m.year <= 2025:
            b = form(m)
            if b:
                books.append(b)
    port = {}
    for b in books:
        m0 = b["entry"]
        for k in range(12):
            m = m0 + pd.DateOffset(months=k) + pd.offsets.MonthEnd(0)
            g = df[df["month"] == m]
            lr = g[g["ticker"].isin(b["longs"])]["ret_next"].dropna()
            sr = g[g["ticker"].isin(b["shorts"])]["ret_next"].dropna()
            if len(lr) < 5 or len(sr) < 5:
                continue
            # champion t=0.25: (1.25)*L - (0.75)*S - cost
            pnl = 1.25 * lr.mean() - 0.75 * sr.mean()
            if k == 0:
                pnl -= 4 * COST
            if k == 11:
                pnl -= 4 * COST
            port.setdefault(m, []).append(pnl)
    return pd.Series({m: np.mean(v) for m, v in sorted(port.items())})


def load_1m_monthly():
    """1m ensemble book: monthly decile L/S (long top-decile, short bottom-
    decile by 'ens' score), booking ret_next, net 24bp/mo. EW."""
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_ens1m.parquet")
    df["month"] = pd.to_datetime(df["month"])
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["ens", "ret_next"])
        n = len(g)
        if n < 40:
            continue
        g = g.sort_values("ens", ascending=False)
        nq = max(int(n * 0.1), 5)
        lg = g["ret_next"].iloc[:nq].mean()
        sg = g["ret_next"].iloc[-nq:].mean()
        rows.append((m, lg - sg - 4 * COST))
    return pd.Series(dict(rows)).sort_index()


def main():
    print("Building 1y ex1st and 1m ensemble monthly books...", flush=True)
    ys = load_1y_ex1st_monthly()
    ms = load_1m_monthly()
    df = pd.concat([ys.rename("y1"), ms.rename("m1")], axis=1).dropna()
    df = df[df.index >= "2009-01-01"]
    print(f"aligned months {len(df)}  ({df.index.min().date()}..{df.index.max().date()})")
    print(f"1y ex1st leg: {stats_monthly(df['y1'])}")
    print(f"1m ens  leg : {stats_monthly(df['m1'])}")
    print(f"leg corr     : {df['y1'].corr(df['m1']):.3f}")

    print("\n=== COMBO WEIGHT SWEEP (w = weight on 1y leg) ===")
    rows = []
    for w in [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]:
        combo = w * df["y1"] + (1 - w) * df["m1"]
        st = stats_monthly(combo)
        rows.append((w, st))
        print(f"  w1y={w:.1f}: SR {st['sr']}  ann {st['ann']:+.1%}  dd {st['dd']:+.1%}  Calmar {st['calmar']}")
    best_w = max(rows, key=lambda r: r[1]["sr"])
    print(f"\nBest coarse w1y = {best_w[0]:.1f} (SR {best_w[1]['sr']})")

    # fine sweep around best
    print("\n=== FINE SWEEP around best ===")
    for dw in [0.05, 0.05, 0.05, 0.05]:
        pass
    center = best_w[0]
    for w in np.arange(max(0.0, center - 0.15), min(1.0, center + 0.16), 0.05):
        combo = w * df["y1"] + (1 - w) * df["m1"]
        st = stats_monthly(combo)
        print(f"  w1y={w:.2f}: SR {st['sr']}  ann {st['ann']:+.1%}  dd {st['dd']:+.1%}  Calmar {st['calmar']}")

    # save
    df.to_csv(os.path.join(OUT, "gkx_combo_legs_monthly.csv"))
    print(f"\nSaved legs -> {OUT}/gkx_combo_legs_monthly.csv")


if __name__ == "__main__":
    main()
