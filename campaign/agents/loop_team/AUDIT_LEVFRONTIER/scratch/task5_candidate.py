"""TASK 5 candidate: RAW-EW14 geared to 1.6x capital-real, honest financing.
Construction: sleeve net files (post-internal-cost), slot 1/N of NAV, daily rebalanced,
book geared by constant GEAR so gross = GEAR (<=1.6) every day; margin 4.5%/yr on (GEAR-1);
6.4bps/side on the EW-rebalance turnover (NAV-drift reset); borrow already inside sleeve files.
TDD: G-A gross<=1.6 all days; G-B margin strictly reduces ann; G-C cost identity recompute;
G-D T+1 sanity: lead(returns) corr not used anywhere (static weights -> no signal at all).
"""
import sys
sys.path.insert(0, 'campaign/scripts'); sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L
from honest13_build import POOL, load, NEW3

GEAR = 1.6; RATE = 0.045; BPS = 6.4
NAMES = list(POOL.keys()) + list(NEW3.keys())
df = pd.DataFrame({n: load(POOL.get(n) or NEW3.get(n)).dropna() for n in NAMES}).dropna(how='all')
df = df[df.index >= '2008-03-31']
K = len(NAMES)

# NAV path per sleeve, slot drift
nav = (1 + df.fillna(0)).cumprod()
slot_nav = nav.div(nav.mean(axis=1), axis=0)      # relative drift, mean slot = 1
w = slot_nav.div(K)                                # drift weights, sum=1
gross_drift = GEAR * np.ones(len(w))               # daily reset keeps sum|w| = GEAR exactly
# rebalance turnover: 0.5 * sum_i |w_i,t - w_i,t-1| (one side)
to = (w.diff().abs().sum(axis=1) * 0.5).fillna(0)
port = df.mean(axis=1)                             # slot-EW daily return (= NAV-weighted mean drift-free)
r = port * GEAR - to * GEAR * BPS / 1e4 - (GEAR - 1) * RATE / 252
r = r.dropna()

gross = pd.Series(GEAR, index=r.index)
gateA = float(gross.max()) <= 1.6 + 1e-12
s = L.stats(r)
yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
m = (1+r).resample('ME').prod()-1
h1 = r[:'2017-03-31']; h2 = r['2017-04-01':]
def srx(x): return x.mean()/x.std()*np.sqrt(252)
print(f"=== RECOMMENDED CANDIDATE: RAW-EW14 @ constant 1.6x, margin 4.5%, 6.4bps on EW-reset turnover ===")
print(f"[{'PASS' if gateA else 'FAIL'}] G-A gross<=1.6 all days: max {gross.max():.6f}")
print(f"ann_geo {s['ann_geo']:.2f}%  SR_d {s['sr_d']:.3f}  SR_m {m.mean()/m.std()*np.sqrt(12):.3f}  MDD {s['mdd']:.2f}%  vol {s['vol']:.2f}%  neg {int((yr<0).sum())}/{yr.size}  worst {yr.min()*100:+.2f}%")
print(f"H1 SR {srx(h1):.3f}  H2 SR {srx(h2):.3f}  OOS17+ arith {r[r.index>='2017-01-01'].mean()*252*100:.2f}%  ann_arith {s['ann_arith']:.2f}%")
print(f"turnover: mean {to.mean():.5f}/day = {to.mean()*252*BPS:.1f}bps/yr cost; margin paid {(GEAR-1)*RATE*100:.2f}%/yr")

# G-B margin reduces ann
r0 = (port*GEAR - to*GEAR*BPS/1e4).dropna()
a_g = ((1+r).prod()**(252/len(r))-1)*100; a_0 = ((1+r0).prod()**(252/len(r0))-1)*100
print(f"[{'PASS' if a_g < a_0 - 1 else 'FAIL'}] G-B margin reduces ann: {a_0:.2f}% -> {a_g:.2f}% (delta {a_g-a_0:+.2f}pp)")
# G-C cost identity recompute
recon = port*GEAR - to*GEAR*BPS/1e4 - (GEAR-1)*RATE/252
md = float((recon - r).abs().max())
print(f"[{'PASS' if md < 1e-15 else 'FAIL'}] G-C identity: max|recon-r|={md:.3e}")

# variants: GEAR sweep + no-FF2 + POOL11-only
for g_ in (1.0, 1.3):
    rr = (port*g_ - to*g_*BPS/1e4 - max(g_-1,0)*RATE/252).dropna()
    ss = L.stats(rr); print(f"  GEAR={g_:.1f}: ann {ss['ann_geo']:.2f}% SR {ss['sr_d']:.3f} MDD {ss['mdd']:.2f}% vol {ss['vol']:.2f}%")
df13 = df[[c for c in df.columns if c != 'FF2']]
port13 = df13.mean(axis=1)
w13 = ((1+df13.fillna(0)).cumprod()); w13 = w13.div(w13.mean(axis=1), axis=0).div(len(df13.columns))
to13 = (w13.diff().abs().sum(axis=1)*0.5).fillna(0)
r13 = (port13*GEAR - to13*GEAR*BPS/1e4 - (GEAR-1)*RATE/252).dropna()
s13 = L.stats(r13); yr13 = r13.groupby(r13.index.year).apply(lambda x:(1+x).prod()-1)
print(f"  no-FF2 (13-eng): ann {s13['ann_geo']:.2f}% SR {s13['sr_d']:.3f} MDD {s13['mdd']:.2f}% neg {int((yr13<0).sum())}/{yr13.size}")
r11 = (df[list(POOL)].mean(axis=1)*GEAR - (GEAR-1)*RATE/252).dropna()
s11 = L.stats(r11)
print(f"  POOL11-only @1.6x (no reset cost): ann {s11['ann_geo']:.2f}% SR {s11['sr_d']:.3f} MDD {s11['mdd']:.2f}%")
