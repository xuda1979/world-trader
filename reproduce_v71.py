#!/usr/bin/env python3
"""REPRODUCE V7.1 — standalone verifier. Implements V71_REPLICATION_SPEC.md §2-6 exactly.
Reads ONLY: campaign/work_backtest_oos/OPT_20V71_weights.csv + the 20 sleeve CSVs +
OPT_20V71_FULL_LEDGER.csv. Exit 0 = all canonical numbers reproduced. Exit 1 = ANY
mismatch (STOP live trading)."""
import pandas as pd, numpy as np, os, sys
B=os.path.dirname(os.path.abspath(__file__)); B=os.path.join(B,"campaign")
OD=os.path.join(B,"work_backtest_oos")
LEV=1.6; RATE=0.053; MARG_D=0.6*RATE/252; BPS=6.4
TWO_LEG=["brwt7","RB_hobr_crack","inter_gasreg","calendar_vixterm","crack_crack321",
         "inter_dieseljet","diescrack","cnpair","D_xlu_ief"]
w_df=pd.read_csv(os.path.join(OD,"OPT_20V71_weights.csv"),index_col=0)
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
TRAIL2Y=pd.Timestamp("2024-10-01")
os_g=gross_m[gross_m.index>=IS_END]
is_g=gross_m[gross_m.index<IS_END]
full_g=gross_m
def srm(x): x=x.dropna(); return x.mean()/x.std()*np.sqrt(12)
def dd_m(x): x=(1+x.dropna()).cumprod(); return (x/x.cummax()-1).min()*100
# ---- realistic net FROM THE COMMITTED V7.1 LEDGER (canonical trade record) ----
LED=pd.read_csv(os.path.join(OD,"OPT_20V71_FULL_LEDGER.csv"),parse_dates=['date'])
g=LED.groupby('date')[['pnl','cost']].sum()
net_d=(g.pnl-g.cost).sort_index()
net_m=(1+net_d).resample("ME").prod()-1
net_m_oos=net_m[net_m.index>=IS_END]
net_m_t2y=net_m[net_m.index>=TRAIL2Y]
# ledger reconciliation: marks == LEV x gross daily (weights incl. zeros; gross uses
# the switched weight vector — pre-switch months use V7.0 weights, so recon is checked
# on the post-switch window where the §1 table applies)
marks=LED[LED.component=='mark'].groupby('date')['pnl'].sum().sort_index()
fails=0
ddata={s:load(s) for s in sleeves}
ddf=pd.DataFrame(ddata)[pd.DataFrame(ddata).index>="2009-01-01"].fillna(0)
post=ddf[ddf.index>=TRAIL2Y]
gross_post=post[sleeves].dot(w)
mpost=marks[marks.index>=TRAIL2Y]
recon=(mpost-LEV*gross_post.reindex(mpost.index)).abs().max()
print(f"ledger recon (post-switch): marks == 1.6 x gross_daily, max|diff| = {recon:.2e}")
if recon>1e-9:
    fails+=1
    print("RECON FAIL")
# pre-switch marks must equal the V7.0 ledger's marks exactly (act only from 2024-10)
LED7=pd.read_csv(os.path.join(OD,"OPT_20V7_FULL_LEDGER.csv"),parse_dates=['date'])
m7=LED7[LED7.component=='mark'].groupby('date')['pnl'].sum().sort_index()
pre_j=m7[m7.index<TRAIL2Y]
pre_new=marks[marks.index<TRAIL2Y]
dev_pre=(pre_j-pre_new.reindex(pre_j.index)).abs().max()
print(f"pre-switch marks == V7.0 ledger marks, max|diff| = {dev_pre:.2e}")
if dev_pre>0.0:
    fails+=1
    print("PRE-SWITCH MARKS FAIL")
yrs=(1+net_m).groupby(net_m.index.year).prod()-1
NEG_YRS=int((yrs<0).sum())
yrs_oos=yrs[yrs.index>=2017]
NEG_YRS_OOS=int((yrs_oos<0).sum())
halves=net_m.dropna(); h=len(halves)//2
H1=srm(halves.iloc[:h]); H2=srm(halves.iloc[h:])
checks=[
 ("Full SR (net, monthly)",       srm(net_m),   4.0792, 0.005),
 ("OOS SR (net, monthly)",        srm(net_m_oos),3.6718, 0.005),
 ("Full ann net (arith)",         net_m.mean()*12*100, 27.969, 0.05),
 ("OOS ann net (arith)",          net_m_oos.mean()*12*100, 30.481, 0.05),
 ("trail2y SR (net, monthly)",    srm(net_m_t2y),3.9223, 0.005),
 ("trail2y ann net (arith)",      net_m_t2y.mean()*12*100, 28.125, 0.05),
 ("Daily DD net",                 ((1+net_d).cumprod()/(1+net_d).cumprod().cummax()-1).min()*100, -3.161, 0.05),
 ("Neg years (net, full)",        NEG_YRS,      0, 0.5),
 ("Neg years (net, OOS)",         NEG_YRS_OOS,  0, 0.5),
 ("H1 SR (net, monthly)",         H1,           5.671, 0.01),
 ("H2 SR (net, monthly)",         H2,           3.5790, 0.01),
 ("Zeroed sleeve w == 0",         float(w[['FXD1_KRWTRI_raw_daily.csv' in s or 'crossasset_rev_L8' in s for s in w.index]].sum()), 0.0, 1e-12),
 ("Survivor renorm (sum==1)",     float(w.sum()), 1.0, 1e-9),
]
print(f"{'CHECK':<36}{'REPRODUCED':>12}{'CANONICAL':>12}{'TOL':>8}  STATUS")
for name,got,want,tol in checks:
    ok=abs(got-want)<=tol
    fails+= (not ok)
    print(f"{name:<36}{got:>12.4f}{want:>12.4f}{tol:>8.3f}  {'PASS' if ok else '**FAIL**'}")
print("\nRESULT:", "ALL REPRODUCED — safe for live use" if fails==0 else f"{fails} MISMATCH(ES) — DO NOT TRADE")
sys.exit(1 if fails else 0)
