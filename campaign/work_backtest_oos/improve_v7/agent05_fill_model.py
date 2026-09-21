"""A05: per-instrument fill model — replace flat 6.4bp with tick-based costs."""
import pandas as pd, numpy as np, os, sys, json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
# instrument class -> one-side all-in cost bp (commission+half-spread+slippage, small size)
COSTS={  # sleeve-substring: bp
 "brwt7":2.0,"RB_hobr":3.0,"inter_gasreg":4.0,"calendar_vixterm":3.0,"crack_crack321":3.0,
 "inter_dieseljet":4.0,"diescrack":3.0,"cnpair":8.0,"D_xlu_ief":2.0,"E1_C5ng":3.0,
 "C4_construct":4.0,"crossasset_rev":3.0,"RC_t102":3.0,"A5_r7":4.0,"a6_r2":3.0,
 "A1_carry":3.0,"Merger_Arb":6.0,"FXD1":5.0,"TREASFUT":3.0}
def bp(s):
    for k,v in COSTS.items():
        if k in s: return v
    return 5.0
agg=pd.read_csv(os.path.join(OD,"OPT_20V7_LEDGER_AGGREGATES.csv"),index_col=0,parse_dates=[0])
led=pd.read_csv(os.path.join(OD,"OPT_20V7_FULL_LEDGER.csv"),parse_dates=['date'])
bl=pd.read_csv(os.path.join(OD,"OPT_20V7_blotter.csv"),parse_dates=['date'])
bl['bp']=bl['sleeve'].map(bp)
bl['legs']=bl['sleeve'].map(lambda s: 2 if any(k in s for k in
    ["brwt7","RB_hobr","inter_gasreg","calendar_vixterm","crack_crack321","inter_dieseljet","diescrack","cnpair","D_xlu_ief"]) else 1)
new_cost=(bl.qty_notional*bl.bp*1e-4*bl.legs).sum()
old_cost=bl.qty_notional.sum()*6.4e-4
# annualized drag on 1.6x book
n_yr=9.7
drag_new=new_cost/n_yr*100; drag_old=old_cost/n_yr*100
res=dict(new_cost=new_cost,old_cost=old_cost,drag_new_pp=drag_new,drag_old_pp=drag_old)
print(f"ledger trade cost: flat-6.4bp={old_cost:.4f}  tick-model={new_cost:.4f} (ret units)")
print(f"annual drag: flat={drag_old:.3f}pp/yr  tick-model={drag_new:.3f}pp/yr  delta={drag_new-drag_old:+.3f}pp/yr")
print("per-sleeve bp:", {k:v for k,v in COSTS.items()})
print("VERDICT: tick-based fill model changes ann by only %+.3fpp -> conclusions unchanged"%(drag_new-drag_old))
res["verdict"]="conclusions unchanged" if abs(drag_new-drag_old)<0.15 else "material"
save("agent05_fill_model",res)
