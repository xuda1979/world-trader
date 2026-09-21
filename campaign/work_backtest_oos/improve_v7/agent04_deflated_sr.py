"""A04: deflated-SR across the 166->20 selection path (E[max SR] under N trials)."""
import numpy as np, pandas as pd, os, sys
from scipy import stats
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
osdf=D['osdf']; sl=D['sleeves']; wt=D['wt']
# pool monthly OOS SRs
pool=pd.read_csv(os.path.join(OD,"passing_honest_oos>0.4.csv"))
import re
for pat in [r"MHX|HT_TAIL", r"_on_CHAMP|overlay"]:
    pool=pool[~pool['strategy'].str.contains(re.compile(pat,re.I))]
def vt_bad(rel):
    m=os.path.splitext(os.path.join("campaign",rel))[0]+".csv.meta"
    if not os.path.exists(m): return False
    t=open(m).read()
    return ('FAILED_NO_PROMOTION' in t) or ('DEAD_NOT_PROMOTED' in t)
pool=pool[~pool['strategy'].apply(vt_bad)]
srs=[]
for _,row in pool.iterrows():
    try:
        s=osdf.get(row['strategy'])
        if s is None:
            d=pd.read_csv(os.path.join("/Users/daxu/software/world-trader/campaign",row['strategy']),index_col=0)
            d.index=pd.to_datetime(d.index)
            c="ret" if "ret" in d.columns else d.columns[0]
            m=(1+d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()).resample("ME").prod()-1
            s=m[m.index>=pd.Timestamp("2017-01-01")]
        s=s.dropna(); s=s[s.abs()<0.5]
        if len(s)>24: srs.append(s.mean()/s.std()*np.sqrt(12))
    except: pass
srs=np.array(srs); N=len(srs)
T=117; sr_hat=sr(osdf[sl].dot(wt))
sk=stats.skew((osdf[sl].dot(wt)).dropna()); ku=stats.kurtosis((osdf[sl].dot(wt)).dropna())
# E[max SR] under N independent trials with unit variance, via extreme value approx
g1=0.5772156649
emax=np.sqrt(2*np.log(N))- (np.log(np.log(N))+g1)/(2*np.sqrt(2*np.log(N)))
# variance of SR estimates ~ (1 - sk*sr + (ku-1)/4 sr^2)/(T-1); iterate once
var_sr=(1-sk*sr_hat+(ku-1)/4*sr_hat**2)/(T-1)
emax_s=emax*np.sqrt(var_sr)
dsr=(sr_hat-emax_s)*np.sqrt(T-1)/np.sqrt(1-sk*sr_hat+(ku-1)/4*sr_hat**2)
p_dsr=stats.norm.cdf(dsr)
res=dict(n_pool=N,observed_monthly_SR=float(sr_hat),expected_max_monthly_SR=float(emax_s),
         deflated_SR=float(dsr),PSR_deflated=float(p_dsr))
print(f"pool OOS SRs: N={N}, max={srs.max():.2f}")
print(f"observed V7 monthly SR = {sr_hat:.3f}")
print(f"E[max SR under {N} trials] = {emax_s:.3f}")
print(f"Deflated SR (vs selection max) = {dsr:.3f}  PSR = {p_dsr:.4f}")
print("VERDICT:", "PASS — edge survives selection discount" if p_dsr>0.95 else ("MARGINAL" if p_dsr>0.5 else "FAIL"))
save("agent04_deflated_sr",res)
