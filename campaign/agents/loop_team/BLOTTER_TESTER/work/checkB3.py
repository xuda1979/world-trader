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
    books[name]=dict(b=b,sc=sc,reb=reb,dsc=dsc,htb=htb)
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
idx=champ.index; n=len(idx); Y=n/252
led_reb=pd.read_csv(f'{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv',parse_dates=['date']).groupby('date').qty_notional.sum().reindex(idx).fillna(0)
champ_reb=((books['SAFE']['reb']+books['AGG']['reb'])/2).reindex(idx).fillna(0)
gros=((books['SAFE']['b']*books['SAFE']['sc'])+(books['AGG']['b']*books['AGG']['sc']))/2
dsc=((books['SAFE']['dsc']+books['AGG']['dsc'])/2).reindex(idx).fillna(0)
htb=((books['SAFE']['htb']+books['AGG']['htb'])/2).reindex(idx).fillna(0)
twd=tw.reindex(idx).fillna(0)
common=gros-dsc*6e-4-twd*6e-4-htb/252
pnl_l=(common-led_reb*6e-4); pnl_c=(common-champ_reb*6e-4)
def ann(r):
    r=r.dropna(); return ((1+r).prod()**(252/len(r))-1)*100
print("B2-FIXED: ann(ledger-as-cost)=%.4f%%  ann(committed)=%.4f%%  gap=%.4f pp/yr"%(ann(pnl_l),ann(pnl_c),ann(pnl_l)-ann(pnl_c)))
d=(pnl_l-pnl_c)
print("daily max|diff|=%.4e  cumulative diff=%.4f%% NAV over %.1fy"%(d.abs().max(),((1+d).prod()-1)*100,Y))
print()
print("LEDGER cost if trusted: %d trades*6.4bps on 716.70x = %.2f%% NAV (%.3f%%/yr)"%(61194,716.6999*6.4e-4*100,716.6999*6.4e-4*100/Y))
print("CHAMPION charged: reb %.2f%% + tw/dsc %.2f%% + borrow %.2f%% = %.2f%% NAV (%.3f%%/yr @6.0bps)"%(
  champ_reb.sum()*6e-4*100,(twd.sum()+dsc.sum())*6e-4*100,htb.sum()/252*100,
  (champ_reb.sum()*6e-4+(twd.sum()+dsc.sum())*6e-4+htb.sum()/252)*100,
  (champ_reb.sum()*6e-4+(twd.sum()+dsc.sum())*6e-4+htb.sum()/252)*100/Y))
print("ledger-vs-champion NET cost gap = %.2f%% NAV (%.3f%%/yr)"%(
  (716.6999*6.4e-4-(champ_reb.sum()*6e-4+(twd.sum()+dsc.sum())*6e-4+htb.sum()/252))*100,
  (716.6999*6.4e-4-(champ_reb.sum()*6e-4+(twd.sum()+dsc.sum())*6e-4+htb.sum()/252))*100/Y))
print()
print("champion span:",champ.index.min().date(),"->",champ.index.max().date(),"n=",n)
print("ledger span: 2006-12-29 -> 2026-08-27; champion dates BEFORE first ledger trade:",(idx<idx[idx>='2006-12-29'][0]).sum())
print("champion dates AFTER last ledger trade:",(idx>'2026-08-27').sum())
