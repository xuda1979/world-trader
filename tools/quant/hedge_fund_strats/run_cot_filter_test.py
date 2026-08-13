"""A/B test: COT positioning-agreement filter on natgas inside the CTA leg.

Iter-2 finding: corr(COT natgas spec z, fwd 13w natgas) = +0.17 stable across
decade splits, and gating the 63d trend on z-agreement improved the standalone
natgas trend in EVERY sub-period (SR -0.484->-0.220, MaxDD -89%->-49%) even
though the standalone leg is negative. This tests the same filter INSIDE the
real CTA leg (14 FRED series, vol-scaled) — the place where natgas squeezes
(Jan-2024 +319%) actually hurt.

Steps:
  1. Reproduce the baseline multi-21d CTA -> compare to the official
     equity_CTA_Futures_multi_21d.csv (pipeline fidelity check).
  2. Run the COT-filtered variant (zero out natgas position when the
     multi-timeframe signal disagrees with COT positioning, |z|>=0.25).
  3. Blend each CTA into the flagship (h3+AP) and compare.

Usage: python tools/quant/hedge_fund_strats/run_cot_filter_test.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from strat_cta_futures import (  # noqa: E402
    load_futures, compute_multi_timeframe_signal, vol_target_weights)
from core import BacktestEngine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
COT = os.path.join(HERE, "data_cot", "cot_tidy.csv")

# COT contract codes for natgas (NYMEX HH + ICE Henry LD1)
NG_CODES = ["023651", "023391"]


def load_natgas_z(prices_index):
    """Weekly natgas spec-positioning z-score -> daily (published-lag safe)."""
    df = pd.read_csv(COT, parse_dates=["report_date"])
    g = df[df["contract_code"].isin(NG_CODES)].groupby("report_date").agg(
        l=("m_money_long", "sum"), s=("m_money_short", "sum"), oi=("oi", "sum"))
    g["spec_pct"] = (g["l"] - g["s"]) / g["oi"]
    g["z"] = ((g["spec_pct"] - g["spec_pct"].rolling(104, min_periods=52).mean())
              / g["spec_pct"].rolling(104, min_periods=52).std())
    # report is as-of Tuesday, published Friday -> usable Monday (3 trading days)
    z = g["z"].reindex(prices_index, method="ffill").shift(3)
    return z


def build_weights(prices, signal, target_vol=0.15):
    returns = prices.pct_change()
    return vol_target_weights(signal, returns, target_vol=target_vol)


def run(prices, weights, rebalance_freq=21):
    engine = BacktestEngine(prices, cost_bps=6.0)
    daily_ret, equity, turnover = engine.run(weights, rebalance_freq=rebalance_freq)
    return daily_ret


def main():
    print("=" * 70)
    print("COT FILTER A/B TEST — natgas positioning gate inside the CTA leg")
    print("=" * 70)
    data = load_futures()
    prices = pd.DataFrame({sym: df["close"] for sym, df in data.items()})
    prices = prices.dropna(how="all").ffill(limit=5)
    prices = prices[prices.index >= "2008-01-01"]
    ok = [c for c in prices.columns if prices[c].count() > 300]
    prices = prices[ok]
    for y in ("us2y", "us10y", "us30y"):
        if y in prices.columns:
            prices[y] = -prices[y]
    print(f"Panel: {prices.shape[0]}d x {prices.shape[1]} instruments, "
          f"{prices.index[0].date()}..{prices.index[-1].date()}")

    base_signal = compute_multi_timeframe_signal(prices)
    base_w = build_weights(prices, base_signal)
    base_ret = run(prices, base_w, rebalance_freq=21)
    base_ret.to_csv(os.path.join(RESULTS, "_ab_base_cta_21d.csv"))

    official = pd.read_csv(os.path.join(RESULTS, "equity_CTA_Futures_multi_21d.csv"),
                           index_col=0, parse_dates=True).iloc[:, 0].pct_change()
    m = pd.concat({"official": official, "repro": base_ret}, axis=1).dropna()
    print(f"\nreproduction check vs official multi_21d (n={len(m)}):")
    print(f"  corr = {m['official'].corr(m['repro']):+.4f}")
    print(f"  corr of LEVELS = {(1+m['official']).cumprod().corr((1+m['repro']).cumprod()):+.4f}")

    # --- COT-filtered variants ---
    z = load_natgas_z(prices.index)
    print(f"\nnatgas z: {z.notna().sum()}/{len(z)} days covered")
    for atten, tag in [(0.0, "zero"), (0.5, "half")]:
        sig = base_signal.copy()
        agree = (np.sign(z) == np.sign(sig["natgas"])) | (z.abs() < 0.25)
        sig["natgas"] = sig["natgas"] * np.where(agree, 1.0, atten)
        w = build_weights(prices, sig)
        ret = run(prices, w, rebalance_freq=21)
        ret.to_csv(os.path.join(RESULTS, f"_ab_cot_{tag}_cta_21d.csv"))
        active = (~agree).sum()
        print(f"  {tag}: filter active {active} days ({active/len(sig)*100:.1f}%)")


if __name__ == "__main__":
    main()
