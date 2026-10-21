"""Idea 1 flip: short-term industry REVERSAL. Idea 3: leader/breadth timing of laggards."""
import sys; sys.path.insert(0,'.')
import lib48, numpy as np, pandas as pd
R=lib48.load48()
champ=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
def run(tag,sig,vt=0.10,cap=3.0,quiet=False):
    sc=lib48.vt_scale(sig,R,vt=vt,cap=cap)
    net,W=lib48.net_of_book48(sig,R,w_scale=sc)
    net=net[net.index>='2008-01-01'].dropna()
    st=lib48.full_stats(net); h1,h2=lib48.halves_sr(net); fg=lib48.flatten_gates(net)
    cv,_=lib48.corr_to(net,champ)
    turn=float(W.diff().abs().fillna(0.0).sum(axis=1).mean()*252)
    print(f"{tag:24s} SR {st['sr']:+.3f} ann {st['ann_geo']*100:+6.1f}% MDD {st['mdd']*100:5.1f}% H1 {h1:+.2f} H2 {h2:+.2f} ac1 {fg['ac1']:.3f} corrV3 {cv:+.3f} turn {turn:.0f}")
    return net
def rankrev(score,K):
    rk=score.rank(axis=1,ascending=False)
    sig=pd.DataFrame(0.0,index=R.index,columns=R.columns)
    sig[rk<=K]=-1.0/K; sig[rk>48-K]=+1.0/K   # losers long, winners short
    return sig
# short-term reversal
for lb in [3,5,10,21]:
    for K in [6,12]:
        run(f"REV lb{lb} K{K}",rankrev(R.rolling(lb).mean(),K))
# breadth timing: frac of industries above own 63d MA -> time the 63d-reversal book? and a
# long-breadth gate on a laggard book (long bottom-K by mom63 gated by breadth>0.5)
mom63=R.rolling(63).mean()
breadth=(R>R.rolling(63).mean()).sum(axis=1)/48
lag_rev=rankrev(mom63,12)
for th in [0.4,0.5,0.6]:
    g=(breadth.shift(0)>th).astype(float)
    run(f"lagRev12 x breadth>{th}",lag_rev.mul(g,axis=0))
# leader timing: cyclical composite (Steel,Chems,Mach,Trans) 21d mean <0 -> hold laggards else cash
cyc=R[['Steel','Chems','Mach','Trans']].mean(axis=1).rolling(21).mean()
lag_g=rankrev(mom63,12).mul((cyc<0).astype(float),axis=0)
run("lagRev12 x cyc<0",lag_g)
lead=R[['Steel','Chems','Mach','Trans']].rolling(21).mean().mean(axis=1)
lag_bm=rankrev(mom63,12)
run("lagRev12 x lead21z",lag_bm.mul(((lead-lead.expanding(252).mean())/lead.expanding(252).std()<0).astype(float),axis=0))
