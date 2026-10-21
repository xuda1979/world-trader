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
rebA=fulls['SAFE'].diff().abs().sum(axis=1)   # SAFE book turnover/day
rebB=fulls['AGG'].diff().abs().sum(axis=1)    # AGG book turnover/day
bal_reb=(rebA+rebB)/2                          # what BALANCED champion actually charges

led=pd.read_csv(f'{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv',parse_dates=['date'])

print("=== CHECK A: RECONCILIATION ===")
# per-sleeve: ledger sum|qty| vs AGG path |diff| (skipna)
lt=led.groupby('sleeve').qty_notional.sum()
pt=fulls['AGG'].diff().abs().sum(axis=0)
comp=pd.concat([lt.rename('ledger'),pt.rename('agg_pospath')],axis=1)
comp['diff']=comp.ledger-comp.agg_pospath
comp['diff'].abs()/comp.agg_pospath*1e6
print(comp.round(6).to_string())
print("max rel diff (ppm): %.4f"%comp.rel_ppm.max())
print("ledger total turn=%.4f  AGG path turn=%.4f  SAFE path turn=%.4f  BAL charged turn=%.4f"%(
    led.qty_notional.sum(), rebB.sum(), rebA.sum(), bal_reb.sum()))
print("SAFE/AGG ratio=%.4f"%(rebA.sum()/rebB.sum()))
print("ledger covers only %.2f%% of BALANCED charged turnover"%(100*led.qty_notional.sum()/bal_reb.sum()))
