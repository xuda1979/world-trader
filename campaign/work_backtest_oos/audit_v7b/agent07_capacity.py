import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"07_capacity","checks":[]}
print("=== 07 CAPACITY (sqrt impact, 10bp@$50M on futures legs) ===")
ok=True
for aum in [1e7,1e8,1e9]:
    scale=np.sqrt(aum/5e7)
    impact_bp=10*scale
    n=net_series(bps=6.4+impact_bp,oos=True)
    a=sr(n)>2.0
    ok&=a
    R["checks"].append({"check":f"AUM ${aum/1e6:.0f}M","status":"PASS" if a else "FAIL",
        "detail":f"impact={impact_bp:.1f}bp ann={ann(n):.2f}% SR={sr(n):.3f}"})
    print(f"AUM ${aum/1e6:4.0f}M: impact {impact_bp:5.1f}bp -> ann={ann(n):6.2f}% SR={sr(n):.3f}")
R["overall"]="PASS" if ok else "FAIL"
json.dump(R,open("agents/agent07_report.json","w"),indent=2)
