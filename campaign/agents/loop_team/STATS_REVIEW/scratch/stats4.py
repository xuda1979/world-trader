#!/usr/bin/env python3
"""STATS_REVIEW part 4: GF debug, FIX@0.11/0.14, SAFE/AGGR gates, loss tail."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from scipy import stats as st
from statsmodels.stats.diagnostic import acorr_ljungbox
import honest11_build as hb
ROOT="/Users/daxu/software/world-trader"
def load(fn):
    df=pd.read_csv(f"{ROOT}/campaign/results/{fn}",index_col=0,parse_dates=True); return df.iloc[:,0].astype(float)
rb=load("GOAL100_HONEST11FIX_BALANCED_daily.csv"); r08=rb[rb.index>='2008-03-31']

# --- GF debug ---
GF=['2008-03-21','2009-04-10','2010-04-02','2011-04-22','2012-04-06','2013-03-29','2014-04-18',
    '2015-04-03','2016-03-25','2017-04-14','2018-03-30','2019-04-19','2020-04-10','2021-04-02',
    '2022-04-15','2023-04-07','2024-03-29','2025-04-18','2026-04-03']
ts=[pd.Timestamp(d) for d in GF]
present=[t for t in ts if t in rb.index]
print("GF debug: index dtype",rb.index.dtype,"sample idx repr",repr(rb.index[-1]))
print("GF dates present in FIX BAL:",len(present),[str(t.date()) for t in present])
gfr=r08[r08.index.isin(present)]
print(f"GF rows 2008+: n={len(gfr)} mean {gfr.mean()*1e4:.2f}bp min {gfr.min()*1e4:.1f} max {gfr.max()*1e4:.1f}")
# impact of dropping GF rows on stats
present08=[t for t in present if t in r08.index]
for nm,rr in [("as-committed",r08),("GF dropped",r08.drop(index=present08))]:
    eq=(1+rr).cumprod()
    print(f"  {nm}: n={len(rr)} ann {(1+rr).prod()**(252/len(rr))-1:.4%} SR_d {rr.mean()/rr.std(ddof=1)*np.sqrt(252):.3f} MDD {(eq/eq.cummax()-1).min():.2%}")

# --- FIX at TGT 0.11/0.04 & 0.14/0.03 (ann>=80 attempt on honest FIX machinery) ---
def gross_mean(TGT,THR):
    POOL=hb.POOL; Ns=len(POOL); S={}
    for n in POOL:
        _,s=hb.vt(hb.sn(POOL[n]),0.08); S[n]=s
    Sd=pd.DataFrame(S)
    Vn=pd.DataFrame({n: hb.vt(hb.sn(POOL[n]),0.08)[0] for n in POOL})
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    vg,sg=hb.vt(blend,TGT)
    eq=(1+vg.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=blend.index)
    g=Sd.abs().sum(axis=1)/Ns*sg*sc
    return g[g.index>='2008-03-31']
A=hb.build(0.11,0.04,0.08,REBAL=True,KEEP=True); B=hb.build(0.14,0.03,0.08,REBAL=True,KEEP=True)
BALX=((A+B)/2).dropna(); BALX=BALX[BALX.index>='2008-03-31']
gA=gross_mean(0.11,0.04); gB=gross_mean(0.14,0.03); gX=(gA+gB)/2
eq=(1+BALX).cumprod(); yr=BALX.groupby(BALX.index.year).apply(lambda z:(1+z).prod()-1)
print(f"\nFIX@TGT0.11/0.14 BAL 2008+: ann {(1+BALX).prod()**(252/BALX.size)-1:.2%} SR_d {BALX.mean()/BALX.std(ddof=1)*np.sqrt(252):.2f} "
      f"MDD {(eq/eq.cummax()-1).min():.2%} negYrs {int((yr<0).sum())}/{yr.size} worstYr {yr.min():.2%} | all-in gross mean {gX.mean():.2f} p95 {gX.quantile(0.95):.2f} max {gX.max():.2f}")

# --- SAFE/AGGR gates ---
for tag,fn in [("SAFE","GOAL100_HONEST11FIX_SAFE_daily.csv"),("AGGR","GOAL100_HONEST11FIX_AGGRESSIVE_daily.csv")]:
    r=load(fn); r=r[r.index>='2008-03-31']
    ac1=r.autocorr(1)
    lb=acorr_ljungbox(r.values,lags=[10],return_df=True)
    print(f"{tag}: n={len(r)} uniqR {r.nunique()/len(r):.4f} ac1 {ac1:.4f} LB10 p {float(lb.lb_pvalue.iloc[0]):.2e} maxday {r.max()*100:.2f}% minday {r.min()*100:.2f}%")

# --- loss tail counts (BAL 2008+) ---
x=r08.values
for th in [0.01,0.015,0.02,0.025,0.03,0.0368]:
    nl=int((x<=-th).sum()); ng=int((x>=th).sum())
    print(f"days |r|>={th*100:.2f}%: losses {nl}, gains {ng}")
print(f"max loss {x.min()*100:.2f}% ({r08.idxmin().date()}), max gain {x.max()*100:.2f}% ({r08.idxmax().date()})")
# Aug-2026 tail
aug=rb[rb.index>'2026-07-31']
print("Aug-2026: max",f"{aug.max()*100:.2f}%","min",f"{aug.min()*100:.2f}%")
