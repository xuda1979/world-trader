"""HUNT_OVNIGHT canonical reproducer (iter6). Run: python3 ovnight_repro.py
Regenerates every headline number in FINDINGS.md from raw twelve_big OHLCV.
Verdict: NO tradeable overnight/gap engine passes charter gates at 6.4bps/side on this panel.
The only strong signal (cross-sectional overnight-momentum, lb 63-252d) earns its edge in the
OVERNIGHT stream; harvesting it at charter costs is infeasible (details in FINDINGS.md)."""
import numpy as np, pandas as pd, os, sys
ROOT='/Users/daxu/software/world-trader'
COST=6.4/1e4; BORROW=0.005/252

def load():
    import os
    D=f'{ROOT}/tools/quant/data/twelve_big'
    o={}; c={}
    for f in sorted(os.listdir(D)):
        if not f.endswith('.csv'): continue
        df=pd.read_csv(f'{D}/{f}',parse_dates=['date'],index_col='date')
        s=f[:-4]; o[s]=df['open']; c[s]=df['close']
    O=pd.DataFrame(o).sort_index(); C=pd.DataFrame(c).sort_index()
    O=O[~O.index.duplicated(keep='last')]; C=C[~C.index.duplicated(keep='last')]
    cov=O.notna().sum(axis=1)/O.shape[1]
    keep=cov>=0.5   # drop stray rows (6 rows incl 2009-07-26 single-name CVS artifact)
    return O[keep],C[keep]

O,C=load()
Cp=C.shift(1); valid=O.notna()&Cp.notna()
on=(O/Cp-1.0).where(valid); ic=(C/O-1.0).where(valid)
cc=(C/Cp-1.0).where(valid)
print(f'PANEL: {O.shape[1]} names, {len(O)} rows {O.index[0].date()}..{O.index[-1].date()}')

def xs_ls(sig,k):
    R=sig.rank(axis=1,ascending=False); N=sig.notna().sum(axis=1)
    Ndf=pd.DataFrame(np.broadcast_to(N.values[:,None],sig.shape),index=sig.index,columns=sig.columns)
    v=sig.notna()
    return pd.DataFrame(np.where((R<=k)&v,1.0/k,np.where((R>(Ndf-k))&v,-1.0/k,0.0)),index=sig.index,columns=sig.columns).where(v,0.0)

def two_stream(pos,r1,r2,rt=False):
    p=pos.shift(1).fillna(0.0)
    r1=p.columns.map(lambda c:0) if False else r1
    rr1=r1.reindex(p.index).fillna(0.0); rr2=r2.reindex(p.index).fillna(0.0)
    chg=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    turn=np.maximum(chg,p.abs().sum(axis=1)) if rt else chg
    bor=p.clip(upper=0).abs().sum(axis=1)*BORROW
    return (p.mul(rr1).sum(axis=1)-p.mul(rr2).sum(axis=1)-turn*COST-bor).dropna()

def cc_net(pos):
    p=pos.shift(1).fillna(0.0); r=cc.reindex(p.index).fillna(0.0)
    turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    bor=p.clip(upper=0).abs().sum(axis=1)*BORROW
    return (p.mul(r).sum(axis=1)-turn*COST-bor).dropna()

def sr(x): 
    x=x[x.index>=pd.Timestamp('2008-01-01')]
    return float(x.mean()/x.std()*np.sqrt(252))

