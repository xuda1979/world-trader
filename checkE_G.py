import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make, NEW3, vt, POOL, SHORTF, EXEC
ROOT='/Users/daxu/software/world-trader'
led=pd.read_csv(f'{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv',parse_dates=['date'])
print("=== CHECK E: BORROW ===")
print("ledger columns:", list(led.columns))
print("'borrow' in any form:", any('borrow' in c.lower() for c in led.columns))
Sd, capW, blend, tw, wts = make(NEW3)
books={}
for name,(TGT,THR) in {'SAFE':(0.07,0.04),'AGG':(0.091,0.03)}.items():
    b,gb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index)
    books[name]=dict(capW=capW,sc=sc)
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
idx=champ.index; Y=len(idx)/252
tot=0
print("borrow charged in builder (PnL) vs ledger (ABSENT):")
for n in POOL:
    sf=SHORTF[n]
    if sf>0:
        hA=(books['SAFE']['capW'][n]*books['SAFE']['sc']*sf*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)).reindex(idx).fillna(0)
        hB=(books['AGG']['capW'][n]*books['AGG']['sc']*sf*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)).reindex(idx).fillna(0)
        h=(hA+hB)/2/252
        tot+=h.sum()
        print("  %-9s shortF=%.1f  borrow charged=%6.3f%% NAV (%.4f%%/yr)"%(n,sf,h.sum()*100,h.sum()*100/Y))
print("  TOTAL borrow: %.3f%% NAV over %.1fy (%.4f%%/yr) — %s"%(tot*100,Y,tot*100/Y,
  "ABSENT from ledger" if not any('borrow' in c.lower() for c in led.columns) else "present"))
print()
print("=== CHECK G: INSTRUMENT COMPLETENESS + REAL pct ===")
g=led.groupby('sleeve').price_source.apply(lambda s:(s=='REAL').mean()*100).round(1)
n=led.groupby('sleeve').size()
for s in led.sleeve.unique():
    print("  %-10s %5.1f%% REAL  n=%d  instrument=%s"%(s,g[s],n[s],led[led.sleeve==s].instrument.iloc[0]))
print()
print("=== LEVERAGE cross-check (ledger/path vs disclosed 3.45x mean, p95 7.18x) ===")
gross=pd.concat([(books[k]['capW'].abs()*0).add(1) for k in books],axis=1).iloc[:,:0]  # placeholder
fulls={}
for name,(TGT,THR) in {'SAFE':(0.07,0.04),'AGG':(0.091,0.03)}.items():
    b,gb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index)
    fulls[name]=capW.mul(gb,axis=0).mul(sc,axis=0)
gpath=((fulls['SAFE'].abs().sum(axis=1)+fulls['AGG'].abs().sum(axis=1))/2).reindex(idx).dropna()
print("capital-real gross (avg of books): mean=%.3fx p95=%.3fx max=%.3fx (disclosed: 3.45x mean / 7.18x p95)"%(gpath.mean(),gpath.quantile(0.95),gpath.max()))
led_daily=led.groupby('date').qty_notional.sum()
print("ledger daily one-side turn: mean=%.4f  p95=%.4f"%(led_daily.mean(),led_daily.quantile(0.95)))
