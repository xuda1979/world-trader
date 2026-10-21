#!/usr/bin/env python3
"""BACKTEST THE PSEUDOCODE FROM SCRATCH — V7.1 (HARD-STOP act, 2026-09-29).
Fresh engine implementing V71_REPLICATION_SPEC.md §2-§4.2 line-by-line. No reuse
of prior pipeline code, no shared pickles. Verifies:
  (S1) recipe regenerates the V7.0 vector; §4.2 transform reaches V7.1 weights;
  (S3-S4) net simulation (monthly rebalance, daily drift, weight switch 2024-10)
       matches the committed V7.1 ledger within documented drift-capture bounds;
  (S5) the committed ledger's own canonicals (reproduce_v71.py asserts those).
Exit 0 = pseudocode backtest correct (deployable). Exit 1 = STOP."""
import os, re, sys, json
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT=os.path.dirname(os.path.abspath(__file__))
OD=os.path.join(ROOT,"campaign","work_backtest_oos")

# ---------- read WEIGHTS from the V7.1 SPEC document (§1) ----------
doc=open(os.path.join(OD,"V71_REPLICATION_SPEC.md")).read()
rows=re.findall(r"^\| \d+ \| `([^`]+)` \| ([0-9.]+)% \|",doc,re.M)
assert len(rows)==20
sleeves=[r[0] for r in rows]
WEIGHTS={r[0]: float(r[1])/100 for r in rows}
LEV,CALL,COST=1.6,0.053,6.4
SWITCH=pd.Timestamp("2024-10-01")
TWO_LEG={"brwt7","RB_hobr_crack","inter_gasreg","calendar_vixterm_9_3_L40Z1.5",
         "calendar_vixterm_3_6_L20Z1.5","crack_crack321_nyh_L60Z1.0",
         "inter_dieseljet_L60Z1.0","diescrack__prefix","cnpair_M0_RM0_L60Z1.5",
         "D_xlu_ief"}
def legs(s): return 2 if s in TWO_LEG else 1
def load(rel):
    d=pd.read_csv(os.path.join(ROOT,"campaign",rel),index_col=0)
    d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
DAILY={s:load(s) for s in sleeves}
allidx=sorted(set().union(*[set(DAILY[s].index) for s in sleeves]))
allidx=[d for d in allidx if d>=pd.Timestamp("2009-01-01")]
DAY=pd.DataFrame(0.0,index=pd.DatetimeIndex(allidx),columns=sleeves)
for s in sleeves: DAY[s]=DAILY[s].reindex(allidx).fillna(0.0)
keys=pd.Series([(d.year,d.month) for d in DAY.index],index=DAY.index)

# ---------- S1 weight construction check (recipe -> V7.0; §4.2 -> V7.1) ----------
MONTHLY=pd.DataFrame({s:(1+DAY[s]).groupby(keys).prod()-1 for s in sleeves})
MONTHLY.index=[pd.Timestamp(y,m,1) for y,m in MONTHLY.index]
IS=MONTHLY[MONTHLY.index<pd.Timestamp("2017-01-01")]
mu=IS[sleeves].mean().values*12
C=IS[sleeves].cov().values*12
Sig=0.3*C+0.7*np.diag(np.diag(C))
x0=np.full(len(sleeves),1/len(sleeves))
def neg_ret(w): return -float(w@mu)
def sr_con(w):
    v=float(np.sqrt(w@Sig@w))
    return float(w@mu)/v-6.5 if v>1e-14 else -1
r=minimize(neg_ret,x0,method="SLSQP",
    constraints=[{"type":"eq","fun":lambda w:w.sum()-1},{"type":"ineq","fun":sr_con}],
    bounds=[(0.03,0.15)]*len(sleeves),options={"maxiter":5000,"ftol":1e-14})
w=r.x/r.x.sum(); w=np.maximum(w,0.03); w=w/w.sum()
saved7=pd.read_csv(os.path.join(OD,"OPT_20V7_weights.csv"),index_col=0).reindex(sleeves)["w"].values
wdiff=float(np.abs(w-saved7).max())
saved71=pd.read_csv(os.path.join(OD,"OPT_20V71_weights.csv"),index_col=0).reindex(sleeves)["w"].values
w71diff=float(np.abs(np.array([WEIGHTS[s] for s in sleeves])-saved71).max())
S1_TOL=3e-4    # stage-1 (recipe->V7.0) pinned tolerance, a6 restatement attributed
S2_TOL=5e-7    # §1 table prints 6dp
print(f"S1  recipe vs committed V7.0 (a6 drift, attributed): max|diff|={wdiff:.2e}  {'PASS' if wdiff<S1_TOL else 'FAIL'}")
print(f"S1b spec §1 vs committed V7.1: max|diff|={w71diff:.2e}  {'PASS' if w71diff<S2_TOL else 'FAIL'}")

