import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"; COST=6/10000
POOL={
 "A5r7":"campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "a6r7":"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "A1inf":"campaign/agents/E1_20yspan/sleeves/E1_A1inf_GLD_2006.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "XGB1y":"campaign/results/sleeve_library/XGB1y_deploy.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "brwt":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "B3momhml":"campaign/agents/E1_20yspan/work/B3momhml_costed.csv",
 "C5ng":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv"}
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
    blend=Vn.mean(axis=1); blend=blend[blend.index>=start]
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,_=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(LB).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,FR,1.0),index=b.index); b=b*sc
    tot=tw.reindex(b.index).fillna(0)+sc.diff().abs().fillna(0)*0.5
    return (b-tot*COST).dropna()
