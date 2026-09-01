"""IDEA 5: real-rate momentum. TIPS-synth nominal TR = -7.5*d(DFII10) + DFII10/252 (real
carry) + T10YIE/252 (inflation accrual). Signal: DFII10 trailing-L change; LONG when real
yields FELL (duration wins), flat/short otherwise. Weekly step. 2003+ only — DISCLOSED."""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from d1_lib import *

DT=7.5
yreal=yld('DFII10'); be=yld('T10YIE'); y10=yld('DGS10')
df=pd.concat([yreal.rename('yr'),be.rename('be'),y10.rename('y10')],axis=1,sort=True).dropna()
tips_tr=-DT*df['yr'].diff()+df['yr']/252.0+df['be']/252.0/100.0*0  # be in %, /252/100
# NOTE: yreal already decimal (/100 in yld); be decimal too -> accrual = be/252
tips_tr=-DT*df['yr'].diff()+df['yr']/252.0+df['be']/252.0
nom_tr=rfn(df['y10'],DUR['DGS10'])
rfc=rf_daily().reindex(df.index).fillna(0)
chgyr=df['yr'].diff(L) if False else None
res=[]
for L in (63,126,252):
    for mode in ('LF','LS'):
        for step in (5,10,21):
            chg=df['yr'].diff(L)
            z=chg.iloc[::step]
            if mode=='LF': sig=(z<0).astype(float)
            else: sig=((z<0).astype(float)*2-1)
            sig=sig.reindex(df.index).ffill().shift(1).fillna(0)
            leg=sig*tips_tr-(0 if mode=='LF' else sig*0)  # LF: flat earns rf
            if mode=='LF':
                net=vt(sig*tips_tr-sig.diff().abs().fillna(0)*COST+rfc*(1-sig))
                gn=1.0
            else:
                # long tips / short 1x nominal (DV01-neutral-ish: 7.5 vs 8.5 dur, use notional 1)
                pair=tips_tr-nom_tr
                net=vt(sig*pair-sig.diff().abs().fillna(0)*2*COST+rfc*0)
                gn=2.0
            sr=net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0
            res.append((sr,L,mode,step,net,sig,gn))
res.sort(key=lambda t:-t[0])
print("top 6:")
for sr,L,mode,step,_,_,_ in res[:6]: print(f"  SR={sr:.2f} L={L} {mode} step={step}")
sr,L,mode,step,net,sig,gn=res[0]
s=stats(net); h=halves(net); cb=corr_to(net,CHAMP); p,real=rotation_scramble(net,sig,tips_tr if mode=='LF' else tips_tr-nom_tr,rfc,seed=2)
print(f"\nBEST {L} {mode} step{step}: SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% negy={s['negy']} worst={s['worst']:.1f}% H1={h[0]:.2f} H2={h[1]:.2f} corr_champ={cb:.3f} scramble_p={p:.3f} to/d={sig.diff().abs().mean():.4f}")
print("yearly:", s['yearly'])
