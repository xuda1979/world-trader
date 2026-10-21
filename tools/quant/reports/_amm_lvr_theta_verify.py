import numpy as np
# Correct funding/theta identity for CPMM: funding_rate = 0.5 s2 P2 |x*'(P)| == LVR rate
# using |x*'| = 0.5 sqrt(k) P^-1.5  (the hedge-ratio gamma), NOT V''(P).
k=1.0; s=0.3; s2=s*s
P=np.array([0.5,0.8,1.0,1.25,2.0])
xdp = 0.5*np.sqrt(k)*np.power(P,-1.5)         # |x*'(P)|
lvr = 0.5*s2*P**2*xdp                          # LVR rate
red = 0.25*s2*np.sqrt(k)*np.sqrt(P)            # closed form 1/4 s2 sqrt(k) sqrt(P)
# naive V''(P) gamma (wrong object):
Vpp = 0.75*np.sqrt(k)*P**-2.5 + 0.75*np.sqrt(k)*P**-0.5
naive = 0.5*s2*P**2*Vpp
print("P    | LVR(id)    | closed 1/4 s2 sqrt(kP) | naive-theta  | match")
for i in range(len(P)):
    print(f"{P[i]:.2f} | {lvr[i]:.5f} | {red[i]:.5f}            | {naive[i]:.5f}    | {abs(lvr[i]-red[i])<1e-9}")
print("\n=> LVR == funding = 1/4 s2 sqrt(kP) (via |x*'| hedge gamma); naive V''(P) theta gives wrong magnitude.")
