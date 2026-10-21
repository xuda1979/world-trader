import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make, NEW3, vt, POOL, SHORTF
ROOT='/Users/daxu/software/world-trader'
Sd, capW, blend, tw, wts = make(NEW3)
books={}
for name,(TGT,THR) in {'SAFE':(0.07,0.04),'AGG':(0.091,0.03)}.items():
    b,gb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index)
    full=capW.mul(gb,axis=0).mul(sc,axis=0)
    reb=full.diff().abs().sum(axis=1); dsc=sc.diff().abs()*0.5
    terms=[]
    for n in POOL:
        sf=SHORTF[n]
        if sf>0: terms.append(capW[n]*sc*sf*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2))
    htb=pd.concat(terms,axis=1).sum(axis=1)
    r=(b*sc-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4-reb.reindex(b.index).fillna(0)*6e-4-htb.reindex(b.index).fillna(0)/252).dropna(how='all')
    books[name]=dict(r=r,reb=reb,dsc=dsc,htb=htb,b=b,sc=sc,full=full)
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
idx=champ.index; Y=len(idx)/252
led=pd.read_csv(f'{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv',parse_dates=['date'])
led_reb=led.groupby('date').qty_notional.sum().reindex(idx).fillna(0)
champ_reb=((books['SAFE']['reb']+books['AGG']['reb'])/2).reindex(idx).fillna(0)
gros=((books['SAFE']['b']*books['SAFE']['sc'])+(books['AGG']['b']*books['AGG']['sc']))/2
dsc=((books['SAFE']['dsc']+books['AGG']['dsc'])/2).reindex(idx).fillna(0)
htb=((books['SAFE']['htb']+books['AGG']['htb'])/2).reindex(idx).fillna(0)
twd=tw.reindex(idx).fillna(0)
common_gross=gros-dsc*6e-4-twd*6e-4-htb/252
pnl_l=common_gross-led_reb*6e-4     # if ledger were THE cost record
pnl_c=common_gross-champ_reb*6e-4   # as committed
d=(pnl_l-pnl_c)
print("B2 exact: ledger-vs-committed daily PnL: max|diff|=%.4e  mean=%.4e  n_diff_days=%d/5086"%(
    d.abs().max(), d.mean(), (d.abs()>1e-12).sum()))
ann_l=(1+pnl_l).prod()**(252/Y)-1; ann_c=(1+pnl_c).prod()**(252/Y)-1
print("ann(ledger-cost book)=%.4f%%  ann(committed)=%.4f%%  gap=%.4fpp"%(ann_l*100,ann_c*100,(ann_l-ann_c)*100))
print("turnover overcharge: ledger 716.70x vs charged 600.78x = +%.2f%% too much reb turnover"%((716.70/600.78-1)*100))
print("while OMITTING: tw 293.37x + dsc 8.75x turnover (17.60%%+0.52%% NAV) and borrow 6.35%% NAV")
