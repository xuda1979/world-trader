"""GKX-style monthly cross-sectional ML replication (best efforts, free data).

Monthly characteristic panel from free data:
  - technicals (local daily prices): momentum 1/3/6/12m, 12-1, vol, maxDD,
    Amihud, 52w hi/lo distance, beta, idio vol, RSI, skew/kurt, volume z
  - fundamentals (Finnhub stock/metric, current snapshot): size, PE, PB, ROE,
    rev/eps growth, asset turnover, debt/equity, div yield
  - earnings (local earnings_panel): surprise (ffill), days-to-earnings
  - macro state + interactions (FRED): vix z, mkt 3m ret, credit z, and
    momentum x macro interactions (GKX-style)
Models: Ridge (linear baseline), XGBoost GBRT, MLP (3-layer NN).
Validation: PURGED walk-forward (train on months <= m-1 to predict month m+1
return), yearly refit on rolling 7y window. Decile long/short, EW + cap-weight,
gross AND net (6bp/side full cycle 24bp/mo). 20y OOS 2008-2026.
"""
from __future__ import annotations
import os, sys, json, pickle, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault("DYLD_LIBRARY_PATH","/Users/daxu/homebrew/opt/libomp/lib:"+os.environ.get("DYLD_LIBRARY_PATH",""))
import pipeline_common as pc
from xgb_horizon_ddfilter import _load
ROOT="/Users/daxu/software/world-trader"

