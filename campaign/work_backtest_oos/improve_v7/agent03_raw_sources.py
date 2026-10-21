"""A03: infer raw data sources per sleeve family from its neighborhood scripts."""
import os,re,json,glob,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
RAWD=[]
for d_ in ["/Users/daxu/software/world-trader/tools/quant/data/newdata","/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred","/Users/daxu/software/world-trader/tools/quant/data/more_fred"]:
    RAWD+=glob.glob(os.path.join(d_,"*.csv"))
raw_names={os.path.basename(p).replace(".csv",""):p for p in RAWD}
out={}
for s in D['sleeves']:
    b=os.path.basename(s).replace(".csv","")
    fam=b.split("__")[0].split("_L")[0]
    kw=fam[:6]
    matched=[k for k in raw_names if kw.lower() in k.lower() or k.lower() in b.lower()]
    out[b]={"raw_candidates":sorted(set(matched))[:6]}
    print(f"  {b:<42} raw candidates: {sorted(set(matched))[:6]}")
save("agent03_raw_sources",out)
