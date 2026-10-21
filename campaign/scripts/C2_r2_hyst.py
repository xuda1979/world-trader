"""C2 round-2 salvage v2: precise accounting + hysteresis turnover reduction.
Honest: decimal bond rets, per-leg 6bps costs (also x vol-scale, reported both), correct weekly sampling (no lookahead)."""
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
    rs=pd.DataFrame({t:(-DUR[t]*yld(t).diff()+yld(t)/252/100)/100.0 for t in tenors})
    df=pd.concat([ys,rs],axis=1,sort=True).dropna(); df=df[df.index>=start]
    df.columns=[f"y{t}" for t in tenors]+[f"r{t}" for t in tenors]
    return df
def fly3(df,a,b,c):
    Da,Db,Dc=DUR[a],DUR[b],DUR[c]
    nb=(Dc-Db)/(Dc-Da); nc=(Db-Da)/(Dc-Da)
    return 2*df[f'y{b}']-df[f'y{a}']-df[f'y{c}'], df[f'r{b}']-nb*df[f'r{a}']-nc*df[f'r{c}'], (1.0,nb,nc)
def zs(z,w): return (z-z.rolling(w).mean())/z.rolling(w).std()

def hysteresis_pos(z,thr=1.0,h=0.5,clipv=2.0):
    """continuous target clip(z), position moves in steps >= h (no-trade band)."""
    tgt=z.where(z.abs()>thr,0.0).clip(-clipv,clipv).values
    pos=np.zeros(len(tgt)); cur=0.0
    for i,t in enumerate(tgt):
        if np.isnan(t): pos[i]=cur; continue
        d=t-cur
        if abs(d)>=h: cur=cur+np.sign(d)*round(abs(d)/h)*h
        pos[i]=cur
    return pd.Series(pos,index=z.index)

def run(z,fret,legs,freq='D',h=0.5,thr=1.0,cost_scale=True):
    if freq=='D': sig=hysteresis_pos(z,thr,h)
    else:
        p=hysteresis_pos(z,thr,h)
        grp=p.index.to_period('W')
        # correct: value available at t = last computed pos STRICTLY BEFORE current week (data<=t)
        prev=p.groupby(grp).last().shift(1)
        sig=prev.reindex(grp).set_axis(p.index).fillna(0.0)
    sig=sig.shift(1).fillna(0)
    gross=sig*fret
    to=sum((sig*w).diff().abs().fillna(0.0) for w in legs)
    net_noscale=gross-to*6e-4
    scale=(0.10/(net_noscale.expanding(60).std()*np.sqrt(252))).clip(upper=3.0).shift(1)
    to_eff=to*(scale if cost_scale else 1.0)
    net=gross-to_eff*6e-4
    scaled=(net*scale).dropna()
    gmean=gross.mean()*252*100; gvol=gross.std()*np.sqrt(252)*100
    return scaled, dict(gsr=gmean/gvol if gvol>0 else 0, gann=gmean, gvol=gvol,
        to=to.mean(), cost_noscale=to.mean()*6e-4*252*100, cost_eff=to_eff.mean()*6e-4*252*100, scale_med=scale.median())

cfgs=[('flyA',('DGS2','DGS5','DGS10'),'2006-01-01',75),('flyB',('DGS5','DGS10','DGS30'),'2006-01-01',75),
      ('flyC',('DGS10','DGS20','DGS30'),'2006-01-01',50),('billfly',('DGS1MO','DGS3MO','DGS6MO'),'2001-01-01',63)]
print(f"{'config':34s} {'gSR':>5} {'gAnn%':>6} {'gVol%':>6} {'to':>5} {'cstNS%':>7} {'cstEff%':>8} {'scMed':>5} | {'netSR':>6} {'ann%':>6} {'mdd%':>6} {'H1':>5} {'H2':>5} {'negy':>4} {'wst%':>6}")
best={}
for nm,tn,st,w in cfgs:
    df=build(list(tn),st); fly,fret,legs=fly3(df,*tn); z=zs(fly,w)
    for freq in ['D','W']:
        for h in ([1.0,0.5,0.25,0.1] if freq=='D' else [0.5,0.25]):
            r,info=run(z,fret,legs,freq,h)
            s=G.full_stats(r); h1,h2=G.halves_sr(r)
            print(f"{nm+' '+freq+' h'+str(h):34s} {info['gsr']:5.2f} {info['gann']:6.1f} {info['gvol']:6.1f} {info['to']:5.2f} {info['cost_noscale']:7.1f} {info['cost_eff']:8.1f} {info['scale_med']:5.2f} | {s['sr']:6.2f} {s['ann']:6.1f} {s['mdd']:6.1f} {h1:5.2f} {h2:5.2f} {s['negy']:4d} {s['worst']:6.1f}")
            best[(nm,freq,h)]=(s['sr'],r)
