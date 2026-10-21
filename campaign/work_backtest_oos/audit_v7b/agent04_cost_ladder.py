import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"04_cost_ladder","checks":[]}
print("=== 04 ALL-IN COST LADDER (incl 2nd-leg surcharge) OOS ===")
print(f"{'bps':>5} {'ann':>8} {'SR':>7} {'DD':>8}")
ok=True
for bps in [6.4,10,15,25,50]:
    n=net_series(bps=bps,oos=True); a=sr(n)>2.5 and ann(n)>10
    ok&=a
    R["checks"].append({"check":f"{bps}bps","status":"PASS" if a else "FAIL",
        "detail":f"ann={ann(n):.2f}% SR={sr(n):.3f} DD={ddf_(n):.2f}%"})
    print(f"{bps:5.1f} {ann(n):>7.2f}% {sr(n):>7.3f} {ddf_(n):>7.2f}%")
print(f"  annual turnover: 1leg={AGG.notional_1leg.sum()/9.7:.2f}x +2leg surch={AGG.notional_extra_leg.sum()/9.7:.2f}x")
R["overall"]="PASS" if ok else "FAIL"
json.dump(R,open("agents/agent04_report.json","w"),indent=2)
