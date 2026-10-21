"""INNOVATION AGENT 6 (Factor F) — Cross-Asset Time-Series Momentum (TSMOM).

Genuinely-new, orthogonal book vs the equity L/S champion. Uses PRICE-ONLY data
(no factor models, no stock picking) across a diversified set of global macro
assets: rates, FX, commodities, equity, credit. Classic Moskowitz-Ooi-Pedersen
time-series momentum: for each asset take +1 if trailing 12m return > 0 else -1
(sign), weight by inverse vol (risk parity), risk-target the whole book.

Why creative + high value:
  - orthogonal to the equity L/S champ (crisis-alpha, positive skew, low/neg
    correlation to stocks) -> diversifies the fund;
  - only needs price data we already have (FRED/FX/commodity levels);
  - decades-long test (2000-2026 for the deep series) not 210-mo overfit;
  - the TSMOM premium is one of the most robust documented in the literature.

Overlays reused from our playbook: vol-target whole book + DXY de-risk gate.
Net of 6 bps/side on each asset leg.
"""
from __future__ import annotations
import os, json
import numpy as np, pandas as pd
FRED = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
COST = 0.0006
LOOKBACK = 12            # 12m trailing sign for TSMOM
VOL_WIN = 12            # inverse-vol weighting window
VT_TGT, VT_CAP = 0.12, 1.5
DXY_Z, DXY_F = 1.5, 0.5


def level(name):
    d = pd.read_csv(os.path.join(FRED, f"{name}.csv"), parse_dates=["date"])
    d = d.sort_values("date").drop_duplicates("date").set_index("date")
    # FRED csvs are value/long name -> find numeric column
    num = d.select_dtypes(include=[np.number])
    return num.iloc[:, 0].rename(name).dropna()


def build_prices():
    # deep series (2000-2026) -> max testing depth
    series = {
        "us10y": level("us10y"),
        "us2y":   level("us2y"),
        "wti":    level("wti"),
        "brent":  level("brent"),
        "natgas": level("natgas"),
        "eur":    level("eur"),
        "cny":    level("cny"),
        "dxy":    level("dxy"),
        "copper": level("copper_monthly"),
        "baa":    level("baa"),
    }
    # gold/silver start 2006-07
    try: series["xau"] = level("xau")
    except Exception: pass
    try: series["slv"] = level("slv")
    except Exception: pass
    return pd.DataFrame(series)


def main():
    px = build_prices()
    px = px.resample("ME").last().dropna(how="all")
    px = px[px.index >= "200acher0-12-31"] if False else px
    px = px[px.index >= "2000-12-31"]
    rets = px.pct_change()
    # monthly-sampled but compute 12m sign on monthly returns
    mret = px.pct_change()

    sig = np.sign(mret.rolling(LOOKBACK).mean().shift(1))   # 12m momentum sign, lagged (no lookahead)
    vol = mret.rolling(VOL_WIN).std()                       # trailing vol per asset
    inv_vol = (1.0 / vol).replace([np.inf, -np.inf], np.nan)
    inv_vol = inv_vol.div(inv_vol.sum(axis=1), axis=0)      # risk parity weights

    wts = sig * inv_vol                                     # sign x risk-parity
    wts = wts.div(wts.abs().sum(axis=1).replace(0, np.nan), axis=0)  # normalize gross to 1
    held = wts.shift(1)                                     # formed at t-1
    book = (held * mret).sum(axis=1, min_count=1) - COST * held.diff().abs().sum(axis=1).fillna(0.0)

    # overlays
    rv = book.rolling(12, min_periods=9).std() * np.sqrt(12)
    sc = (VT_TGT / rv).clip(upper=VT_CAP, lower=0.0).fillna(1.0)
    dxy = level("dxy").resample("ME").last()
    dm = dxy.rolling(12, min_periods=8).mean(); ds = dxy.rolling(12, min_periods=8).std()
    dz = ((dxy - dm) / ds).reindex(book.index).ffill().shift(1)
    dgate = pd.Series(1.0, index=book.index); dgate[dz > DXY_Z] = DXY_F
    sc_d = (sc * dgate).fillna(1.0)
    final = book * sc_d - sc_d.diff().abs().fillna(0.0) * 2 * COST

    def stats(s):
        s = s.dropna(); eq = (1 + s).cumprod()
        return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 3),
                "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
                "dd": round(float((eq / eq.cummax() - 1).min()), 4),
                "win": round(float((s > 0).mean()), 3), "n": int(len(s))}

    print(f"=== CROSS-ASSET TSMOM ({px.shape[1]} assets, {len(book)} months "
          f"{book.index.min().date()}..{book.index.max().date()}) ===")
    print("assets:", list(px.columns))
    print(f"  raw      : {stats(book)}")
    print(f"  +vol-targ: {stats(book*sc - (sc.diff().abs().fillna(0))*2*COST)}")
    print(f"  +DXY gate: {stats(final)}")
    by = final.groupby(final.index.year).apply(lambda x: (1 + x).prod() - 1)
    yr = pd.Series(by).dropna()
    print(f"  up-years {(yr>=0).mean():.0%} | mean {yr.mean():+.1%} | worst {yr.min():+.1%}")
    json.dump({"assets": list(px.columns), "raw": stats(book),
               "vol_targ": stats(book*sc - (sc.diff().abs().fillna(0))*2*COST),
               "final": stats(final), "n_months": len(book),
               "annual": {int(k): round(float(v),4) for k,v in yr.items()}},
              open(os.path.join(os.path.dirname(FRED),"..","reports","xgb_horizons","cross_asset_tsmom.json"),"w"),
              indent=2, default=str)
    print("saved -> reports/xgb_horizons/cross_asset_tsmom.json")


if __name__ == "__main__":
    main()
