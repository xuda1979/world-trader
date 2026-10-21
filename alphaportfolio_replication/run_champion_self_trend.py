#!/usr/bin/env python3
"""PORTFOLIO SELF-TREND gate variant of the champion composite.

The champion's MaxDD (-15.95%) is a 22-month slow grind (2021-12..2023-09),
not a sharp crash — crash filters fire too late (after the damage) or skip
V-recoveries. A portfolio self-trend gate scales exposure by the strategy's
OWN trailing return: when the book has lost money over the last N months,
halve/quarter exposure; restore as it recovers. This targets slow grinds.

Baseline champion (run_champion_composite.py, vt15, 6bps):
    SR 0.933, ret 14.43%, MaxDD -15.95%, 2008-2026 (224 months)

Env knobs:
  SELF_TREND_WIN  months of own-return lookback (default 12)
  SELF_TREND_TH   scale down when own win-return < th (default 0.0)
  SELF_TREND_FAC  down-scale factor (default 0.5)
"""
from __future__ import annotations
import os, sys, glob
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import risk_gate as rg
BIG_DIR = os.path.join(HERE, "..", "tools", "quant", "data", "twelve_big")
OUT_CSV = os.environ.get("OUT_CSV", "wf_champion_selftrend.csv")
START_YM = os.environ.get("START_YM", "2008-01")
COST_BPS = float(os.environ.get("COST_BPS", 6.0))
VOL_TARGET = float(os.environ.get("VOL_TARGET", 0.15))
REV_SLEEVE = float(os.environ.get("REV_SLEEVE", 0.3))
SELF_TREND_WIN = int(os.environ.get("SELF_TREND_WIN", 12))
SELF_TREND_TH = float(os.environ.get("SELF_TREND_TH", 0.0))
SELF_TREND_FAC = float(os.environ.get("SELF_TREND_FAC", 0.5))
def build_panel():
    files = sorted(glob.glob(os.path.join(BIG_DIR, "*.csv")))
    all_m=[]
    for f in files:
        sym=os.path.basename(f).replace(".csv","")
        try:
            df=pd.read_csv(f, index_col=0, parse_dates=True)
            c="close" if "close" in df.columns else df.columns[0]
            m=df[c].astype(float).resample("ME").last().dropna(); m.name=sym
            all_m.append(m)
        except: continue
    return pd.concat(all_m,axis=1).sort_index().ffill()
def LM(dt,sig,fwd):
    fr=fwd.loc[dt]; s=sig.loc[dt].dropna(); c=s.index.intersection(fr.dropna().index)
    if len(c)<20: return 0.0
    s=s.loc[c]; fr2=fr.loc[c]; G=max(1,len(c)//4); r2=s.sort_values(ascending=False)
    return fr2.loc[r2.index[:G]].mean()
def SP(dt,sig,fwd):
    fr=fwd.loc[dt]; s=sig.loc[dt].dropna(); c=s.index.intersection(fr.dropna().index)
    if len(c)<20: return 0.0
    s=s.loc[c]; fr2=fr.loc[c]; G=max(1,len(c)//4); r2=s.sort_values(ascending=False)
    return fr2.loc[r2.index[:G]].mean()-fr2.loc[r2.index[-G:]].mean()
def main():
    print("Building panel...", flush=True)
    px=build_panel()
    print(f"Panel: {px.shape[0]}mo x {px.shape[1]} stocks", flush=True)
    fwd=px.pct_change(1).shift(-1)
    comp=(px.pct_change(3)+px.pct_change(6)+px.pct_change(12))/3
    rev=-px.pct_change(2)
    spy=rg.load_daily("SPY").resample("ME").last()
    vix=rg.load_daily("vix").resample("ME").last()
    oos=[d for d in px.index if d.strftime("%Y-%m")>=START_YM]
    v=lambda dt: float(vix.asof(dt)) if pd.notna(vix.asof(dt)) else 20
    sp10=lambda dt: 1.0 if float(spy.asof(dt))>=spy[spy.index<=dt].tail(10).mean() else 0.0
    vg=lambda dt: 0.3 if v(dt)>30 else (0.5 if v(dt)>25 else (0.75 if v(dt)>20 else 1.0))
    raw=[]
    for dt in oos:
        momp=1.0*sp10(dt)*LM(dt,comp,fwd)
        revp=REV_SLEEVE*SP(dt,rev,fwd)
        raw.append((momp+revp)*vg(dt))
    raw=np.array(raw)
    # Vol target + DD reducer + SELF-TREND gate
    scaled=np.zeros(len(raw)); eq=1.0; peak=1.0
    own_trail=1.0
    for i in range(len(raw)):
        s=1.0
        if i>=6:
            rv=np.std(raw[max(0,i-6):i])*np.sqrt(12)+1e-6
            s=min(VOL_TARGET/rv,1.5)
            cur_dd=eq/peak-1
            if cur_dd<-0.12: s*=0.25
            elif cur_dd<-0.08: s*=0.5
            # SELF-TREND: own trailing W-month compounded return < th -> scale
            if i>=SELF_TREND_WIN:
                own_trail=(1+scaled[i-SELF_TREND_WIN:i]).prod()-1
                if own_trail < SELF_TREND_TH: s*=SELF_TREND_FAC
        scaled[i]=raw[i]*s
        eq*=(1+scaled[i]); peak=max(peak,eq)
    r=scaled
    sr=r.mean()/r.std()*np.sqrt(12) if r.std()>0 else 0
    ann=r.mean()*12*100; vol=r.std()*np.sqrt(12)*100
    eq2=np.cumprod(1+r); dd=min((eq2[i]/max(eq2[:i+1])-1) for i in range(len(eq2)))*100
    print(f"SELF-TREND win={SELF_TREND_WIN} th={SELF_TREND_TH:.2f} fac={SELF_TREND_FAC:.2f}: "
          f"SR={sr:.3f} ret={ann:+.2f}% vol={vol:.2f}% MaxDD={dd:.2f}% n={len(r)}")
    pd.DataFrame({"ym":[d.strftime("%Y-%m") for d in oos[:len(r)]], "net":r}).to_csv(os.path.join(HERE,"data",OUT_CSV), index=False)
if __name__=="__main__": main()
