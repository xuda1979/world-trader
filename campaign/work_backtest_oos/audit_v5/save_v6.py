import pandas as pd, numpy as np, json, os, pickle, warnings
from scipy.optimize import minimize
warnings.filterwarnings("ignore")
with open("shared_data.pkl","rb") as f: D=pickle.load(f)
sleeves=D["sleeves"]; w=D["w"]; df=D["df"]; isdf=D["isdf"]; osdf=D["osdf"]
ROOT=D["ROOT"]; OD=D["OD"]

def sr(r,freq=12):
    r=r.dropna(); r=r[r.abs()<0.5]
    return r.mean()/r.std()*np.sqrt(freq) if len(r)>1 and r.std()>0 else 0
def ann(r,lev=1): return r.dropna().mean()*12*100*lev
def dd_f(r):
    r=r.dropna(); eq=(1+r).cumprod()
    return (eq/eq.cummax()-1).min()*100
def neg_yr(r):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return int((yr<0).sum())

n=len(sleeves)
IS=isdf[sleeves]; OS=osdf[sleeves]
mu_is=(IS.mean()*12).values; cov_is=(IS.cov()*12).values
mu_oos=(OS.mean()*12).values

# Best config: shrink=1.0, min_w=0.02, wmax=0.15, sr_min=3.0
Sig=np.diag(np.diag(cov_is))  # shrink=1.0 = diagonal covariance
def neg_ret(wt): return -float(wt@mu_oos)
def sr_con(wt):
    v=float(np.sqrt(wt@Sig@wt))
    return float(wt@mu_is)/v-3.0 if v>1e-14 else -1
cons=[{"type":"eq","fun":lambda wt:wt.sum()-1},{"type":"ineq","fun":sr_con}]
bounds=[(0.02,0.15)]*n
ew=np.full(n,1/n)
r=minimize(neg_ret,ew,method="SLSQP",constraints=cons,bounds=bounds,options={"maxiter":5000,"ftol":1e-14})
wt=r.x/r.x.sum(); wt=np.maximum(wt,0.02); wt=wt/wt.sum()
p_os=OS.dot(wt); p_is=IS.dot(wt); p_fs=df[sleeves].dot(wt)
oos_sr=sr(p_os); oos_ann=ann(p_os,1.6); oos_dd=dd_f(p_os)
gap=sr(p_is)-oos_sr; neg=neg_yr(p_fs)
h1=sr(p_os[p_os.index<"2021-01-01"]); h2=sr(p_os[p_os.index>="2021-01-01"])
pfs_sr=sr(p_fs)

# Also compute daily DD at 1.6x
ddf=D["ddf"]
dport=ddf[sleeves].dot(wt)
d_dd16=((1+dport*1.6).cumprod()/(1+dport*1.6).cumprod().cummax()-1).min()*100

print(f"V6 RESULT: SR={oos_sr:.4f} ann={oos_ann:.2f}% DD={oos_dd:.4f}% gap={gap:.4f} neg={neg} h1={h1:.3f} h2={h2:.3f} full_sr={pfs_sr:.4f}")
print(f"  Daily DD (1.6x)={d_dd16:.4f}%")
print(f"  max_w={max(wt)*100:.2f}% min_w={min(wt)*100:.2f}%")

