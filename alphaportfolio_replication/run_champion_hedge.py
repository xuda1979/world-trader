#!/usr/bin/env python3
"""CHAMPION + SPY-short trend hedge (20y walk-forward).

Same composite as run_champion_composite.py (composite momentum 3+6+12mo,
30% 2mo-reversal LS sleeve, SPY10MA momentum gate, VIX-level de-risk,
vol-target + DD reducer) PLUS an untested lever for the MaxDD < 10% target:

  HEDGE: when SPY < 10-month MA (momentum gate OFF), short SPY by HEDGE
         fraction of equity instead of standing flat. Active negative-beta
         during down-trends vs the champion's near-cash state.

Costs: explicit 6 bps one-way on one-way turnover (momentum full churn
monthly + reversal sleeve + hedge establish/close), so net = gross - cost.
Both gross and net reported; HEDGE=0 reproduces the champion baseline.
"""
from __future__ import annotations
import os, sys, glob
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import risk_gate as rg
BIG_DIR = os.path.join(HERE, "..", "tools", "quant", "data", "twelve_big")
START_YM = os.environ.get("START_YM", "2008-01")
COST_BPS = float(os.environ.get("COST_BPS", 6.0))
VOL_TARGET = float(os.environ.get("VOL_TARGET", 0.15))
REV_SLEEVE = float(os.environ.get("REV_SLEEVE", 0.3))
HEDGE = float(os.environ.get("HEDGE", 0.0))

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
    """Long-only top-quartile of composite momentum signal."""
    fr=fwd.loc[dt]; s=sig.loc[dt].dropna(); c=s.index.intersection(fr.dropna().index)
    if len(c)<20: return 0.0
    s=s.loc[c]; fr2=fr.loc[c]; G=max(1,len(c)//4); r2=s.sort_values(ascending=False)
    return fr2.loc[r2.index[:G]].mean()

def SP(dt,sig,fwd):
    """Market-neutral long-short of reversal signal (top G long, bottom G short)."""
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
    spy_fwd=spy.pct_change(1).shift(-1)
    vix=rg.load_daily("vix").resample("ME").last()
    oos=[d for d in px.index if d.strftime("%Y-%m")>=START_YM]
    v=lambda dt: float(vix.asof(dt)) if pd.notna(vix.asof(dt)) else 20
    sp10=lambda dt: 1.0 if float(spy.asof(dt))>=spy[spy.index<=dt].tail(10).mean() else 0.0
    vg=lambda dt: 0.3 if v(dt)>30 else (0.5 if v(dt)>25 else (0.75 if v(dt)>20 else 1.0))

    raw=[]; legs=[]; costs=[]; prev_g=0.0
    for dt in oos:
        g=sp10(dt)
        momp=g*LM(dt,comp,fwd)                     # momentum long (gated)
        revp=REV_SLEEVE*SP(dt,rev,fwd)             # reversal LS sleeve
        hedg=-(1-g)*HEDGE*float(spy_fwd.asof(dt))  # short SPY when gate OFF
        book=(momp+revp)*vg(dt)+hedg
        # one-way turnover estimate: momentum ~0.5 (topQ churn), reversal 0.3*0.5,
        # hedge 0 if gate state unchanged, ~1.0 of |HEDGE| on flip
        turn=0.65+HEDGE*abs((1-g)-(1-prev_g))
        raw.append(book); legs.append((momp,revp,hedg,vg(dt))); costs.append(turn*COST_BPS/1e4)
        prev_g=g
    raw=np.array(raw); costs=np.array(costs)
    # Vol target + DD reducer on GROSS book; net = scaled gross - scaled cost
    scaled=np.zeros(len(raw)); eq=1.0; peak=1.0; scale=np.ones(len(raw))
    for i in range(len(raw)):
        s=1.0
        if i>=6:
            rv=np.std(raw[max(0,i-6):i])*np.sqrt(12)+1e-6
            s=min(VOL_TARGET/rv,1.5)
            cur_dd=eq/peak-1
            if cur_dd<-0.12: s*=0.25
            elif cur_dd<-0.08: s*=0.5
        scale[i]=s
        scaled[i]=raw[i]*s
        eq*=(1+scaled[i]); peak=max(peak,eq)
    r_gross=scaled; r_net=scaled-costs*scale
    def stats(r):
        sr=r.mean()/r.std()*np.sqrt(12) if r.std()>0 else 0
        ann=r.mean()*12*100; vol=r.std()*np.sqrt(12)*100
        eq2=np.cumprod(1+r); dd=min((eq2[i]/max(eq2[:i+1])-1) for i in range(len(eq2)))*100
        return sr,ann,vol,dd
    for tag,r in (("GROSS",r_gross),("NET  ",r_net)):
        sr,ann,vol,dd=stats(r)
        print(f"HEDGE={HEDGE:.2f} {tag}: SR={sr:.3f} ret={ann:+.2f}% vol={vol:.2f}% MaxDD={dd:.2f}% n={len(r)}")
    # worst months decomposition
    idx=np.argsort(r_net)[:8]
    print("worst months (net): ym  mom  rev  hedge vg   net%")
    for i in sorted(idx):
        m_,rv,h,vgg=legs[i]
        print(f"  {oos[i].strftime('%Y-%m')} {m_:+7.3f} {rv:+6.3f} {h:+6.3f} {vgg:4.2f} {r_net[i]*100:+6.2f}")

if __name__=="__main__": main()
