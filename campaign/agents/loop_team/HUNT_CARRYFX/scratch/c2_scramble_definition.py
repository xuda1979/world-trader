"""RESOLVE THE SCRAMBLE-DEFINITION DISCREPANCY.
Charter gate: '200x block-scramble (10-day blocks), p<0.05 that SR<=0'.
Tail A (operational, VET G6a): p = frac(bootstrap SR <= 0). Small p = robust positive mean.
Tail B (FXMICRO-suspected):   p = frac(bootstrap SR >= real SR). ~0.5 for EVERYTHING.
Controls: (1) white-noise SR~1.9 (diffuse real edge)  (2) 60-day-episode artifact SR~1.9.
Gate has power iff it rejects (2) and passes (1)."""
import numpy as np
def sr(x): return x.mean()/x.std()*np.sqrt(252)
rng0=np.random.default_rng(7)
n=1749
# control 1: diffuse iid edge SR~1.9
x1=rng0.normal(4.75e-4,3.97e-3,n); x1=x1*sr(x1)**-1*0  # noop
x1=rng0.normal(0,4.0e-3,n); x1+= (1.9/np.sqrt(252))*x1.std()  # shift mean to SR 1.9
def set_sr(x,target):
    return x - x.mean() + target*x.std()/np.sqrt(252)
x1=set_sr(x1,1.9/s)  if False else x1
x1=set_sr(np.asarray(x1),1.9)
# control 2: single 60-day episode
x2=np.zeros(n); e=rng0.normal(0.016,0.02,60); x2[500:560]=e; x2=set_sr(x2,1.9)
for tag,x in [("diffuse SR1.9",x1),("60d-episode SR1.9",x2)]:
    real=sr(x); B=10; nb=n//B
    out={}
    for seed in range(3):
        rng=np.random.default_rng(seed)
        starts=rng.integers(0,n-B,size=(2000,nb))
        srs=[]
        for row in starts[:2000]:
            xb=np.concatenate([x[s:s+B] for s in row])[:n]
            srs.append(sr(xb))
        srs=np.array(srs)
        pA=float((srs<=0).mean()); pB=float((srs>=real).mean())
        out[seed]=(round(pA,4),round(pB,4))
    print(f"{tag}: real SR={real:.2f} | per-seed (pA=SR<=0, pB=SR>=real): {out}")
