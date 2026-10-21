"""Final honest Avellaneda-Lee: FORCE dollar-neutral each day (equal gross long & short by most-
extreme s-scores), low-turnover (hold names, only re-rank monthly to cut churn), raw-return P&L,
5bp one-way. This removes the unneutralized-market beta artifact from the prior pass.
"""
import sys, numpy as np, pandas as pd, glob, os, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
DATA="/Users/daxu/software/world-trader/tools/quant/data"; champ=E.champ_ref()
def load_close(path):
    try:
        df=pd.read_csv(path)
        if 'date' not in df.columns or 'close' not in df.columns: return None
        df['date']=pd.to_datetime(df['date']); return df.set_index('date')['close'].astype(float).sort_index()
    except: return None
px={}
for f in glob.glob(f"{DATA}/twelve_big/*.csv"):
    t=os.path.basename(f)[:-4]; s=load_close(f); px[t]=s
for f in glob.glob(f"{DATA}/twelve_extend/*.csv"):
    t=os.path.basename(f)[:-4]
    if t not in px: px[t]=load_close(f)
P=pd.DataFrame({k:v for k,v in px.items() if v is not None}); P=P.loc[:,~P.columns.duplicated()].apply(pd.to_numeric,errors='coerce')
P=P.ffill(); P=P.loc[:,P.columns[P.notna().sum()>2500]]; P=P[P.index>='2009-01-01']
lr=np.log(P/P.shift(1)).replace([np.inf,-np.inf],np.nan)
mkt=lr.mean(axis=1); T,N=lr.shape; lbl=21; Rv=lr.values; Mv=mkt.values
resid=lr.copy()*np.nan
for t in range(lbl,T):
    wm=Mv[t-lbl:t]; wr=Rv[t-lbl:t]; mw=wm-wm.mean(); var=np.dot(mw,mw)
    if var<1e-12: continue
    beta=(wr-wr.mean(axis=0)).T@mw/var; resid.iloc[t]=Rv[t]-(Mv[t]*beta)
# OU s-score + half-life, rolling
ss=pd.DataFrame(0.0,index=resid.index,columns=resid.columns); hl=pd.DataFrame(np.nan,index=resid.index,columns=resid.columns)
resid_arr=np.array(resid,dtype=float)
for c in range(N):
    r=pd.Series(Rv[:,c],index=resid.index)
    mu=r.rolling(60,min_periods=60).mean(); sd=r.rolling(60,min_periods=60).std()
    ss.iloc[:,c]=(r-mu)/sd
    x=resid_arr[:,c]
    for t in range(60,T):
        w=x[t-60:t]; m=np.nanmean(w); wc=w-m; v=np.dot(wc[:-1],wc[:-1]); cn=np.dot(wc[:-1],wc[1:])
        if v>1e-12 and 0<(cn/v)<1: hl.iloc[t,c]=-np.log(cn/v)/0.693
tradable=(hl>3)&(hl<60); z=ss.where(tradable,0.0)
print(f"universe {N} names, {T} days")

# dollar-neutral, monthly rebalance: each rebalance day pick top-K(|s|>1.25) long & short, EW both legs
rebal=pd.date_range('2012-01-01',z.index[-1],freq='MS')
pos=pd.DataFrame(0.0,index=z.index,columns=z.columns)
for i,dt in enumerate(rebal):
    if dt<z.index[0]: continue
    row=z.loc[z.index.asof(dt)] if dt not in z.index else z.loc[dt]
    s=row.dropna(); s=s[s.abs()>1.25]
    if len(s)<8: continue
    K=min(int(len(z.columns)*0.15), len(s)//2)
    longs=s.nsmallest(K).index; shorts=s.nlargest(K).index
    end=rebal[i+1]-pd.Timedelta(days=1) if i+1<len(rebal) else z.index[-1]
    mask=(pos.index>=dt)&(pos.index<=end)
    w=pd.Series(0.0,index=z.columns); w[longs]=1.0/K; w[shorts]=-1.0/K
    pos.loc[mask]=w.values
netexp=pos.sum(axis=1)
print("net exposure: mean=%.4f std=%.2f (should be ~0 if neutral)"%(netexp.mean(),netexp.std()))
gr=(pos.shift()*lr).sum(axis=1,min_count=1); turn=pos.diff().abs().sum(axis=1)
net=gr-turn*5/1e4
saves={}
for tag,rets in [('gross',gr),('net',net)]:
    r=rets[rets.index>='2012-01-01'].dropna(); nv,_=E.vol_target(r,vt_ann=0.08)
    st=E.evaluate(nv,champ,'al_neutral')
    saves[tag]=nv
    print(f"{tag}: SR={st['SR']:+.3f} ann={st['ann_geo']*100:+.1f}% MDD={st['MDD']*100:.1f}% negy={st['negyr']} "
          f"corr={st['corr_champ']:+.3f} turn={turn.mean():.2f} H=({st['H1_H2'][0]:.2f},{st['H1_H2'][1]:.2f})")
E.save_sleeve(saves['net'], "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_HF_STATARB/sleeves/al_dollar_neutral_net.csv")
print("SAVED al_dollar_neutral_net.csv")
