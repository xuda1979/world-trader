"""D3_fxfactor shared lib: DEX panel loaders, FX backtest, full gate suite."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval

ND='/Users/daxu/software/world-trader/tools/quant/data/newdata'
FR='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
BLEND='/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv'
COST=6.0/1e4

def _s(path):
    df=pd.read_csv(path,index_col=0,parse_dates=True)
    s=pd.to_numeric(df.iloc[:,0],errors='coerce').dropna()
    return s[~s.index.duplicated()].sort_index()

def load_dex():
    """USD per 1 local (rise = local appreciates vs USD). Tries newdata then fred dir."""
    loc_per_usd=[('INR','DEXINUS'),('BRL','DEXBZUS'),('ZAR','DEXSFUS'),('MXN','DEXMXUS'),
                 ('KRW','DEXKOUS'),('SGD','DEXSIUS'),('JPY','DEXJPUS'),('SEK','DEXSEUS'),
                 ('NOK','DEXNOUS'),('DKK','DEXDNUS'),('CAD','DEXCAUS'),('THB','DEXTHUS'),('TWD','DEXTWUS')]
    usd_per_loc=[('EUR','DEXUSEU'),('GBP','DEXUSUK'),('AUD','DEXUSAL')]
    out={}
    for name,code in loc_per_usd:
        for base in (ND,FR):
            try:
                s=_s(f'{base}/{code}.csv'); s=s[s>0]
                out[name]=1.0/s; break
            except Exception: pass
    for name,code in usd_per_loc:
        for base in (ND,FR):
            try:
                s=_s(f'{base}/{code}.csv'); s=s[s>0]; out[name]=s; break
            except Exception: pass
    df=pd.DataFrame(out).sort_index()
    # to business-day grid, ffill short gaps (holidays); DEX is stale-Friday sometimes
    bd=pd.bdate_range(df.index.min(),df.index.max())
    df=df.reindex(bd).ffill(limit=5)
    return df

def load_vix():
    s=_s(f'{FR}/vixcls.csv'); bd=pd.bdate_range(s.index.min(),s.index.max())
    return s.reindex(bd).ffill(limit=5)

def load_blend():
    b=pd.read_csv(BLEND,index_col=0,parse_dates=True)
    return b.iloc[:,0]

def weekly_pos(sig_d, week_start_only=True):
    """sig_d: daily signal already lagged to be tradable. Returns positions held daily,
    updated only on first trading day of ISO week."""
    iso=pd.Index(sig_d.index).isocalendar()
    wk=(iso['year'].astype(int).astype(str)+iso['week'].astype(int).astype(str)).values
    newweek=pd.Series(np.r_[True, wk[1:]!=wk[:-1]], index=sig_d.index)
    out=sig_d.where(newweek).ffill() if week_start_only else sig_d
    return out

def bt(sig_raw, px, start='2008-01-01', pub_lag=1, weekly=True, vt=0.10):
    """sig_raw: DataFrame (pos weights) computed from px WITHOUT any lag (info<=t).
    pub_lag: extra days for FRED noon-rate publication lag. T+1 execution.
    Returns (net_scaled, net_raw, scale, info)"""
    sig=sig_raw.shift(pub_lag+1)          # T+1 exec + publication lag
    if weekly: sig=weekly_pos(sig)
    px2=px.reindex(sig.index).ffill()
    ret=px2.pct_change().fillna(0.0)
    gross=(sig*ret).sum(axis=1)
    turn=sig.diff().abs().sum(axis=1).fillna(0.0)
    net=gross-turn*COST
    net=net[net.index>=start]
    scaled,scale=vol_target(net,vt_ann=vt) if vt else (net,pd.Series(1.0,index=net.index))
    return scaled,net,scale

def gates(scaled, name='x', min_sr=1.0, hmin=0.5, blend=None):
    s=full_stats(scaled); h1,h2=halves_sr(scaled)
    pv,real=scramble_pval(scaled,n=200,seed=0)
    g={'full_sr>=1.0':s['sr']>=min_sr,'H1>=0.5':h1>=hmin,'H2>=0.5':h2>=hmin,
       'negy<=2':s['negy']<=2,'worst>-5':s['worst']>-5.0,'scramble_p<0.05':pv<0.05}
    corr=None
    if blend is not None:
        j=pd.concat([scaled,blend],axis=1).dropna()
        if len(j)>250: corr=float(np.corrcoef(j.iloc[:,0],j.iloc[:,1])[0,1])
    # IS/OOS info split at 2018
    isd=scaled[scaled.index<'2018-01-01']; oos=scaled[scaled.index>='2018-01-01']
    res={'name':name,'start':str(scaled.index[0].date()),'end':str(scaled.index[-1].date()),
         'sr':round(s['sr'],2),'ann':round(s['ann'],1),'vol':round(s['vol'],1),'mdd':round(s['mdd'],1),
         'H1':round(h1,2),'H2':round(h2,2),'SR_IS':round(full_stats(isd)['sr'],2),
         'SR_OOS':round(full_stats(oos)['sr'],2) if len(oos)>250 else None,
         'negy':s['negy'],'worst':round(s['worst'],1),'scramble_p':round(pv,3),
         'corr_blend':None if corr is None else round(corr,3),'gates':g,'all_pass':all(g.values())}
    return res

def show(res):
    import json
    print(json.dumps({k:v for k,v in res.items() if k!='gates'},default=str))
    print({k:bool(v) for k,v in res['gates'].items()},'ALLPASS' if res['all_pass'] else 'FAIL')
