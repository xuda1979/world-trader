"""RECON 4: BAB done RIGHT on this panel (inv-vol weights, not equal-weight halves),
plus vol-managed timing of HML/MOM with realized-vol z gates, and VIX-gated MOM/HML timing.
Also: 63d lookback variants + short-vol-only leg. 2008+, T+1, 6bps, borrow, vt10."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd, glob

champ=lib.load_champion()
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

px={}
for f in sorted(glob.glob('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/*.csv')):
    n=f.split('/')[-1][:-4]
    px[n]=pd.read_csv(f,index_col=0,parse_dates=True)['close']
P=pd.DataFrame(px); R=P.pct_change(); Rm=R.mask(R.abs()>0.25)
print('panel:',P.shape, P.index.min().date(), P.index.max().date(),flush=True)

rows=[]
# (1) inv-vol BAB (weights proportional 1/vol, long-only = "low-vol sleeve" with 0 short side option)
for half in ('dec20','half'):
    v=Rm.rolling(25,min_periods=10).std()
    q=v.rank(axis=1,pct=True)
    if half=='dec20': m=(q<=0.2).astype(float)
    else: m=(q<=0.5).astype(float)
    w=m*(1.0/v)
    w=w.div(w.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    rows.append(ev(f'BABinvvol_longonly_{half}',w,Rm))
    ws=(q>=1-0.2 if half=='dec20' else q>=0.5).astype(float)*(1.0/v)
    ws=ws.div(ws.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    rows.append(ev(f'BABinvvol_L_{half}_S_hi',(w-ws),Rm))
# (2) HML/MOM vol-managed timing (Moreira-Muir done right: scale=1/trailing var, normalized)
ff=lib.load_ff3(); mom=lib.load_mom()
F={'HML':ff['HML'],'MOM':mom['MOM'],'MKT':ff['Mkt-RF'],'SMB':ff['SMB']}
one=lambda i: pd.Series(1.0,index=i)
for nm,s in F.items():
    s=s[s.index>='2005-01-01']
    rv63=s.rolling(63,min_periods=40).std()
    z=(rv63-rv63.expanding(252).mean())/rv63.expanding(252).std()
    for th in (0.0,0.5,1.0):
        pos=pd.Series(np.where(z.shift(1)<th,1.0,0.0),index=s.index)  # invest when vol BELOW z-th
        rows.append(ev(f'vm_{nm}_rv63_z{th}',pos,s))
df=pd.DataFrame(rows)
pd.set_option('display.width',250)
print(df.to_string(index=False))
df.to_csv('recon4_results.csv',index=False)
