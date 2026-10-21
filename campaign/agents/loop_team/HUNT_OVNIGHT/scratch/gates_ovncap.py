"""FULL charter gate battery on OVNCAP family (vol-targeted tgt 0.10 cap 3, trailing expanding).
Gates: SR>=0.6, H1/H2>=0.3, negy<=2 each>-5%, poslag scramble 200x p<0.05, |corr|<0.15 to
GOAL100_HONEST14V3_BALANCED, ac1<0.5, uniqR>=0.08, T+1, 6.4bps/side, borrow 0.5%/yr."""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
champ=H.load_champion()

def book_net(pos_on, pos_ic):
    common=on.index
    p1=pos_on.reindex(common).fillna(0.0).shift(1).fillna(0.0)
    p2=pos_ic.reindex(common).fillna(0.0).shift(1).fillna(0.0)
    r1=on.reindex(common).fillna(0.0); r2=ic.reindex(common).fillna(0.0)
    gross=(p1*r1).sum(axis=1)+(p2*r2).sum(axis=1)
    turn=((p1.diff().abs().sum(axis=1))+(p2.diff().abs().sum(axis=1)))/2.0
    bor=(p1.clip(upper=0).abs().sum(axis=1)+p2.clip(upper=0).abs().sum(axis=1))*H.BORROW
    return (gross-turn*H.COST-bor).dropna(), p1, p2

def posls(sig,k):
    return H.xs_ls(sig,k=k)

results={}
print('=== OVNCAP gate battery (vol-targeted 10% cap 3) ===')
for lb in [63,126,189,252]:
    sig=on.rolling(lb,min_periods=max(2,lb//3)).mean()
    for k in [15,25,50]:
        pos=posls(sig,k)
        net,_,_=book_net(pos,-pos)
        rv=net.expanding(60).std()*np.sqrt(252)
        sc=(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)
        netv=net*sc
        g,st=H.gate_battery(f'OVNCAP lb{lb} k{k}', netv, pos, on, champ)
        results[(lb,k)]=(g,st)

print()
print('=== param plateau check around chosen lb126 k25 (SR values, vt) ===')
for (lb,k),(g,st) in sorted(results.items()):
    print(f"lb{lb} k{k}: SR {g['SR']:.3f}")

print()
print('=== extra lag probes on chosen variant (T+1 integrity) ===')
lb,k=126,25
sig=on.rolling(lb,min_periods=lb//3).mean()
pos=posls(sig,k)
for extra in [0,1,2,5]:
    net,_,_=book_net(pos.shift(extra),-pos.shift(extra))
    rv=net.expanding(60).std()*np.sqrt(252); sc=(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)
    nv=(net*sc); nv=nv[nv.index>='2008-01-01']
    print(f'extra lag {extra}d: SR {nv.mean()/nv.std()*np.sqrt(252):.3f}')
