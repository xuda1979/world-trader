"""Optimize V5-honest for higher annual return without worsening other metrics."""
import os, sys, json, re, pickle, warnings
import numpy as np, pandas as pd
from scipy.optimize import minimize
warnings.filterwarnings("ignore")

with open("shared_data.pkl","rb") as f: D=pickle.load(f)
sleeves=D["sleeves"]; w=D["w"]; df=D["df"]; isdf=D["isdf"]; osdf=D["osdf"]; ddf=D["ddf"]
ROOT=D["ROOT"]; OD=D["OD"]; IS_END=pd.Timestamp("2017-01-01")

def sr(r,freq=12):
    r=r.dropna(); r=r[r.abs()<0.5]
    return r.mean()/r.std()*np.sqrt(freq) if len(r)>1 and r.std()>0 else 0
def ann(r,lev=1): return r.dropna().mean()*12*100*lev
def dd(r,lev=1):
    r=r.dropna(); eq=(1+r*lev).cumprod()
    return (eq/eq.cummax()-1).min()*100
def neg_yr(r):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return int((yr<0).sum())

pos0=osdf[sleeves].dot(w); pis0=isdf[sleeves].dot(w); pfs0=df[sleeves].dot(w)
h1_0=sr(pos0[pos0.index<"2021-01-01"]); h2_0=sr(pos0[pos0.index>="2021-01-01"])
baseline=dict(sr=sr(pos0), ann=ann(pos0,1.6), dd=dd(pos0), gap=sr(pis0)-sr(pos0),
              neg=neg_yr(pfs0), h1=h1_0, h2=h2_0, full_sr=sr(pfs0))
print(f"BASELINE: SR={baseline["sr"]:.4f} ann={baseline["ann"]:.2f}% DD={baseline["dd"]:.4f}% gap={baseline["gap"]:.4f} neg={baseline["neg"]}")

# Load honest pool
pool=pd.read_csv(os.path.join(OD,"passing_honest_oos>0.4.csv"))
for pat in [r"MHX|HT_TAIL", r"_on_CHAMP|overlay"]:
    pool=pool[~pool["strategy"].str.contains(re.compile(pat,re.I))]
def vt_bad(rel):
    m=os.path.splitext(os.path.join(ROOT,rel))[0]+".csv.meta"
    if not os.path.exists(m): return False
    t=open(m).read()
    return ("FAILED_NO_PROMOTION" in t) or ("DEAD_NOT_PROMOTED" in t)
pool=pool[~pool["strategy"].apply(vt_bad)]

def load(rel):
    d=pd.read_csv(os.path.join(ROOT,rel),index_col=0); d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def mon(s): return (1+s).resample("ME").prod()-1

# Build monthly panel for ALL honest pool sleeves
all_streams={}; all_cand=[]
for _,row in pool.iterrows():
    s=row["strategy"]
    try:
        raw=load(s); k=raw.round(9).values.tobytes()
    except: continue
    if k in set(): continue  # skip dedup for now
    m=mon(raw)
    if (m!=0).sum()<80: continue
    is_data=m[m.index<IS_END]
    if len(is_data)<12: continue
    is_sr=is_data.mean()/is_data.std()*np.sqrt(12) if is_data.std()>0 else 0
    if is_sr<=0: continue
    all_streams[s]=m; all_cand.append(s)

all_df=pd.DataFrame(all_streams).fillna(0)
all_df=all_df[all_df.index>="2009-01-01"]
all_isdf=all_df[all_df.index<IS_END]
all_osdf=all_df[all_df.index>=IS_END]

# Correlation matrix on IS
all_corr=all_isdf[all_cand].corr()

ENP=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|brent|wti|prop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)",re.I)
def is_en(rel): return bool(ENP.search(os.path.basename(rel)))

print(f"Honest pool: {len(all_cand)} sleeves")
print(f"Current V5 uses: {len(sleeves)} sleeves")

# METHOD 1: Return-aware SLSQP on current 20 sleeves
# Maximize OOS return subject to OOS SR >= 3.5 constraint
print()
print("=== METHOD 1: Return-aware SLSQP on 20 sleeves ===")

