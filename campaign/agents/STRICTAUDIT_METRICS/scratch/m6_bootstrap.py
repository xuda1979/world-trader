# m6: bootstrap CIs — iid monthly resample 5000x; also block bootstrap on daily; daily-SR CI
import pandas as pd, numpy as np
rng = np.random.default_rng(20260902)
CSV = "/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
r = pd.read_csv(CSV, index_col=0, parse_dates=True)['ret'].dropna()
m = r.resample("ME").apply(lambda x:(1+x).prod()-1).values
n_m = len(m)

# iid monthly bootstrap
B=5000
srs = np.empty(B)
for b in range(B):
    s = rng.choice(m, size=n_m, replace=True)
    srs[b] = s.mean()/s.std(ddof=1)*np.sqrt(12)
lo,hi = np.percentile(srs,[2.5,97.5])
print(f"IID MONTHLY bootstrap ({B}x, n={n_m} months): monthly SR point={m.mean()/m.std(ddof=1)*np.sqrt(12):.3f}  CI=[{lo:.3f},{hi:.3f}]  [claim [3.02,4.01]]")

# block bootstrap monthly (blocks of 6 months)
L=6; nb=n_m//L
srs_b=np.empty(B)
for b in range(B):
    starts=rng.integers(0,n_m-L+1,size=nb)
    s=np.concatenate([m[s:s+L] for s in starts])[:n_m]
    srs_b[b]=s.mean()/s.std(ddof=1)*np.sqrt(12)
lo2,hi2=np.percentile(srs_b,[2.5,97.5])
print(f"BLOCK(6mo) MONTHLY bootstrap: CI=[{lo2:.3f},{hi2:.3f}]")

# daily iid bootstrap
d=r.values; n_d=len(d)
srs_d=np.empty(B)
for b in range(B):
    s=rng.choice(d,size=n_d,replace=True)
    srs_d[b]=s.mean()/s.std(ddof=1)*np.sqrt(252)
lod,hid=np.percentile(srs_d,[2.5,97.5])
print(f"IID DAILY bootstrap: daily SR point={d.mean()/d.std(ddof=1)*np.sqrt(252):.3f}  CI=[{lod:.3f},{hid:.3f}]")

# circular block bootstrap daily (block=21d)
Ld=21; nb_d=n_d//Ld
srs_db=np.empty(B)
for b in range(B):
    starts=rng.integers(0,n_d-Ld+1,size=nb_d)
    s=np.concatenate([d[s:s+Ld] for s in starts])[:n_d]
    srs_db[b]=s.mean()/s.std(ddof=1)*np.sqrt(252)
lo3,hi3=np.percentile(srs_db,[2.5,97.5])
print(f"BLOCK(21d) DAILY bootstrap: CI=[{lo3:.3f},{hi3:.3f}]")

# analytic normal CIs for reference
se_d = np.sqrt((1+0.5*5.241**2)/n_d)*np.sqrt(252/252)  # approx via SR/sqrt(n)*sqrt(1+SR^2/2) in daily units
sr_daily_dailyunits = d.mean()/d.std(ddof=1)
se = np.sqrt((1+0.5*sr_daily_dailyunits**2)/n_d)
print(f"analytic daily SR CI (Lo, daily-units annualized): [{(sr_daily_dailyunits-1.96*se)*np.sqrt(252):.3f},{(sr_daily_dailyunits+1.96*se)*np.sqrt(252):.3f}]")
sr_m_mu = m.mean(); sr_m_sd = m.std(ddof=1)
se_m = np.sqrt((1+0.5*(sr_m_mu/sr_m_sd)**2)/n_m)
srm = sr_m_mu/sr_m_sd*np.sqrt(12)
print(f"analytic monthly SR CI: [{srm-1.96*se_m*np.sqrt(12):.3f},{srm+1.96*se_m*np.sqrt(12):.3f}]")
