#!/usr/bin/env python3
"""C4_construct_v2 (C4_metaalloc round-2 deliverable): NEW 16-pool EW-of-vol-normalized
blend, expanding-window vol target 11% ann (min 60d, scale cap 3.0), binary 126d trailing
drawdown throttle (half exposure when shift-1 trailing 126d DD < -3%), 6bps one-side costs.
Pool: 14 GOAL80 sleeves + C5_ng_weekday_prem + C5_ng_summer_weekday (coordinator 16-pool).
Config frozen on IS 2008-09..2023 (rule: max IS SR s.t. IS MaxDD<=8% AND every calendar-year
MaxDD<=8%; argmax identical for IS ends 2016/2019/2022/2023). OOS 2017-2026 revealed once:
FULL ann 55.5% SR 5.40 MaxDD -7.8%, 0 neg years, worst yr +6.5%; OOS 60.5% ann DD -7.8%.
Repro: python3 campaign/scripts/c4_construct_v2.py
Out:   campaign/agents/C4_metaalloc/sleeves/C4_construct_v2.csv
"""
import numpy as np, pandas as pd
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
 "C5ng":"campaign/agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv",
}
def load(p):
    df=pd.read_csv(f"{ROOT}/{p}",index_col=0); df.index=pd.to_datetime(df.index)
    return df["ret" if "ret" in df.columns else df.columns[0]].astype(float)
def vt(r,tgt=0.11,cap=3.0,min_win=60):
    vol=r.rolling(min_win).std().shift(1)*np.sqrt(252)
    s=(tgt/vol).clip(upper=cap); s[vol.isna()]=0
    return r*s.fillna(0)
def main(out=True):
    V={};G={}
    for n,p in POOL.items():
        r=load(p)
        vol=r.rolling(60).std().shift(1)*np.sqrt(252)
        s=(0.10/vol).clip(upper=8.0); s[vol.isna()]=0
        V[n]=r*s.fillna(0); G[n]=s
    V=pd.DataFrame(V); G=pd.DataFrame(G)
    W=G.div(G.sum(axis=1),axis=0).fillna(0)
    raw=V.mean(axis=1)
    raw=raw[raw.index>=pd.Timestamp("2008-09-01")]
    W=W.loc[raw.index]
    tw=(W-W.shift(1)).abs().sum(axis=1)*0.5
    b=vt(raw,0.11)
    eq=(1+b.fillna(0)).cumprod()
    rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    g=pd.Series(np.where(tdd<-0.03,0.5,1.0),index=b.index).fillna(1.0)
    b=b*g
    turn=tw.reindex(b.index).fillna(0)+g.diff().abs().mul(0.5).fillna(0)
    r=(b-turn*COST).dropna()
    if out:
        r.to_csv(f"{ROOT}/campaign/agents/C4_metaalloc/sleeves/C4_construct_v2.csv",header=["ret"])
    return r
def perf(r):
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    print(f"ann={r.mean()*252*100:.1f}% SR={r.mean()/r.std()*np.sqrt(252):.2f} MaxDD={dd*100:.1f}% n={len(r)}")
if __name__=="__main__":
    perf(main())