def build_monthly_panel(P, finn, earn_panel, macro):
    close=P["close"]
    mclose=close.resample("ME").last()
    mret=mclose.pct_change()
    F={}
    for lag,cols in [(1,"m1"),(3,"m3"),(6,"m6"),(12,"m12")]:
        F[f"ret_{cols}"]=mclose.pct_change(lag)
    F["ret_12_1"]=F["ret_m12"]-F["ret_m1"]
    # vol from daily within month
    dret=close.pct_change()
    mvol=dret.resample("ME").std()
    F["vol_m3"]=mvol.rolling(3,min_periods=2).mean(); F["vol_m12"]=mvol.rolling(12,min_periods=6).mean()
    # max drawdown over trailing 12m (daily)
    eq=close; mdd=(eq/eq.rolling(252).max()-1).resample("ME").last()
    F["maxdd_12m"]=mdd
    # amihud monthly avg
    amihud=(dret.abs()/(close*P["vol"]).replace(0,np.nan)).resample("ME").mean()
    F["amihud_3m"]=amihud.rolling(3).mean()
    # 52w hi/lo distance
    F["dist_hi252"]=close/close.rolling(252).max()-1
    F["dist_lo252"]=close/close.rolling(252).min()-1
    F["dist_hi252"]=F["dist_hi252"].resample("ME").last(); F["dist_lo252"]=F["dist_lo252"].resample("ME").last()
    # volume z
    F["vol_z"]=((P["vol"]-P["vol"].rolling(252).mean())/P["vol"].rolling(252).std()).resample("ME").last()
    # skew/kurt monthly
    F["skew_m3"]=dret.resample("ME").apply(lambda x: x.skew()).rolling(3).mean(); F["kurt_m3"]=dret.resample("ME").apply(lambda x: x.kurt()).rolling(3).mean()
    # beta to SPY
    spy=pd.read_csv(f"{ROOT}/tools/quant/data/twelve_big/SPY.csv",parse_dates=["date"]).set_index("date")["close"]
    spyr=spy.pct_change()
    cov=dret.rolling(63).cov(spyr); var=spyr.rolling(63).var().replace(0,np.nan)
    F["beta_12m"]=(cov.div(var,axis=0)).resample("ME").last()
    xs_disp=(dret.sub(dret.mean(axis=1),axis=0).std(axis=1)).resample("ME").std().rolling(3).mean()
    F["idio_vol_m3"]=pd.DataFrame({s:xs_disp for s in close.columns},index=mclose.index)
    # fundamentals (current snapshot tiled back as constant per name)
    for k in ["marketCap","pe","pb","roe","rev_growth","eps_growth","asset_turn","debt_eq","div_yield"]:
        col={}
        for s,info in finn.items():
            if s not in close.columns or info.get("error"): continue
            v=info.get(k)
            if v is None or (isinstance(v,float) and (v!=v)): continue
            col[s]=float(v)
        ser=pd.Series(col)
        F[k]=pd.DataFrame({s:ser.get(s,np.nan) for s in close.columns},index=mclose.index)
    # earnings: last surprise ffill + days to next (entries are dicts w/ 'date')
    surp=pd.DataFrame(np.nan,index=mclose.index,columns=close.columns)
    dnext=pd.DataFrame(np.nan,index=mclose.index,columns=close.columns)
    for s,dates in earn_panel.items():
        if s not in close.columns or not dates: continue
        try:
            ts=[pd.Timestamp(e['date']) for e in dates]
        except (TypeError, KeyError):
            ts=[pd.Timestamp(e) for e in dates]
        sv=pd.Series({ts[i]: (dates[i].get('surprise_prc') if isinstance(dates[i],dict) else np.nan)
                      for i in range(len(ts))})
        surp[s]=sv.reindex(mclose.index,method='ffill')
        dnext[s]=mclose.index.to_series().map(lambda dt: min([(d-dt).days for d in ts if d>dt],default=np.nan))
    F["earn_surp"]=surp; F["earn_dnext"]=dnext
    # macro state + interactions
    vixz=macro["vixz"].reindex(mclose.index); mk3=macro["mkt3"].reindex(mclose.index)
    F["vix_z"]=pd.DataFrame({s:vixz for s in close.columns},index=mclose.index)
    F["mkt_ret_3m"]=pd.DataFrame({s:mk3 for s in close.columns},index=mclose.index)
    F["ret_12_x_vix"]=F["ret_m12"].mul(vixz,axis=0)
    F["ret_6_x_mkt"]=F["ret_m6"].mul(mk3,axis=0)
    F["vol_x_vix"]=F["vol_m3"].mul(vixz,axis=0)
    # log size
    F["log_mcap"]=np.log(F["marketCap"].replace(0,np.nan))
    # stack into long frame
    names=sorted(F.keys())
    idx=mclose.index; cols=close.columns
    parts=[F[k].loc[idx,cols].stack().rename(k) for k in names]
    df=pd.concat(parts,axis=1)
    df.index.names=["month","ticker"]
    df=df.reset_index()
    df["ret_next"]=mret.stack().shift(-1).reindex(pd.MultiIndex.from_frame(df[["month","ticker"]])).to_numpy() if False else None
    # forward next-month return
    mret_long=mret.stack(); mret_long.index.names=["month","ticker"]
    mi=pd.MultiIndex.from_frame(df[["month","ticker"]])
    df["ret_next"]=mret_long.shift(-1).reindex(mi).to_numpy()
    # SANITY: exclude penny stocks (median month-end close < $2, untradable at
    # size) and extreme monthly returns (data errors / split artifacts).
    medprice=mclose.median()
    keep_tk=set(medprice[medprice>=2.0].index)
    df=df[df["ticker"].isin(keep_tk)]
    df=df[(df["ret_next"]>=-0.95)&(df["ret_next"]<=2.5)]
    return df, names

def main():
    P=pc.load_ohlcv()
    finn=json.load(open(f"{HERE}/data/finnhub_metrics.json"))
    earn={}
    import glob
    for fp in glob.glob(f"{HERE}/data/earnings_panel/*.json"):
        s=os.path.basename(fp)[:-5]; earn[s]=json.load(open(fp))
    vix=_load("vix.csv"); spx=_load("spx.csv")
    vixz=(vix-vix.rolling(252).mean())/vix.rolling(252).std()
    macro={"vixz":vixz,"mkt3":spx.pct_change(63)}
    print("building monthly panel...",flush=True)
    df,names=build_monthly_panel(P,finn,earn,macro)
    print(f"panel: {df.shape} | {len(names)} characteristics | months {df['month'].min().date()}..{df['month'].max().date()}",flush=True)
    df.to_parquet(f"{HERE}/data/gkx_monthly_panel.parquet")
    json.dump(names,open(f"{HERE}/data/gkx_names.json","w"))
    print("saved panel",flush=True)

if __name__=="__main__":
    main()
