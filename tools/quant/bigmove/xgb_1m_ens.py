"""Ridge+XGB 1m ensemble: robustness suite + live record + artifacts.

The ensemble (mean of the two models' per-month z-scores) won the 1m
model contest: net SR 0.97, ann +19.9%. This stress-tests it (costs,
quintile, $2 floor, ADV floors), measures its live record, and saves
the combined prediction as a parquet artifact + current live book.
No retraining — joins gkx_preds_{ridge,xgb}.parquet.
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from scipy.stats import zscore
import union_panel

OUT = os.path.join(HERE, "..", "reports", "xgb_horizons")
COST = 0.0006


def load():
    rx = pd.read_parquet(f"{HERE}/data/gkx_preds_ridge.parquet")
    rx["month"] = pd.to_datetime(rx["month"])
    xb = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb.parquet")
    xb["month"] = pd.to_datetime(xb["month"])
    df = xb[["month", "ticker", "pred", "ret_next", "dollar_vol"]].rename(columns={"pred": "pxgb"})
    df = df.merge(rx[["month", "ticker", "pred"]].rename(columns={"pred": "pridge"}),
                  on=["month", "ticker"], how="inner")
    df["zr"] = df.groupby("month")["pridge"].transform(lambda s: zscore(s, nan_policy="omit"))
    df["zx"] = df.groupby("month")["pxgb"].transform(lambda s: zscore(s, nan_policy="omit"))
    W = float(os.environ.get("ENS_W", 0.6))  # weight sweep: 0.6 best
    df["ens"] = W * df["zr"] + (1 - W) * df["zx"]
    mclose = union_panel.load_union()["close"].resample("ME").last()
    px = mclose.stack().rename("px_m")
    px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")
    return df


def monthly_ls(df, frac=0.1, cost=COST, min_price=None, min_adv=None):
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["ens", "ret_next"])
        g = g[(g["ret_next"] >= -0.95) & (g["ret_next"] <= 2.5)]
        if min_price is not None:
            g = g[g["px_m"] >= min_price]
        if min_adv is not None:
            g = g[g["dollar_vol"] >= min_adv]
        n = len(g)
        if n < 40: continue
        g = g.sort_values("ens", ascending=False)
        nq = max(int(n * frac), 5)
        rows.append((m, g["ret_next"].iloc[:nq].mean() - g["ret_next"].iloc[-nq:].mean() - 4 * cost))
    return pd.Series(dict(rows)).sort_index()


def stats(s):
    s = s.dropna()
    if len(s) < 12 or s.std() == 0: return None
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 2),
            "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4),
            "n": int(len(s)), "win": round(float((s > 0).mean()), 3)}


def main():
    df = load()
    print("=== ENSEMBLE (Ridge+XGB 1m), monthly decile L/S, net ===")
    for label, kw in [("decile 24bp", {}), ("decile 48bp", {"cost": 2*COST}),
                      ("decile 96bp", {"cost": 4*COST}),
                      ("quintile 24bp", {"frac": 0.2}),
                      ("decile PIT-$2", {"min_price": 2.0}),
                      ("decile $5M ADV", {"min_adv": 5e6}),
                      ("decile $20M ADV", {"min_adv": 20e6})]:
        s = monthly_ls(df, **kw)
        print(f"  {label:16s}: {stats(s)}")
    s = monthly_ls(df)
    py = s.groupby(s.index.year).apply(lambda x: (1 + x).prod() - 1)
    print("  by year:", {int(k): round(float(v), 3) for k, v in py.items()})
    # live record
    rec = s[s.index >= pd.Timestamp("2025-06-30")]
    print(f"  live (2025-06..): {int((rec > 0).sum())}/{len(rec)} positive, "
          f"compounded {float(np.prod(1 + rec.to_numpy()) - 1):+.0%}")
    # artifacts
    df[["month", "ticker", "ens", "ret_next"]].to_parquet(
        f"{HERE}/data/gkx_preds_ens1m.parquet")
    dmax = df["month"].max()
    g = df[df["month"] == dmax].dropna(subset=["ens"])
    g2 = g[g["px_m"] >= 2.0]
    top = g2.sort_values("ens", ascending=False).iloc[:max(int(len(g2)*0.1), 5)]
    bot = g2.sort_values("ens", ascending=False).iloc[-max(int(len(g2)*0.1), 5):]
    book = pd.concat([top.assign(leg="LONG"), bot.assign(leg="SHORT")])[
        ["leg", "ticker", "ens", "px_m", "dollar_vol"]].copy()
    book.to_csv(os.path.join(OUT, f"gkx_1m_ens_live_book_{dmax.date()}.csv"), index=False)
    print(f"saved gkx_preds_ens1m.parquet + live book (as of {dmax.date()}, "
          f"long {len(top)}: {list(top.ticker[:10])})")


if __name__ == "__main__":
    main()
