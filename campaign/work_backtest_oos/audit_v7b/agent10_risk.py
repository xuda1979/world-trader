import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"10_risk_decomp","checks":[]}
print("=== 10 RISK CONTRIBUTIONS (OOS, static weights) ===")
sl=D['sleeves']; wt=D['wt']; osdf=D['osdf']
cov=osdf[sl].cov()*12
pvar=float(wt.values@cov.values@wt.values)
contrib=(wt.values*(cov.values@wt.values))/pvar
top=sorted(zip(sl,contrib),key=lambda x:-x[1])[:5]
print("  top-5 risk contributors:")
for s,c in top: print(f"    {c*100:5.1f}%  {os.path.basename(s)}")
ok=top[0][1]<0.45
R["checks"].append({"check":"top risk<45%","status":"PASS" if ok else "FAIL","detail":f"{top[0][1]*100:.1f}%"})
# implied sleeve vol & portfolio vol
vols=osdf[sl].std()*np.sqrt(12)
print(f"  portfolio OOS vol={np.sqrt(pvar)*100:.2f}%  mean sleeve vol={vols.mean()*100:.1f}%  max={vols.max()*100:.1f}%")
R["checks"].append({"check":"port vol<6%","status":"PASS" if np.sqrt(pvar)<0.06 else "FAIL","detail":f"{np.sqrt(pvar)*100:.2f}%"})
ok&=np.sqrt(pvar)<0.06
R["overall"]="PASS" if ok else "FAIL"
json.dump(R,open("agents/agent10_report.json","w"),indent=2)
