"""A02: HUNT workdirs — each hunt dir's driver writes its sleeves; map them."""
import os,re,json,glob,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
out={}
for s in D['sleeves']:
    b=os.path.basename(s).replace(".csv","")
    fam=b.split("__")[0]
    hits=[]
    for py in glob.glob("/Users/daxu/software/world-trader/campaign/agents/**/driver*.py",recursive=True)+ \
              glob.glob("/Users/daxu/software/world-trader/campaign/agents/**/charter*.py",recursive=True)+ \
              glob.glob("/Users/daxu/software/world-trader/campaign/agents/**/gen*.py",recursive=True):
        try: txt=open(py,encoding='utf-8',errors='ignore').read()
        except: continue
        if fam in txt: hits.append(py)
    out[b]={"driver_hits":hits[:4]}
    print(f"  {len(hits):3d} drivers mention  {b}")
save("agent02_hunt_lineage",out)
