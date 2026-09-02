import numpy as np, pandas as pd, sys
ROOT="/Users/daxu/software/world-trader"
FXD=f"{ROOT}/tools/quant/data/fx"
COST=6.0/1e4

def load(p):
    df=pd.read_csv(f"{FXD}/{p}.csv",index_col=0,parse_dates=True)
    df=df[df.index.dayofweek<5]
    df=df[~df.index.duplicated(keep='last')].sort_index()
    return df

pairs={p:load(p) for p in ["GBP_USD","NZD_USD","AUD_USD","EUR_GBP"]}
# common calendar
idx=None
for p,df in pairs.items():
    i=df.index
    idx=i if idx is None else idx.intersection(i)
print("common weekdays:",len(idx),idx[0].date(),"..",idx[-1].date())
C=pd.DataFrame({p:pairs[p].close.reindex(idx) for p in pairs})
print("NaNs:",C.isna().sum().to_dict())

def zbook(pA,pB,lb=42,cap=2.0):
    """log-spread z-reversion: spread=log(P_A)-log(P_B); z=(sp-mean_lb)/std_lb;
    w (per-leg size, +w long A / -w long B) = clip(-z,-cap,cap)/2. T+1: sig.shift(1)."""
    la,lb_=np.log(C[pA]),np.log(C[pB])
    sp=la-lb_
    m=sp.rolling(lb).mean(); s=sp.rolling(lb).std()
    z=((sp-m)/s).shift(1)               # signal from data <= t
    w=(cap*(-z)).clip(-cap,cap)/2.0     # desired leg size, decided at t, earned t->t+1
    w=w.shift(1)                        # T+1
    r=C.pct_change()
    gross=w*(r[pA]-r[pB])
    turn=2*w.diff().abs()               # one-side turnover across 2 legs
    net=gross-turn*COST
    return net.dropna(how='all'),w

def sr(x): 
    x=x.dropna(); return float(x.mean()/x.std()*np.sqrt(252))

ref=pd.read_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv",index_col=0,parse_dates=True)["ret"]
books={"GBPNZD":("GBP_USD","NZD_USD"),"AUDGBP":("AUD_USD","GBP_USD"),"AUDEUR":("AUD_USD","EUR_GBP")}
comps={}
for name,(a,b) in books.items():
    net,w=zbook(a,b)
    comps[name]=net
    print(f"{name}: n={len(net)} SR={sr(net):.3f} vol={net.std()*np.sqrt(252)*100:.2f}%")
ew=pd.concat(comps,axis=1).mean(axis=1).dropna()
print(f"EW-3book: n={len(ew)} {ew.index[0].date()}..{ew.index[-1].date()} SR={sr(ew):.3f} vol={ew.std()*np.sqrt(252)*100:.2f}%")
j=pd.concat([ew.rename('mine'),ref.rename('ref')],axis=1,join='inner').dropna()
print(f"corr(my EW, committed FXMR3)={j.corr().iloc[0,1]:.4f} n={len(j)}  SR_ref={sr(ref):.3f}")
# variant: leg size clip(-z,-2,2) WITHOUT /2
def zbook2(pA,pB,lb=42,cap=2.0):
    la,lb_=np.log(C[pA]),np.log(C[pB]); sp=la-lb_
    z=((sp-sp.rolling(lb).mean())/sp.rolling(lb).std()).shift(1)
    w=(cap*(-z)).clip(-cap,cap)
    w=w.shift(1); r=C.pct_change()
    gross=w*(r[pA]-r[pB]); turn=2*w.diff().abs()
    return (gross-turn*COST).dropna(how='all'),w
ew2=pd.concat([zbook2(a,b)[0] for a,b in books.values()],axis=1).mean(axis=1).dropna()
j2=pd.concat([ew2.rename('mine'),ref.rename('ref')],axis=1,join='inner').dropna()
print(f"variant no-/2: SR={sr(ew2):.3f} vol={ew2.std()*np.sqrt(252)*100:.2f}% corr={j2.corr().iloc[0,1]:.4f}")
