import numpy as np, pandas as pd, pickle
ROOT="/Users/daxu/software/world-trader"
st = pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))
BAL, A, B = st['BAL'], st['A'], st['B']

def yearly(r, label):
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    print(f"--- {label} yearly:")
    for y, v in yr.items():
        n = (r.index.year==y).sum()
        print(f"  {y}: {v*100:8.2f}%  (n={n}) {'  NEG' if v<0 else ''}")
    return yr

yrB = yearly(BAL, "FIX BALANCED full span (as committed)")
w = BAL[(BAL.index>='2008-01-01')&(BAL.index<='2026-07-31')]
yrw = w.groupby(w.index.year).apply(lambda x:(1+x).prod()-1)
print(f"comparable window 2008-01-01..2026-07-31: neg {(yrw<0).sum()}/{yrw.size}  worst {yrw.min()*100:.2f}%  ann(geo) {((1+w).prod()**(252/len(w))-1)*100:.2f}%")
# OOS 2017+ arithmetic ann on comparable window
o = w[w.index>='2017-01-01']
print(f"comparable-window OOS17+ arith ann: {o.mean()*252*100:.2f}%  SR_d {o.mean()/o.std()*np.sqrt(252):.3f}")
o2 = BAL[BAL.index>='2017-01-01']
print(f"full-span OOS17+ arith ann: {o2.mean()*252*100:.2f}%")
# MDD on comparable window
eq=(1+w).cumprod(); print(f"comparable-window MDD: {(eq/eq.cummax()-1).min()*100:.2f}%")
