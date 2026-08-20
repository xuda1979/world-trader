"""Horizon profile + sensitivity for the 1y-target PIT XGB predictions.

No retraining: reuses gkx_preds_xgb_1y_pit.parquet (purged walk-forward OOS
predictions, 47 point-in-time characteristics). Answers:
  1. HORIZON PROFILE: decile L/S realized spreads for hold windows
     3m / 6m / 12m / 24m on the SAME 12m-trained predictions, using
     non-overlapping cohorts (entry months spaced by the window).
  2. SENSITIVITY: 12m annual cohorts under 2x/4x costs, quintile instead of
     decile, and a point-in-time $2 month-end-price floor (tradeable vs
     penny-stock artifact).
  3. LIVE BOOK: top decile at the latest prediction month, restricted to
     names priced >= $2 at that month-end.
Each horizon applies its own sane-tail label filter INSIDE the cohort group
(never destructively on the shared frame — that would silently shrink the
ranking universe of the other horizons).
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import union_panel

OUT = os.path.join(HERE, "..", "reports", "xgb_horizons")
COST = 0.0006
HOLDS = {3: dict(months=[2, 5, 8, 11], obs_per_yr=4, last_entry=2025),
         6: dict(months=[2, 8], obs_per_yr=2, last_entry=2025),
         12: dict(months=[2], obs_per_yr=1, last_entry=2025),
         24: dict(months=[2], obs_per_yr=0.5, last_entry=2024)}


def load():
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    df["month"] = pd.to_datetime(df["month"])
    mclose = union_panel.load_union()["close"].resample("ME").last()
    px = mclose.stack().rename("px_m")
    px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")
    for h in (3, 6, 24):
        fwd = (mclose.shift(-h) / mclose - 1.0).stack().rename(f"ret_fwd{h}")
        fwd.index.names = ["month", "ticker"]
        df = df.join(fwd, on=["month", "ticker"], how="left")
    return df


def spread_series(df, hold_h, frac=0.1, cost=COST, min_price=None):
    cfg = HOLDS[hold_h]
    lab = f"ret_fwd{hold_h}"
    rows = []
    for m, g in df.groupby("month"):
        if m.month not in cfg["months"] or m.year < 2009 or m.year > cfg["last_entry"]:
            continue
        g = g.dropna(subset=["pred", lab])
        # sane tail per group: label in [-0.95, 2.5]
        g = g[(g[lab] >= -0.95) & (g[lab] <= 2.5)]
        if min_price is not None:
            g = g[g["px_m"] >= min_price]   # point-in-time investable floor
        n = len(g)
        if n < 40: continue
        g = g.sort_values("pred", ascending=False)
        nq = max(int(n * frac), 5)
        lg = g[lab].iloc[:nq].mean(); sg = g[lab].iloc[-nq:].mean()
        rows.append((m, lg - sg - 4 * cost))
    return pd.Series(dict(rows)).sort_index()


def stats(s, obs_per_yr):
    s = s.dropna()
    if len(s) < 8 or s.std() == 0: return None
    eq = (1 + s).cumprod()
    sr = s.mean() / s.std() * np.sqrt(obs_per_yr)
    ann = (1 + s).prod() ** (obs_per_yr / len(s)) - 1
    dd = (eq / eq.cummax() - 1).min()
    return {"sr": round(float(sr), 2), "ann": round(float(ann), 4),
            "dd": round(float(dd), 4), "n": int(len(s)),
            "win": round(float((s > 0).mean()), 3)}


def main():
    df = load()
    print("=== HORIZON PROFILE (PIT XGB preds, EW decile L/S, net) ===")
    for h, cfg in HOLDS.items():
        s = spread_series(df, h)
        st = stats(s, cfg["obs_per_yr"])
        print(f"  {h:>2}m-hold: {st}   mean obs {s.mean():+.1%}")
        s.to_frame(f"ls_{h}m").to_csv(os.path.join(OUT, f"gkx_1y_profile_{h}m.csv"))
        if h == 24:
            print("   24m cohorts:", {str(k.date()): round(v, 3) for k, v in s.items()})
    print("\n=== 12m SENSITIVITY (annual cohorts, EW) ===")
    for label, kw in [("decile 24bp", {}), ("decile 48bp", {"cost": 2*COST}),
                      ("decile 96bp", {"cost": 4*COST}),
                      ("quintile 24bp", {"frac": 0.2}),
                      ("decile 24bp PIT-$2", {"min_price": 2.0})]:
        s = spread_series(df, 12, **kw)
        print(f"  {label:18s}: {stats(s, 1.0)}")
    print("\n=== LIVE BOOK (latest pred month, px >= $2) ===")
    dmax = df["month"].max()
    g = df[df["month"] == dmax].dropna(subset=["pred"])
    n_all = len(g)
    g2 = g[g["px_m"] >= 2.0]
    top = g2.sort_values("pred", ascending=False).iloc[:max(int(len(g2)*0.1), 5)]
    bot = g2.sort_values("pred", ascending=False).iloc[-max(int(len(g2)*0.1), 5):]
    book = pd.concat([top.assign(leg="LONG"), bot.assign(leg="SHORT")])[
        ["leg", "ticker", "pred", "ret_m12", "px_m"]].copy()
    print(f"as of {dmax.date()}: {n_all} ranked, {len(g2)} priced >= $2")
    print(book.to_string(index=False))
    book.to_csv(os.path.join(OUT, f"gkx_1y_live_book_{dmax.date()}.csv"), index=False)
    print("saved live book csv")


if __name__ == "__main__":
    main()
