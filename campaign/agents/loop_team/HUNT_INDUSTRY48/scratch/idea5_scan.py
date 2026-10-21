"""DEEP DELIVERY CANDIDATES: high-turnover daily industry engines
 A: 1d industry reversal (unconditional)   B: vol-scaling regimes
 C: xsec RESIDUAL rev vs mkt (betas exp252) D: best-of + gap filter"""
import sys; sys.path.insert(0,'.')
import lib48, numpy as np, pandas as pd
R=lib48.load48()
champ=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
def run(tag,sig,vt=0.10,cap=3.0,stats=False):
    sc=lib48.vt_scale(sig,R,vt=vt,cap=cap)
    net,W=lib48.net_of_book48(sig,R,w_scale=sc)
    net=net[net.index>='2008-01-01'].dropna()
    st=lib48.full_stats(net); h1,h2=lib48.halves_sr(net); fg=lib48.flatten_gates(net)
    cv,_=lib48.corr_to(net,champ)
    yr=net.groupby(net.index.year).apply(lambda x:(1+x).prod()-1)
    turn=float(W.diff().abs().fillna(0.0).sum(axis=1).mean()*252)
    print(f"{tag:26s} SR {st['sr']:+.3f} ann {st['ann_geo']*100:+6.1f}% MDD {st['mdd']*100:6.1f}% H1 {h1:+.2f} H2 {h2:+.2f} ac1 {fg['ac1']:.3f} uniq {fg['uniqR']:.2f} corrV3 {cv:+.3f} turn {turn:.0f} negy {st['negy']} worst {st['worst']*100:+.1f}%",flush=True)
    return net
# A: 1d reversal across 48, EW long losers short winners scaled by 1/vol
for K in [12,24]:
    lag1=R.shift(1)
    rk=lag1.rank(axis=1)  # smallest return = rank 1 = biggest loser
    sig=pd.DataFrame(0.0,index=R.index,columns=R.columns)
    sig[rk<=K]=+1.0/K; sig[rk>48-K]=-1.0/K
    run(f"REV1d EW K{K}",sig)
# B: vol-adjusted 1d reversal: weight = -(r_t)/vol^2 style (LS-cap via rank top/bottom 12)
vol21=R.rolling(21).std()
z1=R.shift(1)/vol21.shift(1)
rkz=z1.rank(axis=1)
for K in [12,24]:
    sig=pd.DataFrame(0.0,index=R.index,columns=R.columns)
    sig[rkz<=K]=+1.0/K; sig[rkz>48-K]=-1.0/K
    run(f"REV1d volz K{K}",sig)
# C: xsec residual reversal: r_resid = r - beta*mkt (beta exp252)
mkt=R.mean(axis=1)
beta=(R.rolling(252).cov(mkt)/mkt.rolling(252).var())
beta=beta.replace([np.inf,-np.inf],np.nan).ffill()
resid=R-beta.mul(mkt,axis=0)
zres=(resid.shift(1)/vol21.shift(1))
rkres=zres.rank(axis=1)
for K in [12,24]:
    sig=pd.DataFrame(0.0,index=R.index,columns=R.columns)
    sig[rkres<=K]=+1.0/K; sig[rkres>48-K]=-1.0/K
    run(f"RESREV1d K{K}",sig)