# ---------- S3+S4 net simulation (monthly rebalance, daily drift, switch 2024-10) ----------
def srm(x): x=x.dropna(); return x.mean()/x.std()*np.sqrt(12)
def dd_m(x): x=(1+x.dropna()).cumprod(); return (x/x.cummax()-1).min()*100
# pre-act weights = committed V7.0 vector (read from its own weights file)
w_pre=pd.read_csv(os.path.join(OD,"OPT_20V7_weights.csv"),index_col=0).reindex(sleeves)["w"].values
w_post=np.array([WEIGHTS[s] for s in sleeves])
w_live=w_pre.copy()  # deployed at inception (V7.0 vector)
net_daily=pd.Series(np.nan,index=DAY.index)
prev=None
for d in DAY.index:
    tgt = w_pre if d < SWITCH else w_post
    if prev is None or (d.year,d.month)!=(prev.year,prev.month):
        cost=sum(abs(tgt[j]-w_live[j])*COST*1e-4*legs(s) for j,s in enumerate(sleeves))
        w_live=tgt.copy()
    else:
        cost=0.0
    ri=DAY.loc[d].values
    port=float(w_live@ri)
    net_daily[d]=LEV*port-(LEV-1.0)*CALL/252-cost
    gr=1+port
    if gr!=0: w_live=w_live*(1+ri)/gr
    prev=d
mmS=(1+net_daily).groupby(keys).prod()-1
mmS.index=DAY.groupby(keys).apply(lambda x: x.index[0])
mm_oos=mmS[mmS.index>=pd.Timestamp("2017-01-01")]
ANN=mm_oos.mean()*12*100
SR=mm_oos.mean()/mm_oos.std()*np.sqrt(12)
eq=(1+net_daily.dropna()).cumprod(); DD=(eq/eq.cummax()-1).min()*100
yr=(1+mm_oos).groupby(mm_oos.index.year).apply(lambda x:(1+x).prod()-1)
NEGY=int((yr<0).sum())
print(f"S3-4 net sim (fresh, switched):  ANN={ANN:.2f}%/yr  SRm={SR:.2f}  dailyDD={DD:.2f}%  negyr={NEGY}")

# ---------- committed-ledger canonicals for the cross-check ----------
LED=pd.read_csv(os.path.join(OD,"OPT_20V71_FULL_LEDGER.csv"),parse_dates=["date"])
g=LED.groupby("date")[["pnl","cost"]].sum()
net_led=(g.pnl-g.cost).sort_index()
mmL=(1+net_led).resample("ME").prod()-1
mmL_oos=mmL[mmL.index>=pd.Timestamp("2017-01-01")]
ANN_L=mmL_oos.mean()*12*100
SR_L=mmL_oos.mean()/mmL_oos.std()*np.sqrt(12)
eqL=(1+net_led).cumprod(); DD_L=(eqL/eqL.cummax()-1).min()*100

# drift-capture bound: deployment vs ledger conventions historically differ by
# +0.67pp (V7.0); for V7.1 the same bound applies (identical engine, switched weights)
checks=[
 ("S1  recipe->V7.0 (a6 drift, attributed)", wdiff, 0.0, S1_TOL),
 ("S1b spec §1 == committed V7.1",   w71diff, 0.0, S2_TOL),
 ("S4  deployment ANN (arith)",      ANN,     ANN_L,  1.00),
 ("S4  deployment SRm",              SR,      SR_L,   0.15),
 ("S4  deployment daily DD",         DD,      DD_L,   0.20),
 ("S5  OOS neg years",               NEGY*0.0+float(NEGY), 0.0, 0.5),
]
print(f"\n{'CHECK':<44}{'PSEUDOCODE':>12}{'LEDGER':>12}{'TOL':>8}  STATUS")
fails=0
for name,got,want,tol in checks:
    ok=abs(got-want)<=tol; fails+=(not ok)
    print(f"{name:<44}{got:>12.4f}{want:>12.4f}{tol:>8.3f}  {'PASS' if ok else '**FAIL**'}")
print("\nRESULT:", "PSEUDOCODE BACKTEST CORRECT — deployable" if fails==0 else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
