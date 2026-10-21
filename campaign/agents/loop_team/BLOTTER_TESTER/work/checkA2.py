import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make, NEW3, vt, POOL
ROOT='/Users/daxu/software/world-trader'
Sd, capW, blend, tw, wts = make(NEW3)
fulls={}
for name,(TGT,THR) in {'SAFE':(0.07,0.04),'AGG':(0.091,0.03)}.items():
    b, gb = vt(blend, TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index)
    fulls[name]=capW.mul(gb,axis=0).mul(sc,axis=0)
rebA=fulls['SAFE'].diff().abs().sum(axis=1); rebB=fulls['AGG'].diff().abs().sum(axis=1)
bal_reb=(rebA+rebB)/2
led=pd.read_csv(f'{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv',parse_dates=['date'])
lt=led.groupby('sleeve').qty_notional.sum(); pt=fulls['AGG'].diff().abs().sum(axis=0)
comp=pd.concat([lt.rename('ledger'),pt.rename('agg_pospath')],axis=1)
comp['adiff']=(comp['ledger']-comp['agg_pospath']).abs()
comp['rel_ppm']=comp['adiff']/comp['agg_pospath']*1e6
print("max per-sleeve rel diff: %.3e ppm -> EXACT-MATCH verdict: %s"%(comp.rel_ppm.max(), comp.rel_ppm.max()<1.0))
print("ledger total |turn| = %.4f"%led.qty_notional.sum())
print("AGG path total      = %.4f   (ledger/AGG = %.6f)"%(rebB.sum(), led.qty_notional.sum()/rebB.sum()))
print("SAFE path total     = %.4f   (ledger/SAFE = %.6f)"%(rebA.sum(), led.qty_notional.sum()/rebA.sum()))
print("BALANCED charged    = %.4f   (ledger/BAL = %.6f)"%(bal_reb.sum(), led.qty_notional.sum()/bal_reb.sum()))
print()
# What cost does the champion actually charge, and what would the ledger's 6.4bps imply?
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
n=len(champ); yrs=n/252
for lbl,turn in [('AGG(6.0bps charged builder rate)',rebB),('BALANCED avg',bal_reb),('LEDGER',led.groupby('date').qty_notional.sum())]:
    d=turn.reindex(champ.index).fillna(0)
    cost=d.values*6.4e-4
    ann=cost.sum()/yrs*100
    print(f"{lbl}: total one-side turn {d.sum():.1f}x, 6.4bps cost total {cost.sum()*100:.2f}% of NAV, ann {ann:.3f}%/yr")
cost6=bal_reb.reindex(champ.index).fillna(0).values*6.0e-4; cost64=bal_reb.reindex(champ.index).fillna(0).values*6.4e-4
gap=(cost64.sum()-cost6.sum())/yrs*100
print()
print("EXACT 6.0 vs 6.4 bps gap on BALANCED charged turnover: total %.2f%% vs %.2f%% of NAV -> %.4f%%/yr (%.2f bps/yr of NAV)"%(cost6.sum()*100,cost64.sum()*100,gap,gap*100))
ann_turn=bal_reb.reindex(champ.index).fillna(0).mean()*252
print("mean one-side turnover %.2f x/yr -> 0.4bps = %.4f%%/yr"%(ann_turn, ann_turn*0.4e-4*100))
