"""Cross-sectional commodity multi-factor (CTA 截面多因子) — momentum + carry-positioning proxy.
14+ year China commodity futures pool. Monthly rebalance; long bottom-20% (cheap/loser), short
top-20% (rich/winner) by cross-sectional factor; equal-weight; T+1 within rebalance. Honest gates.
"""
import sys, numpy as np, pandas as pd, os
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
ROOT="/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES"; DATA=ROOT+"/data"
champ=E.champ_ref()
UNIV=[s for s in ['RB0','CU0','NI0','I0','M0','Y0','P0','SR0','MA0','TA0','FU0','SC0','CF0','AU0','AG0','RM0','OI0','HC0','AL0','ZN0','PP0'] if os.path.exists(f"{DATA}/{s}.csv")]
def load(s):
    df=pd.read_csv(f"{DATA}/{s}.csv",index_col=0,parse_dates=True)
    return df['close'].astype(float).rename(s)
px=pd.DataFrame({s:load(s) for s in UNIV}).sort_index()
ret=px.pct_change()

def xsection_factor(px, ret, mom_lb=120, skip=20, rebal_days=21):
    """cross-sectional momentum + short-term reversal composite, monthly rebalance.
    Return series: long bottom-quintile, short top-quintile, EW, T+1."""
    closes=px.copy()
    # momentum = past mom_lb return skipping skip (standard skip-1m)
    mom=closes/closes.shift(mom_lb+skip)-1
    # reversal = past 5d (short-term)
    rev=-(closes/closes.shift(5)-1)
    factor=mom+rev*0.5  # simple composite (equal-ish)
    dates=closes.index
    pos=pd.DataFrame(0.0,index=dates,columns=closes.columns)
    rs=pd.Series(0.0,index=dates)
    lst_dates=[dates[0]]
    # monthly rebalance (every 21 trading days)
    for i in range(0,len(dates),rebal_days):
        lst_dates.append(dates[i])
    lst_dates=pd.to_datetime(sorted(set(lst_dates)))
    for i,dt in enumerate(lst_dates):
        if i==0: continue
        start=lst_dates[i-1]; 
        row=factor.loc[start]
        good=row.dropna()
        if len(good)<6: continue
        rk=good.rank(pct=True)
        # long bottom 20%, short top 20%
        sel_long=rk[rk<=0.25].index
        sel_short=rk[rk>=0.75].index
        w=pd.Series(0.0,index=closes.columns)
        if len(sel_long): w[sel_long]=1/len(sel_long)
        if len(sel_short): w[sel_short]=-1/len(sel_short)
        end=lst_dates[i+1]-pd.Timedelta(days=1) if i+1<len(lst_dates) else dates[-1]
        pos.loc[start:end]=w.values
    # T+1 P&L
    book=(pos.shift()*ret).sum(axis=1,min_count=1)
    turn=(pos.diff().abs().sum(axis=1))
    net=book-turn*6.4/1e4
    return net,pos

for mom_lb in [63,126,189,252]:
    net,pos=xsection_factor(px,ret,mom_lb=mom_lb)
    nr=net['2010':].dropna(); nv,_=E.vol_target(nr)
    st=E.evaluate(nv,champ,'xs_commodity')
    print(f"mom_lb={mom_lb:4d}: SR={st['SR']:+.3f} ann={st['ann_geo']*100:+5.1f}% MDD={st['MDD']*100:5.1f}% "
          f"negy={st['negyr']} H1={st['H1_H2'][0]:.2f} H2={st['H1_H2'][1]:.2f} corr={st['corr_champ']:+.3f} uniq={st['uniqR']:.2f}")
