import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
def bd(s):
    s=s.astype(float).dropna(); s=s[~s.index.duplicated(keep="last")].sort_index()
    return s.reindex(pd.bdate_range(s.index[0], s.index[-1])).ffill()
GLD=pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelvedata/GLD.csv',index_col=0,parse_dates=True)["close"].dropna()
GLD.index=pd.to_datetime(GLD.index)
COST=6.0
P={"natgas":bd(fred("natgas")),"xau":bd(GLD)}
R={k:v.pct_change() for k,v in P.items()}
wti,br=bd(fred("wti_full")),bd(fred("brent"))
idx=wti.index; w=wti.reindex(idx); b=br.reindex(idx)
valid=w.notna()&b.notna(); w=w.where(valid).ffill(); b=b.where(valid).ffill()
bad=((w<5)|(b<5)).fillna(True)
spr=(w-b).mask(bad)
z=(spr-spr.rolling(126).mean())/spr.rolling(126).std()
tb=bd(fred("tbill3m")).resample("D").ffill()
def vtclip(x,tgt,cap):
    v=x.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    return (x*(tgt/v).clip(0,cap)).fillna(0)
psp=np.sign(-z).where(z.abs()>1.0,np.nan)
psp=psp.where(z.abs()>0.75,0).ffill().fillna(0).shift(1).fillna(0)
bm=bad|bad.shift(1).fillna(True)
psp=psp.where(~bm,0.0)
fwd=(spr.diff()/w).shift(-1)
n1=psp*fwd-psp.diff().abs().fillna(0)*2*COST/1e4
n1=vtclip(n1,0.10,3.0)
p2,r2=P["natgas"],R["natgas"]
sig2=pd.Series(0.0,index=p2.index); sig2[p2.index.month.isin([11,12,1,2])]=1.0
vol2=r2.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
w2=(sig2*(0.10/vol2).clip(upper=1.0)).replace([np.inf,-np.inf],0.0).fillna(0.0)
rf=(tb.reindex(r2.index).ffill().fillna(0)/100.0/252.0)
n2=((w2.shift(1)*r2).fillna(0)+(1-w2.shift(1).clip(0,1))*rf-w2.diff().abs().fillna(0)*COST/1e4)
p3,r3=P["xau"],R["xau"]
sig3=(p3/p3.shift(252)-1>0).astype(float)*(p3/p3.shift(84)-1>0).astype(float)
vol3=r3.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
w3=(sig3*(0.10/vol3).clip(upper=1.0)).replace([np.inf,-np.inf],0.0).fillna(0.0)
n3=((w3.shift(1)*r3).fillna(0)+(1-w3.shift(1).clip(0,1))*rf-w3.diff().abs().fillna(0)*COST/1e4)
jj=pd.concat([n1,n2,n3],axis=1).sort_index().dropna()
m=jj.mean(axis=1)
rv=m.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
sleeve=(m*(0.08/rv).clip(0,3)).fillna(0)
e=sleeve[sleeve.index>='2007-06-01']
f=pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv',parse_dates=['date']).set_index('date')['ret']
j=pd.concat([e.rename('r'),f.rename('f')],axis=1,sort=True).dropna()
d=(j['r']-j['f']).abs()
print(f"carryv2 E1 rebuild: n={len(j)} corr={j['r'].corr(j['f']):.8f} max|d|={d.max():.3e} exact={(d<1e-12).sum()}")
