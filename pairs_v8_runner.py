#!/usr/bin/env python3
import os,sys
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"tools","quant"))
import pairs_research_v4 as v4
import pairs_crosssec as pc
import math,statistics,random,json,time
COST=3.8
NSCR=8
secs={k:v for k,v in v4.SECTORS.items() if k!="ETFs"}
POLY=os.path.join("tools","quant","data","polygon")
sfil={}
for n,syms in secs.items():
  av=[s for s in syms if os.path.exists(os.path.join(POLY,s+".csv"))]
  if len(av)>=4:sfil[n]=av
print("Sectors:",list(sfil.keys()))
cal,m,data=pc.build_matrix(sfil)
print("Calendar:",len(cal),"days")
print("\nMOMENTUM GRID (form/hold/k)")
print("%-20s %8s %8s %8s %8s %8s"%("Config","NetSR","GrossSR","bps/d","ScramMn","zScr"))
print("-"*60)
res=[]
for form in [10,20,30,40,60]:
 for hold in [10,20,30]:
  if form>hold*3:continue
  for k in [1,2,3]:
   nm="mom_%d/%d_k%d"%(form,hold,k)
   rn,rg=pc.run_book(cal,m,sfil,form,hold,top_k=k,scramble=False,cost_bps=COST,momentum=True)
   mn=pc.metrics(rn);mg=pc.metrics(rg)
   ss=[]
   for s in range(NSCR):
    _,sg=pc.run_book(cal,m,sfil,form,hold,top_k=k,scramble=True,rng=random.Random(3000+s),cost_bps=COST,momentum=True)
    ms=pc.metrics(sg)
    if ms["sharpe"]!=0:ss.append(ms["sharpe"])
   sm=statistics.fmean(ss) if ss else 0
   ssd=statistics.pstdev(ss) if len(ss)>1 else 0
   z=(mg["sharpe"]-sm)/ssd if ssd>0 else 0
   print("%-20s %+8.3f %+8.3f %+8.1f %+8.3f %+8.2f"%(nm,mn["sharpe"],mg["sharpe"],mn["mean_bps"],sm,z))
   res.append(dict(name=nm,net=round(mn["sharpe"],4),gross=round(mg["sharpe"],4),bps=round(mn["mean_bps"],2),sm=round(sm,4),z=round(z,3)))
res.sort(key=lambda r:r["net"],reverse=True)
print("\nTOP 10 BY NET SHARPE")
for r in res[:10]:print("  %-25s net=%+.3f gross=%+.3f z=%+.2f"%(r["name"],r["net"],r["gross"],r["z"]))
