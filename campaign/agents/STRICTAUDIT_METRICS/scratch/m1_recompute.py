# STRICTAUDIT_METRICS m1: independent recomputation of ALL headline claims from CSV alone.
import pandas as pd, numpy as np

CSV = "/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
raw = pd.read_csv(CSV)
print("raw shape:", raw.shape, "cols:", list(raw.columns))
r = pd.read_csv(CSV, index_col=0, parse_dates=True).iloc[:, 0]
r = r.sort_index()
d = r.dropna()
print(f"n_full={len(r)} n_dropna={len(d)}  first={d.index[0].date()} last={d.index[-1].date()}")
span_y_days = (d.index[-1] - d.index[0]).days / 365.25
span_y_252  = len(d) / 252.0
print(f"span: {span_y_days:.3f}y (calendar-day) | {span_y_252:.3f}y (n/252) | n={len(d)}")
print(f"claimed span 17.9y, n=4522  -> CHECK n: {'MATCH' if len(d)==4522 else 'DIFF'}")

mu, sd = d.mean(), d.std(ddof=1)
ann_mean = mu*252
cagr = (1+d).prod()**(252/len(d)) - 1
cagr_cal = (1+d).prod()**(1/span_y_days) - 1
vol = sd*np.sqrt(252)
sr_d = mu/sd*np.sqrt(252)
print(f"\n--- headline ---")
print(f"ann (arith mu*252): {ann_mean*100:.2f}%   CAGR(n/252): {cagr*100:.2f}%   CAGR(calendar): {cagr_cal*100:.2f}%   [claim 49.4%]")
print(f"ann vol: {vol*100:.2f}%")
print(f"daily SR (arith, sqrt252): {sr_d:.3f}   [claim 5.24]")

# monthly
m = d.resample("ME").apply(lambda x: (1+x).prod()-1)
sr_m = m.mean()/m.std(ddof=1)*np.sqrt(12)
print(f"monthly series n={len(m)} ({m.index[0].date()}..{m.index[-1].date()})  SR_monthly: {sr_m:.3f}   [claim 3.46]")

# MaxDD full
eq = (1+d).cumprod(); dd = eq/eq.cummax()-1
mdd = dd.min(); mdd_date = dd.idxmin()
print(f"MaxDD full: {mdd*100:.2f}%  trough {mdd_date.date()}  [claim -6.1%]")

# per calendar year
yr = d.groupby(d.index.year).apply(lambda x:(1+x).prod()-1)
neg = yr[yr<0]
print(f"\n--- years (n={len(yr)}) ---")
print(f"negative years: {len(neg)}  [claim 0/19]")
print(f"lowest year: {yr.idxmin()} {yr.min()*100:.2f}%   [claim lowest 2026-partial +20.7%]")
print(f"best year:  {yr.idxmax()} {yr.max()*100:.2f}%   [claim 151.1% (2023)]")
for y,v in yr.items():
    x = d[d.index.year==y]
    print(f"  {y}: {v*100:8.2f}%  n={len(x):4d}  last={x.index[-1].date()}")

# OOS 2017+
o = d[d.index>="2017-01-01"]
oeq = (1+o).cumprod(); odd = oeq/oeq.cummax()-1
sr_o = o.mean()/o.std(ddof=1)*np.sqrt(252)
print(f"\n--- OOS 2017+ (n={len(o)}) ---")
print(f"ann(arith): {o.mean()*252*100:.2f}%  CAGR: {((1+o).prod()**(252/len(o))-1)*100:.2f}%  SR: {sr_o:.3f}  MaxDD: {odd.min()*100:.2f}%  [claim 55.9% @ -6.1%]")

# autocorrelation / daily-vs-monthly gap
a1 = d.autocorr(1)
m1 = m.autocorr(1)
print(f"\n--- daily vs monthly SR gap ---")
print(f"daily lag-1 autocorr: {a1:+.4f}   monthly lag-1: {m1:+.4f}")
print(f"daily SR / monthly SR = {sr_d/sr_m:.3f} (gap factor {sr_d/sr_m:.2f}x)")
# Lo shaft: SR from q-day horizon
for q in [1,5,21,63]:
    rq = (1+d).rolling(q).apply(np.prod, raw=True) - 1
    vr = rq.var()/(q*d.var())
    print(f"  q={q:3d}: variance-ratio VR={vr:.4f}  SR_q (sqrt252/q scaled) = {(rq.mean()/rq.std()*np.sqrt(252/q)):.3f}")
