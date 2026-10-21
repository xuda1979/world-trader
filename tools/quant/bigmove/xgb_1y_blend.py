"""Dual-horizon XGB blend: 1m-target + 1y-target prediction rank-average.

The desk has two verified OOS signals: the 1m-target XGB (gkx_preds_xgb
.parquet, monthly decile L/S net SR +0.57 after the ret_next fix) and the
1y-target PIT XGB (gkx_preds_xgb_1y_pit.parquet, annual-hold SR ~0.34,
monthly 1m-hold SR +0.29). This blends their per-month cross-sectional
RANKS (z-scored) with weight w on the 1m signal and backtests the monthly
decile L/S (book ret_next, net 24bp/mo) for w in {1.0, 0.7, 0.5, 0.3, 0.0}.

No training: joins existing OOS predictions on (month, ticker).
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from scipy.stats import zscore

COST = 0.0006
OUT = os.path.join(HERE, "..", "reports", "xgb_horizons")


def load_both():
    p1 = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb.parquet")
    p1["month"] = pd.to_datetime(p1["month"])
    p1 = p1[["month", "ticker", "pred"]].rename(columns={"pred": "pred1m"})
    py = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    py["month"] = pd.to_datetime(py["month"])
    py = py[["month", "ticker", "pred", "ret_next"]].rename(columns={"pred": "pred1y"})
    df = py.merge(p1, on=["month", "ticker"], how="inner")
    # per-month cross-sectional z-scores (preds have different scales/horizons)
    df["z1m"] = df.groupby("month")["pred1m"].transform(lambda s: zscore(s, nan_policy="omit"))
    df["z1y"] = df.groupby("month")["pred1y"].transform(lambda s: zscore(s, nan_policy="omit"))
    print(f"joined {len(df):,} rows | months {df.month.min().date()}..{df.month.max().date()} | "
          f"tickers/mo ~{df.groupby('month').size().mean():.0f}", flush=True)
    return df


def decile_ls(df, sig, cost=COST):
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=[sig, "ret_next"])
        n = len(g)
        if n < 40: continue
        g = g.sort_values(sig, ascending=False)
        nq = max(int(n * 0.1), 5)
        lg = g["ret_next"].iloc[:nq].mean(); sg = g["ret_next"].iloc[-nq:].mean()
        rows.append((m, lg - sg - 4 * cost))
    return pd.Series(dict(rows)).sort_index()


def stats(s):
    s = s.dropna()
    if len(s) < 12 or s.std() == 0: return None
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 2),
            "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4),
            "n": int(len(s)),
            "win": round(float((s > 0).mean()), 3)}


def main():
    df = load_both()
    print("\n=== MONTHLY DECILE L/S (EW, net 24bp) ===")
    for w in [1.0, 0.7, 0.5, 0.3, 0.0]:
        sig = f"blend_{w}"
        df[sig] = w * df["z1m"] + (1 - w) * df["z1y"]
        print(f"  w1m={w:.1f} (blend): {stats(decile_ls(df, sig))}")
    print(f"  pure 1m (z1m):  {stats(decile_ls(df, 'z1m'))}")
    print(f"  pure 1y (z1y):  {stats(decile_ls(df, 'z1y'))}")

    # best blend (w=0.5) correlation vs the pure legs
    s_b = decile_ls(df, "blend_0.5"); s_1 = decile_ls(df, "z1m"); s_y = decile_ls(df, "z1y")
    both = pd.concat([s_b.rename("blend"), s_1.rename("m1"), s_y.rename("y1")], axis=1).dropna()
    print(f"\nblend corr vs 1m {both['blend'].corr(both['m1']):.2f}, vs 1y {both['blend'].corr(both['y1']):.2f}")
    both.to_csv(os.path.join(OUT, "gkx_1y_blend_monthly.csv"))
    print("saved gkx_1y_blend_monthly.csv")


if __name__ == "__main__":
    main()
