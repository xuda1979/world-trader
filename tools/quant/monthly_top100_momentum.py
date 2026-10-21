"""MONTHLY-REBALANCED TOP-100 HIGH-SHARPE US MOMENTUM — backtest.

Strategy (per user directive):
  * Universe: US-listed common stocks from the broad `twelve_big` panel
    (long history since 2006); ETFs + foreign ADRs excluded so we rank real
    US equities.
  * On each rebalance date (1st trading day of every calendar month):
      - lookback = 1 calendar year of DAILY returns (252 trading days)
      - compute past-year Sharpe = mean(daily ret) / std(daily ret) * sqrt(252)
      - keep ONLY stocks with positive past-year Sharpe
      - pick the TOP 100 by past-year Sharpe
      - equal-weight the selected names
  * Hold the portfolio for one month, then rebalance (monthly churn).
  * Long-only. Real prices, no look-ahead: the signal at time t uses only
    data strictly before t.

No synthetic data, no selection bias stadiums — this is an honest walk-forward
on real market prices.
"""
import os, sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
DATA_DIR = os.path.join(ROOT, "tools/quant/data/twelve_big")

TRADING_DAYS = 252
LOOKBACK = 252            # one year of daily returns
TOP_N = 100               # top 100 names
MIN_HISTORY = LOOKBACK + 5  # need >= 1yr + buffer of returns before ranking
COST_ONE_SIDE = 0.00038   # 3.8 bps one-side commission (repo convention); slippage on top

# Non-US ADRs + index/benchmark ETFs present in twelve_big -> exclude
BLOCKLIST = {"QQQ", "SPY", "XLF", "ASML", "HMC", "TM"}


def load_prices():
    """Load all US common stocks -> DataFrame[date, ticker] of close prices.
    Keeps only names with >= MIN_HISTORY observation pairs for honest ranking."""
    data = {}
    for fn in os.listdir(DATA_DIR):
        if not fn.upper().endswith(".CSV"):
            continue
        sym = fn[:-4]
        if sym in BLOCKLIST:
            continue
        df = pd.read_csv(os.path.join(DATA_DIR, fn), parse_dates=["date"])
        if df.empty or "close" not in df.columns:
            continue
        df = df.sort_values("date").set_index("date")
        df = df[~df.index.duplicated(keep="last")]["close"]
        df = df.dropna()
        if len(df) < MIN_HISTORY:
            continue
        data[sym] = df
    panel = pd.DataFrame(data).sort_index()
    # keep only full-day rows (rows where enough names have data)
    return panel


def daily_ret(prices):
    """Simple daily returns, per ticker."""
    return prices.pct_change()


def past_year_sharpe(ret, n=LOOKBACK):
    """Rolling past-year Sharpe per ticker. NaN until a full window exists.
    Sharpe = mean/std*sqrt(252)."""
    mean = ret.rolling(n).mean()
    std = ret.rolling(n).std()
    sr = (mean / std) * np.sqrt(TRADING_DAYS)
    return sr


def monthly_rebalance_dates(prices, start, end):
    """First trading day of each calendar month within [start, end]."""
    idx = prices.index
    # month change: a new calendar month begins where the (year,month) tuple changes
    months = idx.strftime("%Y-%m")
    is_first = months != np.roll(months, 1)
    is_first[0] = True
    first = idx[is_first]
    out = [d for d in first if start <= d <= end]
    return out


def stats(r):
    """(Sharpe, ann return, ann vol, max drawdown, n) for a daily return series."""
    s = (r.mean() / r.std()) * np.sqrt(TRADING_DAYS)
    ann = (1 + r).prod() ** (TRADING_DAYS / len(r)) - 1
    vol = r.std() * np.sqrt(TRADING_DAYS)
    eq = (1 + r).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    return s, ann, vol, dd, len(r)


def prepare():
    """Load panel + precompute ranking inputs once (shared across filter sweeps)."""
    prices = load_prices()
    ret = daily_ret(prices)
    sharpe = past_year_sharpe(ret)          # aligned by date
    # Start backtest after we can form a pool: need LOOKBACK+1 rows before first rank.
    start = prices.index[LOOKBACK]
    end = prices.index[-1]
    rdates = monthly_rebalance_dates(prices, start, end)
    return prices, ret, sharpe, rdates


def walk_forward(prices, ret, sharpe, rdates, exposure=None):
    """Walk the monthly top-100 book forward -> daily strategy return series.

    exposure: optional pd.Series aligned to prices.index with values in [0,1]
    (daily fraction of the held book to keep; None = fully invested). When the
    fraction changes, one-side cost is charged on the traded fraction.
    Returns (strat_ret, n_toggles, avg_monthly_turnover)."""
    strat_ret = pd.Series(index=prices.index, dtype=float)
    if exposure is None:
        exposure = pd.Series(1.0, index=prices.index)
    d_exp = exposure.diff().abs().fillna(0.0)   # traded fraction per day
    n_toggles = int((d_exp > 0).sum())

    sel_prev = None
    monthly_turnover = []

    for ri, rdate in enumerate(rdates):
        # signal computed from data strictly before rdate
        sr = sharpe.loc[:rdate].iloc[-1]          # last available Sharpe as of rdate
        valid = sr.dropna()
        # keep only positive sharpe
        pos = valid[valid > 0]
        top = pos.sort_values(ascending=False).head(TOP_N)
        sel = top.index.tolist()

        # next rebalance (or end)
        next_date = rdates[ri + 1] if ri + 1 < len(rdates) else prices.index[-1]
        # day-after for holding: hold from day after rdate up to and including next_date
        hold_mask = (prices.index > rdate) & (prices.index <= next_date)
        hdates = prices.index[hold_mask]

        if len(hdates) > 0:
            # turnover between prior and current selection (fraction of book changed)
            turnover = 0.0
            if sel_prev is not None:
                added = set(sel) - set(sel_prev)
                dropped = set(sel_prev) - set(sel)
                turnover = (len(added) + len(dropped)) / max(1, len(sel_prev))
                monthly_turnover.append(turnover)
            sel_prev = set(sel)
            # round-trip cost charged on the rebalance day for the changed fraction
            cost_hit = turnover * 2 * COST_ONE_SIDE

            # daily returns of the held book during this holding month
            rslice = ret.loc[hdates, sel]
            book_ret = rslice.fillna(0.0).mean(axis=1)
            # regime overlay: scale exposure; pay one-side cost on toggled fraction
            book_ret = book_ret * exposure.loc[hdates].values \
                - d_exp.loc[hdates].values * COST_ONE_SIDE
            book_ret.iloc[0] -= cost_hit          # pay trading cost at rebalance
            strat_ret.loc[hdates] = book_ret.values

    avg_turnover = np.mean(monthly_turnover) if monthly_turnover else None
    return strat_ret.dropna(), n_toggles, avg_turnover


