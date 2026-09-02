"""RECON 2 (memory-safe): 48-industry xs momentum/reversal, 6pf SMB/HML spreads,
OP/INV decile Hi-Lo spreads, 10 momentum deciles Hi-Lo. T+1, 6bps/side, borrow, vt10."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

champ=lib.load_champion()

def parse_generic(path):
    """Handles both KF raw (comments then 'Average Value Weighted Returns -- Daily' header)
    and pre-cleaned decimal CSV (row 0 = header with leading '0,' or names)."""
    lines=open(path).read().split('\n')
    hi=None
    for i,ln in enumerate(lines):
        if 'Average Value Weighted Returns -- Daily' in ln: hi=i; break
    if hi is not None:
        cols=[c.strip() for c in lines[hi+1].split(',') if c.strip()]
        start=hi+2; pct=True
    else:
        # pre-cleaned: find first line that parses as header (contains letters) then data
        hdr=None
        for i,ln in enumerate(lines[:5]):
            parts=ln.split(',')
            if any(not p.strip().replace('.','').replace('-','').isdigit() for p in parts[1:]):
                hdr=i; break
        cols=[c.strip() for c in lines[hdr].split(',')[1:]]
        start=hdr+1; pct=False
    idx=[]; dat=[]; last=None
    for ln in lines[start:]:
        p=ln.split(',')
        tok=p[0].strip() if p else ''
        if tok.isdigit() and len(tok)==8:
            d=pd.to_datetime(tok,format='%Y%m%d')
            if last is not None and d<=last: break   # new section restarts dates
            last=d
            idx.append(d)
            dat.append([float(x) if x.strip() else np.nan for x in p[1:]])
        elif tok.count('-')==2 and len(tok)==10 and tok[0].isdigit():
            d=pd.to_datetime(tok,format='%Y-%m-%d')
            if last is not None and d<=last: break
            last=d
            idx.append(d)
            dat.append([float(x) if x.strip() else np.nan for x in p[1:]])
    df=pd.DataFrame(dat,index=pd.DatetimeIndex(idx),columns=cols)
    if pct: df=df.mask(df<=-99.0)/100.0
    df=df[~df.index.duplicated(keep='last')]
    return df

def ev(tag,pos,r):
    if isinstance(pos,pd.DataFrame): net=lib.net_of_book(pos,r)
    else: net,_=lib.net_of(pos,r)
    rv=net.expanding(60).std()*np.sqrt(252)
    net=net*((0.10/rv).clip(upper=3.0).shift(1).fillna(1.0))
    net=net[net.index>=pd.Timestamp('2008-01-01')].dropna()
    if len(net)<500 or float(net.std())==0.0: return dict(tag=tag,sr=np.nan,n=len(net))
    st=lib.full_stats(net); h1,h2=lib.halves_sr(net)
    okn,ny=lib.negyr_tol(net); fg=lib.flatten_gates(net); corr,_=lib.corr_to(net,champ)
    return dict(tag=tag,sr=round(st['sr'],2),h1=round(h1,2),h2=round(h2,2),negy=st['negy'],
                worst=round(st['worst'],3),ac1=round(fg['ac1'],2),uniq=round(fg['uniqR'],2),
                corr=round(corr,3),ann=round(st['ann_geo'],3),mdd=round(st['mdd'],3),n=st['n'])

rows=[]
ind=parse_generic('/Users/daxu/software/world-trader/tools/quant/data/kenfrench/48_Industry_Portfolios_Daily.csv')
print('48ind',ind.shape,flush=True)
for lb in (21,63,125):
    x=ind.rolling(lb).sum().shift(1)
    xr=x.sub(x.mean(axis=1),axis=0)
    pos=np.sign(xr).div(np.sign(xr).abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    rows.append(ev(f'indmom{lb}_LS',pos,ind))
    posr=(-np.sign(x)).div(np.sign(x).abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    rows.append(ev(f'indrev{lb}_LS',posr,ind))
del ind

p6=parse_generic('/Users/daxu/software/world-trader/tools/quant/data/kenfrench/6_Portfolios_2x3_Daily.csv')
print('6pf',p6.shape,flush=True)
one=pd.Series(1.0,index=p6.index)
sv=(p6['SMALL HiBM']+p6['BIG HiBM'])/2; sg=(p6['SMALL LoBM']+p6['BIG LoBM'])/2
rows.append(ev('HML_from_6pf',one,sv-sg))
ss=(p6['SMALL LoBM']+p6['SMALL HiBM'])/2; bb=(p6['BIG LoBM']+p6['BIG HiBM'])/2
rows.append(ev('SMB_from_6pf',one,ss-bb))
del p6

for f,tag in [('OP_VW_daily','OP'),('INV_VW_daily','INV')]:
    d=parse_generic(f'/Users/daxu/software/world-trader/tools/quant/data/kenfrench/{f}.csv')
    print(tag,d.shape,flush=True)
    one=pd.Series(1.0,index=d.index)
    rows.append(ev(f'{tag}_Hi30_Lo30',one,d['Hi 30']-d['Lo 30']))
    rows.append(ev(f'{tag}_Hi10_Lo10',one,d['Hi 10']-d['Lo 10']))
    del d

m10=parse_generic('/Users/daxu/software/world-trader/tools/quant/data/kenfrench/10_Portfolios_Prior_12_2_Daily.csv')
print('m10',m10.shape,flush=True)
one=pd.Series(1.0,index=m10.index)
rows.append(ev('MomDec_HiLo_VW',one,m10['Hi PRIOR']-m10['Lo PRIOR']))
# xs timing of deciles: long top-3 short bottom-3 by trailing 125d perf (factor rotation)
x=m10.rolling(125).sum().shift(1)
r=x.rank(axis=1)
ls=(r>=9).astype(float)-(r<=2).astype(float)
w=ls.div(ls.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
rows.append(ev('MomDec_rotation_top3bot3',w,m10))
del m10

df=pd.DataFrame(rows)
pd.set_option('display.width',250)
print(df.to_string(index=False))
df.to_csv('recon2_results.csv',index=False)
