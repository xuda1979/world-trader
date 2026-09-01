"""C2 round-2 scan: charter items 1,2,3,5,6 (+bonus 10s20s30s fly). Item 4 intl = monthly-only (skip)."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd, importlib.util
spec=importlib.util.spec_from_file_location("gates","/Users/daxu/software/world-trader/campaign/agents/B2_highfreq/gates.py")
G=importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'

def yld(name):
    s=pd.read_csv(f"{FRED}/{name}.csv",index_col=0,parse_dates=True)
    s=pd.to_numeric(s.iloc[:,0],errors='coerce').replace([-99.99,-99.9],np.nan).dropna()
    return s[~s.index.duplicated(keep='last')].sort_index()

DUR={'DGS1MO':0.08,'DGS3MO':0.25,'DGS6MO':0.5,'DGS2':1.9,'DGS5':4.4,'DGS10':8.5,'DGS20':15.0,'DGS30':17.5}

def build(tenors,start):
    ys=pd.DataFrame({t:yld(t) for t in tenors})
    print("starts:",{t:str(ys[t].dropna().index[0].date())+" n="+str(len(ys[t].dropna())) for t in tenors})
    ys=ys.dropna(); rs=pd.DataFrame({t:(-DUR[t]*yld(t).diff()+yld(t)/252/100) for t in tenors})
    df=pd.concat([ys,rs],axis=1).dropna(); df=df[df.index>=start]
    df.columns=[f"y{t}" for t in tenors]+[f"r{t}" for t in tenors]
    return df

def fly3(df,a,b,c):
    Da,Db,Dc=DUR[a],DUR[b],DUR[c]
    nb=(Dc-Db)/(Dc-Da); nc=(Db-Da)/(Dc-Da)
    fly=2*df[f'y{b}']-df[f'y{a}']-df[f'y{c}']
    fret=df[f'r{b}']-nb*df[f'r{a}']-nc*df[f'r{c}']
    return fly,fret,(nb,nc)

def sprd2(df,a,b):
    Da,Db=DUR[a],DUR[b]
    sp=df[f'y{b}']-df[f'y{a}']
    flat=Db/(Da+Db)*df[f'r{a}']-Da/(Da+Db)*df[f'r{b}']
    return sp,flat

def zs(z,w): return (z-z.rolling(w).mean())/z.rolling(w).std()

def vtscale(net):
    rcum=net.expanding(60).std()*np.sqrt(252)
    return (0.10/rcum).clip(upper=3.0).shift(1)

def pnl_sig(sig,fret):
    gross=sig*fret; to=sig.diff().abs().fillna(0.0)
    net=gross-to*6e-4
    return (net*vtscale(net)).dropna()

def sig_z(z,thr=1.0,clipv=2.0,sign=1):
    s=z.where(z.abs()>thr,0.0)*sign
    return s.clip(-clipv,clipv).shift(1).fillna(0)

def sig_band(z,entry,exitv):
    zv=z.values; pos=np.zeros(len(zv)); cur=0.0
    for i,v in enumerate(zv):
        if np.isnan(v): pos[i]=cur; continue
        a=abs(v)
        if cur==0 and a>entry: cur=np.sign(v)*min(a,2.0)
        elif cur!=0 and a<exitv: cur=0.0
        pos[i]=cur
    return pd.Series(pos,index=z.index).shift(1).fillna(0)

def row(name,r,to=None):
    s=G.full_stats(r); h1,h2=G.halves_sr(r)
    print(f"{name:36s} n={len(r):5d} ann={s['ann']:6.1f} SR={s['sr']:5.2f} mdd={s['mdd']:6.1f} H1={h1:5.2f} H2={h2:5.2f} negy={s['negy']:2d} worst={s['worst']:6.1f}"+(f" to={to:.3f}" if to is not None else ""))

def turnover(sig): return sig.diff().abs().fillna(0).mean()

# ============ curve flies (2006+) ============
df=build(['DGS2','DGS5','DGS10','DGS30'],'2006-01-01')
flyA,fretA,wA=fly3(df,'DGS2','DGS5','DGS10'); print("flyA DN wing weights (n2,n10):",np.round(wA,3))
flyB,fretB,wB=fly3(df,'DGS5','DGS10','DGS30'); print("flyB DN wing weights (n5,n30):",np.round(wB,3))
print("\n--- charter1: flyA / flyB solo (w=75 thr=1.0) + w-plateau grid ---")
for w in [50,63,75,100,126]:
    for nm,fly,fret in [('A',flyA,fretA),('B',flyB,fretB)]:
        sig=sig_z(zs(fly,w),1.0); row(f"fly{nm} w{w} thr1.0",pnl_sig(sig,fret),turnover(sig))
print("\n--- charter2: 2-leg steepeners z-reversion / momentum ---")
for (a,b) in [('DGS2','DGS10'),('DGS5','DGS30')]:
    sp,flat=sprd2(df,a,b)
    for w in [50,75,126]:
        z=zs(sp,w)
        for sign,lbl in [(1,'rev'),(-1,'mom')]:
            sig=sig_z(z,1.0,sign=sign); row(f"{a[-1]}s{b[-1]}s w{w} {lbl}",pnl_sig(sig,flat),turnover(sig))
print("\n--- bonus: 10s20s30s fly ---")
dfc=build(['DGS10','DGS20','DGS30'],'2006-01-01')
flyC,fretC,wC=fly3(dfc,'DGS10','DGS20','DGS30'); print("flyC DN weights:",np.round(wC,3))
for w in [50,75,100,126]:
    sig=sig_z(zs(flyC,w),1.0); row(f"flyC(10s20s30s) w{w} thr1.0",pnl_sig(sig,fretC),turnover(sig))

# ============ bill-area fly (2001+) ============
print("\n--- charter5: bill-area flies/spreads (2001+, honest short window) ---")
dfb=build(['DGS1MO','DGS3MO','DGS6MO'],'2001-01-01')
flybl,fretbl,_=fly3(dfb,'DGS1MO','DGS3MO','DGS6MO')
for w in [21,42,63,126]:
    for thr in [0.75,1.0,1.25]:
        sig=sig_z(zs(flybl,w),thr); row(f"billfly 1s3s6s w{w} thr{thr}",pnl_sig(sig,fretbl),turnover(sig))
sp13,flat13=sprd2(dfb,'DGS1MO','DGS3MO'); sp36,flat36=sprd2(dfb,'DGS3MO','DGS6MO')
for w in [42,63,126]:
    for thr in [0.75,1.0,1.25]:
        sig=sig_z(zs(sp13,w),thr); row(f"billsp 1-3 w{w} thr{thr} rev",pnl_sig(sig,flat13),turnover(sig))
for w in [63,126]:
    sig=sig_z(zs(sp36,w),1.0); row(f"billsp 3-6 w{w} thr1.0 rev",pnl_sig(sig,flat36),turnover(sig))

# ============ breakeven / TIPS legs (2004+) ============
print("\n--- charter3: breakeven level + BE-slope fly (2004+) ---")
b10,b5=yld('T10YIE'),yld('T5YIE'); dbe=pd.concat([b10.rename('b10'),b5.rename('b5')],axis=1).dropna()
dbe=dbe[dbe.index>='2004-01-01']
sl=dbe['b10']-dbe['b5']
# DN BE-fly: long 10y BE (long TIPS/short nom, D=8.5), short 1.93x 5y BE -> PnL = 8.5*d(slope)/100 + carry
w5=8.5/4.4
fret_sl=8.5/100*sl.diff()+(w5*dbe['b5']-dbe['b10'])/252/100
fret10=8.5/100*dbe['b10'].diff()-dbe['b10']/252/100
fret5=4.4/100*dbe['b5'].diff()-dbe['b5']/252/100
for w in [21,42,63,126]:
    z=zs(sl,w)
    for sign,lbl in [(1,'rev'),(-1,'mom')]:
        sig=sig_z(z,1.0,sign=sign); row(f"BEslope(10-5) w{w} {lbl}",pnl_sig(sig,fret_sl),turnover(sig))
for w in [42,63,126]:
    for sign,lbl in [(1,'rev'),(-1,'mom')]:
        sig=sig_z(zs(dbe['b10'],w),1.0,sign=sign); row(f"BE10 solo w{w} {lbl}",pnl_sig(sig,fret10),turnover(sig))
        sig=sig_z(zs(dbe['b5'],w),1.0,sign=sign); row(f"BE5 solo w{w} {lbl}",pnl_sig(sig,fret5),turnover(sig))

# ============ charter6: asymmetric band entries on proven flies ============
print("\n--- charter6: flyA/flyB asymmetric band (w75) ---")
zA,zB=zs(flyA,75),zs(flyB,75)
for (e,x) in [(2.0,0.5),(1.5,0.25),(2.0,0.25),(1.25,0.25)]:
    sig=sig_band(zA,e,x); row(f"flyA band e{e} x{x}",pnl_sig(sig,fretA),turnover(sig))
    sig=sig_band(zB,e,x); row(f"flyB band e{e} x{x}",pnl_sig(sig,fretB),turnover(sig))