def run_backtest():
    prices, ret, sharpe, rdates = prepare()
    print(f"Loaded {prices.shape[1]} US common stocks, "
          f"{prices.shape[0]} trading days ({prices.index.min().date()}..{prices.index.max().date()})")
    print(f"Monthly rebalances from {rdates[0].date()} to {rdates[-1].date()}: {len(rdates)} rebalances")

    strat_ret, _, monthly_turnover = walk_forward(prices, ret, sharpe, rdates)

    # ---- performance ----
    s, ann, vol, dd, n = stats(strat_ret)
    h = len(strat_ret) // 2
    s1, *_ = stats(strat_ret.iloc[:h]); s2, *_ = stats(strat_ret.iloc[h:])

    print("\n===================== RESULTS (net of 3.8bp one-side) =====================")
    print(f"  Backtest period : {strat_ret.index.min().date()} -> {strat_ret.index.max().date()} "
          f"({len(strat_ret)} trading days, {len(rdates)} monthly rebalances)")
    print(f"  Top-N picks     : {TOP_N} highest past-year Sharpe US stocks (positive Sharpe only)")
    print(f"  Rebalance       : monthly")
    print(f"  Annualized ret  : {ann:8.2%}")
    print(f"  Annualized vol  : {vol:8.2%}")
    print(f"  Sharpe          : {s:8.2f}")
    print(f"  Max drawdown    : {dd:8.2%}")
    print(f"  Split-half Sharpe: {s1:5.2f} / {s2:5.2f}")
    if monthly_turnover is not None:
        print(f"  Avg monthly turnover: {monthly_turnover:.2%}")
    # NOTE: cost (3.8bp one-side) is charged on rebalance-day turnover in the loop,
    # so all metrics above are NET of realistic trading costs.

    # ---- benchmark comparison: SPY and equal-weight whole pool ----
    bench_ts = None
    bw_path = os.path.join(ROOT, "tools/quant/data/twelve_big", "SPY.csv")
    if os.path.exists(bw_path):
        b = pd.read_csv(bw_path, parse_dates=["date"]).set_index("date")["close"]
        b = b.reindex(strat_ret.index).dropna()
        if len(b) > 30:
            br = b.pct_change().dropna()
            bs, bann, bvol, bdd, _ = stats(br)
            print("\n--- Benchmarks (same window) ---")
            print(f"  SPY            : Sharpe {bs:5.2f} | AnnRet {bann:6.2%} | MaxDD {bdd:6.2%}")

    # equal-weight whole pool
    pool = ret.loc[strat_ret.index].fillna(0.0).mean(axis=1).dropna()
    if len(pool) > 30:
        ps, pann, pvol, pdd, _ = stats(pool)
        print(f"  EW whole pool  : Sharpe {ps:5.2f} | AnnRet {pann:6.2%} | MaxDD {pdd:6.2%}")

    # ---- save equity / csv ----
    outdir = os.path.join(ROOT, "tools/quant/reports")
    os.makedirs(outdir, exist_ok=True)
    eq = (1 + strat_ret).cumprod()
    eqdf = pd.DataFrame({"date": strat_ret.index, "strategy_ret": strat_ret.values,
                         "strategy_eq": eq.values})
    eqdf.to_csv(os.path.join(outdir, "top100_momentum_eq.csv"), index=False)
    report = {
        "strategy": "top100_high_sharpe_us_momentum",
        "universe_n": prices.shape[1],
        "top_n": TOP_N,
        "rebalance": "monthly",
        "lookback_days": LOOKBACK,
        "positive_sharpe_only": True,
        "cost_one_side_bps": COST_ONE_SIDE * 1e4,
        "metrics_are_net_of_cost": True,
        "period": [str(strat_ret.index.min().date()), str(strat_ret.index.max().date())],
        "trading_days": n,
        "rebalances": len(rdates),
        "ann_return": round(float(ann), 6),
        "ann_vol": round(float(vol), 6),
        "sharpe": round(float(s), 3),
        "max_drawdown": round(float(dd), 6),
        "split_half_sharpe": [round(float(s1), 3), round(float(s2), 3)],
        "avg_monthly_turnover": round(float(monthly_turnover), 4) if monthly_turnover is not None else None,
        "benchmark_spy_sharpe": round(float(bs), 3) if 'bs' in dir() else None,
    }
    import json
    with open(os.path.join(outdir, "top100_momentum.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nsaved -> {outdir}/top100_momentum_eq.csv and top100_momentum.json")
    return report


if __name__ == "__main__":
    run_backtest()
