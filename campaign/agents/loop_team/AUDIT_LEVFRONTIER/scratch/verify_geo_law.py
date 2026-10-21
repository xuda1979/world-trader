"""Root-cause verification: which ann convention + does geo identity hold on REAL path?"""
import sys
sys.path.insert(0, 'campaign/scripts'); sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L

rA, gA, _ = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.045)
rB, gB, _ = L.capped_book(L.NEW3, 0.091, 0.03, rate=0.045)
old = ((rA+rB)/2).dropna(); old = old[old.index >= '2008-03-31']
mu = old.mean()*252; sig = old.std()*np.sqrt(252); sr = mu/sig
geo = ((1+old).prod()**(252/len(old))-1)
pred = np.exp(sr*sig - sig**2/2) - 1
print(f"REAL capped V3 BAL+margin: mu_arith {mu*100:.3f}% sigma {sig*100:.3f}% SR {sr:.4f}")
print(f"ann_geo measured {geo*100:.3f}%  vs exp(SR*sig-sig^2/2)-1 = {pred*100:.3f}%  diff {(geo-pred)*100:+.3f}pp")

u = ((L.committed_replica13(L.NEW3, 0.07, 0.04) + L.committed_replica13(L.NEW3, 0.091, 0.03))/2).dropna()
uu = u[u.index>='2008-03-31']
mu2 = uu.mean()*252; sig2 = uu.std()*np.sqrt(252)
geo2 = ((1+uu).prod()**(252/len(uu))-1)
law2 = (np.exp(mu2-sig2**2/2)-1)
print(f"UNCAPPED V3 BAL: mu {mu2*100:.2f}% sig {sig2*100:.2f}% SR {mu2/sig2:.3f} ann_geo {geo2*100:.2f}% law {(np.exp(mu2-sig2**2/2)-1)*100:.2f}%")

r0A,_,_ = L.capped_book(L.NEW3,0.07,0.04,rate=0.0); r0B,_,_ = L.capped_book(L.NEW3,0.091,0.03,rate=0.0)
r0 = ((r0A+r0B)/2).dropna(); r0 = r0[r0.index>='2008-03-31']
print(f"mu arith: rate0 {r0.mean()*252*100:.3f}% rate4.5 {mu*100:.3f}% diff {(mu-r0.mean()*252)*100:.3f}pp (margin mean 2.509/yr)")
