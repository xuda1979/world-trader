"""C5 Round-3 charter items 1-3.
Item 1: per-month weekday leg table estimated on IS 2008-2016 ONLY, frozen, applied full.
Item 2: exact EIA WNGSR season (first Thursday April -> last Thursday October) vs Apr-Oct.
Item 3: vol-regime sizing (trailing 63d SR of the raw book, cap 2x, floor 0).
Baseline = Round-2 summer book (SR 2.19, ann 27.2, MDD -11.9).
Also: honest full_stats on VIX-Fri and HO-Tue survivors for the FINDINGS log.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import apply_cost
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr

D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
COST=6e-4
s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
lr=np.log(s).diff(); idx=lr.index
IS_END='2016-12-31'

def build(legs_by_month, month_set, k=2.5):
    """legs_by_month: dict month -> {dow: sign}. Returns net vt-scaled series."""
    pos=pd.Series(0.0,index=idx)
    for m,legs in legs_by_month.items():
        msk=idx.month==m
        for dow,sgn in legs.items():
            pos[msk & (idx.dayofweek==dow)]=sgn
    thr=lr.rolling(90).std().shift(1)*k
    pos=pos.mask(lr.abs()>thr,0.0)
    gr=pos*lr.shift(-1)
    turn=pos.diff().abs(); turn.iloc[0]=abs(pos.iloc[0])
    net=(gr-turn*COST).dropna(); net=net[net.index>='2008-01-01']
    sc,_=vol_target(net)
    return sc.dropna()

BASE={m:{2:-1.,3:-1.,4:1.} for m in range(4,11)}
r_base=build(BASE,None)
print('BASE static summer:',{k2:round(v,2) for k2,v in full_stats(r_base).items() if k2!='yearly'})

# ---- Item 1: per-month leg selection on IS ONLY ----
# for each month 4..10, each dow: IS signed t-stat; keep legs with |t|>=2 (sign per IS)
leg_tab={}
rows=[]
for m in range(4,11):
    for dow in range(5):
        msk=(idx.month==m)&(idx.dayofweek==dow)&(idx<=IS_END)&(idx>='2008-01-01')
        pnl=lr[msk].dropna()
        if len(pnl)<30: continue
        t=pnl.mean()/pnl.std()*np.sqrt(len(pnl))
        rows.append((m,dow,round(t,2),len(pnl),round(pnl.mean()*1e4,1)))
        if abs(t)>=2.0: leg_tab.setdefault(m,{})[dow]=float(np.sign(t))
T=pd.DataFrame(rows,columns=['month','dow','IS_t','n','IS_mean_bp'])
print('--- IS leg t-table (2008-2016) ---'); print(T.pivot(index='month',columns='dow',values='IS_t').to_string())
print('selected legs (IS |t|>=2):',leg_tab)
r_rot=build(leg_tab,None)
print('ROT month-table:',{k2:round(v,2) for k2,v in full_stats(r_rot).items() if k2!='yearly'})

# variant: also add Tue-short where IS supports (leg_tab may include dow2 sign -1)
# variant: IS t>=1.5 threshold
leg_tab15={}
for m in range(4,11):
    for dow in range(5):
        msk=(idx.month==m)&(idx.dayofweek==dow)&(idx<=IS_END)&(idx>='2008-01-01')
        pnl=lr[msk].dropna()
        if len(pnl)<30: continue
        t=pnl.mean()/pnl.std()*np.sqrt(len(pnl))
        if abs(t)>=1.5: leg_tab15.setdefault(m,{})[dow]=float(np.sign(t))
r_rot15=build(leg_tab15,None)
print('ROT t>=1.5:',{k2:round(v,2) for k2,v in full_stats(r_rot15).items() if k2!='yearly'})

# ---- Item 2: exact EIA WNGSR season: first Thursday of April .. last Thursday of October ----
def season_mask(index):
    yrs=index.year.unique(); keep=np.zeros(len(index),bool)
    for y in yrs:
        apr=pd.Timestamp(y,4,1); # first Thursday
        d=(3-apr.dayofweek)%7; first_thu=apr+pd.Timedelta(days=d)
        octb=pd.Timestamp(y,10,31)
        d=(3-octb.dayofweek)%7; last_thu=octb-pd.Timedelta(days=d)
        keep|=((index>=first_thu)&(index<=last_thu)).values
    return pd.Series(keep,index=index)
sm=season_mask(idx)
BASEall={m:{2:-1.,3:-1.,4:1.} for m in range(1,13)}
pos=pd.Series(0.0,index=idx)
for m in range(1,13):
    for dow,sgn in BASEall[m].items():
        pos[(idx.month==m)&(idx.dayofweek==dow)]=sgn
thr=lr.rolling(90).std().shift(1)*2.5
pos=pos.mask(lr.abs()>thr,0.0)
pos[~sm]=0.0
gr=pos*lr.shift(-1); turn=pos.diff().abs(); turn.iloc[0]=abs(pos.iloc[0])
net=(gr-turn*COST).dropna(); net=net[net.index>='2008-01-01']
sc,_=vol_target(net); r_exact=sc.dropna()
print('EXACT season:',{k2:round(v,2) for k2,v in full_stats(r_exact).items() if k2!='yearly'})

# ---- Item 3: vol-regime sizing: size = trailing 63d SR of base book (trailing only), cap 2 floor 0 ----
pos_base=pd.Series(0.0,index=idx)
for m in BASE:
    for dow,sgn in BASE[m].items(): pos_base[(idx.month==m)&(idx.dayofweek==dow)]=sgn
pos_base=pos_base.mask(lr.abs()>thr,0.0)
gr_base=pos_base*lr.shift(-1)
turn_base=pos_base.diff().abs(); turn_base.iloc[0]=abs(pos_base.iloc[0])
net_base=(gr_base-turn_base*COST).dropna(); net_base=net_base[net_base.index>='2008-01-01']
sr63=net_base.rolling(63).mean()/net_base.rolling(63).std()*np.sqrt(252)
for cap in (2.0,1.0,1.5):
    size=(sr63.shift(1)/1.0).clip(lower=0,upper=cap).fillna(0)  # decided at t-1
    sized=net_base*size
    sc,_=vol_target(sized); r=sc.dropna()
    st=full_stats(r)
    print(f'VOLREGIME cap{cap}:',{k2:round(v,2) for k2,v in st.items() if k2!='yearly'})

# ---- VIX Fri / HO Tue honest full stats (documentation) ----
for nm,dw,d in [('vix',4,1),('DHOILNYH',2,-1)]:
    p='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred/vix.csv' if nm=='vix' else '/Users/daxu/software/world-trader/tools/quant/data/newdata/DHOILNYH.csv'
    ss=pd.read_csv(p,index_col=0,parse_dates=True).iloc[:,0]
    ss=pd.to_numeric(ss,errors='coerce'); ss=ss[ss>0].dropna().sort_index()
    l=np.log(ss).diff(); pos=pd.Series(0.0,index=l.index); pos[l.index.dayofweek==dw]=d
    g=pos*l.shift(-1); tn=pos.diff().abs(); tn.iloc[0]=abs(pos.iloc[0])
    n=(g-tn*COST).dropna(); n=n[n.index>='2008-01-01']
    sc,_=vol_target(n); st=full_stats(sc.dropna())
    yr=st.pop('yearly')
    print(f'{nm} dow{dw} dir{d} NET:',{k2:round(v,2) for k2,v in st.items()})
    print('  yearly:',yr)
