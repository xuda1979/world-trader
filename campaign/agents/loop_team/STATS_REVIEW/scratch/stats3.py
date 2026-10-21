#!/usr/bin/env python3
"""STATS_REVIEW part 3: tail re-model, GF impact, fine sweep, Aug-2026 checks."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from scipy import stats as st
import honest11_build as hb
ROOT="/Users/daxu/software/world-trader"
def load(fn):
    df=pd.read_csv(f"{ROOT}/campaign/results/{fn}",index_col=0,parse_dates=True); return df.iloc[:,0].astype(float)
rb=load("GOAL100_HONEST11FIX_BALANCED_daily.csv"); full=rb.copy()
rb=rb[rb.index>='2008-03-31']
x=rb.values; mu=x.mean(); sd=x.std(ddof=1); z=(x-mu)/sd
T=len(x)
print("days |z|>12:", [(str(rb.index[i].date()), round(float(x[i])*100,2), round(float(z[i]),1)) for i in np.where(np.abs(z)>12)[0]])

# --- tail models for P(day <= -14.4%) ---
zday=0.1439883; zsig=zday/sd
# 1) Student-t MLE on standardized returns (full fit)
dfr, locr, sc_r = st.t.fit(z)
p_t=st.t.cdf(-(zsig), dfr, loc=locr, scale=sc_r)
print(f"\nt-fit on standardized: df={dfr:.3f} loc={locr:.4f} scale={sc_r:.4f}; P(day<=-14.4%)={p_t:.3e} (1 per {1/p_t/252:,.0f} yrs)")
# 2) GPD peaks-over-threshold on LOSSES, u=2%
losses=-x
u=0.02; exc=losses[losses>u]-u; nu=len(exc)
xi,loc2,sc2=st.genextreme.fit(exc); xi_g,_,sc_g=st.genpareto.fit(exc, floc=0)
p_gpd=(nu/T)*st.genpareto.sf(zday-u, xi_g, loc=0, scale=sc_g)
print(f"GPD(u=2%): n_exc={nu} xi={xi_g:.3f} scale={sc_g:.4f}; P(loss>=14.4%)={p_gpd:.3e} (1 per {1/p_gpd/252:,.0f} yrs)")
# 3) empirical/Poisson bound
print(f"empirical: 0 losses>3.68% in {T} days; 1 gain>14% -> P(any 24-sigma day) Poisson95% upper = {3/T:.2e}/day (1 per {T/3/252:.1f} yrs at 95% conf)")
# 4) GEV redo properly on 21d MAX GAIN+LOSS blocks (absolute) with method MLE, report shape
blk=21; absm=np.array([np.abs(x[i*blk:(i+1)*blk]).max() for i in range(T//blk)])
c3,l3,s3=st.genextreme.fit(absm)
print(f"GEV 21d |r| maxima (nb={T//blk}): shape={c3:.3f} upper_endpt={l3+s3/max(-c3,1e-9) if c3<0 else 'inf'} P(blockmax<14.4%)={st.genextreme.cdf(zday,c3,l3,s3):.4f}")

# --- breach statement ---
print(f"\nbreach: a single -14.4% day => DD at least 14.4% from any level (equity always <= peak); breaches the 7% wall from EVERY state. From -5.60% DD -> {((0.944)*(1-zday)-1)*100:.2f}%")

# --- Good-Friday kept rows: impact ---
gf=['2008-03-21','2009-04-10','2010-04-02','2011-04-22','2012-04-06','2013-03-29','2014-04-18','2015-04-03','2016-03-25','2017-04-14','2018-03-30','2019-04-19','2021-04-02','2022-04-15','2023-04-07','2024-03-29','2025-04-18','2026-04-03']
gf=[d for d in gf if pd.Timestamp(d) in rb.index]
gfr=rb[rb.index.isin(gf)]
print(f"\nGood-Friday rows kept in FIX 2008+: n={len(gfr)} mean {gfr.mean()*1e4:.2f}bp sum {(1+gfr).prod()-1:.4%}")
rb_noGF=rb.drop(index=[d for d in gfr.index])
for nm,rr in [("with GF",rb),("drop GF",rb_noGF)]:
    eq=(1+rr).cumprod(); print(f"  {nm}: ann {( (1+rr).prod()**(252/len(rr))-1)*100:.2f}% SR_d {rr.mean()/rr.std(ddof=1)*np.sqrt(252):.3f} MDD {(eq/eq.cummax()-1).min()*100:.2f}%")

# --- warmup added rows sanity (373 rows 2006-10..2008-03) ---
warm=full[full.index<pd.Timestamp('2008-03-31')]
print(f"\nwarmup rows n={len(warm)} mean {warm.mean()*1e4:.3f}bp sd {warm.std()*1e4:.1f}bp zeros {100*(warm==0).mean():.1f}%")
aug=full[full.index>'2026-07-31']
print(f"Aug-2026 rows n={len(aug)} mean {aug.mean()*1e4:.2f}bp distinct {aug.nunique()} flat-run max {max((aug!=aug.shift()).cumsum().value_counts().iloc[1:][lambda s: s.index==False].tolist() or [0]) if False else int((aug.diff()!=0).cumsum().value_counts().max())}")

# --- fine sweep for max ann under mean all-in gross <= 1.6 ---
def lev_path(TGT,THR):
    POOL=hb.POOL; Ns=len(POOL)
    S={}
    for n in POOL:
        _,s=hb.vt(hb.sn(POOL[n]),0.08); S[n]=s
    Sd=pd.DataFrame(S)
    Vn=pd.DataFrame({n: hb.vt(hb.sn(POOL[n]),0.08)[0] for n in POOL})
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    vg,sg=hb.vt(blend,TGT)
    eq=(1+vg.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=blend.index)
    gall=sg*sc
    strict=Sd.abs().sum(axis=1)/Ns*gall
    idx=strict.index[strict.index>='2008-03-31']
    return strict.reindex(idx)
print("\nfine sweep for gross<=1.6 (mean, /11 convention, 2008+):")
for TGT in [0.036,0.037,0.0375,0.038,0.039]:
    r=hb.build(TGT,0.04,0.08,REBAL=True,KEEP=True); r=r[r.index>='2008-03-31']
    lv=lev_path(TGT,0.04)
    eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda z:(1+z).prod()-1)
    ann=(1+r).prod()**(252/len(r))-1
    print(f"TGT {TGT}: ann {ann*100:.2f}% SR_d {r.mean()/r.std(ddof=1)*np.sqrt(252):.2f} MDD {mdd*100:.2f}% grossMean {lv.mean():.3f} max {lv.max():.2f} neg {int((yr<0).sum())}")
