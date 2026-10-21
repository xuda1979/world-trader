"""HUNT_CLASSIC_SPREADS — TREND FOLLOWING / CTA (趋势跟踪).
Turtle-style: 50d channel breakout entry, 20d exit, EW diversified 40-series universe,
portfolio-level trailing vol-target. Honest daily book. Spot/ETF/FX proxies (no roll futs).
"""
import sys, numpy as np, pandas as pd, glob, os
sys.path.insert(0,'.')
import engine as E
OUT='/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves'
DATA=f'{E.DATA}'; champ=E.champ_ref()

def load_series(path, col=None):
    df=pd.read_csv(path); df['date']=pd.to_datetime(df['date']); s=df.set_index('date')
    c=col if col else ('close' if 'close' in s.columns else s.columns[0])
    return s[c][~s.index.duplicated()].sort_index()

uni={}
for f in sorted(glob.glob(f'{DATA}/fx_hist/USD_*.csv')):
    n=os.path.basename(f)[:-4]
    try: uni[n]=load_series(f,'close')
    except: pass
for n in ['SP500','DJIA','NASDAQCOM','NIKKEI225']:
    try: uni[n]=load_series(f'{DATA}/newdata/{n}.csv')
    except: pass
for n in ['USO','GLD','SLV','DBC','BNO','CORN','WEAT','DBA','UNG','CPER']:
    p=f'{DATA}/more_etf/{n}.csv'
    if os.path.exists(p):
        try: uni[n]=load_series(p)
        except: pass
for n,fn in [('WTI','wti_spot_daily'),('BRENT','brent_spot_daily'),('NATGAS','natgas_HH_spot_daily')]:
    p=f'{DATA}/eia_weekly/{fn}.csv'
    if os.path.exists(p):
        try: uni[n]=load_series(p)
        except: pass

uni={k:v.dropna() for k,v in uni.items() if len(v.dropna())>3000}
px=pd.DataFrame(uni).ffill().dropna(how='all')
px=px['2000':]
# drop any column still with leading NaNs after ffill from 2000 (data not started)
px=px.dropna(axis=1, how='any')
ret=px.pct_change().replace([np.inf,-np.inf],np.nan)
print(f"Universe: {px.shape[1]} series, {px.shape[0]} rows, start {px.index.min().date()}")

entry,exitn=50,20
hi=px.shift(1).rolling(entry).max(); lo=px.shift(1).rolling(entry).min()
ehi=px.shift(1).rolling(exitn).max(); elo=px.shift(1).rolling(exitn).min()
pos=pd.DataFrame(0.0,index=px.index,columns=px.columns)
state_map={c:0.0 for c in px.columns}
# vectorized-ish state via loop over columns (rows loop; small enough)
cl=px.values; hic=hi.values; loc=lo.values; ehc=ehi.values; elc=elo.values
for j in range(px.shape[1]):
    st=0.0
    colvals=np.zeros(px.shape[0])
    for i in range(px.shape[0]):
        x=cl[i,j]
        if np.isnan(x): colvals[i]=st; continue
        if st==0.0:
            if not np.isnan(hic[i,j]) and x>hic[i,j]: st=1.0
            elif not np.isnan(loc[i,j]) and x<loc[i,j]: st=-1.0
        elif st==1.0:
            if not np.isnan(ehc[i,j]) and x<ehc[i,j]: st=0.0
        elif st==-1.0:
            if not np.isnan(elc[i,j]) and x>elc[i,j]: st=0.0
        colvals[i]=st
    pos.iloc[:,j]=colvals

# T+1 P&L: pos.shift() * ret (equal weight 1 per name; /N later)
gr=(pos.shift()*ret).sum(axis=1,min_count=1)
turn=pos.diff().abs().sum(axis=1)
net=gr-turn*6.4/1e4
net08=net['2008':].dropna()
# vol target portfolio
netvt,scal=E.vol_target(net08,vt_ann=0.08)
def stats(r):
    r=r.dropna(); sr=r.mean()/r.std()*np.sqrt(252); eq=(1+r).cumprod()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(sr=sr,ann=eq.iloc[-1]**(252/len(r))-1,mdd=(eq/eq.cummax()-1).min(),
                negy=int((yr<0).sum()),worst=yr.min() if len(yr) else 0,n=len(r))
print("\n=== TREND (Turtle 50/20) EW book, 2008+ ===")
for tag,r in [('gross pre-vt',net08),('net vt',netvt)]:
    st=stats(r); _j=pd.concat([r.rename('s'),champ.rename('c')],axis=1,join='inner').dropna()
    print(f"{tag:14s}: SR={st['sr']:.3f} ann={st['ann']*100:.1f}% MDD={st['mdd']*100:.1f}% "
          f"negy={st['negy']} worst={st['worst']*100:.1f}% corr={_j['s'].corr(_j['c']):+.3f} turn={turn.mean():.3f}")
# scramble
r=netvt.values; T=len(r); rng=np.random.default_rng(0); srr=netvt.mean()/netvt.std()*np.sqrt(252); cnt=0
for _ in range(100):
    lag=int(rng.integers(21,max(T-21,22))); rc=np.concatenate([r[lag:],r[:lag]])
    if rc.std()>0 and rc.mean()/rc.std()*np.sqrt(252)>=srr: cnt+=1
print(f"scramble p={cnt/100:.3f}")
E.save_sleeve(netvt, f"{OUT}/trend_turtle50_diverse.csv"); print("saved")