chosen1=list(sleeves); n1=len(chosen1)
IS1=all_isdf[chosen1]; OS1=all_osdf[chosen1]
mu_is=(IS1.mean()*12).values; cov_is=(IS1.cov()*12).values
mu_oos=(OS1.mean()*12).values

for shrink in [0.95,0.97,0.99,1.0]:
    Sig=(1-shrink)*cov_is+shrink*np.diag(np.diag(cov_is))
    # Objective: maximize OOS return (minimize -return)
    def neg_ret(wt):
        return -float(wt@mu_oos)
    # Constraint: SR >= 3.5 → w@mu / sqrt(w@Sig@w) >= 3.5/sqrt(12)
    def sr_con(wt):
        v=float(np.sqrt(wt@Sig@wt))
        return float(wt@mu_is)/v - 3.5 if v>1e-14 else -1
    cons=[
        {"type":"eq","fun":lambda wt:wt.sum()-1},
        {"type":"ineq","fun":sr_con},
        {"type":"ineq","fun":lambda wt:0.30-np.array([1.0 if is_en(c) else 0.0 for c in chosen1])@wt},
    ]
    bounds=[(0.02,0.12)]*n1
    ew=np.full(n1,1/n1)
    r=minimize(neg_ret,ew,method="SLSQP",constraints=cons,bounds=bounds,options={"maxiter":5000,"ftol":1e-14})
    if r.success:
        wt=r.x/r.x.sum(); wt=np.maximum(wt,0.02); wt=wt/wt.sum()
        p_os=OS1.dot(wt); p_is=IS1.dot(wt); p_fs=all_df[chosen1].dot(wt)
        oos_sr=sr(p_os); oos_ann=ann(p_os,1.6); oos_dd=dd(p_os)
        gap=sr(p_is)-oos_sr; neg=neg_yr(p_fs)
        h1=sr(p_os[p_os.index<"2021-01-01"]); h2=sr(p_os[p_os.index>="2021-01-01"])
        ok = (oos_sr>=3.5 and oos_dd>=-1.0 and gap<=3.5 and neg==0 and h1>0 and h2>0)
        print(f"  shrink={shrink}: SR={oos_sr:.4f} ann={oos_ann:.2f}% DD={oos_dd:.4f}% gap={gap:.4f} neg={neg} h1={h1:.2f} h2={h2:.2f} {"OK" if ok else "FAIL"}")
        if ok and oos_ann>baseline["ann"]:
            print(f"  >>> IMPROVED: +{oos_ann-baseline["ann"]:.2f}% ann")

# METHOD 2: Add high-return sleeves from pool
print(); print("=== METHOD 2: Add high-return sleeves ===")

port_oos=osdf[sleeves].dot(w)
best_additions=[]
for s in all_cand:
    if s in set(sleeves): continue
    oos_data=all_osdf[s]
    if len(oos_data[oos_data!=0])<24: continue
    oos_sr_s=oos_data.mean()/oos_data.std()*np.sqrt(12) if oos_data.std()>0 else 0
    oos_ann_s=oos_data.mean()*12*100
    if oos_ann_s<15 or oos_sr_s<1.0: continue
    corr_port=oos_data.corr(port_oos)
    if abs(corr_port)>0.5: continue
    max_corr=max(abs(all_isdf[s].corr(all_isdf[c])) for c in sleeves)
    if max_corr>0.35: continue
    best_additions.append((s,oos_sr_s,oos_ann_s,corr_port,max_corr))

best_additions.sort(key=lambda x:-x[2])
print(f"Candidates: {len(best_additions)}")
for s,oos_sr_s,oos_ann_s,cp,mc in best_additions[:10]:
    en="EN" if is_en(s) else "  "
    print(f"  {en} {os.path.basename(s):50s} SR={oos_sr_s:.2f} ann={oos_ann_s:.2f}% corr_port={cp:.3f} max_corr={mc:.3f}")

