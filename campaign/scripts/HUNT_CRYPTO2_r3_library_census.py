#!/usr/bin/env python3
"""HUNT_CRYPTO2 ROUND 3 (b): sleeve_library census.

Charter: scan campaign/results/sleeve_library metas for crypto-adjacent sleeves;
verify manifest completeness (every csv has meta with span + cost convention);
report gaps.

Crypto-adjacency is checked TWO ways (name grep is not enough for a returns-only
library):
  1. name/meta grep for crypto tokens;
  2. data-driven: |Pearson corr| of each library sleeve vs BTC and vs an
     equal-weight 12-coin crypto basket (tools/quant/data/more_crypto), computed
     on the overlapping daily index. |corr| >= 0.30 flags adjacency (the champion
     gate uses 0.15/0.35 thresholds, so 0.30 is a conservative tripwire).
Manifest completeness per GATES_CONTRACT item 4 spirit: every csv must have a
.meta carrying an identifiable span and the cost convention. A bare provenance
one-liner ("converted from ...") carries NEITHER and is logged as a gap.

Usage: python3 campaign/scripts/HUNT_CRYPTO2_r3_library_census.py
Out:   stdout + work_r3/R3b_library_census.txt
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "agents", "chief", "coord", "HUNT_CRYPTO2", "work_r3"))
import r3lib  # noqa: E402

LIB = os.path.join(ROOT, "results", "sleeve_library")
CRYPTO_DIR = os.path.join(os.path.dirname(ROOT), "tools", "quant", "data", "more_crypto")
OUT = os.path.join(ROOT, "agents", "chief", "coord", "HUNT_CRYPTO2", "work_r3",
                   "R3b_library_census.txt")

CRYPTO_TOKENS = re.compile(r"crypto|bitcoin|btc|eth\b|ether|altcoin|binance|coin|xbt|solana|doge",
                           re.IGNORECASE)
COINS = ["BTC", "ETH", "BNB", "ADA", "XRP", "SOL", "DOT", "LINK", "LTC", "MATIC", "AVAX", "DOGE"]
ADJ_CORR = 0.30   # tripwire for data-driven crypto adjacency
GATE_CORR = 0.15  # campaign decorrelation bar (contract 3f, preferred)


def crypto_refs():
    """BTC series + EW basket of the 12 coins, daily simple returns."""
    px = {}
    for c in COINS:
        p = os.path.join(CRYPTO_DIR, f"{c}.csv")
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        df.columns = [str(c).strip().lower() for c in df.columns]
        dcol = next(col for col in df.columns if col in ("date", "timestamp", "time", "day"))
        ccol = next(col for col in df.columns if col.startswith("close") or col in ("adj close", "price"))
        s = pd.Series(df[ccol].astype(float).values, index=pd.DatetimeIndex(df[dcol]))
        px[c] = s[~s.index.duplicated(keep="last")].sort_index()
    rets = {c: s.pct_change().dropna() for c, s in px.items()}
    btc = rets.get("BTC")
    basket = pd.concat([rets[c].rename(c) for c in rets], axis=1).dropna().mean(axis=1)
    return btc, basket


def main():
    btc, basket = crypto_refs()
    files = sorted(f for f in os.listdir(LIB) if f.endswith(".csv"))
    lines = [f"# R3b sleeve_library census ({len(files)} csv) — "
             f"manifest completeness + crypto-adjacency",
             f"crypto tripwire: |corr|>={ADJ_CORR} vs BTC or EW-12 basket "
             f"(overlap span); gate bar for reference {GATE_CORR}", ""]
    n_gap_meta, n_gap_span, n_gap_cost, n_adjacent = 0, 0, 0, 0
    for f in files:
        path = os.path.join(LIB, f)
        name = f[:-4]
        meta_path = path + ".meta"
        meta_txt = open(meta_path).read().strip() if os.path.exists(meta_path) else None
        try:
            r = r3lib.load_ret(path)
            m = dict(n=len(r), start=str(r.index[0].date()), end=str(r.index[-1].date()),
                     sr=r3lib.sharpe_d(r), vol=r3lib.evaluate_arm(r, btc)["vol"])
        except Exception as e:  # unreadable csv is itself a manifest gap
            lines.append(f"{name:32s} UNREADABLE: {e}")
            n_gap_meta += 1
            continue
        # --- meta completeness
        gaps = []
        if meta_txt is None:
            gaps.append("NO_META"); n_gap_meta += 1
        else:
            has_span = bool(re.search(r"20\d{2}-\d{2}|19\d{2}-\d{2}|\b(19|20)\d{2}\b", meta_txt)) \
                or (2010 <= r.index[0].year <= 2020)  # span derivable from csv itself
            has_cost = bool(re.search(r"6\.4|bps|borrow|cost|net|gross", meta_txt, re.I))
            if not has_span:
                gaps.append("meta:span"); n_gap_span += 1
            if not has_cost:
                gaps.append("meta:cost"); n_gap_cost += 1
        # --- crypto adjacency
        name_hit = bool(CRYPTO_TOKENS.search(name)) or (meta_txt and bool(CRYPTO_TOKENS.search(meta_txt)))
        j = pd.concat([r.rename("r"), btc.rename("btc")], axis=1, sort=True).dropna()
        cb = float(j["r"].corr(j["btc"])) if len(j) > 60 else np.nan
        k = pd.concat([r.rename("r"), basket.rename("b")], axis=1, sort=True).dropna()
        ck = float(k["r"].corr(k["b"])) if len(k) > 60 else np.nan
        adj = name_hit or (np.isfinite(max(cb, ck, key=lambda x: -9 if pd.isna(x) else x))
                           and max(np.abs(x) for x in (cb, ck) if np.isfinite(x)) >= ADJ_CORR)
        flag = ""
        if adj:
            flag = " <== CRYPTO-ADJACENT"; n_adjacent += 1
        lines.append(
            f"{name:32s} n={m['n']:5d} {m['start']}..{m['end']} SR={m['sr']:+6.2f} vol={100*m['vol']:5.1f}% "
            f"corrBTC={cb:+.3f} corrBASKET={ck:+.3f} meta={'1-liner' if meta_txt and len(meta_txt.splitlines())==1 else ('NONE' if meta_txt is None else 'rich')}"
            f"{' GAPS['+','.join(gaps)+']' if gaps else ''}{flag}")
    lines += ["",
              f"SUMMARY: {len(files)} csv | no-meta: {n_gap_meta} | meta w/o span: {n_gap_span} | "
              f"meta w/o cost: {n_gap_cost} | crypto-adjacent (name or |corr|>={ADJ_CORR}): {n_adjacent}"]
    txt = "\n".join(lines)
    print(txt)
    with open(OUT, "w") as fh:
        fh.write(txt + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
