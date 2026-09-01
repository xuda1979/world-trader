"""E1 idea2: de-truncate a6r7_bond2y_trend (START 2007->1990, DGS2 1976+, 378d trend warmup only)
and brwt_spread_rev15 (min_start 2008->2000-05, brent floor 2000-01). Frozen params."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import save_sleeve, fred
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval

ROOT="/Users/daxu/software/world-trader"
BLEND = pd.read_csv(f'{ROOT}/campaign/results/GOAL100_CHAMPION20Y_BALANCED_daily.csv',
                    index_col=0, parse_dates=True).iloc[:,0]

def stats_report(name, r, eval_start):
    e=r[r.index>=eval_start]
    st=full_stats(e); h1,h2=halves_sr(e); pv,real=scramble_pval(e,200)
    a,b=e.align(BLEND,join='inner'); c=a.corr(b)
    pre=e[e.index<'2017-01-01']; post=e[e.index>='2017-01-01']
    print(f"== {name} eval {eval_start}+ ==")
    print(f" span {e.index.min().date()}..{e.index.max().date()} n={len(e)} SR={st['sr']:.2f} ann={st['ann']:.1f}% vol={st['vol']:.1f}% MDD={st['mdd']:.1f}% negy={st['negy']}/{st['years']} worst={st['worst']:.1f}%")
    print(f" H1={h1:.2f} H2={h2:.2f} scramble_p={pv:.4f} corr_blend={c:.3f} IS={pre.mean()/pre.std()*np.sqrt(252):.2f} OOS={post.mean()/post.std()*np.sqrt(252):.2f}")
    print(f" yearly={st['yearly']}")
    return e,st

# ---- a6r7 rebuild from 1990 (params frozen: DUR1.9 K378 CAD42 VT12 CAP5) ----
DUR,K,CAD,VT,CAP=1.9,378,42,0.12,5.0
y=pd.read_csv(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv",index_col=0,parse_dates=True)["value"].astype(float)/100.0
y=y[~y.index.duplicated(keep="last")].sort_index()
tr=(-DUR*y.diff()+y/252.0).dropna()
sig=(tr.rolling(K).mean()>0).astype(float)
W=sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
gross=(W.shift(1)*tr)                       # NO truncation
turn=(W.shift(1)-W.shift(2)).abs().fillna(0.0)
net=(gross-turn*6.0/1e4).dropna()
lev=(VT/np.sqrt(252)/net.expanding(60).std().shift(1)).clip(0,CAP).fillna(0.0)
a6=(net*lev).dropna()
e,st=stats_report('E1_a6r7_1990',a6,'1992-01-01')

# plateau quick: K neighbors
for Kk in [252,315,378,441,504]:
    sg=(tr.rolling(Kk).mean()>0).astype(float)
    Wk=sg.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
    gk=(Wk.shift(1)*tr); tk=(Wk.shift(1)-Wk.shift(2)).abs().fillna(0)
    nk=(gk-tk*6e-4).dropna(); lk=(VT/np.sqrt(252)/nk.expanding(60).std().shift(1)).clip(0,CAP).fillna(0)
    rk=(nk*lk).dropna(); ek=rk[rk.index>='1992-01-01']
    print(f"  K={Kk}: SR={ek.mean()/ek.std()*np.sqrt(252):.2f}", end=' ')
print()

# ---- brwt rebuild from brent floor 2000 (params frozen: lookback15 z +-1.5) ----
BR=fred('brent').dropna(); WT=fred('wti_full').dropna()   # wti_full = 1986+, same WTI series
sp=(np.log(BR)-np.log(WT)).dropna()
z=(sp-sp.rolling(15,min_periods=15).mean())/sp.rolling(15,min_periods=15).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp.index); pos[z<-1.5]=1.0; pos[z>1.5]=-1.0
ret=sp.diff().shift(-1)
net=pos*ret-(pos.diff().abs()/2.0)*6e-4
br_net=net.dropna()
br_sc,_=vol_target(br_net); br_sc=br_sc.dropna()
eb,sb=stats_report('E1_brwt_2000',br_sc,'2001-01-01')
# overlap check vs original
old=pd.read_csv(f"{ROOT}/campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv",index_col=0,parse_dates=True).iloc[:,0]
j=pd.concat([br_sc.rename('new'),old.rename('old')],axis=1,join='inner').dropna()
print(f"brwt overlap corr={j.corr().iloc[0,1]:.4f} n={len(j)}")

save_sleeve(a6,f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
"E1 de-truncated a6_r7_bond2y_trend: identical frozen construction (FRED DGS2 quote dates, synthetic 2y TR=-1.9*dy+y/252, long when 378-obs mean TR>0, 42-obs cadence freeze, T+1, 6bps, expanding vt12 cap5). ONLY CHANGE: eval from 1990 (no 2007 truncation; DGS2 1976+, 378d warmup).")
save_sleeve(br_sc,f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
"E1 de-truncated brwt_spread_rev15: identical frozen construction (Brent-WTI log-spread z15 mean-reversion +-1.5, T+1, 6bps half-turn, expanding vt10 min60 cap3). ONLY CHANGE: eval from brent data floor 2000-01 (no 2008 truncation; wti_full 1986+ aligned).")
