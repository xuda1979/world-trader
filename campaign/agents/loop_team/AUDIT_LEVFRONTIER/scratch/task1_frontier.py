import sys
sys.path.insert(0, 'campaign/scripts'); sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L

def fmt(label, r, gross=None, start='2008-03-31'):
    s = L.stats(r, start)
    rr = r[r.index >= start]
    yr = rr.groupby(rr.index.year).apply(lambda x: (1+x).prod()-1)
    extra = ""
    if gross is not None and len(gross):
        gg = gross[gross.index >= start].dropna()
        extra = f"  gmean {gg.mean():.3f}x  days>1.6 {float((gg>1.6).mean())*100:5.1f}%"
    print(f"{label:38s} ann_geo {s['ann_geo']:6.2f}%  SR_d {s['sr_d']:5.3f}  SR_m {s['sr_m']:5.3f}  MDD {s['mdd']:6.2f}%  vol {s['vol']:5.2f}%  neg {s['neg']}/{yr.size}  worst {s['worst']:6.2f}%{extra}")

print("=== TASK 1: HONEST FRONTIER @ capital-real 1.6x cap, 6.4bps/side, borrow 0.5%/yr, margin on (gross-1) ===")
print("--- A. financing-rate sweep on V3 BAL @1.6x ---")
for rate in (0.03, 0.045, 0.06):
    rA, gA, _ = L.capped_book(L.NEW3, 0.07, 0.04, rate=rate)
    rB, gB, _ = L.capped_book(L.NEW3, 0.091, 0.03, rate=rate)
    fmt(f"V3 BAL @1.6x + {rate*100:.1f}%/yr margin", ((rA+rB)/2).dropna(), ((gA+gB)/2))
print("--- B. uncapped committed reference (6.0bps, margin free) ---")
for nm, TGT, THR in [('SAFE', 0.07, 0.04), ('AGGR', 0.091, 0.03)]:
    fmt(f"V3 {nm} committed uncapped", L.committed_replica13(L.NEW3, TGT, THR))
fmt("V3 BAL committed uncapped", ((L.committed_replica13(L.NEW3, 0.07, 0.04) + L.committed_replica13(L.NEW3, 0.091, 0.03))/2).dropna())
print("--- C. all builds @1.6x cap + 4.5%/yr margin (BASE CASE) ---")
for fam, NEW in [('V3', L.NEW3), ('V2', L.NEW2)]:
    rA, gA, _ = L.capped_book(NEW, 0.07, 0.04)
    rB, gB, _ = L.capped_book(NEW, 0.091, 0.03)
    fmt(f"{fam} SAFE @1.6x+4.5%", rA, gA)
    fmt(f"{fam} AGGR @1.6x+4.5%", rB, gB)
    bal = ((rA+rB)/2).dropna()
    fmt(f"{fam} BAL @1.6x+4.5%", bal, ((gA+gB)/2))
rA, gA, _ = L.capped_book11(0.07, 0.04)
rB, gB, _ = L.capped_book11(0.091, 0.03)
fmt("POOL11 SAFE @1.6x+4.5%", rA, gA)
fmt("POOL11 AGGR @1.6x+4.5%", rB, gB)
fmt("POOL11 BAL @1.6x+4.5%", ((rA+rB)/2).dropna(), ((gA+gB)/2))
print("--- D. financing-rate sweep on V2 BAL and POOL11 BAL @1.6x ---")
for rate in (0.03, 0.06):
    rA, gA, _ = L.capped_book(L.NEW2, 0.07, 0.04, rate=rate)
    rB, gB, _ = L.capped_book(L.NEW2, 0.091, 0.03, rate=rate)
    fmt(f"V2 BAL @1.6x + {rate*100:.1f}%", ((rA+rB)/2).dropna(), ((gA+gB)/2))
rA, gA, _ = L.capped_book11(0.07, 0.04, rate=0.03)
rB, gB, _ = L.capped_book11(0.091, 0.03, rate=0.03)
fmt("POOL11 BAL @1.6x + 3.0%", ((rA+rB)/2).dropna(), ((gA+gB)/2))
rA, gA, _ = L.capped_book11(0.07, 0.04, rate=0.06)
rB, gB, _ = L.capped_book11(0.091, 0.03, rate=0.06)
fmt("POOL11 BAL @1.6x + 6.0%", ((rA+rB)/2).dropna(), ((gA+gB)/2))
