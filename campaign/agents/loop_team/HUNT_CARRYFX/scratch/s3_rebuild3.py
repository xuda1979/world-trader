import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
FXD=f"{ROOT}/tools/quant/data/fx"; COST=6.0/1e4
def load(p):
    df=pd.read_csv(f"{FXD}/{p}.csv",index_col=0,parse_dates=True)
    df=df[df.index.dayofweek<5]
    df=df[~df.index.duplicated(keep='last')].sort_index()
    return df
names=["GBP_USD","NZD_USD","AUD_USD","EUR_USD","EUR_GBP"]
pairs={p:load(p) for p in names}
idx=None
for p,df in pairs.items():
    i=df.index; idx=i if idx is None else idx.intersection(i)
C=pd.DataFrame({p:pairs[p].close.reindex(idx) for p in pairs})
R=C.pct_change()
def sr(x): x=x.dropna(); return float(x.mean()/x.std()*np.sqrt(252))
ref=pd.read_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv",index_col=0,parse_dates=True)["ret"]

def zbook(pA,pB,lb=42,cap=2.0,div=2.0,invA=False,invB=False):
    la=np.log(C[pA])*(-1 if invA else 1); lb_=np.log(C[pB])*(-1 if invB else 1)
    sp=la-lb_
    z=(sp-sp.rolling(lb).mean())/sp.rolling(lb).std()
    w=((cap*(-z)).clip(-cap,cap)/div).shift(1)
    rA=R[pA]*(-1 if invA else 1); rB=R[pB]*(-1 if invB else 1)
    gross=w*(rA-rB); turn=2*w.diff().abs()
    return (gross-turn*COST).dropna(how='all')

for tag,(a,b,ia,ib) in {
  "M1 GBPNZD":("GBP_USD","NZD_USD",False,False),
  "M2 AUDGBP":("AUD_USD","GBP_USD",False,False),
  "M3 aud/eur raw":("AUD_USD","EUR_USD",False,False),
  "M3b aud/inveur":("AUD_USD","EUR_USD",False,True),
  "M3c aud/eurGBP":("AUD_USD","EUR_GBP",False,False)}.items():
    n=zbook(a,b,invA=ia,invB=ib)
    print(f"{tag}: SR={sr(n):+.3f} vol={n.std()*np.sqrt(252)*100:.2f}%")

combs={"A(raw EURUSD)":["GBP_USD","NZD_USD","AUD_USD","GBP_USD","AUD_USD","EUR_USD"],
       "B(EURGBP)":["GBP_USD","NZD_USD","AUD_USD","GBP_USD","AUD_USD","EUR_GBP"]}
for lab,pp in combs.items():
    nets=[]
    for i in range(0,6,2):
        nets.append(zbook(pp[i],pp[i+1]))
    ew=pd.concat(nets,axis=1).mean(axis=1).dropna()
    j=pd.concat([ew.rename('m'),ref.rename('r')],axis=1,join='inner').dropna()
    print(f"EW3[{lab}]: n={len(ew)} SR={sr(ew):+.3f} vol={ew.std()*np.sqrt(252)*100:.2f}% corr_ref={j.corr().iloc[0,1]:+.4f} max|d|={ (ew-j['r']).abs().max():.2e}")
