#!/usr/bin/env python3
"""TDD gates for AUDIT_LEVFRONTIER (RED must be observed before GREEN)."""
import sys
sys.path.insert(0, 'campaign/scripts')
sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L

ROOT = "/Users/daxu/software/world-trader"
fails = []
def gate(name, ok, detail):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok: fails.append(name)

# G1: byte-repro of my reconstruction vs committed CSVs (verification gate)
for tag, fn, TGT, THR, NEW in [
    ('V3',  'GOAL100_HONEST14V3_SAFE_daily.csv',        0.07, 0.04, L.NEW3),
    ('V3',  'GOAL100_HONEST14V3_AGGRESSIVE_daily.csv',  0.091, 0.03, L.NEW3),
    ('V2',  'GOAL100_HONEST13V2_BALANCED_daily.csv',    None, None, L.NEW2),
    ('POOL11','GOAL100_HONEST11FIX_BALANCED_daily.csv', None, None, {})]:
    if TGT is None:
        a = L.committed_replica(NEW, 0.07, 0.04); b = L.committed_replica(NEW, 0.091, 0.03)
        r = ((a + b) / 2).dropna()
    else:
        r = L.committed_replica(NEW, TGT, THR)
    old = pd.read_csv(f"{ROOT}/campaign/results/{fn}", index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([old.rename('o'), r.rename('n')], axis=1, join='inner').dropna()
    md = float((j.o - j.n).abs().max()); full = (len(j) == max(len(old), len(r)))
    gate(f"G1 repro {fn}", md < 1e-12 and full, f"max|diff|={md:.3e} rows old={len(old)} new={len(r)} joined={len(j)}")

# G2: capped gross <= 1.6 on ALL days (new code — must be RED with stub)
r, g, to = L.capped_book(L.NEW3, 0.07, 0.04)
gate("G2 cap<=1.6 all days", float(g.max()) <= 1.6 + 1e-9, f"max gross={float(g.max()):.4f} mean={float(g.mean()):.4f}")

# G3: margin financing actually charged (rate>0 must strictly reduce ann)
r0, _, _ = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.0)
import levfrontier
r4, _, _ = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.045)
a0 = (1+r0).prod()**(252/len(r0)) - 1; a4 = (1+r4).prod()**(252/len(r4)) - 1
gate("G3 margin charged", a4 < a0 - 0.005, f"ann rate0={a0*100:.2f}% rate4.5={a4*100:.2f}% delta={(a4-a0)*100:.2f}pp")

# G4: cost reconciliation: charged cost == 6.4bps x onemiddle turnover exactly
r6, g6, to6 = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.0)
c = L.components(L.NEW3, 0.07, 0.04)
# recompute charged components independently
idx = c['b'].index; kap = L.cap_factor(c['gross_raw']).reindex(idx).fillna(0)
tw_c = c['tw'].reindex(idx).fillna(0)*kap
dsc_c = (c['sc'].diff().abs()*0.5).reindex(idx).fillna(0)*kap
reb_c = c['full'].mul(kap, axis=0).diff().abs().sum(axis=1).reindex(idx).fillna(0)
tot_turn = float((tw_c + dsc_c + reb_c).sum())
# charged inside r6 = b*sc - turn*6.4e-4 - htb
grosspre = (c['b']*c['sc']).reindex(r6.index)
htb = (c['htb'].reindex(idx).fillna(0)*kap/252).reindex(r6.index).fillna(0)
recon = grosspre - (tw_c+reb_c).reindex(r6.index).fillna(0)*6.4e-4 - dsc_c.reindex(r6.index).fillna(0)*6.4e-4 - htb
md = float((recon - r6).abs().max())
gate("G4 cost ledger identity", md < 1e-15, f"max|recon-r|={md:.3e} tot1side_turn={tot_turn:.1f} charged_cost={tot_turn*6.4e-4*100:.2f}%cum")

print("RED-STAGE FAILURES:", fails if fails else "none")
