"""Test multi-day overlapping hold to push Sharpe toward >=2.

Idea: instead of full daily turnover, hold a rolling book with staggered daily
entry. On each day enter the top-K (and short bottom-K) but keep prior positions
for H days (rolling). This averages overlapping positions -> smoother daily
returns, higher Sharpe IF the signal has return persistence across days.

Implementation: for each day t, compute the predicted return. A position entered
at day s with realized return rn held for H days earns sum of rn over s..s+H.
We approximate the rolling-book daily P&L by, on each day, taking the NEW entry
(this day's top-K long / bottom-K short) weighted 1/H, and carrying H-1 prior
layers each also at 1/H (equal notional across layers). This is the standard
overlapping-horizon daily P&L = (1/H) * sum_{h=0}^{H-1} signal_ret_{t-h}
where signal_ret = long_topK - short_bottomK realized that day.

So daily blended ret = rolling-mean( H ) of the per-day LS return series.
"""
import numpy as np, pandas as pd
HERE="/Users/daxu/software/world-trader/tools/quant/bigmove"
fr=pd.read_parquet(HERE+"/data/xgb_scaled_pred.parquet"); fr["date"]=pd.to_datetime(fr["date"])
live=fr.dropna(subset=["pred_ret","rn"]).copy(); COST=0.0006; K=8
# per-day LS return (correct both-leg cost), like before
rows=[]
for date,g in live.groupby("date"):
    g=g.sort_values("pred_ret",ascending=False); n=len(g)
    if n<2*K: continue
    li=g.index[:K]; si=g.index[-K:]
    rows.append((date, g.loc[li,"rn"].mean()-2*COST-(g.loc[si,"rn"].mean()-2*COST)))
ls=pd.Series(dict(rows)).sort_index()
full=ls.reindex(pd.date_range(ls.index.min(),ls.index.max(),freq="B")).fillna(0)
def stat(r):
    eq=(1+r).cumprod()
    sr=(r.mean()/r.std())*np.sqrt(252); ann=eq.iloc[-1]**(252/len(r))-1; dd=(eq/eq.cummax()-1).min()
    return sr,ann,dd
print("daily (H=1): SR=%.3f ann=%.1f%% DD=%.1f%%" % stat(full))
# overlapping H-day
for H in [3,5,10,15,20]:
    rh=full.rolling(H).mean()
    sr,ann,dd=stat(rh)
    print(f"H={H:d}: SR=%.3f ann=%.1f%% DD=%.1f%%"%stat(rh))
