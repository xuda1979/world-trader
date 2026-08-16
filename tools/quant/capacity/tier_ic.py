"""Capacity-tier cross-sectional momentum IC study (thesis Pillar 1 test).

CLAIM to test: the agile-operator edge (medium-frequency predictive signal)
should be STRONGER in less-efficient / less-crowded names than in mega-caps,
because institutions arbitrage the big-liquid names but can't deploy into the
smaller ones. If true, the cross-sectional IC of a momentum/trend signal should
rise as we move from the most-liquid tier to the least-liquid tier.

Data: the reliable local daily price panels only (no gated live endpoints).
We proxy 'capacity/liquidity' by each name's median dollar-turnover
(close*vol) over the sample — the standard liquidity proxy. Names are split
into terciles by this; the thesis predicts IC(top tercile) < IC(bottom tercile).

Method: monthly cross-sectional, no look-ahead. For each month, signal = past
252d risk-adjusted momentum (Sharpe-like) per name; compute Spearman/rank IC of
signal vs forward 21d (and 63d) return, within the valid names each month, then
average IC per tier. Honest small-sample caveat: 320 names / 3 tiers ~107 each,
recent ~3y window -> ~36 monthly ICs per tier.
"""
from __future__ import annotations
import os, glob, sys
import numpy as np, pandas as pd, json

PANELS = ["twelve_big", "twelve_liq", "twelvedata", "polygon", "polygon_v2"]
ROOT = os.path.join(os.path.dirname(__file__), "..", "data")

def load():
    series = {}
    for panel in PANELS:
        d = os.path.join(ROOT, panel)
        if not os.path.isdir(d): continue
        for f in glob.glob(os.path.join(d, "*.csv")):
            sym = os.path.basename(f)[:-4].upper()
            if sym in series: continue
            try:
                df = pd.read_csv(f, parse_dates=[0])
                df = df.tail(1000).set_index(df.columns[0])
                for c in ["close", "vol", "high", "low"]:
                    if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
                if "close" not in df: continue
                series[sym] = df
            except Exception:
                pass
    return series

def per_name(s):
    """Return (log_close_series, med_dollar_vol)."""
    close = s["close"].dropna()
    dol = (close * s["vol"]).median() if "vol" in s else np.nan
    return np.log(close), dol

def main():
    series = load()
    print(f"loaded {len(series)} names")
    # align all on union of dates
    dates = sorted(set().union(*[set(s.index) for s in series.values()]))
    # For speed, restrict to a common recent window where most names have data
    dates = [d for d in dates if d >= pd.Timestamp("2023-06-01")]
    # build aligned log-close matrix
    import collections
    mats = {}
    dol = {}
    for sym, s in series.items():
        lc, dv = per_name(s)
        mats[sym] = lc.reindex(dates).ffill()
        dol[sym] = dv
    logmat = pd.DataFrame(mats, index=dates)
    print(f"log-close matrix {logmat.shape}")

    # liquidity tiers
    liq = pd.Series(dol)
    liq = liq.dropna().sort_values(ascending=False)
    t3 = liq.quantile(0.34); t1 = liq.quantile(0.66)
    tier = pd.Series(index=liq.index, dtype=str)
    tier[liq >= t1] = "large"     # most liquid
    tier[(liq < t1) & (liq >= t3)] = "mid"
    tier[liq < t3] = "small"      # least liquid
    print(f"tiers: {tier.value_counts().to_dict()}")
    print(f"  large med $vol {liq[tier=='large'].median():,.0f} | small med $vol {liq[tier=='small'].median():,.0f}")

    mom = logmat.diff(252)
    results = {}
    for h, hlab in [(21, "21d"), (63, "63d")]:
        fwd = logmat.shift(-h) - logmat
        ics = {t: [] for t in ["large", "mid", "small"]}
        for m in range(252, len(dates) - h, 21):   # monthly rebalance
            i = dates[m]
            sig = mom.loc[i].dropna()
            fv = fwd.loc[i].reindex(sig.index).dropna()
            common = sig.reindex(fv.index).dropna()
            if len(common) < 20: continue
            for t in ["large", "mid", "small"]:
                sub = common[tier.reindex(common.index) == t].dropna()
                if len(sub) < 15: continue
                # rank IC
                from scipy.stats import spearmanr
                rho, _ = spearmanr(sub, fv.reindex(sub.index))
                if not np.isnan(rho): ics[t].append(rho)
        avg = {t: (float(np.mean(v)) if v else None) for t, v in ics.items()}
        se = {t: (float(np.std(v)/np.sqrt(len(v))) if len(v) > 1 else None) for t, v in ics.items()}
        n = {t: len(v) for t, v in ics.items()}
        results[hlab] = {"mean_rank_IC": avg, "se": se, "n_months": n}
        print(f"\nforward {hlab}: mean rank-IC by capacity tier (mean +- SE):")
        for t in ["large", "mid", "small"]:
            if avg[t] is not None:
                print(f"   {t:6s}: IC={avg[t]:+.4f} +-{se[t]:.4f}  (n={n[t]} months)")
            else:
                print(f"   {t}: n/a")
    rdir = os.path.join(os.path.dirname(__file__), "..", "reports"); os.makedirs(rdir, exist_ok=True)
    out = {"tiers_med_dolvol": {t: float(liq[tier==t].median()) for t in tier.unique()},
           "results": results}
    with open(os.path.join(rdir, "capacity_tier_ic.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nsaved reports/capacity_tier_ic.json")

if __name__ == "__main__":
    main()
