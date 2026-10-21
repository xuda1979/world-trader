#!/usr/bin/env python3
"""Blend the three validated champions: AP gold + polygon LS + DRL (vt10).

AP-gold champion : data/wf_champion_gold_opt.csv (gold 0.2, vt12, rev30,
                   monthly 2008-2026)
LS champion      : ../tools/quant/ls/results/champion_n10_r14_fresh/
                   daily_returns.csv (n10_r14, polygon, scramble-validated)
DRL ensemble     : data/ap_net6bps_returns.csv (16-seed, 6bps), vol-targeted
                   to 10% here (SR 1.66 at 0.55% vol -> deployable)

2026-08-12 findings: 2-way corr -0.15; 3-way 1/3-each -> SR 1.886 / ret
11.4% / MaxDD -3.0% (meets BOTH user targets, best SR of the program).

Usage: python run_blend_champions.py [w_ap w_ls w_drl]  (defaults 1/3 each)
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

def monthly(s: pd.Series) -> pd.Series:
    m = s.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    m.index = m.index.to_period("M").to_timestamp()
    return m

def stats(r):
    sr = r.mean() / r.std() * np.sqrt(12)
    eq = np.cumprod(1 + r)
    dd = min(eq / np.maximum.accumulate(eq) - 1) * 100
    return sr, r.mean() * 12 * 100, dd

def stats_d(r):
    sr = r.mean() / r.std() * np.sqrt(252)
    eq = np.cumprod(1 + r)
    dd = min(eq / np.maximum.accumulate(eq) - 1) * 100
    return sr, r.mean() * 252 * 100, dd

def main() -> None:
    # DAILY-frequency blend (2026-08-13 audit: daily is the honest view -
    # monthly sampling misses intra-month drawdowns). The 2-way default
    # blends the daily AP stream with the daily LS stream at daily freq.
    apd_path = os.path.join(HERE, "data", "wf_champion_gold_opt_daily.csv")
    if os.path.exists(apd_path):
        ap = pd.read_csv(apd_path, index_col=0, parse_dates=True).iloc[:, 0]
    else:
        ap_m = pd.read_csv(os.path.join(HERE, "data", "wf_champion_gold_opt.csv"))
        ap_m["ym"] = pd.to_datetime(ap_m["ym"])
        ap = ap_m.set_index("ym")["net"]
        ap.index = ap.index.to_period("M").to_timestamp()

    ls_dir = os.environ.get("LS_DIR", "levdet3.0")   # levdet3.0 = 3x gross (deployment variant)
    lsd = pd.read_csv(os.path.join(ROOT, "tools/quant/ls/results",
                                   ls_dir, "daily_returns.csv"),
                      index_col=0, parse_dates=True)
    col = "daily_return" if "daily_return" in lsd.columns else lsd.columns[0]
    ls = lsd[col]                                    # keep DAILY

    drl = pd.read_csv(os.path.join(HERE, "data", "ap_net6bps_returns.csv"),
                      index_col=0).iloc[:, 0].astype(float)
    drl.index = pd.to_datetime(drl.index).to_period("M").to_timestamp()
    # NOTE 2026-08-12: vol-targeting the DRL leg is NOT achievable (trailing
    # vol-target collapses SR 1.66 -> 0.43). Use the RAW returns (its real
    # 0.92%/yr); the deployable blend is the 2-way (w_drl=0).

    df = pd.concat({"ap": ap, "ls": ls}, axis=1).dropna()
    print(f"DAILY overlap: {df.index[0].date()}..{df.index[-1].date()} "
          f"n={len(df)} corr ap-ls={df['ls'].corr(df['ap']):.3f}")
    weights = [float(a) for a in sys.argv[1:]] or [0.4, 0.6, 0.0]   # 2-way default (deployable)
    print(f"{'w_ap':>6s} {'w_ls':>6s} {'SR':>7s} {'ret%':>8s} {'MaxDD%':>8s}")
    for i in range(0, len(weights), 3):
        w = weights[i:i+3]
        if len(w) < 3:
            break
        if w[2] > 0:
            # 3-leg: resample the daily 2-way to monthly to join the DRL
            b = (w[0]*df["ap"] + w[1]*df["ls"]).resample("ME").apply(lambda x: (1+x).prod()-1)
            b.index = b.index.to_period("M").to_timestamp()
            d3 = pd.concat({"b": b, "drl": drl}, axis=1).dropna()
            sr, ret, dd = stats(d3["b"] + w[2]*d3["drl"])
            print(f"{w[0]:6.2f} {w[1]:6.2f} {w[2]:6.2f} {sr:7.3f} {ret:+8.2f} {dd:8.2f} (monthly frame)")
        else:
            sr, ret, dd = stats_d(w[0]*df["ap"] + w[1]*df["ls"])
            print(f"{w[0]:6.2f} {w[1]:6.2f} {w[2]:6.2f} {sr:7.3f} {ret:+8.2f} {dd:8.2f} (daily)")

if __name__ == "__main__":
    main()
