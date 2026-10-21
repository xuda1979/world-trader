"""C2 round-2 salvage: honest decimal bond returns + REAL per-leg 6bps costs.
Fix: sample signal at weekly/biweekly/monthly freq to cut turnover 5-20x.
Engines: flyA(2s5s10s), flyB(5s10s30s), flyC(10s20s30s), billfly(1s3s6s, 2001+)."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd, importlib.util
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
    w=(1.0,nb,nc)  # leg notional weights (belly long 1, wings short nb+nc=1) -> gross 2
    fly=2*df[f'y{b}']-df[f'y{a}']-df[f'y{c}']
    fret=df[f'r{b}']-nb*df[f'r{a}']-nc*df[f'r{c}']
    return fly,fret,w
def zs(z,w): return (z-z.rolling(w).mean())/z.rolling(w).std()
def backtest_honest(z,fret,legs,freq='D',thr=1.0,clipv=2.0):
    """freq: 'D' daily, 5=weekly, 10=biweekly, 21=monthly rebalance (sample, ffill).
    Per-leg turnover: sum |d(sig*w_leg)| * 6bps one-side."""
    zraw=z.where(z.abs()>thr,0.0).clip(-clipv,clipv)
    if freq=='D': sig=zraw
    else:
        # sample on freq-end days, ffill within period (uses only data<=t)
        grp=zraw.index.to_period({5:'W',10:'W',21:'M'}[freq])
        sampled=zraw.groupby(grp).last()
        sig=sampled.reindex(grp).set_axis(zraw.index)
    sig=sig.shift(1).fillna(0)                       # T+1
    gross=sig*fret
    to=sum((sig*w).diff().abs().fillna(0.0) for w in legs)   # per-leg notional turnover
    net=gross-to*6e-4
    scale=(0.10/(net.expanding(60).std()*np.sqrt(252))).clip(upper=3.0).shift(1)
    return (net*scale).dropna(), to.mean()
def sr(r): return r.mean()/r.std()*np.sqrt(252)
def brief(name,r,to):
    s=G.full_stats(r); h1,h2=G.halves_sr(r)
    flag="<<<" if (s['sr']>=1.0 and h1>=0.5 and h2>=0.5 and s['negy']<=2 and s['worst']>-5) else ""
    print(f"{name:30s} ann={s['ann']:5.1f} vol={s['vol']:4.1f} SR={s['sr']:5.2f} mdd={s['mdd']:6.1f} H1={h1:5.2f} H2={h2:5.2f} negy={s['negy']:2d} worst={s['worst']:6.1f} to={to:.3f} {flag}")

cfgs=[('flyA',('DGS2','DGS5','DGS10'),'2006-01-01',75),('flyB',('DGS5','DGS10','DGS30'),'2006-01-01',75),
      ('flyC',('DGS10','DGS20','DGS30'),'2006-01-01',50),('billfly',('DGS1MO','DGS3MO','DGS6MO'),'2001-01-01',63)]
eng={}
for nm,tn,st,w in cfgs:
    df=build(list(tn),st); fly,fret,legs=fly3(df,*tn); eng[nm]=(zs(fly,w),fret,legs,df.index[0])

print("=== honest backtest: rebalance-frequency x engine ===")
for freq in ['D',5,10,21]:
    for nm in ['flyA','flyB','flyC','billfly']:
        z,fret,legs,_=eng[nm]
        r,to=backtest_honest(z,fret,legs,freq)
        brief(f"{nm} freq={freq}",r,to)
print("\n=== window plateau at weekly for flyA/flyB/flyC ===")
for nm,tn,st,_ in cfgs[:3]:
    df=build(list(tn),st); fly,fret,legs=fly3(df,*tn)
    for w in [42,63,75,100,126]:
        r,to=backtest_honest(zs(fly,w),fret,legs,5)
        brief(f"{nm} wk w{w}",r,to)
print("\n=== combos (EW of vol-targeted legs) at weekly ===")
import itertools
def get(nm,freq=5,w=None):
    z,fret,legs,_=eng[nm]
    return backtest_honest(z,fret,legs,freq)[0]
combos={'AB':('flyA','flyB'),'ABC':('flyA','flyB','flyC'),'ABb':('flyA','flyB','billfly'),
        'ABCb':('flyA','flyB','flyC','billfly'),'AC':('flyA','flyC'),'BC':('flyB','flyC')}
for cn,mem in combos.items():
    rs=pd.concat([get(m) for m in mem],axis=1).dropna()
    ens=rs.mean(axis=1)
    brief(f"combo {cn} weekly",ens,0)
blend=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv',index_col=0,parse_dates=True)['ret']
for cn in ['AB','ABC','ABb','ABCb']:
    rs=pd.concat([get(m) for m in combos[cn]],axis=1).dropna(); ens=rs.mean(axis=1)
    i=ens.index.intersection(blend.index)
    print(f"combo {cn}: corr_blend={np.corrcoef(ens[i],blend[i])[0,1]:.3f}")
