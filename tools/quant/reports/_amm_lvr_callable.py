#!/usr/bin/env python3
"""AMM LVR fee-breakeven calculator.
Converts the AMM/LVR math into per-pair sizing numbers.

Core relations (see AMM_LVR_MATHEMATICS.md §1-7):
  full-range CPMM:  LVR rate = (1/8) s2 * V
  concentrated v3 :  LVR rate = (1/4) s2 * L * sqrt(P)
  break-even fee-turned (fraction of capital per yr) >= LVR/V
Usage:
  python3 _amm_lvr_callable.py
"""
import numpy as np

def lvr_full(sigma, V):
    return 0.125*sigma**2*V

def lvr_concentrated(sigma, L, P):
    return 0.25*sigma**2*L*np.sqrt(P)

def breakeven(sigma_ann, range_=(None,None)):
    """Return LVR/V per year (i.e. min fee-as-%of-capital/yr to break even).
    range_=None -> full range CPMM; else (Pa,Pb) concentrated around P=1 with L=1."""
    s2 = sigma_ann**2
    P=1.0
    if range_[0] is None:
        V=2.0
        lvr=lvr_full(sigma_ann,V)
    else:
        Pa,Pb=range_
        L=1.0
        x=L/np.sqrt(P)-L/np.sqrt(Pb); y=L*(np.sqrt(P)-np.sqrt(Pa)); V=x+y*P
        lvr=lvr_concentrated(sigma_ann,L,P)
    return lvr/V, lvr, V

if __name__=="__main__":
    print("=== LVR fee-breakeven (min fee as % of capital/yr to stay flat vs LVR) ===\n")
    for sig in [0.1,0.3,0.5,1.0]:
        print(f"sigma={sig*100:.0f}%/yr :")
        for name,rn in [("full-range",(None,None)),("[0.5,2.0]",(0.5,2.0)),
                        ("[0.8,1.25]",(0.8,1.25)),("[0.9,1.1]",(0.9,1.1)),
                        ("[0.99,1.01]",(0.99,1.01))]:
            frac,lvr,V=breakeven(sig,rn)
            # translate to a simple 0.05% (5bp) per-trade fee tier: need turnover nu s.t.
            # f*nu_many > frac  =>  nu > frac/f   (trades/yr per unit capital)
            f=0.0005
            nu=frac/f
            print(f"   {name:12s} LVR/V={frac*100:8.2f}%/yr   equiv turnover@5bp fees: {nu:9.1f}x/yr  (V={V:.3f})")
        print()
