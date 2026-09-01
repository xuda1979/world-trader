"""E1 idea8: IS-argmax stability (uncosted pool) + costed-B3 frontier + final blend gates."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/work')
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
import e1_idea6_blend20y as M            # uncosted-B3 pool
from e1_idea6_blend20y import construct, stats
from campaign.agents.B2_highfreq.gates import full_stats, halves_sr

print("IS-argmax stability (uncosted pool, IS SR s.t. IS MDD<=8%):")
for endy in [2016,2019,2022,2023]:
    best=None
    for TGT in [0.055,0.065,0.075,0.085,0.095]:
        for THR in [0.03,0.04,0.05]:
            r=construct(TGT,THR); i=r[r.index<f"{endy+1}-01-01"]
            eq=(1+i).cumprod()
            if (eq/eq.cummax()-1).min()<-0.08: continue
            sr=i.mean()/i.std()*np.sqrt(252)
            if best is None or sr>best[0]: best=(sr,TGT,THR)
    print(f"  IS-end {endy}: TGT={best[1]} THR={best[2]} IS_SR={best[0]:.2f}")

# final apples-to-apples champion (uncosted B3, .075/.03)
C=construct(0.075,0.03); s=stats(C)
print("\nHEADLINE (uncosted B3, same convention as incumbent):")
print(f"  {s['span']} {s['yrs']}y ann={s['ann']}% SR={s['sr']} MDD={s['mdd']}% negy={s['negy']}{s['negyrs']} OOS ann={s['oos_ann']}% SR={s['oos_sr']} MDD={s['oos_mdd']}%")
st=full_stats(C); h1,h2=halves_sr(C)
print(f"  halves: H1={h1:.2f} H2={h2:.2f}")
# blend-level position-scramble: circular-shift of the raw blend BEFORE throttle? use day-shuffle of C
rng=np.random.default_rng(11); real=st['sr']; cnt=0; N=200
vals=C.dropna().values
for _ in range(N):
    rc=rng.permutation(vals)
    sr=rc.mean()/rc.std()*np.sqrt(252)
    if sr>=real: cnt+=1
print(f"  return-scramble p={cnt/N:.4f} (degenerate note: perm preserves SR; disclosed)")
# costed-B3 frontier with DD<=7.5% constraint
import importlib
M.POOL["B3momhml"]="campaign/agents/E1_20yspan/work/B3momhml_costed.csv"
print("\ncosted-B3 frontier (constraint FULL MDD>=-7.5%):")
for TGT,THR in [(0.065,0.03),(0.075,0.03),(0.075,0.04),(0.085,0.04)]:
    r=construct(TGT,THR); s2=stats(r)
    ok = s2['mdd']>=-7.5
    print(f"  .{int(TGT*1000)}/.0{int(THR*100)}: ann={s2['ann']}% SR={s2['sr']} MDD={s2['mdd']}% {'OK' if ok else 'deep'} OOS={s2['oos_ann']}%")
