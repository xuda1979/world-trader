"""Cleaner trend test: developed-market FX + global equity indices only (no EM blowups, no risky
commodity ETFs). Honest check of whether turtle trend has merit absent roll-yield distortion."""
import sys, numpy as np, pandas as pd, glob, os
sys.path.insert(0,'.')
import engine as E
DATA=f'{E.DATA}'; champ=E.champ_ref()
def load_series(path, col=None):
    df=pd.read_csv(path); df['date']=pd.to_datetime(df['date']); s=df.set_index('date')
    c=col if col else ('close' if 'close' in s.columns else s.columns[0])
    return s[c][~s.index.duplicated()].sort_index()
# G10 FX (relative to USD) - use fx_hist
fx_names=['USD_AUD','USD_CAD','USD_CHF','USD_EUR','USD_GBP','USD_JPY','USD_NZD','USD_SEK','USD_NOK','USD_DKK']
uni={}
for n in fx_names:
    p=f'{DATA}/fx_hist/{n}.csv'
    if os.path.exists(p):
        try: uni[n]=load_series(p,'close')
        except: pass
uni['SP500']=load_series(f'{DATA}/newdata/SP500.csv')
uni['NIKKEI225']=load_series(f'{DATA}/newdata/NIKKEI225.csv')
uni['FTSE' if False else 'DJIA']=load_series(f'{DATA}/newdata/DJIA.csv')
px=pd.DataFrame(uni).ffill().dropna(how='any')['2000':]
ret=px.pct_change().replace([np.inf,-np.inf],np.nan)
entry,exitn=50,20
hi=px.shift(1).rolling(entry).max(); lo=px.shift(1).rolling(entry).min()
ehi=px.shift(1).rolling(exitn).max(); elo=px.shift(1).rolling(exitn).min()
pos=pd.DataFrame(0.0,index=px.index,columns=px.columns)
cl=px.values; hic=hi.values; loc=lo.values; ehc=ehi.values; elc=elo.values
for j in range(px.shape[1]):
    st=0.0; cv=np.zeros(px.shape[0])
    for i in range(px.shape[0]):
        x=cl[i,j]
        if np.isnan(x): cv[i]=st; continue
        if st==0.0:
            if not np.isnan(hic[i,j]) and x>hic[i,j]: st=1.0
            elif not np.isnan(loc[i,j]) and x<loc[i,j]: st=-1.0
        elif st==1.0:
            if not np.isnan(ehc[i,j]) and x<ehc[i,j]: st=0.0
        elif st==-1.0:
            if not np.isnan(elc[i,j]) and x>elc[i,j]: st=0.0
        cv[i]=st
    pos.iloc[:,j]=cv
gr=(pos.shift()*ret).sum(axis=1,min_count=1); turn=pos.diff().abs().sum(axis=1)
net=gr-turn*6.4/1e4
net08=net['2008':].dropna(); netvt,_=E.vol_target(net08)
def stats(r):
    r=r.dropna(); sr=r.mean()/r.std()*np.sqrt(252); eq=(1+r).cumprod()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(sr=sr,ann=eq.iloc[-1]**(252/len(r))-1,mdd=(eq/eq.cummax()-1).min(),
                negy=int((yr<0).sum()),worst=yr.min() if len(yr) else 0)
for tag,r in [('net vt',netvt)]:
    st=stats(r); _j=pd.concat([r.rename('s'),champ.rename('c')],axis=1,join='inner').dropna()
    print(f"{tag}: SR={st['sr']:.3f} ann={st['ann']*100:.1f}% MDD={st['mdd']*100:.1f}% negy={st['negy']} worst={st['worst']*100:.1f}% corr={_j['s'].corr(_j['c']):+.3f}")
