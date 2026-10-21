"""Novel cross-sectional strategies on the 84-stock universe, 2026-08-05.

Each strategy uses a signal DIFFERENT from the champion's momentum/vol/liquidity
core.  All are cross-sectional (relative ranking), which scramble controls can
falsify by shuffling ticker identities.

Strategies:
  S1: Overnight momentum     — stocks with strong overnight returns outperform
  S2: MAX effect (reverse)   — short high-MAX (lottery) stocks
  S3: 52w-high distance      — long stocks far from 52w high (anchor reversal)
  S4: Idio vol effect        — short high-idio-vol stocks (IVOL anomaly)
  S5: Short-term reversal    — 1-week reversal (anti-momentum)
  S6: Amihud illiquidity     — long illiquid stocks (liquidity premium)

All costs: 3.8bps one-side, T+1 execution, monthly rebalance (21d).
Scramble: shuffle ticker columns -> destroys cross-sectional ranking.

Output: daily returns CSV + metrics + scrambled control for each strategy.
Run: python tools/quant/ls/novel_xs_strategies.py [--scramble SEED]
"""
from __future__ import annotations
import os, sys, argparse
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(ROOT, "tools/quant/data/twelvedata")
COST_BPS = 3.8
REBAL = 21
N_LONG_PCT = 0.10   # top 10% of universe
N_SHORT_PCT = 0.10  # bottom 10%


def load_panel():
    """Load all 90 tickers, filter to stocks with full history."""
    frames = {}
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(DATA_DIR, fn),
                        parse_dates=["date"], usecols=["date", "close", "open", "high", "low", "vol"])
        frames[fn[:-4]] = df.set_index("date").sort_index()
    # Keep only tickers with close and sufficient history
    closes = {}
    opens = {}
    highs = {}
    lows = {}
    vols = {}
    for tkr, df in frames.items():
        if "close" in df.columns and len(df) >= 500:
            closes[tkr] = df["close"]
            if "open" in df.columns:
                opens[tkr] = df["open"]
            if "high" in df.columns:
                highs[tkr] = df["high"]
            if "low" in df.columns:
                lows[tkr] = df["low"]
            if "vol" in df.columns:
                vols[tkr] = df["vol"]

    prices = pd.DataFrame(closes)
    prices.index = pd.to_datetime(prices.index)
    prices = prices.dropna(axis=0, how="all")
    prices = prices.loc[:, prices.count() > 500]  # need decent history

    # Align others to same tickers/dates
    aligned = {"prices": prices}
    for name, data in [("opens", opens), ("highs", highs), ("lows", lows), ("vols", vols)]:
        if data:
            df = pd.DataFrame({k: v for k, v in data.items() if k in prices.columns})
            df.index = pd.to_datetime(df.index)
            df = df.reindex(prices.index)
            aligned[name] = df
    return aligned


