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


def load_positioning(asof):
    """Equity-index spec positioning lens (informational only).

    TFF leveraged-fund z (2017+) with legacy non-commercial z (pre-2017)
    fallback — 1993+ continuous. Historically (1993-2016): spec z < -1.5
    (capitulation short) preceded +5.2% fwd-13w SPY vs +0.9% baseline
    (n=122) — the contrarian tail; post-2017 the same extreme was
    momentum-flavored (+0.3%..-0.6%), so the lens reports the value and
    leaves interpretation to the operator. NOT a stance input.
    """
    cot = Path(__file__).resolve().parent / "data_cot"
    z_parts = []
    tff = cot / "tff_tidy.csv"
    if tff.exists():
        tdf = pd.read_csv(tff, parse_dates=["report_date"])
        core = tdf[tdf["contract_code"].isin(["13874+", "20974+", "239742"])]
        g = core.groupby("report_date").agg(
            l=("lev_fund_long", "sum"), s=("lev_fund_short", "sum"), oi=("oi", "sum"))
        g["pct"] = (g["l"] - g["s"]) / g["oi"]
        g["z"] = ((g["pct"] - g["pct"].rolling(104, min_periods=52).mean())
                  / g["pct"].rolling(104, min_periods=52).std())
        z_parts.append(g["z"])
    leg = cot / "legacy_tidy.csv"
    if leg.exists():
        ldf = pd.read_csv(leg, parse_dates=["report_date"])
        sp = ldf[ldf["contract_code"].isin(["138741", "13874A"])]
        g = sp.groupby("report_date").agg(
            l=("noncomm_long", "sum"), s=("noncomm_short", "sum"), oi=("oi", "sum"))
        g["pct"] = (g["l"] - g["s"]) / g["oi"]
        g["z"] = ((g["pct"] - g["pct"].rolling(104, min_periods=52).mean())
                  / g["pct"].rolling(104, min_periods=52).std())
        z_parts.append(g["z"])
    if not z_parts:
        return {}
    z = pd.concat(z_parts).sort_index()
    z = z[~z.index.duplicated(keep="last")]
    # latest value at or before asof (data is weekly, asof is daily)
    avail = z[z.index <= pd.Timestamp(asof)]
    if avail.empty:
        return {}
    cur = float(avail.iloc[-1])
    return {
        "equity_spec_z": round(cur, 2),
        "asof": str(avail.index[-1].date()),
        "extreme_short": cur < -1.5,
        "extreme_long": cur > 1.5,
        "historical_note": "1993-2016: z<-1.5 preceded +5.2% fwd-13w SPY vs +0.9% "
                           "baseline (capitulation contrarian); post-2017 extremes "
                           "were momentum-flavored — interpret in context. Episode "
                           "reference (legacy noncomm net % of OI): 1987 crash — specs "
                           "~flat pre-crash, -6.3% after (exogenous, no capitulation "
                           "setup); 1990-10 and 1994-07 bottoms — extreme -20% "
                           "capitulation shorts; 1998/2002 — moderate shorts. Same "
                           "asymmetry replicates in WTI (2001-2016): z<-1.5 -> fwd13w "
                           "+4.9% vs +2.1% at z>1.5 — extreme short = capitulation "
                           "buy across markets, era-dependent.",
    }


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

    asof_str = str(f.index[-1].date())
    positioning = load_positioning(asof_str)
    # slow-decay lens (informational): 5y rolling MONTHLY Sharpe — the
    # rolling-window decay found 2026-08-13 (min 5y SR +0.31 in the most
    # recent window, driven by the 2022-23 soft patch) is otherwise invisible
    # to the daily-based stance logic.
    fm = f.resample("MS").agg(lambda s: (1 + s).prod() - 1)
    fivey = fm.iloc[-60:]
    slow_sr = (fivey.mean() * 12 - 0.02) / (fivey.std() * np.sqrt(12)) \
        if len(fivey) >= 24 else float("nan")

    stats = {
        "asof": asof_str,
        "last_252d_rolling_sharpe": round(cur_rs, 3),
        "last_63d_drawdown_vs_1y_high_pct": round(cur_dd63 * 100, 2),
        "persistent_neg_sharpe_21d": bool(consecutive_neg_sharpe),
        "short_term_stress_dd": bool(stress_short),
        "stance": stance,
        "rolling_5y_monthly_sharpe": round(slow_sr, 3),
        "flagship_full_stats": {
            "sharpe": round(f.mean() / f.std() * np.sqrt(252), 3),
            "cagr_pct": round(((1 + f).prod() ** (252 / len(f)) - 1) * 100, 2),
            "maxdd_pct": round(((1 + f).cumprod() / (1 + f).cumprod().cummax() - 1).min() * 100, 2),
            "n_days": int(len(f)),
        },
        "note": "TRIM = sustained regime degradation (rs<0 for 21d AND -3% qtr dd); "
                "this is the pull-the-lever event. CAUTION = one-off tail (likely a "
                "fast blip that recovers). GO = normal all-weather operation.",
        "positioning": positioning,
    }

    # append to history (dedupe: same asof + stance + key numbers -> update
    # the latest row instead of stacking identical rows from intraday fires)
    if HIST.exists():
        try:
            hist = json.load(open(HIST))
        except Exception:
            hist = []
    else:
        hist = []
    if hist and hist[-1].get("asof") == stats["asof"] \
            and hist[-1].get("stance") == stance \
            and hist[-1].get("last_252d_rolling_sharpe") == stats["last_252d_rolling_sharpe"] \
            and hist[-1].get("rolling_5y_monthly_sharpe") == stats["rolling_5y_monthly_sharpe"]:
        hist[-1] = stats  # refresh timestamp/positioning, keep one row per state
    else:
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
    print(f"  rolling 5y monthly Sharpe ... {stats['rolling_5y_monthly_sharpe']:+.2f}  (slow-decay lens)")
    print(f"  flagship full-window ........ SR {stats['flagship_full_stats']['sharpe']:.2f}, "
          f"CAGR {stats['flagship_full_stats']['cagr_pct']:.1f}%, "
          f"MaxDD {stats['flagship_full_stats']['maxdd_pct']:.1f}%")
    if stats.get("positioning"):
        pos = stats["positioning"]
        flag = " (EXTREME)" if (pos.get("extreme_short") or pos.get("extreme_long")) else ""
        print(f"  equity spec positioning z ... {pos['equity_spec_z']:+.2f}{flag}"
              f"  [asof {pos['asof']}, informational only]")
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
