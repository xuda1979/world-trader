"""Is the returns-block-scramble a NO-OP? SR is permutation-invariant, so a block-permutation
of the RETURN series leaves SR identical up to fp error. If so, any p-value from it is
tie-noise -- which would explain FXMR3's recorded p 0.61-0.85 / 0.50 'failures'."""
import numpy as np, pandas as pd
r=pd.read_csv("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv",
              index_col=0,parse_dates=True)["ret"].dropna()
def sr(x): return x.mean()/x.std()*np.sqrt(252)
x=r.values; n=len(x); B=10; nb=n//B
real=sr(r)
rng=np.random.default_rng(0)
starts=rng.integers(0,n-B,size=(200,nb))
same=0; ge=0; diffs=[]
for row in starts:
    xb=np.concatenate([x[s:s+B] for s in row])
    xb=np.concatenate([xb,x[nb*B:]])[:n]
    s=sr(pd.Series(xb))
    diffs.append(abs(s-real))
    if abs(s-real)<1e-9: same+=1
    if s>=real: ge+=1
print(f"real SR={real:.10f}")
print(f"block-perm of RETURNS: identical(SR) in {same}/200 reps (|dSR|<1e-9), p(perm>=real)={ge/200:.3f}")
print(f"max |dSR| = {max(diffs):.2e}  <- pure fp tie-noise => the test is VACUOUS on returns")
