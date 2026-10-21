"""HUNT_CARRYFX lib — honest FX cross z-reversion + carry-tilt composite builder.
T+1 (signal decided at t from data<=t earns close_t->close_{t+1}), 6bps/side one-side turnover.
Carry accrual: FRED intl 10y monthly (PIT: month-m value usable from first bday of m+1), ffilled.
Convention per pair (a,b): long a / short b, leg weight w (z-driven); carry tilt adds
(+carry_a - carry_b) accrual on gross notional as return add-on at position w... (kept separate:
carry used as SIGNAL TILT on w only, never as phantom return).
"""
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
FXD=f"{ROOT}/tools/quant/data/fx"
FRED=f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
COST=6.0/1e4
ALLPAIRS=["AUD_USD","EUR_GBP","EUR_USD","GBP_USD","NZD_USD","USD_CAD","USD_CHF","USD_JPY"]

def load(p):
    df=pd.read_csv(f"{FXD}/{p}.csv",index_col=0,parse_dates=True)
    df=df[df.index.dayofweek<5]                      # spot FX closed Sat/Sun (stale rows)
    df=df[~df.index.duplicated(keep='last')].sort_index()
    return df

def load_close(pairs):
    d={p:load(p) for p in pairs}
    idx=None
    for p,df in d.items():
        i=df.index; idx=i if idx is None else idx.intersection(i)
    C=pd.DataFrame({p:d[p].close.reindex(idx) for p in pairs})
    assert C.isna().sum().sum()==0, C.isna().sum()
    return C

def sr(x):
    x=pd.Series(x).dropna()
    return float(x.mean()/x.std()*np.sqrt(252)) if x.std()>0 else np.nan

def zsig(C,a,b,lb=42,cap=2.0,div=2.0):
    """log-spread z; desired book weight w in [-cap/div, +cap/div] (fade), T+1 shifted outside."""
    sp=np.log(C[a])-np.log(C[b])
    z=(sp-sp.rolling(lb).mean())/sp.rolling(lb).std()
    return (cap*(-z)).clip(-cap,cap)/div

def carry_pit(c_a,c_b,index):
    """PIT monthly 10y-yield diff (base a minus quote b), value of month m usable from
    first business day of m+1 (HUNT_FXMICRO-verified PIT convention). Returns daily bps/252."""
    def y(c):
        s=pd.read_csv(f"{FRED}/{c}.csv",index_col=0,parse_dates=True).iloc[:,0]
        return pd.to_numeric(s,errors='coerce').dropna()
    Y=pd.DataFrame({'a':y(c_a),'b':y(c_b)}).dropna().resample('MS').last()
    diff=(Y['a']-Y['b']).shift(1)                    # month m usable from m+1
    diff=diff.reindex(pd.bdate_range(index.min(),index.max())).ffill()
    return (diff.reindex(index).ffill()/100.0/252.0)

CCY2FRED={'USD':'us2y','JPY':'jp10y','EUR':'ez10y','GBP':'gb10y','CAD':'ca10y',
          'AUD':'au10y','NZD':'nz10y','CHF':'ch10y'}

def book_pnl(C,a,b,lb=42,cap=2.0,div=2.0,carry_tilt=0.0,wday=None):
    """net daily PnL of one z-reversion book. carry_tilt g in [0,1]: w' = w*(1+g*tanh(carry_z))
    where carry_z = PIT 10y diff in %/yr standardized by 2% (sign: long high-carry leg more).
    wday: optional dict dow->size multiplier applied to DECISION day (T+1-safe)."""
    w=zsig(C,a,b,lb,cap,div)
    if carry_tilt>0:
        cp=carry_pit(CCY2FRED[a.split('_')[0]],CCY2FRED[b.split('_')[0]],C.index)
        cz=(cp*252*100/2.0).clip(-1,1)               # +2%/yr diff -> full tilt
        w=w*(1+carry_tilt*cz)
    if wday is not None:
        m=C.index.dayofweek.map(lambda d: wday.get(d,1.0))
        w=w*pd.Series(m,index=C.index)
    sig=w.shift(1)                                    # T+1
    R=C.pct_change()
    gross=sig*(R[a]-R[b])
    turn=2*sig.diff().abs()
    return (gross-turn*COST).dropna(how='all'), sig.dropna()

