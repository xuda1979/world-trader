#!/usr/bin/env python3
"""SHARP-REVERSAL crash filter variant of the champion composite.

Question (2026-08-12 loop): the blunt crash filter (skip momentum after any
SPY -3%/-5% month) kills return (12.8% -> 3-5%) because it fires on ~20-30
ordinary down months. Can a filter that fires ONLY on the momentum-crash
signature — SPY above its 10MA last month, THEN a sharp 3m/1m drop (the
2018-Q4 type) — cut MaxDD without collapsing return?

Baseline champion (run_champion_composite.py, vt15, 6bps):
    SR 0.933, ret 14.43%, MaxDD -15.95%, 2008-2026 (224 months)

Env knobs:
  CRASH_3M_TH  e.g. -0.08 : fire if SPY 3m ret < th AND SPY>10MA at t-1
  CRASH_1M_TH  e.g. -0.08 : fire if SPY 1m ret < th AND SPY>10MA at t-1
  CRASH_FACTOR e.g. 0.0   : exposure multiplier when fired
"""
from __future__ import annotations
import os, sys, glob
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import risk_gate as rg
BIG_DIR = os.path.join(HERE, "..", "tools", "quant", "data", "twelve_big")
OUT_CSV = os.environ.get("OUT_CSV", "wf_champion_sharp.csv")
START_YM = os.environ.get("START_YM", "2008-01")
COST_BPS = float(os.environ.get("COST_BPS", 6.0))
VOL_TARGET = float(os.environ.get("VOL_TARGET", 0.15))
REV_SLEEVE = float(os.environ.get("REV_SLEEVE", 0.3))
CRASH_3M_TH = float(os.environ.get("CRASH_3M_TH", 0.0))
CRASH_1M_TH = float(os.environ.get("CRASH_1M_TH", 0.0))
CRASH_FACTOR = float(os.environ.get("CRASH_FACTOR", 0.0))
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
    spy_m=spy[spy.index>=px.index[0]]
    spy_3m=spy_m.pct_change(3)
    spy_1m=spy_m.pct_change(1)
    spy_ma10=spy_m.rolling(10).mean()
    oos=[d for d in px.index if d.strftime("%Y-%m")>=START_YM]
    v=lambda dt: float(vix.asof(dt)) if pd.notna(vix.asof(dt)) else 20
    sp10=lambda dt: 1.0 if float(spy.asof(dt))>=spy[spy.index<=dt].tail(10).mean() else 0.0
    vg=lambda dt: 0.3 if v(dt)>30 else (0.5 if v(dt)>25 else (0.75 if v(dt)>20 else 1.0))
    def crash(dt):
        """Fire ONLY on momentum-crash signature: above 10MA at t-1, sharp drop."""
        if dt not in spy_m.index: return False
        i = spy_m.index.get_loc(dt)
        if i < 1: return False
        above_prev = float(spy_m.iloc[i-1]) >= float(spy_ma10.iloc[i-1])
        if not above_prev: return False
        r3 = float(spy_3m.iloc[i]) if i >= 3 and pd.notna(spy_3m.iloc[i]) else 0.0
        r1 = float(spy_1m.iloc[i]) if pd.notna(spy_1m.iloc[i]) else 0.0
        return (CRASH_3M_TH < 0 and r3 < CRASH_3M_TH) or (CRASH_1M_TH < 0 and r1 < CRASH_1M_TH)
    raw=[]; fires=[]; fired=0
    for dt in oos:
        momp=1.0*sp10(dt)*LM(dt,comp,fwd)
        revp=REV_SLEEVE*SP(dt,rev,fwd)
        base=(momp+revp)*vg(dt)
        if crash(dt):
            base*=CRASH_FACTOR; fired+=1; fires.append(dt.strftime("%Y-%m"))
        raw.append(base)
    raw=np.array(raw)
    # Vol target + DD reducer
    scaled=np.zeros(len(raw)); eq=1.0; peak=1.0
    for i in range(len(raw)):
        s=1.0
        if i>=6:
            rv=np.std(raw[max(0,i-6):i])*np.sqrt(12)+1e-6
            s=min(VOL_TARGET/rv,1.5)
            cur_dd=eq/peak-1
            if cur_dd<-0.12: s*=0.25
            elif cur_dd<-0.08: s*=0.5
        scaled[i]=raw[i]*s
        eq*=(1+scaled[i]); peak=max(peak,eq)
    r=scaled
    sr=r.mean()/r.std()*np.sqrt(12) if r.std()>0 else 0
    ann=r.mean()*12*100; vol=r.std()*np.sqrt(12)*100
    eq2=np.cumprod(1+r); dd=min((eq2[i]/max(eq2[:i+1])-1) for i in range(len(eq2)))*100
    print(f"SHARP-CRASH 3m={CRASH_3M_TH:.3f} 1m={CRASH_1M_TH:.3f} f={CRASH_FACTOR:.2f}: "
          f"SR={sr:.3f} ret={ann:+.2f}% vol={vol:.2f}% MaxDD={dd:.2f}% n={len(r)} "
          f"fired={fired} ({', '.join(fires) if fires else 'none'})")
    pd.DataFrame({"ym":[d.strftime("%Y-%m") for d in oos[:len(r)]], "net":r}).to_csv(os.path.join(HERE,"data",OUT_CSV), index=False)
if __name__=="__main__": main()