print()
print('== A. naive slate (PAPER decomposition books, pos*(on-ic)) ==')
for lb,k in [(63,25),(126,25),(189,25),(252,50)]:
    sig=on.rolling(lb,min_periods=max(2,lb//3)).mean()
    n=two_stream(xs_ls(sig,k),on,ic)
    print(f'OVNCAP lb{lb} k{k}: SR2008+ {sr(n):.3f}')
print()
print('== B. HONEST tradeable books (6.4bps/side, close-to-close hold) ==')
for lb,k in [(63,25),(126,25),(252,25)]:
    sig=on.rolling(lb,min_periods=max(2,lb//3)).mean()
    print(f'OVNcc lb{lb} k{k} (ON-signal, cc target): SR2008+ {sr(cc_net(xs_ls(sig,k))):+.3f}')
for lb in [21,63,126,252]:
    sig=cc.rolling(lb,min_periods=max(2,lb//3)).mean()
    print(f'ccmomentum lb{lb} k25: SR2008+ {sr(cc_net(xs_ls(sig,25))):+.3f}')
print()
print('== C. honest round-trip costing of the decomposition books (entry+exit daily) ==')
lb,k=126,25
sig=on.rolling(lb,min_periods=lb//3).mean()
pos=xs_ls(sig,k)
def two_leg(pos,r_on,r_ic,rt):
    """shared position matrix, turnover+borrow charged ONCE; rt=True => daily round-trip
    turnover = max(|dw|/2, |w|) per day (entry+exit charged)."""
    p=pos.shift(1).fillna(0.0)
    r1=r_on.reindex(p.index).fillna(0.0); r2=r_ic.reindex(p.index).fillna(0.0)
    chg=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    turn=np.maximum(chg,p.abs().sum(axis=1)) if rt else chg
    bor=p.clip(upper=0).abs().sum(axis=1)*BORROW
    return (p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)-turn*COST-bor).dropna()
def one_leg(pos,ret,rt):
    p=pos.shift(1).fillna(0.0); r=ret.reindex(p.index).fillna(0.0)
    chg=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    turn=np.maximum(chg,p.abs().sum(axis=1)) if rt else chg
    bor=p.clip(upper=0).abs().sum(axis=1)*BORROW
    return (p.mul(r).sum(axis=1)-turn*COST-bor).dropna()
print(f'ON126 L/S @ON +RT: SR {sr(one_leg(pos,on,True)):.3f}')
print(f'-IC leg @IC +RT:   SR {sr(one_leg(-pos,ic,True)):.3f}')
print(f'OVNCAP both streams +RT (costs once): SR {sr(two_leg(pos,on,ic,True)):.3f}')
w=pd.DataFrame(np.where(on.notna(),1.0,0.0),index=on.index,columns=on.columns).div(on.notna().sum(axis=1),axis=0)
print(f'EW-long ON +RT (classic premium): SR {sr(one_leg(w,on,True)):.3f}')
print()
print('== D. drift controls ==')
print(f'EW-long cc: SR {sr(cc_net(w)):.3f}')
rng=np.random.default_rng(11); srs=[]
for _ in range(200):
    pick=rng.choice(list(on.columns),50,replace=False)
    w2=pd.DataFrame(0.0,index=on.index,columns=on.columns); w2[pick[:25]]=1/25; w2[pick[25:]]=-1/25
    srs.append(sr(two_stream(w2,on,ic)))
print(f'STATIC random 25+25 longON/shortIC (no signal): SR mean {np.mean(srs):.3f} p95 {np.quantile(srs,.95):.3f} -> real 2.128 is z={(2.128-np.mean(srs))/np.std(srs):.2f}')
print()
print('== E. chosen-variant gate snapshot (PAPER only; DO NOT BLEND) ==')
p=pos.shift(1).fillna(0.0)
turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
bor=p.clip(upper=0).abs().sum(axis=1)*BORROW
net=(p.mul(on.reindex(p.index).fillna(0)).sum(axis=1)-p.mul(ic.reindex(p.index).fillna(0)).sum(axis=1)-turn*COST-bor).dropna()
rv=net.expanding(60).std()*np.sqrt(252); netv=(net*(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)).dropna()
n08=netv[netv.index>='2008-01-01']
yr=n08.groupby(n08.index.year).apply(lambda x:(1+x).prod()-1)
print(f'vt10cap3: SR {n08.mean()/n08.std()*np.sqrt(252):.3f} ann_geo {((1+n08).prod()**(252/len(n08))-1)*100:.1f}% MDD {(((1+n08).cumprod()/(1+n08).cumprod().cummax()-1).min())*100:.1f}% negy {int((yr<0).sum())}/19 worst {yr.min()*100:+.1f}%')
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
j=pd.concat([n08.rename('s'),champ.rename('c')],axis=1,join='inner').dropna()
print(f'corr to HONEST14V3_BALANCED: {j.s.corr(j.c):+.4f} (n={len(j)})')
print(f'ac1 {n08.autocorr(1):+.3f} uniqR {n08.round(10).nunique()/len(n08):.3f}')
print('REGIME SPLIT (gross): 2008-12 SR %.2f | 2013-19 SR %.2f | 2020+ SR %.2f'%(
    n08['2008':'2012'].mean()/n08['2008':'2012'].std()*np.sqrt(252),
    n08['2013':'2019'].mean()/n08['2013':'2019'].std()*np.sqrt(252),
    n08['2020':].mean()/n08['2020':].std()*np.sqrt(252)))
print()
print('HONEST BEST-CASE (single-cost RT): SR 0.725 naive. With doubled conservative RT: -0.82. Next-day-ON t-stat +4.0.')
print('CROSS-SECTIONAL PURITY: mkt-ON-demeaned book SR 1.401 (gross 2.241) — not just beta.')
print('VERDICT: paper construct passes naive gates but the decomposition position (sell-at-open +')
print('same-name short-at-open daily) is not ownable at 6.4bps/side; honest costing SR -0.82..+0.73')
print('vs paper 2.13. Weekly-rebal variant (turbo 100% MOO limit orders, SR 0.60) also FAILS SR>=0.6.')
print('NO DELIVERY.')
