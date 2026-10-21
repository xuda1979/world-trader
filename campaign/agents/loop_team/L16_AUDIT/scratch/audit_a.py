import numpy as np, pandas as pd, json
ROOT="/Users/daxu/software/world-trader"
def load(fn):
    df=pd.read_csv(f"{ROOT}/campaign/results/{fn}",index_col=0,parse_dates=True)
    return df.iloc[:,0].astype(float)

def stats(r,label):
    out={"label":label,"n":int(len(r))}
    out["start"]=str(r.index.min().date()); out["end"]=str(r.index.max().date())
    out["ann_geo"]=float((1+r).prod()**(252/len(r))-1)
    out["ann_arith"]=float(r.mean()*252)
    out["sr_d"]=float(r.mean()/r.std()*np.sqrt(252))
    m=(1+r).resample("ME").prod()-1
    out["sr_m"]=float(m.mean()/m.std()*np.sqrt(12))
    eq=(1+r).cumprod(); out["mdd"]=float((eq/eq.cummax()-1).min())
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    out["years"]={int(k):float(v) for k,v in yr.items()}
    out["neg_years"]=int((yr<0).sum()); out["worst_year"]=float(yr.min())
    # worst 3y subwindow MaxDD
    w3=0.0
    for s in pd.date_range(r.index.min(),r.index.max(),freq="MS"):
        sub=r[(r.index>=s)&(r.index<s+pd.DateOffset(years=3))]
        if len(sub)>500:
            e=(1+sub).cumprod(); d=(e/e.cummax()-1).min()
            w3=min(w3,float(d))
    out["worst3y_mdd"]=w3
    o=r[r.index>="2017-01-01"]
    out["oos17_ann"]=float(o.mean()*252); out["oos17_sr"]=float(o.mean()/o.std()*np.sqrt(252))
    # mechanical flatten/zero checks
    out["n_unique"]=int(r.round(12).nunique())
    out["uniq_ratio"]=out["n_unique"]/len(r)
    out["ac1"]=float(r.autocorr(1))
    mid=r.iloc[1:-1]; z=(mid==0)
    runs=[]; c=0
    for v in z:
        if v: c+=1
        else:
            if c>=10: runs.append(c)
            c=0
    if c>=10: runs.append(c)
    out["zero_runs>=10"]=runs
    out["max_abs_daily"]=float(r.abs().max())
    # calendar completeness vs NYSE weekdays
    allb=pd.bdate_range(r.index.min(),r.index.min()+pd.offsets.CustomBusinessDay(0)) # placeholder
    return out

res={}
for fn,lab in [("GOAL100_HONEST11L16_BALANCED_daily.csv","BAL"),
               ("GOAL100_HONEST11L16_SAFE_daily.csv","SAFE"),
               ("GOAL100_HONEST11L16_AGGRESSIVE_daily.csv","AGGR")]:
    r=load(fn); res[lab]=stats(r,lab)
    print(f"== {lab} n={res[lab]['n']} {res[lab]['start']}..{res[lab]['end']}")
    print(f" ann_geo {res[lab]['ann_geo']*100:.2f}%  SR_d {res[lab]['sr_d']:.3f}  SR_m {res[lab]['sr_m']:.3f}  MDD {res[lab]['mdd']*100:.2f}%  worst3y {res[lab]['worst3y_mdd']*100:.2f}%")
    print(f" negyrs {res[lab]['neg_years']} worst_yr {res[lab]['worst_year']*100:.2f}%  OOS17 ann {res[lab]['oos17_ann']*100:.1f}% SR {res[lab]['oos17_sr']:.2f}")
    print(f" uniq {res[lab]['n_unique']} ratio {res[lab]['uniq_ratio']:.4f}  ac1 {res[lab]['ac1']:.4f}  zeroRuns>=10d {res[lab]['zero_runs>=10']}  max|d| {res[lab]['max_abs_daily']*100:.2f}%")
json.dump(res,open(f"{ROOT}/campaign/agents/loop_team/L16_AUDIT/scratch/stats_l16.json","w"),indent=1)
