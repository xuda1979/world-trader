import pandas as pd, numpy as np
ROOT="/Users/daxu/software/world-trader"
r=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
def stats(r,label=""):
    r=r.dropna(); eq=(1+r).cumprod(); dd=eq/eq.cummax()-1
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    m=r.resample("ME").apply(lambda x:(1+x).prod()-1)
    sr_d=r.mean()/r.std()*np.sqrt(252)
    sr_m=m.mean()/m.std()*np.sqrt(12)
    o=r[r.index>="2017-01-01"]
    print(f"{label} n={len(r)} span {r.index[0].date()}..{r.index[-1].date()} ({(r.index[-1]-r.index[0]).days/365.25:.2f}y)")
    print(f"  ann(mean*252)={r.mean()*252*100:.1f}%  ann(CAGR)={((1+r).prod()**(252/len(r))-1)*100:.1f}%  vol={r.std()*np.sqrt(252)*100:.1f}%")
    print(f"  SR_daily={sr_d:.2f}  SR_monthly={sr_m:.2f}  ratio={sr_d/sr_m:.3f}")
    print(f"  MaxDD={dd.min()*100:.2f}%  neg years={int((yr<0).sum())}/{len(yr)}  worst={yr.min()*100:.1f}%({yr.idxmin()}) best={yr.max()*100:.1f}%({yr.idxmax()})")
    oeq=(1+o).cumprod(); omdd=(oeq/oeq.cummax()-1).min()
    print(f"  OOS2017+: ann={o.mean()*252*100:.1f}% SR={o.mean()/o.std()*np.sqrt(252):.2f} DD={omdd*100:.2f}%")
    return yr,m
print("=== FULL claimed-champion series ===")
yr,m=stats(r,"CHAMP")
print("\n=== per-year return & SR ===")
for y in sorted(yr.index):
    x=r[r.index.year==y]
    print(f"  {y}: ret={yr[y]*100:7.1f}%  SR={x.mean()/x.std()*np.sqrt(252):5.2f}  n={len(x)}")
# autocorr
print("\n=== daily autocorr ===")
for k in [1,2,3,5,10,21]:
    print(f"  lag{k}: {r.autocorr(k):+.4f}")
mm=r.resample("ME").apply(lambda x:(1+x).prod()-1)
print("monthly autocorr lag1:", round(mm.autocorr(1),4))
# variance ratio (how much daily SR inflated by mean reversion)
# VR(q) = Var(q-day ret)/(q*Var(1day)); VR<1 => mean reversion
for q in [5,21,63]:
    rq=(1+r).rolling(q).apply(np.prod,raw=True)-1
    vr=rq.var()/(q*r.var())
    sr_honest_d=r.mean()/r.std()*np.sqrt(252/vr)  # SR scaled: if VR<1, honest daily SR lower
    print(f"  VR({q}d)={vr:.4f} -> autocorr-corrected daily-SR proxy = {r.mean()/r.std()*np.sqrt(252)*np.sqrt(vr):.2f}")
