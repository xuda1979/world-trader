"""RECON 3: BAB + QMJ proxies built from twelve_big (298 names, full history) + VIX-gated timing
of MOM/HML + vol-managed MKT (Moreira-Muir with proper scaling). All T+1, 6bps, borrow, vt10, 2008+."""
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

# load panel: per-name close + vol from daily returns (25d rolling, min 10)
px={}; names=[]
for f in sorted(glob.glob('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/*.csv')):
    n=f.split('/')[-1][:-4]; names.append(n)
    d=pd.read_csv(f,index_col=0,parse_dates=True)
    px[n]=d['close']
P=pd.DataFrame(px)
R=P.pct_change()
# hygiene per HUNT_FUNDAMENTAL Q3: mask per-name |r|>25% prints (treat as missing)
Rm=R.mask(R.abs()>0.25)
vol=Rm.rolling(25,min_periods=10).std()
vol_fwd_known=vol.shift(1)   # vol known at t (from r up to t) -> use shift(1) so pos(t) uses vol(t-1)?? 
rows=[]
# BAB: pos(t) = low-vol long / high-vol short, weights = inverse of decile rank z
# uses vol known at t (vol from returns through t) => shift(1) in net_of gives T+1 anyway
v=vol
for look in (25,):
    # BETTING-AGAINST-BETA (Frazzini-Pedersen proxy): long low-vol half, short high-vol half, equal $ per name
    q=v.rank(axis=1,pct=True)
    lo=(q<=0.5); hi=(q>0.5)
    n_lo=lo.sum(axis=1); n_hi=hi.sum(axis=1)
    wl=lo.div(n_lo.replace(0,np.nan),axis=0).fillna(0.0)
    ws=-hi.div(n_hi.replace(0,np.nan),axis=0).fillna(0.0)
    rows.append(ev('BAB_v25_L05S05',(wl+ws),Rm))
    # with momentum tilt inside halves (low-vol long side ranked by 12-1 mom)
    mom=Rm.rolling(250,min_periods=200).sum().shift(21)
    mr=mom.rank(axis=1,pct=True)
    wl2=lo*(0.5+mr)*1.0; wl2=wl2.div(wl2.sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    ws2=hi*(0.5+(1-mr)); ws2=ws2.div(ws2.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)*-1
    rows.append(ev('BAB_v25_momtilt',(wl2+ws2),Rm))
    # QMJ-ish: use vol(low) + mom(high) long vs vol(high)+mom(low) short
    wl3=lo*(mr>=0.5); wl3=wl3.div(wl3.sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    ws3=hi*(mr<=0.5); ws3=ws3.div(ws3.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)*-1
    rows.append(ev('BABmom2x2_L_volmom_S_volloser',(wl3+ws3),Rm))
    # quality-minus-junk proxy: low vol + profitable... no fundamentals daily; use low-vol + low-downside
    dnv=Rm.copy(); dnv[dnv>0]=0
    dn=dnv.rolling(63,min_periods=40).std()
    qj=(dn.rank(axis=1,pct=True)<=0.3).astype(float)-(dn.rank(axis=1,pct=True)>=0.7).astype(float)
    qj=qj.div(qj.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    rows.append(ev('QMJproxy_lowdownside',qj,Rm))
    # low-vol L/S on REVERSAL feature (short-term rev within halves)
    r5=Rm.rolling(5).sum()
    r5r=r5.rank(axis=1,pct=True)
    wl4=lo*(r5r<=0.5); wl4=wl4.div(wl4.sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    ws4=hi*(r5r>0.5); ws4=ws4.div(ws4.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)*-1
    rows.append(ev('BABrev2x2',wl4+ws4,Rm))

df=pd.DataFrame(rows)
pd.set_option('display.width',250)
print(df.to_string(index=False))
df.to_csv('recon3_results.csv',index=False)
