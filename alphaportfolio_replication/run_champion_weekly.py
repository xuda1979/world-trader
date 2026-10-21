#!/usr/bin/env python3
"""WEEKLY REBALANCE variant of the champion composite (momentum+reversal).

Tests the "react faster to momentum crashes" lever: weekly signals/holds
instead of monthly. Real costs: 6bps on weekly one-way turnover (measured
properly — mom book membership change + rev sleeve L/S churn).

Baseline champion (monthly, vt15, 6bps): SR 0.933, ret 14.43%, DD -15.95%.
Gold 20 sleeve (monthly): SR 1.053, ret 15.10%, DD -15.00%.
"""
from __future__ import annotations
import os, sys, glob
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import risk_gate as rg
BIG_DIR = os.path.join(HERE, "..", "tools", "quant", "data", "twelve_big")
GLD_CSV = os.path.join(HERE, "..", "tools", "quant", "data", "twelvedata", "GLD.csv")
OUT_CSV = os.environ.get("OUT_CSV", "wf_champion_weekly.csv")
START_DT = os.environ.get("START_DT", "2008-01-01")
COST_BPS = float(os.environ.get("COST_BPS", 6.0))
VOL_TARGET = float(os.environ.get("VOL_TARGET", 0.15))
REV_SLEEVE = float(os.environ.get("REV_SLEEVE", 0.3))
GOLD_W = float(os.environ.get("GOLD_W", 0.0))
ANNUAL = 52
def build_panel(rule):
    files = sorted(glob.glob(os.path.join(BIG_DIR, "*.csv")))
    all_m=[]
    for f in files:
        sym=os.path.basename(f).replace(".csv","")
        try:
            df=pd.read_csv(f, index_col=0, parse_dates=True)
            c="close" if "close" in df.columns else df.columns[0]
            m=df[c].astype(float).resample(rule).last().dropna(); m.name=sym
            all_m.append(m)
        except: continue
    return pd.concat(all_m,axis=1).sort_index().ffill()
def load_gold(rule):
    df=pd.read_csv(GLD_CSV, index_col=0, parse_dates=True)
    c="close" if "close" in df.columns else df.columns[0]
    return df[c].astype(float).resample(rule).last().dropna()
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
    rule = "W-FRI"
    print("Building weekly panel...", flush=True)
    px=build_panel(rule)
    print(f"Panel: {px.shape[0]}w x {px.shape[1]} stocks", flush=True)
    fwd=px.pct_change(1).shift(-1)
    # momentum lookbacks in weekly units (21d~1mo -> 4w, 63d->12w, 252d->52w)
    comp=(px.pct_change(12)+px.pct_change(26)+px.pct_change(52))/3
    rev=-px.pct_change(8)  # ~2mo reversal
    spy=rg.load_daily("SPY").resample(rule).last()
    vix=rg.load_daily("vix").resample(rule).last()
    gld=load_gold(rule); gld_ret=gld.pct_change().reindex(px.index).fillna(0.0)
    oos=[d for d in px.index if d>=pd.Timestamp(START_DT)]
    v=lambda dt: float(vix.asof(dt)) if pd.notna(vix.asof(dt)) else 20
    sp10=lambda dt: 1.0 if float(spy.asof(dt))>=spy[spy.index<=dt].tail(10).mean() else 0.0
    vg=lambda dt: 0.3 if v(dt)>30 else (0.5 if v(dt)>25 else (0.75 if v(dt)>20 else 1.0))
    mom_sets=[]; rev_sets=[]
    for dt in oos:
        s=comp.loc[dt].dropna(); G=max(1,len(s)//4)
        mom_sets.append(set(s.sort_values(ascending=False).index[:G].tolist()))
        r=rev.loc[dt].dropna().sort_values(ascending=False)
        rev_sets.append((set(r.index[:G].tolist()), set(r.index[-G:].tolist())))
    raw=[]; cost_arr=[]; prev=None
    for i,dt in enumerate(oos):
        momp=1.0*sp10(dt)*LM(dt,comp,fwd)
        revp=REV_SLEEVE*SP(dt,rev,fwd)
        book=(momp+revp)*vg(dt)
        gr=float(gld_ret.loc[dt]) if dt in gld_ret.index else 0.0
        raw.append((1-GOLD_W)*book + GOLD_W*gr)
        # cost: one-way turnover = mom membership churn + rev L/S churn
        if prev is None:
            cost_arr.append(0.0)
        else:
            mo = 1 - len(prev[0] & mom_sets[i])/max(1,len(mom_sets[i]))
            rp, rs = prev[1]; cp, cs = rev_sets[i]
            ro = (1-len(rp&cp)/max(1,len(cp)) + 1-len(rs&cs)/max(1,len(cs)))/2
            turn = mo + REV_SLEEVE*2*ro
            cost_arr.append(COST_BPS/1e4 * turn)
        prev=(mom_sets[i], rev_sets[i])
    raw=np.array(raw); cost_arr=np.array(cost_arr)
    net=raw-cost_arr
    # Vol target + DD reducer (on net)
    scaled=np.zeros(len(net)); eq=1.0; peak=1.0
    for i in range(len(net)):
        s=1.0
        if i>=6:
            rv=np.std(net[max(0,i-6):i])*np.sqrt(ANNUAL)+1e-6
            s=min(VOL_TARGET/rv,1.5)
            cur_dd=eq/peak-1
            if cur_dd<-0.12: s*=0.25
            elif cur_dd<-0.08: s*=0.5
        scaled[i]=net[i]*s
        eq*=(1+scaled[i]); peak=max(peak,eq)
    r=scaled
    sr=r.mean()/r.std()*np.sqrt(ANNUAL) if r.std()>0 else 0
    ann=r.mean()*ANNUAL*100; vol=r.std()*np.sqrt(ANNUAL)*100
    eq2=np.cumprod(1+r); dd=min((eq2[i]/max(eq2[:i+1])-1) for i in range(len(eq2)))*100
    print(f"WEEKLY gold={GOLD_W:.0%}: SR={sr:.3f} ret={ann:+.2f}% vol={vol:.2f}% "
          f"MaxDD={dd:.2f}% n={len(r)} cost_drag={cost_arr.mean()*ANNUAL*100:.2f}%/yr "
          f"turn={cost_arr.mean()/ (COST_BPS/1e4):.1%}/wk")
    pd.DataFrame({"dt":[d.strftime("%Y-%m-%d") for d in oos[:len(r)]], "net":r}).to_csv(os.path.join(HERE,"data",OUT_CSV), index=False)
if __name__=="__main__": main()
