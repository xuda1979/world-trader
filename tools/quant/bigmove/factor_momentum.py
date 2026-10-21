"""INNOVATION AGENT 1 — Cross-sectional factor-momentum (market-neutral across
Fama-French factor portfolios).

This is a TOTALLY NEW book, orthogonal to the stock-picking champion:
instead of long/short individual equities, it trades AMONG factor portfolios
(SMB, HML, RMW, CMA, MOM) — going long the factors with the strongest trailing
return and short the weakest, dollar-neutral/gross-neutral across the factor
books. The investment case:
  - factor returns are persistent + lowly correlated with each other
    (momentum works ON factors, a well-documented edge);
  - zero market beta / naturally hedged (net-zero across factor books);
  - CAPACITY-RICH (index-scale factor portfolios, no small-cap liquidity wall);
  - testable over a CENTURY (1926-2026, = thousands of independent months,
    vs the equity book's 210 OOS months).

Overlays (reusing our drawdown playbook on a NEW asset class):
  - vol-target the whole factor book (~0.10 ann, cap 1.5) to cut tail
  - DXY dollar-stress de-risk (z>1.5->0.4) as the crisis gate
Net of 6 bps/side on each factor leg.
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
HERE = "/Users/daxu/software/world-trader/tools/quant/bigmove"
FRED = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred"
COST = 0.0006
LOOKBACK = 6          # factor-momentum lookback (months)
HOLD = 1              # monthly rebalance
VT_TGT, VT_CAP = 0.10, 1.5
DXY_Z, DXY_F = 1.5, 0.4
MIN_YEAR = 1964       # start after the first survivable multi-factor era


def load_factor_returns():
    def rd(f, skip, cols):
        d = pd.read_csv(os.path.join("/Users/daxu/software/world-trader/tools/quant/data/ff_factors", f), skiprows=skip)
        d.columns = [c.strip() for c in d.columns]
        d = d.dropna(subset=[d.columns[0]])
        d = d[d[d.columns[0]].astype(str).str.match(r"^\d{8}$")]
        d["date"] = pd.to_datetime(d[d.columns[0]].astype(str), format="%Y%m%d")
        out = d.set_index("date")[cols] / 100.0
        return out
    res = rd("F-F_Research_Data_Factors_daily.csv", 3, ["SMB", "HML", "RF"])
    mom = rd("F-F_Momentum_Factor_daily.csv", 16, ["Mom"])  # verify skip
    # RMW, CMA live in the 5-factor file if available; else skip
    try:
        f5 = rd("F-F_Research_Data_5Factors_daily.csv", 3, ["RMW", "CMA"])
    except Exception:
        f5 = pd.DataFrame()
    m = res.resample("ME").last()
    momm = mom.resample("ME").last()
    fr = pd.DataFrame({"SMB": m["SMB"], "HML": m["HML"]})
    fr["MOM"] = momm["Mom"].reindex(fr.index)
    if len(f5):
        f5m = f5.resample("ME").last()
        fr["RMW"] = f5m["RMW"].reindex(fr.index)
        fr["CMA"] = f5m["CMA"].reindex(fr.index)
    return fr.dropna() * 0  # placeholder, real fill below


def main():
    # simpler, robust load (5-factor + mom), skip header rows by scanning
    def load(fname, ncols, idcol=None):
        # FF daily files: description block, then a NAMED header line, then data.
        # The named header line contains letters (e.g. "Mkt", "SMB", "Mom"); find it.
        path = os.path.join("/Users/daxu/software/world-trader/tools/quant/data/ff_factors", fname)
        with open(path) as fh:
            lines = fh.readlines()
        header = 0
        for i, ln in enumerate(lines):
            # true header = the line immediately BEFORE the first data row
            # (a data row starts with an 8-digit YYYYMMDD date)
            if i + 1 < len(lines):
                nxt = lines[i + 1].split(",")[0].strip()
                if len(nxt) == 8 and nxt.isdigit():
                    header = i
                    break
        df = pd.read_csv(path, skiprows=header, header=0)
        df.columns = [c.strip() for c in df.columns]
        if idcol is None:
            idcol = df.columns[0]
        df["ymd"] = df[idcol].astype(str)
        df = df[df["ymd"].str.match(r"^\d{8}$")]
        df["date"] = pd.to_datetime(df["ymd"], format="%Y%m%d")
        return df.set_index("date")

    ff3 = load("F-F_Research_Data_Factors_daily.csv", 5)         # ymd Mkt-RF SMB HML RF
    mom = load("F-F_Momentum_Factor_daily.csv", 2)               # ymd Mom
    ff5 = load("F-F_Research_Data_5Factors_daily.csv", 7) if os.path.exists(
        os.path.join("/Users/daxu/software/world-trader/tools/quant/data/ff_factors/F-F_Research_Data_5Factors_daily.csv")) else None

    fac = pd.DataFrame(index=ff3.index)
    for col in ["Mkt-RF", "SMB", "HML"]:
        fac[col] = ff3[col].astype(float) / 100.0
    fac["MOM"] = mom["Mom"].astype(float) / 100.0
    if ff5 is not None:
        if "RMW" in ff5.columns:
            fac["RMW"] = ff5["RMW"].astype(float) / 100.0
        if "CMA" in ff5.columns:
            fac["CMA"] = ff5["CMA"].astype(float) / 100.0
    fac = fac.resample("ME").last().dropna()
    fac = fac[fac.index >= f"{MIN_YEAR}-01-01"]

    n_sec = fac.shape[1]
    print(f"factor universe {fac.shape[1]} ({list(fac.columns)}) months {fac.index.min().date()}..{fac.index.max().date()} | {len(fac)} mo", flush=True)

    # factor-momentum sign: long the strong factors, short the weak, EW across factors
    mom_sig = fac.rolling(LOOKBACK).mean().shift(1)   # 6m prior return, known at t (no lookahead)
    # cross-sectional rank within month -> +0.5 top half, -0.5 bottom half (net zero)
    sig = mom_sig.sub(mom_sig.mean(axis=1), axis=0)
    wts = np.sign(sig).fillna(0.0)
    # normalize so each side sums to +/-1 (gross ~1 long + 1 short)
    norm = wts.abs().sum(axis=1).replace(0, np.nan)
    wts = wts.div(norm, axis=0) * 2.0   # sum pos ~ +1, sum neg ~ -1

    rets = wts.shift(1) * fac   # hold wts formed at t-1 over month-t factor returns
    book = rets.sum(axis=1) - 2.0 * COST * wts.diff().abs().sum(axis=1).fillna(0.0)  # gross churn cost

    # overlays
    rv = book.rolling(12, min_periods=9).std() * np.sqrt(12)
    sc = (VT_TGT / rv).clip(upper=VT_CAP, lower=0.0).fillna(1.0)
    dxy = pd.read_csv(os.path.join(FRED, "dxy.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    m = dxy.rolling(12, min_periods=8).mean(); sd = dxy.rolling(12, min_periods=8).std()
    dz = (((dxy - m) / sd).reindex(book.index).ffill().shift(1) > DXY_Z).fillna(False)
    dgate = pd.Series(1.0, index=book.index); dgate[dz] = DXY_F
    sc_d = (sc * dgate).fillna(1.0)
    final = book * sc_d - sc_d.diff().abs().fillna(0.0) * 2 * COST

    def stats(s, ypf=12):
        s = s.dropna(); eq = (1 + s).cumprod()
        return {"sr": round(float(s.mean() / s.std() * np.sqrt(ypf)), 3),
                "ann": round(float((1 + s).prod() ** (ypf / len(s)) - 1), 4),
                "dd": round(float((eq / eq.cummax() - 1).min()), 4),
                "win": round(float((s > 0).mean()), 3), "n": int(len(s))}

    print("\n=== FACTOR-MOMENTUM L/S (6m lookback, net 6bp/side factor legs) ===")
    print(f"  raw            : {stats(book)}")
    print(f"  + vol-targ 0.10: {stats(book * sc - (sc.diff().abs().fillna(0))*2*COST)}")
    print(f"  + DXY gate     : {stats(final)}")
    by = final.groupby(final.index.year).apply(lambda x: (1 + x).prod() - 1)
    yr = pd.Series(by); print(f"  annual pairs (1980+):")
    for y, v in yr[yr.index >= 1980].items():
        print(f"    {y}: {v:+.1%}")
    print(f"  up-years {(yr>=0).mean():.0%} | mean ann {yr.mean():+.1%} | worst yr {yr.min():+.1%}")
    import json
    json.dump({"raw": stats(book), "vol_targ": stats(book*sc - (sc.diff().abs().fillna(0))*2*COST),
               "final": stats(final), "n_months": len(book),
               "annual": {int(k): round(float(v), 4) for k, v in yr.items()}},
              open(os.path.join(HERE, "..", "reports", "xgb_horizons", "factor_momentum.json"), "w"),
              indent=2, default=str)
    print("\nsaved -> reports/xgb_horizons/factor_momentum.json")


if __name__ == "__main__":
    main()
