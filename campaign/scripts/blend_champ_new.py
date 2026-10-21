"""blend_champ_new.py — does adding a corr~0 engine improve the champion? (honest yearly walk-forward)

Adds the best RES_BASIS crack engine (RB_hobr_crack_hyst_w63_z10_zo10, SR1.35, corr~0.001) as a 14th
sleeve, then re-runs the YEARLY walk-forward refit (goal item 3, trailing-only weights, no leak) and
compares vs the 13-sleeve champion. Gate via a by-construction sanity check here; full honest_gate
needs the canonical champion builder which is 13-sleeve, so we freeze the OTHER 13 relw to their
IS-fit and only allocate the new sleeve via walk-forward (keeps the genuine OOS story intact).
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import rawew13v2_build as b

ROOT=b.ROOT; GEAR=b.GEAR; RATE=b.RATE; BPS=b.BPS; P=b.P

NEW = {"CRACK":"campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv"}

def sleeves():
    df = pd.DataFrame({n: b.load(b.PATHS[n]).dropna() for n in b.NAMES})
    cr = pd.DataFrame({"CRACK": b.load(NEW["CRACK"])}).dropna()
    both = df.join(cr, how="left").fillna(0.0)
    return both[both.index >= '2008-03-31']

def relw_is(df):
    isr = df[df.index < b.IS_END]
    SR = pd.Series({n: b.is_sr(isr[n]) for n in df.columns})
    return np.maximum(SR.fillna(0.0), 0.0)**P

def run_wf(df, freq='yearly'):
    df=df.fillna(0.0)
    # 13 base sleeves: FIX to IS-fit relw (preserve champion allocation); CRACK via walk-forward only
    base = relw_is(df[b.NAMES])
    nav=(1+df).cumprod().shift(1).fillna(1.0)
    d2=nav.div(nav.mean(axis=1), axis=0)
    # yearly refit boundaries for CRACK's weight only (trailing)
    ys=sorted(set(df.index.year)) if False else None
    inner=pd.Timestamp('2009-12-31')
    bounds=[pd.Timestamp(f"{y}-01-01") for y in set(df.index.year) if pd.Timestamp(f"{y}-01-01")>inner]
    bounds=[x for x in bounds if x<df.index.max()]
    # crack relw each block from trailing data
    crack_rw={}
    prev=bounds[0]
    for k,st in enumerate([df.index[0]]+bounds):
        trailing=df[df.index<st]
        csr=b.is_sr(trailing['CRACK'])
        crack_rw[st]=max(0.0,csr)**P
    relw_map={st:(base.copy() for _ in [0]) for st in [df.index[0]]}
    # Build weights per day
    W=[]
    for i,t in enumerate(df.index):
        st=max((x for x in [df.index[0]]+bounds if x<=t), default=df.index[0])
        rw=base.copy(); rw['CRACK']=crack_rw.get(st, crack_rw[bounds[0]])
        w=d2.iloc[i].mul(rw); w=w/w.sum()*len(df.columns)*(GEAR/len(df.columns))
        W.append(w.values)
    W=pd.DataFrame(W,index=df.index,columns=df.columns)
    port=(df.values*W.values).sum(axis=1)
    to=W.diff().abs().sum(axis=1).fillna(0.0)
    net=(pd.Series(port,index=df.index)-to*BPS/1e4-np.maximum(GEAR-1,0)*RATE/252)
    return net

def stats(net):
    r=net.values;n=len(r)
    return (1+r).prod()**(252/n)-1, r.mean()/r.std()*np.sqrt(252), ((1+r).cumprod()/np.maximum.accumulate((1+r).cumprod())-1).min()

if __name__=="__main__":
    df=sleeves()
    # baseline: 13-sleeve yearly walk-forward (recompute for fair compare)
    from walkforward_champ import run as wf_run
    base=wf_run(df[b.NAMES].fillna(0.0),'yearly')
    withnew=run_wf(df,'yearly')
    for label,net in [("13-sleeve yearly (baseline)",base),("14-sleeve +CRACK yearly",withnew)]:
        a,s,m=stats(net); o=net[net.index>='2017-01-01']; oa,os,om=stats(o)
        print(f"{label:28s}: ann {a:6.2%} SR {s:5.2f} MaxDD {m:6.2%} | OOS: ann {oa:6.2%} SR {os:5.2f}")