def stats(r):
    r=r.dropna()
    eq=(1+r).cumprod(); mdd=float((eq/eq.cummax()-1).min())
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    h=len(r)//2
    m=(1+r).resample('ME').prod()-1
    tot=r.sum(); o=np.argsort(r.values)[::-1]
    out=dict(n=len(r),start=str(r.index[0].date()),end=str(r.index[-1].date()),
        SR=round(sr(r),3),SR_m=round(sr(m.dropna()),3),
        ann_geo=round(float((1+r).prod()**(252/len(r))-1)*100,2),
        vol=round(float(r.std()*np.sqrt(252))*100,2),MDD=round(mdd*100,2),
        SR_H1=round(sr(r.iloc[:h]),3),SR_H2=round(sr(r.iloc[h:]),3),
        negyrs=int((yr<0).sum()),worst_yr=round(float(yr.min())*100,2),
        top5=round(float(r.values[o[:5]].sum()/tot)*100,1),
        top20=round(float(r.values[o[:20]].sum()/tot)*100,1),
        top50=round(float(r.values[o[:50]].sum()/tot)*100,1))
    out['ac1']=round(float(r.autocorr(1)),4)
    out['uniqR']=round(float(r.round(10).nunique()/len(r)),4)
    return out

def block_boot_p(r,B=10,nperm=200,seed=0):
    """charter scramble: moving-block bootstrap of RETURNS (block B), p(SR_boot<=0)."""
    x=r.dropna().values; n=len(x); nb=n//B
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n-B,size=(nperm,nb))
    real=sr(r); cnt=0
    for row in starts:
        xb=np.concatenate([x[s:s+B] for s in row])[:n]
        if xb.std()>0 and xb.mean()/xb.std()*np.sqrt(252)<=real: cnt+=1  # placeholder
    # p that SR<=0:
    rng=np.random.default_rng(seed)
    cnt=0
    for row in starts:
        xb=np.concatenate([x[s:s+B] for s in row])[:n]
        if xb.std()>0 and xb.mean()/xb.std()*np.sqrt(252)<=0: cnt+=1
    return cnt/nperm

def scrub_sr(r,k):
    x=r.dropna(); v=x.values; o=np.argsort(v)[::-1]
    keep=np.ones(len(v),bool); keep[o[:k]]=False
    return sr(pd.Series(v[keep],index=x.index[keep]))

def loyo_sr(r):
    return {int(y):round(sr(r[r.index.year!=y]),2) for y in sorted(set(r.index.year))}

def sig_scramble_p(bookargs,C,B=10,nperm=200,seed=0):
    """signal-level block scramble: permute the WEIGHT path in B-day blocks (same perm all books
    of one call), keep price moves fixed; p(perm SR >= real SR)."""
    w=zsig(C,bookargs[0],bookargs[1],*bookargs[2:]) if len(bookargs)==3 else zsig(C,bookargs[0],bookargs[1],bookargs[2])
    sig=w.shift(1).dropna()
    R=C.pct_change()
    d=R[bookargs[0]]-R[bookargs[1]]
    turn=2*sig.diff().abs()
    real=(sig*d.reindex(sig.index)-turn*COST).dropna()
    base=sr(real)
    v=sig.values; n=len(v); nb=n//B
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n-B,size=(nperm,nb))
    cnt=0
    for row in starts:
        vs=np.concatenate([v[s:s+B] for s in row])
        vs=np.concatenate([vs,v[nb*B:]])[:n]
        s_=pd.Series(vs,index=sig.index)
        net=(s_*d.reindex(sig.index)-2*s_.diff().abs()*COST).dropna()
        if sr(net)>=base: cnt+=1
    return cnt/nperm, round(base,3)
