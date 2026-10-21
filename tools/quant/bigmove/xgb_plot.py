import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pipeline_common import load_ohlcv

ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
HERE=os.path.dirname(os.path.abspath(__file__))
fr=pd.read_parquet(os.path.join(HERE,"data","xgb_pred_frame.parquet")); fr["date"]=pd.to_datetime(fr["date"])
P=load_ohlcv(); open_,low,close=P["open"],P["low"],P["close"]
mi=pd.MultiIndex.from_arrays([fr["date"].to_numpy(),fr["ticker"].to_numpy()],names=["date","ticker"])
def vec(df,sh=0): return df.shift(sh).stack().reindex(mi).to_numpy()
fr["next_open"]=vec(open_,-1); fr["next_low"]=vec(low,-1)
fr=fr.dropna(subset=["next_open","next_low"])
COST=0.0006
live=fr[fr["pred_ret"].notna()].copy()
q=0.99; sp=0.10
cut=live["pred_ret"].quantile(q); d=live[live["pred_ret"]>=cut].copy()
entry=d["entry"].to_numpy(); op=d["next_open"].to_numpy(); lo=d["next_low"].to_numpy(); nc=d["next_close"].to_numpy()
stop=entry*(1-sp)
exit_px=np.where(op<=stop,op,np.where(lo<=stop,stop,nc))
gross=exit_px/entry-1; net=gross-2*COST
d["net"]=net
daily=d.groupby("date")["net"].mean().reindex(fr["date"].unique(),fill_value=0).sort_index()
eq=(1+daily).cumprod()
# SPY
spy=pd.read_csv(os.path.join(ROOT,"tools/quant/data/twelve_big","SPY.csv"),parse_dates=["date"]).set_index("date")["close"]
spy=spy.reindex(eq.index).dropna(); spy_eq=spy/spy.iloc[0]
plt.figure(figsize=(12,6))
plt.plot(eq.index,eq.values,label="XGB top-1% + 10% stop")
plt.plot(spy_eq.index,spy_eq.values,label="SPY buy&hold",color="black",alpha=0.7)
plt.yscale("log"); plt.title("XGB-regression big-move strategy (OOS 2018-2026, calendar-time, 6bp) vs SPY")
plt.legend(); plt.grid(True,which="both",alpha=0.3); plt.tight_layout()
plt.savefig(os.path.join(OUT,"bigmove_xgb_equity_vs_spy.png"),dpi=110)
print("saved:",os.path.join(OUT,"bigmove_xgb_equity_vs_spy.png"))
# save daily book
(pd.DataFrame({"date":eq.index,"eq":eq.values})).to_csv(os.path.join(OUT,"bigmove_xgb_best_equity.csv"),index=False)
print("saved equity csv")
