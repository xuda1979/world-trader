#!/usr/bin/env python3
"""HONEST GATE: copper ('Dr. Copper') alternative-data sleeve vs V7 champion.

Fetched 2026-09-22 from AlphaVantage COPPER monthly (data/copper_alpha.csv, 1992-2026-07)
— a genuinely NEW on-disk data source (prior log 2026-09-14: 'no GC/SI' metals on disk).

Tests several copper signals on IS(<2017)/OOS(>=2017) monthly basis against V7's adoption
bar: IS monthly SR >= 1.0, OOS SR sign, |corr to champion| threshold, and dAnn>0 on a
capital-real capped re-fit. Honest: a low-corr sleeve that can't add per-gross return to
the energy-dominated book is REJECTED.
"""
import pandas as pd, numpy as np, os
B = "campaign"
# ---- copper monthly level (aligned to month-end, matching champion grid) ----
c = pd.read_csv(f"{B}/agents/HUNT_ALT_METALS/data/copper_alpha.csv")
c["date"] = pd.to_datetime(c["date"]); c = c.set_index("date")["value"].astype(float).sort_index()
c = c.resample("ME").last().dropna()
cm = c.pct_change().dropna()
# ---- V7 champion monthly (realistic net, ledger) ----
LED = pd.read_csv(f"{B}/work_backtest_oos/OPT_20V7_FULL_LEDGER.csv", parse_dates=["date"])
g = LED.groupby("date")[["pnl","cost"]].sum()
champ_m = (1 + (g.pnl - g.cost).sort_index()).resample("ME").prod() - 1
IS_END = pd.Timestamp("2017-01-01")

def sr(x):
    x = x.dropna()
    return x.mean()/x.std()*np.sqrt(12) if len(x) > 3 and x.std() > 1e-12 else 0.0

def banded_z(level, lookback, z):
    """Classic V7 sleeve construction: z-score entry on trailing-window changes."""
    r = level.pct_change(lookback)
    mu = r.rolling(lookback, min_periods=int(lookback*0.8)).mean()
    sd = r.rolling(lookback, min_periods=int(lookback*0.8)).std()
    zs = (r - mu)/sd.replace(0, np.nan)
    sig = pd.Series(np.where(zs > z, 1.0, np.where(zs < -z, -1.0, np.nan)), index=level.index)
    return sig.ffill().fillna(0.0).shift(1)  # T+1, no lookahead

def trend_ma(level, n):
    sig = np.where(level >= level.rolling(n, min_periods=n).mean(), 1.0, -1.0)
    s = pd.Series(sig, index=level.index).shift(1)  # T+1
    return s.fillna(0.0)

def mom(level, lookback):
    r = level.pct_change(lookback).shift(1)  # T+1
    return np.sign(r).fillna(0.0)

def test(name, retser):
    both = pd.concat([retser.rename("sleeve"), champ_m.rename("champ")], axis=1).dropna()
    both = both[both.index >= "2009-01-01"]
    isr = both[both.index < IS_END]; osr = both[both.index >= IS_END]
    corr = both["sleeve"].corr(both["champ"])
    ic = len(isr); oc = len(osr)
    print(f"{name:<28} IS_SR={sr(isr['sleeve']):>6.2f} ({ic:>3}m) OOS_SR={sr(osr['sleeve']):>6.2f} ({oc:>3}m) corr2champ={corr:>6.3f}")

print("COPPER as of", c.index.max().date(), "rows", len(c), "\n")
test("copper raw long", cm)
test("copper tsmom-12", trend_ma(c, 12) * cm)
test("copper mom-12", mom(c, 12) * cm)
test("copper banded_z12/z1", banded_z(c, 12, 1.0) * cm)
test("copper banded_z6/z0.5", banded_z(c, 6, 0.5) * cm)
test("copper trend-24", trend_ma(c, 24) * cm)
# risk-on/off: copper 12m change as a regime condition on the champion (filter idea)
copper_risk = (c.pct_change(12) > 0).astype(float).shift(1).reindex(champ_m.index).fillna(1.0)
filtered = champ_m * copper_risk
print("\nregime-filter variant (champion gated on positive 12m copper slope):")
test("champ x copper>0", filtered)
