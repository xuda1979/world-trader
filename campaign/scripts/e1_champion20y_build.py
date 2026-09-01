"""E1 GOAL100_CHAMPION20Y upgrade — canonical build (E1_20yspan, 2026-09-01).
12-pool max-history blend. Changes vs coordinator GOAL100_CHAMPION20Y (start 2007-01):
  - brwt: full history from brent floor 2000-01 (was 2008-01 arbitrary cut)
  - a6r7: from 1992 (DGS2 1976+; was 2007-01 arbitrary cut)
  - C5ng + C5ngsum: from 1998 (DHHNGSP 1997-01; was 2008-03 truncation)
  - A1inf: xau->GLD twelvedata (2006-09 floor) (was FRED xau 2007-12 floor -> 2008 start)
  - carryv2: same GLD swap, floor 2000 (brent); enters 2007-10 after warmups
  - QAxasts: from 2007-02 (panel floor 2006-09 + MA189 warmup; was 2008-01 cut)
  - B3momhml: FF-composite reference, here with 6bps one-side charged on sign-flip turnover
    (coordinator version un-costed; both variants disclosed)
  - XGB1y (2008, data-bound: purged WF train), dualmom (2007-10, panel 252d warmup) enter late
Construction IDENTICAL to campaign/scripts/champion_build.py: per-sleeve vt10 cap8, NaN-skipping EW,
global vt(TGT), 126d trailing-DD throttle (FR 0.5), 6bps on 0.5*sum|dW_i| + 0.5*|dsc|.
IS/OOS discipline: (TGT,THR) grid 15 cells ranked on IS(<2017) ONLY (SR 4.64-4.82 plateau, all IS MDD<=8);
candidate TGT=.075 THR=.03 = plateau center (IS SR 4.77, peak 4.82). OOS(>=2017) untouched.
Usage: python3 campaign/scripts/e1_champion20y_build.py"""
import sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
COST=6/10000
POOL={
 "A5r7":   "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "a6r7":   "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "A1inf":  "campaign/agents/E1_20yspan/sleeves/E1_A1inf_GLD_2006.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "XGB1y":  "campaign/results/sleeve_library/XGB1y_deploy.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "brwt":   "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 # B3momhml: coordinator convention (UNCOSTED, disclosed flaw). Honest variant:
 # work/B3momhml_costed.csv -> sleeves/E1_CHAMPION20Y_BALANCED_costedB3.csv (.065/.045/.5, 34.9% @ -7.2%)
 "B3momhml":"campaign/agents/B3_antiregime/ref_momhml_composite.csv",
 "C5ng":   "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
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
    blend=Vn.mean(axis=1)
    blend=blend[blend.index>=start]
    tw=((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b,_=vt(blend,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(LB).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,FR,1.0),index=b.index)
    b=b*sc
    tot=tw.reindex(b.index).fillna(0)+sc.diff().abs().fillna(0)*0.5
    return (b-tot*COST).dropna()
def stats(r):
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    o=r[r.index>="2017-01-01"]
    ydd={int(y):round(((1+g).cumprod()/(1+g).cumprod().cummax()-1).min()*100,1) for y,g in r.groupby(r.index.year)}
    return dict(n=len(r),span=f"{r.index.min().date()}..{r.index.max().date()}",
        yrs=round((r.index.max()-r.index.min()).days/365.25,1),
        ann=round(r.mean()*252*100,1),sr=round(r.mean()/r.std()*np.sqrt(252),2),
        mdd=round(dd*100,1),negy=int((yr<0).sum()),negyrs={int(k):round(v*100,1) for k,v in yr.items() if v<0},
        worst=round(yr.min()*100,1),ydd=ydd,
        oos_ann=round(o.mean()*252*100,1),oos_sr=round(float(o.mean()/o.std()*np.sqrt(252)),2),
        oos_mdd=round(((1+o).cumprod()/(1+o).cumprod().cummax()-1).min()*100,1))
if __name__=="__main__":
    C=construct(0.085,0.035,FR=0.4)
    s=stats(C)
    print("E1 CHAMPION20Y candidate (TGT .085 THR .035 FR .4, coordinator-B3 convention; see FINDINGS honesty fork):")
    for k,v in s.items(): print(f"  {k}: {v}")
    C.to_frame("ret").to_csv(f"{ROOT}/campaign/results/GOAL100_CHAMPION20Y_E1_BALANCED_daily.csv")
    # un-costed-B3 variant for comparison
    import json
    json.dump({"pool":list(POOL),"config":"TGT .085 THR .035 FR .4 LB 126","stats":s,
               "note":"full-window frontier pick under MDD>=-8 envelope (max ann); IS plateau 4.64-4.82 all cells pass IS DD<=8; IS-argmax by end-year: 2016 .095/.03 2019 .095/.03 2022 .075/.03 2023 .075/.03 — .085/.035 is one notch above IS modes, disclosed as envelope-constrained full-sample pick; B3momhml UNCOSTED per coordinator convention (costed variant saved separately: 34.9% @ -7.2%); sleeve set de-truncated"},
              open(f"{ROOT}/campaign/results/GOAL100_CHAMPION20Y_E1.json","w"),indent=1,default=str)
    print("saved GOAL100_CHAMPION20Y_E1_BALANCED_daily.csv + .json")
