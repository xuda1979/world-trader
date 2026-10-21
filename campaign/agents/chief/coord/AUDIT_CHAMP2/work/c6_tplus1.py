#!/usr/bin/env python3
"""AUDIT_CHAMP2 C6: T+1 no-lookahead quantification (pure numpy row ops).
(1) HONEST re-accounting: PnL(t)=w(t-1).r(t) with exact self-financing drift + true trade turnover.
(2) PERTURBATION: real weights x shifted(+1) returns -> SR collapse test.
(3) compounded vs cumsum MaxDD (resolves -6.80 vs -6.94 discrepancy)."""
import numpy as np, pandas as pd
src = open('/Users/daxu/software/world-trader/campaign/agents/chief/coord/AUDIT_CHAMP2/work/indep_rebuild.py').read()
exec(src.split('# --- byte compare')[0])

def stats(r, tag):
    r = pd.Series(r).dropna()
    yrs = (1+r).groupby(r.index.year).prod()-1
    ann = (1+r).prod()**(252/len(r))-1
    sr = r.mean()/r.std(ddof=1)*np.sqrt(252)
    cs = r.cumsum(); mdd_cs = (cs-cs.cummax()).min()
    cum = (1+r).cumprod(); mdd_cp = ((cum-cum.cummax())/cum.cummax()).min()
    print(f"{tag}: ann={ann:.4%} SR={sr:.3f} MDDcumsum={mdd_cs:.4%} MDDcomp={mdd_cp:.4%} "
          f"neg={int((yrs<0).sum())}/{len(yrs)} worst={yrs.min():.4%}")
    return ann, sr, mdd_cs, mdd_cp

stats(net, "BUILDER w(t).r(t):")

# (1) honest lag-1 re-accounting, fully self-financing
R = filled.values                       # (T,K) sleeve returns
W = Wg.values                           # (T,K) builder weights
Wl = np.vstack([np.zeros((1, W.shape[1])), W[:-1]])   # w(t-1)
p_h = (R*Wl).sum(axis=1)                # honest daily port return
denom = (1.0 + p_h)[:, None]
W_drift = Wl*(1.0+R)/denom              # drifted from-weights (gross preserved 1:1)
to_h = np.abs(W - W_drift).sum(axis=1)  # true one-side trade at close t
to_h[0] = W[0].sum()                    # day-0 initial buy-in at full gross
net_h = pd.Series(p_h - to_h*BPS/1e4 - np.maximum(GEAR-1,0)*RATE/252, index=df.index)
gross_h = np.abs(Wl).sum(axis=1)
stats(net_h, "HONEST  w(t-1).r(t):")
print(f"honest turnover={to_h.mean()*252*BPS:.4f}bps/yr vs builder-charged {to.mean()*252*BPS:.4f}bps/yr")
print(f"honest gross: mean={gross_h.mean():.10f} max={gross_h.max():.12f} over={int((gross_h>1.6+1e-9).sum())}")
a_b = stats(net, "builder(repr)")[:1][0]; a_h = stats(net_h, "honest(repr)")[:1][0]
print(f"ANN DELTA honest-vs-builder: {a_h:.4%} vs {a_b:.4%}  (delta {a_h-a_b:+.4%})")
sr_b = net.dropna(); sr_h = net_h.dropna()
print(f"SR DELTA: builder {sr_b.mean()/sr_b.std(ddof=1)*np.sqrt(252):.3f} honest {sr_h.mean()/sr_h.std(ddof=1)*np.sqrt(252):.3f}")
yrs_h = (1+sr_h).groupby(sr_h.index.year).prod()-1
print(f"HONEST neg years: {int((yrs_h<0).sum())}/{len(yrs_h)} worst={yrs_h.min():.4%}")
cs_h = sr_h.cumsum(); print(f"HONEST MDDcumsum={(cs_h-cs_h.cummax()).min():.4%}  MDDcomp={((1+sr_h).cumprod().pipe(lambda c: ((c-c.cummax())/c.cummax())).min()):.4%}")

# (2) perturbation: same weights, returns shifted +1 (breaks any same-day signal exploitation)
Rp = np.vstack([R[1:], np.zeros((1, R.shape[1]))])    # r'(t) = r(t+1)
p_p = (Rp*W).sum(axis=1)
net_p = pd.Series(p_p - to*BPS/1e4 - np.maximum(GEAR-1,0)*RATE/252, index=df.index).dropna()
print(f"PERTURB weights x r(t+1): SR={net_p.mean()/net_p.std(ddof=1)*np.sqrt(252):.3f} ann={(1+net_p).prod()**(252/len(net_p))-1:.4%}")
