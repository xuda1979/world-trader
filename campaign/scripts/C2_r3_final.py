"""C2 round-3 FINAL: honest low-turnover rates engines.
Key constructions (all decimal units, per-leg 6bps/side, T+1, trailing VT 10% clip 3.0):
1. flyA/B/C weekly-step z-reversion (charter 1-2): z sampled every 5/10/21 sessions.
2. monthly 2s10s reversion 1976+ (charter 3).
3. 20y-belly fly variants D_5s20s30s E_2s20s30s (charter 5).
4. BONUS: always-on DV01-neutral steepener carry (2s10s: long 2y x4.474 vs short 10y x1).
Run: python3 campaign/scripts/C2_r3_final.py
"""
import numpy as np, pandas as pd
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
BLEND='/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv'
DUR={'DGS1MO':0.08,'DGS3MO':0.25,'DGS6MO':0.5,'DGS2':1.9,'DGS5':4.4,'DGS10':8.5,'DGS20':15.0,'DGS30':17.5}
def yld(n):
    s=pd.read_csv(f'{FRED}/{n}.csv',index_col=0,parse_dates=True).iloc[:,0]
    s=pd.to_numeric(s,errors='coerce').replace([-99.99,-99.9],np.nan).dropna()
    return s[~s.index.duplicated(keep='last')].sort_index()
def rfn(y,d): return (-d*y.diff()/100.0+y/252/100.0)  # DECIMAL honest
def vt(net,vt_ann=0.10,clip=3.0):
    return (net*(vt_ann/(net.expanding(60).std()*np.sqrt(252))).clip(upper=clip).shift(1)).dropna()
def gates(sc):
    yr=sc.groupby(sc.index.year).apply(lambda x:(1+x).prod()-1)
    neg={int(k):round(v*100,1) for k,v in yr.items() if v<0}
    mid=sc.index[len(sc)//2]; h1,h2=sc[sc.index<=mid],sc[sc.index>mid]
    b=pd.read_csv(BLEND,index_col=0,parse_dates=True)['ret']
    i=sc.index.intersection(b.index); cb=np.corrcoef(sc[i],b[i])[0,1]
    return dict(sr=round(sc.mean()/sc.std()*np.sqrt(252),2),ann=round(sc.mean()*252*100,1),
        mdd=round(((1+sc).cumprod()/(1+sc).cumprod().cummax()-1).min()*100,1),
        negy=len(neg),worst=round(yr.min()*100,1),
        H1=round(h1.mean()/h1.std()*np.sqrt(252),2),H2=round(h2.mean()/h2.std()*np.sqrt(252),2),
        corr_blend=round(cb,3))
def fly3(a,b,c,start='2006-01-01'):
    ya,yb,yc=yld(a),yld(b),yld(c)
    Da,Db,Dc=DUR[a],DUR[b],DUR[c]
    nb,nc=(Dc-Db)/(Dc-Da),(Db-Da)/(Dc-Da)
    fly=2*yb-ya-yc
    rf=rfn(yb,Db)-nb*rfn(ya,Da)-nc*rfn(yc,Dc)
    df=pd.concat([fly.rename('fly'),rf.rename('rf')],axis=1).dropna()
    return df[df.index>=start], nb+nc
def step_z(df,gn,w=75,step=5,thr=1.0,clipv=2.0):
    z=(df['fly']-df['fly'].rolling(w).mean())/df['fly'].rolling(w).std()
    zz=z.iloc[::step]
    sig=zz.where(zz.abs()>thr,0.0).clip(-clipv,clipv)
    sig=sig.reindex(z.index).ffill().shift(1).fillna(0)
    gross=sig*df['rf']; to=sig.diff().abs().fillna(0)*gn
    return vt(gross-to*6e-4)
# charter 1-2: weekly-step flies
for nm,(a,b,c) in {'A_2s5s10s':('DGS2','DGS5','DGS10'),'B_5s10s30s':('DGS5','DGS10','DGS30'),
                   'C_10s20s30s':('DGS10','DGS20','DGS30'),'D_5s20s30s':('DGS5','DGS20','DGS30'),
                   'E_2s20s30s':('DGS2','DGS20','DGS30')}.items():
    df,gn=fly3(a,b,c)
    rows=[(step_z(df,gn,w,step,thr),w,step,thr) for w in (50,75,126) for step in (5,10,21) for thr in (0.75,1.0,1.5)]
    rs,_,_,_=max(rows,key=lambda t:t[0].mean()/t[0].std())
    print(f"fly {nm}: best weekly-step net {gates(rs)}")
# charter 3: monthly 2s10s reversion 1976+
y2,y10=yld('DGS2'),yld('DGS10'); sp=(y10-y2).dropna(); sp=sp[sp.index>='1976-06-01']
rfst=4.474*rfn(y2,1.9)-rfn(y10,8.5)
df=pd.concat([sp.rename('sp'),rfst.rename('rf')],axis=1).dropna()
z=(df['sp']-df['sp'].rolling(126).mean())/df['sp'].rolling(126).std()
zz=z.iloc[::21].clip(-2,2); sig=zz.reindex(z.index).ffill().shift(1).fillna(0)
gross=sig*df['rf']; to=sig.diff().abs().fillna(0)*5.474
print("monthly 2s10s rev 1976+: net SR",round(vt(gross-to*6e-4).mean()/vt(gross-to*6e-4).std()*np.sqrt(252),2))
# BONUS: always-on steepener carry (BEST engine found; fails gate d + scramble)
def steep_carry(a,b,Da,Db,start='2006-01-01'):
    ya,yb=yld(a),yld(b)
    w=Db/Da
    rf=w*rfn(ya,Da)-rfn(yb,Db)
    pos=pd.Series(1.0,index=rf[rf.index>=start].index).shift(1).fillna(0)
    rf=rf.reindex(pos.index)
    gross=pos*rf; to=pos.diff().abs().fillna(0)*(1+w)
    return vt(gross-to*6e-4)
for nm,(a,b,Da,Db) in {'2s10s':('DGS2','DGS10',1.9,8.5),'5s30s':('DGS5','DGS30',4.4,17.5),
                       '2s5s':('DGS2','DGS5',1.9,4.4)}.items():
    sc=steep_carry(a,b,Da,Db)
    print(f"always-on steepener {nm}: {gates(sc)}")
