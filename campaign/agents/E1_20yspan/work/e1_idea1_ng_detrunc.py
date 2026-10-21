"""E1 idea1: de-truncated C5 natgas weekday sleeves from raw DHHNGSP (1997-01+), warmup only.
Same frozen params as saved C5 sleeves (k=2.5, weekdays Wed/Thu short, Fri long; summer Apr-Oct for sum variant).
Gates on 1998-01..2026-08 (charter). corr vs current blend GOAL100_CHAMPION20Y_BALANCED."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import save_sleeve
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval

COST = 6e-4
D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
MONTHS=list(range(4,11))
BLEND = pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_CHAMPION20Y_BALANCED_daily.csv',
                    index_col=0, parse_dates=True).iloc[:,0]

def run(summer=False, k=2.5):
    s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
    s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
    lr=np.log(s).diff(); idx=lr.index
    pos=pd.Series(0.0,index=idx)
    pos[idx.dayofweek==2]=-1.0; pos[idx.dayofweek==3]=-1.0; pos[idx.dayofweek==4]=1.0
    if summer: pos[~idx.month.isin(MONTHS)]=0.0
    thr=lr.rolling(90).std().shift(1)*k
    pos=pos.mask(lr.abs()>thr,0.0)
    gr=pos*lr.shift(-1)
    turn=pos.diff().abs(); turn.iloc[0]=abs(pos.iloc[0])
    net=(gr-turn*COST).dropna()          # NO truncation: warmup = 90d sigma + 60d vol target only
    scaled,_=vol_target(net)
    return scaled.dropna()

def wd_scramble_pval(net, n=200, seed=1):
    """weekday-map scramble: shuffle the day-of-week -> position mapping, keep calendar"""
    s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
    s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
    lr=np.log(s).diff().dropna()
    rng=np.random.default_rng(seed)
    real=net.mean()/net.std()*np.sqrt(252)
    cnt=0
    for _ in range(n):
        dws=list(range(5)); rng.shuffle(dws)
        pos=pd.Series(0.0,index=lr.index)
        pos[lr.index.dayofweek==dws[2]]=-1.0; pos[lr.index.dayofweek==dws[3]]=-1.0; pos[lr.index.dayofweek==dws[4]]=1.0
        gr=pos*lr.shift(-1); turn=pos.diff().abs().fillna(0)
        n2=(gr-turn*COST).dropna()
        n2,_=vol_target(n2); n2=n2.dropna()
        n2=n2.reindex(net.index).fillna(0)
        sr=n2.mean()/n2.std()*np.sqrt(252) if n2.std()>0 else 0
        if sr>=real: cnt+=1
    return cnt/n

def report(name, r, eval_start='1998-01-01'):
    e=r[r.index>=eval_start]
    st=full_stats(e); h1,h2=halves_sr(e)
    pv,real=scramble_pval(e,200)
    wp=wd_scramble_pval(e.reindex(r.index).dropna())
    c=np.corrcoef(e.align(BLEND,join='inner')[0], e.align(BLEND,join='inner')[1])[0,1]
    # plateau: k grid on eval window
    ks=[1.5,2.0,2.5,3.0,3.5]; srs=[]
    for kk in ks:
        rr=run(summer=name.endswith('sum'),k=kk); ee=rr[rr.index>=eval_start]
        srs.append(round(ee.mean()/ee.std()*np.sqrt(252),2))
    print(f"== {name} (eval {eval_start}..) ==")
    print(f" span {e.index.min().date()}..{e.index.max().date()} n={len(e)}")
    print(f" SR={st['sr']:.2f} ann={st['ann']:.1f}% vol={st['vol']:.1f}% MDD={st['mdd']:.1f}% negy={st['negy']}/{st['years']} worst={st['worst']:.1f}%")
    print(f" H1={h1:.2f} H2={h2:.2f} scramble_p={pv:.4f} wd_scramble_p={wp:.4f} corr_blend={c:.3f}")
    print(f" plateau k{ks} -> {srs}  yearly={st['yearly']}")
    pre=e[e.index<'2017-01-01']; post=e[e.index>='2017-01-01']
    print(f" IS(<2017) SR={pre.mean()/pre.std()*np.sqrt(252):.2f} ann={pre.mean()*252*100:.1f}%  OOS SR={post.mean()/post.std()*np.sqrt(252):.2f} ann={post.mean()*252*100:.1f}%")
    return st,h1,h2,pv,wp,c,srs

r1=run(summer=False); r2=run(summer=True)
report('E1_C5ng_weekday_prem_1997', r1)
report('E1_C5ng_summer_weekday_1997', r2)
save_sleeve(r1,'/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv',
"""E1 de-truncated C5_ng_weekday_prem: identical frozen signal/params as C5_newdata saved sleeve
(Wed/Thu short, Fri long Henry Hub weekday premium; calm filter |lr|>2.5x trailing 90d sigma, info<=t;
T+1, 6bps/side, harness expanding vt10 min60 cap3). ONLY CHANGE: no 2008 truncation - full DHHNGSP
history 1997-01+ (90d sigma warmup -> first rows 1997-04). Charter eval window 1998-01+.""")
save_sleeve(r2,'/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv',
"""E1 de-truncated C5_ng_summer_weekday: identical frozen signal/params as C5_newdata saved sleeve
(Apr-Oct only; Wed/Thu short, Fri long; calm filter; T+1; 6bps; vt10 cap3). ONLY CHANGE: no 2008
truncation - full DHHNGSP 1997-01+. Charter eval window 1998-01+.""")
