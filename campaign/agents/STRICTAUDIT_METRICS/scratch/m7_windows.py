# m7: window-DD claim verification (job 3)
import pandas as pd, numpy as np
CSV="/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
r=pd.read_csv(CSV,index_col=0,parse_dates=True)['ret'].dropna()
eq=(1+r).cumprod()

# (a) full-series MaxDD
dd=eq/eq.cummax()-1
print(f"full MaxDD = {dd.min()*100:.3f}% (trough {dd.idxmin().date()}) [claim -6.1%]")

# (b) every 3y subwindow: rolling 756-row windows (stride 21 for report; ALL windows checked exactly)
W=756
worst=0.0; worst_start=None; n_win=0; viol=[]
vals=[]
for i in range(0, len(r)-W+1):
    w=eq.iloc[i:i+W+1].values  # W returns -> W+1 points? use returns i..i+W-1, eq from them
    wret=r.iloc[i:i+W].values
    e=np.cumprod(1+wret); pk=np.maximum.accumulate(e); mdd=((e/pk)-1).min()
    n_win+=1
    vals.append(mdd)
    if mdd<worst: worst=mdd; worst_start=r.index[i]
vals=np.array(vals)
print(f"\n3y rolling windows (756 rows, stride 1): n={n_win}")
print(f"  worst 3y-window DD = {worst*100:.3f}%  (window starting {worst_start.date()})")
print(f"  claim 'every 3y window DD <= -6.1% (i.e., no window worse than -6.1%)' -> windows worse than -6.05%: {(vals < -0.0605).sum()}")
print(f"  windows worse than -6.1%: {(vals < -0.061).sum()}")
print(f"  distribution: p1={np.percentile(vals,1)*100:.2f}% p5={np.percentile(vals,5)*100:.2f}% median={np.median(vals)*100:.2f}%")

# (c) calendar-year DDs
print("\ncalendar-year DDs:")
viol_y=[]
for y in sorted(r.index.year.unique()):
    x=(1+r[r.index.year==y]).cumprod()
    d=((x/x.cummax())-1).min()
    flag=" <-- WORSE than -6.1%" if d < -0.061 else ""
    if d<-0.061: viol_y.append(y)
    print(f"  {y}: {d*100:7.2f}%{flag}")
print(f"calendar years with DD worse than -6.1%: {viol_y}  [claim: none]")

# (d) also check: does any 2-year or 1-year window break -6.1%?
for W2,label in [(252,"1y"),(504,"2y")]:
    wv=[]
    for i in range(0,len(r)-W2+1):
        wret=r.iloc[i:i+W2].values
        e=np.cumprod(1+wret); pk=np.maximum.accumulate(e); wv.append(((e/pk)-1).min())
    wv=np.array(wv)
    print(f"rolling {label} windows: worst DD={wv.min()*100:.2f}%; windows worse than -6.1%: {(wv<-0.061).sum()}")
