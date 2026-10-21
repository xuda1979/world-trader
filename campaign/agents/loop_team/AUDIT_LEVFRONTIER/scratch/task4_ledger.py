"""TASK 4d v2: per-sleeve ledger over POOL(11)+NEW(3), RAW-EW of all 14."""
import sys
sys.path.insert(0, 'campaign/scripts'); sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L
import honest11_build as h11
from honest13_build import POOL, load, NEW3

INSTR = {'brwt15':'BRENT/WTI FUT SPREAD','brwt10':'BRENT/WTI FUT SPREAD','brwt7':'BRENT/WTI FUT SPREAD',
 'brwt5':'BRENT/WTI FUT SPREAD','C5ng':'HENRY HUB NG FUT','C5ngsum':'HENRY HUB NG FUT',
 'A5r2':'SPY (gate)','a6r7':'US 2Y FUT','QAxasts':'US 10Y FUT','carryv2':'GLD','dualmom':'EQ L/S',
 'diescrack':'DIESEL/WTI','CFX4':'FX CROSS BOOK','FF2':'FF MOM+MKT (research-only)'}
SYNTH = {'dualmom','CFX4','FF2'}

print("=== (d) per-sleeve ledger (raw committed net files, 2008-03-31+) ===")
rows = {}
for nm in list(POOL.keys()) + list(NEW3.keys()):
    rel = POOL.get(nm) or NEW3.get(nm)
    r = load(rel).dropna()
    rr = r[r.index >= '2008-03-31']
    yr = rr.groupby(rr.index.year).apply(lambda x: (1+x).prod()-1)
    eq = (1+rr).cumprod()
    sr = rr.mean()/rr.std()*np.sqrt(252)
    ann = ((1+rr).prod()**(252/len(rr))-1)*100
    mdd = ((eq/eq.cummax())-1).min()*100
    src = 'SYNTH' if nm in SYNTH else 'REAL'
    print(f"  {nm:10s} n={len(rr):5d} ann {ann:7.2f}% SR_d {sr:5.2f} MDD {mdd:6.2f}% neg {int((yr<0).sum()):2d}/{yr.size} vol {rr.std()*np.sqrt(252)*100:5.2f}%  {INSTR[nm]:26s} px:{src}")
    rows[nm] = rr

print("\n=== RAW-EW assemble (all sleeves slot 1/N of NAV, NO vt overlay, NO regear) ===")
df = pd.DataFrame(rows).dropna(how='all')
for subset, label in [([n for n in POOL], 'RAW-EW11 (pool only)'),
                      (list(POOL)+list(NEW3), 'RAW-EW14 (V3 pool)')]:
    d2 = df[subset]
    ew = d2.mean(axis=1).dropna(); ew = ew[ew.index >= '2008-03-31']
    s = L.stats(ew)
    yr = ew.groupby(ew.index.year).apply(lambda x: (1+x).prod()-1)
    print(f"  {label}: ann_geo {s['ann_geo']:6.2f}% SR_d {s['sr_d']:5.3f} SR_m {s['sr_m']:5.3f} MDD {s['mdd']:6.2f}% vol {s['vol']:5.2f}% n={s['n']} neg {int((yr<0).sum())}/{yr.size} worst {yr.min()*100:+.2f}%")
print("  construction: each sleeve capped at slot 1/N of NAV -> book gross <= 1.0x ALWAYS (no margin,")
print("  capital-real leverage 1.0x < 1.6x goal); the committed build's gross>1 comes ONLY from the")
print("  per-sleeve/global vol-target overlays (scale>1 on low-vol sleeves), not from the slots.")
