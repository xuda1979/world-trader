import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
FXD=f"{ROOT}/tools/quant/data/fx"; COST=6.0/1e4
def load(p):
    df=pd.read_csv(f"{FXD}/{p}.csv",index_col=0,parse_dates=True)
    df=df[df.index.dayofweek<5]
    df=df[~df.index.duplicated(keep='last')].sort_index()
    return df
pairs={p:load(p) for p in ["GBP_USD","NZD_USD","AUD_USD","EUR_GBP"]}
idx=None
for p,df in pairs.items():
    i=df.index; idx=i if idx is None else idx.intersection(i)
C=pd.DataFrame({p:pairs[p].close.reindex(idx) for p in pairs})
R=C.pct_change()

def zbook(pA,pB,lb=42,cap=2.0,divide=2.0):
    sp=np.log(C[pA])-np.log(C[pB])
    z=(sp-sp.rolling(lb).mean())/sp.rolling(lb).std()
    w=(cap*(-z)).clip(-cap,cap)/divide   # desired at t from info<=t
    sig=w.shift(1)                        # T+1
    gross=sig*(R[pA]-R[pB])
    turn=2*sig.diff().abs()
    net=(gross-turn*COST).dropna(how='all')
    return net
def sr(x): x=x.dropna(); return float(x.mean()/x.std()*np.sqrt(252))
books={"GBPNZD":("GBP_USD","NZD_USD"),"AUDGBP":("AUD_USD","GBP_USD"),"AUDEUR":("AUD_USD","EUR_GBP")}
ref=pd.read_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv",index_col=0,parse_dates=True)["ret"]
for div in (2.0,1.0):
    for sgn,lab in ((1,"fade(-z)"),(-1,"mom(+z)")):
        nets={k:zbook(a,b,divide=div)*(sgn if lab=="mom(+z)" else 1) for k,(a,b) in books.items()}
        ew=pd.concat(nets,axis=1).mean(axis=1).dropna()
        j=pd.concat([ew.rename('m'),ref.rename('r')],axis=1,join='inner').dropna()
        print(f"div={div} {lab}: SR={sr(ew):+.3f} vol={ew.std()*np.sqrt(252)*100:.2f}% corr_ref={j.corr().iloc[0,1]:+.4f}")
# per-book with correct lag
for k,(a,b) in books.items():
    n=zbook(a,b); print(f"  {k}: SR={sr(n):+.3f} vol={n.std()*np.sqrt(252)*100:.2f}%")
