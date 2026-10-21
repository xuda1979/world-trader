"""Idea 1 closure: 12-1 skip momentum, vol-adjusted mom rank, long-only. Idea 2: mom-accel CARDS."""
import sys; sys.path.insert(0,'.')
import lib48, numpy as pd, numpy as np, pandas as pd
R=lib48.load48()
champ=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]

def run(tag,sig,vt=0.10,cap=3.0):
    sc=lib48.vt_scale(sig,R,vt=vt,cap=cap)
    net,W=lib48.net_of_book48(sig,R,w_scale=sc)
    net=net[net.index>='2008-01-01'].dropna()
    st=lib48.full_stats(net); h1,h2=lib48.halves_sr(net); fg=lib48.flatten_gates(net)
    cv,_=lib48.corr_to(net,champ)
    turn=float(W.diff().abs().fillna(0.0).sum(axis=1).mean()*252)
    print(f"{tag:22s} SR {st['sr']:+.3f} ann {st['ann_geo']*100:+6.1f}% MDD {st['mdd']*100:5.1f}% H1 {h1:+.2f} H2 {h2:+.2f} ac1 {fg['ac1']:.3f} corrV3 {cv:+.3f} turn {turn:.1f}")
    return net

def rankbook(score,K,long_only=False):
    rk=score.rank(axis=1,ascending=False)
    sig=pd.DataFrame(0.0,index=R.index,columns=R.columns)
    if long_only:
        sig[rk<=K]=1.0/K
    else:
        sig[rk<=K]=1.0/K; sig[rk>48-K]=-1.0/K
    return sig

# 1b-i: 12-1 skip momentum
m252=R.rolling(252).mean(); m21=R.rolling(21).mean()
s121=m252.shift(21)-m21.shift(21)
for K in [3,6,12]: run(f"12-1 K{K}",rankbook(s121,K))
# 1b-ii: vol-adjusted mom63
vol=R.rolling(63).std()
run("sharpe63 K6",rankbook(R.rolling(63).mean()/vol,6))
run("sharpe252 K6",rankbook(R.rolling(252).mean()/R.rolling(252).std(),6))
# 1b-iii: long-only
for K in [6,12]: run(f"longonly 12-1 K{K}",rankbook(s121,K,True))
# IDEA 2: momentum acceleration (CARDS hybrid: mom63 minus own 20d-lagged mom63)
acc=R.rolling(63).mean()-R.rolling(63).mean().shift(20)
for K in [3,6,12]: run(f"accel K{K}",rankbook(acc,K))
# IDEA 2b: pure TS: long industry if own mom63>0 else short (all 48, 1/48 each)
tsig=pd.DataFrame(np.sign(R.rolling(63).mean()).values,index=R.index,columns=R.columns)/48
run("TS sign63 all48",tsig)
