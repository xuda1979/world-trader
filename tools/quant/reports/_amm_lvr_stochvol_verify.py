import numpy as np
np.random.seed(7)
dt=1/3650.0; T=4.0; N=int(T/dt); nsim=8000
vol0=0.30; kapp=3.0; xi=0.22
dW=np.random.randn(nsim,N); dWv=np.random.randn(nsim,N)
v=np.full(nsim,vol0)
lvr_all=np.zeros((nsim,N)); vpath=np.zeros((nsim,N))
# widen xi to create more pronounced tails -> insurance value more visible
xi=0.35; kapp=2.5
dWv=np.random.randn(nsim,N)
v=np.full(nsim,vol0)
for t in range(N):
    dv=-kapp*(v-vol0)*dt + xi*v*np.sqrt(dt)*dWv[:,t]
    v=np.maximum(v+dv,0.01); vpath[:,t]=v
    lvr_all[:,t]=0.125*v*v*dt
tot_lvr=lvr_all.sum(axis=1)   # total LVR per path over 4y (always-on)
# kill-switch total LVR per path
for sstar in [None,0.32,0.28]:
    mask=np.ones((nsim,N),bool) if sstar is None else (vpath<=sstar)
    tl=(lvr_all*mask).sum(axis=1)
    print(f"{'always-on' if sstar is None else f's*={sstar}':10s}: "
          f"mean LVR={tl.mean():.4f}  95th-pct={np.quantile(tl,.95):.4f}  "
          f"99th-pct={np.quantile(tl,.99):.4f}  max={tl.max():.4f}  "
          f"std={tl.std():.4f}")
