"""HALF-TRADEABLE decomposition: earn ON stream on close-position (correct: buy at close,
earn open_{t+1}->? NO — you can only earn on if you sell at next open). REALISTIC halves:
(A) 'sell-at-open' book: pos decided close_t, exit at open_{t+1}: earns on_{t+1} exactly. COST:
    buy close_t -> sell open_{t+1} = 2 legs/day (full round trip daily). 6.4bps x (|w| entries+exits).
    This IS tradeable if we charge entry+exit daily. vs OVNCAP which also earned -w*ic leg.
(B) 'buy-at-open' book: earn ic_{t+1}: buy open, sell close: same daily round-trip costs.
Both earn 'decomposition' streams but WITH daily round-trip costs charged on gross |w|.
Benchmark: EW-long ON with daily round trip (overnight drift harvest) — the classic premium.
"""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()

def rt_net(pos, ret, roundtrip=True):
    """pos decided at t, earns ret_{t+1} = shift(1). If roundtrip: assume entry+exit each day
    for every unit of |pos| (positions are rebuilt daily at the needed times):
    turnover = |pos| (entry) + |pos| (exit) => one-side = |pos| per day. Additionally position
    CHANGES matter if kept overnight — we take the conservative max of both conventions."""
    p=pos.shift(1).fillna(0.0)
    r=ret.reindex(p.index).fillna(0.0)
    chg=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    gross_rt=(p.abs().sum(axis=1))   # one-side notional per day for daily round trip
    turn=np.maximum(chg, gross_rt) if roundtrip else chg
    bor=p.clip(upper=0).abs().sum(axis=1)*H.BORROW
    return (p.mul(r).sum(axis=1)-turn*H.COST-bor).dropna()

def st1(tag,net):
    net=net[net.index>=pd.Timestamp('2008-01-01')]
    st=H.full_stats(net)
    print(f"{tag}: SR {st['sr']:.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']}/{st['years']} worst {st['worst']*100:+.1f}%")
    return st

lb,k=126,25
sig=on.rolling(lb,min_periods=lb//3).mean()
posL=H.xs_ls(sig,k=k)
print('=== (A) sell-at-open ON book WITH daily round-trip costs ===')
st1(f'ON126 top25/bot25 L/S @ON + RT costs', rt_net(posL,on))
print()
print('=== (B) buy-at-open IC book WITH daily round-trip costs ===')
st1(f'IC side -pos @IC + RT costs', rt_net(-posL,ic))
print()
print('=== benchmark: EW-long overnight harvest with daily RT (classic premium) ===')
nval=on.notna().sum(axis=1)
w=pd.DataFrame(np.where(on.notna(),1.0,0.0),index=on.index,columns=on.columns).div(nval,axis=0)
st1('EW-long ON + RT costs', rt_net(w,on))
st1('EW-long ON, hold-only costs', rt_net(w,on,roundtrip=False))
print()
print('=== OVNCAP honest-cost variant: both streams + full daily RT on both ===')
p=posL
n1=rt_net(p,on); n2=rt_net(-p,ic)
st1('OVNCAP honest (ON+(-IC) streams, RT both)', n1+n2)
