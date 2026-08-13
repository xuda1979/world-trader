"""Robust multi-strategy robustness test (2026-08-13 loop fire).

Validates the positive-only multi-strategy finding over a LONGER, denser
window using the LS n10r14 stream (2019-2026, dense ~1851 rows) plus the
hedge-fund positive streams and the validated cross-suite legs.

Tests:
  A) Positive-only hedge streams 4:  LS_volman + RiskParity + CTA + FX
  B) + AP gold
  C) + LS n10r14 (long, dense)  <- the new robust multi-year validation
  D) 6: hedge-pos + AP gold + LS n10r14
Weightings: equal-weight (EW) vs inverse-vol (IV).
Sub-periods: 2019-2022, 2023-2026.
"""
import sys
from pathlib import Path
import pandas as pd, numpy as np
HERE = Path(__file__).resolve().parent
RES = HERE / "results"
ROOT = HERE.parent.parent.parent

def load(path, col=0):
    df = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, col].astype(float)
    return df

def perf(r, ann=252):
    r = r.dropna()
    if len(r) < 30 or r.std()==0: return None
    eq = (1+r).cumprod()
    ret = (eq.iloc[-1])**(ann/len(r))-1
    sr = r.mean()/r.std()*np.sqrt(ann)
    dd = (eq/eq.cummax()-1).min()
    return dict(n=len(r), ret=ret, sr=sr, maxdd=dd)

sts = {}
sts["ls_volman"]=load(RES/"equity_L_S_130_30_volmanaged.csv").pct_change()
sts["riskparity"]=load(RES/"equity_Risk_Parity_Bridgewater.csv").pct_change()
sts["cta_fut"]=load(RES/"equity_CTA_Futures_macro_21d.csv").pct_change()
sts["fx_carry"]=load(RES/"equity_FX_Carry.csv").pct_change()
ap=load(ROOT/"alphaportfolio_replication/data/wf_champion_gold_opt_daily.csv"); ap=ap[ap.index!=0]; sts["ap_gold"]=ap
ls=load(ROOT/"alphaportfolio_replication/data/ls_n10r14_daily.csv"); ls=ls[ls!=0]; sts["ls_n10r14"]=ls

def blend(names, wtype="ew", lo="2019-01-01"):
    df=pd.concat([sts[n] for n in names],axis=1)[lo:].ffill().dropna()
    if len(df)==0: return None,None,None
    if wtype=="ew":
        w=np.ones(len(names))/len(names); ew=df.mean(axis=1)
    else:
        iv=df.std().replace(0,np.nan); w=(1/iv); w/=w.sum(); ew=df.dot(w)
    return ew, df.corr(), perf(ew)

# TRUSTED (independently verified via df.dot(weights), 2019-2026 n=2054, 6bps):
#   Hedge-pos4 EW      SR 1.05 ret 9.4% DD -11.7%
#   +LS n10r14 EW      SR 1.12 ret 8.2% DD -9.2%
#   +AP+LS EW          SR 1.10 ret 8.3% DD -9.0%
#   +AP+LS IV   <BEST> SR 1.24 ret 6.1% DD -5.9%  (2019-22 SR1.48, 2023-26 SR1.01)

import itertools
cases=[
    ("Hedge-pos 4 (LSvolman+RP+CTA+FX)","EW",["ls_volman","riskparity","cta_fut","fx_carry"]),
    ("Hedge-pos 4 + AP gold","EW",["ls_volman","riskparity","cta_fut","fx_carry","ap_gold"]),
    ("Hedge-pos 4 + LS n10r14","EW",["ls_volman","riskparity","cta_fut","fx_carry","ls_n10r14"]),
    ("Hedge-pos 4 + AP gold + LS n10r14","EW",["ls_volman","riskparity","cta_fut","fx_carry","ap_gold","ls_n10r14"]),
    ("Hedge-pos 4 + AP gold + LS n10r14","IV",["ls_volman","riskparity","cta_fut","fx_carry","ap_gold","ls_n10r14"]),
]
print("="*76)
print("ROBUST MULTI-STRATEGY — window 2019-01 .. 2026-08 (6 bps, free data)")
print("="*76)
for label,wtype,names in cases:
    ew,c,p=blend(names,wtype)
    if p is None: print(f"{label:38s} {wtype:3s}: no common data"); continue
    tri=c.where(np.triu(np.ones(c.shape),1).astype(bool)).values
    mc=np.nanmean(np.abs(tri))
    print(f"\n### {label} [{wtype}]")
    print(f"   FULL 2019+: SR {p['sr']:.3f} | ret {p['ret']*100:.1f}% | MaxDD {p['maxdd']*100:.1f}% | n={p['n']} | mean|corr| {mc:.3f}")
    for lo,hi in [("2019-01-01","2022-12-31"),("2023-01-01","2026-12-31")]:
        if not (ew.index>=lo).any() or not (ew.index<=hi).any(): continue
        ews = ew[(ew.index>=lo)&(ew.index<=hi)]
        p2=perf(ews)
        if p2: print(f"     {lo[:4]}-{hi[:4]}: SR {p2['sr']:.3f} | ret {p2['ret']*100:.1f}% | MaxDD {p2['maxdd']*100:.1f}% | n={p2['n']}")
