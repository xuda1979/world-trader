"""Robustness suite for the 1m-target XGB/Ridge monthly decile L/S.

Reuses the champion OOS predictions (gkx_preds_xgb.parquet = depth-3 XGB,
gkx_preds_ridge.parquet) — no retraining. Tests on the FULL union universe:
  - cost sensitivity: 24/48/96bp per month
  - quintile vs decile width
  - point-in-time $2 price floor at selection
  - ADV capacity floors ($1M/$5M/$20M) at selection
  - per-year compounded returns
  - horizon decay: annual Feb cohorts booking fwd3/6/12 on the same preds
  - live book: latest month's top/bottom decile (px >= $2)
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import union_panel

OUT = os.path.join(HERE, "..", "reports", "xgb_horizons")
COST = 0.0006


def load(model="xgb"):
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_{model}.parquet")
    df["month"] = pd.to_datetime(df["month"])
    mclose = union_panel.load_union()["close"].resample("ME").last()
    px = mclose.stack().rename("px_m")
    px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")
    for h in (3, 6, 12):
        fwd = (mclose.shift(-h) / mclose - 1.0).stack().rename(f"ret_fwd{h}")
        fwd.index.names = ["month", "ticker"]
        df = df.join(fwd, on=["month", "ticker"], how="left")
    return df


def monthly_ls(df, frac=0.1, cost=COST, min_price=None, min_adv=None):
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["pred", "ret_next"])
        g = g[(g["ret_next"] >= -0.95) & (g["ret_next"] <= 2.5)]
        if min_price is not None:
            g = g[g["px_m"] >= min_price]
        if min_adv is not None:
            g = g[g["dollar_vol"] >= min_adv]
        n = len(g)
        if n < 40: continue
        g = g.sort_values("pred", ascending=False)
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


def annual_ls(df, hold_h, frac=0.1):
    lab = f"ret_fwd{hold_h}"
    cfg = {3: ([2, 5, 8, 11], 4), 6: ([2, 8], 2), 12: ([2], 1)}[hold_h]
    rows = []
    for m, g in df.groupby("month"):
        if m.month not in cfg[0] or m.year < 2009 or m.year > 2025: continue
        g = g.dropna(subset=["pred", lab])
        g = g[(g[lab] >= -0.95) & (g[lab] <= 2.5)]
        n = len(g)
        if n < 40: continue
        g = g.sort_values("pred", ascending=False)
        nq = max(int(n * frac), 5)
        rows.append((m, g[lab].iloc[:nq].mean() - g[lab].iloc[-nq:].mean() - 4 * COST))
    s = pd.Series(dict(rows)).sort_index()
    eq = (1 + s).cumprod()
    sr = s.mean() / s.std() * np.sqrt(cfg[1])
    ann = (1 + s).prod() ** (cfg[1] / len(s)) - 1
    return {"sr": round(float(sr), 2), "ann": round(float(ann), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4), "n": int(len(s))}


def main():
    model = os.environ.get("MODEL", "xgb")
    df = load(model)
    print(f"=== 1m-target {model.upper()}, monthly decile L/S, full universe ===")
    for label, kw in [("decile 24bp", {}), ("decile 48bp", {"cost": 2*COST}),
                      ("decile 96bp", {"cost": 4*COST}),
                      ("quintile 24bp", {"frac": 0.2}),
                      ("decile PIT-$2", {"min_price": 2.0}),
                      ("decile $1M ADV", {"min_adv": 1e6}),
                      ("decile $5M ADV", {"min_adv": 5e6}),
                      ("decile $20M ADV", {"min_adv": 20e6})]:
        s = monthly_ls(df, **kw)
        print(f"  {label:16s}: {stats(s)}")
    s = monthly_ls(df)
    py = s.groupby(s.index.year).apply(lambda x: (1 + x).prod() - 1)
    print("  by year:", {int(k): round(float(v), 3) for k, v in py.items()})
    print("\n=== horizon decay (annual cohorts on 1m preds) ===")
    for h in (3, 6, 12):
        print(f"  {h:>2}m-hold: {annual_ls(df, h)}")
    print("\n=== LIVE BOOK (latest pred month, px >= $2) ===")
    dmax = df["month"].max()
    g = df[df["month"] == dmax].dropna(subset=["pred"])
    g2 = g[g["px_m"] >= 2.0]
    top = g2.sort_values("pred", ascending=False).iloc[:max(int(len(g2)*0.1), 5)]
    bot = g2.sort_values("pred", ascending=False).iloc[-max(int(len(g2)*0.1), 5):]
    book = pd.concat([top.assign(leg="LONG"), bot.assign(leg="SHORT")])[
        ["leg", "ticker", "pred", "ret_m1", "px_m", "dollar_vol"]].copy()
    print(f"as of {dmax.date()}: {len(g)} ranked, {len(g2)} px>=2")
    print(book.to_string(index=False))
    book.to_csv(os.path.join(OUT, f"gkx_1m_live_book_{dmax.date()}.csv"), index=False)
    print("saved live book csv")


if __name__ == "__main__":
    main()
