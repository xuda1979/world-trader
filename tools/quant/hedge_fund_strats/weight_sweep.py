"""Sleeve-level review of the flagship: h3/AP weight sweep + IV/vol-target
alternatives to the fixed 50/50 construction.

Answers, for the 2008-2026 window:
  1. Is 50/50 actually optimal for SR/CAGR/MaxDD, or is there a better mix?
  2. Do inverse-vol or rolling-vol-target weights beat static EW?

Usage: python tools/quant/hedge_fund_strats/weight_sweep.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from blend_6stream import load_hedge_streams, load_ap_gold, load_ls_champion  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def stats(r, rf=0.02):
    r = r.dropna()
    g = (1 + r).cumprod()
    mdd = (g / g.cummax() - 1).min()
    ann = (1 + r).prod() ** (252 / len(r)) - 1
    sr = (r.mean() * 252 - rf) / (r.std() * np.sqrt(252))
    return sr, ann, mdd


def main():
    h = load_hedge_streams()
    h3 = pd.concat([h["ls"], h["cta"], h["macro"]], axis=1).mean(axis=1)
    ap = load_ap_gold()
    ls = load_ls_champion()

    frame = pd.concat({"h3": h3, "ap": ap, "ls": ls}, axis=1)
    # 2008-2026 window = h3+AP only (ls is 2024+)
    f = frame[["h3", "ap"]].dropna()
    print(f"window: {f.index.min().date()} .. {f.index.max().date()} ({len(f)} days)")
    for c in ["h3", "ap"]:
        sr, ann, mdd = stats(f[c])
        vol = f[c].std() * np.sqrt(252)
        print(f"  {c}: SR {sr:+.3f}  CAGR {ann*100:+.1f}%  MaxDD {mdd*100:.1f}%  vol {vol*100:.1f}%")
    print(f"  corr(h3,ap) = {f['h3'].corr(f['ap']):+.3f}")

    print("\n== static weight sweep (h3 weight, rest AP) ==")
    rows = []
    for w in [0.0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.8, 0.9, 1.0]:
        p = w * f["h3"] + (1 - w) * f["ap"]
        sr, ann, mdd = stats(p)
        rows.append((w, sr, ann, mdd))
        print(f"  h3={w:.2f}: SR {sr:+.3f}  CAGR {ann*100:+.1f}%  MaxDD {mdd*100:.1f}%")
    best = max(rows, key=lambda r: r[1])
    print(f"  -> max-SR at h3={best[0]:.2f}: SR {best[1]:+.3f} (baseline 50/50 is row h3=0.50)")

    print("\n== inverse-vol weights (full-sample vol, EW cap) ==")
    vol = f.std() * np.sqrt(252)
    ivw = (1 / vol) / (1 / vol).sum()
    p = (f * ivw).sum(axis=1)
    sr, ann, mdd = stats(p)
    print(f"  IV weights: {ivw.round(3).to_dict()} -> SR {sr:+.3f}  CAGR {ann*100:+.1f}%  MaxDD {mdd*100:.1f}%")

    print("\n== rolling inverse-vol (252d, rebalanced monthly, no lookahead) ==")
    rv = f.rolling(252).std()
    rw = (1 / rv).div((1 / rv).sum(axis=1), axis=0)
    rw = rw.resample("MS").last().reindex(f.index).ffill()
    p = (f * rw).sum(axis=1)
    sr, ann, mdd = stats(p)
    print(f"  rolling IV: SR {sr:+.3f}  CAGR {ann*100:+.1f}%  MaxDD {mdd*100:.1f}%")
    print(f"  avg weights: {rw.mean().round(3).to_dict()}")

    print("\n== rolling 10% vol-target on h3 (AP unscaled), monthly ==")
    h3_vol_ann = f["h3"].rolling(252).std() * np.sqrt(252)
    for tv in [0.06, 0.08, 0.10, 0.12]:
        scale = (tv / h3_vol_ann).clip(0.25, 3)
        scale = scale.resample("MS").last().reindex(f.index).ffill()
        p = scale * f["h3"] * 0.5 + f["ap"] * 0.5
        sr, ann, mdd = stats(p)
        print(f"  h3 vol-target {tv*100:.0f}%: SR {sr:+.3f}  CAGR {ann*100:+.1f}%  MaxDD {mdd*100:.1f}%")


if __name__ == "__main__":
    main()
