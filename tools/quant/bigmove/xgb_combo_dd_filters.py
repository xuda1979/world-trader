"""DRAWDOWN-FILTER SWEEP on the champion combo (1y-ex1st w=0.65 + 1m-ens).

User ask: lower the champion drawdown, KEEP average annual return, IMPROVE
Sharpe, using any macro indexes / market data. The combo is the champion
(SR ~1.45, ann ~+24%, dd ~-38%). This tests risk overlays that PARTIALLY
de-risk in stress and fully restore in calm (the only kind that keeps ann).

Macro/regime filters (all month-end, LAGGED 1 month -> no lookahead):
  1. VIX level    : sweep thresholds (full -> f at VIX>t1 -> 0 at VIX>t2)
  2. VIX spike    : VIX > k x trailing-12m median
  3. Market trend : union-index trailing 12m return < 0 OR index below its
                    own 12m MA (built from the full union price panel -> the
                    only market index with full 2009-2026 coverage; SPX.hy
                    OAS too short)
  4. VIX + trend combined
Objective: minimize the (dd cut) while ann-drop <= 2pp and SR >= baseline.
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import union_panel

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")
W1Y = 0.65   # combo weight on the 1y ex1st leg (re-optimized champion)


def load_combo():
    df = pd.read_csv(os.path.join(OUT, "gkx_combo_legs_monthly.csv"),
                     parse_dates=["Unnamed: 0"]).set_index("Unnamed: 0")
    df.index = pd.to_datetime(df.index)
    combo = W1Y * df["y1"] + (1 - W1Y) * df["m1"]
    return combo, df


def monthly_series_from_fred(name):
    df = pd.read_csv(os.path.join(FRED, f"{name}.csv"), parse_dates=["date"])
    return df.set_index("date")["value"].resample("ME").last()


def stats_monthly(s):
    s = s.dropna()
    if len(s) < 24 or s.std() == 0:
        return None
    eq = (1 + s).cumprod()
    sr = s.mean() / s.std() * np.sqrt(12)
    ann = (1 + s).prod() ** (12 / len(s)) - 1
    dd = (eq / eq.cummax() - 1).min()
    return {"sr": round(float(sr), 3), "ann": round(float(ann), 4),
            "dd": round(float(dd), 4),
            "calmar": round(float(ann / abs(dd)), 2) if dd < 0 else None,
            "n": int(len(s))}


def market_trend(idx):
    """Union-index trailing-12m return and below-12m-MA flags, lagged 1m."""
    u = union_panel.load_union()["close"].mean(axis=1).resample("ME").last()
    trend = (u / u.shift(12) - 1.0).shift(1)          # trailing 12m, lagged
    ma = u.rolling(12).mean().shift(1)
    below_ma = (u / ma - 1.0 < 0).astype(float).shift(1)
    ret12 = pd.Series((trend < 0).astype(float), index=trend.index)
    return ret12.reindex(idx).ffill(), below_ma.reindex(idx).ffill()


def apply_gate(combo, gate):
    """gate: monthly exposure series (0..1), same index as combo.
    Scale combo returns by gate, aligned (gate applied to the month it's known
    before)."""
    g = gate.reindex(combo.index).ffill().fillna(1.0)
    return combo * g


def main():
    combo, legs = load_combo()
    combo = combo[combo.index >= "2009-01-01"]
    base = stats_monthly(combo)
    print("=== CHAMPION COMBO BASELINE (w1y=0.65) ===")
    print(f"  SR {base['sr']}  ann {base['ann']:+.1%}  dd {base['dd']:+.1%}  Calmar {base['calmar']}")
    baseline_sr, baseline_ann = base["sr"], base["ann"]

    vix = monthly_series_from_fred("vix")
    dxy = monthly_series_from_fred("dxy")
    curve = monthly_series_from_fred("t10y2y")
    baa = monthly_series_from_fred("baa")
    ret12, below_ma = market_trend(combo.index)
    vix_med = vix.rolling(12, min_periods=6).median()

    results = []
    def try_gate(name, gate, combo):
        s = apply_gate(combo, gate)
        st = stats_monthly(s)
        if not st:
            return
        ann_drop = (baseline_ann - st["ann"]) * 100
        dd_cut = (base["dd"] - st["dd"]) * 100
        sr_delta = st["sr"] - baseline_sr
        results.append((name, st, ann_drop, dd_cut, sr_delta))

    print("\n=== VIX LEVEL gate (f at >t1, 0 at >t2) ===")
    for t1, t2, f in [(22, 35, 0.5), (28, 40, 0.5), (25, 32, 0.5),
                      (25, 35, 0.3), (22, 30, 0.3), (20, 28, 0.5)]:
        ex = pd.Series(np.nan, index=vix.index)
        ex[vix <= t1] = 1.0
        ex[(vix > t1) & (vix <= t2)] = f
        ex[vix > t2] = 0.0
        gate = ex.shift(1)
        s = apply_gate(combo, gate)
        st = stats_monthly(s)
        if st:
            print(f"  VIX>{t1}->{f}, >{t2}->0 : SR {st['sr']}  ann {st['ann']:+.1%}  dd {st['dd']:+.1%}")
            results.append((f"VIXlev {t1}/{t2} f{f}", st,
                            (baseline_ann-st['ann'])*100, (base['dd']-st['dd'])*100, st['sr']-baseline_sr))

    print("\n=== VIX SPIKE gate (VIX > k*12m med) ===")
    for k, f in [(1.2, 0.3), (1.5, 0.5), (1.5, 0.3), (2.0, 0.5), (1.3, 0.4)]:
        spk = (vix > k * vix_med).astype(float)
        gate = (1.0 - (1.0 - f) * spk).shift(1)
        st = stats_monthly(apply_gate(combo, gate))
        if st:
            print(f"  VIX>{k}x med ->{f}       : SR {st['sr']}  ann {st['ann']:+.1%}  dd {st['dd']:+.1%}")
            results.append((f"VIXspk {k}x f{f}", st,
                            (baseline_ann-st['ann'])*100, (base['dd']-st['dd'])*100, st['sr']-baseline_sr))

    print("\n=== MARKET TREND (union index) ===")
    for name, flag, f in [("ret12<0 ->0.5", ret12, 0.5), ("ret12<0 ->0.3", ret12, 0.3),
                          ("below MA ->0.5", below_ma, 0.5), ("below MA ->0.3", below_ma, 0.3)]:
        gate = 1.0 - (1.0 - f) * flag
        st = stats_monthly(apply_gate(combo, gate))
        if st:
            print(f"  {name:24s}: SR {st['sr']}  ann {st['ann']:+.1%}  dd {st['dd']:+.1%}")
            results.append((f"trend {name}", st,
                            (baseline_ann-st['ann'])*100, (base['dd']-st['dd'])*100, st['sr']-baseline_sr))

    print("\n=== VIX + MARKET TREND combined ===")
    vixlev = pd.Series(np.nan, index=vix.index)
    vixlev[vix <= 22] = 1.0; vixlev[(vix > 22) & (vix <= 35)] = 0.5; vixlev[vix > 35] = 0.0
    combos = {
        "VIXlev(22/35)+ret12": vixlev.shift(1) * (1.0 - 0.5 * ret12),
        "VIXspk(1.5)+ret12": (1.0 - 0.5 * (vix > 1.5 * vix_med).astype(float)).shift(1) * (1.0 - 0.5 * ret12),
        "VIXlev+belowMA": vixlev.shift(1) * below_ma.where(below_ma == 年报 if '年' in '' else 1.0, 1.0) if False else None,
    }
    # combined gates
    vixspk = (1.0 - 0.5 * (vix > 1.5 * vix_med).astype(float)).shift(1)
    tr12 = 1.0 - 0.5 * ret12
    combos = {
        "VIXspk(1.5x,0.5) * ret12(0.5)": vixspk * tr12,
        "VIXlev(22/35) * ret12(0.5)": vixlev.shift(1) * tr12,
    }
    for name, gate in combos.items():
        st = stats_monthly(apply_gate(combo, gate))
        if st:
            print(f"  {name:28s}: SR {st['sr']}  ann {st['ann']:+.1%}  dd {st['dd']:+.1%}")
            results.append((name, st,
                            (baseline_ann-st['ann'])*100, (base['dd']-st['dd'])*100, st['sr']-baseline_sr))

    # Rank by objective: maximize SR improvement, keep ann drop <= 2pp, dd must drop
    print("\n=== RANKED (SR delta desc; ann-drop<=2pp & dd-cut>0 required) ===")
    good = [r for r in results if r[2] <= 2.0 and r[3] > 0]
    good.sort(key=lambda r: -r[4])
    for name, st, adrop, ddcut, srd in good[:10]:
        print(f"  {name:28s} SR {st['sr']:+.3f} (Δ{ srd:+.3f})  ann {st['ann']:+.1%} (Δ{ -adrop:+.1f}pp)  "
              f"dd {st['dd']:+.1%} (cut {ddcut:+.1f}pp)")
    if not good:
        print("  NO config meets (ann-drop<=2pp & dd-cut>0).")


if __name__ == "__main__":
    main()
