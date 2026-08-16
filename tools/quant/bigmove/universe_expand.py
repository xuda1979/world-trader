"""Build an expanded universe: long-history US equities (twelve_big+twelve_liq+
twelvedata union) + non-correlated assets (crypto BTC/ETH, FX, commodities from
data_fred). Returns an OHLCV-like panel dict P = {open,high,low,close,vol} date x
ticker, all share one index. Excludes ETFs/ADRs/indexes.
"""
from __future__ import annotations
import os, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"; DATA=os.path.join(ROOT,"tools/quant/data")
FRED=os.path.join(ROOT,"tools/quant/hedge_fund_strats","data_fred")
MAX_HISTORY=1300  # only include names with >=5 yrs history (need 3y train)

BLOCK={"QQQ","SPY","XLF","XLK","XLV","XLI","XLY","XLP","XLC","XLU","XLRE","XLB",
       "DIA","IWM","VTI","VOO","ASML","HMC","TM","XYZ"}

def _read_ohlcv(path):
    df=pd.read_csv(path,parse_dates=["date"]).sort_values("date").drop_duplicates("date")
    df=df.set_index("date")
    for c in ["open","high","low","close"]: df[c]=pd.to_numeric(df[c],errors="coerce")
    df["vol"]=pd.to_numeric(df.get("vol"),errors="coerce")
    return df

def load_us_equities():
    series={}
    for d in ["twelve_big","twelve_liq","twelvedata"]:
        for fn in os.listdir(os.path.join(DATA,d)):
            if not fn.endswith(".csv"): continue
            sym=fn[:-4]
            if sym in BLOCK: continue
            p=os.path.join(DATA,d,fn)
            if sum(1 for _ in open(p))-1 < MAX_HISTORY: continue
            df=_read_ohlcv(p)
            if len(df)<MAX_HISTORY: continue
            # prefer the longest-history source if dup
            if sym in series and len(series[sym])>=len(df): continue
            series[sym]=df
    return series

def load_non_eq():
    """Non-correlated assets as synthetic 'tickers' with full OHLCV-shaped rows."""
    series={}
    # crypto
    for c in ["BTC","ETH"]:
        p=os.path.join(DATA,"binance",f"{c}.csv")
        if os.path.exists(p):
            df=_read_ohlcv(p); series[c]=df
    # FX
    for c in ["EUR_USD","GBP_USD","USD_JPY","USD_CAD","AUD_USD","USD_CHF"]:
        p=os.path.join(DATA,"fx",f"{c}.csv")
        if os.path.exists(p):
            df=_read_ohlcv(p); df["vol"]=0.0; series[c]=df
    # commodities & macro from data_fred (close/level as 'close', vol 0)
    for c in ["brent","natgas","slv"]:
        p=os.path.join(FRED,f"{c}.csv")
        if os.path.exists(p):
            df=pd.read_csv(p,parse_dates=["date"]).set_index("date")
            v=df.iloc[:,0]
            v=pd.to_numeric(v,errors="coerce")
            out=pd.DataFrame(index=pd.to_datetime(v.index))
            out["close"]=v; out["open"]=out["high"]=out["low"]=v; out["vol"]=0.0
            series["FRED_"+c]=out
    return series

def build_panel():
    eq=load_us_equities(); nq=load_non_eq()
    all_series={**eq,**nq}
    # align to common index (intersection start => union end), need >= min obs after align
    # build per-field concat on inner-index-over-time but outer over series
    dts=[s.index for s in all_series.values()]
    dts=[pd.DatetimeIndex(d) for d in dts]
    idx=pd.DatetimeIndex(sorted(set().union(*[set(d) for d in dts])))
    frames={f:{} for f in ["open","high","low","close","vol"]}
    for sym,df in all_series.items():
        for f in ["open","high","low","close","vol"]:
            frames[f][sym]=df[f]
    P={f:pd.DataFrame(frames[f],index=idx).sort_index() for f in ["open","high","low","close","vol"]}
    return P, len(eq), len(nq)

if __name__=="__main__":
    P,neq,nnq=build_panel()
    print(f"expanded universe: {P['close'].shape[1]} total = {neq} US equities + {nnq} non-equity")
    print(f"date range: {P['close'].index.min().date()} .. {P['close'].index.max().date()}")
    print("sample:", list(P['close'].columns)[:10])
    # correlation structure: avg pairwise corr of daily returns among equities
    dr=P['close'].pct_change()
    eqcols=[c for c in dr.columns if not c.startswith(('FRED','BTC','ETH','EUR','GBP','USD'))]
    mc=dr[eqcols[:50]].corr().values
    tri=np.triu(mc,1); print(f"avg pairwise US-equity daily-ret corr: {tri[tri!=0].mean():.3f}")
