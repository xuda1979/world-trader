"""HUNT_CLASSIC_SPREADS — PAIRS TRADING (配对交易/统计套利), 299-stock panel.
Cointegration-style z-score on log-price ratio: 60d z, enter |z|>2, exit |z|<0.5, stop |z|>3.5.
Related-sector pair universe. EW book, T+1, 6.4bps, vol-target.
"""
import sys, numpy as np, pandas as pd, os
sys.path.insert(0,'.')
import engine as E
DATA=f'{E.DATA}'; champ=E.champ_ref(); OUT='/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves'

def load_close(t):
    df=pd.read_csv(f'{DATA}/twelve_big/{t}.csv')
    df['date']=pd.to_datetime(df['date']); df=df.drop_duplicates('date').set_index('date').sort_index()
    return df['close']

pairs=[('AAPL','MSFT'),('GOOGL','MSFT'),('NVDA','AMD'),('AMZN','META'),
  ('JPM','BAC'),('JPM','C'),('BAC','C'),('GS','MS'),
  ('XOM','CVX'),('XOM','COP'),('CVX','SLB'),('OXY','COP'),
  ('KO','PEP'),('PG','KMB'),('JNJ','PFE'),('MRK','PFE'),('DIS','CMCSA')]
valid=[]
for a,b in pairs:
    pa=os.path.exists(f'{DATA}/twelve_big/{a}.csv'); pb=os.path.exists(f'{DATA}/twelve_big/{b}.csv')
    if pa and pb:
        try:
            j=pd.concat([load_close(a).rename('a'),load_close(b).rename('b')],axis=1,join='inner').dropna()
            if len(j)>2000: valid.append((a,b,j))
        except Exception as e: pass
print(f"Valid pairs: {len(valid)}"); [print(' ',a,b,len(j)) for a,b,j in valid[:5]]

def pair_book(j, lb=60, entry=2.0, exitz=0.5, stop=3.5):
    sp=np.log(j['a']/j['b'])
    m=sp.rolling(lb).mean(); sd=sp.rolling(lb).std().replace(0,np.nan); z=(sp-m)/sd
    pos=pd.Series(0.0,index=sp.index); st=0.0
    for i,zz in z.items():
        if st==0.0:
            if zz>entry: st=-1.0
            elif zz<-entry: st=1.0
        elif st==-1.0:
            if abs(zz)<exitz: st=0.0
            elif zz<-stop: st=1.0
        elif st==1.0:
            if abs(zz)<exitz: st=0.0
            elif zz>stop: st=-1.0
        pos.loc[i]=st
    ret=sp.diff().shift(-1); gr=(pos*ret).dropna(); tup=pos.diff().abs().reindex(gr.index).fillna(0)
    return (gr-tup*6.4/1e4),pos

print("\n--- lookback / gate scan (equal-weight pairs book) ---")
allrecs=[]
for lb in [30,60,90,120]:
    for entry in [1.5,2.0,2.5]:
        nn=[]
        for a,b,j in valid:
            try: nn.append(pair_book(j,lb=lb,entry=entry)[0])
            except: pass
        if nn:
            bk=pd.concat(nn,axis=1).fillna(0).sum(axis=1)/len(nn)
            b08=bk['2008':].dropna(); bv,_=E.vol_target(b08)
            s=E.evaluate(bv,champ,'pairs')
            allrecs.append((s['SR'],lb,entry,s['ann_geo']*100,s['MDD']*100,s['negyr'],s['corr_champ'],s))
allrecs.sort(reverse=True)
print("top configs by SR:")
for sr,lb,en,ann,mdd,neg,corr,s in allrecs[:8]:
    print(f"  lb={lb:3d} entry={en:3.1f}: SR={sr:+.3f} ann={ann:+.1f}% MDD={mdd:.1f}% negy={neg} corr={corr:+.3f}")
rec=allrecs[0]; sr,lb,en,ann,mdd,neg,corr,s=rec
print("\nBEST config full gates:")
for k in ['SR','ann_geo','MDD','negyr','worst','H1_H2','negyr_pass','ac1','uniqR','corr_champ']:
    print(f"  {k:14s} = {s[k]}")
