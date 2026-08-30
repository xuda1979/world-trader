"""Charter r6 idea 1: always-on overnight EW book, 298-panel, 12bp/d round trip. VERDICT: FAIL (cost-dead).
Gross ON premium 4.7bp/d < 12bp/d cost. Net SR -0.50. Breakeven cost ~2.3bp/side."""
import sys; sys.path.insert(0,".")
from r6_lib import *
held=pd.Series(True,index=days())
r=net_series(on_ew,held,COST_ON)
stats(r,"ON always pre-vt"); stats(util.vol_target(r,0.10),"ON always vt10")
for bps in (1,3,6):
    rr=net_series(on_ew,held,2*bps/1e4)
    print(f"cost {bps}bp/side: SR {rr.mean()/rr.std()*np.sqrt(252):.2f}")
