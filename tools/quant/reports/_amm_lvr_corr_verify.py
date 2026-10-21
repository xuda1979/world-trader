import numpy as np
# Correlation/contagion study: aggregate LVR across N pools.
# Naive view: pools independent -> aggregate LVR = sum of per-pool E[LVR] (diversifies).
# Correlated-vol view: a common vol-shock factor hits all pools -> aggregate LVR variance
# and tail blow up. Quantify understatement of (a) mean aggr LVR, (b) tail aggr LVR.
np.random.seed(3)
T=3.0; nsim=4000; NPOOL=5
freq=252; N=int(T*freq)  # daily-ish steps
dt=1.0/freq
vol0=0.25; kapp=3.0; xi=0.25

# Two scnarios:
#  A) INDEPENDENT vol: each pool its own MR vol, shocks uncorrelated
#  B) CORRELATED: common factor drives all pools' vol together (rho high)
def gen(rho):
    lvr=np.zeros((nsim,NPOOL))
    for i in range(nsim):
        v=np.full(NPOOL,vol0)
        zc=np.random.randn(N)                     # common shock
        ze=np.random.randn(N,NPOOL)               # idiosyncratic
        za=np.random.randn(N,NPOOL)               # price shocks
        for t in range(N):
            c=np.sqrt(rho)*zc[t]+np.sqrt(1-rho)*ze[t,:]
            v=np.maximum(v + (-kapp*(v-vol0)*dt + xi*v*np.sqrt(dt)*c),0.01)
            lvr[i,:]+= 0.125*v*v*dt
    return lvr
for rho in [0.0,0.3,0.6,0.9]:
    lvr=gen(rho)
    aggr=lvr.sum(axis=1)
    # naive independent aggregate: sum of per-pool means (diversify, low var)
    naive_var=lvr.var()*NPOOL          # if independent
    print(f"rho={rho:.1f}: aggr mean={aggr.mean():.4f}  aggr std={aggr.std():.4f}  "
          f"99th={np.quantile(aggr,.99):.4f}  max={aggr.max():.4f}  "
          f"std/mean={aggr.std()/aggr.mean():.3f}  (independent-implied std={np.sqrt(naive_var):.4f})")
