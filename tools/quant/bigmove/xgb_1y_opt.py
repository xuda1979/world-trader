"""Portfolio optimization for the 1y-target XGB strategy.

Takes the champion 12m-ahead predictions (gkx_preds_xgb_1y_pit.parquet,
depth-3) and optimizes the PORTFOLIO layer instead of equal weights:
  - weight schemes: EW / rank-linear / z-proportional / inverse-vol
  - net-long tilts: long 1+t, short 1-t for t in {0, .25, .5, .75, 1}
    (t=1 = long-only top decile) — NOT forced market-neutral
  - rebalance frequency: monthly (book ret_next) vs quarterly (book
    ret_fwd3 once per non-overlapping cohort)
Correct booking throughout (return horizon == rebalance period), 24bp/mo
full-cycle cost on gross exposure, px>=2 + optional $20M ADV floor.
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import union_panel

OUT = os.path.join(HERE, "..", "reports", "xgb_horizons")
COST = 0.0006
FRAC = 0.1


def load():
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    df["month"] = pd.to_datetime(df["month"])
    for col in ("px_m", "ret_fwd3"):
        if col in df.columns:
            df = df.drop(columns=[col])
    mclose = union_panel.load_union()["close"].resample("ME").last()
    px = mclose.stack().rename("px_m")
    px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")
    fwd3 = (mclose.shift(-3) / mclose - 1.0).stack().rename("ret_fwd3")
    fwd3.index.names = ["month", "ticker"]
    df = df.join(fwd3, on=["month", "ticker"], how="left")
    return df


def leg_weights(g, scheme):
    """Weights for one leg (a pred-sorted frame slice), sum->1."""
    n = len(g)
    if scheme == "EW":
        return pd.Series(1.0 / n, index=g.index)
    if scheme == "rank":
        w = np.arange(n, 0, -1).astype(float)
        return pd.Series(w / w.sum(), index=g.index)
    if scheme == "z":
        z = (g["pred"] - g["pred"].mean()) / (g["pred"].std() + 1e-12)
        w = np.clip(z.to_numpy(), 0, None) + 1e-3
        return pd.Series(w / w.sum(), index=g.index)
    if scheme == "ivol":
        v = g["vol_m3"].replace(0, np.nan).fillna(g["vol_m3"].median())
        w = 1.0 / v
        return pd.Series(w / w.sum(), index=g.index)
    raise ValueError(scheme)


def book_return(g, lab, scheme, tilt, cost=COST):
    """Return of one rebalance period: (1+t)*L - (1-t)*S - cost."""
    g = g.sort_values("pred", ascending=False)
    nq = max(int(len(g) * FRAC), 5)
    longs = g.iloc[:nq]; shorts = g.iloc[-nq:]
    wl = leg_weights(longs, scheme); ws = leg_weights(shorts, scheme)
    rl = (longs[lab] * wl).sum(); rs = (shorts[lab] * ws).sum()
    return (1 + tilt) * rl - (1 - tilt) * rs - 4 * cost


def run_monthly(df, scheme, tilt, min_price=2.0, min_adv=None):
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["pred", "ret_next"])
        g = g[(g["ret_next"] >= -0.95) & (g["ret_next"] <= 2.5)]
        if min_price is not None:
            g = g[g["px_m"] >= min_price]
        if min_adv is not None:
            g = g[g["dollar_vol"] >= min_adv]
        if len(g) < 40: continue
        rows.append((m, book_return(g, "ret_next", scheme, tilt)))
    return pd.Series(dict(rows)).sort_index()


def run_quarterly(df, scheme, tilt, min_price=2.0, min_adv=None):
    rows = []
    for m, g in df.groupby("month"):
        if m.month not in (2, 5, 8, 11) or m.year < 2009 or m.year > 2025: continue
        g = g.dropna(subset=["pred", "ret_fwd3"])
        g = g[(g["ret_fwd3"] >= -0.95) & (g["ret_fwd3"] <= 2.5)]
        if min_price is not None:
            g = g[g["px_m"] >= min_price]
        if min_adv is not None:
            g = g[g["dollar_vol"] >= min_adv]
        if len(g) < 40: continue
        rows.append((m, book_return(g, "ret_fwd3", scheme, tilt)))
    s = pd.Series(dict(rows)).sort_index()
    return s


def stats(s, obs_per_yr=12):
    s = s.dropna()
    if len(s) < 12 or s.std() == 0: return None
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(obs_per_yr)), 2),
            "ann": round(float((1 + s).prod() ** (obs_per_yr / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4),
            "win": round(float((s > 0).mean()), 3)}


def main():
    df = load()
    print("=== MONTHLY rebalance (px>=2), by scheme x tilt ===")
    print(f"{'scheme':8s} | " + " | ".join(f"t={t}" for t in [0, .25, .5, .75, 1.0]))
    for scheme in ["EW", "rank", "z", "ivol"]:
        cells = []
        for tilt in [0, .25, .5, .75, 1.0]:
            s = run_monthly(df, scheme, tilt)
            st = stats(s)
            cells.append(f"{st['sr']:>5.2f}" if st else "   —")
        print(f"{scheme:8s} | " + " | ".join(cells))
    print("\n=== QUARTERLY rebalance (px>=2), by scheme x tilt (SR annualized) ===")
    for scheme in ["EW", "rank", "z", "ivol"]:
        cells = []
        for tilt in [0, .25, .5, .75, 1.0]:
            s = run_quarterly(df, scheme, tilt)
            st = stats(s, obs_per_yr=4)
            cells.append(f"{st['sr']:>5.2f}" if st else "   —")
        print(f"{scheme:8s} | " + " | ".join(cells))
    print("\n=== best configs, full detail ===")
    best = []
    for freq, runner, opy in [("monthly", run_monthly, 12), ("quarterly", run_quarterly, 4)]:
        for scheme in ["EW", "rank", "z", "ivol"]:
            for tilt in [0, .25, .5, .75, 1.0]:
                s = runner(df, scheme, tilt)
                st = stats(s, obs_per_yr=opy)
                if st:
                    best.append((st["sr"], freq, scheme, tilt, st))
    best.sort(reverse=True)
    for sr, freq, scheme, tilt, st in best[:6]:
        print(f"  {freq:9s} {scheme:5s} t={tilt:.2f}: SR {sr}  ann {st['ann']:+.1%}  dd {st['dd']:+.1%}  win {st['win']}")
    print("\n=== capacity check: best neutral + best tilted, $20M ADV ===")
    for freq, scheme, tilt in [("monthly", "rank", 0), ("monthly", "rank", .5),
                               ("quarterly", "rank", .5)]:
        s = runner(df, scheme, tilt, min_adv=20e6)
        st = stats(s, obs_per_yr=12 if freq == "monthly" else 4)
        print(f"  {freq} {scheme} t={tilt} @ $20M ADV: {st}")


if __name__ == "__main__":
    main()
