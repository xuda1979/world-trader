"""r6 extra: cross-sectional trailing-ON tilt. Unshifted signal = SR 1.34 (LOOKAHEAD TRAP: ON_t is the
last point of its own signal window). shift(1) -> SR 0.08. Oracle full-sample top-30 gross 13bp/d ~ cost.
VERDICT: FAIL; family cannot clear 12bp/d daily round trips at any selection strength."""
import sys; sys.path.insert(0,".")
from r6_lib import *
q=ON.where(ON.abs()<0.5)
for lag in (0,1):
    tr=q.rolling(252,min_periods=126).mean().shift(lag)
    g=q.where(tr.rank(axis=1,ascending=False)<=20).mean(axis=1).dropna()
    r=g-2*6/1e4
    print(f"lag{lag}: gross {g.mean()*1e4:.1f}bp/d net SR {r.mean()/r.std()*np.sqrt(252):.2f}")
mu=q.mean().sort_values(ascending=False)
print("oracle top-30 gross bp/d:",round((mu.head(30)*1e4).mean(),1))
