"""IDEA 1 (revised gates): rotation-scramble on chosen config + plateau check across the grid."""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from d1_lib import *
from idea1 import build, sp, ex, rfc   # reuse data + builder

# recompute grid SRs to define plateau around chosen (w=504,step=5,thr=1.0,mom)
grid={}
for w in (378,504):
    for step in (5,10):
        for thr in (0.5,1.0,1.5):
            net,sig=build(w,step,thr,'mom')
            grid[(w,step,thr)]=net.mean()/net.std()*np.sqrt(252)
print("neighborhood grid:", {k:round(v,2) for k,v in grid.items()})
chosen=grid[(504,5,1.0)]; peak=max(grid.values())
print(f"chosen {chosen:.2f} vs peak {peak:.2f} -> plateau pass={chosen>=0.8*peak}")

net,sig=build(504,5,1.0,'mom')
p,real=rotation_scramble(net,sig,ex.reindex(sig.index),rfc.reindex(sig.index),n=200,seed=1)
print(f"rotation scramble: real SR {real:.2f}, p={p:.3f} (pass if <=0.05)")
# subwindow check: campaign window 2008+
n08=net[net.index>='2008-09-01']
s=stats(n08); h1,h2=halves(n08)
print(f"2008+ subwindow: n={s['n']} SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% negy={s['negy']} worst={s['worst']:.1f}% H1={h1:.2f} H2={h2:.2f}")
