"""Charter r6 idea 2: overnight only in turn-of-month windows. VERDICT: FAIL (all windows net-negative)."""
import sys; sys.path.insert(0,".")
from r6_lib import *
tdom,tend=tdom_masks()
for name,mask in [("last3+first2",(tend<=3)|(tdom<=2)),("last2+first1",(tend<=2)|(tdom<=1)),
                  ("last1+first1",(tend<=1)|(tdom<=1)),("last5+first3",(tend<=5)|(tdom<=3)),
                  ("last3td",(tend<=3)),("first2td",(tdom<=2)),("last1td",(tend<=1))]:
    stats(net_series(on_ew,mask,COST_ON),f"TOM {name}")
