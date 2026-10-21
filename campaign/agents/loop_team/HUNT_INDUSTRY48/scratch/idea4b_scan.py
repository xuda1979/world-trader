"""Idea 4b-d continued (vectorized, no rolling-apply): def-vs-cyc ratio, vol-filtered mom, RlEst"""
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
    print(f"{tag:24s} SR {st['sr']:+.3f} ann {st['ann_geo']*100:+6.1f}% MDD {st['mdd']*100:5.1f}% H1 {h1:+.2f} H2 {h2:+.2f} ac1 {fg['ac1']:.3f} corrV3 {cv:+.3f} turn {turn:.0f}",flush=True)
    return net
defen=['Food','Hshld','MedEq','Drugs','Util','Telcm','Insur']
cyc=['Steel','Chems','Mach','Trans','BldMt','Cnstr','Autos','Aero']
ratio=(R[defen].mean(axis=1)/R[cyc].mean(axis=1))
trend=ratio.rolling(63).mean()
sgn=np.sign(trend-trend.shift(21))
sig=pd.DataFrame(0.0,index=R.index,columns=R.columns)
for c in defen: sig[c]=sgn/len(defen)
for c in cyc: sig[c]=-sgn/len(cyc)
run("def-vs-cyc ratio63 L/S",sig)
lo=pd.DataFrame(0.0,index=R.index,columns=R.columns)
w_=(trend>trend.shift(21))/len(defen)
for c in defen: lo[c]=w_
run("def longonly ratio63",lo)
vol=R.rolling(21).std(); med=vol.median(axis=1)
rk=R.rolling(126).mean().rank(axis=1,ascending=False)
vok=vol.le(med*2,axis=0)
sig2=pd.DataFrame(0.0,index=R.index,columns=R.columns); sig2[(rk<=3)&vok]=1/3
run("mom126 top3 volfilt L-only",sig2)
# 4e: industry PAIR carries (idle spreads): RlEst-Util spread mean-revert; Telcm-Comps
pairs=[('RlEst','Util'),('Telcm','Comps'),('Meals','Rtail'),('Banks','Insur')]
for a,b in pairs:
    sp=R[a].rolling(63).mean()-R[b].rolling(63).mean()
    z=(sp-sp.expanding(252).mean())/sp.expanding(252).std()
    sig3=pd.DataFrame(0.0,index=R.index,columns=R.columns)
    sig3[a]=np.where(z>1,-1/2,np.where(z<-1,1/2,0))
    sig3[b]=np.where(z>1,1/2,np.where(z<-1,-1/2,0))
    run(f"pair {a}-{b} z63",sig3)
