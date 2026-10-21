#!/usr/bin/env python3
"""ITER18 — EIA storage-surprise sleeve (US working gas) traded on Henry Hub.

The one lead the campaign ledger still marked UNTESTED: the EIA regional/product storage
cross-section. This is its simplest honest form — the aggregate US weekly storage figure.

Signal
  * level L_t  : weekly working gas in underground storage (Friday-dated, 1994+, Bcf)
  * change     : dL_t = L_t - L_{t-1}                        (injection / withdrawal)
  * norm N_t   : mean of dL over the SAME week-of-year in the trailing NORM_YEARS years,
                 strictly prior years only
  * surprise   : s_t = dL_t - N_t   (a bigger-than-normal build = bearish)
  * position   : -clip(z(s), -Z_CAP, +Z_CAP) / Z_CAP  in [-1, +1]

Causality (the reason this file exists at all)
  EIA publishes the week-ending-Friday figure the FOLLOWING THURSDAY, so the value dated week
  w is only usable from w + PUB_LAG_DAYS. The daily sleeve then earns day t from the position
  known at t-1:  ret_t = pos_{t-1} * ng_ret_t. Both steps are pinned by
  campaign/bt/tests/test_iter18_storage_sleeve.py.

Usage: python3 campaign/scripts/iter18_storage_sleeve.py [--emit]
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
STORAGE = "tools/quant/data/newdata/GASDESW.csv"          # EIA weekly US working gas
PRICE = "tools/quant/data/newdata/DHHNGSP.csv"            # Henry Hub spot, daily
PUB_LAG_DAYS = 6      # Friday figure -> following Thursday release
NORM_YEARS = 5
Z_WIN = 52
Z_CAP = 3.0
OUT = f"{ROOT}/campaign/agents/chief/coord/ITER18_STORAGE/sleeves/NG_storage_surprise_daily.csv"


def load(path):
    df = pd.read_csv(f"{ROOT}/{path}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float).sort_index()


def seasonal_norm(level, years=NORM_YEARS):
    """Trailing mean of the same week-of-year change, using STRICTLY PRIOR years."""
    ch = level.diff()
    woy = pd.Series(level.index.isocalendar().week.values, index=level.index)
    out = pd.Series(np.nan, index=level.index)
    for w in woy.unique():
        grp = ch[woy == w]
        for d in grp.index:
            prior = grp[(grp.index < d) & (grp.index >= d - pd.Timedelta(days=int(365.25 * years) + 7))]
            if len(prior) >= 2:
                out[d] = float(prior.mean())
    return out


def signal(level, z_win=Z_WIN, z_cap=Z_CAP, years=NORM_YEARS):
    """Weekly target position in [-1, +1]; negative = short gas (surprise build)."""
    surprise = level.diff() - seasonal_norm(level, years)
    m = surprise.rolling(z_win, min_periods=26).mean()
    sd = surprise.rolling(z_win, min_periods=26).std()
    z = (surprise - m) / sd.replace(0.0, np.nan)
    return (-z.clip(-z_cap, z_cap) / z_cap).fillna(0.0)


def build_sleeve(level, price, pub_lag_days=PUB_LAG_DAYS):
    """Daily causal sleeve return series on the price index."""
    pos = signal(level)
    pos.index = pos.index + pd.Timedelta(days=pub_lag_days)   # published later
    daily_pos = pos.reindex(price.index, method="ffill").fillna(0.0)
    return (daily_pos.shift(1) * price.pct_change()).fillna(0.0)


def main():
    level = load(STORAGE)
    price = load(PRICE)
    ret = build_sleeve(level, price)
    print(f"storage {level.index.min().date()}..{level.index.max().date()} ({len(level)} wks)")
    print(f"price   {price.index.min().date()}..{price.index.max().date()} ({len(price)} days)")
    r = ret[ret.index >= level.index.min() + pd.Timedelta(days=PUB_LAG_DAYS)]
    print(f"sleeve  n={len(r)}  mean {r.mean()*252*100:.3f}%/yr  vol {r.std()*np.sqrt(252)*100:.3f}%  "
          f"SR {r.mean()/r.std()*np.sqrt(252):.4f}")
    if "--emit" in sys.argv:
        import os
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        pd.DataFrame({"ret": ret}).to_csv(OUT)
        print("wrote", OUT)


if __name__ == "__main__":
    main()
