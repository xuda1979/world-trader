import pandas as pd, numpy as np
np.random.seed(0)
D='/Users/daxu/software/world-trader/tools/quant/data/'
R='/Users/daxu/software/world-trader/campaign/agents/V1_volterm_results/'
COST=6e-4; MARG=0.045/252; BORR=0.005/252

def vol(n): return pd.read_csv(D+'more_vol/'+n+'.csv',parse_dates=['date']).set_index('date')['close']
def etf(n):
    df=pd.read_csv(D+'more_etf/'+n+'.csv',parse_dates=['date']).set_index('date')
    return df['close']
def px(n): return pd.read_csv(D+n+'.csv',parse_dates=['date']).set_index('date')['close']

spy=px('cboe_hist/SPY'); champ=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_CHAMPION_daily.csv',parse_dates=['date']).set_index('date')['ret']
vix,v3m,v6m,v9d,vxv,ovx,gvz=vol('VIX'),vol('VIX3M'),vol('VIX6M'),vol('VIX9D'),vol('VXV'),vol('OVX'),vol('GVZ')
xle=etf('XLE')
print('spans: VIX %s..%s VIX3M %s..%s VIX6M %s..%s VIX9D %s..%s VXV %s..%s OVX %s..%s GVZ %s..%s SPY %s..%s XLE %s..%s champ %s..%s'%(
 vix.index[0].date(),vix.index[-1].date(),v3m.index[0].date(),v3m.index[-1].date(),v6m.index[0].date(),v6m.index[-1].date(),
 v9d.index[0].date(),v9d.index[-1].date(),vxv.index[0].date(),vxv.index[-1].date(),ovx.index[0].date(),ovx.index[-1].date(),
 gvz.index[0].date(),gvz.index[-1].date(),spy.index[0].date(),spy.index[-1].date(),xle.index[0].date(),xle.index[-1].date(),
 champ.index[0].date(),champ.index[-1].date()))
# VXV vs VIX3M identity check
j=pd.concat([vxv,v3m],axis=1).dropna(); print('VXV~VIX3M overlap n=%d corr=%.4f'%(len(j),j.corr().iloc[0,1]))

sret=spy.pct_change()
def metr(r,name,turn):
    r=r.dropna(); n=len(r)
    if n<500 or r.std()==0: return dict(name=name,n=n,ann=np.nan,sr=np.nan,vv=np.nan,mdd=np.nan,turn=turn,corr=np.nan)
    ann=(1+r).prod()**(252/n)-1; sr=r.mean()/r.std()*np.sqrt(252); vv=r.std()*np.sqrt(252)
    cu=(1+r).cumprod(); mdd=(cu/cu.cummax()-1).min()
    ci=r.index.intersection(champ.index)
    cc=r[ci].corr(champ[ci]) if len(ci)>250 else np.nan
    return dict(name=name,n=n,ann=ann,sr=sr,vv=vv,mdd=mdd,turn=turn,corr=cc)

def bt(w,ret,sret_):
    # w decided at close t (index=t), held t+1; ret indexed by return day
    wp=w.shift(1).reindex(ret.index)
    cost=COST*(wp-wp.shift(1)).abs().fillna(0)
    r=wp*ret-cost
    r=r-( (-wp.clip(upper=0))*BORR )
    r=r-((wp.abs()-1).clip(lower=0))*MARG
    turn=(wp-wp.shift(1)).abs().fillna(0).sum()/ (len(wp)/252)
    return r,turn

results=[]
def run(name,w,ret,idx=None):
    if idx is not None: w=w.reindex(w.index.intersection(idx)).dropna()
    r,turn=bt(w,ret,None)
    m=metr(r,name,turn); results.append(m); return r,m

# master index: main window from VIX3M start
main=spy.index.intersection(vix.index).intersection(v3m.index)
main=main[main>=pd.Timestamp('2009-10-01')]
sret_m=sret.reindex(main)
slope=v3m/vix; slope=slope.reindex(main).ffill()
# sanity: slope NaN count
print('slope NaN in main:',slope.isna().sum(),'n days',len(main))

V={}
V['BH_SPY']=pd.Series(1.0,index=main)
V['TS_bin']= (slope>1.0).astype(float)
V['TS_bin_hyst']=np.nan
h=pd.Series(np.nan,index=main); s=slope.values; pos=0.0; out=[]
for v in s:
    if np.isnan(v): out.append(pos); continue
    if pos==0 and v>1.02: pos=1.0
    elif pos==1 and v<0.98: pos=0.0
    out.append(pos)
V['TS_bin_hyst']=pd.Series(out,index=main)
z=(slope-slope.rolling(504).mean())/slope.rolling(504).std()
V['TS_z']= (1-0.5*z.clip(-2,2)).clip(0,1)
V['TS_lin']=((slope-1)*10).clip(0,1)
V['TS_LS']=np.where(slope>1,1.0,-1.0); V['TS_LS']=pd.Series(V['TS_LS'],index=main)
spike=(vix.reindex(main).ffill()>32).astype(float)
V['TS_bin_vixgate']=V['TS_bin']*(1-spike)  # stand down on VIX spike
# VIX6M/VIX9D window
m2=spy.index.intersection(v6m.index).intersection(v9d.index); m2=m2[m2>=pd.Timestamp('2011-01-05')]
sl2=(v6m/v9d).reindex(m2).ffill(); sret2=sret.reindex(m2)
V['TS69_bin']=pd.Series((sl2>1.0).astype(float),index=m2)
V2={'BH_SPY':pd.Series(1.0,index=m2)}
# OVX gates on XLE (single-tenor: level + trend as slope proxies)
xo=pd.concat([xle,ovx],axis=1,join='inner').dropna(); xo=xo[xo.index>=pd.Timestamp('2010-01-01')]
xret=xle.pct_change().reindex(xo.index)
ovx_=ovx.reindex(xo.index)
V3={'BH_XLE':pd.Series(1.0,index=xo.index),
    'OVX_lt_med63':pd.Series((ovx_<ovx_.rolling(63).median()).astype(float).values,index=xo.index),
    'OVX_mom5':pd.Series((ovx_.pct_change(5)<0).astype(float).values,index=xo.index),
    'OVX_lt40':pd.Series((ovx_<40).astype(float).values,index=xo.index)}

rows=[]; series={}
for k,w in V.items(): series[k]=run(k,w,sret_m)[0]
for k,w in V2.items():
    r,turn=bt(w,sret2,None); series['69_'+k]=r; rows.append(metr(r,'69_'+k,turn))
for k,w in V3.items():
    r,turn=bt(w,xret,None); series['E_'+k]=r; rows.append(metr(r,'E_'+k,turn))
rows=[m for m in results if m['name'] in [k for k in V]] + rows
res=pd.DataFrame(rows).set_index('name')
print(res.round(4).to_string())
# scramble: circular-shift weights +252d vs returns for TS_bin_hyst
wp=V['TS_bin_hyst'].shift(252).shift(1).reindex(main); r=wp*sret_m-COST*wp.diff().abs().fillna(0)
print('scramble TS_bin_hyst SR=%.3f'%(r.dropna().mean()/r.dropna().std()*np.sqrt(252)))
pd.Series(series).to_pickle(R+'series.pkl'); res.to_csv(R+'grid1.csv')
