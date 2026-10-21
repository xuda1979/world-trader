#!/usr/bin/env python3
"""CHAMPION composite + defensive tilt on the momentum book (20y).

Motivation (2026-08-12): the champion's binding MaxDD month is 2018-09
(net -13.8%) where the EQUAL-WEIGHT top-quartile momentum book (high-beta
growth names) gets crushed while the month-end gate is still ON. Every
de-risking lever (VIX gates, crash filters, hedge, cadence, reducer
resolution) fails. Untested: change WHAT the book holds, not how much.

TILT variants (momentum leg only; reversal sleeve unchanged):
  none    - equal-weight top quartile (champion, must reproduce 0.933/14.4/-16)
  vol     - inverse-6m-vol weights within the top quartile (w_i ~ 1/sigma_i)
  lowvol  - restrict to the lower-vol HALF of the top quartile (G/2 names)
Turnover is tracked on real weights (0.5*sum|w_t - w_{t-1}|) at 6 bps
one-way; reversal sleeve fixed at 0.15/month churn.
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
TILT = os.environ.get("TILT", "none")

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

def mom_leg(dt, sig, fwd, vol6, tilt):
    """Weighted top-quartile momentum forward return for tilt variant."""
    fr=fwd.loc[dt]; s=sig.loc[dt].dropna(); c=s.index.intersection(fr.dropna().index)
    if len(c)<20: return 0.0, {}, 0.0
    s=s.loc[c]; fr2=fr.loc[c]; G=max(1,len(c)//4)
    top=list(s.sort_values(ascending=False).index[:G])
    if tilt=="vol":
        v=vol6.loc[dt, top].replace(0,np.nan).dropna()
        if len(v)<max(1,G//2):  # too many missing vols -> equal weight
            w={k:1.0/G for k in top}
        else:
            inv=1.0/v; w=(inv/inv.sum()).to_dict()
    elif tilt=="lowvol":
        v=vol6.loc[dt, top].dropna().sort_values()
        keep=list(v.index[:max(1,len(v)//2)])
        w={k:1.0/len(keep) for k in keep}
    else:
        w={k:1.0/G for k in top}
    keys=[k for k in w if k in fr2.index]
    if not keys: return 0.0, {}, 0.0
    ret=sum(w[k]*fr2[k] for k in keys)/sum(w[k] for k in keys)
    return ret, w, len(keys)

def main():
    print("Building panel...", flush=True)
    px=build_panel()
    print(f"Panel: {px.shape[0]}mo x {px.shape[1]} stocks", flush=True)
    fwd=px.pct_change(1).shift(-1)
    comp=(px.pct_change(3)+px.pct_change(6)+px.pct_change(12))/3
    rev=-px.pct_change(2)
    vol6=px.pct_change(1).rolling(6).std()
    spy=rg.load_daily("SPY").resample("ME").last()
    vix=rg.load_daily("vix").resample("ME").last()
    oos=[d for d in px.index if d.strftime("%Y-%m")>=START_YM]
    v=lambda dt: float(vix.asof(dt)) if pd.notna(vix.asof(dt)) else 20
    sp10=lambda dt: 1.0 if float(spy.asof(dt))>=spy[spy.index<=dt].tail(10).mean() else 0.0
    vg=lambda dt: 0.3 if v(dt)>30 else (0.5 if v(dt)>25 else (0.75 if v(dt)>20 else 1.0))

    raw=[]; costs=[]; prev_w={}
    for dt in oos:
        g=sp10(dt)
        mom_ret, w, n= mom_leg(dt, comp, fwd, vol6, TILT)
        # reversal sleeve: market-neutral LS, 0.15 monthly churn estimate
        s2=rev.loc[dt].dropna(); fr2=fwd.loc[dt].dropna(); c2=s2.index.intersection(fr2.index)
        if len(c2)>=20:
            G2=max(1,len(c2)//4); r2=s2.loc[c2].sort_values(ascending=False)
            revp=REV_SLEEVE*(fr2.loc[r2.index[:G2]].mean()-fr2.loc[r2.index[-G2:]].mean())
        book=(g*mom_ret+revp)*vg(dt)
        raw.append(book)
        # turnover: momentum weight change (incl. gate flip) + reversal 0.15
        if isinstance(prev_w,dict) and prev_w and w:
            t0=0.5*sum(abs(w.get(k,0)-prev_w.get(k,0)) for k in set(w)|set(prev_w))
        else:
            t0=0.5*sum(abs(x) for x in w.values()) if w else 0.0
        costs.append((t0+0.15)*COST_BPS/1e4)
        prev_w=w
    raw=np.array(raw); costs=np.array(costs)
    scaled=np.zeros(len(raw)); eq=1.0; peak=1.0; scale=np.ones(len(raw))
    for i in range(len(raw)):
        s=1.0
        if i>=6:
            rv=np.std(raw[max(0,i-6):i])*np.sqrt(12)+1e-6
            s=min(VOL_TARGET/rv,1.5)
            cur_dd=eq/peak-1
            if cur_dd<-0.12: s*=0.25
            elif cur_dd<-0.08: s*=0.5
        scale[i]=s; scaled[i]=raw[i]*s
        eq*=(1+scaled[i]); peak=max(peak,eq)
    r_net=scaled-costs*scale
    def stats(r):
        sr=r.mean()/r.std()*np.sqrt(12) if r.std()>0 else 0
        ann=r.mean()*12*100; vol=r.std()*np.sqrt(12)*100
        eq2=np.cumprod(1+r); dd=min((eq2[i]/max(eq2[:i+1])-1) for i in range(len(eq2)))*100
        return sr,ann,vol,dd
    gsr,gret,gvol,gdd=stats(scaled)
    sr,ann,vol,dd=stats(r_net)
    print(f"TILT={TILT:6s} GROSS: SR={gsr:.3f} ret={gret:+.2f}% vol={gvol:.2f}% MaxDD={gdd:.2f}% | NET: SR={sr:.3f} ret={ann:+.2f}% vol={vol:.2f}% MaxDD={dd:.2f}%")
    idx=np.argsort(r_net)[:5]
    print("  worst 5 (net):", " ".join(f"{oos[i].strftime('%Y-%m')} {r_net[i]*100:+.1f}%" for i in sorted(idx)))

if __name__=="__main__": main()