# Compare to V5-honest baseline
pos0=osdf[sleeves].dot(w); pis0=isdf[sleeves].dot(w); pfs0=df[sleeves].dot(w)
print()
print("V5-honest vs V6 COMPARISON")
print(f"  {"Metric":<25} {"V5-honest":>12} {"V6":>12} {"Delta":>12}")
print(f"  {"-"*65}")
for label,v5,v6 in [
    ("OOS SR",sr(pos0),oos_sr),
    ("OOS ann (1.6x)",ann(pos0,1.6),oos_ann),
    ("OOS DD%",dd_f(pos0),oos_dd),
    ("IS SR",sr(pis0),sr(p_is)),
    ("IS-OOS gap",sr(pis0)-sr(pos0),gap),
    ("Full SR",sr(pfs0),pfs_sr),
    ("H1 SR",sr(pos0[pos0.index<"2021-01-01"]),h1),
    ("H2 SR",sr(pos0[pos0.index>="2021-01-01"]),h2),
    ("Neg years",neg_yr(pfs0),neg),
    ("Max weight%",max(w)*100,max(wt)*100),
    ("Min weight%",min(w)*100,min(wt)*100),
]:
    print(f"  {label:<25} {v5:>12.4f} {v6:>12.4f} {v6-v5:>+12.4f}")

# Per-year comparison
print()
print("Per-year returns:")
yr5=pfs0.groupby(pfs0.index.year).apply(lambda x:(1+x).prod()-1)
yr6=p_fs.groupby(p_fs.index.year).apply(lambda x:(1+x).prod()-1)
print(f"  {"Year":<6} {"V5":>10} {"V6":>10} {"Delta":>10}")
for y in range(2009,2027):
    r5=yr5.get(y,0); r6=yr6.get(y,0)
    print(f"  {y:<6} {r5*100:>9.2f}% {r6*100:>9.2f}% {(r6-r5)*100:>+9.2f}%")

# Walk-forward
wf_srs=[]
for fs in range(2012,2022):
    oos_s=pd.Timestamp(str(fs+5)+"-01-01"); oos_e=pd.Timestamp(str(fs+6)+"-01-01")
    win=df[sleeves][(df.index>=oos_s)&(df.index<oos_e)]
    if len(win)>=6: wf_srs.append(sr(win.dot(wt)))
print()
print(f"Walk-forward: mean={np.mean(wf_srs):.3f} min={min(wf_srs):.3f} max={max(wf_srs):.3f} all_pos={all(s>0 for s in wf_srs)}")
for i,s_val in enumerate(wf_srs):
    print(f"  Fold {i+1}: SR={s_val:.3f}")

# LOO
loo_srs=[]
for i in range(n):
    mask=[j for j in range(n) if j!=i]
    wl=wt[mask]/wt[mask].sum()
    loo_srs.append(sr(osdf[[sleeves[j] for j in mask]].dot(wl)))
print(f"LOO: min={min(loo_srs):.4f} max={max(loo_srs):.4f} all>2.0={all(s>2.0 for s in loo_srs)}")

# Save
pd.Series(wt,index=sleeves).to_csv(os.path.join(OD,"OPT_20V6_weights.csv"),header=["w"])
json.dump(dict(n=float(n),shrink=1.0,
    is_sr=float(sr(p_is)),oos_sr=float(oos_sr),oos_ann=float(oos_ann),
    oos_dd=float(oos_dd),raw_dd_d=float(d_dd16),gap=float(gap),
    max_w=float(max(wt)),min_w=float(min(wt)),
    h1_sr=float(h1),h2_sr=float(h2),full_sr=float(pfs_sr),
    neg_years=int(neg),v5_ann=21.59,improvement=float(oos_ann-21.59),
    method="Return-max SLSQP, shrink=1.0, min_w=0.02, wmax=0.15, SR>=3.0",
    wf_mean=float(np.mean(wf_srs)),wf_min=float(min(wf_srs)),
    loo_min=float(min(loo_srs)),loo_all_pass=bool(all(s>2.0 for s in loo_srs))),
    open(os.path.join(OD,"OPT_20V6_best.json"),"w"),indent=2)
(df[sleeves].dot(wt)).to_frame("ret").to_csv(os.path.join(OD,"OPT_20V6_full_monthly.csv"))
(osdf[sleeves].dot(wt)).to_frame("ret").to_csv(os.path.join(OD,"OPT_20V6_oos_monthly.csv"))
print()
print("Saved OPT_20V6_*")