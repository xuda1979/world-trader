import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_H11FIX/scratch")
from rebuild_fix import build, vt, sn, POOL, ROOT

# --- full-span capital-real gross (reconcile commit "3.25x") ---
_, sa = build(0.07,0.04); _, sb = build(0.091,0.03)
ga = sa['Sd'].abs().sum(axis=1)/11 * sa['gs']; gb = sb['Sd'].abs().sum(axis=1)/11 * sb['gs']
gB = ((ga+gb)/2).dropna()
print(f"gross BAL FULL span: mean {gB.mean():.3f}x  p95 {gB.quantile(.95):.3f}x  max {gB.max():.3f}x  | 2008+: mean {gB[gB.index>='2008-01-01'].mean():.3f}x")

# --- sc / no-sc decomposition of exact turnover vs builder formula ---
print("\nexact-vs-formula reb turnover decomposition (2008+, one-side bp/day):")
for tag, s in [('SAFE',sa),('AGGR',sb)]:
    Sd, gs, sc = s['Sd'], s['gs'], s['sc']
    form  = (Sd.diff().abs().sum(axis=1)/11 + gs.diff().abs().fillna(0))
    pos_nosc = Sd.mul(gs, axis=0)
    exact_nosc = pos_nosc.diff().abs().sum(axis=1)/11
    pos_sc = Sd.mul(gs*sc, axis=0)
    exact_sc = pos_sc.diff().abs().sum(axis=1)/11
    flips_all = sc.diff().abs().fillna(0) > 0
    flips = (form.index.isin(flips_all[flips_all].index))
    w = (form.index>='2008-01-01')
    print(f"[{tag}] formula {form[w].mean()*1e4:.1f} | exact-no-sc {exact_nosc[w].mean()*1e4:.1f} | exact-with-sc {exact_sc[w].mean()*1e4:.1f} | sc-flip days contribute {(exact_sc-exact_nosc)[w].mean()*1e4:.1f} bp/d over {(flips & (form.index>='2008-01-01')).sum()} flip days")
    print(f"      drag/yr: formula {form[w].mean()*6e-4*252*100:.3f}%  exact-no-sc {exact_nosc[w].mean()*6e-4*252*100:.3f}%  exact-with-sc {exact_sc[w].mean()*6e-4*252*100:.3f}%")

# --- BAL == (SAFE+AGGR)/2 on committed files ---
A = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
G = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
Bc = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
mid = ((A+G)/2).dropna()
j = pd.concat([mid, Bc], axis=1, join='inner').dropna()
print(f"\nBAL vs (SAFE+AGGR)/2: max|diff| {float((j.iloc[:,0]-j.iloc[:,1]).abs().max()):.3e}, n={len(j)} (mid n={len(mid)}, BAL n={len(Bc)})")

# --- Columbus/Veterans lumping: which sleeves print on those days ---
from pandas.tseries.holiday import USFederalHolidayCalendar
hol = set(d.date() for d in USFederalHolidayCalendar().holidays(start='2006-01-01', end='2026-12-31'))
raw = {n: sn(p) for n,p in POOL.items()}
rawsn = {n: s for n,s in raw.items()}
# pre-sn raw
def loadraw(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0); df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)
rawl = {n: loadraw(p) for n,p in POOL.items()}
cnt = 0; lumped=0
for y in range(2008,2026):
    d = pd.Timestamp(year=y, month=10, day=1)
    while d.dayofweek!=0: d += pd.Timedelta(days=1)
    d += pd.Timedelta(weeks=1)  # Columbus (2nd Mon)
    if d in Bc.index: continue
    have = [n for n,r in rawl.items() if d in r.index and not pd.isna(r[d])]
    cnt += 1
    if have:
        lumped += 1
        if lumped<=3: print(f"  {d.date()} sleeves with raw prints (will be lumped into next day): {have} vals_bp={[round(float(rawl[n][d])*1e4,1) for n in have]}")
print(f"Columbus days 2008-2025 not in FIX: {cnt}; of which >=1 sleeve has raw print (lumped): {lumped}")
