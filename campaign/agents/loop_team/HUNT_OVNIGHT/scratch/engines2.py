"""Refined slate: overnight-targeted books + drift-control variants. All net T+1/6.4bps/borrow."""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
O=pd.read_pickle('scratch/O.pkl'); C=pd.read_pickle('scratch/C.pkl')
r_cc=(C/C.shift(1)-1.0).where(on.notna())
r_on=on
r_ic=ic.where(on.notna())
nval=on.notna().sum(axis=1)
def ew_long(mask_or_sig=None):
    w=pd.DataFrame(np.where(on.notna(),1.0,0.0),index=on.index,columns=on.columns)
    return w.div(nval,axis=0)
def st1(tag,net,start='2008-01-01'):
    net=net[net.index>=pd.Timestamp(start)]
    st=H.full_stats(net)
    print(f"{tag}: SR {st['sr']:.3f} ann {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% negy {st['negy']}/{st['years']} worst {st['worst']*100:+.1f}%")
    return st

print('--- DRIFT CONTROLS (equal-wt long-only, no signal) ---')
st1('EW-long ON only', H.net_of_book(ew_long(),on)[0])
w_on=ew_long(); w_cc=w_on
st1('EW-long CC', H.net_of_book(w_cc,r_cc)[0])

print()
print('--- ON63 long-top-k-only (no shorts; k names, beta-min) ---')
sig=on.rolling(63,min_periods=31).mean()
for k in [15,25,50]:
    R=sig.rank(axis=1,ascending=False)
    w=pd.DataFrame(np.where((R<=k)&sig.notna(),1.0/k,0.0),index=sig.index,columns=sig.columns)
    st1(f'ON63 top{k} long-only ON', H.net_of_book(w,r_on)[0])
print()
print('--- ON63 long low-beta names (beta from 252d ON vs mkt ON) ---')
mkt_on=on.mean(axis=1)
cov=on.sub(mkt_on,axis=0).rolling(252,min_periods=126).cov(mkt_on.rolling(252,min_periods=126).var())
# simpler: rolling cov via loops is slow; use ewm-style manual: cov_t = mean(x*y)-mean(x)mean(y) over 252d
xy=(on.mul(mkt_on,axis=0)).rolling(252,min_periods=126).mean()
vx=(on**2).rolling(252,min_periods=126).mean()
mx=on.rolling(252,min_periods=126).mean()
my=mkt_on.rolling(252,min_periods=126).mean()
beta=(xy-mx.mul(my,axis=0))/(vx-mx**2)
beta=beta.clip(-1,5)
sig2=on.rolling(63,min_periods=31).mean()
for qmax in [0.2,0.4]:
    bq=beta.quantile(qmax,axis=1)
    wmask=(beta.le(bq,axis=0))&(sig2.rank(axis=1,ascending=False)<=25)&sig2.notna()
    w=pd.DataFrame(np.where(wmask,1.0/25,0.0),index=sig.index,columns=sig.columns)
    st1(f'ON63 top25 beta<{qmax} long-only ON', H.net_of_book(w,r_on)[0])
print()
print('--- ON63 -> next-day INTRADAY (does it fade IC after strong ON names?) ---')
for k in [25]:
    R=sig.rank(axis=1,ascending=False)
    w=pd.DataFrame(np.where((R<=k)&sig.notna(),1.0/k,0.0),index=sig.index,columns=sig.columns)
    st1(f'ON63 top{k} long-only IC', H.net_of_book(w,r_ic)[0])
    st1(f'ON63 top{k} long-only CC', H.net_of_book(w,r_cc)[0])
print()
print('--- vol-scaled ON63 k25 LS (rv target on book) ---')
posLS=H.xs_ls(sig,k=25)
netLS,_=H.net_of_book(posLS,r_on)
w_on_s=w_on
print('--- ON63 LS + short-intraday overlay hybrid: long ON63top25 & short bottom25 INTRADAY ---')
R=sig.rank(axis=1,ascending=False)
wlong=pd.DataFrame(np.where((R<=25)&sig.notna(),1.0/50,0.0),index=sig.index,columns=sig.columns)
wshortic=pd.DataFrame(np.where((R>sig.notna().sum(axis=1).values[:,None]-25)&sig.notna(),-1.0/50,0.0),index=sig.index,columns=sig.columns)
w2=wlong+wshortic
n2=H.net_of_book(w2,r_on)[0]+H.net_of_book(w2,r_ic)[0]
st1('hybrid ON63: long-top25@ON + short-bot25@IC', n2)
