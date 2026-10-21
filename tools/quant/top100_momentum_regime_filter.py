"""VIX / macro regime filter for the monthly top-100 momentum book.

User ask: the top momentum strategy works well sometimes, not always —
use VIX (or a macro stress index) to filter the drawdown/underperformance
periods.

Filter families (all no-lookahead: index value lagged 1 trading day):
  vix_abs     VIX >= T                            -> exposure f (else 1)
  vix_pct     VIX >= rolling-252d percentile q    -> exposure f
  credit_pct  BAA-AAA spread >= rolling-252d pct q -> exposure f
  curve_inv   10y-2y < 0 (inverted curve)         -> exposure f
Sweeps thresholds (T, q) and de-risk factors (f). Baseline (no filter) is
computed in the same panel load for apples-to-apples comparison. One-side
toggle cost is charged on the traded fraction whenever exposure changes.

Output: tools/quant/reports/top100_momentum_regime_filter.json
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monthly_top100_momentum import (
    TRADING_DAYS, COST_ONE_SIDE, prepare, walk_forward, stats)

ROOT = "/Users/daxu/software/world-trader"
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats/data_fred")
OUTDIR = os.path.join(ROOT, "tools/quant/reports")


def load_fred(name):
    df = pd.read_csv(os.path.join(FRED, name), parse_dates=["date"])
    return df.set_index("date")["value"].sort_index()


def exposure_abs(series, idx, T, f):
    """1 while index < T, f once index >= T (series lagged 1d inside)."""
    s = series.shift(1).reindex(idx).ffill()
    return (s < T).astype(float) * (1.0 - f) + f


def exposure_pct(series, idx, q, f, window=252):
    """1 while index below its trailing-window percentile q, f at/above it."""
    s = series.shift(1).reindex(idx).ffill()
    r = s.rolling(window, min_periods=window).rank(pct=True).fillna(0.0)
    return (r < q).astype(float) * (1.0 - f) + f


def exposure_below(series, idx, level, f):
    """1 while index >= level, f while index < level (curve inversion gate)."""
    s = series.shift(1).reindex(idx).ffill()
    return (s >= level).astype(float) * (1.0 - f) + f


def yearly(st_ret):
    out = {}
    for y, g in st_ret.groupby(st_ret.index.year):
        eq = (1 + g).cumprod()
        out[y] = {
            "ret": float((1 + g).prod() - 1),
            "mdd": float((eq / eq.cummax() - 1).min()),
        }
    return out


def cum_in_window(r, d0, d1):
    """Compounded return over (d0, d1] — days after peak through trough."""
    r = r[(r.index > d0) & (r.index <= d1)]
    return float((1 + r).prod() - 1) if len(r) else None


def main():
    prices, ret, sharpe, rdates = prepare()
    idx = prices.index
    print(f"Panel: {prices.shape[1]} names, {len(idx)} days "
          f"({idx.min().date()}..{idx.max().date()})")

    # baseline first (shared panel; must reproduce the unfiltered run)
    base_ret, _, _ = walk_forward(prices, ret, sharpe, rdates)
    b_s, b_ann, b_vol, b_dd, b_n = stats(base_ret)
    base_eq = (1 + base_ret).cumprod()
    dd_series = base_eq / base_eq.cummax() - 1
    trough_i = dd_series.idxmin()
    peak_i = base_eq.loc[:trough_i].idxmax()
    print(f"Baseline: SR {b_s:.3f} ann {b_ann:.2%} vol {b_vol:.2%} "
          f"MaxDD {b_dd:.2%} (peak {peak_i.date()} -> trough {trough_i.date()}, n={b_n})")

    spy = pd.read_csv(os.path.join(ROOT, "tools/quant/data/twelve_big", "SPY.csv"),
                      parse_dates=["date"]).set_index("date")["close"]
    spy_r = spy.pct_change().reindex(base_ret.index).dropna()

    vix = load_fred("vix.csv")
    baa = load_fred("baa.csv")
    aaa = load_fred("aaa.csv")
    spread = (baa - aaa).dropna()
    t10y2y = load_fred("t10y2y.csv")

    configs = []
    for T in [20, 22, 25, 28, 32, 35]:
        for f in [0.0, 0.3, 0.5]:
            configs.append((f"vix_abs_{T}_f{f}", exposure_abs(vix, idx, T, f)))
    for q in [0.85, 0.90, 0.95]:
        for f in [0.0, 0.3, 0.5]:
            configs.append((f"vix_pct_{q}_f{f}", exposure_pct(vix, idx, q, f)))
    for q in [0.85, 0.90, 0.95]:
        for f in [0.3, 0.5]:
            configs.append((f"credit_pct_{q}_f{f}", exposure_pct(spread, idx, q, f)))
    for f in [0.3, 0.5]:
        configs.append((f"curve_inv_f{f}", exposure_below(t10y2y, idx, 0.0, f)))

    rows = []
    for name, exp in configs:
        r, toggles, _ = walk_forward(prices, ret, sharpe, rdates, exp)
        s, ann, vol, dd, n = stats(r)
        h = len(r) // 2
        s1, *_ = stats(r.iloc[:h])
        s2, *_ = stats(r.iloc[h:])
        derisk = float((exp.loc[r.index] < 1).mean())
        rows.append({
            "name": name,
            "sharpe": round(s, 3),
            "ann_ret": round(ann, 6),
            "ann_vol": round(vol, 6),
            "maxdd": round(dd, 6),
            "split_half": [round(s1, 3), round(s2, 3)],
            "toggles": toggles,
            "pct_days_derisked": round(derisk, 4),
            "cum_in_baseline_dd_window": cum_in_window(r, peak_i, trough_i),
            "yearly": yearly(r),
        })

    rows.sort(key=lambda x: -x["sharpe"])
    print(f"\n{'config':<24} {'SR':>6} {'ann':>8} {'vol':>7} {'MaxDD':>8} "
          f"{'half':>11} {'DDwin':>8} {'%derisk':>8} {'tgl':>4}")
    for r in rows:
        print(f"{r['name']:<24} {r['sharpe']:6.3f} {r['ann_ret']:8.2%} "
              f"{r['ann_vol']:7.2%} {r['maxdd']:8.2%} "
              f"{r['split_half'][0]:>5.2f}/{r['split_half'][1]:<5.2f} "
              f"{r['cum_in_baseline_dd_window']:8.2%} {r['pct_days_derisked']:8.2%} "
              f"{r['toggles']:4d}")

    out = {
        "baseline": {
            "sharpe": round(b_s, 3),
            "ann_ret": round(b_ann, 6),
            "ann_vol": round(b_vol, 6),
            "maxdd": round(b_dd, 6),
            "period": [str(base_ret.index.min().date()), str(base_ret.index.max().date())],
            "worst_dd_window": [str(peak_i.date()), str(trough_i.date())],
            "worst_dd_window_cum": cum_in_window(base_ret, peak_i, trough_i),
            "yearly": yearly(base_ret),
        },
        "spy_yearly": yearly(spy_r),
        "configs": rows,
    }
    with open(os.path.join(OUTDIR, "top100_momentum_regime_filter.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nsaved -> {OUTDIR}/top100_momentum_regime_filter.json")


if __name__ == "__main__":
    main()
