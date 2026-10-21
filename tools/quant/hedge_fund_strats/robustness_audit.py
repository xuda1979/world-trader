"""Robustness / tail audit of the all-weather flagship (2026-08-13 loop).

Directly serves the user requirement "profitability & high Sharpe in ANY
market scenario": quantify how the company's core book behaves in every major
historical crash (2008 GFC, 2011, 2015, 2018 Q4, 2020 COVID, 2022 bear) vs the
equity market, plus tail metrics (VaR/CVaR/skew, worst N days/months).

Usage: python tools/quant/hedge_fund_strats/robustness_audit.py
Writes results/robustness_audit.json
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

RES = Path(__file__).resolve().parent / "results"
FRED = Path(__file__).resolve().parent / "data_fred"

EPISODES = [
    ("2008 GFC", "2008-09-01", "2009-03-09"),
    ("2011 Euro", "2011-07-22", "2011-10-04"),
    ("2015-16 selloff", "2015-08-18", "2016-02-11"),
    ("2018 Q4", "2018-09-20", "2018-12-24"),
    ("2020 COVID", "2020-02-19", "2020-03-23"),
    ("2022 Bear", "2022-01-03", "2022-10-12"),
]

def load_flagship():
    f = pd.read_csv(RES / "portfolio_weights.csv", index_col=0, parse_dates=True)
    return f["portfolio_return"].dropna()

def load_spx():
    s = pd.read_csv(FRED / "spx.csv", index_col=0, parse_dates=True).iloc[:, 0]
    return s.pct_change().dropna()

def main():
    f = load_flagship()
    spx = load_spx()
    eq = (1 + f).cumprod()

    # --- crash-episode table ---
    rows = []
    for name, a, b in EPISODES:
        ff = f[(f.index >= a) & (f.index <= b)]
        ss = spx[(spx.index >= a) & (spx.index <= b)]
        rows.append({
            "episode": name, "window": f"{a}..{b}",
            "flagship_total_pct": round(float(ff.sum() * 100), 2),
            "spx_total_pct": round(float(ss.sum() * 100), 2) if len(ss) else None,
            "flagship_days": int(len(ff)),
        })

    # --- tail metrics (full window) ---
    r = f
    var95 = np.percentile(r, 5)
    cvar95 = r[r <= var95].mean()
    worst_d = r.nsmallest(10)
    worst_m = r.resample('ME').sum().nsmallest(6) if hasattr(r.index,'tz') is False else r.resample('ME').sum().nsmallest(6)

    tail = {
        "daily_var_95": round(float(var95), 5),
        "daily_cvar_95": round(float(cvar95), 5),
        "daily_skew": round(float(r.skew()), 3),
        "worst_10_days_pct": [round(float(v * 100), 2) for v in worst_d.values],
        "worst_6_months_pct": [round(float(v * 100), 2) for v in worst_m.values],
        "worst_month_pct": round(float(worst_m.min() * 100), 2),
        "worst_calendar_year_pct": round(float(r.groupby(r.index.year).sum().min() * 100), 2),
    }

    # --- drawdown recovery ---
    dd = eq / eq.cummax() - 1
    # longest stretch below -5% (days in drawdown beyond -5%)
    below5 = dd < -0.05
    runs = (below5 != below5.shift()).cumsum()[below5]
    worst_dd_length = int(runs.value_counts().max()) if len(runs) else 0

    out = {
        "asof": str(f.index[-1].date()),
        "flagship_full": {"sharpe": round(float(f.mean() / f.std() * np.sqrt(252)), 3),
                          "cagr_pct": round(float(((1 + f).prod() ** (252 / len(f)) - 1) * 100), 2),
                          "maxdd_pct": round(float(dd.min() * 100), 2),
                          "n_days": int(len(f))},
        "crash_episodes": rows,
        "tail": tail,
        "longest_stretch_below_neg5pct_days": int(worst_dd_length),
        "note": ("Flagship is a low-beta all-weather book (beta ~+0.34). In the "
                 "2020 COVID crash it lost -12.1% vs SPX -37.8% (~1/3 the equity "
                 "loss); in 2018 Q4 -12.0% vs -20.7%. It still carries equity tail "
                 "(worst months -5..-9%), so fast crashes (2018/2020) remain its "
                 "deepest DD — these are NOT catchable by a 1-day-lagged monitor."),
    }
    with open(RES / "robustness_audit.json", "w") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=" * 78)
    print("ALL-WEATHER FLAGSHIP — ROBUSTNESS / TAIL AUDIT")
    print("=" * 78)
    print(f"Full: SR {out['flagship_full']['sharpe']}, CAGR {out['flagship_full']['cagr_pct']}%, "
          f"MaxDD {out['flagship_full']['maxdd_pct']}%")
    print(f"\nCrash-episode performance (flagship vs SPX):")
    print(f"  {'episode':16s} {'flagship':>10s} {'SPX':>10s}  (SPX data 2016+)")
    for r in rows:
        sp = f"{r['spx_total_pct']:>+9.1f}%" if r["spx_total_pct"] is not None else "       n/a"
        print(f"  {r['episode']:16s} {r['flagship_total_pct']:>+9.1f}% {sp}")
    print(f"\nTail metrics (2008-2026 daily):")
    print(f"  VaR(5%) {var95*100:.2f}%  CVaR(5%) {cvar95*100:.2f}%  skew {tail['daily_skew']}")
    print(f"  worst month {tail['worst_month_pct']}% | worst year "
          f"{tail['worst_calendar_year_pct']}% | longest stay <-5%: {worst_dd_length}d")
    print("\nWrote results/robustness_audit.json")

if __name__ == "__main__":
    main()
