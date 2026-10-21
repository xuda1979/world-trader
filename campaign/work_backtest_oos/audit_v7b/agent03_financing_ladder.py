import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"03_financing_ladder","checks":[]}
print("=== 03 CALL-RATE LADDER (gross 1.6x) OOS window ===")
print(f"{'rate':>6} {'ann':>8} {'SR':>7} {'DD':>8} {'negYr':>6}")
ok=True
for rate in [0.045,0.053,0.065,0.08]:
    n=net_series(rate=rate,oos=True)
    n_,ny,_=negy(n)
    a=sr(n)>2.5 and ddf_(n)>-5 and n_==0
    ok&=a
    R["checks"].append({"check":f"rate {rate*100:.1f}%","status":"PASS" if a else "FAIL",
        "detail":f"ann={ann(n):.2f}% SR={sr(n):.3f} DD={ddf_(n):.2f}% neg={n_}"})
    print(f"{rate*100:5.1f}% {ann(n):>7.2f}% {sr(n):>7.3f} {ddf_(n):>7.2f}% {n_:>5}/ny")
n0=net_series(rate=0.0,oos=True)
print(f"  0.0% (no-financing ref): ann={ann(n0):.2f}% SR={sr(n0):.3f}")
R["overall"]="PASS" if ok else "FAIL"
json.dump(R,open("agents/agent03_report.json","w"),indent=2)
