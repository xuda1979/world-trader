import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"12_plausibility","checks":[]}
print("=== 12 IS SR~4 PLAUSIBLE? BREADTH MATH ===")
sl=D['sleeves']; osdf=D['osdf']
srs=np.array([sr(osdf[s]) for s in sl])
C=osdf[sl].corr().values
N=len(sl); mean_sr=srs.mean(); rho=(C.sum()-N)/(N*(N-1))
pred=mean_sr*np.sqrt(N)/np.sqrt(1+(N-1)*rho)
real=sr(osdf[sl].dot(D['wt']))
print(f"  mean sleeve OOS SR={mean_sr:.2f}  avg pairwise rho={rho:.3f}  N={N}")
print(f"  predicted port SR (breadth) ={pred:.2f}   realized={real:.2f}   ratio={real/pred:.2f}")
R["checks"].append({"check":"breadth math explains SR (0.7<ratio<1.4)","status":"PASS" if 0.7<real/pred<1.4 else "FAIL","detail":f"ratio={real/pred:.2f}"})
# what must be true live: per-sleeve SR>0 survival rate
print(f"  sleeves OOS SR>0: {(srs>0).sum()}/{N}; SR>1: {(srs>1).sum()}; SR>2: {(srs>2).sum()}")
print("  NOTE: streams are campaign-simulated nets; live per-sleeve SR typically halves.")
half=mean_sr*0.5
pred_half=half*np.sqrt(N)/np.sqrt(1+(N-1)*rho)
print(f"  IF live sleeve SRs halve -> predicted port SR ~= {pred_half:.2f} (still strong)")
R["checks"].append({"check":"even half-edge SR>2","status":"PASS" if pred_half>2 else "FAIL","detail":f"{pred_half:.2f}"})
ok=all(c["status"]=="PASS" for c in R["checks"])
R["overall"]="PASS" if ok else "FAIL"
json.dump(R,open("agents/agent12_report.json","w"),indent=2)
