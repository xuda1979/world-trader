"""Walk-forward OOS check for the credit-spread percentile gate on top100 momentum.

Sweep context: full-sample best of 35 configs was credit_pct_0.85_f0.3
(SR 0.779 vs baseline 0.626, MaxDD -31.8% vs -50.6%). To rule out sweep
selection bias: within the credit_pct family (q in 0.85/0.90/0.95, f=0.3),
pick the best q on one half of the sample, apply it to the other half.
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monthly_top100_momentum import prepare, walk_forward, stats
from top100_momentum_regime_filter import load_fred, exposure_pct

FRED = os.path.join("/Users/daxu/software/world-trader",
                    "tools/quant/hedge_fund_strats/data_fred")
QS = [0.85, 0.90, 0.95]


def half_sharpes(r):
    h = len(r) // 2
    return (stats(r.iloc[:h])[0], stats(r.iloc[h:])[0])


def main():
    prices, ret, sharpe, rdates = prepare()
    idx = prices.index
    baa = load_fred("baa.csv")
    aaa = load_fred("aaa.csv")
    spread = (baa - aaa).dropna()

    base_r, _, _ = walk_forward(prices, ret, sharpe, rdates)
    bh = half_sharpes(base_r)
    print(f"baseline halves          : h1 {bh[0]:.3f} | h2 {bh[1]:.3f}")

    fam = {}
    for q in QS:
        r, _, _ = walk_forward(prices, ret, sharpe, rdates,
                               exposure_pct(spread, idx, q, 0.3))
        fam[q] = r
        h1, h2 = half_sharpes(r)
        print(f"credit_pct_{q}_f0.3      : h1 {h1:.3f} | h2 {h2:.3f}")

    # WF: pick best q on h1 -> OOS on h2, and vice versa
    best_h1 = max(QS, key=lambda q: half_sharpes(fam[q])[0])
    best_h2 = max(QS, key=lambda q: half_sharpes(fam[q])[1])
    print(f"\nWF direction 1: q={best_h1} chosen in-sample on h1 "
          f"(IS {half_sharpes(fam[best_h1])[0]:.3f}) "
          f"-> OOS h2 Sharpe {half_sharpes(fam[best_h1])[1]:.3f} "
          f"(baseline h2 {bh[1]:.3f})")
    print(f"WF direction 2: q={best_h2} chosen in-sample on h2 "
          f"(IS {half_sharpes(fam[best_h2])[1]:.3f}) "
          f"-> OOS h1 Sharpe {half_sharpes(fam[best_h2])[0]:.3f} "
          f"(baseline h1 {bh[0]:.3f})")


if __name__ == "__main__":
    main()
