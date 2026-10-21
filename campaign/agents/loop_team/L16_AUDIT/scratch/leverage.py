import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
exec(open('campaign/agents/loop_team/L16_AUDIT/scratch/audit_b_build.py').read().split("A,ma=build")[0])

# L16-exact construction (Sn at 0.08)
Sn08=pd.DataFrame({n:vt(sn(p),0.08)[1] for n,p in POOL.items()}).dropna(how='all')
capW8=Sn08/N
def build8(TGT,THR):
    V={}; S={}
    for n in POOL:
        r=sn(POOL[n]); v,s=vt(r,0.08)
        V[n]=v-capW8[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4); S[n]=s
    Vn=pd.DataFrame(V); Sd=pd.DataFrame(S)
    W=Sn08.div(Sn08.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,sb=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=b.index); b=b*sc; dsc=sc.diff().abs()*0.5
    r_out=b-(tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    htb=pd.Series(0.0,index=Sn08.index)
    for n in POOL:
        sf=SHORTF[n]
        if sf>0:
            gn=Sn08[n]/N*sc*sf; htb=htb+gn*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
    out=(r_out-htb/252).dropna()
    return out,sb,Sd,sc,W,tw

A,sbA,SdA,scA,WA,twA=build8(0.07,0.04)
B,sbB,SdB,scB,WB,twB=build8(0.091,0.03)
BAL=((A+B)/2).dropna()
# verify byte exact
for fn,r in [("GOAL100_HONEST11L16_SAFE_daily.csv",A),("GOAL100_HONEST11L16_AGGRESSIVE_daily.csv",B),("GOAL100_HONEST11L16_BALANCED_daily.csv",BAL)]:
    old=pd.read_csv(f"{ROOT}/campaign/results/{fn}",index_col=0,parse_dates=True).iloc[:,0]
    j=pd.concat([old.rename('o'),r.rename('n')],axis=1,join='inner').dropna()
    print(f"verify {fn}: max|d|={float((j.o-j.n).abs().max()):.3e}")

idx = BAL.index
# L16 published def: EW of per-sleeve |vt scale| (capital-real gross, per config, then averaged for BAL)
scA_clip=SdA.clip(upper=8.0)
scB_clip=SdB.clip(upper=8.0)
grossA = scA_clip.mean(axis=1)   # EW of per-sleeve scale
grossB = scB_clip.mean(axis=1)
# throttle multiplies exposure by 0.5 when tripped
grossA_thr = grossA*scA.reindex(grossA.index).fillna(1.0)
grossB_thr = grossB*scB.reindex(grossB.index).fillna(1.0)
bal_gross = 0.5*(grossA_thr+grossB_thr)
bal_gross = bal_gross.reindex(idx)
print("\n--- LEVERAGE (published def: EW of per-sleeve |vt scale|, x throttle) ---")
for nm,g in [("SAFE",grossA_thr),("AGGR",grossB_thr),("BAL",bal_gross)]:
    gg=g.dropna()
    gg=gg[gg.index>='2008-03-31']
    print(f"{nm}: mean {gg.mean():.3f}x  median {gg.median():.3f}x  p95 {gg.quantile(0.95):.3f}x  max {gg.max():.3f}x  frac>1.6: {(gg>1.6).mean()*100:.1f}%  frac>2: {(gg>2).mean()*100:.1f}%")
print("BAL days >1.6:", int((bal_gross.dropna()>1.6).sum()), "of", int(bal_gross.notna().sum()))

# conservative all-in: per-sleeve scale x global scale x throttle
gA_all = (SdA.mean(axis=1)*sbA*scA.reindex(SdA.index).fillna(1.0))
gB_all = (SdB.mean(axis=1)*sbB*scB.reindex(SdB.index).fillna(1.0))
print("\n--- CONSERVATIVE all-in (mean per-sleeve scale x global scalar x throttle) ---")
for nm,g in [("SAFE",gA_all),("AGGR",gB_all),("BAL",0.5*(gA_all+gB_all))]:
    gg=g.reindex(idx).dropna()
    print(f"{nm}: mean {gg.mean():.3f}x  median {gg.median():.3f}x  p95 {gg.quantile(0.95):.3f}x  max {gg.max():.3f}x")

# yearly gross and yearly returns check (neg-year claim), BAL
yr_ret = BAL.groupby(BAL.index.year).apply(lambda x:(1+x).prod()-1)
gB_yr = bal_gross.dropna().groupby(bal_gross.dropna().index.year).mean()
print("\nyear:  BAL ret   mean gross(1.59x-def)")
for y in yr_ret.index:
    print(f"{y}: {yr_ret[y]*100:8.2f}%   {gB_yr.get(y,float('nan')):.3f}x")
print("\nmax gross day BAL:",bal_gross.max(),"on",bal_gross.idxmax().date())
print("BAL gross>1.6 top dates:"); print(bal_gross.dropna()[bal_gross.dropna()>1.6].sort_values(ascending=False).head(8))
bal_gross.to_frame('gross').to_csv(f"{ROOT}/campaign/agents/loop_team/L16_AUDIT/scratch/bal_gross_path.csv")
