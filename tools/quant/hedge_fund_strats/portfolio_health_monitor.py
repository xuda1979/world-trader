"""Company-level portfolio HEALTH MONITOR — the correct dynamic-regime layer.

Finding (regime_adaptive_report.py, 2026-08-13 loop): for the validated low-beta
all-weather flagship (h3+AP, 2008-2026), FAST VIX-gating and defensive rotation
both FAIL on data — static allocation is already near regime-optimal (SR 1.04,
positive 17/19 calendar yrs). The RIGHT dynamic lever is a HEALTH MONITOR that
flags SUSTAINED regime degradation (the 2022-23 inflation-shock soft patch is
the only stretch that impaired the book), NOT an exposure gate.

This monitor is the deployable dynamic-adjustment control plane. On each fire it
reports the flagship's live health and an explicit GO / CAUTION / TRIM stance.

Logic (persistence-based, no lookahead, uses only realized daily returns):
  - 252d rolling Sharpe (rs): below 0 => in the adverse tail (10th pctl)
  - 63d rolling drawdown vs last-1y high (short-term stress)
  - STRESS if BOTH: rs < 0 for a PERSISTENT 21 consecutive days (a real regime,
    not a fast blip) AND current 63d drawdown < -3%.
  - CAUTION if rs < 0 OR 63d dd < -3% (one condition, likely short-lived blip).
  - TRIM (STRESS) is the operator's trigger to reduce gross exposure; it fires
    only on persistence so it does NOT repurchase the fast-gating failure of L1.

Outputs consolidated `results/portfolio_health.json` (latest stance + history)
and prints the current card. Exit code 0 = GO, 2 = TRIM, 1 = CAUTION (for
alerting/CI use).

Usage: python tools/quant/hedge_fund_strats/portfolio_health_monitor.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

RES = Path(__file__).resolve().parent / "results"
HIST = RES / "portfolio_health_history.json"

ROLL = 252        # 1y rolling window for Sharpe (calendar ~252 trading days)
PERSIST = 21      # consecutive days below threshold to declare a real regime
DD_LOOK = 63      # 1-quarter for short-term stress drawdown
DD_TRIM = -0.03   # -3% intra-quarter drawdown as the short-term stress bar


def load_flagship():
    f = pd.read_csv(RES / "portfolio_weights.csv", index_col=0, parse_dates=True)
    return f["portfolio_return"].dropna()


def main():
    f = load_flagship()
    rs = (f.rolling(ROLL).mean() / f.rolling(ROLL).std() * np.sqrt(252)).dropna()
    # 63d drawdown vs trailing 1y high
    eq = (1 + f).cumprod()
    year_high = eq.rolling(ROLL).max()
    dd63 = (eq / year_high - 1).reindex(f.index)  # dd vs 1y high, evaluated daily

    # persistence: last PERSIST days must ALL have rs < 0
    rs_below = (rs < 0.0).astype(int)
    consecutive_neg_sharpe = rs_below.rolling(PERSIST).sum().iloc[-1] >= PERSIST \
        if len(rs_below) >= PERSIST else False

    cur_rs = float(rs.iloc[-1]) if len(rs) else 0.0
    cur_dd63 = float(dd63.dropna().iloc[-1]) if dd63.notna().any() else 0.0
    stress_short = cur_dd63 < DD_TRIM

    # stance
    if consecutive_neg_sharpe and stress_short:
        stance = "TRIM"
    elif (cur_rs < 0) or stress_short:
        stance = "CAUTION"
    else:
        stance = "GO"

    stats = {
        "asof": str(f.index[-1].date()),
        "last_252d_rolling_sharpe": round(cur_rs, 3),
        "last_63d_drawdown_vs_1y_high_pct": round(cur_dd63 * 100, 2),
        "persistent_neg_sharpe_21d": bool(consecutive_neg_sharpe),
        "short_term_stress_dd": bool(stress_short),
        "stance": stance,
        "flagship_full_stats": {
            "sharpe": round(f.mean() / f.std() * np.sqrt(252), 3),
            "cagr_pct": round(((1 + f).prod() ** (252 / len(f)) - 1) * 100, 2),
            "maxdd_pct": round(((1 + f).cumprod() / (1 + f).cumprod().cummax() - 1).min() * 100, 2),
            "n_days": int(len(f)),
        },
        "note": "TRIM = sustained regime degradation (rs<0 for 21d AND -3% qtr dd); "
                "this is the pull-the-lever event. CAUTION = one-off tail (likely a "
                "fast blip that recovers). GO = normal all-weather operation.",
    }

    # append to history
    if HIST.exists():
        try:
            hist = json.load(open(HIST))
        except Exception:
            hist = []
    else:
        hist = []
    hist.append(stats)
    HIST.parent.mkdir(parents=True, exist_ok=True)
    with open(HIST, "w") as fh:
        json.dump(hist, fh, indent=2)
    with open(RES / "portfolio_health.json", "w") as fh:
        json.dump(stats, fh, indent=2, default=str)

    print("=" * 66)
    print("COMPANY-LEVEL PORTFOLIO HEALTH MONITOR (all-weather flagship)")
    print("=" * 66)
    print(f"  asof ........................ {stats['asof']}")
    print(f"  stance ...................... {stance}")
    print(f"  last 252d rolling Sharpe .... {cur_rs:+.2f}  (persistent<0 for 21d: {bool(consecutive_neg_sharpe)})")
    print(f"  last 63d drawdown vs 1y hi .. {cur_dd63*100:+.2f}%  (stress bar <-3%: {stress_short})")
    print(f"  flagship full-window ........ SR {stats['flagship_full_stats']['sharpe']:.2f}, "
          f"CAGR {stats['flagship_full_stats']['cagr_pct']:.1f}%, "
          f"MaxDD {stats['flagship_full_stats']['maxdd_pct']:.1f}%")
    print(f"\n  ACTION: {stance.upper()}")
    if stance == "GO":
        print("    No regime degradation detected. Hold full allocation (static = optimal).")
    elif stance == "CAUTION":
        print("    One-off adverse tail (likely a fast blip). Hold; re-check next fire.")
    else:
        print("    SUSTAINED regime degradation (2022-23-style). Trim gross before adding risk.")
    print(f"\n  Wrote portfolio_health.json + history ({len(hist)} checks)")

    import sys
    sys.exit({"GO": 0, "CAUTION": 1, "TRIM": 2}[stance])


if __name__ == "__main__":
    main()
