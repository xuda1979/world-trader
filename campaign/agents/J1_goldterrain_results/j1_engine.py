import pandas as pd, numpy as np
COST=6e-4; MARG=0.045; BORR=0.005
def ann(r): 
    r=r.dropna(); n=len(r); return (1+r).prod()**(252/n)-1
def sr(r):
    r=r.dropna(); return r.mean()/r.std()*np.sqrt(252) if r.std()>0 else np.nan
def maxdd(r):
    r=r.dropna(); return float((((1+r).cumprod()/(1+r).cumprod().cummax())-1).min())
def stats(r, label):
    r=r.dropna()
    yrs=r.groupby(r.index.year)
    negy=int((yrs.apply(lambda x:(1+x).prod()-1)<0).sum())
    return dict(name=label, ann=round(ann(r)*100,2), sr=round(sr(r),3), maxdd=round(maxdd(r)*100,2),
                negy=negy, nyrs=r.index.year.nunique(), turn=round(float(r.index.to_series().diff().dt.days.mean())*0+ (np.nan),0))
def run(px, pos):
    """pos: position signal decided at close t (index t). Held on day t+1. T+1 causal."""
    ret=px.pct_change()
    W=pos.shift(1)                      # weight held during day t = pos_{t-1}
    turn=(pos-pos.shift(1)).abs().shift(1)   # turnover executed at t (from pos change at t-1), charged day t
    gross=W.abs()
    margin=MARG*np.clip(gross-1,0,None)/252
    borrow=BORR*np.clip(-W,0,None)/252
    r=W*ret-COST*turn-margin-borrow
    return r
def mom(px, skip=0): return px.shift(skip)/px.shift(252)-1
def volreg(px):
    v=px.pct_change().rolling(63).std()*np.sqrt(252)
    med=v.rolling(756,min_periods=252).median()
    return np.where(v>1.25*med,2,np.where(v<0.75*med,0,1))  # 0 low,1 mid,2 high (causal, trailing)
px=pd.read_csv('tools/quant/data/newdata2/gold_pm.csv',parse_dates=['date']).set_index('date').usd.sort_index()
vr=pd.Series(volreg(px),index=px.index)
m12=mom(px,21); m0=mom(px,0)
tr=m0>0
sig={
 'A1_TSMOM12m_LF': m0.where(m0>0,0.0),
 'A2_TSMOM12_1_LF': m12.where(m12>0,0.0),
 'A3_TSMOM12m_LS': np.sign(m0),
 'A4_TSMOM12_1_LS': np.sign(m12),
 'B1_TERRAIN_LF_benignbull': (tr&(vr!=2)).astype(float),
 'B2_TERRAIN_VT15_cap2': np.where(tr, np.minimum(0.15/(px.pct_change().rolling(63).std()*np.sqrt(252)),2.0),0.0),
 'B3_TERRAIN_LS_standdown_hivol': np.sign(m0).where(vr!=2,0.0),
 'B0_ALWAYS_LONG': pd.Series(1.0,index=px.index),
}
sig={k:pd.Series(v,index=px.index).where(px.notna()&px.shift(252).notna(),0.0) for k,v in sig.items()}
W=px.index>=pd.Timestamp(1968,4,1)
W08=px.index>=pd.Timestamp(2008,9,1)
champ=pd.read_csv('campaign/results/GOAL100_CHAMPION_daily.csv',parse_dates=['date']).set_index('date').ret
print("CHAMPION: sr",round(sr(champ),3),"ann%",round(ann(champ)*100,2),"maxdd%",round(maxdd(champ)*100,2),"n",len(champ))
rows=[]
for k,p in sig.items():
    r=run(px,p)
    def w(m): return r[m].dropna()
    rf, r8 = w(W), w(W08)
    j=pd.concat([r8.rename('s'),champ.rename('c')],axis=1).dropna()
    corr=float(j.s.corr(j.c))
    turn=float((p.diff().abs()).mean())*252
    rows.append(dict(sig=k, sr68=round(sr(rf),3), sr08=round(sr(r8),3), ann68=round(ann(rf)*100,2), ann08=round(ann(r8)*100,2),
                     dd68=round(maxdd(rf)*100,2), negy68=int((rf.groupby(rf.index.year).apply(lambda x:(1+x).prod()-1)<0).sum()),
                     turn=round(turn,3), corr_champ=round(corr,3)))
df=pd.DataFrame(rows); print(df.to_string(index=False))
# halves + era detail for top gates
for k,p in sig.items():
    r=run(px,p).dropna(); h1=r[:'1997-06-30']; h2=r['1997-07-01':]
    print(k,"H1_68-97 sr",round(sr(h1),3),"H2_97-26 sr",round(sr(h2),3),"| 1971+ sr",round(sr(r[r.index>=pd.Timestamp(1971,1,1)]),3),
          "| 71-80",round(sr(r['1971':'1980']),3),"81-99",round(sr(r['1981':'1999']),3),"00-07",round(sr(r['2000':'2007']),3),"08-15",round(sr(r['2008':'2015']),3),"16-26",round(sr(r['2016':]),3))

# ---- robustness: discrete positions + leak checks ----
print("--- discrete variants + leak checks ---")
disc={'A1d_LF':(m0>0).astype(float),'A4d_LS':np.sign(m0),
      'B1d_LF':(tr&(vr!=2)).astype(float),'B3d_LS':np.sign(m0).where(vr!=2,0.0)}
res={}
for k,p in disc.items():
    p=pd.Series(p,index=px.index); r=run(px,p)
    res[k]=(round(sr(r[W]),3),round(sr(r[W08]),3),round(ann(r[W])*100,2),round(ann(r[W08])*100,2))
    print(k,res[k])
# leak check: extra 1-day lag must NOT increase SR materially (same-period corr small)
for k,p in sig.items():
    if k=='B0_ALWAYS_LONG': continue
    p=pd.Series(p,index=px.index); r1=run(px,p); r2=run(px,p.shift(1).fillna(0.0))
    ret=px.pct_change()
    samecorr=float(pd.concat([p.shift(1)*ret,ret],axis=1).dropna().corr().iloc[0,1])
    print(k,"lag0 sr68",round(sr(r1[W]),3),"lag+1d sr68",round(sr(r2[W]),3),"same-period pos*ret corr",round(samecorr,3))