def scramble_tickers(data, seed):
    """Scramble by shuffling ticker columns -> destroys cross-sectional ranking."""
    rng = np.random.default_rng(seed)
    for key in ["prices", "opens", "highs", "lows", "vols"]:
        if key in data and data[key] is not None:
            df = data[key].copy()
            cols = list(df.columns)
            rng.shuffle(cols)
            # Reassign with a random lag per column too
            for c in df.columns:
                vals = df[c].values.copy()
                lag = int(rng.integers(5, len(vals) // 4))
                df[c] = np.roll(vals, lag)
            df.iloc[:max(5, int(len(vals) // 4))] = np.nan
            data[key] = df
    return data


# ---- Signal functions ----

def signal_overnight_momentum(data, t):
    """Overnight return momentum: average overnight return over past 60 days."""
    prices = data["prices"]
    opens = data.get("opens")
    if opens is None or t < 120:
        return None
    # Overnight return = open_t / close_{t-1} - 1
    overnight = opens.iloc[1:].values / prices.iloc[:-1].values - 1
    overnight = pd.DataFrame(overnight, index=prices.index[1:], columns=prices.columns)
    # Average overnight return over past 60 days
    avg = overnight.iloc[max(0, t-60):t].mean()
    return avg.dropna()


def signal_max_effect(data, t):
    """MAX effect: max daily return in past month (21 days). Higher -> underperform."""
    prices = data["prices"]
    if t < 60:
        return None
    rets = prices.pct_change().iloc[max(0, t-21):t]
    max_ret = rets.max()
    # Negative: higher MAX -> lower expected return
    return -max_ret.dropna()


def signal_52w_high(data, t):
    """Distance from 52-week high. Farther from high -> higher expected return (anchor reversal)."""
    prices = data["prices"]
    if t < 252:
        return None
    high_52w = prices.iloc[t-252:t].max()
    dist = 1 - prices.iloc[t-1] / high_52w  # 0 = at high, 1 = far from high
    return dist.dropna()


def signal_idio_vol(data, t):
    """Idiosyncratic volatility: residual vol after market regression. Higher IVOL -> underperform."""
    prices = data["prices"]
    if t < 120:
        return None
    rets = prices.pct_change()
    # Use SPY as market proxy
    spy_ret = rets.get("SPY", rets.iloc[:, 0])
    window = rets.iloc[max(0, t-60):t]
    spy_w = spy_ret.iloc[max(0, t-60):t]
    ivols = {}
    for c in window.columns:
        stock_w = window[c].dropna()
        spy_w_aligned = spy_w.loc[stock_w.index].dropna()
        common = stock_w.index.intersection(spy_w_aligned.index)
        if len(common) < 20:
            continue
        # Simple: residual = stock - beta * spy
        cov = np.cov(stock_w.loc[common], spy_w_aligned.loc[common])[0, 1]
        var = np.var(spy_w_aligned.loc[common])
        beta = cov / var if var > 0 else 1.0
        resid = stock_w.loc[common] - beta * spy_w_aligned.loc[common]
        ivols[c] = resid.std()
    result = pd.Series(ivols)
    return -result  # negative: higher IVOL -> lower expected return


def signal_short_reversal(data, t):
    """Short-term reversal: 1-week return. Higher -> lower expected return (reverse)."""
    prices = data["prices"]
    if t < 21:
        return None
    ret_5d = prices.iloc[t-1] / prices.iloc[t-5] - 1
    return -ret_5d.dropna()  # negative: reverse the 1-week return


def signal_amihud(data, t):
    """Amihud illiquidity: avg |return| / dollar_volume. Higher -> higher expected return."""
    prices = data["prices"]
    vols = data.get("vols")
    if vols is None or t < 60:
        return None
    rets = prices.pct_change()
    window_ret = rets.iloc[max(0, t-21):t].abs()
    window_vol = vols.iloc[max(0, t-21):t]
    # Approximate dollar volume = close * volume (no price adjustment needed for ranking)
    dv = prices.iloc[max(0, t-21):t] * window_vol
    with np.errstate(divide="ignore", invalid="ignore"):
        amihud = (window_ret / dv.replace(0, np.nan)).mean()
    return amihud.dropna()


# ---- Backtest harness ----

def backtest(data, signal_fn, signal_name, seed=None):
    """Cross-sectional backtest: long top pct, short bottom pct, equal-weight legs."""
    if seed is not None:
        data = scramble_tickers(data, seed)

    prices = data["prices"]
    dates = prices.index
    tickers = prices.columns
    n_long = max(1, int(len(tickers) * N_LONG_PCT))
    n_short = max(1, int(len(tickers) * N_SHORT_PCT))

    pos = pd.DataFrame(0.0, index=dates, columns=tickers)
    rets = prices.pct_change()

    for t in range(252, len(dates)):
        if (t - 252) % REBAL != 0:
            continue
        sig = signal_fn(data, t)
        if sig is None or len(sig) < n_long + n_short:
            continue
        sig = sig.dropna()
        if len(sig) < n_long + n_short:
            continue
        w = pd.Series(0.0, index=tickers)
        longs = sig.nlargest(n_long).index
        shorts = sig.nsmallest(n_short).index
        w[longs] = 0.5 / n_long
        w[shorts] = -0.5 / n_short
        pos.iloc[t] = w

    pos = pos.shift(1)  # T+1
    daily = (pos * rets).sum(axis=1)
    to = pos.diff().abs().sum(axis=1)
    daily = daily - to * (COST_BPS / 1e4)

    # Vol target 15%
    vol60 = daily.rolling(60).std() * np.sqrt(252)
    scale = np.clip(0.15 / vol60.replace(0, np.nan), 0, 2.0).fillna(0)
    daily = daily * scale.shift(1).fillna(0)

    out = pd.DataFrame({"daily_return": daily}, index=dates)
    return out.iloc[252 + 60:]


def metrics(r):
    r = r.dropna()
    if len(r) < 60 or r.std() == 0:
        return {"sharpe": 0.0, "ann_ret": 0.0, "vol": 0.0, "maxdd": 0.0, "n": len(r)}
    eq = (1 + r).cumprod()
    return {
        "sharpe": round(float(r.mean() / r.std() * np.sqrt(252)), 4),
        "ann_ret": round(float(eq.iloc[-1] ** (252 / len(r)) - 1), 4),
        "vol": round(float(r.std() * np.sqrt(252)), 4),
        "maxdd": round(float((eq / eq.cummax() - 1).min()), 4),
        "n": len(r),
    }


STRATEGIES = {
    "overnight_mom": signal_overnight_momentum,
    "max_effect": signal_max_effect,
    "high52w_dist": signal_52w_high,
    "idio_vol": signal_idio_vol,
    "short_reversal": signal_short_reversal,
    "amihud_illiq": signal_amihud,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scramble", type=int, default=None)
    args = ap.parse_args()

    print("Loading 84-stock panel...")
    data = load_panel()
    tickers = data["prices"].columns
    dates = data["prices"].index
    print(f"Panel: {len(dates)}d x {len(tickers)} stocks "
          f"({dates[0].date()}..{dates[-1].date()})")

    out_dir = os.path.join(ROOT, "tools/quant/ls/results/novel_xs")
    os.makedirs(out_dir, exist_ok=True)

    results = {}
    for name, fn in STRATEGIES.items():
        tag = "real" if args.scramble is None else f"scramble{args.scramble}"
        print(f"\n--- {name} ({tag}) ---")
        r = backtest(data, fn, name, args.scramble)
        m = metrics(r["daily_return"])
        print(f"  {m}")
        fn_out = f"daily_{name}_{tag}.csv"
        r.to_csv(os.path.join(out_dir, fn_out))
        results[name] = m

    if args.scramble is None:
        print("\n=== Summary (real) ===")
        for name, m in results.items():
            print(f"  {name:20s}: sharpe={m['sharpe']:7.4f}  ann_ret={m['ann_ret']:8.4f}  "
                  f"vol={m['vol']:.4f}  maxdd={m['maxdd']:.4f}")
        # Save summary
        pd.DataFrame(results).T.to_csv(os.path.join(out_dir, "summary_real.csv"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
