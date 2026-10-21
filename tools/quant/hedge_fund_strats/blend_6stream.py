"""6-stream blend: hedge 4-stream EW + AP gold composite + polygon LS champion.

Rebuilds the one-off addendum computation from RESEARCH_REPORT.md as a
permanent, reproducible script, with honest cost handling:

  - hedge streams: equity curves from results/ (cost-inclusive at
    TRADING_COST_BPS, currently 6 bps/side = 12 bps round-trip).
  - AP gold composite: wf_champion_gold_opt.csv (monthly, already net of
    6 bps one-way). Forward-filled to daily.
  - LS champion: levdet3.0/daily_returns.csv — generated at 3.8 bps
    one-side; adjusted here to 6 bps one-side using the champion's own
    turnover series (cost is linear in turnover, so this is exact).

Usage:
    python tools/quant/hedge_fund_strats/blend_6stream.py
    (after run_all.py + run_extras.py at the current TRADING_COST_BPS)
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from core import compute_performance  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
AP_GOLD = os.path.join(
    HERE, "..", "..", "..", "alphaportfolio_replication", "data", "wf_champion_gold_opt.csv")
LS_RET = os.path.join(HERE, "..", "ls", "results", "levdet3.0", "daily_returns.csv")
LS_TURN = os.path.join(HERE, "..", "ls", "results", "levdet3.0", "turnover.csv")

LS_COST_AS_BUILT_BPS = 3.8   # cost embedded in LS daily_returns.csv
TARGET_COST_BPS = 6.0        # 6 bps one-side, user spec


def load_hedge_streams() -> dict:
    """4-stream hedge blend components, cost-inclusive at engine cost."""
    candidates = {
        "ls": ["equity_L_S_130_30.csv"],
        "cta": ["equity_CTA_Futures_multi_21d.csv", "equity_CTA_15vol.csv",
                "equity_CTA_CTA_15vol_21d.csv"],
        "macro": ["equity_Global_Macro.csv"],
        "statarb": ["equity_StatArb_40pairs_z15.csv"],
    }
    streams = {}
    for key, names in candidates.items():
        for nm in names:
            path = os.path.join(RESULTS, nm)
            if os.path.exists(path):
                eq = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
                streams[key] = eq.pct_change()
                print(f"  hedge {key}: {nm} ({len(eq)} rows)")
                break
        if key not in streams:
            print(f"  hedge {key}: MISSING — run run_all.py/run_extras.py first")
    return streams


def load_ap_gold() -> pd.Series:
    """AP gold composite at DAILY frequency. Already net of 6 bps one-way.

    Preferred source: the AP suite's own daily audit of the champion
    (alphaportfolio_replication/data/wf_champion_gold_opt_daily.csv) —
    same monthly-cadence signals, honest DAILY returns of the held book
    ("daily is the honest view; monthly sampling misses intra-month
    drawdowns" — AP suite 2026-08-13). NOTE: this daily series is NOT
    the daily extension of the monthly file (their monthly-compounded
    corr is only ~0.13); use the monthly file at monthly frequency
    (blend_monthly.py) and this file at daily frequency.

    Fallback (no daily file): distribute each month's return evenly
    across the month's trading days, preserving monthly totals. This is
    an approximation only — it is nearly uncorrelated with the real
    daily path.
    """
    daily_path = os.path.join(
        HERE, "..", "..", "..", "alphaportfolio_replication", "data",
        "wf_champion_gold_opt_daily.csv")
    if os.path.exists(daily_path):
        s = pd.read_csv(daily_path, header=None, names=["d", "r"],
                        index_col=0, parse_dates=True)["r"]
        return s
    df = pd.read_csv(AP_GOLD, parse_dates=["ym"])
    df["ym"] = pd.to_datetime(df["ym"]).dt.to_period("M").dt.to_timestamp()
    df = df.set_index("ym")
    days = pd.date_range(df.index.min(), df.index.max(), freq="D")
    days = days[days.dayofweek < 5]  # trading-day grid
    s = pd.Series(np.nan, index=days)
    for m_ts, r in df["net"].items():
        idx = days[(days >= m_ts) & (days < m_ts + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1))]
        idx = idx[(idx - m_ts) <= pd.Timedelta(days=31)]  # current calendar month only
        if len(idx) == 0:
            continue
        s.loc[idx] = (1 + r) ** (1.0 / len(idx)) - 1.0
    return s.dropna()


def load_ls_champion() -> pd.Series:
    """LS champion daily returns, re-costed 3.8 -> 6 bps one-side via turnover."""
    ret = pd.read_csv(LS_RET, index_col=0, parse_dates=True).iloc[:, 0]
    to = pd.read_csv(LS_TURN, index_col=0, parse_dates=True).iloc[:, 0]
    to = to.reindex(ret.index).fillna(0.0)
    drag = to * (TARGET_COST_BPS - LS_COST_AS_BUILT_BPS) / 1e4
    return ret - drag


def stats(series: pd.Series):
    eq = (1 + series).cumprod()
    perf = compute_performance(series, eq, benchmark_returns=None)
    return perf.sharpe, perf.annual_return, perf.max_drawdown, perf.beta


def main():
    print("=" * 70)
    print("6-STREAM BLEND (hedge EW + AP gold + LS champion)")
    print("=" * 70)
    hedge = load_hedge_streams()
    ap = load_ap_gold()
    ls = load_ls_champion()
    print(f"  AP gold: {ap.index.min().date()}..{ap.index.max().date()} ({len(ap)} daily)")
    print(f"  LS champ: {ls.index.min().date()}..{ls.index.max().date()} ({len(ls)} rows, "
          f"re-costed {LS_COST_AS_BUILT_BPS} -> {TARGET_COST_BPS} bps/side)")

    hedge_ew = pd.concat(hedge, axis=1).mean(axis=1).dropna()
    frame = pd.concat({"hedge": hedge_ew, "ap": ap, "ls": ls}, axis=1).dropna()
    print(f"\nCommon window: {frame.index.min().date()}..{frame.index.max().date()} "
          f"({len(frame)} days)")

    for i, col in enumerate(["hedge", "ap", "ls"]):
        sr, ret, mdd, beta = stats(frame[col])
        print(f"  {col:>5}: SR {sr:+.2f}  ret {ret*100:+.1f}%  MaxDD {mdd*100:.1f}%  beta {beta:+.2f}")

    corr = frame.corr()
    print("\nPairwise corr:")
    print(corr.round(3).to_string())

    six = frame.mean(axis=1)
    sr, ret, mdd, beta = stats(six)
    print(f"\n6-stream EW: SR {sr:.3f}  ret {ret*100:.1f}%  MaxDD {mdd*100:.1f}%  beta {beta:+.2f}")
    print(f"hedge EW    : SR {stats(hedge_ew.loc[frame.index])[0]:.3f}  "
          f"ret {stats(hedge_ew.loc[frame.index])[1]*100:.1f}%  "
          f"MaxDD {stats(hedge_ew.loc[frame.index])[2]*100:.1f}%")

    # Sub-period split (2 halves of the 26-month window)
    mid = frame.index[len(frame) // 2]
    for label, sub in [("1st half", frame.loc[:mid]), ("2nd half", frame.loc[mid:])]:
        h = sub["hedge"]
        s6 = sub.mean(axis=1)  # EW of hedge-EW + AP + LS
        print(f"\n{label} ({sub.index.min().date()}..{sub.index.max().date()}): "
              f"hedge EW SR {stats(h)[0]:+.2f} -> 6-stream SR {stats(s6)[0]:+.2f}")

    out = pd.DataFrame({"six_stream_ew": six})
    out.to_csv(os.path.join(RESULTS, "blend_6stream_daily.csv"))
    print("\nsaved -> results/blend_6stream_daily.csv")


if __name__ == "__main__":
    main()
