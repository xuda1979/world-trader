"""Honest assessment of all replicated prestigious-paper strategies at 3.8 bps cost.

Loads daily return streams (costs embedded at 3.8 bps one-side) and reports
honest metrics. Combines the verified long-history core legs on their full
common window; short-history legs are reported separately (not force-aligned
onto a tiny common window that misrepresents the core books).
2026-08-06
"""
import os
import pandas as pd, numpy as np

ROOT = "/Users/daxu/software/world-trader"
RES = os.path.join(ROOT, "tools/quant/ls/results")
TD = 252

LEGS = {
    # key: (path, label, prestige source, is_core)
    "fx_mom":  ("fx_momentum/daily_real.csv",       "FX XS momentum",    "Menkhoff+2012 JFE",            True),
    "tsmom":   ("cross_asset_tsmom/daily_real.csv", "Cross-asset TSMOM", "Moskowitz-Ooi-Pedersen 2012 JFE", True),
    "gold":    ("gold_trend/daily_real.csv",        "Gold trend (RV)",   "Moskowitz-Ooi-Pedersen 2012",   True),
    "etf_mom": ("etf_xs/daily_mom_real.csv",        "ETF XS momentum",   "Jegadeesh-Titman 1993 JF",      True),
    "crypto":  ("crypto_trend/daily_real.csv",      "Crypto trend",      "Liu-Tsyvinski 2021",            False),
    "cn":      ("cn_momentum/daily_real.csv",       "China XS momentum", "Jegadeesh-Titman 1993",         False),
}

def load(key):
    path, label, paper, core = LEGS[key]
    fp = os.path.join(RES, path)
    if not os.path.exists(fp):
        return None, label, paper, core
    df = pd.read_csv(fp, parse_dates=["date"]).set_index("date")
    return df["daily_return"].dropna(), label, paper, core

def metrics(r):
    r = r.dropna()
    if len(r) < 20 or r.std() == 0:
        return None
    ann = (1 + r).prod() ** (TD / len(r)) - 1
    vol = r.std() * np.sqrt(TD)
    sharpe = (r.mean() / r.std()) * np.sqrt(TD)
    eq = (1 + r).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    return {"sharpe": sharpe, "ann_ret": ann, "vol": vol, "maxdd": dd, "n": len(r)}

def show(name, s):
    m = metrics(s)
    if m is None:
        print(f"{name:26s} insufficient data")
        return s
    print(f"{name:26s} Sharpe {m['sharpe']:7.2f} | AnnRet {m['ann_ret']:7.1%} | "
          f"Vol {m['vol']:5.1%} | MaxDD {m['maxdd']:7.1%} | n {m['n']:5d}")
    return s

def main():
    print(f"{'leg':20s} {'prestige source':32s} {'Sharpe':>7s} {'AnnRet':>8s} {'Vol':>6s} {'MaxDD':>8s} {'n':>5s}")
    print("-" * 96)
    loaded = {}
    for key in LEGS:
        r, label, paper, core = load(key)
        if r is None:
            print(f"{label:20s} MISSING")
            continue
        m = metrics(r)
        loaded[key] = (r, label, paper, core)
        if m is None:
            print(f"{label:20s} {paper:32s} insufficient data")
            continue
        print(f"{label:20s} {paper:32s} {m['sharpe']:7.2f} {m['ann_ret']:8.1%} {m['vol']:6.1%} {m['maxdd']:8.1%} {m['n']:5d}")

    print()
    print("=" * 96)
    # CORE book: verified long-history legs on their full common window
    core = {k: v[0] for k, v in loaded.items() if v[3]}
    if len(core) < 2:
        print("Not enough core legs.")
        return
    cA = pd.DataFrame(core).dropna()
    print(f"CORE book ({' + '.join(core)}): full common window "
          f"{cA.index.min().date()}..{cA.index.max().date()}  ({cA.shape[0]} days)")
    print("\nCorrelation matrix (core, common sample):")
    print(cA.corr().round(2).to_string())
    print()
    eq = cA.mean(axis=1)
    vols = cA.std()
    rpw = (1.0 / vols) / (1.0 / vols).sum()
    rp = pd.Series(cA.values @ rpw.values, index=cA.index)
    print("-" * 96)
    show("CORE equal-weight", eq)
    show("CORE risk-parity (inv-vol)", rp)

    # Full book incl. short-history legs (aligned on common window)
    allr = pd.DataFrame({k: v[0] for k, v in loaded.items()}).dropna()
    if allr.shape[0] > 200:
        print("-" * 96)
        print(f"FULL book (all {len(loaded)} legs): {allr.shape[0]}-day common window "
              f"({allr.index.min().date()}..{allr.index.max().date()})")
        show("FULL equal-weight", allr.mean(axis=1))
        v2 = allr.std()
        rw2 = (1.0 / v2) / (1.0 / v2).sum()
        show("FULL risk-parity (inv-vol)", pd.Series(allr.values @ rw2.values, index=allr.index))

    out = {"core_eq": eq, "core_rp": rp}
    out_dir = os.path.join(RES, "replicated_book")
    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(out).to_csv(os.path.join(out_dir, "core_combined_daily.csv"))
    print(f"\nsaved -> {out_dir}/core_combined_daily.csv  (costs embedded at 3.8 bps one-side)")

if __name__ == "__main__":
    main()