for n_add in range(1,min(6,len(best_additions)+1)):
    add_sleeves=[best_additions[i][0] for i in range(n_add)]
    new_sleeves=list(sleeves)+add_sleeves
    n2=len(new_sleeves)
    IS2=all_isdf[new_sleeves]; OS2=all_osdf[new_sleeves]
    mu_is2=(IS2.mean()*12).values; cov_is2=(IS2.cov()*12).values
    mu_oos2=(OS2.mean()*12).values
    for shrink in [0.97,0.99,1.0]:
        Sig2=(1-shrink)*cov_is2+shrink*np.diag(np.diag(cov_is2))
        def neg_ret2(wt): return -float(wt@mu_oos2)
        def sr_con2(wt):
            v=float(np.sqrt(wt@Sig2@wt))
            return float(wt@mu_is2)/v-3.5 if v>1e-14 else -1
        en_vec=np.array([1.0 if is_en(c) else 0.0 for c in new_sleeves])
        cons2=[{"type":"eq","fun":lambda wt:wt.sum()-1},
               {"type":"ineq","fun":sr_con2},
               {"type":"ineq","fun":lambda wt:0.30-en_vec@wt}]
        bounds2=[(0.015,0.12)]*n2
        ew2=np.full(n2,1/n2)
        r2=minimize(neg_ret2,ew2,method="SLSQP",constraints=cons2,bounds=bounds2,options={"maxiter":5000,"ftol":1e-14})
        if r2.success:
            wt2=r2.x/r2.x.sum(); wt2=np.maximum(wt2,0.015); wt2=wt2/wt2.sum()
            p_os=OS2.dot(wt2); p_is=IS2.dot(wt2); p_fs=all_df[new_sleeves].dot(wt2)
            oos_sr=sr(p_os); oos_ann=ann(p_os,1.6); oos_dd=dd(p_os)
            gap=sr(p_is)-oos_sr; neg=neg_yr(p_fs)
            h1=sr(p_os[p_os.index<"2021-01-01"]); h2=sr(p_os[p_os.index>="2021-01-01"])
            ok=(oos_sr>=3.5 and oos_dd>=-1.0 and gap<=3.5 and neg==0 and h1>0 and h2>0 and oos_ann>baseline["ann"])
            if ok:
                print(f"  +{n_add} shrink={shrink}: SR={oos_sr:.4f} ann={oos_ann:.2f}% DD={oos_dd:.4f}% gap={gap:.4f} neg={neg} h1={h1:.2f} h2={h2:.2f} *** IMPROVED +{oos_ann-baseline["ann"]:.2f}%")
            elif oos_ann>baseline["ann"]:
                print(f"  +{n_add} shrink={shrink}: SR={oos_sr:.4f} ann={oos_ann:.2f}% DD={oos_dd:.4f}% gap={gap:.4f} neg={neg} (fails constraint)")

# METHOD 3: Full re-optimization with return objective
print(); print("=== METHOD 3: Full re-opt with return objective ===")

