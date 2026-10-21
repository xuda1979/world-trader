#!/usr/bin/env python3
"""AMM LP — compute NET RETURN & SHARPE for a given pool configuration.
Produces the decision table "how much can we make" (fees - LVR - staging - re-bridging),
annualized, with Sharpe. Companion to AMM_LVR_RETURNS.md.
Run: python3 _amm_lvr_ret_sharpe.py
"""
import numpy as np
dt=1/(365*24); YR=int(1/dt)

def book(h, sigma, fee_rate, turnover, years=4, nsim=4000):
    """Net annual return / unit capital and its std (=> Sharpe)."""
    nets=[]
    for i in range(nsim):
        net=0.0
        for yr in range(years):
            lg=np.cumsum(-0.5*sigma**2*dt+sigma*np.sqrt(dt)*np.random.randn(YR))
            inside=np.abs(lg)<=np.log(1+h); vi=np.abs(lg[inside])
            fees=fee_rate*turnover*(vi.mean() if vi.size else 0)
            lvr=0.125*sigma**2*inside.mean()
            staging=fee_rate*turnover*((~inside).mean())*0.5
            cross=((~inside)[1:]&inside[:-1]).sum()+(inside[1:]&(~inside)[:-1]).sum()
            rebr=cross*0.0003
            net+=(fees-lvr-staging-rebr)
        nets.append(net/years)
    nets=np.array(nets)
    return nets.mean(), nets.std(ddof=1), nets

if __name__=="__main__":
    print("Net annual return & Sharpe (3bp fees, 300x turnover):")
    print(f"{'h':>5}{'sigma':>7}{'net':>8}{'vol':>7}{'sharpe':>8}")
    for h in [0.05,0.15,0.30,0.50]:
        for sig in [0.15,0.30]:
            m,s,n=book(h,sig,0.0003,300)
            print(f"{h:5.2f}{sig:7.2f}{m*100:7.2f}%{s*100:6.2f}%{m/s:8.2f}")
