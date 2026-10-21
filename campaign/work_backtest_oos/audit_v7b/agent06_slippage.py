import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"06_slippage_mc","checks":[]}
print("=== 06 EXECUTION SLIPPAGE MC (adverse, on monthly trade notional) ===")
rng=np.random.default_rng(7)
ok=True
for slip in [0.001,0.0025,0.005]:
    costs=[]
    n1=AGG.notional_1leg; n2=AGG.notional_extra_leg
    for _ in range(500):
        k=rng.random(len(AGG))
        drag=((n1+n2)*(slip*(0.5+k))).resample("YE").sum()  # annual slip drag path
        costs.append(drag.mean())
    drag_mu=np.mean(costs)
    n=net_series(bps=6.4,oos=True)-slip*((n1+n2).reindex(net_series(bps=6.4,oos=True).index).fillna(0))
    a=sr(n)>2.5 and ann(n)>10
    ok&=a
    R["checks"].append({"check":f"slip {slip*1e4:.0f}bp","status":"PASS" if a else "FAIL",
        "detail":f"ann={ann(n):.2f}% SR={sr(n):.3f} avgExtraDrag={drag_mu*100:.3f}pp/yr"})
    print(f"slip {slip*1e4:4.0f}bp: net ann={ann(n):6.2f}% SR={sr(n):.3f}  (extra drag ~{drag_mu*100:.3f}pp/yr)")
R["overall"]="PASS" if ok else "FAIL"
json.dump(R,open("agents/agent06_report.json","w"),indent=2)
