import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make, NEW3, vt, POOL, SHORTF
ROOT='/Users/daxu/software/world-trader'
Sd, capW, blend, tw, wts = make(NEW3)

# gross components per book
rebs={}
for name,(TGT,THR) in {'SAFE':(0.07,0.04),'AGG':(0.091,0.03)}.items():
    b, gb = vt(blend, TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index)
    full=capW.mul(gb,axis=0).mul(sc,axis=0)
    reb=full.diff().abs().sum(axis=1)
    dsc=sc.diff().abs()*0.5
    terms=[]
    for n in POOL:
        sf=SHORTF[n]
        if sf>0: terms.append(capW[n]*sc*sf*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2))
    htb=pd.concat(terms,axis=1).sum(axis=1)
    r=(b*sc - (tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4 - reb.reindex(b.index).fillna(0)*6e-4
       - htb.reindex(b.index).fillna(0)/252).dropna(how='all')
    rebs[name]=(r,reb,dsc,htb,b,sc)
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
repro=((rebs['SAFE'][0]+rebs['AGG'][0])/2).dropna()
j=pd.concat([champ.rename('champ'),repro.rename('repro')],axis=1,join='inner').dropna()
print("B1: full-model repro of BALANCED: n=%d max|diff|=%.3e"%(len(j),(j.champ-j.repro).abs().max()))

# now ledger-based repro: ledger reb (AGG only) vs champion charged ((SAFE+AGG)/2)
led=pd.read_csv(f'{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv',parse_dates=['date'])
led_reb=led.groupby('date').qty_notional.sum()
champ_reb=(rebs['SAFE'][1]+rebs['AGG'][1])/2
gros=((rebs['SAFE'][4]*rebs['SAFE'][5])+(rebs['AGG'][4]*rebs['AGG'][5]))/2
dsc=((rebs['SAFE'][2]+rebs['AGG'][2])/2)
htb=((rebs['SAFE'][3]+rebs['AGG'][3])/2)
idx=champ.index
pnl_ledger=(gros.reindex(idx).fillna(0)
            - (tw.reindex(idx).fillna(0)+dsc.reindex(idx).fillna(0))*6e-4
            - led_reb.reindex(idx).fillna(0)*6e-4
            - htb.reindex(idx).fillna(0)/252)
pnl_champ=(gros.reindex(idx).fillna(0)
           - (tw.reindex(idx).fillna(0)+dsc.reindex(idx).fillna(0))*6e-4
           - champ_reb.reindex(idx).fillna(0)*6e-4
           - htb.reindex(idx).fillna(0)/252)
d=(pnl_ledger-pnl_champ).dropna()
yrs=len(d)/252
print("B2: ledger-as-charged repro max|diff|=%.3e  total cum-PnL diff=%.4f%% of NAV  ann=%.4f%%/yr"%(
    d.abs().max(), (1+d).prod()-1, ((1+pnl_ledger.dropna()).prod()**(252/len(d))-1-(1+pnl_champ.dropna()).prod()**(252/len(d)))*100))

# cost decomposition of champion (BALANCED)
n=len(champ); Y=n/252
twT=tw.reindex(idx).fillna(0).sum(); dscT=dsc.reindex(idx).fillna(0).sum(); rebT=champ_reb.reindex(idx).fillna(0).sum()
print()
print("Champion BALANCED cost decomposition over %.1fy:"%Y)
print("  overlay-vt turnover tw : %8.2fx  @6.0bps = %6.2f%% NAV  (%.3f%%/yr)  [NOT IN LEDGER]"%(twT,twT*6e-4*100,twT*6e-4*100/Y))
print("  throttle trades dsc    : %8.2fx  @6.0bps = %6.2f%% NAV  (%.3f%%/yr)  [NOT IN LEDGER]"%(dscT,dscT*6e-4*100,dscT*6e-4*100/Y))
print("  position-path reb      : %8.2fx  @6.0bps = %6.2f%% NAV  (%.3f%%/yr)  [IN LEDGER as 716.70x AGG-only]"%(rebT,rebT*6e-4*100,rebT*6e-4*100/Y))
bor=htb.reindex(idx).fillna(0)/252
print("  borrow (shorts)        :           %6.2f%% NAV  (%.3f%%/yr)  [NOT IN LEDGER]"%(bor.sum()*100,bor.sum()*100/Y))
tot=(twT+dscT)*6e-4+rebT*6e-4+bor.sum()
print("  TOTAL charged cost     :           %6.2f%% NAV  (%.3f%%/yr)"%(tot*100,tot*100/Y))
# gross/nEt
print("  champ ann(geo) 2008+ = %.2f%%"%((((1+champ[champ.index>='2008-03-31']).prod())**(252/len(champ[champ.index>='2008-03-31']))-1)*100))
