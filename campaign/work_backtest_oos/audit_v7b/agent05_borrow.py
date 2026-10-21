import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"05_borrow_stress","checks":[]}
print("=== 05 SHORT-BORROW STRESS (on 50% short notional) OOS ===")
ok=True
for b in [0.0,0.005,0.01,0.02,0.03]:
    n=net_series(rate=0.053,borrow=b,oos=True)
    a=ann(n)>10 and sr(n)>2.5
    ok&=a
    R["checks"].append({"check":f"borrow {b*100:.1f}%","status":"PASS" if a else "FAIL",
        "detail":f"ann={ann(n):.2f}% SR={sr(n):.3f}"})
    print(f"borrow {b*100:4.1f}%: ann={ann(n):6.2f}% SR={sr(n):.3f} (drag {b*1.6*0.5*100:.2f}pp)")
R["overall"]="PASS" if ok else "FAIL"
json.dump(R,open("agents/agent05_report.json","w"),indent=2)
