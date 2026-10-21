"""E1 idea6: max-history 12-pool blend (de-truncated sleeves), champion_build construction.
IS/OOS discipline: (TGT,THR) grid ranked on IS (<2017-01) with IS-DD<=8% constraint; report OOS after."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd

ROOT="/Users/daxu/software/world-trader"
COST=6/10000
POOL={
 "A5r7":   "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",          # 1990+
 "a6r7":   "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",        # 1992+
 "A1inf":  "campaign/agents/E1_20yspan/sleeves/E1_A1inf_GLD_2006.csv",                # 2006-09
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",         # 2007-02
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",          # 1990+
 "XGB1y":  "campaign/results/sleeve_library/XGB1y_deploy.csv",                        # 2008 data-bound
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",            # 2007-10 data-bound
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",              # 2007-06
 "brwt":   "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",        # 2001+
 "B3momhml":"campaign/agents/B3_antiregime/ref_momhml_composite.csv",                 # 2006-01 REFERENCE (no costs!) 
 "C5ng":   "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",             # 1998+
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",           # 1998+
}
def load(p):
    df=pd.read_csv(f"{ROOT}/{p}",index_col=0); df.index=pd.to_datetime(df.index)
    c="ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)
def vt(r,tgt,min_win=60,cap=8.0):
    vol=r.rolling(min_win).std().shift(1)*np.sqrt(252)
    s=(tgt/vol).clip(upper=cap); s[vol.isna()]=0
    return r*s.fillna(0),s
def construct(TGT,THR,FR=0.5,LB=126,start="2006-10-01"):
    V,S={},{}
    for n,p in POOL.items():
        r=load(p); v,s=vt(r,0.10); V[n]=v; S[n]=s
    Vn=pd.DataFrame(V); Sn=pd.DataFrame(S)
    W=Sn.div(Sn.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1)              # NaN-skipping EW: members enter as data appears
    blend=blend[blend.index>=start]
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,_=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod()
    rm=eq.rolling(LB).max().shift(1)
    tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,FR,1.0),index=b.index)
    b=b*sc
    dsc=sc.diff().abs()*0.5
    tot=tw.reindex(b.index).fillna(0)+dsc.fillna(0)
    return (b-tot*COST).dropna()
def stats(r):
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    o=r[r.index>="2017-01-01"]
    ydd={}
    for y,g in r.groupby(r.index.year):
        e=(1+g).cumprod(); ydd[int(y)]=round(((e/e.cummax()-1).min())*100,1)
    return dict(ann=round(r.mean()*252*100,1),sr=round(r.mean()/r.std()*np.sqrt(252),2),
                mdd=round(dd*100,1),negy=int((yr<0).sum()),worst=round(yr.min()*100,1),
                oos_ann=round(o.mean()*252*100,1),oos_sr=round(float(o.mean()/o.std()*np.sqrt(252)),2),
                oos_mdd=round(((1+o).cumprod()/(1+o).cumprod().cummax()-1).min()*100,1),ydd=ydd)

# IS grid (<2017): constraint IS MDD<=8, maximize IS ann? coordinator used max SR s.t. DD<=8 & each IS yr DD<=8
grid=[]
for TGT in [0.055,0.065,0.075,0.085,0.095]:
    for THR in [0.03,0.04,0.05]:
        r=construct(TGT,THR)
        i=r[r.index<"2017-01-01"]
        eq=(1+i).cumprod(); mdd=(eq/eq.cummax()-1).min()
        yrdd=i.groupby(i.index.year).apply(lambda x:((1+x).cumprod()/(1+x).cumprod().cummax()-1).min())
        ok = mdd>=-0.08 and yrdd.min()>=-0.08
        sr=i.mean()/i.std()*np.sqrt(252)
        grid.append((TGT,THR,round(sr,2),round(mdd*100,1),ok))
print("IS grid (TGT,THR,IS_SR,IS_MDD,okDD<=8):")
for g in grid: print("  ",g)

print("\n=== FULL-window eval per grid cell (not used for selection; OOS >=2017 untouched) ===")
for TGT,THR in [(0.055,0.03),(0.065,0.04),(0.075,0.03),(0.085,0.03),(0.085,0.04),(0.095,0.03),(0.095,0.04)]:
    r=construct(TGT,THR)
    s=stats(r)
    print(f" TGT{TGT} THR{THR}: ann={s['ann']}% SR={s['sr']} MDD={s['mdd']}% negy={s['negy']} worst={s['worst']}% | OOS(17+): ann={s['oos_ann']}% SR={s['oos_sr']} MDD={s['oos_mdd']}%")

A=construct(0.065,0.04); B=construct(0.085,0.03); BAL=((A+B)/2).dropna()
print("\nE1 20Y configs:")
for nm,r in [("SAFE(A .065/.04)",A),("AGGR(B .085/.03)",B),("BALANCED",BAL)]:
    s=stats(r)
    print(f" {nm}: span {r.index.min().date()}..{r.index.max().date()} ({(r.index.max()-r.index.min()).days/365.25:.1f}y)")
    print(f"   ann={s['ann']}% SR={s['sr']} MDD={s['mdd']}% negy={s['negy']} worst={s['worst']}%")
    print(f"   OOS: ann={s['oos_ann']}% SR={s['oos_sr']} MDD={s['oos_mdd']}%")
    print(f"   yearly DD%: {s['ydd']}")

# incumbent comparison on common window
inc=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_CHAMPION20Y_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
for nm,r in [("E1_BAL",BAL)]:
    j=pd.concat([r.rename('e1'),inc.rename('inc')],axis=1,join='inner').dropna()
    si=stats(j['inc']); se=stats(j['e1'])
    print(f"\ncommon-window ({j.index.min().date()}..{j.index.max().date()}):")
    print(f"  incumbent: ann={si['ann']}% SR={si['sr']} MDD={si['mdd']}% negy={si['negy']}")
    print(f"  E1_BAL   : ann={se['ann']}% SR={se['sr']} MDD={se['mdd']}% negy={se['negy']}")

# honesty variant: B3momhml with 6bps costs charged on its sign-flip turnover
f=pd.concat([__import__('campaign.harness.data',fromlist=['ff_factors']).ff_factors(),__import__('campaign.harness.data',fromlist=['ff_mom']).ff_mom()],axis=1).loc['2006':]
mom=f['Mom']-f['RF']; hml=f['HML']-f['RF']
combo=mom*1.0+hml*0.2
pos=np.sign(combo)
gross=(pos.shift(1)*combo)
vol=gross.rolling(60).std()*np.sqrt(252)
gross=(gross/(vol.shift(1).clip(lower=0.03))*0.08).fillna(0.0)
turn=pos.diff().abs().fillna(0.0)*0.5
gross_h=gross-turn*COST
POOL_H=dict(POOL); import pandas as _pd
save_sleeve=__import__('campaign.harness.data',fromlist=['save_sleeve']).save_sleeve
save_sleeve(gross_h.loc['2006-01-04':],f"{ROOT}/campaign/agents/E1_20yspan/work/B3momhml_costed.csv","B3momhml with 6bps one-side on half-turnover (honest variant)")
POOL_H["B3momhml"]=f"campaign/agents/E1_20yspan/work/B3momhml_costed.csv"
def construct_H(TGT,THR,FR=0.5,LB=126,start="2006-10-01"):
    V,S={},{}
    for n,p in POOL_H.items():
        r=load(p); v,s=vt(r,0.10); V[n]=v; S[n]=s
    Vn=pd.DataFrame(V); Sn=pd.DataFrame(S)
    W=Sn.div(Sn.sum(axis=1),axis=0).fillna(0)
    blend=Vn.mean(axis=1); blend=blend[blend.index>=start]
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,_=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(LB).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,FR,1.0),index=b.index); b=b*sc
    tot=tw.reindex(b.index).fillna(0)+sc.diff().abs()*0.5*0.5*2  # dsc
    return (b-(tw.reindex(b.index).fillna(0)+sc.diff().abs().fillna(0)*0.5)*COST).dropna()
AH=construct_H(0.065,0.04); BH=construct_H(0.085,0.03); BALH=((AH+BH)/2).dropna()
sH=stats(BALH)
print(f"\nHONEST-VARIANT BALANCED (B3momhml costed): ann={sH['ann']}% SR={sH['sr']} MDD={sH['mdd']}% negy={sH['negy']} OOS ann={sH['oos_ann']}%")
