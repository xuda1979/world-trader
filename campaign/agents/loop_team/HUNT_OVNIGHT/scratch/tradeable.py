"""TRADEABLE family: positions decided at close_t, held to close_{t+1}; PnL = w * cc_{t+1}.
Costs: 6.4bps/side on close-position changes only (correct for close-to-close holds).
Benchmark: plain cc momentum. All 2008+ naive first, then gates on survivors."""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
O=pd.read_pickle('scratch/O.pkl'); C=pd.read_pickle('scratch/C.pkl')
cc=(C/C.shift(1)-1.0).where(on.notna())

def cc_net(pos):
    p=pos.shift(1).fillna(0.0)
    r=cc.reindex(p.index).fillna(0.0)
    turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    bor=p.clip(upper=0).abs().sum(axis=1)*H.BORROW
    return (p.mul(r).sum(axis=1)-turn*H.COST-bor).dropna()

def st1(tag,net):
    net=net[net.index>=pd.Timestamp('2008-01-01')]
    st=H.full_stats(net)
    print(f"{tag}: SR {st['sr']:.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']}/{st['years']} worst {st['worst']*100:+.1f}%")
    return st

print('=== OVNcc: signal=ON-mean, trade close-to-close ===')
for lb in [21,63,126,252]:
    sig=on.rolling(lb,min_periods=max(2,lb//3)).mean()
    for k in [15,25,50]:
        pos=H.xs_ls(sig,k=k)
        st1(f'OVNcc lb{lb} k{k}',cc_net(pos))
print()
print('=== benchmark: plain cc momentum L/S ===')
for lb in [21,63,126,252]:
    sig=cc.rolling(lb,min_periods=max(2,lb//3)).mean()
    pos=H.xs_ls(sig,k=25)
    st1(f'ccmom lb{lb} k25',cc_net(pos))
print()
print('=== benchmark: EW long cc (drift control) ===')
w=pd.DataFrame(np.where(cc.notna(),1.0,0.0),index=cc.index,columns=cc.columns).div(cc.notna().sum(axis=1),axis=0)
st1('EW-long cc k=all',cc_net(w))
print()
print('=== OVNcc with IC-tilt: sig = on_mean - ic_mean (spread), cc target ===')
for lb in [21,63,126]:
    sig=(on-ic).rolling(lb,min_periods=max(2,lb//3)).mean()
    for k in [25]:
        pos=H.xs_ls(sig,k=k)
        st1(f'ONICspread->cc lb{lb} k{k}',cc_net(pos))
