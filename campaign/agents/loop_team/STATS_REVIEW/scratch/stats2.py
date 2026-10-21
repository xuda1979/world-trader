#!/usr/bin/env python3
"""STATS_REVIEW part 2: DSR (correct units), GEV tail, leverage/TGT sweep, added-row forensics."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from scipy import stats as st
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox
import honest11_build as hb

ROOT="/Users/daxu/software/world-trader"
rng=np.random.default_rng(7)
def load(fn):
    df=pd.read_csv(f"{ROOT}/campaign/results/{fn}",index_col=0,parse_dates=True); return df.iloc[:,0].astype(float)
rb=load("GOAL100_HONEST11FIX_BALANCED_daily.csv"); rb=rb[rb.index>='2008-03-31']
x=rb.values; T=len(x); mu=x.mean(); sd=x.std(ddof=1)
SR_d=mu/sd; skew=st.skew(x); kurt=st.kurtosis(x,fisher=False)
SR_ann=SR_d*np.sqrt(252)
print(f"T={T} SR_d(unit)={SR_d:.5f} SR_ann={SR_ann:.4f} skew={skew:.4f} raw_kurt={kurt:.2f}")

# ---------- DSR, Bailey/Lopez de Prado, correct per-period (daily) units ----------
g=0.5772156649015329; N=500
z1=st.norm.ppf(1-1.0/N); z2=st.norm.ppf(1-1.0/(N*np.e))
c=(1-g)*z1+g*z2
def psr(sr_hat_d, sr_star_d, T_, skew_, kurt_):
    den=np.sqrt(1-skew_*sr_hat_d+(kurt_-1)/4*sr_hat_d**2)
    return float(st.norm.cdf((sr_hat_d-sr_star_d)*np.sqrt(T_-1)/den)), den
# dispersion anchors (annualized SR units)
srsleeve=np.array([4.27,3.84,4.11,3.96,1.87,3.26,1.17,1.32,1.09,0.78,1.04])
anchors={"N=500 sd=0.25":0.25,"N=500 sd=0.50":0.50,"N=500 sd=1.00":1.00,
         "N=500 sd=pool11(1.442)":float(srsleeve.std(ddof=1)),
         "N=500 sd=7 distinct engines":float(np.array([4.27,1.87,3.26,1.17,1.32,1.09,0.78,1.04]).std(ddof=1))}
print("\n--- DSR(N=500) daily units ---")
for lab,sd_ann in anchors.items():
    sr_star_d=(sd_ann/np.sqrt(252))*c
    p,den=psr(SR_d,sr_star_d,T,skew,kurt)
    print(f"{lab}: SR*_ann={sr_star_d*np.sqrt(252):.3f} haircut={sr_star_d*np.sqrt(252):.3f} DSR={p:.4f} z={(SR_d-sr_star_d)*np.sqrt(T-1)/den:.2f}")
# threshold dispersion for DSR=0.95
from scipy.optimize import brentq
f=lambda s: psr(SR_d,(s/np.sqrt(252))*c,T,skew,kurt)[0]-0.95
s_th=brentq(f,0.5,3.0)
print(f"cross-trial SR sd threshold for DSR>=0.95: {s_th:.3f} (ann units)")
# monthly-unit PSR/DSR
m=(1+rb).resample('ME').prod()-1; xm=m.values; SR_m_d=xm.mean()/xm.std(ddof=1); Tm=len(xm)
sk_m=st.skew(xm); ku_m=st.kurtosis(xm,fisher=False)
print(f"monthly: SR_m={SR_m_d*np.sqrt(12):.3f} T={Tm} skew_m={sk_m:.2f} kurt_m={ku_m:.1f}")
for lab,sd_ann in anchors.items():
    sr_star_m=(sd_ann/np.sqrt(12))*c if False else (sd_ann*1.0)*c/np.sqrt(12)
    p,den=psr(SR_m_d,sr_star_m,Tm,sk_m,ku_m)
    print(f"  monthly {lab}: SR*={sr_star_m*np.sqrt(12):.3f} DSR={p:.4f}")

# ---------- Ljung-Box lag profile ----------
ac=[rb.autocorr(l) for l in range(1,11)]
print("\nautocorr lags1-10:",np.round(ac,4))
lb=acorr_ljungbox(x,lags=[10],return_df=True)
print("LB(10):",float(lb.lb_stat.iloc[0]),"p",float(lb.lb_pvalue.iloc[0]))
lbsq=acorr_ljungbox((x-mu)**2,lags=[10],return_df=True)
print("LB(10) squared:",float(lbsq.lb_stat.iloc[0]),"p",float(lbsq.lb_pvalue.iloc[0]))
# exclude the single 24-sigma day
x2=np.concatenate([x[x<0.10],x[x>=0.10]*0.0])  # zero out the big day
lb2=acorr_ljungbox(x2,lags=[10],return_df=True)
print("LB(10) with +14.4% day zeroed:",float(lb2.lb_stat.iloc[0]),"p",float(lb2.lb_pvalue.iloc[0]))

# ---------- GEV block maxima: P(loss <= -14.4%) recurrence ----------
losses=-x  # positive = loss
blk=21; nb=T//blk
bmax=np.array([losses[i*blk:(i+1)*blk].max() for i in range(nb)])
c_,loc_,sc_=st.genextreme.fit(bmax)
# P(single day loss>0.144) via GEV of 21d maxima: P(blockmax<=v)^... per-day approx
v=0.144
p_block_le=st.genextreme.cdf(v,c_,loc_,sc_)
p_day_ge=1-p_block_le**(1/blk)   # daily prob that day sets a block max > v (approx: any-day prob)
print(f"\nGEV fit 21d loss-maxima (nb={nb}): shape={c_:.3f} loc={loc_:.4f} scale={sc_:.4f}")
print(f"P(21d block max loss <= 14.4%)={p_block_le:.4f} -> implied P(a day loses >=14.4%)≈{p_day_ge:.2e} (≈1 per {1/p_day_ge/252:.0f} yrs)")
rl=st.genextreme.ppf(1-1/4616*1,c_,loc_,sc_)  # return level over ~4616d of days? use quantile of blocks for T blocks
# also empirical: 2 of 4616 days |z|>12
print("empirical: max loss",float(losses.max()),"max gain",float(x.max()),"|z|>12 count",int((np.abs((x-mu)/sd)>12).sum()))
print("t-fit df(whole series):",st.t.fit((x-mu)/sd)[0])
ax=np.sort(np.abs((x-mu)/sd))[::-1]; k=int(0.01*T); H=np.mean(np.log(ax[:k]/ax[k]))
print(f"Hill(1%) tail index={1/H:.2f}")
# scenario: breach of 7% wall from best case (equity at peak)
print("breach math: equity<=running peak ALWAYS -> a -14.4% day lands DD<=-14.4% i.e. breach of 7% wall CERTAIN; from -5.60% current DD -> -19.2%")

# ---------- LEVERAGE: capture scales on FIX machinery ----------
POOL=hb.POOL; Ns=len(POOL)
SnP=pd.DataFrame({n: hb.vt(hb.sn(p),0.08)[1] for n,p in POOL.items()}).dropna(how='all')
capWP=SnP/Ns
def lev_path(TGT,THR):
    V={};S={}
    for n in POOL:
        r=hb.sn(POOL[n]); v,s=hb.vt(r,0.08); S[n]=s
    Sd=pd.DataFrame(S)
    Vn=pd.DataFrame({n: hb.vt(hb.sn(POOL[n]),0.08)[0] for n in POOL})
    blend=Vn.mean(axis=1); blend=blend[blend.index>='2006-10-01']
    vg,sg=hb.vt(blend,TGT)
    eq=(1+vg.fillna(0)).cumprod(); rm=eq.rolling(126).max().shift(1); tdd=eq.shift(1)/rm-1
    sc=pd.Series(np.where(tdd<-THR,0.5,1.0),index=blend.index)
    gall=sg*sc   # effective global scalar
    strict=Sd.abs().sum(axis=1)/Ns*gall           # /11 convention
    present=Sd.notna().sum(axis=1)
    loose=Sd.abs().sum(axis=1)/present*gall       # per-present-sleeve convention
    idx=strict.index[strict.index>='2008-03-31']
    return pd.DataFrame({'strict':strict,'loose':loose}).reindex(idx), Sd
def yr_means(s):
    y=s.groupby(s.index.year).mean(); return {int(k):round(float(v),3) for k,v in y.items()}
print("\n--- ALL-IN (capital-real) GROSS on FIX construction, 2008+ ---")
for tag,TGT,THR in [("SAFE",0.07,0.04),("BAL",None,None),("AGGR",0.091,0.03)]:
    if TGT is None:
        a,_=lev_path(0.07,0.04); b,_=lev_path(0.091,0.03)
        lv=(a['strict']+b['strict'])/2
        lvloose=(a['loose']+b['loose'])/2
    else:
        lv,_=lev_path(TGT,THR); lv=lv['strict']; lvo=None
    print(f"{tag}: mean {lv.mean():.3f} median {lv.median():.3f} p95 {lv.quantile(0.95):.3f} max {lv.max():.3f} | days>1.6: {100*(lv>1.6).mean():.1f}% | yrs>1.6: {sum(1 for v in yr_means(lv).values() if v>1.6)}/19")
    if tag=="BAL": print("   BAL yearly means:",yr_means(lv)); bal_loose_mean=float(lvloose.mean())

print("BAL /present-sleeve convention mean:",round(bal_loose_mean,3))
# ---------- TGT sweep at THR=0.04, per-sleeve 0.08, REBAL+KEEP semantics for returns ----------
def build_fix(TGT,THR):
    return hb.build(TGT,THR,0.08,REBAL=True,KEEP=True)
print("\n--- TGT sweep (THR=0.04): comparable-span 2008+ stats vs all-in mean gross (strict /11) ---")
print(f"{'TGT':>6} {'ann%':>7} {'SR_d':>6} {'MDD%':>7} {'grossMean':>9} {'p95':>6} {'max':>6} {'negYrs':>6}")
for TGT in [0.020,0.025,0.030,0.033,0.035,0.040,0.045,0.050,0.055,0.060,0.070]:
    r=build_fix(TGT,0.04); r=r[r.index>='2008-03-31']
    lv,_=lev_path(TGT,0.04); lv=lv['strict']
    eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda z:(1+z).prod()-1)
    ann=(1+r).prod()**(252/len(r))-1
    print(f"{TGT:>6} {ann*100:>7.2f} {r.mean()/r.std(ddof=1)*np.sqrt(252):>6.2f} {mdd*100:>7.2f} {lv.mean():>9.3f} {lv.quantile(0.95):>6.2f} {lv.max():>6.2f} {int((yr<0).sum()):>6d}")
# ---------- added-row forensics ----------
print("\n--- added-row forensics (rows in FIX not in L16) ---")
l16=load("GOAL100_HONEST11L16_BALANCED_daily.csv")
added=rb.index.difference(l16.index)
inwin=[d for d in added if pd.Timestamp('2008-03-31')<=d<=pd.Timestamp('2026-07-31')]
print(f"added in-window {len(inwin)}: mean ret {np.mean([rb[d] for d in inwin])*1e4:.2f}bp vs overall {mu*1e4:.2f}bp")
# which pool sleeves have raw rows on a Good Friday and 2024-03-29?
gfdays=[d for d in inwin if d.dayofweek==4 and d.month in (3,4) and d==d - pd.Timedelta(days=0)]
# identify Good Fridays properly: check against holiday list is useless (not federal); use known ones
gf_known=[d for d in inwin if str(d.date()) in ('2013-03-29','2014-04-18','2015-04-03','2016-03-25','2017-04-14','2018-03-30','2019-04-19','2021-04-02','2022-04-15','2023-04-07','2024-03-29','2025-04-18','2010-04-02','2011-04-22','2012-04-06','2009-04-10','2012-04-06','2026-04-03')]
gf_known=sorted(set(gf_known))
print("Good-Friday-like added days:",len(gf_known))
probe=gf_known[-1] if gf_known else None
if probe is not None:
    print("probe",probe.date())
    for n,p in POOL.items():
        s=hb.sn(p)
        print(f"  {n}: {'PRESENT' if probe in s.index else 'absent'}", (f"ret {s[probe]*1e4:.1f}bp" if probe in s.index else ""))
    print("  FIX return that day:",f"{rb[probe]*1e4:.2f}bp")
