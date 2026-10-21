"""Rebuild STRICTTRADE champion from 12 sleeve files using documented champion_build
construction (trailing vt10 per sleeve, EW, global vt, throttle, costs). Try to match
the committed STRICTTRADE CSV to establish the aggregation convention."""
import sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
POOL={
 "brwt15":f"{ROOT}/campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv",
 "brwt10":f"{ROOT}/campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv",
 "brwt7":f"{ROOT}/campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv",
 "brwt5":f"{ROOT}/campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv",
 "C5ng":f"{ROOT}/campaign/agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv",
 "C5ngsum":f"{ROOT}/campaign/agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv",
 "A5r2":f"{ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7":f"{ROOT}/campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv",
 "QAxasts":f"{ROOT}/campaign/agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv",
 "carryv2":f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv",
 "dualmom":f"{ROOT}/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "XGB1y":f"{ROOT}/campaign/results/sleeve_library/XGB1y_deploy.csv",
}
def load(p):
    df=pd.read_csv(p,index_col=0); df.index=pd.to_datetime(df.index)
    c="ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)
raw={n:load(p) for n,p in POOL.items()}
rawdf=pd.DataFrame(raw)
print("sleeve span:"); print(rawdf.apply(lambda c:(c.dropna().index.min().date(),c.dropna().index.max().date())))
def vt(r,tgt,min_win=60,cap=8.0):
    vol=r.rolling(min_win).std().shift(1)*np.sqrt(252)
    s=(tgt/vol).clip(upper=cap); s[vol.isna()]=0
    return r*s.fillna(0),s
target=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
# standard champion_build BALANCED on 12-pool
COST=6/10000
def construct(pool,TGTA=0.085,THRA=0.04,TGTB=0.11,THRB=0.03,FR=0.5,LB=126,extra_cost=0.0):
    def one(TGT,THR):
        V={};S={}
        for n in pool:
            v,s=vt(raw[n],0.10); V[n]=v;S[n]=s
        Vn=pd.DataFrame(V);Sn=pd.DataFrame(S)
        W=Sn.div(Sn.sum(axis=1),axis=0).fillna(0)
        blend=Vn.mean(axis=1); blend=blend[blend.index>="2008-09-01"]
        tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
        b,_=vt(blend,TGT)
        eq=(1+b.fillna(0)).cumprod()
        rm=eq.rolling(LB).max().shift(1); tdd=eq.shift(1)/rm-1
        sc=pd.Series(np.where(tdd<-THR,FR,1.0),index=b.index); b=b*sc
        dsc=sc.diff().abs()*0.5
        tot=tw.reindex(b.index).fillna(0)+dsc.fillna(0)
        return (b-tot*COST-extra_cost).dropna()
    A=one(TGTA,THRA); B=one(TGTB,THRB)
    return ((A+B)/2).dropna()
bal=construct(list(POOL))
j=pd.concat([target.rename("target"),bal.rename("rebuild")],axis=1,join="inner").dropna()
print(f"\nn={len(j)} corr={j.corr().iloc[0,1]:.6f} maxdiff={ (j.target-j.rebuild).abs().max():.3e}")
print(f"target ann={target.mean()*252*100:.1f}% SR={target.mean()/target.std()*np.sqrt(252):.2f}")
print(f"rebuild ann={bal.mean()*252*100:.1f}% SR={bal.mean()/bal.std()*np.sqrt(252):.2f}")
# also compare with FINAL_TRUTH balanced (14-pool) restricted
ft=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_FINAL_TRUTH_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
ij=pd.concat([target.rename("st"),ft.rename("ft")],axis=1,join="inner").dropna()
print(f"\nSTRICTTRADE vs FINAL_TRUTH: n={len(ij)} corr={ij.corr().iloc[0,1]:.4f} ann_st={target.mean()*252*100:.1f} ann_ft={ft.mean()*252*100:.1f}")
ib=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_IBKR_STRICT_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
ij2=pd.concat([target.rename("st"),ib.rename("ibkr")],axis=1,join="inner").dropna()
print(f"STRICTTRADE vs IBKR_STRICT: n={len(ij2)} corr={ij2.corr().iloc[0,1]:.4f} ann_ibkr={ib.mean()*252*100:.1f}")
print(f"rows only in IBKR: {len(ib)-len(ij2)}; target len {len(target)}")
# Try: is STRICTTRADE = EW-12 of IBKR sleeve legs with cost haircut? Check simple avg relation:
diff=(target-ib).reindex(target.index).dropna()
print("mean(STRICTTRADE-IBKR daily)=",diff.mean()*1e4,"bps/day; std=",diff.std()*1e4)
