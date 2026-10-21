"""C4 round-2 engine: 16-pool EW-of-vt10 + global vt + DD throttle. Honest trailing-only."""
import numpy as np, pandas as pd, os
ROOT="/Users/daxu/software/world-trader"
COST=6/10000
BASE=["H21_f5","H21_br","A5r7","a6r7","A1inf","QAxasts","A5r2","A1credit","XGB1y",
      "dualmom","carryv2","A5r4","brwt","B3momhml"]
PATHS={
 "H21_f5":"tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv",
 "H21_br":"tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv",
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
 "C5ng":"campaign/agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv",
 "C5ngsumddt":"campaign/agents/C5_newdata/sleeves/C5_ng_summer_weekday_ddt.csv",
}
PATHS["H21_br"]="tools/quant/reports/xgb_horizons/h21_breadth_gate_daily.csv"
def load(n):
    df=pd.read_csv(f"{ROOT}/{PATHS[n]}",index_col=0); df.index=pd.to_datetime(df.index)
    c="ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

CACHE=f"{ROOT}/campaign/agents/C4_metaalloc/_cache_vt.pkl"
def build_cache(comp=("C5ng","C5ngsum"), pcap=8.0):
    names=BASE+list(comp)
    V={};G={}
    for n in names:
        r=load(n); vol=r.rolling(60).std().shift(1)*np.sqrt(252)
        s=(0.10/vol).clip(upper=pcap); s[vol.isna()]=0
        V[n]=r*s.fillna(0); G[n]=s
    V=pd.DataFrame(V); G=pd.DataFrame(G)
    W=G.div(G.sum(axis=1),axis=0).fillna(0)
    raw=V.mean(axis=1)
    raw=raw[raw.index>=pd.Timestamp("2008-09-01")]
    W=W.loc[raw.index]
    tw=(W-W.shift(1)).abs().sum(axis=1)*0.5
    pd.to_pickle({"V":V,"raw":raw,"tw":tw,"names":names},CACHE)
    return raw,tw

def get_raw(comp=("C5ng","C5ngsum")):
    d=pd.read_pickle(CACHE)
    return d["raw"],d["tw"]

def vt(r,tgt,cap=3.0,min_win=60):
    vol=r.rolling(min_win).std().shift(1)*np.sqrt(252)
    s=(tgt/vol).clip(upper=cap); s[vol.isna()]=0
    return (r*s.fillna(0)),s

def run(raw,tw,tgt,thr,fr,lb):
    b,_=vt(raw,tgt)
    eq=(1+b.fillna(0)).cumprod()
    rm=eq.rolling(lb).max().shift(1)
    tdd=eq.shift(1)/rm-1
    g=pd.Series(np.where(tdd< -thr,fr,1.0),index=b.index).fillna(1.0)
    b=b*g
    turn=tw.reindex(b.index).fillna(0)+g.diff().abs().mul(0.5).fillna(0)
    r=(b-turn*COST).dropna()
    return r

def stats(r):
    r=r.dropna(); eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    ydd={y:(eq[eq.index.year==y]/eq[eq.index.year==y].cummax()-1).min() for y in sorted(set(eq.index.year))}
    return dict(ann=r.mean()*252, sr=r.mean()/r.std()*np.sqrt(252), mdd=dd,
                negy=int((yr<0).sum()), worst=yr.min(), ydd=ydd, n=len(r))
def sub(r,a,b):
    w=r[(r.index>=a)&(r.index<b)]; eq=(1+w).cumprod()
    return dict(ann=w.mean()*252, sr=w.mean()/w.std()*np.sqrt(252) if w.std()>0 else 0,
                mdd=(eq/eq.cummax()-1).min())
def show(tag,s):
    print(f"{tag}: ann {s['ann']*100:5.1f}% SR {s['sr']:5.2f} DD {s['mdd']*100:5.1f}% negy {s['negy']} worst {s['worst']*100:5.1f}%")
