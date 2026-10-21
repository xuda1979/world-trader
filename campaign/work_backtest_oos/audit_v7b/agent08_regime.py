import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"08_regime_net","checks":[]}
print("=== 08 PER-YEAR NET (6.4bp + 5.3% margin @1.6x) ===")
n=net_series(oos=True)
yr=(1+n).groupby(n.index.year).prod()-1
ok=True
for y,v in yr.items():
    a=v>0; ok&=a
    R["checks"].append({"check":f"{y} net +","status":"PASS" if a else "FAIL","detail":f"{v*100:+.2f}%"})
    print(f"  {y}: {v*100:+6.2f}%")
roll=(1+n).rolling(252).apply(lambda x:(1+x).prod()-1,raw=True).dropna()
print(f"  worst rolling-12m net: {roll.min()*100:.2f}%")
R["checks"].append({"check":"worst 12m >-8%","status":"PASS" if roll.min()>-0.08 else "FAIL","detail":f"{roll.min()*100:.2f}%"})
ok&=roll.min()>-0.08
R["overall"]="PASS" if ok else "FAIL"
json.dump(R,open("agents/agent08_report.json","w"),indent=2)
