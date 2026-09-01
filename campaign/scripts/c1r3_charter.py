"""C1 Round-3 repro (CHARTER_3.md). All 5 ideas tested; NONE passed gates.
Contract: T+1 via c1_lib.bt (pos decided on data<=t earns ret t+1), 6bps one-side turnover,
VT 10% expanding trailing min60 clip3, window 2008-09..2026-08. Gates: SR>=1, H1&H2>=0.5,
negy<=2, worst>-5%, scramble200 p>0.05, |corr|<0.15 vs COORD_FINAL.
Usage: python3 c1r3_charter.py   (prints the headline numbers from the round)
"""
import sys, numpy as np, pandas as pd, itertools, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import c1_lib as L

R = L.kf48().loc['1995':]
rb_d = pd.Series(True, index=R.index)
rb_w = pd.Series(R.index.dayofweek==4, index=R.index)
def ranks(sig): return sig.rank(axis=1, ascending=False).values
cntv = lambda sig: sig.notna().sum(axis=1).values
def topbot(sig,k,rb):
    rk=ranks(sig); c=cntv(sig)
    lng=pd.DataFrame((rk<=k)&(c>=2*k)[:,None],index=sig.index,columns=sig.columns)
    shrt=pd.DataFrame((rk>c[:,None]-k)&(c>=2*k)[:,None],index=sig.index,columns=sig.columns)
    pos=(lng.astype(float)-shrt.astype(float))/k
    return pos.where(rb,0.0).ffill().fillna(0.0)
def evaluate(pos,name):
    net,_,_=L.bt(pos,R); net=net.loc['2008-09-01':]; netv,_=L.vt(net)
    s=L.stats(netv); cb=L.corr_blend(netv)
    print(f"{name:28s} SR {s['sr']:5.2f} ann {s['ann']:6.1f}% mdd {s['mdd']:6.1f}% negy {s['negy']:2d} corrB {cb:+.3f}")
    return netv

print("IDEA1 mom-skip grid (36 cells) best cell:")
evaluate(topbot(R.shift(21).rolling(231).sum(),3,rb_d), "mom252-sk21 k3 daily")
print("\nIDEA2 dip-in-strength (all 24 cells NEGATIVE, e.g.):")
mom=R.rolling(252).sum(); rev=-R.rolling(10).sum()
sig=mom.where(rev>0)
evaluate(topbot(sig,6,rb_d), "dip252-rv10-cond k6 wk")
print("\nIDEA3 pair stat-arb: wf HL 5-60d, N20, ZW63, z-thresh: best variant (rev zth2.0 ZW21):")
# see inline round log; structure identical to scripts/c1_idea3456_spreads.py + this file
print("  (pair code above in LOG_3/FINDINGS; all cells SR -0.18..-0.86)")
print("\nIDEA4 vol-managed momentum (all 16 cells <=0.24), best:")
vol21=R.rolling(21).std(); rk=ranks(mom); c=cntv(mom)
lng=pd.DataFrame((rk<=6)&(c>=12)[:,None],index=R.index,columns=R.columns)
shrt=pd.DataFrame((rk>c[:,None]-6)&(c>=12)[:,None],index=R.index,columns=R.columns)
iv=(1.0/vol21).replace([np.inf,-np.inf],np.nan)
l2=((lng*iv).div((lng*iv).sum(axis=1),axis=0).fillna(0)-(shrt*iv).div((shrt*iv).sum(axis=1),axis=0).fillna(0)).where(rb_d,0.0).ffill().fillna(0.0)
evaluate(l2, "vm-mom252-k6-ind daily")
print("\nIDEA5 TOM seasonality: TOM-day EW SR 0.20, per-industry max|t|=3.05<4.0 Bonferroni; anti-TOM SR 0.61")
idx=R.index; is_tom=pd.Series(False,index=idx)
for i,dt in enumerate(idx):
    nxt=idx[idx>dt]; nxt=nxt[0] if len(nxt) else None
    is_tom[dt]=(dt.day<=3) or (nxt is not None and nxt.month!=dt.month)
pos=np.where((~is_tom).values.astype(float),1.0/48,0.0)
evaluate(pd.DataFrame(np.outer(pos,np.ones(48)),index=idx,columns=R.columns), "anti-TOM EW rest-of-month")
print("\nIDEA7 composite EW-of-3 best legs: SR 0.50 negy 7 corrB +0.215 -> FAIL (see FINDINGS)")
