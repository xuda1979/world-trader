import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])
oldA=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_SAFE_daily.csv",index_col=0,parse_dates=True).iloc[:,0]

def vtf(r,tgt,min_win=60,cap=8.0,ddof=1,annf=252):
    vol=r.rolling(min_win).std(ddof=ddof).shift(1)*np.sqrt(annf)
    s=(tgt/vol).clip(upper=cap); s[vol.isna()]=0
    return r*s.fillna(0),s

def build_v(TGT,THR,vfun=vt,vol_on_gross=False,percost=True):
    V={};G={}
    for n in POOL:
        r=sn(POOL[n]); v,s=vfun(r,0.08)
        c=capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
        V[n]=v-c; G[n]=v
    Vn=pd.DataFrame(V); Gn=pd.DataFrame(G)
    W=Sn.div(Sn.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    blendg=Gn.mean(axis=1); blendg=blendg[blendg.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    volsrc = blendg if vol_on_gross else blend
    bv,sb=vfun(volsrc,TGT)
    b=bv*blend/volsrc.replace(0,np.nan)
    b=b.fillna(0)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Sn.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn[n]/N*sc*sf; htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    return (r_out-htb/252).dropna()

tests={
 "baseline(vt,vol_on_net)":dict(),
 "vol_on_gross":dict(vol_on_gross=True),
 "ddof0":dict(vfun=lambda r,t: vtf(r,t,ddof=0)),
 "win63":dict(vfun=lambda r,t: vtf(r,t,min_win=63)),
 "sqrt250":dict(vfun=lambda r,t: vtf(r,t,annf=250)),
 "win90":dict(vfun=lambda r,t: vtf(r,t,min_win=90)),
}
for name,kw in tests.items():
    try:
        A=build_v(0.07,0.04,**kw)
        j=pd.concat([oldA.rename('o'),A.rename('n')],axis=1,join='inner').dropna()
        print(f"{name:26s} max|d|={float((j.o-j.n).abs().max()):.3e} mean|d|={float((j.o-j.n).abs().mean()):.3e}")
    except Exception as e:
        print(name,"ERR",e)
