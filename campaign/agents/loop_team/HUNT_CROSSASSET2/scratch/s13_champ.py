"""SECTOR-TRIO z-reversion in FXD1-frozen convention (per-leg costs, log-spread).
Candidates: lb in {(15,),(10,),(10,15,21),(15,21),(21,42)} x cap {1.5,2.0,3.0, sign}.
Gate battery with CORRECT leg-level 10d-block position-lag scramble (200x, seeds 0/1/2)."""
import sys; sys.path.insert(0,'.')
from lib import *
COST=6.0/1e4
TD=f'{ROOT}/tools/quant/data/twelvedata'
def etf(t):
    df=pd.read_csv(f'{TD}/{t}.csv',index_col=0,parse_dates=True)
    v=pd.to_numeric(df['close'],errors='coerce'); v=v[v>0]
    return v[~v.index.duplicated(keep='last')].sort_index()
def zpos(spread,lb,cap,mode='scaled'):
    m=spread.rolling(lb).mean(); s=spread.rolling(lb).std()
    z=(spread-m)/s
    if mode=='sign':
        w=pd.Series(0.0,index=spread.index); w[z<-1.0]=1/cap; w[z>1.0]=-1/cap
        return w
    return (-z/cap).clip(-0.5,0.5)
def net_of_book(pos,r):
    common=pos.index.intersection(r.index)
    p=pos.reindex(common).fillna(0.0); rr=r.reindex(common).fillna(0.0)
    ps=p.shift(1).fillna(0.0)
    gross=(ps*rr).sum(axis=1)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    bor=BORROW*ps.clip(upper=0.0).abs().sum(axis=1)
    return (gross-turn*COST-bor),p,rr
BOOKS=[('XLB','XLF'),('XLB','XLI'),('XLF','XLI')]
def build(lbs,cap=2.0,mode='scaled'):
    px={t:etf(t) for t in ['XLB','XLF','XLI']}
    lp={t:np.log(px[t]) for t in px}; rets={t:px[t].pct_change() for t in px}
    rs=[];PS=[];RR=[]
    for a,b in BOOKS:
        sp=lp[a]-lp[b]
        pos=sum(zpos(sp,lb,cap,mode) for lb in lbs)/len(lbs)
        r,p,rr=net_of_book(pd.DataFrame({a:pos,b:-pos}),pd.DataFrame({a:rets[a],b:rets[b]}))
        rs.append(r.fillna(0));PS.append(p);RR.append(rr)
    r=pd.concat(rs,axis=1).sum(axis=1)/3
    return r,r,PS,RR
def scramble_legs(PS,RR,n=200,seed=0,blk=10):
    # pooled position matrix & return matrix across books/legs
    idx=None
    for p in PS: idx=p.index if idx is None else idx.union(p.index)
    P=pd.concat([p.reindex(idx).fillna(0) for p in PS],axis=1)
    R=pd.concat([r.reindex(idx).fillna(0) for r in RR],axis=1)
    pv=P.values; rv=R.values; T=len(pv); nb=T//blk
    # real
    gr=(pv*rv).sum(axis=1); tn=(np.abs(np.diff(pv,axis=0,prepend=pv[:1]))/2).sum(axis=1)
    bor=BORROW*np.clip(pv,None,0).__abs__().sum(axis=1)
    net=pd.Series(gr-tn*COST-bor,index=idx).dropna()
    real=net.mean()/net.std()*np.sqrt(252)
    rng=np.random.default_rng(seed); cnt=0
    for _ in range(n):
        k=int(rng.integers(3,nb-3)); vs=np.roll(pv,k*blk,axis=0)
        t_=(np.abs(np.diff(vs,axis=0,prepend=vs[:1]))/2).sum(axis=1)
        b_=BORROW*np.abs(np.clip(vs,None,0)).sum(axis=1)
        ns=pd.Series((vs*rv).sum(axis=1)-t_*COST-b_,index=idx).dropna()
        if ns.std()>0 and ns.mean()/ns.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n,real
if __name__=='__main__':
    blend=load_blend()
    for cap in [1.5,2.0,3.0]:
        for lbs,name in [((15,),'lb15'),((10,),'lb10'),((10,15,21),'lb101521'),((15,21),'lb1521'),((21,42),'lb2142')]:
            r,_,PS,RR=build(lbs,cap)
            r2=r[r.index>='2008-01-01']
            st=full_stats(r2); h1,h2=halves_sr(r2); okn,negyrs=negyr_tol(r2)
            ps=[scramble_legs(PS,RR,seed=s)[0] for s in (0,1,2)]
            fg=flatten_gates(r2); corr,nc=corr_to(r2,blend)
            yr=r2.groupby(r2.index.year).apply(lambda x:(1+x).prod()-1)
            ny={int(k):round(v*100,2) for k,v in yr[yr<0].items()}
            npass=sum([st['sr']>=0.6,h1>=0.3 and h2>=0.3,okn,max(ps)<0.05,fg['ac1']<0.5,fg['uniqR']>=0.08,abs(corr)<0.15])
            print(f"cap{cap} {name:9s} SR {st['sr']:.3f} ann {st['ann_geo']*100:5.1f}% MDD {st['mdd']*100:6.1f}% | H1 {h1:.2f} H2 {h2:.2f} | negy {st['negy']} worst {st['worst']*100:6.2f}% | scr {[round(x,3) for x in ps]} | ac1 {fg['ac1']:.3f} uq {fg['uniqR']:.2f} | corr {corr:+.3f} | {npass}/7 | {ny}")
