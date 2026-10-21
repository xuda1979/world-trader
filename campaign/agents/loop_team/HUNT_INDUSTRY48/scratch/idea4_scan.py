"""Idea 4 variants: industry CARRY proxies (idle KF columns): RlEst vs market gap; Mom/Val spread."""
import sys; sys.path.insert(0,'.')
import lib48, numpy as np, pandas as pd
R=lib48.load48()
champ=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
def run(tag,sig,vt=0.10,cap=3.0):
    sc=lib48.vt_scale(sig,R,vt=vt,cap=cap)
    net,W=lib48.net_of_book48(sig,R,w_scale=sc)
    net=net[net.index>='2008-01-01'].dropna()
    st=lib48.full_stats(net); h1,h2=lib48.halves_sr(net); fg=lib48.flatten_gates(net)
    cv,_=lib48.corr_to(net,champ)
    turn=float(W.diff().abs().fillna(0.0).sum(axis=1).mean()*252)
    print(f"{tag:24s} SR {st['sr']:+.3f} ann {st['ann_geo']*100:+6.1f}% MDD {st['mdd']*100:5.1f}% H1 {h1:+.2f} H2 {h2:+.2f} ac1 {fg['ac1']:.3f} corrV3 {cv:+.3f} turn {turn:.0f}")
    return net
# 4a: own-lb autocorr (sticky winner persistence)
for lb in [21,63]:
    c=pd.DataFrame(index=R.index,columns=R.columns,dtype=float)
    a=R.rolling(lb).apply(lambda x: x.autocorr(1),raw=False)
    run(f"ac1 lb{lb} K12 L/S",a.pipe(lambda s: pd.DataFrame(np.where(s.rank(axis=1,ascending=False)<=12,-1/12,np.where(s.rank(axis=1,ascending=False)>36,1/12,0)),index=R.index,columns=R.columns)))
# 4b: defensive-vs-cyclical ratio momentum: Util+Hlth+Cons? vs cyc composite (ratio trend)
defen=[c for c in R.columns if c in ['Util','Food','Hshld','MedEq','Drugs','Telcm','Insur']]
print('defensive:',defen)
cyc=['Steel','Chems','Mach','Trans','BldMt','Cnstr','Autos','Aero']
ratio=(R[defen].mean(axis=1)/R[cyc].mean(axis=1))
# long def when ratio 63d trend up (flight to safety persistent)
trend=ratio.rolling(63).mean()
sig=pd.DataFrame(0.0,index=R.index,columns=R.columns)
sig[defen]=np.sign(trend-trend.shift(21)).values[:,None]/len(defen)
sig[cyc]=-np.sign(trend-trend.shift(21)).values[:,None]/len(cyc)
run("def-vs-cyc ratio63 L/S",sig)
# 4c: defensive long-only gated by ratio trend
run("def longonly ratio63",pd.DataFrame(np.where(trend>trend.shift(21),1/len(defen),0),index=R.index,columns=defen).reindex(columns=R.columns).fillna(0))
# 4d: cross-indust VALIDATION: mom126 top3 with own 21d VOL filter (skip if own vol>2x cs median)
vol=R.rolling(21).std(); med=vol.median(axis=1)
rk=mom126=R.rolling(126).mean().rank(axis=1,ascending=False)
vok=vol.le(med*2,axis=0)
sig=pd.DataFrame(0.0,index=R.index,columns=R.columns); sig[(rk<=3)&vok]=1/3
run("mom126 top3 vol-filtered L-only",sig)
