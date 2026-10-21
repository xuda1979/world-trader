"""GOAL100 coordinator v2: exact COORD_FINAL construction + full pool + new C sleeves.
EW-of-vol-normalized (per-sleeve vt10, weights ~ scale) + global vt + trailing 126d DD throttle.
Usage: python3 campaign/scripts/coord_goal100_v2.py
"""
import numpy as np, pandas as pd, glob, os, json
ROOT="/Users/daxu/software/world-trader"
COST=6/10000

POOL={
 "H21_f5":"tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv",
 "H21_br":"tools/quant/reports/xgb_horizons/h21_breadth_gate_daily.csv",
 "A5r7":"campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "a6r7":"campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv",
 "A1inf":"campaign/agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv",
 "QAxasts":"campaign/agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv",
 "A5r2":"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "XGB1y":"campaign/results/sleeve_library/XGB1y_deploy.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "carryv2":"campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv",
 "A5r4":"campaign/agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv",
 "brwt":"campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv",
 "B3momhml":"campaign/agents/B3_antiregime/ref_momhml_composite.csv",
}
# any new C-series sleeves get added dynamically
for f in sorted(glob.glob(f"{ROOT}/campaign/agents/C*/sleeves/*.csv")):
    if f.endswith('.meta'): continue
    name=os.path.basename(f)[:-4]
    POOL.setdefault(name, os.path.relpath(f, ROOT))

def load(p):
    df=pd.read_csv(f"{ROOT}/{p}",index_col=0); df.index=pd.to_datetime(df.index)
    c="ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def vt(r,tgt,min_win=60):
    vol=r.rolling(min_win).std().shift(1)*np.sqrt(252)
    scale=(tgt/vol).clip(upper=8.0); scale[vol.isna()]=0
    return r*scale.fillna(0), scale

def perf(r,label=""):
    r=r.dropna(); eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    sr=r.mean()/r.std()*np.sqrt(252); ann=r.mean()*252
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    o=r[r.index>="2017-01-01"]; oeq=(1+o).cumprod(); odd=(oeq/oeq.cummax()-1).min()
    osr=o.mean()/o.std()*np.sqrt(252); oann=o.mean()*252
    print(f"{label}: FULL ann {ann*100:.1f}% SR {sr:.2f} DD {dd*100:.1f}% negy {(yr<0).sum()} worst {yr.min()*100:.1f}% | OOS17+ ann {oann*100:.1f}% SR {osr:.2f} DD {odd*100:.1f}%")
    return dict(ann=ann,sr=sr,mdd=dd,negy=int((yr<0).sum()),worst=yr.min(),
                oos=dict(ann=oann,sr=osr,mdd=odd))

def blend(names, TGT=0.075, DD_THR=0.04, min_hist=750):
    D={}
    for n in names:
        try:
            r=load(POOL[n]); 
        except Exception as e:
            print("skip",n,e); continue
        if len(r)>=min_hist: D[n]=r
    V=pd.DataFrame(D)
    scales={}
    Vt={}; 
    for n in V.columns:
        v,s=vt(V[n],0.10); Vt[n]=v; scales[n]=s
    Vn=pd.DataFrame(Vt); Wn=pd.DataFrame(scales)
    W=Wn.div(Wn.sum(axis=1),axis=0).fillna(0)
    raw=Vn.mean(axis=1)[lambda x:x.index>="2008-09-01"]
    tw=(W-W.shift(1)).abs().sum(axis=1)*0.5
    b,_=vt(raw,TGT)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-DD_THR,0.5,1.0),index=b.index)
    b=b*sc
    dsc=sc.diff().abs()*0.5
    tot=tw.reindex(b.index).fillna(0)+dsc.fillna(0)
    r=(b-tot*COST).dropna()
    return r, list(V.columns)

if __name__=="__main__":
    # 1. baseline repro
    r14,names=blend(list(POOL.keys()) if False else ["H21_f5","H21_br","A5r7","a6r7","A1inf","QAxasts","A5r2","A1credit","XGB1y","dualmom","carryv2","A5r4","brwt","B3momhml"])
    perf(r14,"COORD14 repro")
    # 2. with all new C sleeves (>=750d history)
    allnames=list(POOL.keys())
    rN,namesN=blend(allnames)
    perf(rN,f"COORD+new ({len(namesN)})")
    # sub-periods DD check
    for a,bb in [("08-12","2008","2012"),("13-15","2013","2015"),("16-18","2016","2018"),("19-21","2019","2021"),("22-24","2022","2024"),("25-26","2025","2026")]:
        pass
    # save
    out=pd.DataFrame({"ret":rN}); out.to_csv(f"{ROOT}/campaign/results/GOAL100_v2_daily.csv")
    json.dump({"sleeves":namesN}, open(f"{ROOT}/campaign/results/GOAL100_v2.json","w"))
    print("saved GOAL100_v2_daily.csv")
