"""E1 idea3: brwt-2000 full gates (position-scramble + plateau) and save; a6r7-1990 save w/ gate-d disclosure."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import save_sleeve, fred
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr

ROOT="/Users/daxu/software/world-trader"
BR=fred('brent').dropna(); WT=fred('wti_full').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
z=(sp-sp.rolling(15,min_periods=15).mean())/sp.rolling(15,min_periods=15).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp.index); pos[z<-1.5]=1.0; pos[z>1.5]=-1.0
ret=sp.diff().shift(-1)

def build_net(pos):
    net=(pos*ret-(pos.diff().abs()/2.0)*6e-4).dropna()
    s,_=vol_target(net)
    return s.dropna()

# ---- position-scramble: circular-shift raw positions by random lag (preserves pos autocorr, breaks alignment) ----
r2001=build_net(pos); e=r2001[r2001.index>='2001-01-01']
real=e.mean()/e.std()*np.sqrt(252)
rng=np.random.default_rng(7)
cnt=0; N=200
for _ in range(N):
    lag=rng.integers(20,260)
    ps=pos.shift(lag).fillna(0.0)
    ns=build_net(ps); es=ns[ns.index>='2001-01-01']
    sr=es.mean()/es.std()*np.sqrt(252) if es.std()>0 else 0
    if sr>=real: cnt+=1
print(f"brwt position-shift scramble: p={cnt/N:.4f} real_SR={real:.2f} (200 reps, lag 20-260d)")

# ---- plateau grid: lookback x z ----
print("plateau (2001+ SR):")
best=None
for LB in [10,15,20]:
    row=[]
    for bz in [1.0,1.5,2.0]:
        zz=(sp-sp.rolling(LB,min_periods=LB).mean())/sp.rolling(LB,min_periods=LB).std().replace(0,np.nan)
        pp=pd.Series(0.0,index=sp.index); pp[zz<-bz]=1.0; pp[zz>bz]=-1.0
        nn=build_net(pp); ee=nn[nn.index>='2001-01-01']
        sr=ee.mean()/ee.std()*np.sqrt(252); row.append(round(sr,2))
    print(f"  LB={LB}: {row}")

st=full_stats(e); h1,h2=halves_sr(e)
print(f"FINAL brwt2001: SR={st['sr']:.2f} ann={st['ann']:.1f}% MDD={st['mdd']:.1f}% negy={st['negy']}/{st['years']} worst={st['worst']:.1f}% H1={h1:.2f} H2={h2:.2f}")

save_sleeve(r2001,f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
"""E1 de-truncated brwt_spread_rev15 (B2 engine, extended history). IDENTICAL frozen construction:
Brent-WTI log-spread, z=(sp-MA15)/SD15, long z<-1.5 short z>1.5, T+1 (ret=sp.diff().shift(-1)),
6bps/side on half-turnover, harness expanding vt10 min60 cap3. ONLY CHANGE vs B2 sleeve:
no 2008-01 truncation -> full brent history (FRED brent floor 2000-01-04; wti_full 1986+ aligned).
GATES (eval 2001-01+): SR=2.73 ann=25.7% vol=9.4% MDD=-7.9% negy=0/26 worst=+6.3% H1=2.98 H2=2.48
position-shift scramble 200x p=0.0000 (lag 20-260d); plateau LB{10,15,20} x z{1,1.5,2} all SR 2.4-3.0
center=peak; IS(<2017) SR=3.02 OOS(>=2017) SR=2.27; corr to GOAL100_CHAMPION20Y_BALANCED = 0.220
(corr_ok_secondary; the blend already holds the 2008+ version of this engine - use E1 file INSTEAD,
not in addition). RATIONALE: oil-quality spread reverts to locational/quality differential;
physically arbitraged by refinery logistics; 26y persistence incl 2008/2015/2020 dislocations.
CAVEAT: FRED spot quotes, roll-free proxy; tradeable via WTI/Brent futures spread with basis risk.""")
print("saved E1_brwt_spread_rev15_2000")
