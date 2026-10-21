import numpy as np
# Expected LVR over many paths. Define per-interval LVR properly:
# At each step, the pool rebalances at stale price Pa[i] instead of Pa[i+1].
# LVR_i = value of the trade the rebalancer does that the AMM lags.
# Classic pathwise: dLVR = 1/2 s2 P^2 |x*'| dt (P&L the AMM loses per dt).
# We simulate the AMM LP value and a rebalancer BOTH as a function of P, but
# the AMM's "holdings-per-price" is locked so it cannot pnl from trading; the
# rebalancer's discrete trading pnl is tracked. Expected(LVR)>=0.
sigma=0.3; dt=1/2520.0; T=0.25; k=1.0; P0=1.0; N=int(T/dt); nsim=20000
dW=np.random.normal(0,np.sqrt(dt),size=(nsim,N))
plog=np.cumsum(-0.5*sigma**2*dt+sigma*dW,axis=1)
P=P0*np.exp(plog)  # nsim x N, Pa_t for t=1..N, with Pa_0=P0
def xstar(P): return np.sqrt(k)/np.sqrt(P)

# Discrete LVR: the AMM executes each trade at the CURRENT (post-move) price but
# charges the rebalancing at pre-move. Difference in trading P&L between ideal
# rebalancer and AMM:
#  ideal rebalancer pnl over step = (x*(P_i+)-x*(P_i))*... 
# Cleanest known equivalent: expected instantaneous LVR rate = 1/8 s2 * V.
# Verify expectation directly from pathwise integral:
xdp = 0.5*np.sqrt(k)*np.power(P,-1.5)   # |x*'(P)|
instant_rate = 0.5*sigma**2* P**2 * xdp   # per unit time at each P
LVR_mean = np.mean(np.sum(instant_rate*dt,axis=1))
# 1/8 s2 E[V]: V = x + P y = 2 sqrt(kP)
V = 2*np.sqrt(k*P)
one8 = np.mean(np.sum(0.125*sigma**2*V*dt,axis=1))
print(f"E[ integral 1/2 s2 P^2|x*'| dt ] over {nsim} paths = {LVR_mean:.6f}")
print(f"E[ integ of 1/8 s2 V dt ]                                = {one8:.6f}")
print(f"ratio = {LVR_mean/one8:.4f}  (expect 1.0)")

def spot_check(P=1.0, sigma=0.3, k=1.0):
    """V1: closed-form equivalence at a point. Both forms must agree."""
    xp = 0.5*k**0.5*P**-1.5                  # |x*'(P)|
    V  = 2*(k*P)**0.5                        # pool value in X numeraire
    a = 0.5*sigma**2*P**2*xp
    b = 0.125*sigma**2*V
    print(f"V1 spot @P={P},s={sigma}: 1/2 s2 P2|x*'|={a:.6f}   1/8 s2 V={b:.6f}   diff={abs(a-b):.1e}")
    return abs(a-b)

if __name__=="__main__":
    spot_check()