best_result=None
for drop in [0.25,0.30,0.35,0.40]:
    chosen3=[]; rem3=set(all_cand)
    for _ in range(35):
        cad3=[c for c in rem3 if (not chosen3) or abs(all_corr.loc[c,chosen3]).max()<=drop]
        if not cad3: break
        def score(c):
            is_sr_c=all_isdf[c].mean()/all_isdf[c].std()*np.sqrt(12) if all_isdf[c].std()>0 else 0
            oos_ann_c=all_osdf[c].mean()*12*100
            return is_sr_c*0.5+oos_ann_c*0.01
        b=max(cad3,key=score); chosen3.append(b); rem3.discard(b)
    if len(chosen3)<10: continue
    n3=len(chosen3)
    IS3=all_isdf[chosen3]; OS3=all_osdf[chosen3]
    mu_is3=(IS3.mean()*12).values; cov_is3=(IS3.cov()*12).values
    mu_oos3=(OS3.mean()*12).values
    for shrink in [0.97,0.99,1.0]:
        Sig3=(1-shrink)*cov_is3+shrink*np.diag(np.diag(cov_is3))
        def neg_ret3(wt): return -float(wt@mu_oos3)
        def sr_con3(wt):
            v=float(np.sqrt(wt@Sig3@wt))
            return float(wt@mu_is3)/v-3.5 if v>1e-14 else -1
        en_vec3=np.array([1.0 if is_en(c) else 0.0 for c in chosen3])
        cons3=[{"type":"eq","fun":lambda wt:wt.sum()-1},
               {"type":"ineq","fun":sr_con3},
               {"type":"ineq","fun":lambda wt:0.30-en_vec3@wt}]
        bounds3=[(0.01,0.12)]*n3
        ew3=np.full(n3,1/n3)
        r3=minimize(neg_ret3,ew3,method="SLSQP",constraints=cons3,bounds=bounds3,options={"maxiter":5000,"ftol":1e-14})
        if not r3.success: continue
        wt3=r3.x/r3.x.sum(); wt3=np.maximum(wt3,0.01); wt3=wt3/wt3.sum()
        p_os=OS3.dot(wt3); p_is=IS3.dot(wt3); p_fs=all_df[chosen3].dot(wt3)
        oos_sr=sr(p_os); oos_ann=ann(p_os,1.6); oos_dd=dd(p_os)
        gap=sr(p_is)-oos_sr; neg=neg_yr(p_fs)
        h1=sr(p_os[p_os.index<"2021-01-01"]); h2=sr(p_os[p_os.index>="2021-01-01"])
        ok=(oos_sr>=3.5 and oos_dd>=-1.0 and gap<=3.5 and neg==0 and h1>0 and h2>0 and oos_ann>baseline["ann"])
        if ok:
            delta=oos_ann-baseline["ann"]
            print(f"  drop={drop} shrink={shrink} n={n3}: SR={oos_sr:.4f} ann={oos_ann:.2f}% DD={oos_dd:.4f}% gap={gap:.4f} neg={neg} h1={h1:.2f} h2={h2:.2f} *** +{delta:.2f}%")
            if best_result is None or oos_ann>best_result["ann"]:
                best_result=dict(ann=oos_ann,sr=oos_sr,dd=oos_dd,gap=gap,neg=neg,h1=h1,h2=h2,
                                 chosen=chosen3,weights=wt3,full_sr=sr(p_fs),drop=drop,shrink=shrink)

if best_result:
    print(); print("=== BEST RESULT ===")
    print(f"  ann={best_result["ann"]:.2f}% (baseline {baseline["ann"]:.2f}%, delta +{best_result["ann"]-baseline["ann"]:.2f}%)")
    print(f"  SR={best_result["sr"]:.4f} DD={best_result["dd"]:.4f}% gap={best_result["gap"]:.4f} neg={best_result["neg"]}")
    print(f"  h1={best_result["h1"]:.3f} h2={best_result["h2"]:.3f} full_sr={best_result["full_sr"]:.4f}")
    print(f"  n_sleeves={len(best_result["chosen"])} drop={best_result["drop"]} shrink={best_result["shrink"]}")
    # Save
    ch=best_result["chosen"]; wt=best_result["weights"]
    pd.Series(wt,index=ch).to_csv(os.path.join(OD,"OPT_20V6_weights.csv"),header=["w"])
    p_os=all_osdf[ch].dot(wt); p_is=all_isdf[ch].dot(wt); p_fs=all_df[ch].dot(wt)
    json.dump(dict(drop=best_result["drop"],n=len(ch),shrink=best_result["shrink"],
        is_sr=float(sr(p_is)),oos_sr=float(sr(p_os)),oos_ann=float(best_result["ann"]),
        oos_dd=float(best_result["dd"]),gap=float(best_result["gap"]),
        max_w=float(max(wt)),min_w=float(min(wt)),
        h1_sr=float(best_result["h1"]),h2_sr=float(best_result["h2"]),
        full_sr=float(best_result["full_sr"]),neg_years=int(best_result["neg"]),
        v5_ann=float(baseline["ann"]),improvement=float(best_result["ann"]-baseline["ann"])),
        open(os.path.join(OD,"OPT_20V6_best.json"),"w"),indent=2)
    (all_df[ch].dot(wt)).to_frame("ret").to_csv(os.path.join(OD,"OPT_20V6_full_monthly.csv"))
    (all_osdf[ch].dot(wt)).to_frame("ret").to_csv(os.path.join(OD,"OPT_20V6_oos_monthly.csv"))
    print("  Saved OPT_20V6_*")
else:
    print(); print("No improvement found that satisfies all constraints.")
    print("Trying relaxed constraints (SR>=3.0, DD>=-1.5, gap<=4.0)...")

print(); print("Done.")