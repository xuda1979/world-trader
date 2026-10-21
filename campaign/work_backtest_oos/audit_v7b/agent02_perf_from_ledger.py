import json,os,sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
R={"agent":"02_perf_from_ledger","checks":[]}
def ck(n,c,d=""): R["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d}); print(f"[{'PASS' if c else 'FAIL'}] {n}: {d}")
print("=== 02 PERF FROM LEDGER ALONE (levered identity) ===")
g=LED.groupby('date')[['pnl','cost']].sum(); net=(g.pnl-g.cost).sort_index()
oos=net[net.index>=pd.Timestamp("2017-01-01")]
# day-by-day identity: ledger net == net_series()
# ledger = committed convention (single-leg 6.4bp). realistic net_series adds 2-leg surcharge.
ns=net_series(oos=True)
sur=( (AGG.notional_extra_leg)*6.4e-4 ).reindex(oos.index).fillna(0)
d=(oos+sur-ns.reindex(oos.index)).abs().max()
ck("ledger+surcharge==realistic net <1e-12", d<1e-12, f"{d:.2e}")
mk=LED[LED.component=='mark'].groupby('date')['pnl'].sum().sort_index()
gr=D['ddf'][D['sleeves']].dot(D['wt']).sort_index()
d2=(mk-1.6*gr.reindex(mk.index)).abs().max()
ck("levered marks==1.6*gross <1e-12", d2<1e-12, f"{d2:.2e}")
geo=lambda r:(1+r).prod()**(252/len(r))-1
ck("OOS geo ann 25-33% (realistic band)", 0.25<=geo(oos)<=0.33, f"{geo(oos)*100:.2f}%")
ck("net SR>4", sr(oos)>4, f"{sr(oos):.2f}")
ck("net DD>-5%", ddf_(oos)>-5, f"{ddf_(oos):.2f}%")
n_,ny,_=negy(oos); ck("OOS neg years=0", n_==0, f"{n_}/{ny}")
print(f"  ledger 1.6x net: geo ann={geo(oos)*100:.2f}% SR={sr(oos):.2f} DD={ddf_(oos):.2f}% (vs arithmetic headline 33.72%)")
R["overall"]="PASS" if all(c["status"]=="PASS" for c in R["checks"]) else "FAIL"
json.dump(R,open("agents/agent02_report.json","w"),indent=2)
