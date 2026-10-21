import pandas as pd, numpy as np
# Final headline verification with both conventions + OOS + DD windows
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv',parse_dates=['date']).set_index('date')
r = pd.to_numeric(ch['ret'],errors='coerce').dropna()
print(f"n={len(r)} span {r.index[0].date()}..{r.index[-1].date()}")
print(f"arith ann {r.mean()*252*100:.1f}% | geo ann {((1+r).prod()**(252/len(r))-1)*100:.1f}%")
print(f"SR daily {r.mean()/r.std()*np.sqrt(252):.2f}")
mr=(1+r).groupby(r.index.to_period('M')).prod()-1
print(f"SR monthly {mr.mean()/mr.std()*np.sqrt(12):.2f}")
eq=(1+r).cumprod(); print(f"MaxDD {(eq/eq.cummax()-1).min()*100:.1f}%")
yr=(1+r).groupby(r.index.year).prod()-1
print(f"neg years {(yr<0).sum()}/{len(yr)}; worst {yr.min()*100:.1f}% ({yr.idxmin()}); best {yr.max()*100:.1f}% ({yr.idxmax()})")
oos=r[r.index>='2017-01-01']
print(f"OOS2017+ arith ann {oos.mean()*252*100:.1f}% SR {oos.mean()/oos.std()*np.sqrt(252):.2f}")
# geo OOS
print(f"OOS geo {((1+oos).prod()**(252/len(oos))-1)*100:.1f}%")
# bootstrap CI for SR (monthly, 1000 reps)
rng=np.random.default_rng(7)
vals=mr.values; n=len(vals)
srs=[]
for _ in range(1000):
    s=rng.choice(vals,n,replace=True)
    srs.append(s.mean()/s.std()*np.sqrt(12))
print(f"monthly SR bootstrap 95% CI [{np.percentile(srs,2.5):.2f},{np.percentile(srs,97.5):.2f}]")
