"""Monthly-frame blend analysis at the current TRADING_COST_BPS.

The daily 6-stream SR is inflated by AP gold's smooth dailyized leg
(~sqrt(21) sampling effect). This script gives the honest monthly-sampled
numbers, at sleeve-EW (each suite = one sleeve, as in the addenda):

  - Long window (2008-02..2026-07): hedge 3-stream / 4-stream EW with and
    without the AP gold sleeve (AP's full history).
  - Short window (2024-07..2026-07): same + LS champion sleeve
    (hedge + AP + LS and hedge3 + AP + LS), both with stat arb in and out.
  - Sub-period robustness (geometric monthly SR) for the long-window
    variants.

Hedge sleeves: monthly-resampled from the 12-bps-RT daily equity curves.
AP gold: native monthly, already net of 6 bps one-way.
LS champion: monthly-resampled from the re-costed 6 bps/side daily series
(reuse blend_6stream.load_ls_champion).

Usage: python tools/quant/hedge_fund_strats/blend_monthly.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from blend_6stream import load_ap_gold, load_ls_champion  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
RISK_FREE = 0.02

PERIODS = [
    ("2008-2012", "2008-01-01", "2012-12-31"),
    ("2013-2017", "2013-01-01", "2017-12-31"),
    ("2018-2022", "2018-01-01", "2022-12-31"),
    ("2023-2026", "2023-01-01", "2026-12-31"),
]

HEDGE_FILES = {
    "ls": "equity_L_S_130_30.csv",
    "cta": "equity_CTA_Futures_multi_21d.csv",
    "macro": "equity_Global_Macro.csv",
    "statarb": "equity_StatArb_40pairs_z15.csv",
}


def load_hedge_monthly() -> dict:
    """12-bps-RT daily equity curves -> month-end returns."""
    out = {}
    for key, fn in HEDGE_FILES.items():
        eq = pd.read_csv(os.path.join(RESULTS, fn), index_col=0, parse_dates=True).iloc[:, 0]
        m = eq.resample("ME").last()
        out[key] = m.pct_change()
    return out


def monthly_sr(r: pd.Series) -> float:
    r = r.dropna()
    if len(r) < 12:
        return np.nan
    return (r.mean() * 12 - RISK_FREE) / (r.std() * np.sqrt(12)) if r.std() > 0 else np.nan


def geom_msr(r: pd.Series) -> float:
    g = np.log1p(r.dropna())
    if len(g) < 12 or g.std() <= 0:
        return np.nan
    return (g.mean() * 12 - RISK_FREE) / (g.std() * np.sqrt(12))


def stats(r: pd.Series):
    r = r.dropna()
    eq = (1 + r).cumprod()
    mdd = (eq / eq.cummax() - 1).min()
    ann = (1 + r).prod() ** (12 / len(r)) - 1
    return monthly_sr(r), ann, mdd


def report(name: str, r: pd.Series):
    sr, ann, mdd = stats(r)
    print(f"  {name:34s} SR {sr:+.2f}  ret {ann*100:+.1f}%  MaxDD {mdd*100:.1f}%  (n={len(r.dropna())})")
    return sr


def main():
    print("=" * 70)
    print("MONTHLY-FRAME BLEND (honest sampling for AP gold leg)")
    print("=" * 70)
    hedge = load_hedge_monthly()
    ap = load_ap_gold().resample("ME").apply(lambda x: (1 + x).prod() - 1)
    ls = load_ls_champion().resample("ME").apply(lambda x: (1 + x).prod() - 1)

    h3 = pd.concat([hedge["ls"], hedge["cta"], hedge["macro"]], axis=1).mean(axis=1)
    h4 = pd.concat([hedge[k] for k in ["ls", "cta", "macro", "statarb"]], axis=1).mean(axis=1)

    # ---- Long window (AP full history) ----
    print(f"\nLong window 2008-02..{ap.index.max().date()} (AP gold full history):")
    long = pd.concat({"h3": h3, "h4": h4, "ap": ap}, axis=1).dropna()
    print(f"  common: {long.index.min().date()}..{long.index.max().date()} ({len(long)} months)")
    report("hedge 4-stream EW", long["h4"])
    report("hedge 3-stream EW", long["h3"])
    report("h4 + AP (sleeve EW)", long[["h4", "ap"]].mean(axis=1))
    report("h3 + AP (sleeve EW)", long[["h3", "ap"]].mean(axis=1))
    print(f"  corr h3-ap {long['h3'].corr(long['ap']):+.3f}  corr h4-ap {long['h4'].corr(long['ap']):+.3f}")

    print("\n  Sub-period geometric SR (long window):")
    for name, r in [("h4", long["h4"]), ("h3", long["h3"]),
                    ("h4+AP", long[["h4", "ap"]].mean(axis=1)),
                    ("h3+AP", long[["h3", "ap"]].mean(axis=1))]:
        subs = [geom_msr(r.loc[s:e]) for _, s, e in PERIODS]
        print(f"    {name:8s} " + "  ".join(f"{v:+.2f}" for v in subs) + "   all")

    # ---- Short window (all three sleeves) ----
    print(f"\nShort window 2024-07..2026-07 (LS champion history):")
    short = pd.concat({"h3": h3, "h4": h4, "ap": ap, "ls": ls}, axis=1).dropna()
    print(f"  common: {short.index.min().date()}..{short.index.max().date()} ({len(short)} months)")
    report("hedge 4-stream EW", short["h4"])
    report("hedge 3-stream EW", short["h3"])
    report("h4 + AP + LS (6-stream)", short[["h4", "ap", "ls"]].mean(axis=1))
    report("h3 + AP + LS (5-stream)", short[["h3", "ap", "ls"]].mean(axis=1))
    report("h3 + LS (no AP)", short[["h3", "ls"]].mean(axis=1))
    c = short[["h3", "h4", "ap", "ls"]].corr()
    print("  corr matrix:")
    print(c.round(3).to_string())

    out = pd.DataFrame({
        "long_h4_ap": long[["h4", "ap"]].mean(axis=1),
        "long_h3_ap": long[["h3", "ap"]].mean(axis=1),
        "short_6stream": short[["h4", "ap", "ls"]].mean(axis=1),
        "short_5stream": short[["h3", "ap", "ls"]].mean(axis=1),
    })
    out.to_csv(os.path.join(RESULTS, "blend_monthly.csv"))
    print("\nsaved -> results/blend_monthly.csv")


if __name__ == "__main__":
    main()
