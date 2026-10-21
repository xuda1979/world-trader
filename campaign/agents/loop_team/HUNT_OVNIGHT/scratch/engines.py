"""Build all candidate engines for HUNT_OVNIGHT. Signal at t uses info<=t; T+1 execution via
net_of_book shift. Costs 6.4bps/side, borrow 0.5%/yr on shorts. Evals on 2008+ net."""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
O=pd.read_pickle('scratch/O.pkl'); C=pd.read_pickle('scratch/C.pkl')
r_on=on
r_cc=(C/C.shift(1)-1.0)
r_cc=r_cc.where(on.notna())          # tradeable validity: need prior close + today open
r_ic=ic.where(on.notna())
champ=H.load_champion()

def mk_xs(sig_mat, ret_mat, k=25, tag='', gross_cap=None):
    pos=H.xs_ls(sig_mat,k=k)
    net,_=H.net_of_book(pos,ret_mat)
    if gross_cap:
        # per-name weight already <=1/k; cap on gross=not needed for xs
        pass
    return pos,net

def eval1(tag,pos,retmat,start='2008-01-01'):
    net,_=H.net_of_book(pos,retmat)
    net=net[net.index>=pd.Timestamp(start)]
    st=H.full_stats(net)
    print(f"{tag}: n={st['n']} SR {st['sr']:.3f} ann {st['ann_geo']*100:+.1f}% vol {st['ann_arith']*0:.0f} MDD {st['mdd']*100:.1f}% negy {st['negy']}/{st['years']} worst {st['worst']*100:+.1f}%")
    return net,st

print('=== Idea 1: overnight momentum L/S (xs, k names per side), trade next overnight ===')
for lb in [1,3,5,10,21,63]:
    sig=on.rolling(lb,min_periods=min(lb,max(2,lb//2))).mean()
    for k in [15,25,50]:
        pos=H.xs_ls(sig,k=k)
        eval1(f"ONmom lb{lb} k{k}",pos,r_on)
print()
print('=== Idea 1b: overnight fade (inverse) ===')
for lb in [1,3,5,10,21]:
    sig=-on.rolling(lb,min_periods=min(lb,max(2,lb//2))).mean()
    pos=H.xs_ls(sig,k=25)
    eval1(f"ONfade lb{lb} k25",pos,r_on)
print()
print('=== Idea 2: intraday momentum/fade L/S, trade next intraday ===')
for lb in [1,3,10,21]:
    for sgn,lab in [(1,'mom'),(-1,'fade')]:
        sig=sgn*ic.rolling(lb,min_periods=min(lb,max(2,lb//2))).mean()
        pos=H.xs_ls(sig,k=25)
        eval1(f"IC{lab} lb{lb} k25",pos,r_ic)
print()
print('=== Idea 3: ON-IC spread book, trade next close-to-close ===')
for lb in [1,3,10,21,63]:
    sig=(on-ic).rolling(lb,min_periods=min(lb,max(2,lb//2))).mean()
    pos=H.xs_ls(sig,k=25)
    eval1(f"ONIC lb{lb} k25",pos,r_cc)
print()
print('=== Idea 3b: ON-IC spread -> trade next OVERNIGHT (decomposition-targeted) ===')
for lb in [3,10,21]:
    sig=(on-ic).rolling(lb,min_periods=min(lb,max(2,lb//2))).mean()
    pos=H.xs_ls(sig,k=25)
    eval1(f"ONIC->ON lb{lb} k25",pos,r_on)
print()
print('=== Idea 4: weekday x overnight (long Tue overnight, from Monday close) ===')
# executed position: hold overnight into Tuesday => pos decided Monday close; implemented as
# signal set on Monday close = 1 (calendar, known at t), ret = Tue overnight
idx=r_on.index
cal=pd.DataFrame(0.0,index=idx,columns=r_on.columns)
tue=idx.dayofweek==1
cal[tue]=1.0
# equal-weight long book across valid names: weight 1/n_valid on each valid name
nval=on.notna().sum(axis=1)
w=cal.div(nval,axis=0).where(on.notna(),0.0)
eval1("Tue-ON long",w,r_on)
for wd,lab in [(0,'Mon->TueON'),(4,'Fri->MonON')]:
    cal=pd.DataFrame(0.0,index=idx,columns=r_on.columns)
    cal[idx.dayofweek==wd]=1.0
    w=cal.div(nval,axis=0).where(on.notna(),0.0)
    eval1(f"{lab} long",w,r_on)
