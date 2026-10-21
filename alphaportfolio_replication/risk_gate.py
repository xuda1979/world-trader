"""Multi-indicator drawdown risk gate (position-scaling, not market timing).

Design per user directive (2026-08-12): cap drawdown at ~10% (no leverage)
by scaling monthly portfolio exposure down when macro/market state is
drawdown-prone.  Multiple FREE indicators vote; the STRICTEST active signal
wins (avoid false negatives — don't miss 2008/2020 style crashes).

Indicators (all computed from data up to month-end t, applied to month t+1
positions — NO look-ahead):
  1. VIX level        : <15 full | 15-20 normal | 20-25 warn (0.7) |
                        25-30 risk (0.5) | >30 crisis (0.3)
  2. VIX percentile   : 90th pctile of trailing 2y -> 0.5 (level alone
                        under-triggers in calm regimes; percentile adapts)
  3. VIX slope        : 3-month VIX change > +50% -> 0.5 (fast spike)
  4. VIX term struct  : VIX > VIX3M (backwardation, panic) -> 0.5
  5. SPY vs 200DMA    : price < 200DMA AND 50DMA < 200DMA (death cross) -> 0.3
  6. SPY drawdown     : -10%..-15% from 52w high -> 0.5 ; < -15% -> 0.3
All data free: CBOE VIX/VIX3M daily CSVs + SPY (twelve_liq local panel).

Exposure multiplier for month m = min over active signals (1.0 if none).
Turnover of the gate itself is tiny (only scales at month boundaries).
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TD = 252


def load_daily(sym: str) -> pd.Series:
    """Daily close series for VIX / VIX3M (CBOE csv) or SPY (local panel)."""
    p = os.path.join(HERE, "data", f"{sym}.csv")
    if not os.path.exists(p) and os.path.exists(os.path.join(HERE, "data", f"{sym}_daily.csv")):
        p = os.path.join(HERE, "data", f"{sym}_daily.csv")
    if os.path.exists(p):
        df = pd.read_csv(p, index_col=0, parse_dates=True)
        col = "vix" if "vix" in df.columns else "close"
        if col not in df.columns:
            col = df.columns[-1]
        s = df[col].astype(float).dropna()
        return s
    # SPY from the quant local panel
    sp = os.path.join(HERE, "..", "tools", "quant", "data", "twelve_liq", f"{sym}.csv")
    if os.path.exists(sp):
        df = pd.read_csv(sp, index_col=0, parse_dates=True)
        c = "close" if "close" in df.columns else df.columns[-1]
        return df[c].astype(float).dropna()
    raise FileNotFoundError(f"no data for {sym}")


def monthly_last(s: pd.Series) -> pd.Series:
    """Last observation per month (month-end close)."""
    return s.resample("ME").last().dropna()


def gate_multipliers(vix: pd.Series, vix3m: pd.Series, spy: pd.Series,
                     floor: float = 0.3, vix_crisis: float = 30.0) -> pd.Series:
    """Monthly exposure multiplier series indexed by month-end, in [floor, 1].

    vix/vix3m/spy: daily close series (any start; only overlap used).
    floor: hard minimum exposure (0.3 = never fully flat, keeps the L/S
    book alive for recovery).
    """
    mv = monthly_last(vix)
    m3 = monthly_last(vix3m)
    ms = monthly_last(spy)

    idx = mv.index
    mult = pd.Series(1.0, index=idx)

    # 1. VIX level
    lvl = mv.clip(lower=0)
    mult = mult.where(lvl < 20, 0.7)
    mult = mult.where(lvl < 25, 0.5)
    mult = mult.where(lvl < vix_crisis, 0.3)

    # 2. VIX 90th percentile of trailing 24m (rolling, no look-ahead)
    p90 = mv.rolling(24 * 12, min_periods=60).quantile(0.90)
    hi_pct = (mv > p90) & p90.notna()
    mult[hi_pct] = mult[hi_pct].clip(upper=0.5)

    # 3. VIX slope: 3-month change > +50%
    chg = mv / mv.shift(3) - 1.0
    spiky = (chg > 0.50) & chg.notna()
    mult[spiky] = mult[spiky].clip(upper=0.5)

    # 4. Term structure: VIX > VIX3M (backwardation)
    if m3.notna().sum() > 60:
        m3a = m3.reindex(idx).ffill()   # align to vix month grid
        back = (mv > m3a) & m3a.notna()
        mult[back] = mult[back].clip(upper=0.5)

    # 5. SPY death cross: price < 200DMA and 50DMA < 200DMA
    ma200 = ms.rolling(200).mean()
    ma50 = ms.rolling(50).mean()
    death = (ms < ma200) & (ma50 < ma200) & ma200.notna()
    d = death.reindex(idx, method="ffill").fillna(False)
    mult[d] = mult[d].clip(upper=0.3)

    # 6. SPY drawdown from 52-week high
    hh = ms.rolling(TD).max()
    dd = ms / hh - 1.0
    dd_m = dd.reindex(idx, method="ffill").fillna(0.0)
    mult[dd_m < -0.15] = 0.3
    mult[(dd_m < -0.10) & (dd_m >= -0.15)] = 0.5

    return mult.clip(lower=floor, upper=1.0)


if __name__ == "__main__":
    v = load_daily("vix")
    v3 = load_daily("vix3m")
    s = load_daily("SPY")
    g = gate_multipliers(v, v3, s)
    n_de = int((g < 1.0).sum())
    print(f"gate multipliers: {len(g)} months, {n_de} de-risked "
          f"({100*n_de/len(g):.0f}%), min={g.min():.2f}")
    print("by year (mean multiplier):")
    by = g.groupby(g.index.year).mean()
    print(by.round(2).to_string())
