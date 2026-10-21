"""90-day trend top-100 variant vs the 252d-Sharpe book, + DD overlay.

Ask: "how about 90 day trend top 100" — rank the top 100 names by past-90d
cumulative return instead of past-year Sharpe, same monthly rebalance,
same 285-name universe, same window and costs (isolation = signal change only).
Horizon sweep for context: 63/90/126/252d return + 90d Sharpe. Then the
layered DD overlay (credit0 + SPY200d + VIX32 + vol-target 12%) is applied
to the 90d book.

Output: tools/quant/reports/top100_momentum_horizon.json
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monthly_top100_momentum import prepare, walk_forward, stats, TRADING_DAYS
from top100_momentum_regime_filter import load_fred, exposure_pct
from top100_momentum_dd_overlay import gate_from_bool, overlay

ROOT = "/Users/daxu/software/world-trader"
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats/data_fred")
OUTDIR = os.path.join(ROOT, "tools/quant/reports")


def trend_signal(prices, n):
    """n-day cumulative return per ticker (aligned to prices.index)."""
    return prices / prices.shift(n) - 1.0


def sharpe_signal(ret, n):
    """n-day rolling Sharpe per ticker."""
    mean = ret.rolling(n).mean()
    std = ret.rolling(n).std()
    return mean / std * np.sqrt(TRADING_DAYS)


def main():
    prices, ret, sharpe252, rdates = prepare()  # same universe/window as book

    signals = {
        "t63_ret": trend_signal(prices, 63),
        "t90_ret": trend_signal(prices, 90),
        "t126_ret": trend_signal(prices, 126),
        "t252_ret": trend_signal(prices, 252),
        "t90_sharpe": sharpe_signal(ret, 90),
        "t252_sharpe": sharpe252,   # the current book signal
    }

    books = {}
    print(f"{'signal':<14}{'SR':>6}{'ann':>8}{'vol':>7}{'MaxDD':>8}{'half':>11}")
    for label, sig in signals.items():
        r, _, _ = walk_forward(prices, ret, sig, rdates)
        books[label] = r
        s, ann, vol, dd, n = stats(r)
        h = len(r) // 2
        s1, *_ = stats(r.iloc[:h])
        s2, *_ = stats(r.iloc[h:])
        print(f"{label:<14}{s:>6.3f}{ann:>8.2%}{vol:>7.2%}{dd:>8.2%}"
              f"{s1:>5.2f}/{s2:<5.2f}")

    # ---- layered DD overlay on the 90d book (and t90_sharpe for reference) ----
    vix = load_fred("vix.csv")
    baa = load_fred("baa.csv")
    aaa = load_fred("aaa.csv")
    spread = (baa - aaa).dropna()
    spy = pd.read_csv(os.path.join(ROOT, "tools/quant/data/twelve_big", "SPY.csv"),
                      parse_dates=["date"]).set_index("date")["close"]
    tb = (load_fred("tbill3m.csv") / 100.0 / 252.0)

    print(f"\n{'config':<34}{'SR':>6}{'ann':>8}{'vol':>7}{'MaxDD':>8}{'half':>11}")
    out_configs = []
    for label in ["t90_ret", "t90_sharpe", "t252_sharpe"]:
        book_r = books[label]
        spy_a = spy.reindex(book_r.index).ffill()
        cash_r = tb.reindex(book_r.index).ffill().fillna(0.0)
        gates = [
            exposure_pct(spread, book_r.index, 0.85, 0.0),
            gate_from_bool(spy_a > spy_a.rolling(200).mean(), 0.0, book_r.index),
            gate_from_bool(vix < 32, 0.0, book_r.index),
        ]
        r, exp = overlay(book_r, gates, cash_r, vol_target=0.12)
        s, ann, vol, dd, n = stats(r)
        h = len(r) // 2
        s1, *_ = stats(r.iloc[:h])
        s2, *_ = stats(r.iloc[h:])
        name = f"{label}+overlay"
        print(f"{name:<34}{s:>6.3f}{ann:>8.2%}{vol:>7.2%}{dd:>8.2%}"
              f"{s1:>5.2f}/{s2:<5.2f}")
        out_configs.append({
            "name": name,
            "sharpe": round(s, 3),
            "ann_ret": round(ann, 6),
            "ann_vol": round(vol, 6),
            "maxdd": round(dd, 6),
            "split_half": [round(s1, 3), round(s2, 3)],
            "pct_invested": round(float((exp > 0.99).mean()), 4),
            "yearly": {y: round((1 + g).prod() - 1, 4)
                       for y, g in r.groupby(r.index.year)},
        })

    with open(os.path.join(OUTDIR, "top100_momentum_horizon.json"), "w") as f:
        json.dump({
            "raw_books": {
                label: {
                    "sharpe": round(stats(r)[0], 3),
                    "ann_ret": round(stats(r)[1], 6),
                    "ann_vol": round(stats(r)[2], 6),
                    "maxdd": round(stats(r)[3], 6),
                    "split_half": [round(stats(r.iloc[:len(r) // 2])[0], 3),
                                   round(stats(r.iloc[len(r) // 2:])[0], 3)],
                } for label, r in books.items()
            },
            "overlaid": out_configs,
        }, f, indent=2)
    print(f"\nsaved -> {OUTDIR}/top100_momentum_horizon.json")


if __name__ == "__main__":
    main()
