"""FF2 TRADEABILITY: what does 'long FF MOM factor' / 'long FF Mkt-RF' mean in instruments?
Re-run the EXACT FF2 construction with r = SPY daily returns instead of FF factor returns:
- if SR collapses / corr explodes => the alpha is in the CRSP factor construction (long/short
  small-vs-big momentum book), NOT in a tradeable index => research-only.
Also: does the gate depend on factor values or only on lagged rv/VIX (observable)?"""
import sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
FFDIR=f"{ROOT}/tools/quant/data/ff_factors"
COST=6.0/1e4

def _parse_kf(path,colname):
    lines=open(path).read().split('\n'); hi=None
    for i,ln in enumerate(lines):
        if ln.startswith(',') and colname in ln: hi=i; break
    assert hi is not None
    rows=[]
    for ln in lines[hi+1:]:
        p=ln.split(',')
        if len(p)>=2 and p[0].strip().isdigit() and len(p[0].strip())==8: rows.append(p)
    df=pd.DataFrame(rows); df[0]=pd.to_datetime(df[0],format='%Y%m%d'); df=df.set_index(0)
    for c in df.columns: df[c]=pd.to_numeric(df[c],errors='coerce')
    return df.dropna(how='all')/100.0

ff=_parse_kf(f'{FFDIR}/F-F_Research_Data_Factors_daily.csv','Mkt-RF'); ff.columns=['Mkt-RF','SMB','HML','RF']
mom=_parse_kf(f'{FFDIR}/F-F_Momentum_Factor_daily.csv','Mom'); mom.columns=['MOM']
vix=pd.read_csv(f'{ROOT}/alphaportfolio_replication/data/vix_daily.csv',index_col=0,parse_dates=True)
vix=vix['vix'][~vix.index.duplicated(keep='last')].sort_index()

def rz(s,win=63,minp=40):
    rv=s.rolling(win,min_periods=minp).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()
def raw_net(pos,r):
    p=pos.shift(1).reindex(r.index)
    return (p*r-(p.diff().abs()/2.0).fillna(0.0)*COST).dropna()
def poolvt(r,tgt=0.08,cap=3.0):
    sd=r.rolling(60,min_periods=60).std()*np.sqrt(252)
    return (r*((tgt/sd).clip(upper=cap).shift(1).fillna(1.0))).dropna()
posA=pd.Series(np.where(rz(MOM).shift(1)<0.0,1.0,0.0),index=MOM.index)
posD=pd.Series(np.where((rz(MKT).shift(1)<0.5)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index)

# SPY proxy: use twelve_big SPY close (adjusted proxy close)
spy=pd.read_csv(f'{ROOT}/tools/quant/data/twelve_big/SPY.csv',parse_dates=['date'],index_col='date')['close'].sort_index()
spyret=spy.pct_change().fillna(0.0)
print("=== question 1: do the GATES need FF factor values? (gate inputs = lagged rv of the same series) ===")
print(f"posA gate input: rv63 of FF MOM; posD gate: rv63 of Mkt-RF + VIX ma252 z. Gates are lagged => no lookahead,")
print(f"but gates are computed on the PAPER factor series itself (MOM rv uses the untradeable L/S book's rv).")

print("\n=== question 2: replace PAPER returns with SPY returns, keep gates identical ===")
def variant(rA,rD,label):
    bl=raw_net(posA,rA)+raw_net(posD,rD)
    bl=bl[bl.index>=pd.Timestamp('2008-01-01')]
    out=poolvt(bl)
    rr=out[out.index>='2008-01-02']
    eq=(1+rr).cumprod()
    yr=rr.groupby(rr.index.year).apply(lambda x:(1+x).prod()-1)
    print(f"{label}: SR {rr.mean()/rr.std()*np.sqrt(252):+.3f} ann_geo {((eq.iloc[-1])**(252/len(rr))-1)*100:+.2f}% MDD {((eq/eq.cummax())-1).min()*100:.2f}% negy {int((yr<0).sum())}/{yr.size}")
    return out
base=variant(MOM,MKT,"PAPER (as delivered)")
spyv=variant(spyret.reindex(MOM.index).fillna(0.0),spyret.reindex(MKT.index).fillna(0.0),"SPY-proxied (same gates)")
j=pd.concat([base.rename('p'),spyv.rename('s')],axis=1,join='inner').dropna()
print(f"corr(PAPER, SPY-proxied) = {j.p.corr(j.s):+.4f}")

print("\n=== question 3: FF2 vs SPY raw corr + composition of FF MOM factor ===")
j2=pd.concat([base.rename('f'),spyret.rename('s')],axis=1,join='inner').dropna()
print(f"corr(delivered FF2 sleeve, SPY daily) = {j2.f.corr(j2.s):+.4f}  (n={len(j2)})")
print("FF MOM daily factor = (top-30%-momentum winners) - (losers), 6x6 size/mom portfolios, L/S SMALL-vs-BIG cmv-blended.")
print("No on-disk ETF tracks it (MTUM/QSPT absent from disk). Mkt-RF proxy = SPY minus RF (RF uncharged in proxy => small SR gift).")
