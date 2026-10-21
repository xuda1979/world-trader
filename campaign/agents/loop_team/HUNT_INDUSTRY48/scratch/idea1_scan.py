"""Idea 1: cross-industry relative momentum among KF48 VW portfolios.
D_s(t) = +1/K on top-K by trailing mean ret (lb days), -1/K on bottom-K. T+1, vt10 expanding min60 cap3.
Costs 6.4bps x sum|dW| both sides + borrow 0.5%/yr shorts. Eval 2008+."""
import sys; sys.path.insert(0,'.')
import lib48, numpy as np, pandas as pd
R=lib48.load48(); R2008=R[R.index>='2008-01-01']
champ=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
dual=pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv',index_col=0,parse_dates=True).iloc[:,0]

def relmom(lb,K,vt=0.10,cap=3.0):
    mom=R.rolling(lb).mean()
    sig=pd.DataFrame(0.0,index=R.index,columns=R.columns)
    rk=mom.rank(axis=1,ascending=False)
    sig[rk<=K]=1.0/K; sig[rk>48-K]=-1.0/K
    sc=lib48.vt_scale(sig,R,vt=vt,cap=cap)
    net,W=lib48.net_of_book48(sig,R,w_scale=sc)
    return net[net.index>='2008-01-01'].dropna(), sig, sc

print('lb  K  SR     ann%   MDD%  H1    H2    ac1    uniqR  corrV3  corrDm  turn/yr')
res={}
for lb in [21,63,126]:
    for K in [3,6,12]:
        net,sig,sc=relmom(lb,K)
        st=lib48.full_stats(net); h1,h2=lib48.halves_sr(net); fg=lib48.flatten_gates(net)
        cv,_=lib48.corr_to(net,champ); cd,_=lib48.corr_to(net,dual)
        W=(sig.mul(sc.shift(1),axis=0)).shift(1)
        turn=float(W.diff().abs().fillna(0.0).sum(axis=1).mean()*252)
        res[(lb,K)]=(net,st)
        print(f"{lb:3d} {K:2d} {st['sr']:.3f} {st['ann_geo']*100:6.1f} {st['mdd']*100:6.1f} {h1:.2f} {h2:.2f} {fg['ac1']:.3f} {fg['uniqR']:.3f} {cv:+.3f} {cd:+.3f} {turn:6.1f}")
