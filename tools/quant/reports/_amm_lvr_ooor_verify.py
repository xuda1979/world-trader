#!/usr/bin/env python3
"""AMM LVR - out-of-range state verification (Section 12 of AMM_LVR_MATHEMATICS.md).
Quantifies: (a) fraction of time a concentrated LP is in/out of its band under GBM,
(b) re-bridging event count, and (c) the total-cost-optimal band width that balances
in-range LVR, out-of-range staging and re-bridge adverse selection.
Run: python3 _amm_lvr_ooor_verify.py
"""
import numpy as np
from scipy import interpolate
dt=1/(365*24); T=1.0; N=int(T/dt)

def metrics(h,sig,mu,nsim=8000):
    nfit=0; nout=0; reb=0
    for i in range(nsim):
        logs=np.cumsum((mu-0.5*sig**2)*dt+sig*np.sqrt(dt)*np.random.randn(N))
        inside=np.abs(logs)<=np.log(1+h)
        nfit+=inside.sum(); nout+=(~inside).sum()
        reb+=(((~inside)[1:])&(inside[:-1])).sum()
    return nfit/N/nsim, nout/N/nsim, reb/nsim

if __name__=="__main__":
    print("In/out-of-range occupation (sigma=0.30, mu=0):")
    for h in [0.05,0.10,0.20,0.30,0.50]:
        fi,o,reb=metrics(h,0.30,0.0)
        print(f"  h={h:<5}: in={fi*100:5.1f}%  out={o*100:5.1f}%  re-bridge={reb:6.2f}/yr")
    print("Total-cost-optimal band search:")
    Hs=[0.05,0.1,0.2,0.3,0.5]; fin,hou,reb=[],[],[]
    for h in Hs:
        fi,o,r=metrics(h,0.30,0.0); fin.append(fi); hou.append(o); reb.append(r)
    def C(h):
        fi=np.interp(h,Hs,fin); o=np.interp(h,Hs,hou); r=np.interp(h,Hs,reb)
        base=np.interp(h,[0.05,0.1,0.2,0.3,0.5],[0.030,0.093,0.30,1.1,1.6])
        return 0.0225*fi/base + 0.15*o + 0.002*r
    best=min((C(h),h) for h in np.linspace(0.05,0.5,60))
    print(f"  optimal half-width h*={best[1]:.3f} (band [{1/(1+best[1]):.2f},{1+best[1]:.2f}]), total cost={best[0]:.4f}/yr")
