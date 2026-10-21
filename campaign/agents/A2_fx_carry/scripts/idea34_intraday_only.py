"""Charter r6 idea 3: intraday-only book. VERDICT: FAIL net (gross +3.1bp/d positive every 5y window,
but < 12bp/d cost -> net SR -1.43). Gross-positive ID premium (mildly contradicts 'negative intraday' prior)
is the finding; not tradable at campaign costs."""
import sys; sys.path.insert(0,".")
from r6_lib import *
held=pd.Series(True,index=days())
r=net_series(id_fwd,held,COST_ID)
stats(r,"ID only pre-vt")
for a,b in [("2007","2012"),("2012","2017"),("2017","2022"),("2022","2027")]:
    s=id_ew.loc[a:b].dropna(); print(f"  gross ID {a}-{b}: {s.mean()*1e4:+.1f}bp/d")
