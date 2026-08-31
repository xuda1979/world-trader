"""C4 construction engine: vol-normalized sleeves -> weights -> vt + throttle.
All management uses shift-1 trailing data. Costs 6bps/side on turnover."""
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
COST=6/10000

def load(p,col=None):
    df=pd.read_csv(f"{ROOT}/{p}",index_col=0); df.index=pd.to_datetime(df.index)
    c=col if col else ("ret" if "ret" in df.columns else df.columns[0])
    return df[c].astype(float)

POOL={
 "H21_f5":"tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv",
 "H21_br":"tools/quant/reports/xgb_horizons/h21_breadth_gate_daily.csv",
 "CHAMP":"campaign/results/WORLDTRADER8_daily.csv",
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
 "B3mh":"campaign/agents/B3_antiregime/ref_momhml_composite.csv",
}

def vt(r,tgt,min_win=60,cap=8.0):
    vol=r.rolling(min_win).std().shift(1)*np.sqrt(252)
    scale=(tgt/vol).clip(upper=cap); scale[vol.isna()]=0
    return r*scale.fillna(0), scale

def build(D=None, tgt=0.075, dd_lb=126, dd_thr=0.04, dd_cut=0.5, wmode="ew",
          start="2008-09-01", costs=True, pv=0.10, pv_win=60, throttle=True):
    """D: dict name->raw returns. Returns (net daily ret Series, weights DF)."""
    if D is None:
        D={n:load(p) for n,p in POOL.items()}
    V={}; S={}
    for n,r in D.items():
        v,s=vt(r,pv,pv_win); V[n]=v; S[n]=s
    V=pd.DataFrame(V); S=pd.DataFrame(S)
    idx=V.index[V.index>=pd.Timestamp(start)]
    if wmode=="ew":
        blend=V.mean(axis=1)
        W=S.div(S.sum(axis=1),axis=0).fillna(0)  # implied per-sleeve weight
    blend=blend[blend.index>=pd.Timestamp(start)]
    tw=(W-W.shift(1)).abs().sum(axis=1)*0.5
    b,sc=vt(blend,tgt)
    if throttle:
        eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(dd_lb).max().shift(1)
        tdd=eq.shift(1)/rm-1
        g=pd.Series(np.where(tdd<-dd_thr,dd_cut,1.0),index=b.index)
    else:
        g=pd.Series(1.0,index=b.index)
    b=b*g
    turnover=tw.reindex(b.index).fillna(0)+g.diff().abs().mul(0.5).fillna(0)
    r=b-(turnover*COST if costs else 0)
    return r.dropna(), W.loc[r.index]

def perf(r, label=""):
    r=r.dropna(); eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    sr=r.mean()/r.std()*np.sqrt(252); ann=r.mean()*252
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    def sub(a,b_):
        x=r[(r.index>=a)&(r.index<b_)]
        if len(x)<100: return None
        e=(1+x).cumprod(); d=(e/e.cummax()-1).min()
        return dict(sr=x.mean()/x.std()*np.sqrt(252), ann=x.mean()*252, mdd=d)
    out=dict(ann=ann,vol=r.std()*np.sqrt(252),sr=sr,mdd=dd,negy=int((yr<0).sum()),
             worst=yr.min(),n=len(r),
             IS=sub("2008-01-01","2017-01-01"),OOS=sub("2017-01-01","2099-01-01"),
             OOS1=sub("2017-01-01","2022-01-01"),OOS2=sub("2022-01-01","2099-01-01"),
             yearly={int(k):round(v*100,1) for k,v in yr.items()})
    if label: print(f"[{label}] ann {ann*100:5.1f}% SR {sr:4.2f} MDD {dd*100:5.1f}% negy {out['negy']}"
                    f" | IS SR {out['IS']['sr']:4.2f} DD {out['IS']['mdd']*100:5.1f}%"
                    f" | OOS ann {out['OOS']['ann']*100:5.1f}% SR {out['OOS']['sr']:4.2f} DD {out['OOS']['mdd']*100:5.1f}%"
                    f" | OOS1 DD {out['OOS1']['mdd']*100:5.1f}% OOS2 DD {out['OOS2']['mdd']*100:5.1f}%")
    return out
