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

# G1: byte-repro committed recipes
for tag, fn, TGT, THR in [
    ('V3', 'GOAL100_HONEST14V3_SAFE_daily.csv', 0.07, 0.04),
    ('V3', 'GOAL100_HONEST14V3_AGGRESSIVE_daily.csv', 0.091, 0.03),
    ('V3', 'GOAL100_HONEST14V3_BALANCED_daily.csv', None, None),
    ('V2', 'GOAL100_HONEST13V2_BALANCED_daily.csv', None, None)]:
    if TGT is None:
        r = ((L.committed_replica13(L.NEW3, 0.07, 0.04) + L.committed_replica13(L.NEW3, 0.091, 0.03))/2).dropna() if tag=='V3' else \
            ((L.committed_replica13(L.NEW2, 0.07, 0.04) + L.committed_replica13(L.NEW2, 0.091, 0.03))/2).dropna()
    else:
        r = L.committed_replica13(L.NEW3, TGT, THR)
    old = pd.read_csv(f"{ROOT}/campaign/results/{fn}", index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([old.rename('o'), r.rename('n')], axis=1, join='inner').dropna()
    md = float((j.o - j.n).abs().max())
    gate(f"G1 {fn}", md < 1e-12 and len(j) == max(len(old), len(r)), f"max|diff|={md:.3e} rows={len(j)}/{len(old)}")

# G5: POOL11 FIX byte-repro
rA = L.committed_replica11(0.07, 0.04); rB = L.committed_replica11(0.091, 0.03)
r = ((rA + rB)/2).dropna()
old = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([old.rename('o'), r.rename('n')], axis=1, join='inner').dropna()
md = float((j.o - j.n).abs().max())
gate("G5 POOL11-FIX BAL", md < 1e-12 and len(j) == max(len(old), len(r)), f"max|diff|={md:.3e} rows={len(j)}/{len(old)}")

# G2: cap <=1.6 all days (V3 SAFE + BAL)
for nm, TGT, THR in [('SAFE', 0.07, 0.04), ('AGGR', 0.091, 0.03)]:
    r, g, to = L.capped_book(L.NEW3, TGT, THR)
    gate(f"G2 cap V3 {nm}", float(g.max()) <= 1.6 + 1e-9, f"max={float(g.max()):.6f} mean={float(g.mean()):.4f}")
r, g, to = ((L.capped_book(L.NEW3, 0.07, 0.04)[0] + L.capped_book(L.NEW3, 0.091, 0.03)[0])/2, None, None)
# G3: margin charged strictly reduces ann
r0, _, _ = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.0)
r45, _, _ = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.045)
a0 = (1+r0).prod()**(252/len(r0)) - 1; a45 = (1+r45).prod()**(252/len(r45)) - 1
gate("G3 margin charged", a45 < a0 - 0.005, f"rate0={a0*100:.2f}% rate4.5={a45*100:.2f}% delta={(a45-a0)*100:.3f}pp")

# G4: cost ledger identity on capped book (independent recompute)
c = L.components13(L.NEW3, 0.07, 0.04)
r6, g6, to6 = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.0)
idx = c['b'].index
kappa = L.cap_factor(c['gross']).reindex(idx).fillna(1.0).clip(upper=1.0)
tw_c = c['tw'].reindex(idx).fillna(0)*kappa
dsc_c = (c['sc'].diff().abs()*0.5).reindex(idx).fillna(0)*kappa
reb_c = c['full'].mul(kappa, axis=0).diff().abs().sum(axis=1).reindex(idx).fillna(0)
htb_c = c['htb'].reindex(idx).fillna(0)*kappa/252
recon = (c['b']*c['sc']*kappa - (tw_c+dsc_c+reb_c)*6.4e-4 - htb_c).reindex(r6.index).dropna()
md = float((recon - r6.reindex(recon.index)).abs().max())
tot = float((tw_c+dsc_c+reb_c).sum())
gate("G4 cost identity", md < 1e-15, f"max|diff|={md:.3e} 1side_turn={tot:.1f}x cost={tot*6.4e-4*100:.2f}%cum")
print("GREEN-STAGE FAILURES:", fails if fails else "none — all gates GREEN")
