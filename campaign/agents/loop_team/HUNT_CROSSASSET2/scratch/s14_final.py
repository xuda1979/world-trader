"""CORRECTED finals: per-leg cost convention (FXD1-frozen), T+1 shift INSIDE scramble pnl().
Families: sector trio, IEF/TLT DV01 books, HYG/LQD credit books. Full gate battery each."""
import sys; sys.path.insert(0,'.')
import pandas as pd, numpy as np
from lib import ROOT, BORROW, full_stats, halves_sr, negyr_tol, load_blend, flatten_gates, corr_to
COST=6.0/1e4
TD=f'{ROOT}/tools/quant/data/twelvedata'
def etf(t):
    df=pd.read_csv(f'{TD}/{t}.csv',index_col=0,parse_dates=True)
    v=pd.to_numeric(df['close'],errors='coerce'); v=v[v>0]
    return v[~v.index.duplicated(keep='last')].sort_index()
def zpos(spread,lb,cap):
    m=spread.rolling(lb).mean(); s=spread.rolling(lb).std()
    z=(spread-m)/s
    return (-z/cap).clip(-0.5,0.5)
def mkbook(A,B,lb,cap):
    """A,B = price series. pos {A:+w,B:-w}, w=-z/cap clip ±0.5. Returns (netR, posdf, retdf)."""
    rets=pd.DataFrame({0:A.pct_change(),1:B.pct_change()})
    sp=np.log(A/B)
    w=zpos(sp,lb,cap)
    pos=pd.DataFrame({0:w,1:-w})
    idx=pos.index  # == rets.index (union, all days)
    p=pos.fillna(0); rr=rets.fillna(0)
    ps=p.shift(1).fillna(0)
    gross=(ps*rr).sum(axis=1)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    bor=BORROW*ps.clip(upper=0.0).abs().sum(axis=1)
    return (gross-turn*COST-bor), p, rr
def scramble(posdfs, retdfs, n=200, seed=0, blk=10):
    P=pd.concat([p for p in posdfs],axis=1); R=pd.concat([r for r in retdfs],axis=1)
    P.columns=[f'c{k}' for k in range(P.shape[1])]; R.columns=P.columns
    pv=P.fillna(0).values; rv=R.fillna(0).values; idx=P.index
    T=len(pv); nb=T//blk
    def pnl(v):
        vs=np.vstack([np.zeros((1,v.shape[1])),v[:-1]])   # T+1 inside
        gr=(vs*rv).sum(axis=1)
        tn=(np.abs(np.diff(vs,axis=0,prepend=vs[:1]))/2).sum(axis=1)
        bo=BORROW*np.abs(np.clip(vs,None,0)).sum(axis=1)
        return pd.Series(gr-tn*COST-bo,index=idx).dropna()
    real_s=pnl(pv); real=real_s.mean()/real_s.std()*np.sqrt(252)
    rng=np.random.default_rng(seed); cnt=0
    for _ in range(n):
        k=int(rng.integers(3,nb-3))
        ns=pnl(np.roll(pv,k*blk,axis=0))
        if ns.std()>0 and ns.mean()/ns.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n,real
blend=load_blend()
def gates(label,netR,posdfs,retdfs):
    r2=netR[netR.index>='2008-01-01']
    st=full_stats(r2); h1,h2=halves_sr(r2); okn,negyrs=negyr_tol(r2)
    ps=[scramble(posdfs,retdfs,seed=s)[0] for s in (0,1,2)]
    fg=flatten_gates(r2); corr,nc=corr_to(r2,blend)
    yr=r2.groupby(r2.index.year).apply(lambda x:(1+x).prod()-1)
    ny={int(k):round(v*100,2) for k,v in yr[yr<0].items()}
    npass=sum([st['sr']>=0.6,h1>=0.3 and h2>=0.3,okn,max(ps)<0.05,fg['ac1']<0.5,fg['uniqR']>=0.08,abs(corr)<0.15])
    print(f"{label:26s} SR {st['sr']:.3f} ann {st['ann_geo']*100:5.1f}% MDD {st['mdd']*100:6.1f}% | H1 {h1:.2f} H2 {h2:.2f} | negy {st['negy']:2d} worst {st['worst']*100:6.2f}% | scr {[round(x,3) for x in ps]} | ac1 {fg['ac1']:.3f} uq {fg['uniqR']:.2f} | corr {corr:+.3f} | {npass}/7 | {ny}")
