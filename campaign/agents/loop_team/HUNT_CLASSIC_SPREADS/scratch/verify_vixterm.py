import sys, numpy as np, pandas as pd
sys.path.insert(0,'.')
import engine as E
DATA=f'{E.DATA}'; champ=E.champ_ref()
def load_ohlc(path, col='close'):
    df=pd.read_csv(path); df['date']=pd.to_datetime(df['date'])
    df=df.drop_duplicates('date').set_index('date').sort_index()
    return df[col]
v9=load_ohlc(f'{DATA}/more_vol/VIX9D.csv')['2011':]; v3m=load_ohlc(f'{DATA}/more_vol/VIX3M.csv')
slope=v3m-v9
def term_book(slope, lb=20, gate=1.0):
    m=slope.rolling(lb).mean(); sd=slope.rolling(lb).std().replace(0,np.nan); z=(slope-m)/sd
    pos=pd.Series(0.0,index=slope.index); pos[z<-gate]=1.0; pos[z>gate]=-1.0
    ret=slope.diff().shift(-1); gr=(pos*ret).dropna(); tup=pos.diff().abs().reindex(gr.index).fillna(0)
    net=gr-tup*6.4/1e4
    return net,pos,ret
net,pos,ret=term_book(slope,20,1.0); nv,_=E.vol_target(net['2011':].dropna())
# PROPER position-rotation scramble
def roll(p, r):
    g=(p*r).dropna(); t=p.diff().abs().reindex(g.index).fillna(0); n=g-t*6.4/1e4
    n,_=E.vol_target(n); return n.dropna()
rng=np.random.default_rng(0); T=len(pos); pv=pos.values; realv=nv.mean()/nv.std()*np.sqrt(252); cnt=0; srs=[]
for _ in range(300):
    lag=int(rng.integers(21,max(T-21,22))); psh=np.roll(pv,lag)
    nb=roll(pd.Series(psh,index=pos.index), ret.rename('r'))
    if len(nb) and nb.std()>0:
        s=nb.mean()/nb.std()*np.sqrt(252); srs.append(s)
        if s>=realv: cnt+=1
srs=np.array(srs)
print(f"VIX term 9_3 L20Z1: real SR={realv:.3f} null mean={srs.mean():.3f} p95={np.percentile(srs,95):.2f} scramble_p(P(null>=real))={cnt/300:.3f}")
