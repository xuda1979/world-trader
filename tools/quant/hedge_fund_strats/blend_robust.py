"""Robust multi-strategy blend — VALIDATED (2026-08-13 loop).
Single-source authoritative computation via df.dot(weights).
Window 2019-01..2026-08, dense 7.5y (n=2054), 6 bps, cost-inclusive curves.

VERIFIED RESULTS (all df.dot, same pipeline, reproducible):
  Hedge-pos 4 EW            SR 1.049 ret 9.4% MaxDD -11.7%
  +AP gold EW               SR 1.047 ret 9.4% MaxDD -11.0%
  +LS n10r14 EW             SR 1.121 ret 8.2% MaxDD -9.2%
  +AP+LS EW                 SR 1.103 ret 8.3% MaxDD -9.0%
  +AP+LS IV  <BEST>         SR 1.240 ret 6.1% MaxDD -5.9%  w=[.07,.12,.10,.20,.12,.38]
  IV sub-period 2019-2022:  SR 1.481 MaxDD -5.2%  |  2023-2026: SR 1.006 MaxDD -5.9%
"""
import pandas as pd, numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent.parent
RES  = ROOT / "tools/quant/hedge_fund_strats/results"
def L(p): return pd.read_csv(p, index_col=0, parse_dates=True).iloc[:,0].astype(float)
sts={
 "ls_volman":L(RES/"equity_L_S_130_30_volmanaged.csv").pct_change(),
 "riskparity":L(RES/"equity_Risk_Parity_Bridgewater.csv").pct_change(),
 "cta_fut":L(RES/"equity_CTA_Futures_macro_21d.csv").pct_change(),
 "fx_carry":L(RES/"equity_FX_Carry.csv").pct_change(),
}
ap=L(ROOT/"alphaportfolio_replication/data/wf_champion_gold_opt_daily.csv"); ap=ap[ap.index!=0]; sts["ap_gold"]=ap
ls=L(ROOT/"alphaportfolio_replication/data/ls_n10r14_daily.csv"); ls=ls[ls!=0]; sts["ls_n10r14"]=ls
def run(names, wtype):
    df=pd.concat([sts[n] for n in names],axis=1)["2019-01-01":].ffill().dropna()
    if wtype=="ew": w=np.ones(len(names))/len(names)
    else:
        v=df.std().replace(0,np.nan); w=(1/v); w/=w.sum()
    r=df.dot(w); eq=(1+r).cumprod()
    sr=r.mean()/r.std()*np.sqrt(252); dd=(eq/eq.cummax()-1).min(); ret=(eq.iloc[-1])**(252/len(r))-1
    return sr,ret,dd,len(r),w
cases=[
 ("Hedge-pos 4 EW","ew",["ls_volman","riskparity","cta_fut","fx_carry"]),
 ("+AP gold EW","ew",["ls_volman","riskparity","cta_fut","fx_carry","ap_gold"]),
 ("+LS n10r14 EW","ew",["ls_volman","riskparity","cta_fut","fx_carry","ls_n10r14"]),
 ("+AP+LS EW","ew",["ls_volman","riskparity","cta_fut","fx_carry","ap_gold","ls_n10r14"]),
 ("+AP+LS IV","iv",["ls_volman","riskparity","cta_fut","fx_carry","ap_gold","ls_n10r14"]),
]
print("="*70); print("VALIDATED MULTI-STRATEGY (2019-2026, n=2054, 6 bps)"); print("="*70)
for label,wt,names in cases:
    sr,ret,dd,n,w=run(names,wt)
    print(f"{label:18s} SR {sr:.3f} ret {ret*100:.1f}% MaxDD {dd*100:.1f}% n={n}")
names6=["ls_volman","riskparity","cta_fut","fx_carry","ap_gold","ls_n10r14"]
df=pd.concat([sts[n] for n in names6],axis=1)["2019-01-01":].ffill().dropna()
v=df.std().replace(0,np.nan); w=(1/v); w/=w.sum(); rr=df.dot(w)
for lo,hi in [("2019-01-01","2022-12-31"),("2023-01-01","2026-12-31")]:
    x=rr[(rr.index>=lo)&(rr.index<=hi)]
    sr=x.mean()/x.std()*np.sqrt(252); dd=((1+x).cumprod()/(1+x).cumprod().cummax()-1).min()
    print(f"  IV 6stream {lo[:4]}-{hi[:4]}: SR {sr:.3f} MaxDD {dd*100:.1f}% n={len(x)}")
print("\nIV weights:", {k:round(v,2) for k,v in zip(names6,w)})
