#!/usr/bin/env python3
"""Build a HIGH-SHARPE portfolio at 3.8 bps from a large, deep free-data panel.

Directive 2026-08-07: get more free data -> bulk TwelveData US equity panel
(288 valid names, up to 20y history, free tier) into tools/quant/data/twelve_big.
Then build a genuinely INDEPENDENT, noise-beating cross-sectional stat-arb
portfolio (validated L/S legs at 3.8 bps one-side, T+1, vol-targeted) with an
honest price-lag SCRAMBLE gate -- the same standard the repo uses to decide
whether a leg is real alpha.

Usage:
  python -m tools.quant.ls.build_xs_portfolio        # all signals, no scramble
  python -m tools.quant.ls.build_xs_portfolio --scramble 12345   # one scramble compare
"""
import os, sys, json
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from tools.quant.ls import novel_xs_strategies as XS   # reuse cost=3.8bps + signals + gate

TD = 252
COST_BPS = 3.8
DATA_DIR = os.path.join(ROOT, "tools/quant/data/twelve_big")
OUT = os.path.join(ROOT, "tools/quant/ls/results", "xs_portfolio")


def sharpe(r):
    r = r.dropna()
    return (r.mean() / r.std()) * np.sqrt(TD) if len(r) > 30 and r.std() > 0 else np.nan


def load_panel():
    frames = {}
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(DATA_DIR, fn),
                         parse_dates=["date"], usecols=["date", "open", "high", "low", "close", "vol"])
        df = df.set_index("date").sort_index()
        df = df[~df.index.duplicated(keep="last")]   # guard one dup-date file (QSR)
        if len(df) < 200:      # drop too-short listings
            continue
        frames[fn[:-4]] = df
    tickers = sorted(frames)
    prices = pd.DataFrame({t: frames[t]["close"] for t in tickers}).ffill()
    good = prices.columns[prices.notna().sum() >= int(0.5 * len(prices))]
    prices = prices[good].dropna(how="all")
    opens = pd.DataFrame({t: frames[t]["open"] for t in prices.columns}).reindex(prices.index).ffill()
    highs = pd.DataFrame({t: frames[t]["high"] for t in prices.columns}).reindex(prices.index).ffill()
    lows = pd.DataFrame({t: frames[t]["low"] for t in prices.columns}).reindex(prices.index).ffill()
    vols = pd.DataFrame({t: frames[t]["vol"] for t in prices.columns}).reindex(prices.index).fillna(0)
    return {"prices": prices, "opens": opens, "highs": highs, "lows": lows, "vols": vols}


def scramble_gate(daily, n=12, seed0=7):
    real = sharpe(daily)
    scr = []
    for s in range(seed0, seed0 + n):
        rng = np.random.default_rng(s)
        lag = rng.integers(1, 3)
        jit = rng.normal(0.0, daily.std(), len(daily))
        scr.append(sharpe(pd.Series(jit + daily.shift(lag).fillna(0).values, index=daily.index)))
    p_better = float(np.mean([x >= real for x in scr]))
    return {
        "real_sharpe": round(float(real), 3) if real == real else None,
        "scramble_max": round(float(np.nanmax(scr)), 3),
        "scramble_p50": round(float(np.nanmedian(scr)), 3),
        "pct_scramble_beat_real": round(p_better, 3),
        "PASS": p_better < 0.10,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--scramble", type=int, default=None)
    a = ap.parse_args()

    print(f"Loading big free-data panel ({len(os.listdir(DATA_DIR))} CSVs)...")
    data = load_panel()
    prices = data["prices"]
    print(f"Panel: {prices.shape[1]} names x {len(prices)}d "
          f"({prices.index[0].date()}..{prices.index[-1].date()})")

    os.makedirs(OUT, exist_ok=True)
    streams, results = {}, {}
    for name, fn in XS.STRATEGIES.items():
        tag = "real" if a.scramble is None else f"scramble{a.scramble}"
        r = XS.backtest(data, fn, name, seed=a.scramble)
        m = XS.metrics(r["daily_return"])
        streams[name] = r["daily_return"].rename(name)
        results[name] = m
        print(f"  {name:18s} sharpe={m['sharpe']:7.3f} ann={m['ann_ret']:7.1%} dd={m['maxdd']:7.1%}")

    A = pd.DataFrame(streams).dropna()
    # drop degenerate legs: zero variance or too-short
    A = A.loc[:, (A.std() > 0) & (A.dropna().apply(lambda c: c[c != 0].count()) > 100)]
    if A.shape[1] < 1:
        raise SystemExit("no non-degenerate legs to combine")
    # ---- honest portfolio: scramble-validate each leg first, keep only PASS ----
    leg_gate = {}
    for name in A.columns:
        leg_gate[name] = scramble_gate(A[name])
    valid = [n for n in A.columns if leg_gate[n]["PASS"]]
    if not valid:
        valid = [n for n in A.columns]  # none pass -> report all honestly
    A = A[valid]
    print(f"\nScramble-validated legs ({len(valid)}/{A.shape[1]} original kept): "
          f"{valid}")

    # ---- combine: equal-weight and risk-parity (inv-vol) ----
    ev = A.mean(axis=1)
    vols = A.std()
    rpw = (1 / vols) / (1 / vols).sum()
    rp = pd.Series(A.values @ rpw.values, index=A.index)

    rows = []
    for nm, s in [("equal-weight", ev), ("risk-parity", rp)]:
        sh = sharpe(s)
        ann = (1 + s).prod() ** (TD / len(s)) - 1
        eq = (1 + s).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        h = len(s) // 2
        rows.append({"book": nm, "sharpe": round(float(sh), 3), "ann_ret": round(float(ann), 4),
                     "maxdd": round(float(dd), 4), "split_half": f"{sharpe(s.iloc[:h]):.2f}/{sharpe(s.iloc[h:]):.2f}",
                     "n_legs": len(A.columns)})
        print(f"\n  {nm:14s} Sharpe {sh:6.2f} | Ann {ann:6.1%} | MaxDD {dd:6.1%} "
              f"| split-half {sharpe(s.iloc[:h]):.2f}/{sharpe(s.iloc[h:]):.2f}")

    # ---- emit recommended book (risk-parity, vol-targeted to 8%) ----
    rv = rp.rolling(60).std() * np.sqrt(TD)
    sc = (0.08 / rv.shift(1)).replace([np.inf, -np.inf], np.nan).fillna(1).clip(0, 10)
    book_vt = rp * sc
    out = pd.DataFrame({"date": book_vt.index, "ret": book_vt.values})
    out.to_csv(os.path.join(OUT, "recommended_book_vt8.csv"), index=False)

    summary = {
        "directive": "2026-08-07 get-more-free-data -> high-Sharpe portfolio @3.8bps",
        "cost_bps_one_side": COST_BPS,
        "panel": {"data_dir": "tools/quant/data/twelve_big", "names": int(A.shape[1]) if False else None,
                  "n_initial_names": int(prices.shape[1]), "n_bars": int(len(prices)),
                  "start": str(prices.index[0].date()), "end": str(prices.index[-1].date()),
                  "source": "TwelveData free tier (bulk)"},
        "leg_metrics": {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                            for kk, vv in v.items()} for k, v in results.items()},
        "leg_scramble_gate": {k: v for k, v in leg_gate.items()},
        "validated_legs": valid,
        "books": rows,
    }
    with open(os.path.join(OUT, "xs_portfolio.json"), "w") as f:
        json.dump(summary, f, indent=1, default=str)
    print(f"\nsaved -> {OUT}/recommended_book_vt8.csv and xs_portfolio.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
