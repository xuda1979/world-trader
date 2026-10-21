import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make, NEW3, vt, POOL
ROOT='/Users/daxu/software/world-trader'
Sd, capW, blend, tw, wts = make(NEW3)
FUT={'brwt15','brwt10','brwt7','brwt5','C5ng','C5ngsum','a6r7','QAxasts','carryv2','diescrack','CFX4','FF2'}
EQ={'A5r2','dualmom'}
fulls={}
for name,(TGT,THR) in {'SAFE':(0.07,0.04),'AGG':(0.091,0.03)}.items():
    b,gb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index)
    fulls[name]=capW.mul(gb,axis=0).mul(sc,axis=0)
def hybrid_turn(F):
    # futures-style: held across gaps (charge only where both ends defined); equity: flat (ffill, 0 on gaps, re-enter)
    out=0
    for c in F.columns:
        col=F[c]
        if c in FUT: out=out+col.diff().abs().fillna(0)
        else:
            f=col.fillna(0); out=out+f.diff().abs().fillna(0)
    return out
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
idx=champ.index; Y=len(idx)/252
charged=(fulls['SAFE'].diff().abs().sum(axis=1)+fulls['AGG'].diff().abs().sum(axis=1))/2
hyb=(hybrid_turn(fulls['SAFE'])+hybrid_turn(fulls['AGG']))/2
flat=((fulls['SAFE'].fillna(0).diff().abs().sum(axis=1))+(fulls['AGG'].fillna(0).diff().abs().sum(axis=1)))/2
held=((fulls['SAFE'].ffill().fillna(0).diff().abs().sum(axis=1))+(fulls['AGG'].ffill().fillna(0).diff().abs().sum(axis=1)))/2
print("=== CHECK F FINAL ===")
for lbl,s in [('charged skipna',charged),('HYBRID honest (fut held+eq flat)',hyb),('all-flat',flat),('all-held',held)]:
    c=s.reindex(idx).fillna(0).sum()*6e-4
    print("%-34s turn=%8.1fx  cost=%7.2f%%NAV  %6.4f%%/yr"%(lbl,s.sum(),c*100,c/Y*100))
gap=(hyb-charged).reindex(idx).fillna(0).sum()*6e-4
print("undercharge (hybrid-charged) = %.2f%% NAV total = %.4f%%/yr"%(gap*100,gap/Y*100))
print("AGG: 716.7 charged vs hybrid %.1f  (gap %.1f = %.1f%%)"%(hyb.sum()*2, (hyb.sum()*2-716.7), (hyb.sum()*2/716.7-1)*100))
# equity-only flat-across cost (the truly-missed forced liquidations)
eqmiss=0
for F in fulls.values():
    for c in EQ: eqmiss+=F[c].fillna(0).diff().abs().sum()-F[c].diff().abs().fillna(0).sum()
print("equity-style-only missed (A5r2+dualmom, both books): %.1fx turn = %.2f%%NAV = %.4f%%/yr"%(eqmiss,eqmiss*6e-4*100,eqmiss*6e-4*100/Y))
print()
print("=== holiday-day PnL share ===")
from pandas.tseries.holiday import USFederalHolidayCalendar
hol=set(USFederalHolidayCalendar().holidays(start='2006-01-01',end='2026-12-31'))
champ_r=champ
is_hol=pd.Series([d in hol for d in champ.index],index=champ.index)
print("champion rows on federal holidays: %d/%d ; their PnL share: %.2f%%"%(is_hol.sum(),len(champ),100*champ[is_hol].sum()/champ.sum()))
led=pd.read_csv(f'{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv',parse_dates=['date'])
hol_led=led[pd.to_datetime(led.date).isin(hol)]
print("ledger holiday trade records: %d on %d distinct holiday dates"%(len(hol_led),hol_led.date.nunique()))
print("holiday qty share: %.3f%% of total notional"%(100*hol_led.qty_notional.sum()/led.qty_notional.sum()))
