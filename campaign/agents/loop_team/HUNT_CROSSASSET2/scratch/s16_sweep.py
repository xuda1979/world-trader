"""FINAL SECTOR SWEEP (frozen conv) + RATES CURVE books (frozen conv).
Exit modes: zscaled (-z/cap), sign (flip at ±1), hysteresis (enter ±1.5, hold till z crosses 0)."""
import sys; sys.path.insert(0,'.')
import pandas as pd, numpy as np
from lib import ROOT, BORROW, full_stats, halves_sr, negyr_tol, load_blend, flatten_gates, corr_to
COST=6.0/1e4
TD=f'{ROOT}/tools/quant/data/twelvedata'
def etf(t):
    df=pd.read_csv(f'{TD}/{t}.csv',index_col=0,parse_dates=True)
    v=pd.to_numeric(df['close'],errors='coerce'); v=v[v>0]
    return v[~v.index.duplicated(keep='last')].sort_index()
def wpos(sp,lb,cap,mode):
    m=sp.rolling(lb).mean(); s=sp.rolling(lb).std(); z=(sp-m)/s
    if mode=='zs': w=(-z/cap).clip(-0.5,0.5)
    elif mode=='sign':
        w=pd.Series(0.0,index=sp.index); w[z<-1.0]=0.5; w[z>1.0]=-0.5
    else:  # hysteresis
        w=pd.Series(np.nan,index=sp.index)
        w[z<-1.5]=0.5; w[z>1.5]=-0.5
        w=w.ffill().fillna(0.0)
        w[(z>=-0.0)&(z<=0.0)]=w  # no-op
        # exit: when z crosses sign of position, zero out
        w[(w>0)&(z>0)]=0.0; w[(w<0)&(z<0)]=0.0
    return w
def mkbook(A,B,lb,cap,mode):
    rets=pd.DataFrame({0:A.pct_change(),1:B.pct_change()}).fillna(0)
    sp=np.log(A/B)
    w=wpos(sp,lb,cap,mode).fillna(0)
    pos=pd.DataFrame({0:w,1:-w})
    ps=pos.shift(1).fillna(0)
    gross=(ps*rets).sum(axis=1)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    bor=BORROW*ps.clip(upper=0.0).abs().sum(axis=1)
    return gross-turn*COST-bor,pos,rets
def scramble(posdfs,retdfs,n=200,seed=0,blk=10):
    P=pd.concat(posdfs,axis=1); R=pd.concat(retdfs,axis=1)
    P.columns=[f'c{k}' for k in range(P.shape[1])]; R.columns=P.columns
    pv=P.fillna(0).values; rv=R.fillna(0).values; idx=P.index; T=len(pv); nb=T//blk
    def pnl(v):
        vs=np.vstack([np.zeros((1,v.shape[1])),v[:-1]])
        gr=(vs*rv).sum(axis=1)
        tn=(np.abs(np.diff(vs,axis=0,prepend=vs[:1]))/2).sum(axis=1)
        bo=BORROW*np.abs(np.clip(vs,None,0)).sum(axis=1)
        return pd.Series(gr-tn*COST-bo,index=idx).dropna()
    rs_=pnl(pv); real=rs_.mean()/rs_.std()*np.sqrt(252)
    rng=np.random.default_rng(seed); cnt=0
    for _ in range(n):
        k=int(rng.integers(3,nb-3)); ns=pnl(np.roll(pv,k*blk,axis=0))
        if ns.std()>0 and ns.mean()/ns.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n
blend=load_blend()
def gates(label,netR,pd_,rd_):
    r2=netR[netR.index>='2008-01-01']
    st=full_stats(r2); h1,h2=halves_sr(r2); okn,_=negyr_tol(r2)
    ps=[scramble(pd_,rd_,seed=s) for s in (0,)]
    fg=flatten_gates(r2); corr,nc=corr_to(r2,blend)
    yr=r2.groupby(r2.index.year).apply(lambda x:(1+x).prod()-1)
    ny={int(k):round(v*100,2) for k,v in yr[yr<0].items()}
    npass=sum([st['sr']>=0.6,h1>=0.3 and h2>=0.3,okn,ps[0]<0.05,fg['ac1']<0.5,fg['uniqR']>=0.08,abs(corr)<0.15])
    print(f"{label:34s} SR {st['sr']:.3f} ann {st['ann_geo']*100:5.1f}% MDD {st['mdd']*100:6.1f}% | H1 {h1:.2f} H2 {h2:.2f} | negy {st['negy']:2d} worst {st['worst']*100:6.2f}% | scr {ps[0]:.3f} | corr {corr:+.3f} | {npass}/7 | {ny}")
X={t:etf(t) for t in ['XLB','XLF','XLI','XLE']}
P3=[('XLB','XLF'),('XLB','XLI'),('XLF','XLI')]
print('=== sector family sweep ===')
for mode in ['zs','sign','hyst']:
    for cap in [1.5,2.0]:
        for lbs in [(15,),(21,),(15,21),(21,63),(42,63),(21,42,63)]:
            res=[mkbook(X[a],X[b],lb,cap,mode) for a,b in P3 for lb in lbs]
            net=pd.concat([x[0] for x in res],axis=1).mean(axis=1)
            gates(f'P3 {mode} c{cap} lb{lbs}',net,[x[1] for x in res],[x[2] for x in res])
print('=== 5-book (add XLE pairs) zs c1.5 ===')
for lbs in [(15,),(21,63)]:
    P5=P3+[('XLE','XLF'),('XLE','XLI')]
    res=[mkbook(X[a],X[b],lb,1.5,'zs') for a,b in P5 for lb in lbs]
    net=pd.concat([x[0] for x in res],axis=1).mean(axis=1)
    gates(f'P5 zs c1.5 lb{lbs}',net,[x[1] for x in res],[x[2] for x in res])
print('=== rates curve books (frozen conv): two "instruments" = yields ===')
from lib import FRED
def fred(f):
    df=pd.read_csv(f'{FRED}/{f}.csv',index_col=0,parse_dates=True)
    v=pd.to_numeric(df.iloc[:,0],errors='coerce')
    return v[~v.index.duplicated(keep='last')].sort_index()
Y={f:fred(f) for f in ['DGS2','DGS5','DGS10','DGS30']}
def mkcurve(A,B,lb,cap,mode):
    rets=pd.DataFrame({0:Y[A].diff(),1:Y[B].diff()}).fillna(0)  # dv in yield pts; scale via vol-target later
    sp=Y[A]-Y[B]
    w=wpos(sp,lb,cap,mode).fillna(0)
    pos=pd.DataFrame({0:w,1:-w})
    ps=pos.shift(1).fillna(0)
    gross=(ps*rets).sum(axis=1)  # long A-yield short B-yield: A+dv, B-dv → pos*w*(dyA) + (-w)*(dyB)= w*d(spread)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    bor=0.0  # treasuries no borrow
    return (gross-turn*COST-bor),pos,rets
for sp_ in [('DGS2','DGS5'),('DGS2','DGS10'),('DGS5','DGS30'),('DGS2','DGS30')]:
    for mode in ['zs','sign']:
        for lb in [21,63,126,252]:
            net,pd_,rd_=mkcurve(sp_[0],sp_[1],lb,2.0,mode)
            gates(f'{sp_[0][3:]}s{sp_[1][3:]}s {mode} lb{lb}',net,[pd_],[rd_])
