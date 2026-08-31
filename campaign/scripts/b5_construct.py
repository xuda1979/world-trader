#!/usr/bin/env python3
"""B5_construct: Portfolio construction maximizing ann% subject to MaxDD<=8%.
Reconstructs the 13-sleeve EW-of-trailing-vol-normalized blend with a trailing
126d drawdown governor (thr 4%) and 7.5% vol target. TRAILING-ONLY (shift-1) —
no lookahead. Costs 6bps one-side on rebalancing turnover.

Repro: python3 campaign/scripts/b5_construct.py
Output: campaign/agents/B5_construct/sleeves/B5_CONSTRUCT_vt75_dd4_13.csv
"""
import numpy as np, pandas as pd

ROOT="/Users/daxu/software/world-trader"
def load(p,col=None):
    df=pd.read_csv(p,index_col=0); df.index=pd.to_datetime(df.index)
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
}
TGT_VOL=0.075; DD_LB=126; DD_THR=0.04; COST=6/10000

def vt(r,tgt,min_win=60):
    r=r.copy(); vol=r.rolling(min_win).std().shift(1)*np.sqrt(252)
    scale=tgt/vol; scale=scale.clip(upper=8.0); scale[vol.isna()]=0
    return r*scale.fillna(0), scale

def main():
    D={n:load(f"{ROOT}/{p}") for n,p in POOL.items()}
    V=pd.DataFrame({n:vt(D[n],0.10)[0] for n in POOL})
    S=pd.DataFrame({n:vt(D[n],0.10)[1] for n in POOL})
    W=S.div(S.sum(axis=1),axis=0).fillna(0)
    blend=V.mean(axis=1); blend=blend[blend.index>="2008-09-01"]
    tw=(W-W.shift(1)).abs().sum(axis=1)*0.5
    b,_=vt(blend,TGT_VOL)
    eq=(1+b.fillna(0)).cumprod(); rm=eq.rolling(DD_LB).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-DD_THR,0.5,1.0),index=b.index)
    b=b*sc
    dsc=sc.diff().abs()*0.5
    tot=tw.reindex(b.index).fillna(0)+dsc.fillna(0)
    r=(b-tot*COST).dropna()
    out=pd.DataFrame({"ret":r})
    out.to_csv(f"{ROOT}/campaign/agents/B5_construct/sleeves/B5_CONSTRUCT_vt75_dd4_13.csv")
    return perf(r)

def perf(r):
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    sr=r.mean()/r.std()*np.sqrt(252); ann=r.mean()*252*100
    print(f"ann={ann:.1f}% SR={sr:.2f} DD={dd*100:.1f}% n={len(r)}")
    return dict(ann=ann,sr=sr,dd=dd)

if __name__=="__main__":
    main()
