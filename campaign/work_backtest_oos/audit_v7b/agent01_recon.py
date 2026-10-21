import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"01_ledger_recon","checks":[]}
def ck(n,c,d=""): R["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d}); print(f"[{'PASS' if c else 'FAIL'}] {n}: {d}")
print("=== 01 LEDGER RECON ===")
ck("ledger rows>100k", len(LED)>100000, f"{len(LED)}")
m=LED[LED.component=='mark'].groupby('date')['pnl'].sum().sort_index()
gross=D['ddf'][D['sleeves']].dot(D['wt']).sort_index()
d=(m-gross.reindex(m.index)).abs().max()
ck("marks==committed gross <1e-12", d<1e-12, f"{d:.2e}")
tr=LED[LED.component=='trade']; bl=pd.read_csv(os.path.join(OD,"OPT_20V7_blotter.csv"))
ck("trade costs reconcile", abs(tr.cost.sum()-bl.qty_notional.abs().sum()*6.4e-4)<1e-12, f"{tr.cost.sum():.6f}")
mg=LED[LED.component=='margin']
ck("margin==0.6*5.3%/252*d", abs(mg.cost.sum()-0.6*0.053/252*len(mg))<1e-12, f"{mg.cost.sum():.4f}")
ck("3 components present", set(LED.component)=={'mark','trade','margin'}, "")
R["overall"]="PASS" if all(c["status"]=="PASS" for c in R["checks"]) else "FAIL"
json.dump(R,open("agents/agent01_report.json","w"),indent=2)
