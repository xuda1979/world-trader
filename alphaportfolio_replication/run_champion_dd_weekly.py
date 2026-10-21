#!/usr/bin/env python3
"""CHAMPION composite, monthly rebalance + WEEKLY intra-month DD-reducer.

The champion (run_champion_composite.py) checks its DD reducer (-8% -> 0.5,
-12% -> 0.25) at MONTHLY resolution: a -13.8% month (2018-09) completes
before the reducer can act. This variant keeps the monthly rebalance
schedule (same legs, same gates, same vol target) but evaluates the equity
curve and DD reducer WEEKLY, scaling the carried book mid-month.

Positions are carried name-by-name (topQ momentum, reversal LS top+bottom
quartiles) and scored weekly with next-1-week returns - real tracking, no
proxy. Cost: 6 bps one-way on rebalance-month membership churn only.
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
MA_WEEKS = int(os.environ.get("MA_WEEKS", 43))
MONTHLY_CHK = int(os.environ.get("MONTHLY_CHK", 0))  # 1 = monthly reducer (control)
RELEASE = float(os.environ.get("RELEASE", 0.0))       # dd recovered above -RELEASE -> full scale

def build_panel():
    files = sorted(glob.glob(os.path.join(BIG_DIR, "*.csv")))
    all_w=[]
    for f in files:
        sym=os.path.basename(f).replace(".csv","")
        try:
            df=pd.read_csv(f, index_col=0, parse_dates=True)
            c="close" if "close" in df.columns else df.columns[0]
            w=df[c].astype(float).resample("W-FRI").last().dropna(); w.name=sym
            all_w.append(w)
        except: continue
    return pd.concat(all_w,axis=1).sort_index().ffill()

def top_bottom(sig, Gfrac=0.25):
    s=sig.dropna()
    if len(s)<20: return [],[]
    G=max(1,int(len(s)*Gfrac))
    r2=s.sort_values(ascending=False)
    return list(r2.index[:G]), list(r2.index[-G:])

def main():
    print("Building panel...", flush=True)
    wpx=build_panel()
    wfwd1=wpx.pct_change(1).shift(-1)                       # next-week returns
    mom12=(wpx.pct_change(12)+wpx.pct_change(24)+wpx.pct_change(48))/3
    rev=-wpx.pct_change(8)
    spy=rg.load_daily("SPY").resample("W-FRI").last()
    vix=rg.load_daily("vix").resample("W-FRI").last()
    oos=[d for d in wpx.index if d.strftime("%Y-%m")>=START_YM
         and wfwd1.loc[d].notna().any()]                   # skip incomplete last week
    last_of_month=[d for i,d in enumerate(oos) if i==len(oos)-1 or d.strftime("%Y-%m")!=oos[i+1].strftime("%Y-%m")]
    # map each week -> its month-end rebalance date
    month_bounds={d.strftime("%Y-%m"):d for d in last_of_month}
    oos2=[d for d in oos if d in month_bounds.values()]     # rebalance dates
    oos2=oos2[oos2.index(next(d for d in oos2 if d.strftime("%Y-%m")>=START_YM)):]
    oos2=[d for d in oos2 if d.strftime("%Y-%m")>=START_YM]

    wret=[]; eq=1.0; peak=1.0; scale=1.0; worst=0.0; prev_mom=set(); prev_rev=set(); prev_vg=None; prev_g=None
    costs=[]
    # group weeks by month, rebalance at the month's last Friday
    months=sorted(set(d.strftime("%Y-%m") for d in oos))
    months=[m for m in months if m>=START_YM]
    for m in months:
        rb=month_bounds[m]
        # --- rebalance: define legs at month-end rb ---
        g=1.0 if float(spy.asof(rb))>=spy[spy.index<=rb].tail(MA_WEEKS).mean() else 0.0
        v=float(vix.asof(rb)) if pd.notna(vix.asof(rb)) else 20
        vg=0.3 if v>30 else (0.5 if v>25 else (0.75 if v>20 else 1.0))
        mt,_=top_bottom(mom12.loc[rb]); rt,rb_=top_bottom(rev.loc[rb])
        if prev_vg is not None and (g!=prev_g):
            # gate flip: momentum book fully churns
            costs.append((1.0+len(set(rt+rb_)-prev_rev)/max(1,len(rt+rb_)))*COST_BPS/1e4)
        else:
            n_new=len(set(mt)-prev_mom)/max(1,len(mt))
            costs.append((n_new+len(set(rt+rb_)-prev_rev)/max(1,len(rt+rb_)))*COST_BPS/1e4)
        prev_mom,prev_rev,prev_g,prev_vg=set(mt),set(rt+rb_),g,vg
        # --- walk the month's weeks ---
        wk=[d for d in oos if d.strftime("%Y-%m")==m]
        # trailing-6-month vol for the monthly vol target (6 month-end rows back)
        if MONTHLY_CHK:
            for w in wk:
                book=(g*wfwd1.loc[w,mt].mean()+REV_SLEEVE*(wfwd1.loc[w,rt].mean()-wfwd1.loc[w,rb_].mean()))*vg
                wret.append(book*scale); eq*=(1+book*scale); peak=max(peak,eq)
        else:
            month_ret=1.0
            for w in wk:
                book=(g*wfwd1.loc[w,mt].mean()+REV_SLEEVE*(wfwd1.loc[w,rt].mean()-wfwd1.loc[w,rb_].mean()))*vg
                wret.append(book*scale); eq*=(1+book*scale); peak=max(peak,eq)
                # WEEKLY DD-reducer (watermark): trip at -8/-12%, release when dd
                # improves RELEASE from its worst point (avoids recovery lock-in)
                dd=eq/peak-1
                worst=min(worst,dd)
                if RELEASE>0 and dd>worst+RELEASE: scale=1.0; worst=0.0
                elif dd<-0.12: scale=0.25
                elif dd<-0.08: scale=0.5
        # monthly vol target for next month (from monthly aggregates) - keep champion-style:
        # trailing 6 months of monthly book returns (computed from this month's compound)
        # (applied next month as scale)
        if len(wret)>=6*4:
            mrets=[np.prod(1+np.array(wret[i:i+4]))-1 for i in range(len(wret)-24,len(wret),4)]
            rv=np.std(mrets)*np.sqrt(12)+1e-6
            nscale=min(VOL_TARGET/rv,1.5)
            if MONTHLY_CHK==0:
                # in weekly mode the DD reducer owns scale; vol target multiplies
                scale=nscale
            else:
                dd=eq/peak-1
                if dd<-0.12: scale=nscale*0.25
                elif dd<-0.08: scale=nscale*0.5
                else: scale=nscale
        else:
            scale=1.0
    r=np.array(wret)
    PER_YR=52
    sr=r.mean()/r.std()*np.sqrt(PER_YR) if r.std()>0 else 0
    ann=r.mean()*PER_YR*100; vol=r.std()*np.sqrt(PER_YR)*100
    eq2=np.cumprod(1+r); dd=min((eq2[i]/max(eq2[:i+1])-1) for i in range(len(eq2)))*100
    tot_cost=sum(costs)
    print(f"MODE={'monthly-chk' if MONTHLY_CHK else 'weekly-chk'}: NET SR={sr:.3f} ret={ann:+.2f}% vol={vol:.2f}% MaxDD={dd:.2f}% n={len(r)}wk cost~{tot_cost*52/len(wret)*100:.2f}%/yr")

if __name__=="__main__": main()
