"""Signal-level 10d-block scramble for the rebuilt FXMR3 EW-3book: shuffle each book's
signal path in 10-day blocks with the SAME permutation across books, rebuild PnL on the
SAME price moves. p = frac(perm SR >= real SR). 200x x5 seeds."""
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
FXD=f"{ROOT}/tools/quant/data/fx"; COST=6.0/1e4
def load(p):
    df=pd.read_csv(f"{FXD}/{p}.csv",index_col=0,parse_dates=True)
    df=df[df.index.dayofweek<5]; df=df[~df.index.duplicated(keep='last')].sort_index()
    return df
names=["GBP_USD","NZD_USD","AUD_USD","EUR_USD"]
pairs={p:load(p) for p in names}
idx=None
for p,df in pairs.items():
    i=df.index; idx=i if idx is None else idx.intersection(i)
C=pd.DataFrame({p:pairs[p].close.reindex(idx) for p in pairs}); R=C.pct_change()
def sr(x): x=x.dropna(); return float(x.mean()/x.std()*np.sqrt(252))
books=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD")]
LB=42; CAP=2.0; DIV=2.0
sig={}; spr={}; trn={}
for k,(a,b) in enumerate(books):
    sp=np.log(C[a])-np.log(C[b])
    z=(sp-sp.rolling(LB).mean())/sp.rolling(LB).std()
    w=((CAP*(-z)).clip(-CAP,CAP)/DIV).shift(1)
    sig[k]=w; spr[k]=(R[a]-R[b]); trn[k]=w.diff().abs()*2
SIG=pd.DataFrame(sig).dropna()
common=SIG.index
G_real=pd.Series(0.0,index=common); T_real=pd.Series(0.0,index=common)
for k in range(3):
    G_real+=SIG[k]*spr[k].reindex(common); T_real+=trn[k].reindex(common)
real=(G_real-T_real*COST)/3.0
base=sr(real)
print(f"EW-3book rebuilt: n={len(real)} {real.index[0].date()}..{real.index[-1].date()} SR={base:.3f} vol={real.std()*np.sqrt(252)*100:.2f}%")

def scramble(B,nperm,seed,base,sigdf=SIG):
    cols=list(sigdf.columns); v=sigdf.values; n=len(v); nb=n//B
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n-B,size=(nperm,nb))
    idx_n=common[:n]
    cnt=0
    for row in starts:
        vs=np.concatenate([v[s:s+B] for s in row])
        vs=np.concatenate([vs, v[nb*B:]])[:n]   # tail kept real (n not divisible by B)
        S=pd.DataFrame(vs,index=idx_n,columns=cols)
        g=pd.Series(0.0,index=idx_n); t=pd.Series(0.0,index=idx_n)
        for k in cols:
            g+=S[k]*spr[k].reindex(idx_n); t+=S[k].diff().abs()*2
        if sr(g-t*COST)>=base: cnt+=1
    return cnt/nperm
ps=[]
for sd in range(5):
    p=scramble(10,200,sd,base); ps.append(p)
    print(f"signal 10d-block scramble p(seed{sd}) = {p:.4f}")
print(f"min p over seeds = {min(ps):.4f}")
for k,(a,b) in enumerate(books):
    sk=SIG[[k]].dropna(); ik=sk.index
    bk=sr(((SIG[k]*spr[k].reindex(ik)-trn[k].reindex(ik)*COST)).dropna())
    pk=scramble(10,200,0,bk,sigdf=sk)
    print(f"  book{k} {a}/{b}: real SR {bk:+.2f}, scramble p {pk:.3f}")
# also: 200x iid-signal scramble (day-level) for reference
def scramble_iid(nperm,seed,base):
    v=SIG.values; n=len(v); rng=np.random.default_rng(seed); idx_n=common
    cnt=0
    for _ in range(nperm):
        vs=rng.permutation(v)
        S=pd.DataFrame(vs,index=idx_n,columns=[0,1,2])
        g=pd.Series(0.0,index=idx_n); t=pd.Series(0.0,index=idx_n)
        for k in range(3):
            g+=S[k]*spr[k].reindex(idx_n); t+=S[k].diff().abs()*2
        if sr(g-t*COST)>=base: cnt+=1
    return cnt/nperm
print(f"iid signal scramble p = {scramble_iid(200,0,base):.4f}")
