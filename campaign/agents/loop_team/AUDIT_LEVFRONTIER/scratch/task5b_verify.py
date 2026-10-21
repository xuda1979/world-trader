import sys
sys.path.insert(0, 'campaign/scripts'); sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L
from honest13_build import POOL, load, NEW3

NAMES = list(POOL.keys()) + list(NEW3.keys())
df = pd.DataFrame({n: load(POOL.get(n) or NEW3.get(n)).dropna() for n in NAMES}).dropna(how='all')
df = df[df.index >= '2008-03-31']
GEAR = 1.6; RATE = 0.045; BPS = 6.4e-4
port = df.mean(axis=1)
nav = (1 + df.fillna(0)).cumprod()
w = nav.div(nav.mean(axis=1), axis=0).div(len(NAMES))
to = (w.diff().abs().sum(axis=1)*0.5).fillna(0)

def cand(rate, gear=GEAR):
    r = (port*gear - to*gear*BPS - max(gear-1,0)*rate/252).dropna()
    return r

print("=== candidate robustness ===")
for rate in (0.03, 0.045, 0.06):
    r = cand(rate); s = L.stats(r)
    print(f"  margin {rate*100:.1f}%: ann_geo {s['ann_geo']:.2f}% SR_d {s['sr_d']:.3f} MDD {s['mdd']:.2f}% vol {s['vol']:.2f}%")
r = cand(0.045)
for cut in ('2012-01-01', '2017-01-01', '2020-01-01'):
    rr = r[r.index >= cut]; s = L.stats(rr, start=cut)
    print(f"  start {cut[:4]}: ann {s['ann_geo']:.2f}% SR {s['sr_d']:.3f} MDD {s['mdd']:.2f}%")
yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
print("  yearly:", " ".join(f"{y}:{v*100:+.1f}" for y, v in yr.items()))
# POOL11 honest variant (with reset cost)
df11 = df[list(POOL)]
port11 = df11.mean(axis=1)
nav11 = (1 + df11.fillna(0)).cumprod()
w11 = nav11.div(nav11.mean(axis=1), axis=0).div(len(POOL))
to11 = (w11.diff().abs().sum(axis=1)*0.5).fillna(0)
r11 = (port11*GEAR - to11*GEAR*BPS - 0.6*RATE/252).dropna()
s11 = L.stats(r11)
print(f"  POOL11 RAW-EW @1.6x honest (cost charged): ann {s11['ann_geo']:.2f}% SR {s11['sr_d']:.3f} MDD {s11['mdd']:.2f}% turn {to11.mean()*252*6.4:.1f}bps/yr")