# sanity: FXD1 convention check with mkbook on DEX
from lib import NEW
def dex(n):
    df=pd.read_csv(f'{NEW}/{n}.csv',index_col=0,parse_dates=True)
    v=pd.to_numeric(df.iloc[:,0],errors='coerce'); v=v[v>0]
    return v[~v.index.duplicated(keep='last')].sort_index()
KO,SD=dex('DEXKOUS'),dex('DEXSDUS')
fxr,fp,fr=mkbook(KO,SD,21,2.0)
fxr2=fxr[fxr.index>='2008-01-01']
print('SANITY KO/SD lb21 cap2 single-book SR %.3f (FXDEPO grid reported 0.784 w/ their conv)'%full_stats(fxr2)['sr'])
# F1 sector trio
X={t:etf(t) for t in ['XLB','XLF','XLI']}
for lbs,name in [((15,),'lb15'),((21,42),'lb2142'),((15,21),'lb1521')]:
    res=[mkbook(X[a],X[b],lb,1.5) for a,b in [('XLB','XLF'),('XLB','XLI'),('XLF','XLI')] for lb in lbs]
    net=pd.concat([x[0] for x in res],axis=1).mean(axis=1)
    gates(f'TRIOzs g1.5 {name}',net,[x[1] for x in res],[x[2] for x in res])
# single XLB-XLI
net,p_,r_=mkbook(X['XLB'],X['XLI'],15,1.5)
gates('XLB-XLI lb15 g1.5',net,[p_],[r_])
# F2 rates: IEF-TLT DV01 ~ (17/7.5) IEF - TLT: pos weights w_IEF=+w*17/7.5*? scale to <=1 gross: use w scaled
I,T_,=etf('IEF'),etf('TLT')
def mkdv(A,B,lb,cap,dA=7.5,dB=17.0):
    """DV01-neutral: units n_A = d_B/d_A per unit of B. w_B=±0.5cap, w_A=∓0.5cap*dB/dA. clip gross<=1"""
    rets=pd.DataFrame({0:A.pct_change(),1:B.pct_change()})
    sp=np.log(A/B); m=sp.rolling(lb).mean(); s=sp.rolling(lb).std(); z=(sp-m)/s
    w=(-z/cap).clip(-0.5,0.5)*(dA/(dA+dB))*2  # wB on leg1, wA=dB/dA*wB... simplify: leg0 w = -w* dB/dA capped
    wB=w.clip(-0.5,0.5); wA=(-wB* dB/dA).clip(-0.5,0.5)
    pos=pd.DataFrame({0:wA,1:wB})
    p=pos.fillna(0); rr=rets.fillna(0); ps=p.shift(1).fillna(0)
    gross=(ps*rr).sum(axis=1); turn=(ps.diff().abs()/2).fillna(0).sum(axis=1)
    bor=BORROW*ps.clip(upper=0).abs().sum(axis=1)
    return (gross-turn*COST-bor),p,rr
for lb in [21,63,126]:
    net,p_,r_=mkdv(I,T_,lb,2.0)
    gates(f'IEF-TLT dv01 z lb{lb}',net,[p_],[r_])
# simple ratio z-rev IEF/TLT
for lb in [21,63]:
    net,p_,r_=mkbook(I,T_,lb,1.5)
    gates(f'IEF-TLT ratio z lb{lb}',net,[p_],[r_])
# F3 credit HYG/LQD
H,L=etf('HYG'),etf('LQD')
for lb in [21,63,126]:
    net,p_,r_=mkbook(H,L,lb,1.5)
    gates(f'HYG-LQD z lb{lb}',net,[p_],[r_])
