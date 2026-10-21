"""OVNCAP family: decomposition-matched overnight harvest.
book(pos_on, pos_ic): net = sum(pos_on*on) + sum(pos_ic*ic) - costs - borrow on shorts.
OVNCAP_k_lb: pos_on = xs LS (+1/k top-k by ON-lb mean, -1/k bottom-k); pos_ic = -pos_on.
  => earns sum(pos_on*(on - ic)): long overnight spread, short intraday spread, same names.
All decided at t close, earn t->t+1 (T+1), 6.4bps/side per stream turnover, borrow 0.5%/yr.
"""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()

def book_net(pos_on, pos_ic):
    """two-stream net with T+1 shift, per-stream turnover costs, borrow on shorts."""
    common=on.index
    p1=pos_on.reindex(common).fillna(0.0).shift(1).fillna(0.0)
    p2=pos_ic.reindex(common).fillna(0.0).shift(1).fillna(0.0)
    r1=on.reindex(common).fillna(0.0); r2=ic.reindex(common).fillna(0.0)
    gross=(p1*r1).sum(axis=1)+(p2*r2).sum(axis=1)
    turn=((p1.diff().abs().sum(axis=1))+(p2.diff().abs().sum(axis=1)))/2.0
    bor=(p1.clip(upper=0).abs().sum(axis=1)+p2.clip(upper=0).abs().sum(axis=1))*H.BORROW
    net=(gross-turn*H.COST-bor).dropna()
    return net, p1, p2

def st1(tag,net):
    net=net[net.index>=pd.Timestamp('2008-01-01')]
    st=H.full_stats(net)
    print(f"{tag}: SR {st['sr']:.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']}/{st['years']} worst {st['worst']*100:+.1f}%")
    return st

print('=== OVNCAP: pos_ic = -pos_on (overnight-spread long, intraday-spread short) ===')
for lb in [21,63,126]:
    sig=on.rolling(lb,min_periods=max(2,lb//3)).mean()
    for k in [15,25,50]:
        pos=H.xs_ls(sig,k=k)
        net,_,_=book_net(pos,-pos)
        st1(f'OVNCAP lb{lb} k{k}',net)
print()
print('=== one-sided pieces at lb63 k25 (drift controls) ===')
sig=on.rolling(63,min_periods=21).mean()
posLS=H.xs_ls(sig,k=25)
longonly=pd.DataFrame(np.where((sig.rank(axis=1,ascending=False)<=25)&sig.notna(),1/25,0.0),index=sig.index,columns=sig.columns)
shortonly=pd.DataFrame(np.where((sig.rank(axis=1,ascending=False)>=(sig.notna().sum(axis=1).values[:,None]-24))&sig.notna(),-1/25,0.0),index=sig.index,columns=sig.columns)
st1('TOP25: +ON only', book_net(longonly,pd.DataFrame(0.0,index=on.index,columns=on.columns))[0])
st1('TOP25: -IC only (short ic)', book_net(pd.DataFrame(0.0,index=on.index,columns=on.columns),-longonly)[0])
st1('BOT25: -ON only', book_net(shortonly,pd.DataFrame(0.0,index=on.index,columns=on.columns))[0])
st1('BOT25: +IC only', book_net(pd.DataFrame(0.0,index=on.index,columns=on.columns),-shortonly)[0])
print()
print('=== OVNCAP mirror control: pos_ic = +pos_on (should kill edge if ON/IC split is real) ===')
net,_,_=book_net(posLS,posLS); st1('CONTROL pos_ic=+pos_on lb63 k25',net)
