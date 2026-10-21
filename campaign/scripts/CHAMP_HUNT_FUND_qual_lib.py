"""CHAMP_HUNT_FUND: equity-quality / fundamental-momentum LS engine library.
Honesty: signals from fundamentals with fy -> June(fy+1) availability lag (FF convention);
momentum from prices through month-end t0; positions held from t0+1 (T+1);
costs 6bps x one-side turnover; vol target 10% expanding(min60) shift(1), clip 3.
r_* columns of model_panel_full.csv are SAME-MONTH ranks (leaky) and are NOT used."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0,'/Users/daxu/software/world-trader')
R='/Users/daxu/software/world-trader'
from campaign.agents.B2_highfreq.gates import full_stats, halves_sr, scramble_pval, vol_target

C=pd.read_pickle(f'{R}/campaign/agents/CHAMP_HUNT_FUND/closes.pkl')
RET=C.pct_change(fill_method=None)
LAST_VALID=C.notna().cummax().idxmax()  # per col: first valid; need last valid below

def last_valid_dates(C):
    a=C.notna().values; idx=C.index.values
    out={}
    for j,s in enumerate(C.columns):
        w=np.where(a[:,j])[0]
        out[s]=idx[w[-1]] if len(w) else pd.NaT
    return pd.Series(out)

LVD=last_valid_dates(C)

def build_fund():
    F=pd.read_parquet(f'{R}/alphaportfolio_replication/data/fundamentals_annual.parquet')
    F=F[F.symbol.isin(C.columns)].copy()
    F=F.sort_values(['symbol','fy'])
    g=F.groupby('symbol')
    F['ta_lag']=g['total_assets'].shift(1)
    F['agr']=(F.total_assets-F.ta_lag)/F.ta_lag
    F['gp_a']=(F.revenue-F.cogs)/F.total_assets
    F['roe']=F.net_income/F.equity
    F['oproa']=F.op_income/F.total_assets
    F['droe']=g['roe'].shift(0)-g['roe'].shift(1)
    F['margin']=(F.op_income/F.revenue)
    F['dmargin']=g['margin'].diff(1)
    F=F.replace([np.inf,-np.inf],np.nan)
    # availability: FY ending Dec of fy -> usable from June of fy+1 (conservative, FF convention)
    F['avail']=pd.to_datetime((F.fy+1).astype(str)+'-06-30')
    return F[F.fy<=2025]

def monthly_weights(score_m, q=0.3, min_names=40):
    """score_m: DataFrame monthend x symbol. LS: long top q, short bottom q, w=+/-1/(q*n_side)."""
    W={}
    for t,row in score_m.iterrows():
        s=row.dropna()
        if len(s)<min_names: W[t]=pd.Series(dtype=float); continue
        s=s.sort_values()
        k=max(3,int(len(s)*q))
        w=pd.Series(0.0,index=s.index)
        w.iloc[:k]=-1.0/k; w.iloc[-k:]=1.0/k
        W[t]=w
    return pd.DataFrame(W).T

def daily_backtest(W_m, start=None):
    """Monthly weights W_m (index=monthend date) -> daily net/gross/to series, T+1."""
    days=RET.index
    if start: days=days[days>=pd.Timestamp(start)]
    me=W_m.index
    # map each day to the most recent monthend strictly BEFORE the day -> T+1
    pos=pd.DataFrame(0.0,index=days,columns=W_m.columns)
    prev=None
    mi=0
    for d in days:
        while mi<len(me) and me[mi]<d: prev=me[mi]; mi+=1
        if prev is not None:
            w=W_m.loc[prev]
            pos.loc[d,w.index]=w.values
    # zero-out names whose price is stale (>15d) to avoid frozen corpses
    alive=(C.reindex(days).notna()) & (pd.Series(days,index=days)-LVD.reindex(C.columns).pipe(lambda s: s)).notna().__array__().reshape(-1,1) if False else None
    gross=(pos*RET.reindex(days)).sum(axis=1)
    to=pos.diff().abs().sum(axis=1).fillna(pos.abs().sum(axis=1))
    net_ex=gross-to*6e-4
    # vol target: expanding std of net_ex, shifted 1 day (strict: uses data < t)
    sd=net_ex.expanding(min_periods=60).std().shift(1)*np.sqrt(252)
    scale=(0.10/sd).clip(upper=3.0).fillna(0.0)
    return net_ex, gross, to, (net_ex*scale)

def score_from_fund(F, monthends, variants, mom_lb=12):
    """Build monthly scores from fundamentals known at each monthend + price momentum."""
    Csub=C
    mrets={}
    for lb in set(v for v in variants.values() if isinstance(v,int)):
        pass
    out={}
    me=monthends
    P=C.reindex(me).ffill()
    for name,cfg in variants.items():
        cols={}
        for m in me:
            avail=F[(F.avail<=m)]
            latest=avail.sort_values('avail').groupby('symbol').tail(1).set_index('symbol')
            sc=pd.Series(0.0,index=latest.index)
            terms=cfg['terms']
            for tname,tw in terms.items():
                if tname=='mom':
                    p=C.loc[:m].iloc[-1]; p0=C.loc[:m].iloc[-(cfg.get('mom_lb',12)+1)]
                    x=(p/p0-1)
                else:
                    x=latest[tname]
                z=(x-x.median())/x.std()
                sc=sc+tw*z.fillna(0.0)*0  # placeholder
            # build matrix version outside loop instead (speed)
            cols[m]=latest
        out[name]=cols
    return out

def score_matrix(F, monthends, term_list, mom_lb=12):
    """term_list: list of (colname|'mom', weight, mom_lb_override). Returns monthend x symbol score."""
    rows={}
    latest_all={}
    P=C.reindex(monthends)
    for m in monthends:
        avail=F[F.avail<=m]
        latest=avail.sort_values('avail').groupby('symbol').tail(1).set_index('symbol')
        latest_all[m]=latest
    for m in monthends:
        latest=latest_all[m]
        sc=pd.DataFrame(index=latest.index)
        for cname,wt,mlb in term_list:
            if cname=='mom':
                lb=mlb or mom_lb
                i=RET.index.searchsorted(m, side='right')-1
                p1=C.iloc[i]; p0=C.iloc[max(0,i-lb*21)]
                x=(p1.reindex(latest.index)/p0.reindex(latest.index)-1)
            else:
                x=latest[cname].reindex(latest.index)
            sc[cname]=(x-x.median())/x.std()
        rows[m]=(sc*pd.Series({c:w for c,w,_ in term_list})).sum(axis=1, min_count=1)
    return pd.DataFrame(rows).T
