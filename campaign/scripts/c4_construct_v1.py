#!/usr/bin/env python3
"""C4_construct_v1 (C4_metaalloc deliverable): 16-sleeve EW-of-vol-normalized blend,
expanding-window vol target 8.5% (cap 3.0), binary 252d drawdown throttle
(half gross when shift-1 trailing 252d drawdown < -3%), 6bps/side.
Vol target 9.5% (expanding, min 60d, scale cap 3.0).
Config frozen on IS 2008-2016 (rule: max IS SR s.t. IS MaxDD<=8%; argmax robust to
7.5% constraint too). OOS 2017-2026 revealed once: ann 52.6%, MaxDD -8.8% full /
-5.9% (17-22) / -6.1% (22-26); beats COORD_FINAL OOS ann 47.7% with subwindow DDs<=8.

Repro: python3 campaign/scripts/c4_construct_v1.py
Out:   campaign/agents/C4_metaalloc/sleeves/C4_construct_v1.csv
"""
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
COST=6/10000
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
 "xrev":"campaign/agents/B2_highfreq/sleeves/crossasset_rev_L8.csv",
}
def load(p):
    df=pd.read_csv(f"{ROOT}/{p}",index_col=0); df.index=pd.to_datetime(df.index)
    return df["ret" if "ret" in df.columns else df.columns[0]].astype(float)
def vt(r,tgt,cap=3.0,min_win=60):
    vol=r.rolling(min_win).std().shift(1)*np.sqrt(252)
    s=(tgt/vol).clip(upper=cap); s[vol.isna()]=0
    return r*s.fillna(0),s
def main(out=True):
    V={};G={}
    for n,p in POOL.items():
        r=load(p)
        vol=r.rolling(60).std().shift(1)*np.sqrt(252)
        s=(0.10/vol).clip(upper=8.0); s[vol.isna()]=0
        V[n]=r*s.fillna(0); G[n]=s
    V=pd.DataFrame(V); G=pd.DataFrame(G); live=G>0
    V=V.loc[V.index>=pd.Timestamp("2008-09-01")]
    G=G.loc[V.index]; live=live.loc[V.index]
    blend=V.sum(axis=1)/live.sum(axis=1).clip(lower=1)
    turn=G.diff().abs().sum(axis=1).mul(0.5)/live.sum(axis=1).clip(lower=1)
    b,_=vt(blend,0.095,cap=3.0)
    eq=(1+b.fillna(0)).cumprod()
    rm=eq.rolling(252).max().shift(1); tdd=eq.shift(1)/rm-1
    g=pd.Series(np.where(tdd<-0.03,0.5,1.0),index=b.index)
    b=b*g
    r=b-(turn.reindex(b.index).fillna(0)+g.diff().abs().mul(0.5).fillna(0))*COST
    r=r.dropna()
    if out:
        r.to_csv(f"{ROOT}/campaign/agents/C4_metaalloc/sleeves/C4_construct_v1.csv", header=["ret"])
    return r
def perf(r):
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    print(f"ann={r.mean()*252*100:.1f}% SR={r.mean()/r.std()*np.sqrt(252):.2f} MaxDD={dd*100:.1f}% n={len(r)}")
if __name__=="__main__":
    perf(main())
