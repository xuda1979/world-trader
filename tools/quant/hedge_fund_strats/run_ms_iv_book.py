"""Deployable runner: multi-strategy inverse-vol blend daily stream (2026-08-13).

Produces ms_iv_daily.csv (date-indexed daily returns) for the VALIDATED
multi-strategy IV book:
  L/S 130/30 vol-managed + Risk Parity + CTA Futures + FX Carry
  + AP gold composite + LS n10r14 (2019-2026, 6 bps, inverse-vol weighted).

Validated: SR 1.24, MaxDD -5.9% (2019-2026, n=2054); OOS walk-forward
SR 1.0/1.5 (both halves beat EW); split-half positive.

Usage: python tools/quant/hedge_fund_strats/run_ms_iv_book.py
Writes: tools/quant/hedge_fund_strats/results/ms_iv_daily.csv
"""
from pathlib import Path
import pandas as pd, numpy as np
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
names=["ls_volman","riskparity","cta_fut","fx_carry","ap_gold","ls_n10r14"]
df=pd.concat([sts[n] for n in names],axis=1)["2019-01-01":].ffill().dropna()
v=df.std().replace(0,np.nan); w=(1/v); w/=w.sum()
r=df.dot(w)
p=pd.DataFrame({"daily_return": r.values}, index=r.index)
p.index.name="date"
out=RES/"ms_iv_daily.csv"
p.to_csv(out)
eq=(1+r).cumprod(); sr=r.mean()/r.std()*np.sqrt(252); dd=(eq/eq.cummax()-1).min(); ret=(eq.iloc[-1])**(252/len(r))-1
print(f"Wrote {out}")
print(f"IV multi-strategy book: SR {sr:.3f} | ret {ret*100:.1f}% | MaxDD {dd*100:.1f}% | n={len(r)}")
print(f"IV weights: { {k:round(x,2) for k,x in zip(names,w)} }")
