"""HUNT_CLASSIC_SPREADS — VOLATILITY ARBITRAGE / variance-risk-premium (波动率套利).
Implied (VIX) -vs- realized (SP500 20d) premium. Sell vol when VIX rich vs realized,
buy vol when cheap. Proxy P&L via VIX-index moves. No VIX futures on disk -> VIX index proxy.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'.')
import engine as E
DATA=f'{E.DATA}'; champ=E.champ_ref(); OUT='/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves'

def load_ohlc(path, col='close'):
    df=pd.read_csv(path); df['date']=pd.to_datetime(df['date']); s=df.set_index('date'); c=col if col in s.columns else s.columns[0]; s=s[c]
    return s[~s.index.duplicated()].sort_index()

spx=load_ohlc(f'{DATA}/newdata/SP500.csv').dropna()
vix=load_ohlc(f'{DATA}/more_vol/VIX.csv').dropna()
rv=spx.pct_change().rolling(20).std()*np.sqrt(252)*100
df=pd.concat({'spx':spx,'vix':vix,'rv':rv},axis=1).dropna()
df['vix_rv_ratio']=df['vix']/df['rv']
df['dVIX']=df['vix'].diff()
rat=df['vix_rv_ratio']; m=rat.rolling(40).mean(); sd=rat.rolling(40).std().replace(0,np.nan)
z=(rat-m)/sd
pos=pd.Series(0.0,index=df.index); pos[z>1.5]=-1.0; pos[z<-1.5]=1.0
ret=df['dVIX']; gr=(pos.shift()*ret).dropna(); turn=pos.diff().abs().reindex(gr.index).fillna(0)
net=gr-turn*6.4/1e4
net08=net['2008':].dropna(); netvt,scal=E.vol_target(net08)
st=E.evaluate(netvt,champ,'volarb_vrp')

def roll_p(p, r):
    g=(p*r).dropna(); t=p.diff().abs().reindex(g.index).fillna(0); n=g-t*6.4/1e4
    n,_=E.vol_target(n); return n.dropna()
rng=np.random.default_rng(0); T=len(pos); pv=pos.values; realv=netvt.mean()/netvt.std()*np.sqrt(252); cnt=0
for _ in range(150):
    lag=int(rng.integers(21,max(T-21,22))); psh=np.roll(pv,lag)
    nb=roll_p(pd.Series(psh,index=pos.index), df['dVIX'])
    if len(nb) and nb.std()>0 and nb.mean()/nb.std()*np.sqrt(252)>=realv: cnt+=1
st['scramble_p']=cnt/150; st['scramble_pass']=st['scramble_p']<0.05
st['ALL_PASS']=bool(st['SR_pass'] and st['H_pass'] and st['negyr_pass'] and st['scramble_pass'] and st['corr_pass'] and st['flatten_pass'])
print("=== VOL ARB (z-rev on VIX/realized-20d ratio, T+1 via VIX-index) 2008+ ===")
for k in ['SR','ann_geo','MDD','negyr','worst','H1_H2','negyr_pass','scramble_p','ac1','uniqR','corr_champ']:
    print(f"  {k:14s} = {st[k]}")
print("  ALL_PASS =", st['ALL_PASS'])
if st['ALL_PASS']:
    E.save_sleeve(netvt, f"{OUT}/volarb_vrp_z402.csv")
    print("  saved volarb sleeve")
