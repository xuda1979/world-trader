"""Correct T+1 Turtle simulator. Signals decided on close of day i (entry/exit/stop/pyramid),
position applies from close_i to close_{i+1} (T+1 execution, NO same-day leak).
Returns (gross_daily, pos_units, turnover). Cost applied at portfolio level.
"""
import numpy as np, pandas as pd

def sim_market(px, entry=20, exit_len=10, n_len=20, max_units=4, point_value=1.0):
    high=px['high'].astype(float); low=px['low'].astype(float); close=px['close'].astype(float)
    prev_c=close.shift(1)
    tr=pd.concat([(high-low),(high-prev_c).abs(),(low-prev_c).abs()],axis=1).max(axis=1)
    N=tr.ewm(span=n_len,adjust=False).mean()
    # prior-period channels (exclude today's bar)
    eh=high.shift(1).rolling(entry).max()
    el=low.shift(1).rolling(entry).min()
    xl=low.shift(1).rolling(exit_len).min()
    xh=high.shift(1).rolling(exit_len).max()
    idx=close.index; n=len(idx)
    pos_arr=np.zeros(n); gross=np.zeros(n); turn=np.zeros(n)
    tiers=[]  # list of (sign, entry_price, best_high_or_best_low, stop)
    pos_int=0
    for i in range(1,n):
        c=close.iloc[i]; h=high.iloc[i]; l=low.iloc[i]; nv=N.iloc[i]
        # 1) update tier stops + apply stops/exits with TODAY's bar (info<=i), position will earn i+1
        new_tiers=[]
        for tr_ in tiers:
            sign,ep,best,stop=tr_
            if sign==1:
                nh=max(best,h); nstop=nh-2*nv if not np.isnan(nv) else stop
                if l<=nstop: continue  # stopped out today
                new_tiers.append((sign,ep,nh,nstop))
            else:
                nl=min(best,l); nstop=nl+2*nv if not np.isnan(nv) else stop
                if h>=nstop: continue
                new_tiers.append((sign,ep,nl,nstop))
        tiers=new_tiers
        # 2) exits today (System: long exits below 10d low)
        if pos_int>0 and not np.isnan(xl.iloc[i]) and c<xl.iloc[i]:
            tiers=[t_ for t_ in tiers if t_[0]!=1]
        if pos_int<0 and not np.isnan(xh.iloc[i]) and c>xh.iloc[i]:
            tiers=[t_ for t_ in tiers if t_[0]!=-1]
        # 3) entry if flat (breakout of prior channel)
        if len(tiers)==0:
            if not np.isnan(eh.iloc[i]) and not np.isnan(nv) and c>eh.iloc[i]:
                tiers=[(1,c,h,c-2*nv)]
            elif not np.isnan(el.iloc[i]) and not np.isnan(nv) and c<el.iloc[i]:
                tiers=[(-1,c,l,c+2*nv)]
        # 4) pyramid: add tier when price 0.5N past last tier entry
        elif len(tiers)<max_units and not np.isnan(nv):
            last=tiers[-1]
            if last[0]==1 and c>=last[1]+0.5*nv:
                tiers.append((1,c,h,c-2*nv))
            elif last[0]==-1 and c<=last[1]-0.5*nv:
                tiers.append((-1,c,l,c+2*nv))
        pos_int=sum(t_[0] for t_ in tiers)
        pos_arr[i]=float(pos_int)
        turn[i]=float(abs(pos_int-pos_arr[i-1]))
    # T+1 P&L: position decided on day i-1 applies to close_i-close_{i-1}
    close_chg=close.diff().values
    g=np.concatenate([[0.0], pos_arr[:-1]*close_chg[1:]])
    return pd.Series(g,index=idx), pd.Series(pos_arr,index=idx), pd.Series(turn,index=idx)
