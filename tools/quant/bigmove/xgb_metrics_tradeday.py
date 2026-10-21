"""Recompute metrics using the CORRECT methodology:
  - mean/std computed over TRADED (active) days only
  - annualized by sqrt(ACTIVE TRADING DAYS PER YEAR)
Annual return and maxDD computed over the ACTIVE-day equity curve.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from pipeline_common import load_ohlcv

ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
HERE=os.path.dirname(os.path.abspath(__file__))
COST=0.0006
fr=pd.read_parquet(os.path.join(HERE,"data","xgb_pred_frame.parquet")); fr["date"]=pd.to_datetime(fr["date"])
P=load_ohlcv(); open_,low,close=P["open"],P["low"],P["close"]
mi=pd.MultiIndex.from_arrays([fr["date"].to_numpy(),fr["ticker"].to_numpy()],names=["date","ticker"])
def vec(df,sh=0): return df.shift(sh).stack().reindex(mi).to_numpy()
fr["next_open"]=vec(open_,-1); fr["next_low"]=vec(low,-1)
fr=fr.dropna(subset=["next_open","next_low"])
live=fr[fr["pred_ret"].notna()].copy()

def exit_logic(entry,op,lo,cl,sp):
    stop=entry*(1-sp); px=np.where(op<=stop,op,np.where(lo<=stop,stop,cl))
    return (px/entry-1)-2*COST

def tradeday_metrics(d, sp):
    """mean/std over ACTIVE days; ann ret & maxDD over active-day equity."""
    net=exit_logic(d["entry"].to_numpy(),d["next_open"].to_numpy(),d["next_low"].to_numpy(),d["next_close"].to_numpy(),sp)
    daily=pd.Series(net,index=d["date"]).groupby(level=0).mean().sort_index()
    n_active=len(daily)
    # span in years from first to last active date
    y0,y1=daily.index.min(),daily.index.max()
    years=max((y1-y0).days/365.25,1/252)
    # active trading days per year
    active_per_year=n_active/years
    mu=daily.mean(); sig=daily.std()
    sharpe_active=(mu/sig)*np.sqrt(active_per_year) if sig>0 else 0.0
    eq=(1+daily).cumprod()
    ann=(eq.iloc[-1])**(1/years)-1
    dd=(eq/eq.cummax()-1).min()
    return mu,sig,n_active,active_per_year,sharpe_active,ann,dd

print(f"{'config':<26}{'mu/day':>9}{'sigma':>8}{'nAct':>6}{'act/yr':>8}{'SR(active)':>11}{'annRet':>9}{'MaxDD':>8}")
rows=[]
for q in [0.99,0.995,0.997]:
    cut=live["pred_ret"].quantile(q); d=live[live["pred_ret"]>=cut]
    for sp in [0.0,0.05,0.10]:
        mu,sig,na,apy,sr,ann,dd=tradeday_metrics(d,sp)
        rows.append((f"top{1-q:.3f}/stop{int(sp*100)}",mu,sig,na,apy,sr,ann,dd))
for r in rows:
    print(f"{r[0]:<26}{r[1]:9.4%}{r[2]:8.4%}{r[3]:6d}{r[4]:8.0f}{r[5]:11.2f}{r[6]:8.2%}{r[7]:8.2%}")

# capture as json
res={r[0]:{"mean_daily":float(r[1]),"std_daily":float(r[2]),"n_active_days":int(r[3]),
          "active_days_per_year":round(float(r[4]),1),"active_sharpe":round(float(r[5]),3),
          "ann_return":round(float(r[6]),4),"max_dd":round(float(r[7]),4)} for r in rows}
with open(os.path.join(OUT,"bigmove_xgb_tradeday_metrics.json"),"w") as f: json.dump(res,f,indent=2)
print("\nsaved ->", os.path.join(OUT,"bigmove_xgb_tradeday_metrics.json"))
