#!/usr/bin/env python3
"""REPRODUCE V7 — standalone verifier. Implements V7_REPLICATION_SPEC.md §2-6 exactly.
Reads ONLY: campaign/work_backtest_oos/OPT_20V7_weights.csv + the 20 sleeve CSVs + best.json.
Exit 0 = all canonical numbers reproduced. Exit 1 = ANY mismatch (STOP live trading)."""
import pandas as pd, numpy as np, json, os, sys, re
B="/Users/daxu/software/world-trader/campaign"
OD=os.path.join(B,"work_backtest_oos")
LEV=1.6; RATE=0.053; MARG_D=0.6*RATE/252; BPS=6.4
TWO_LEG=["brwt7","RB_hobr_crack","inter_gasreg","calendar_vixterm","crack_crack321",
         "inter_dieseljet","diescrack","cnpair","D_xlu_ief"]
w_df=pd.read_csv(os.path.join(OD,"OPT_20V7_weights.csv"),index_col=0)
sleeves=list(w_df.index); w=w_df['w']
def load(rel):
    d=pd.read_csv(os.path.join(B,rel),index_col=0)
    d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def mon(s): return (1+s).resample("ME").prod()-1
panel=pd.DataFrame({s:mon(load(s)) for s in sleeves})
panel=panel[panel.index>="2009-01-01"].fillna(0)
gross_m=panel[sleeves].dot(w)
IS_END=pd.Timestamp("2017-01-01")
os_g=gross_m[gross_m.index>=IS_END]
is_g=gross_m[gross_m.index<IS_END]
full_g=gross_m
def srm(x): x=x.dropna(); return x.mean()/x.std()*np.sqrt(12)
def dd_m(x): x=(1+x.dropna()).cumprod(); return (x/x.cummax()-1).min()*100
# daily net for realistic numbers
# ---- realistic net FROM THE COMMITTED LEDGER (canonical trade record) ----
LED=pd.read_csv(os.path.join(OD,"OPT_20V7_FULL_LEDGER.csv"),parse_dates=['date'])
g=LED.groupby('date')[['pnl','cost']].sum()
net_d=(g.pnl-g.cost).sort_index()
net_m=(1+net_d).resample("ME").prod()-1
net_m_oos=net_m[net_m.index>=IS_END]
# ledger reconciliation: marks == LEV x gross daily
marks=LED[LED.component=='mark'].groupby('date')['pnl'].sum().sort_index()
ddata={s:load(s) for s in sleeves}
ddf=pd.DataFrame(ddata)[pd.DataFrame(ddata).index>="2009-01-01"].fillna(0)
gross_d=ddf[sleeves].dot(w)
recon=(marks-LEV*gross_d.reindex(marks.index)).abs().max()
print(f"ledger recon: marks == 1.6 x gross_daily, max|diff| = {recon:.2e}")
if recon>1e-10: fails+=1; print("**FAIL** ledger/gross reconciliation")
# canonical asserts
bj=json.load(open(os.path.join(OD,"OPT_20V7_best.json")))
yr_g=os_g.groupby(os_g.index.year).apply(lambda x:(1+x).prod()-1)
NEG_YRS_GROSS=float(int((yr_g<0).sum()))
checks=[
 ("IS SR gross",        srm(is_g),            bj['is_sr'],  0.005),
 ("OOS SR gross",       srm(os_g),            bj['oos_sr'], 0.005),
 ("OOS ann gross (arith, headline)", os_g.mean()*12*100*LEV, bj['oos_ann'], 0.05),
 ("OOS MaxDD gross (monthly)", dd_m(os_g),   bj['oos_dd'], 0.05),
 ("Full SR gross",      srm(full_g),          bj['full_sr'],0.005),
 ("Realistic net ann (arith)", net_m_oos.mean()*12*100, 29.66, 0.15),
 ("Realistic net monthly SR", srm(net_m_oos), 3.63, 0.05),
 ("Realistic net daily DD", ((1+net_d).cumprod()/(1+net_d).cumprod().cummax()-1).min()*100, -3.16, 0.15),
 ("Neg years (gross, OOS)", NEG_YRS_GROSS, 0, 0.5),
]
fails=0
print(f"{'CHECK':<36}{'REPRODUCED':>12}{'CANONICAL':>12}{'TOL':>8}  STATUS")
for name,got,want,tol in checks:
    ok=abs(got-want)<=tol
    fails+= (not ok)
    print(f"{name:<36}{got:>12.4f}{want:>12.4f}{tol:>8.3f}  {'PASS' if ok else '**FAIL**'}")
print("\nRESULT:", "ALL REPRODUCED — safe for live use" if fails==0 else f"{fails} MISMATCH(ES) — DO NOT TRADE")
sys.exit(1 if fails else 0)
