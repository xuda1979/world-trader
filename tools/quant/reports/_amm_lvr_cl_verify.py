import numpy as np
# LVR per unit of deployed capital as a function of range width (narrower = more LVR/capital)
s2=0.09
# Full-range (0,inf) x*y=k baseline for reference
k=1.0; Pref=1.0
Vfull=2*np.sqrt(k*Pref)
lvrfull=0.125*s2*Vfull   # = 1/4 s2 sqrt(k) sqrt(P) at P=1 with L=sqrt(k)... =0.0225
print(f"Full-range baseline: V={Vfull:.3f}, LVR_rate={lvrfull:.4f}, LVR/V={lvrfull/Vfull:.4f}")
print()
print("Concentrated (Uniswap v3) around P=1, same L=1:")
for (Pa,Pb) in [(0.5,2.0),(0.8,1.25),(0.9,1.1),(0.99,1.01)]:
  L=1.0; P=1.0
  x=L/np.sqrt(P)-L/np.sqrt(Pb); y=L*(np.sqrt(P)-np.sqrt(Pa)); V=x+y*P
  lvr=0.25*s2*L*np.sqrt(P)   # rate per unit time
  print(f"  range [{Pa},{Pb}]: capital V={V:.4f}, LVR_rate={lvr:.5f}, LVR/V per yr={lvr/V:.4f} "
        f"({lvr/V*100:.1f}%/yr of capital), 1/(LVR/V)={V/lvr:.1f} yrs to bleed out")
