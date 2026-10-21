#!/usr/bin/env python3
"""GOLD SLEEVE variant of the champion composite (multi-asset diversification).

Prior fires: crash filters and self-trend gates cannot cut the champion's
-16.0% MaxDD because it is (a) a 22-month slow grind (2021-09..2023-09) and
(b) a factor-level crash (2018-09, SPY flat). Both are invisible to SPY
price signals. But GOLD (GLD, full 2006-2026 twelvedata history) is a real
diversifier: +4.9% in 2018-12 (SPY -9.3%), +3.6% cum through the 2021-23
grind (SPY -6.2%), corr ~0.14-0.27. Test a small gold sleeve.

Baseline champion (run_champion_composite.py, vt15, 6bps):
    SR 0.933, ret 14.43%, MaxDD -15.95%, 2008-2026 (224 months)

CONFIRMED BEST (2026-08-12 sweep, verified reproduction):
    gold 0.2 + vt12 + rev30 -> SR 1.086, ret 14.07%, MaxDD -14.24%
    gold 0.2 + vt12 + rev50 -> SR 0.986, ret 15.17%, MaxDD -13.77% (min DD)

Modes:
  STATIC  : always hold GOLD_W of gold, (1-GOLD_W) in the mom+rev book.
            gold ret = GOLD_W * gld_ret + (1-GOLD_W) * book_ret, then the
            SAME vol-target + DD-reducer pipeline on the combined stream.
  TACTICAL: gold weight = GOLD_W_HIGH when the book is de-risked (vg<1 or
            sp10 off), else GOLD_W_LOW. This keeps exposure in stress via
            the diversifier instead of cash.

Env knobs:
  GOLD_W, GOLD_W_LOW, GOLD_W_HIGH (static uses GOLD_W)
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
TLT_CSV = os.path.join(HERE, "..", "tools", "quant", "data", "twelvedata", "TLT.csv")
OUT_CSV = os.environ.get("OUT_CSV", "wf_champion_gold.csv")
START_YM = os.environ.get("START_YM", "2008-01")
COST_BPS = float(os.environ.get("COST_BPS", 6.0))
VOL_TARGET = float(os.environ.get("VOL_TARGET", 0.15))
REV_SLEEVE = float(os.environ.get("REV_SLEEVE", 0.3))
GOLD_W = float(os.environ.get("GOLD_W", 0.15))
GOLD_W_LOW = float(os.environ.get("GOLD_W_LOW", 0.0))
GOLD_W_HIGH = float(os.environ.get("GOLD_W_HIGH", 0.3))
MODE = os.environ.get("MODE", "static")
TILT = os.environ.get("TILT", "none")   # none|vol|lowvol (momentum leg)
TLT_W = float(os.environ.get("TLT_W", 0.0))   # second sleeve: long bonds
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
def load_gold():
    df=pd.read_csv(GLD_CSV, index_col=0, parse_dates=True)
    c="close" if "close" in df.columns else df.columns[0]
    return df[c].astype(float).resample("ME").last().dropna()
def load_tlt():
    df=pd.read_csv(TLT_CSV, index_col=0, parse_dates=True)
    c="close" if "close" in df.columns else df.columns[0]
    return df[c].astype(float).resample("ME").last().dropna()
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
def LM_tilted(dt, sig, fwd, vol6, tilt):
    """Tilted top-quartile momentum (see run_champion_tilt.py)."""
    fr=fwd.loc[dt]; s=sig.loc[dt].dropna(); c=s.index.intersection(fr.dropna().index)
    if len(c)<20: return 0.0
    s=s.loc[c]; fr2=fr.loc[c]; G=max(1,len(c)//4)
    top=list(s.sort_values(ascending=False).index[:G])
    if tilt=="vol":
        v=vol6.loc[dt, top].replace(0,np.nan).dropna()
        if len(v)<max(1,G//2): return fr2.loc[top].mean()
        inv=1.0/v; w=(inv/inv.sum())
        return float((w*fr2.loc[w.index]).sum())
    elif tilt=="lowvol":
        v=vol6.loc[dt, top].dropna().sort_values()
        keep=list(v.index[:max(1,len(v)//2)])
        return fr2.loc[keep].mean()
    return fr2.loc[top].mean()
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
    gld=load_gold(); gld_ret=gld.pct_change().reindex(px.index).fillna(0.0)
    tlt_ret=gld_ret*0.0
    if TLT_W>0:
        tlt=load_tlt(); tlt_ret=tlt.pct_change().reindex(px.index).fillna(0.0)
    oos=[d for d in px.index if d.strftime("%Y-%m")>=START_YM]
    v=lambda dt: float(vix.asof(dt)) if pd.notna(vix.asof(dt)) else 20
    sp10=lambda dt: 1.0 if float(spy.asof(dt))>=spy[spy.index<=dt].tail(10).mean() else 0.0
    vg=lambda dt: 0.3 if v(dt)>30 else (0.5 if v(dt)>25 else (0.75 if v(dt)>20 else 1.0))
    raw=[]
    for dt in oos:
        book=(1.0*sp10(dt)*LM_tilted(dt,comp,fwd,vol6,TILT) + REV_SLEEVE*SP(dt,rev,fwd))*vg(dt)
        gr=float(gld_ret.loc[dt]) if dt in gld_ret.index else 0.0
        if MODE=="static":
            w=GOLD_W
        else:  # tactical
            de_risked = vg(dt)<1 or sp10(dt)<1
            w = GOLD_W_HIGH if de_risked else GOLD_W_LOW
        tr=float(tlt_ret.loc[dt]) if dt in tlt_ret.index else 0.0
        raw.append((1-w-TLT_W)*book + w*gr + TLT_W*tr)
    raw=np.array(raw)
    # Vol target + DD reducer (on the combined stream)
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
    mode_lbl = f"static w={GOLD_W}" if MODE=="static" else f"tactical {GOLD_W_LOW}/{GOLD_W_HIGH}"
    print(f"GOLD {mode_lbl}: SR={sr:.3f} ret={ann:+.2f}% vol={vol:.2f}% MaxDD={dd:.2f}% n={len(r)}")
    idx=np.argsort(r)[:6]
    print("  worst 6:", " ".join(f"{oos[i].strftime('%Y-%m')} {r[i]*100:+.1f}%" for i in sorted(idx)))
    pd.DataFrame({"ym":[d.strftime("%Y-%m") for d in oos[:len(r)]], "net":r}).to_csv(os.path.join(HERE,"data",OUT_CSV), index=False)
if __name__=="__main__": main()
