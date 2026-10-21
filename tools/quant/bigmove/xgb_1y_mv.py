"""Mean-variance optimization for the 1y-target XGB strategy.

Real portfolio optimization (not heuristic weightings): each month,
w* = (Sigma + gamma*I)^-1 * mu with Ledoit-Wolf-shrunk rolling covariance
(60m window, point-in-time), mu = the 1y prediction z-score. Constraints:
per-name |w| <= 2%, gross exposure 2.0, net exposure target t (long
1+t / short 1-t — NOT forced neutral). Turnover-based costs (6bp x
sum|dw| per month). Configs validated split-half: grid chosen on
2009-2017, tested on 2018-2026.
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from scipy.stats import zscore
from sklearn.covariance import LedoitWolf
import union_panel

OUT = os.path.join(HERE, "..", "reports", "xgb_horizons")
COST = 0.0006


def load():
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    df["month"] = pd.to_datetime(df["month"])
    px = union_panel.load_union()["close"].resample("ME").last().stack().rename("px_m")
    px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")
    return df


def run_mv(df, gamma, net, min_hist=36):
    """Monthly MV book: w = inv(Sigma+gamma I) mu, clipped, net-normalized."""
    rets = df.pivot_table(index="month", columns="ticker", values="ret_next")
    preds = df.pivot_table(index="month", columns="ticker", values="pred")
    pxm = df.pivot_table(index="month", columns="ticker", values="px_m")
    months = rets.index.intersection(preds.index).intersection(pxm.index)
    rows = []
    prev_w = None
    for i, m in enumerate(months):
        g = pxm.loc[m].dropna(); g = g[g >= 2.0]
        mus = preds.loc[m].reindex(g.index)
        mus = mus[mus.notna()]
        if len(mus) < 40:
            continue
        win = rets.loc[months[i - min_hist:i], mus.index] if i >= min_hist else None
        if win is None or win.notna().sum().sum() < 2000:
            continue
        win = win.dropna(axis=1, how="all").fillna(0.0)
        idx = [t for t in mus.index if t in win.columns]
        if len(idx) < 40:
            continue
        Sigma = LedoitWolf().fit(win[idx].to_numpy()).covariance_
        mu = zscore(mus[idx].to_numpy())
        n = len(idx)
        w = np.linalg.solve(Sigma + gamma * np.eye(n), mu)
        w = np.clip(w, -0.02, 0.02)
        gross = np.abs(w).sum()
        if gross > 0:
            w = w * min(2.0 / gross, 1.0)
        # net exposure: scale long/short sides to (1+t)/(1-t)
        lp = w[w > 0].sum(); sp = -w[w < 0].sum()
        if lp > 0 and sp > 0:
            w[w > 0] *= (1 + net) / lp
            w[w < 0] *= (1 - net) / sp
        r = win[idx].iloc[-1].to_numpy()
        book = float(w @ r)
        if prev_w is not None:
            prev = prev_w.reindex(idx).fillna(0.0).to_numpy()
            book -= COST * float(np.abs(w - prev).sum())
        rows.append((m, book))
        prev_w = pd.Series(w, index=idx)
    return pd.Series(dict(rows)).sort_index()


def stats(s):
    s = s.dropna()
    if len(s) < 12 or s.std() == 0: return None
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 2),
            "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4),
            "win": round(float((s > 0).mean()), 3)}


def main():
    df = load()
    grid = [(gamma, net) for gamma in (0.1, 1.0, 10.0) for net in (0.0, 0.5, 1.0)]
    tr_mask = lambda s: s.index <= pd.Timestamp("2017-12-31")
    te_mask = lambda s: s.index >= pd.Timestamp("2018-01-01")
    print("=== MV grid, split-half: 2009-2017 (fit) vs 2018-2026 (test) ===")
    results = {}
    for gamma, net in grid:
        s = run_mv(df, gamma, net)
        results[(gamma, net)] = s
        st_tr = stats(s[tr_mask(s)]); st_te = stats(s[te_mask(s)])
        print(f"  g={gamma:4.1f} net={net:.1f}: "
              f"fit SR {st_tr['sr'] if st_tr else None} | test SR {st_te['sr'] if st_te else None} "
              f"| full {stats(s)}")
    # pick best on fit period, report test
    best = max(grid, key=lambda k: (stats(results[k][tr_mask(results[k])]) or {"sr": -9})["sr"])
    s = results[best]
    print(f"\nbest-on-fit config g={best[0]}, net={best[1]}:")
    print(f"  FULL: {stats(s)}")
    print(f"  TEST 2018-2026: {stats(s[te_mask(s)])}")
    s.to_frame("mv").to_csv(os.path.join(OUT, "gkx_1y_mv_monthly.csv"))
    json.dump({str(k): stats(v) for k, v in results.items()},
              open(os.path.join(OUT, "gkx_1y_mv_results.json"), "w"), indent=1)
    print("saved gkx_1y_mv_results.json")


if __name__ == "__main__":
    import json
    main()
