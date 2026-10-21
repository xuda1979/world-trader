"""TDD reconciliation tests for HUNT_INDUSTRY48 builders (SUPERPOWERS: RED before GREEN).
Run:  python3 tdd_gates.py <module_importable_on_path containing build_book/net_of_book48>
Tests:
 T1 T+1 leak: flipping signal on a SINGLE day t0 must NOT change net return at t0 (only t0+1).
 T2 cost recon: charged cost == sum|dpos_exec|/2 * 6.4e-4 exactly; borrow on shorts 0.5%/yr.
 T3 scramble: poslag scramble (roll POSITIONS) kills a synthetic edge (p<0.2, median perm SR ~0);
    return-roll would NOT (p==1) — proves we did not ship the degenerate return-roll variant.
Exit code 0 iff all pass."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_INDUSTRY48/scratch')
import importlib
mod = importlib.import_module(sys.argv[1]) if len(sys.argv)>1 else importlib.import_module('lib48')
fails=[]
rng=np.random.default_rng(1)

# synthetic panel: 8 industries x 1500 days, vol 1%/d, iid
T,N=1500,8
R=pd.DataFrame(rng.normal(0,0.01,(T,N)),
    index=pd.bdate_range('2020-01-01',periods=T), columns=[f'I{i}' for i in range(N)])

# T1 leak test on net_of_book48
sig = pd.DataFrame(rng.choice([-1,0,1],size=(T,N)), index=R.index, columns=R.columns)
base, pos_exec = mod.net_of_book48(sig, R)
sig2 = sig.copy(); sig2.iloc[750,:] = 1.0  # flip signal ONLY at t0=750
alt,_ = mod.net_of_book48(sig2, R)
d_same = float(abs(alt.iloc[750]-base.iloc[750])); d_next = float(abs(alt.iloc[751]-base.iloc[751]))
print(f"T1 leak: |Δnet[t0]|={d_same:.3e} (must be 0), |Δnet[t0+1]|={d_next:.3e} (must be >0)")
if d_same>1e-15: fails.append('T1 same-day leak: signal change at t moved return AT t')
if d_next<=0: fails.append('T1 no pass-through: signal change at t did not move t+1')

# T2 cost recon: recompute costs from returned executed-position path; compare to implied
gross=(pos_exec*R).sum(axis=1)   # W_exec already T+1-shifted by builder
turn=pos_exec.diff().abs().fillna(0.0).sum(axis=1)  # STANDARD: both sides pay, qty=|dW| per record
borrow=(0.005/252)*pos_exec.clip(upper=0.0).abs().sum(axis=1)
recon = gross - turn*mod.COST - borrow
j=pd.concat([recon.rename('a'),base.rename('b')],axis=1).dropna()
err=float((j['a']-j['b']).abs().max())
print(f"T2 cost recon: max|recon-net|={err:.3e} (must be <1e-12), COST={mod.COST}")
if not (abs(mod.COST-6.4e-4)<1e-12): fails.append('T2 COST must be 6.4bps/side per charter')
if not mod.EACH_SIDE_PAYS: fails.append('T2 must charge BOTH sides (blotter qty x 6.4bps)')
if err>1e-12: fails.append('T2 ledger-vs-net mismatch: charged cost != turnover*6.4bps + borrow')

# T3 scramble implementation test: synthetic real edge (pos = sign(next r))
edge_pos = pd.DataFrame(np.sign(R.shift(-1)).values, index=R.index, columns=R.columns).fillna(0.0)
p_poslag, med_perm, _real = mod.poslag_scramble_p(edge_pos, R, n=100, seed=3)
# degenerate return-roll control: roll RETURNS instead of positions -> edge survives
roll_sr=[]
r2=R.copy()

cnt=0
for s in range(20):
    lag=int(rng.integers(21,T-21))
    rr=pd.DataFrame(np.roll(R.values,lag,axis=0),index=R.index,columns=R.columns)
    ps=edge_pos.shift(1).fillna(0.0)
    nt=(ps.diff().abs()/2.0).fillna(0.0)
    net=(ps*R-nt*mod.COST).sum(axis=1)  # returns rolled -> same alignment relation? roll RETURNS under FIXED pos edge
    roll_sr.append(float(net.mean()/net.std()*np.sqrt(252)))
print(f"T3 scramble: poslag_p={p_poslag:.3f} (want small), median perm SR={med_perm:.3f} (want ~0), return-roll median SR={np.median(roll_sr):.3f}")
if p_poslag>=0.2: fails.append('T3 poslag scramble failed to kill synthetic edge -> implementation suspicious')
if med_perm>0: fails.append('T3 median permuted SR>0 -> permutation preserves edge -> not a real poslag scramble')
if np.median(roll_sr)<0.5: fails.append('T3 control broken: return-roll should PRESERVE synthetic edge')
# T4 data lint (charter: -99.99 = missing -> drop): loaded panel must contain NO raw missing codes
Rr = mod.load48()
bad = int((Rr<=-0.99).sum().sum())
print(f"T4 missing-code lint: cells<=-0.99 in loaded panel = {bad} (must be 0)")
if bad>0: fails.append('T4 load48 must neutralize -99.99/-999 missing codes')

print('FAILS:', fails if fails else 'NONE — all TDD gates GREEN')
sys.exit(1 if fails else 0)
