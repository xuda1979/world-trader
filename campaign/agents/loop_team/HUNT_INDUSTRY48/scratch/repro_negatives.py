"""HUNT_INDUSTRY48 FINAL REPRO (iter6) — all negative families, fixed lib48 (T4-clean data).
Run: python3 repro_negatives.py   (~2 min)
Engine guarantees (tdd_gates.py all GREEN): T1 leak=0 | T2 cost recon=0 | T3 poslag non-degenerate
| T4 no missing-codes (exact -99.99/-999 masked; 1929-style crashes preserved)."""
import sys; sys.path.insert(0,'.')
import lib48, numpy as np, pandas as pd
R=lib48.load48(); R08=R[R.index>='2008-01-01']
champ=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
dual=pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv',index_col=0,parse_dates=True).iloc[:,0]
def ev(tag,sig):
    sig=sig.reindex(R08.index).fillna(0.0)   # align signal to eval window BEFORE vt (no union zeros)
    sc=lib48.vt_scale(sig,R08).fillna(1.0)   # first 60d: scale=1 (conservative, campaign std)
    net,_=lib48.net_of_book48(sig,R08,w_scale=sc)
    net=net.reindex(sig.index.intersection(R08.index)).dropna()
    net=net[net.index>='2008-01-01']
    st=lib48.full_stats(net); h1,h2=lib48.halves_sr(net); fg=lib48.flatten_gates(net)
    cv,_=lib48.corr_to(net,champ); cd,_=lib48.corr_to(net,dual)
    W=(sig.mul(sc.shift(1),axis=0)).shift(1).fillna(0.0)
    turn=float(W.diff().abs().fillna(0.0).sum(axis=1).mean()*252)
    print(f"{tag:24s} SR {st['sr']:+.3f} ann {st['ann_geo']*100:+6.2f}% MDD {st['mdd']*100:6.1f}% H1 {h1:+.2f} H2 {h2:+.2f} ac1 {fg['ac1']:.3f} corrV3 {cv:+.3f} corrDm {cd:+.3f} turn/yr {turn:.0f}",flush=True)
    return net
def rankbook(score,K):
    rk=score.rank(axis=1,ascending=False)
    s=pd.DataFrame(0.0,index=score.index,columns=score.columns)
    s[rk<=K]=1.0/K; s[rk>48-K]=-1.0/K
    return s
print('== F1 cross-industry relative momentum (48 VW, T+1, vt10, 6.4bps both sides) ==')
for lb in [21,63,126]:
    for K in [3,6,12]: ev(f"mom lb{lb} K{K}",rankbook(R.rolling(lb).mean(),K))
s121=R.rolling(252).mean().shift(21)-R.rolling(21).mean().shift(21)
for K in [3,6,12]: ev(f"12-1 K{K}",rankbook(s121,K))
lo=pd.DataFrame(0.0,index=R.index,columns=R.columns); lo[s121.rank(axis=1,ascending=False)<=12]=1/12
ev("longonly 12-1 K12",lo)
ev("sharpe63 K6",rankbook(R.rolling(63).mean()/R.rolling(63).std(),6))
print('== F2 momentum-acceleration CARDS ==')
ev("accel K6",rankbook(R.rolling(63).mean()-R.rolling(63).mean().shift(20),6))
print('== F3 leader/breadth gates on laggard-reversal book ==')
mom63=R.rolling(63).mean()
rk=mom63.rank(axis=1,ascending=False)
lagrev=pd.DataFrame(0.0,index=R.index,columns=R.columns); lagrev[rk<=12]=-1/12; lagrev[rk>36]=1/12
breadth=(R>R.rolling(63).mean()).sum(axis=1)/48
ev("lagRev12 x breadth>0.4",lagrev.mul((breadth>0.4).astype(float),axis=0))
cyc=['Steel','Chems','Mach','Trans','BldMt','Cnstr','Autos','Aero']
lead=R[cyc].mean(axis=1).rolling(21).mean()
z=(lead-lead.expanding(252).mean())/lead.expanding(252).std()
ev("lagRev12 x lead21z<0",lagrev.mul((z<0).astype(float),axis=0))
ev("mom12 x breadth>0.4",rankbook(mom63,12).mul((breadth>0.4).astype(float),axis=0))
print('== F4 carry-proxy / pairs ==')
defen=['Food','Hshld','MedEq','Drugs','Util','Telcm','Insur']
trend=(R[defen].mean(axis=1)/R[cyc].mean(axis=1)).rolling(63).mean()
sgn=np.sign(trend-trend.shift(21))
sd=pd.DataFrame(0.0,index=R.index,columns=R.columns)
for c in defen: sd[c]=sgn/len(defen)
for c in cyc: sd[c]=-sgn/len(cyc)
ev("def-vs-cyc ratio63 L/S",sd)
for a,b in [('RlEst','Util'),('Banks','Insur')]:
    sp=R[a].rolling(63).mean()-R[b].rolling(63).mean()
    zz=(sp-sp.expanding(252).mean())/sp.expanding(252).std()
    sp2=pd.DataFrame(0.0,index=R.index,columns=R.columns)
    sp2[a]=np.where(zz>1,-0.5,np.where(zz<-1,0.5,0.0))
    sp2[b]=np.where(zz>1,0.5,np.where(zz<-1,-0.5,0.0))
    ev(f"pair {a}-{b} z63",sp2)
print('== F5 1-day industry reversal (gross-positive, cost-dead) ==')
K=12
rk1=R.shift(1).rank(axis=1)
rev=pd.DataFrame(0.0,index=R.index,columns=R.columns); rev[rk1<=K]=1.0/K; rev[rk1>48-K]=-1.0/K
sc=lib48.vt_scale(rev,R08)
W=rev.mul(sc.shift(1),axis=0).shift(1).reindex(R08.index).fillna(0.0)
gross=(W*R08).sum(axis=1); cost=W.diff().abs().fillna(0).sum(axis=1)*6.4e-4
print(f"REV1d K12 vt'd GROSS {float(gross.mean()/gross.std()*np.sqrt(252)):+.3f} SR | gross {float(gross.abs().mean())*1e4:.1f}bp/day vs cost {float(cost.mean())*1e4:.1f}bp/day (unvt gross SR +0.355, cost/gross 1.617)")
net=(gross-cost).dropna()
print(f"REV1d K12 NET SR {float(net.mean()/net.std()*np.sqrt(252)):+.3f}")
for lb in [2,3,5]:
    rkl=R.shift(lb).rank(axis=1)
    s=pd.DataFrame(0.0,index=R.index,columns=R.columns); s[rkl<=K]=1.0/K; s[rkl>48-K]=-1.0/K
    g=(s.reindex(R08.index).fillna(0.0).shift(1)*R08).sum(axis=1)
    print(f"REV lb{lb} GROSS SR {float(g.mean()/g.std()*np.sqrt(252)):+.3f}")
mask=(R.index.dayofweek==4)
f=rev[mask].reindex(R.index).ffill().fillna(0.0)
Wf=f.mul(sc.shift(1),axis=0).shift(1).reindex(R08.index).fillna(0.0)
gf=(Wf*R08).sum(axis=1); cf=Wf.diff().abs().fillna(0).sum(axis=1)*6.4e-4
nf=(gf-cf).dropna()
print(f"REV1d WEEKLY K12 NET SR {float(nf.mean()/nf.std()*np.sqrt(252)):+.3f} (turn {float(Wf.diff().abs().sum(axis=1).mean()*252):.0f}/yr)")
