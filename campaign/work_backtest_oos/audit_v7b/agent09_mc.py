import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"09_monte_carlo","checks":[]}
print("=== 09 BLOCK BOOTSTRAP (monthly net, 10k 1yr paths) ===")
m=monthly(net_series(oos=True)).dropna()
rng=np.random.default_rng(42)
sims=[]
for _ in range(10000):
    idx=rng.integers(0,len(m),12)
    sims.append((1+m.iloc[idx]).prod()-1)
sims=np.array(sims)
p5,p50,p95=np.percentile(sims,[5,50,95])
print(f"  1yr net ann dist: p5={p5*100:.2f}% p50={p50*100:.2f}% p95={p95*100:.2f}%")
print(f"  P(neg year)={float((sims<0).mean())*100:.2f}%  P(>+20%)={float((sims>0.20).mean())*100:.2f}%")
# 3yr DD paths
sims3=[]
for _ in range(3000):
    idx=rng.integers(0,len(m),36)
    pth=(1+m.iloc[idx]).cumprod()
    sims3.append(((pth/pth.cummax())-1).min())
print(f"  3yr path DD: p5={np.percentile(sims3,5)*100:.2f}% p50={np.percentile(sims3,50)*100:.2f}% worst={min(sims3)*100:.2f}%")
ok = p5>0 and float((sims<0).mean())<0.02
R["checks"].append({"check":"1yr p5>0","status":"PASS" if p5>0 else "FAIL","detail":f"{p5*100:.2f}%"})
R["checks"].append({"check":"P(neg yr)<2%","status":"PASS" if float((sims<0).mean())<0.02 else "FAIL","detail":f"{float((sims<0).mean())*100:.2f}%"})
R["checks"].append({"check":"3yr DD p5>-5%","status":"PASS" if np.percentile(sims3,5)>-0.05 else "FAIL","detail":f"{np.percentile(sims3,5)*100:.2f}%"})
ok&=np.percentile(sims3,5)>-0.05
R["overall"]="PASS" if ok else "FAIL"
json.dump(R,open("agents/agent09_report.json","w"),indent=2)
