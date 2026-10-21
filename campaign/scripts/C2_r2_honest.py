"""C2 round-2 HONEST units: fret in DECIMAL = (-D*dy_pctpts + y/252/100)/100. Real 6bps costs.
Re-verifies round-1 C2_fly2AB_75 and evaluates flyC(10s20s30s) + billfly(1s3s6s) candidates."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd, glob, os, importlib.util
spec=importlib.util.spec_from_file_location("gates","/Users/daxu/software/world-trader/campaign/agents/B2_highfreq/gates.py")
G=importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
DUR={'DGS1MO':0.08,'DGS3MO':0.25,'DGS6MO':0.5,'DGS2':1.9,'DGS5':4.4,'DGS10':8.5,'DGS20':15.0,'DGS30':17.5}
def yld(name):
    s=pd.read_csv(f"{FRED}/{name}.csv",index_col=0,parse_dates=True)
    s=pd.to_numeric(s.iloc[:,0],errors='coerce').replace([-99.99,-99.9],np.nan).dropna()
    return s[~s.index.duplicated(keep='last')].sort_index()
def build(tenors,start):
    ys=pd.DataFrame({t:yld(t) for t in tenors}).dropna()
    rs=pd.DataFrame({t:(-DUR[t]*yld(t).diff()+yld(t)/252/100)/100.0 for t in tenors})  # DECIMAL
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
    net=gross-to*6e-4                                  # HONEST 6bps one-side
    scale=(0.10/(net.expanding(60).std()*np.sqrt(252))).clip(upper=3.0).shift(1)  # correct parens
    return (net*scale).dropna(), sig
def report(name,r):
    s=G.full_stats(r); h1,h2=G.halves_sr(r)
    mid=r.index[len(r)//2]
    isd,osd=r[r.index<=mid],r[r.index>mid]
    print(f"{name:24s} n={len(r)} ann={s['ann']:5.1f} vol={s['vol']:4.1f} SR={s['sr']:5.2f} mdd={s['mdd']:6.1f} H1={h1:5.2f} H2={h2:5.2f} negy={s['negy']:2d} worst={s['worst']:6.1f} | IS {isd.mean()/isd.std()*np.sqrt(252):5.2f} OOS {osd.mean()/osd.std()*np.sqrt(252):5.2f} (OOS mdd {((1+osd).cumprod()/(1+osd).cumprod().cummax()-1).min()*100:5.1f}%) yearly={s['yearly']}")
    return s
blend=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv',index_col=0,parse_dates=True)['ret']
def cblend(r):
    i=r.index.intersection(blend.index); return np.corrcoef(r[i],blend[i])[0,1]

print("=== re-verify ROUND-1 sleeve params with HONEST units ===")
dfAB=build(['DGS2','DGS5','DGS10','DGS30'],'2006-01-01')
flyA,fretA=fly3(dfAB,'DGS2','DGS5','DGS10'); flyB,fretB=fly3(dfAB,'DGS5','DGS10','DGS30')
def pnl_round1(flyv,fret,w=75,thr=1.0):
    z=(flyv-flyv.rolling(w).mean())/flyv.rolling(w).std()
    sig=z.where(z.abs()>thr,0).clip(-2,2).shift(1).fillna(0)
    gross=sig*fret; to=sig.diff().abs().fillna(0)
    net=gross-to*6e-4
    scale=(0.10/(net.expanding(60).std()*np.sqrt(252))).clip(upper=3.0).shift(1)
    return (net*scale).dropna()
ensAB=pd.concat([pnl_round1(flyA,fretA).rename('A'),pnl_round1(flyB,fretB).rename('B')],axis=1).mean(axis=1).dropna()
report("round1 2AB w75 HONEST",ensAB)
old=pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/C2_ratescurve/sleeves/C2_fly2AB_75.csv',index_col=0,parse_dates=True)['ret']
i=ensAB.index.intersection(old.index)
print(f"corr honest-rerun vs saved-file: {np.corrcoef(ensAB[i],old[i])[0,1]:.3f} (same signals, different cost accounting)")
sr_old=old.mean()/old.std()*np.sqrt(252); print(f"saved file SR (as-is, buggy-cost): {sr_old:.2f} | honest SR: {ensAB.mean()/ensAB.std()*np.sqrt(252):.2f}")

print("\n=== flyC (10s20s30s) honest ===")
dfC=build(['DGS10','DGS20','DGS30'],'2006-01-01'); flyC,fretC=fly3(dfC,'DGS10','DGS20','DGS30')
bestC=None
for w in [35,42,50,63,75,100]:
    for thr in [0.75,1.0,1.25]:
        r,_=pipeline(zs(flyC,w),fretC,thr)
        sr=r.mean()/r.std()*np.sqrt(252)
        print(f"  flyC w{w} thr{thr}: SR {sr:.2f}", end="")
        if (w,thr)==(50,1.0) or (w,thr)==(42,1.0): pass
    print()
for (w,thr) in [(42,1.0),(50,1.0)]:
    r,sig=pipeline(zs(flyC,w),fretC,thr)
    report(f"flyC w{w} thr{thr}",r); print(f"    corr_blend={cblend(r):.3f} turnover={sig.diff().abs().mean():.3f}")

print("\n=== billfly (1s3s6s, 2001+) honest ===")
dfB=build(['DGS1MO','DGS3MO','DGS6MO'],'2001-01-01'); flybl,fretbl=fly3(dfB,'DGS1MO','DGS3MO','DGS6MO')
for w in [42,63,126]:
    for thr in [0.75,1.0,1.25]:
        r,_=pipeline(zs(flybl,w),fretbl,thr)
        print(f"  billfly w{w} thr{thr}: SR {r.mean()/r.std()*np.sqrt(252):.2f}",end="")
    print()
for (w,thr) in [(63,0.75),(63,1.0),(42,0.75)]:
    r,sig=pipeline(zs(flybl,w),fretbl,thr)
    report(f"billfly w{w} thr{thr}",r); print(f"    corr_blend={cblend(r):.3f} turnover={sig.diff().abs().mean():.3f}")
