"""BIMONTHLY-REBALANCED LONG-ONLY OPTIMIZED US MOMENTUM - whole-pool backtest.

Continuation of monthly_top100_momentum.py, per user directive:
  * optimize the WHOLE pool (not just top-100)
  * rebalance every TWO months (bimonthly)
  * LONG-ONLY

On each rebalance (1st trading day of every 2nd calendar month):
  - lookback = 1 calendar year of daily returns (252 td)
  - past-year Sharpe = mean(daily)/std(daily)*sqrt(252); KEEP ALL positive-Sharpe
  - expected-return signal = past-year annualized mean daily return (momentum)
  - covariance = Ledoit-Wolf-style shrunk covariance (stability)
  - LONG-ONLY optimization:  max w'mu - (lam/2) w'Sigma w
        s.t. 0 <= w_i <= cap, sum(w) = 1
  - no leverage, no shorts, full reinvestment.

Costs: 3.8 bp one-side commission charged on rebalance-day turnover.
No look-ahead: signal at t uses data strictly before t.
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = "/Users/daxu/software/world-trader"
DATA_DIR = os.path.join(ROOT, "tools/quant/data/twelve_big")

TRADING_DAYS = 252
LOOKBACK = 252
MIN_HISTORY = LOOKBACK + 5
COST_ONE_SIDE = 0.00038
RISK_AVERSION = 50.0        # lambda in 0.5*lambda*w'Sigma*w (annual basis)
MAX_W_EACH = 0.05           # 5% per-name cap (full book needs >= 20 names)

BLOCKLIST = {"QQQ", "SPY", "XLF", "ASML", "HMC", "TM"}


def load_prices():
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
        df = df[~df.index.duplicated(keep="last")]["close"].dropna()
        if len(df) < MIN_HISTORY:
            continue
        data[sym] = df
    panel = pd.DataFrame(data).sort_index()
    return panel


def shrunk_cov(rets, shrinkage=0.25):
    """Ledoit-Wolf-style constant-correlation shrinkage covariance (daily)."""
    cols = rets.columns
    A = rets.cov().values
    vol = np.sqrt(np.diag(A))
    vol[vol == 0] = 1e-8
    corr = A / np.outer(vol, vol)
    n = corr.shape[0]
    if n > 1:
        mean_corr = (corr.sum() - n) / (n * (n - 1))
    else:
        mean_corr = 0.0
    target = np.outer(vol, vol) * (mean_corr * (1 - np.eye(n)) + np.eye(n))
    shr = (1 - shrinkage) * A + shrinkage * target
    return pd.DataFrame(shr, index=cols, columns=cols)


def optimize_long_only(mu_ann, Sigma, cap=MAX_W_EACH, lam=RISK_AVERSION):
    """Long-only fully-invested mean-variance: max w'mu - 0.5 lam w'Sigma w."""
    n = len(mu_ann)
    if n == 0:
        return pd.Series(dtype=float)
    mu = mu_ann.values.astype(float)
    S = Sigma.values.astype(float)
    S = (S + S.T) / 2
    S += 1e-8 * np.eye(n)
    bounds = [(0.0, cap)] * n
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0,
             "jac": lambda w: np.ones_like(w)}]
    w0 = np.full(n, 1.0 / n)
    w0 = np.clip(w0, 0.0, cap)
    w0 /= w0.sum()
    res = minimize(_obj, w0, args=(mu, S, lam), method="SLSQP",
                   bounds=bounds, constraints=cons,
                   options={"maxiter": 1000, "ftol": 1e-12})
    w = res.x
    w[w < 1e-7] = 0.0
    if w.sum() > 0:
        w = w / w.sum()
    return pd.Series(w, index=mu_ann.index)


def _obj(w, mu, S, lam):
    return -float(w @ mu) + 0.5 * lam * float(w @ S @ w)


def bimonthly_dates(prices, start, end):
    idx = prices.index
    months = idx.strftime("%Y-%m")
    is_first = months != np.roll(months, 1)
    is_first[0] = True
    first = idx[is_first]
    # take every 2nd month: keep the first, then step by 2
    out = []
    keep = True
    for d in first:
        if start <= d <= end:
            if keep:
                out.append(d)
        keep = not keep  # toggle every calendar-month boundary
    return out


def main():
    prices = load_prices()
    print(f"Loaded {prices.shape[1]} US common stocks, "
          f"{prices.shape[0]} trading days ({prices.index.min().date()}..{prices.index.max().date()})")

    ret = prices.pct_change()

    start = prices.index[LOOKBACK]
    end = prices.index[-1]
    rdates = bimonthly_dates(prices, start, end)
    print(f"Bimonthly rebalances: {rdates[0].date()}..{rdates[-1].date()} ({len(rdates)} rebalances)")

    strat_ret = pd.Series(index=prices.index, dtype=float)
    turnover_list = []
    n_names_hist = []
    w_prev = None

    for ri, rdate in enumerate(rdates):
        hist = ret.loc[:rdate]
        sr = hist.iloc[-LOOKBACK:]
        # per-name mean/std/sharpe over the trailing year of DAILY returns
        mean = sr.mean()
        std = sr.std()
        sharpe = (mean / std) * np.sqrt(TRADING_DAYS)
        valid = sharpe.dropna()
        pos = valid[valid > 0]                     # keep ONLY positive-Sharpe names
        pool = pos.index.tolist()

        if len(pool) < 1:
            continue
        mu = mean.reindex(pool) * TRADING_DAYS     # annualized momentum signal
        sub = sr[pool]
        Sig = shrunk_cov(sub)                      # daily covariance of pool
        Sig_ann = Sig * TRADING_DAYS               # annualize
        w = optimize_long_only(mu, Sig_ann)

        # turnover vs previous book (align over union of names)
        if w_prev is not None:
            uni = w.index.union(w_prev.index)
            allw = w.reindex(uni, fill_value=0.0).fillna(0.0).values
            prev = w_prev.reindex(uni, fill_value=0.0).fillna(0.0).values
            turnover = float(np.abs(allw - prev).sum())
            turnover_list.append(turnover)
        w_prev = w.copy()
        n_names_hist.append(int((w > 1e-7).sum()))

        next_date = rdates[ri + 1] if ri + 1 < len(rdates) else prices.index[-1]
        hold = (prices.index > rdate) & (prices.index <= next_date)
        hdates = prices.index[hold]
        if len(hdates) == 0:
            continue
        rslice = ret.loc[hdates, pool].fillna(0.0)
        book = (rslice * w.reindex(pool)).sum(axis=1) / w.reindex(pool).sum()
        cost_hit = turnover_list[-1] * COST_ONE_SIDE if turnover_list else 0.0
        book.iloc[0] -= cost_hit
        strat_ret.loc[hdates] = book.values

    strat_ret = strat_ret.dropna()

    def stats(r):
        s = (r.mean() / r.std()) * np.sqrt(TRADING_DAYS)
        ann = (1 + r).prod() ** (TRADING_DAYS / len(r)) - 1
        vol = r.std() * np.sqrt(TRADING_DAYS)
        eq = (1 + r).cumprod()
        dd = (eq / eq.cummax() - 1).min()
        return s, ann, vol, dd, len(r)

    s, ann, vol, dd, n = stats(strat_ret)
    h = len(strat_ret) // 2
    s1, *_ = stats(strat_ret.iloc[:h]); s2, *_ = stats(strat_ret.iloc[h:])
    avg_turn = np.mean(turnover_list) if turnover_list else 0.0
    avg_names = np.mean(n_names_hist) if n_names_hist else 0

    print("\n===================== RESULTS (net of 3.8bp one-side) =====================")
    print(f"  Period        : {strat_ret.index.min().date()} -> {strat_ret.index.max().date()} "
          f"({len(strat_ret)} td, {len(rdates)} bimonthly rebalances)")
    print(f"  Pool          : ALL positive-Sharpe US names, optimized long-only")
    print(f"  Avg names held: {avg_names:.0f}")
    print(f"  Annualized ret: {ann:8.2%}")
    print(f"  Annualized vol: {vol:8.2%}")
    print(f"  Sharpe        : {s:8.2f}")
    print(f"  Max drawdown  : {dd:8.2%}")
    print(f"  Split-half    : {s1:5.2f} / {s2:5.2f}")
    print(f"  Avg 2-mo turnover: {avg_turn:.2%}  ({avg_turn/2:.2%}/month equiv)")

    # benchmarks
    bw = os.path.join(ROOT, "tools/quant/data/twelve_big", "SPY.csv")
    if os.path.exists(bw):
        b = pd.read_csv(bw, parse_dates=["date"]).set_index("date")["close"]
        b = b.reindex(strat_ret.index).dropna()
        if len(b) > 30:
            br = b.pct_change().dropna()
            bs, bann, bvol, bdd, _ = stats(br)
            print(f"  SPY           : Sharpe {bs:5.2f} | AnnRet {bann:6.2%} | MaxDD {bdd:6.2%}")
    pool_all = ret.loc[strat_ret.index].fillna(0.0).mean(axis=1).dropna()
    if len(pool_all) > 30:
        ps, pann, pvol, pdd, _ = stats(pool_all)
        print(f"  EW whole pool : Sharpe {ps:5.2f} | AnnRet {pann:6.2%} | MaxDD {pdd:6.2%}")

    outdir = os.path.join(ROOT, "tools/quant/reports")
    os.makedirs(outdir, exist_ok=True)
    eq = (1 + strat_ret).cumprod()
    eqdf = pd.DataFrame({"date": strat_ret.index, "strategy_ret": strat_ret.values,
                         "strategy_eq": eq.values})
    eqdf.to_csv(os.path.join(outdir, "bimonthly_opt_pool_eq.csv"), index=False)
    import json
    report = {
        "strategy": "bimonthly_long_only_optimized_whole_pool_momentum",
        "universe_n": prices.shape[1],
        "rebalance_months": 2, "long_only": True, "whole_pool_optimized": True,
        "position_cap": MAX_W_EACH, "risk_aversion": RISK_AVERSION,
        "positive_sharpe_only": True, "cost_one_side_bps": COST_ONE_SIDE * 1e4,
        "period": [str(strat_ret.index.min().date()), str(strat_ret.index.max().date())],
        "trading_days": n, "rebalances": len(rdates),
        "avg_names_held": round(float(avg_names), 1),
        "ann_return": round(float(ann), 6), "ann_vol": round(float(vol), 6),
        "sharpe": round(float(s), 3), "max_drawdown": round(float(dd), 6),
        "split_half_sharpe": [round(float(s1), 3), round(float(s2), 3)],
        "avg_bimonthly_turnover": round(float(avg_turn), 4),
        "benchmark_spy_sharpe": round(float(bs), 3) if 'bs' in dir() else None,
    }
    with open(os.path.join(outdir, "bimonthly_opt_pool.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nsaved -> {outdir}/bimonthly_opt_pool_eq.csv and bimonthly_opt_pool.json")


if __name__ == "__main__":
    main()
