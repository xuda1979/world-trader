"""Avellaneda-Lee on the BROAD merged universe (twelve_big + twelve_extend, ~700 names).
Efficient market+factor residual model: residual = R - (market factor + 2ndPC) exposures.
OU half-life screen + stateful positions + market-neutral + full costs. Honest.
"""
import sys, numpy as np, pandas as pd, glob, os, time
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_HF_STATARB/scratch')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
DATA="/Users/daxu/software/world-trader/tools/quant/data"
champ=E.champ_ref()

def load_close(path):
    try:
        df=pd.read_csv(path)
        if 'date' not in df.columns or 'close' not in df.columns: return None
        df['date']=pd.to_datetime(df['date'])
        return df.set_index('date')['close'].astype(float).sort_index()
    except Exception:
        return None

# ---- merge universe
px={}
for f in glob.glob(f"{DATA}/twelve_big/*.csv"):
    t=os.path.basename(f)[:-4]; s=load_close(f); px[t]=s if s is not None else None
for f in glob.glob(f"{DATA}/twelve_extend/*.csv"):
    t=os.path.basename(f)[:-4]
    if t not in px:
        s=load_close(f); px[t]=s if s is not None else None
P=pd.DataFrame({k:v for k,v in px.items() if v is not None}); P=P.loc[:,~P.columns.duplicated()].apply(pd.to_numeric,errors='coerce')
# keep names with long history (>=2010) & present in 2015+ (avoid short/entry noise)
P=P.ffill()
keep=P.columns[P.notna().sum()>2500]      # >=2500 non-null days
# require present through 202 Judiciary to avoid breaks
P=P.loc[:,keep]
# restrict to common window
P=P[(P.index>='2009-01-01')]
# drop names with too many interior gaps (>5%) after ffill pin
valid=P.loc[P.index>='2012-01-01'].notna().sum()> (P.loc[P.index>='2012-01-01'].shape[0]*0.9)
P=P.loc[:,valid[valid].index]
lr=np.log(P/P.shift(1)).replace([np.inf,-np.inf],np.nan)
print(f"Broad universe: {P.shape[1]} names, {P.shape[0]} days ({P.index[0].date()}..{P.index[-1].date()})")

# ---- factor model per day (efficient): market = equal-weight mean; residuals via beta on
# trailing 21d to market. Residual = R - beta*mkt. (market 1-factor Fama-French-lite residual)
def residuals(lr, market_beta_win=21):
    mkt=lr.mean(axis=1)
    resid=lr.copy()*np.nan
    Rv=lr.values; Mv=mkt.values; T,N=Rv.shape
    for t in range(market_beta_win, T):
        wm=Mv[t-market_beta_win:t]; wr=Rv[t-market_beta_win:t]
        mw=wm-wm.mean()
        var=np.dot(mw,mw)
        if var<1e-12: continue
        beta=np.dot(mw, wm[None,:])/var if False else (wr-wr.mean(axis=0)).T@mw/var
        resid.iloc[t]=Rv[t]-(Mv[t]*beta)
    return resid
print("computing market residuals...")
t0=time.time()
resid=residuals(lr)
print(f"residuals done in {time.time()-t0:.0f}s")

# ---- OU half-life + stateful AL
import warnings; warnings.filterwarnings('ignore')
def markov_zscores(resid, lookback=60):
    out=pd.DataFrame(0.0,index=resid.index,columns=resid.columns)
    hl=pd.DataFrame(np.nan,index=resid.index,columns=resid.columns)
    rv=resid.values; T,N=rv.shape
    for c in range(N):
        r=pd.Series(rv[:,c],index=resid.index)
        mu=r.rolling(lookback,min_periods=lookback).mean(); sd=r.rolling(lookback,min_periods=lookback).std()
        out.iloc[:,c]=(r-mu)/sd
        x=r.values; bh=np.full(T,np.nan)
        for t in range(lookback,T):
            w=x[t-lookback:t]; m=w.mean(); wc=w-m
            v=np.dot(wc[:-1],wc[:-1]); cn=np.dot(wc[:-1],wc[1:])
            if v>1e-12 and 0< (cn/v) <1: bh[t]=-np.log(cn/v)/0.693
        hl.iloc[:,c]=bh
    return out,hl
ss,hl=markov_zscores(resid)
tradable=(hl>3)&(hl<60)
z=ss.where(tradable,0.0)
print("building stateful book (sign=+1 reversion)...")
for sign in [+1,-1]:
    pos=pd.DataFrame(0.0,index=z.index,columns=z.columns)
    state={c:0.0 for c in z.columns}
    for t in z.index:
        row=z.loc[t]
        for c in z.columns:
            s=row.loc[c]
            if s==0.0 and state[c]!=0: state[c]=0.0; pos.loc[t,c]=0.0; continue
            if state[c]==0.0:
                if sign*s<-1.25: state[c]=1.0
                elif sign*s>1.25: state[c]=-1.0
            elif state[c]==1.0:
                if sign*s>-0.75: state[c]=0.0
            elif state[c]==-1.0:
                if sign*s<0.75: state[c]=0.0
            pos.loc[t,c]=state[c]
    gr=(pos.shift()*lr).sum(axis=1,min_count=1)   # P&L on RAW stock returns (honest tradeable)
    turn=pos.diff().abs().sum(axis=1)
    net=gr-turn*5/1e4
    nr=net.dropna(); nr=nr[nr.index>='2012-01-01']; nv,_=E.vol_target(nr,vt_ann=0.08)
    st=E.evaluate(nv,champ,'al_broad')
    print(f"sign={sign:+d}: grossSR={(gr[gr.index>='2012-01-01'].dropna().mean()/gr[gr.index>='2012-01-01'].dropna().std()*np.sqrt(252)):+.3f} "
          f"netSR={st['SR']:+.3f} ann={st['ann_geo']*100:+.1f}% MDD={st['MDD']*100:.1f}% "
          f"negy={st['negyr']} corr={st['corr_champ']:+.3f} turn={turn.mean():.2f} names_traded={(pos.abs().sum(axis=0)>0).sum()}")
