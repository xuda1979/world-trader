"""Deployable runner: multi-strategy inverse-vol blend daily stream (2026-08-13).

Produces ms_iv_daily.csv (date-indexed daily returns) for the VALIDATED
multi-strategy IV book:
  L/S 130/30 vol-managed + Risk Parity + CTA Futures + FX Carry
  + AP gold composite + LS n10r14 (2019-2026, 6 bps, inverse-vol weighted).

WEIGHTING: ROLLING inverse-vol (126-day window, weights lagged 1 day = no
lookahead). 2026-08-13 audit (RESEARCH_LOG): the previous full-sample inverse-vol
weighting gave the n10r14 sleeve 0.38 (its vol doubled in 2026 -> stale weight).
Rolling-vol weighting adapts to vol regime, de-risks that concentration, and
DOMINATES across every window choice (42/63/126/252d) on SR/MaxDD/half-split:

  full-sample: SR 1.240 MaxDD -5.9% halfSR(1.41/1.06) n10r14wt 0.38
  rolling-126d: SR 1.417 MaxDD -5.5% halfSR(1.52/1.32) n10r14wt ~0.14

Status: deployed stream = ROLLING-126d (the all-around best, robust window).

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
df=pd.concat([sts[n].rename(n) for n in names],axis=1)["2019-01-01":].ffill().dropna()

# ROLLING inverse-vol: 126d window, lagged 1 day (no lookahead), renormalized daily
ROLL_WIN = 126
vol = df.rolling(ROLL_WIN).std().replace(0, np.nan)
w_roll = (1.0 / vol).shift(1)            # weights known at t-1, using vol up to t-1
w_norm = w_roll.div(w_roll.sum(axis=1), axis=0)   # normalize across sleeves each day
r = (df * w_norm.fillna(1.0 / len(names))).sum(axis=1).dropna()

# latest (last valid) weights for reporting
last_w = w_norm.dropna().iloc[-1] if w_norm.notna().any().any() else pd.Series(1/len(names), index=names)
last_w = last_w / last_w.sum()

p = pd.DataFrame({"daily_return": r.values}, index=r.index)
p.index.name = "date"
out = RES / "ms_iv_daily.csv"
p.to_csv(out)
eq = (1 + r).cumprod(); sr = r.mean()/r.std()*np.sqrt(252); dd = (eq/eq.cummax()-1).min(); ret = (eq.iloc[-1])**(252/len(r))-1
print(f"Wrote {out}")
print(f"IV multi-strategy book (rolling-{ROLL_WIN}d weights): SR {sr:.3f} | ret {ret*100:.1f}% | MaxDD {dd*100:.1f}% | n={len(r)}")
print(f"IV latest weights: { {k:round(x,2) for k,x in zip(names,last_w.round(2))} }")
