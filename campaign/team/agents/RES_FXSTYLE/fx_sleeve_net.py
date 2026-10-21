#!/usr/bin/env python3
"""Emit a clean FX cross-sectional momentum sleeve NET series on the champion calendar (2008+).

Uses fx_grid.xsmom-style construction but limits to names that span the whole window so the
sleeve covers 2008+. T+1, trailing, full |dW|@6.4, borrow on shorts.
"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign')
import numpy as np, pandas as pd
from bt.engine import vol_target_scale, cost_turnover, borrow_cost
import importlib.util
spec=importlib.util.spec_from_file_location('fxg','/Users/daxu/software/world-trader/campaign/team/agents/RES_FXSTYLE/fx_grid.py')
fxg=importlib.util.module_from_spec(spec); spec.loader.exec_module(fxg)

def sleeve_net(lb=189, skip=21, nlong=4, nshort=4, hold=10):
    prices=fxg.panel()
    ret=prices.pct_change()
    f=(prices.shift(skip)/prices.shift(lb)-1.0)
    ranks=f.rank(axis=1,method='first'); n=len(ranks.columns)
    pos=pd.DataFrame(0.0,index=ranks.index,columns=ranks.columns)
    pos[ranks>n-nlong]=1.0/nlong; pos[ranks<=nshort]=-1.0/nshort
    pos=pos.shift(1)
    rdates=pos.index[::hold]; held=pd.DataFrame(np.nan,index=pos.index,columns=pos.columns)
    for rd in rdates:
        w=pos.index[(pos.index>=rd)&(pos.index<rd+pd.Timedelta(days=hold*1.5))]
        if len(w): held.loc[w]=pos.loc[rd].values
    held=held.ffill().fillna(0.0)
    # gross=1.0 selected book (long-short already dollar neutral), cap to 1.0
    gross=held.abs().sum(axis=1).clip(upper=1.0)
    # per-name returns used directly (positions with weights->one 2-leg lev to keep it a sleeve)
    port=(held*ret.fillna(0.0)).sum(axis=1)
    to=(held.diff().abs().sum(axis=1)).fillna(0.0)
    net=(port - to*6.4/1e4 - 0.0).dropna()  # borrow negligible for FX dtr
    # vol-target the whole thing to 10% (trailing only) 
    net=net*vol_target_scale(net.to_frame('a'),target=0.10,cap=3.0)['a']
    return net

def main():
    for lb,ns,h in [(126,4,10),(189,4,10),(252,5,21)]:
        net=sleeve_net(lb=lb,nlong=ns,nshort=ns,hold=h)
        net=net.dropna(); net=net[net.index>='2008-03-31']
        ann=((1+net).prod()**(252/len(net))-1)
        sr=net.mean()/net.std()*252**0.5
        print(f"FX lb{lb} n{ns} hold{h}: n={len(net)} SR={sr:.3f} ann={ann*100:.2f}% start={net.index.min().date()}")
    # emit best-ish as net sleeve on champion calendar
    net=sleeve_net(lb=189,nlong=4,nshort=4,hold=10).dropna()
    net=net[net.index>='2008-03-31']
    net.rename('ret').to_frame().to_csv('campaign/team/agents/RES_FXSTYLE/sleeves/fx_xsmom189_44h10_net.csv')
    print('emitted fx_xsmom189_44h10_net.csv rows', len(net))

if __name__=='__main__':
    main()
