import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make, NEW3, vt
ROOT='/Users/daxu/software/world-trader'
Sd, capW, blend, tw, wts = make(NEW3)
fulls={}
for name,(TGT,THR) in {'SAFE':(0.07,0.04),'AGG':(0.091,0.03)}.items():
    b,gb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index)
    fulls[name]=capW.mul(gb,axis=0).mul(sc,axis=0)
print("=== CHECK F: SPARSE-GAP skipna UNDERCHARGE ===")
for name,F in fulls.items():
    skip=F.diff().abs().sum(axis=1).sum()            # as charged (skipna)
    flat=F.fillna(0).diff().abs().sum(axis=1).sum()  # flat-across gaps (exit+re-enter)
    held=F.ffill().fillna(0).diff().abs().sum(axis=1).sum()  # held-across gaps (net change only)
    print(f"{name}: charged(skipna)={skip:.1f}  honest_flat_across={flat:.1f}  honest_held_across={held:.1f}  undercharge vs flat={flat-skip:.1f} ({(flat-skip)/flat*100:.1f}%)  vs held={held-skip:.1f}")
# per-sleeve sparsity on AGG
F=fulls['AGG']
nn=F.notna().sum(); gaps=(len(F)-nn)/len(F)*100
skip=F.diff().abs().sum(axis=0); flat=F.fillna(0).diff().abs().sum(axis=0); held=F.ffill().fillna(0).diff().abs().sum(axis=0)
t=pd.DataFrame({'nan_days%':gaps.round(1),'skipna':skip,'flat':flat,'held':held})
t['uc_flat']=t['flat']-t['skipna']
print()
print(t.sort_values('uc_flat',ascending=False).round(2).to_string())
# annualized cost impact on BALANCED champion, 6bps
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
idx=champ.index; Y=len(idx)/252
skipb=(fulls['SAFE'].diff().abs().sum(axis=1)+fulls['AGG'].diff().abs().sum(axis=1))/2
flatb=(fulls['SAFE'].fillna(0).diff().abs().sum(axis=1)+fulls['AGG'].fillna(0).diff().abs().sum(axis=1))/2
heldb=(fulls['SAFE'].ffill().fillna(0).diff().abs().sum(axis=1)+fulls['AGG'].ffill().fillna(0).diff().abs().sum(axis=1))/2
for lbl,s in [('charged skipna',skipb),('honest flat-across',flatb),('honest held-across',heldb)]:
    c=s.reindex(idx).fillna(0).sum()*6e-4
    print(f"{lbl}: total reb turn {s.sum():.1f}x  cost {c*100:.2f}% NAV  {c/Y*100:.4f}%/yr")
