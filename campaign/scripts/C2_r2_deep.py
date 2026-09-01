"""C2 round-2 deep dive: full gates for flyC(10s20s30s), billfly(1s3s6s), flyA/flyB solo (merge check)."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd, glob, os
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
DUR={'DGS1MO':0.08,'DGS3MO':0.25,'DGS6MO':0.5,'DGS2':1.9,'DGS5':4.4,'DGS10':8.5,'DGS20':15.0,'DGS30':17.5}
def yld(name):
    s=pd.read_csv(f"{FRED}/{name}.csv",index_col=0,parse_dates=True)
    s=pd.to_numeric(s.iloc[:,0],errors='coerce').replace([-99.99,-99.9],np.nan).dropna()
    return s[~s.index.duplicated(keep='last')].sort_index()
def build(tenors,start):
    ys=pd.DataFrame({t:yld(t) for t in tenors}).dropna()
    rs=pd.DataFrame({t:(-DUR[t]*yld(t).diff()+yld(t)/252/100) for t in tenors})
    df=pd.concat([ys,rs],axis=1,sort=True).dropna(); df=df[df.index>=start]
    df.columns=[f"y{t}" for t in tenors]+[f"r{t}" for t in tenors]
    return df
def fly3(df,a,b,c):
    Da,Db,Dc=DUR[a],DUR[b],DUR[c]
    nb=(Dc-Db)/(Dc-Da); nc=(Db-Da)/(Dc-Da)
    return 2*df[f'y{b}']-df[f'y{a}']-df[f'y{c}'], df[f'r{b}']-nb*df[f'r{a}']-nc*df[f'r{c}']
def zs(z,w): return (z-z.rolling(w).mean())/z.rolling(w).std()
def pipeline(z,fret,thr=1.0,clipv=2.0):
    sig=z.where(z.abs()>thr,0.0).clip(-clipv,clipv).shift(1).fillna(0)
    gross=sig*fret; to=sig.diff().abs().fillna(0.0)
    net=gross-to*6e-4
    scale=(0.10/net.expanding(60).std()*np.sqrt(252)).clip(upper=3.0).shift(1)
    return (net*scale).dropna(), sig
def signal_perm_pval(z,fret,thr,n=200,seed=0):
    """proper scramble: permute z vs returns alignment, rebuild full pipeline."""
    zi=z.dropna(); fr=fret.reindex(zi.index).dropna(); zi=zi.reindex(fr.index)
    real,_=pipeline(zi,fr,thr); rs=real.mean()/real.std()*np.sqrt(252)
    rng=np.random.default_rng(seed); cnt=0
    for _ in range(n):
        zz=pd.Series(rng.permutation(zi.values),index=zi.index)
        sc,_=pipeline(zz,fr,thr); s=sc.mean()/sc.std()*np.sqrt(252)
        if s>=rs: cnt+=1
    return cnt/n, rs

dfC=build(['DGS10','DGS20','DGS30'],'2006-01-01')
flyC,fretC=fly3(dfC,'DGS10','DGS20','DGS30')
dfB=build(['DGS1MO','DGS3MO','DGS6MO'],'2001-01-01')
flybl,fretbl=fly3(dfB,'DGS1MO','DGS3MO','DGS6MO')
dfAB=build(['DGS2','DGS5','DGS10','DGS30'],'2006-01-01')
flyA,fretA=fly3(dfAB,'DGS2','DGS5','DGS10'); flyB,fretB=fly3(dfAB,'DGS5','DGS10','DGS30')

print("--- flyC plateau grid (w x thr) ---")
gridC={}
for w in [35,42,50,63,75,100]:
    for thr in [0.75,1.0,1.25]:
        r,_=pipeline(zs(flyC,w),fretC,thr)
        sr=r.mean()/r.std()*np.sqrt(252); gridC[(w,thr)]=sr
        print(f"flyC w{w} thr{thr}: SR {sr:.2f}")
print("\n--- billfly plateau grid ---")
gridbl={}
for w in [42,63,126]:
    for thr in [0.75,1.0,1.25]:
        r,_=pipeline(zs(flybl,w),fretbl,thr)
        sr=r.mean()/r.std()*np.sqrt(252); gridbl[(w,thr)]=sr
        print(f"billfly w{w} thr{thr}: SR {sr:.2f}")

import importlib.util
spec=importlib.util.spec_from_file_location("gates","/Users/daxu/software/world-trader/campaign/agents/B2_highfreq/gates.py")
G=importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
blend=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv',index_col=0,parse_dates=True)['ret']
# library sleeves
lib={}
for p in glob.glob('/Users/daxu/software/world-trader/campaign/results/sleeve_library/*.csv')+glob.glob('/Users/daxu/software/world-trader/campaign/agents/*/sleeves/*.csv'):
    nm=os.path.basename(p)[:-4]
    if nm.endswith('.meta'): continue
    try: lib[nm]=pd.read_csv(p,index_col=0,parse_dates=True)['ret']
    except Exception: pass
def report(name,r):
    s=G.full_stats(r); h1,h2=G.halves_sr(r)
    yr=s['yearly']
    i=r.index.intersection(blend.index); cb=np.corrcoef(r[i],blend[i])[0,1]
    corrs={}
    for nm,rr in lib.items():
        i2=r.index.intersection(rr.index)
        if len(i2)>800:
            c=np.corrcoef(r[i2],rr[i2])[0,1]
            if abs(c)>0.25: corrs[nm]=round(float(c),3)
    mid=r.index[0]+(r.index[-1]-r.index[0])*0.55
    isd=r[r.index<mid]; osd=r[r.index>=mid]
    print(f"\n=== {name} === n={len(r)} ann={s['ann']:.1f} vol={s['vol']:.1f} SR={s['sr']:.2f} mdd={s['mdd']:.1f}")
    print(f"  H1={h1:.2f} H2={h2:.2f} negy={s['negy']} worst={s['worst']:.1f} yearly={yr}")
    print(f"  corr_blend={cb:.3f}  corr_lib>0.25: {dict(sorted(corrs.items(),key=lambda x:-abs(x[1])))}")
    print(f"  IS({r.index[0].date()}..{mid.date()}) SR {isd.mean()/isd.std()*np.sqrt(252):.2f} ann {isd.mean()*252*100:.1f}% | OOS({mid.date()}..) SR {osd.mean()/osd.std()*np.sqrt(252):.2f} ann {osd.mean()*252*100:.1f}% mdd {( (1+osd).cumprod()/(1+osd).cumprod().cummax()-1).min()*100:.1f}%")
    return r
rC,_=pipeline(zs(flyC,50),fretC,1.0); report("flyC w50 thr1.0",rC)
rC2,_=pipeline(zs(flyC,42),fretC,1.0); report("flyC w42 thr1.0",rC2)
rbl,_=pipeline(zs(flybl,63),fretbl,1.0); report("billfly w63 thr1.0",rbl)
rbl2,_=pipeline(zs(flybl,63),fretbl,0.75); report("billfly w63 thr0.75",rbl2)
rA,_=pipeline(zs(flyA,63),fretA,1.0); report("flyA w63 solo",rA)
rB,_=pipeline(zs(flyB,63),fretB,1.0); report("flyB w63 solo",rB)
# sibling correlations
old=pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/C2_ratescurve/sleeves/C2_fly2AB_75.csv',index_col=0,parse_dates=True)['ret']
for nm,r in [('flyC w50',rC),('billfly w63 t1.0',rbl),('flyA63',rA),('flyB63',rB)]:
    i=r.index.intersection(old.index); print(f"sibling corr {nm} vs C2_fly2AB_75: {np.corrcoef(r[i],old[i])[0,1]:.3f}")
print(f"sibling corr flyA63 vs flyB63: {np.corrcoef(*[x.reindex(rA.index.intersection(rB.index)).dropna() for x in (rA,rB)])[0,1]:.3f}")
i3=rC.index.intersection(rbl.index)
print(f"corr flyC vs billfly: {np.corrcoef(rC.reindex(i3),rbl.reindex(i3))[0,1]:.3f}")
# ensemble with existing sleeve
ens=pd.concat([old,rC,rbl],axis=1,sort=True).dropna()
for nm,r in [('2AB+flyC',ens.iloc[:,:2].mean(axis=1)),('2AB+billfly',ens.iloc[:,[0,2]].mean(axis=1)),('2AB+flyC+billfly',ens.mean(axis=1))]:
    s=G.full_stats(r); h1,h2=G.halves_sr(r)
    i=r.index.intersection(blend.index)
    print(f"ENSEMBLE {nm}: SR {s['sr']:.2f} ann {s['ann']:.1f}% mdd {s['mdd']:.1f}% H1 {h1:.2f} H2 {h2:.2f} negy {s['negy']} worst {s['worst']:.1f} corr_blend {np.corrcoef(r[i],blend[i])[0,1]:.3f}")
print("\n--- scramble (signal-perm 200x) on candidates ---")
for nm,z,f,thr in [('flyC w50',zs(flyC,50),fretC,1.0),('billfly w63',zs(flybl,63),fretbl,1.0)]:
    p,rs=signal_perm_pval(z,f,thr); print(f"{nm}: real SR {rs:.2f}, scramble p={p:.3f}")
