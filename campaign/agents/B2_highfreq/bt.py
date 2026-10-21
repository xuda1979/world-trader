"""Shared backtest helper for B2_highfreq. Proper portfolio math + turnover."""
import numpy as np, pandas as pd
from campaign.harness.data import closes
COST = 6.0/1e4

def load_px(min_start='2008-01-01'):
    px = closes()
    px = px[px.index >= min_start]
    return px

def turnover_from_pos(pos):
    """One-side turnover per $1 NAV (gross exposure). pos: weights (long positive, short negative) summing position values.
    NAV=1. Gross exposure = |pos|.sum over names. One-side traded daily ~ sum|diff| of weights across names / 2."""
    diff = pos.diff().abs().sum(axis=1) / 2.0
    return diff

def backtest(px, pos, vt_ann=0.10):
    """pos: weight matrix (long +1/k, short -1/k), defined at t using data<=t.
    Returns executed t+1. Applies costs from actual turnover."""
    fwd = px.pct_change(1).shift(-1)
    valid = px.notna() & fwd.notna()
    pos = pos.where(valid, 0.0)
    gr = (pos*fwd).sum(axis=1)  # gross daily return, NAV=1, dollar-neutral $\sum pos=0$
    # turnover: one-side traded / $1 nav per day
    tup = turnover_from_pos(pos)
    net = gr - tup*COST
    # also vol target using trailing only
    # (kept simple in caller)
    return net, gr, tup

if __name__=='__main__':
    px = load_px()
    for L in [1,2,3,5,10]:
        past = px.pct_change(L)
        rank = past.rank(axis=1, na_option='keep')
        n=px.shape[1]
        k=20
        long_mask=(rank<=k); short_mask=(rank>(n-k))
        pos=pd.DataFrame(0.0,index=px.index,columns=px.columns)
        pos[long_mask]=1.0/k; pos[short_mask]=-1.0/k
        net,gr,tup=backtest(px,pos)
        mu,sd=net.mean(),net.std(); sr=mu/sd*np.sqrt(252) if sd>0 else 0
        eq=(1+net).cumprod(); dd=(eq/eq.cummax()-1).min()
        gmu,gsd=gr.mean(),gr.std(); gsr=gmu/gsd*np.sqrt(252) if gsd>0 else 0
        print(f"L={L} k=20: SR={sr:.2f} ann={mu*252*100:.1f}% GrossSR={gsr:.2f} turn/day={tup.mean():.2f} MaxDD={dd*100:.1f}%")
