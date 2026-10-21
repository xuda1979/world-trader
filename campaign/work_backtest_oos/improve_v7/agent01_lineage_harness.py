"""A01: read harness copy logic — find who writes __prefix files and sleeve_library."""
import os,re,json,glob,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
hits=[]
for py in glob.glob("/Users/daxu/software/world-trader/campaign/**/*.py",recursive=True)+glob.glob("/Users/daxu/software/world-trader/team/**/*.py",recursive=True):
    try: txt=open(py,encoding='utf-8',errors='ignore').read()
    except: continue
    if "__prefix" in txt or "sleeve_library" in txt:
        hits.append(py)
out={"copy_logic_files":hits[:25],"n":len(hits)}
print(f"harness/copy-logic files referencing __prefix/sleeve_library: {len(hits)}")
for h in hits[:10]: print("  ",h)
# for each V7 sleeve, find ANY file mentioning its stem
stems={}
for s in D['sleeves']:
    b=os.path.basename(s).replace(".csv","")
    fs=[py for py in glob.glob("/Users/daxu/software/world-trader/campaign/agents/**/*.py",recursive=True)
        if b.split("__")[0] in open(py,encoding='utf-8',errors='ignore').read()]
    stems[b]={"exact_family_files":len(fs),"sample":fs[:3]}
    print(f"  {len(fs):4d} files mention  {b}")
out["stem_mentions"]=stems
save("agent01_lineage",out)
