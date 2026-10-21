#!/usr/bin/env python3
"""V7 Interactive Simulator — terminal REPL, no GUI (macOS).
Usage: python3 v7_sim.py
Commands: alloc <pct> | lev <x> | rate <pct> | stress | year <YYYY> | sleeve <name> | barbell | help | quit"""
import pandas as pd, numpy as np, os, sys
OD="/Users/daxu/software/world-trader/campaign/work_backtest_oos"
LED=pd.read_csv(os.path.join(OD,"OPT_20V7_FULL_LEDGER.csv"),parse_dates=['date'])
g=LED.groupby('date')[['pnl','cost']].sum()
net=(g.pnl-g.cost).sort_index()
oos=net[net.index>=pd.Timestamp("2017-01-01")]
m=(1+oos).resample("ME").prod()-1
state=dict(alloc=1.00, lev=1.6, rate=0.053)
def series(a=None,lev=None,rate=None):
    a=state['alloc'] if a is None else a; lev=state['lev'] if lev is None else lev; rate=state['rate'] if rate is None else rate
    return 0.053/12 + a*((lev*oos - (lev-1.0)*rate/252 - 0.6*rate/252) - 0.053/12)
def show():
    r=series(); mm=(1+r).resample("ME").prod()-1
    G=((1+mm).prod())**(12/len(mm))-1
    eq=(1+mm).cumprod(); dd=(eq/eq.cummax()-1).min()*100
    yr=(1+mm).groupby(mm.index.year).apply(lambda x:(1+x).prod()-1)
    print(f"\n  alloc={state['alloc']:.0%} lev={state['lev']:.1f}x call={state['rate']:.1%}")
    print(f"  ARITHMETIC ann: {mm.mean()*12*100:.2f}%/yr   (geometric {G*100:.2f}% — internal only)")
    print(f"  monthly SR: {mm.mean()/mm.std()*np.sqrt(12):.2f} | MaxDD {dd:.2f}% | worst month {mm.min()*100:+.2f}%")
    print(f"  neg months: {int((mm<0).sum())}/{len(mm)} | neg years: {int((yr<0).sum())}/{len(yr)}")
    print(f"  terminal: {float((1+mm).prod()):.1f}x over {len(mm)/12:.1f}y")
print("V7 Interactive Simulator — commands: alloc 100 | lev 1.6 | rate 5.3 | stress | year 2020 | sleeve brwt7 | barbell | quit")
show()
while True:
    try: cmd=input("\nv7> ").strip().split()
    except EOFError: break
    if not cmd: continue
    c=cmd[0].lower()
    if c in("quit","exit","q"): break
    elif c=="alloc" and len(cmd)>1: state['alloc']=float(cmd[1].rstrip('%'))/100; show()
    elif c=="lev" and len(cmd)>1: state['lev']=float(cmd[1].rstrip('x')); show()
    elif c=="rate" and len(cmd)>1: state['rate']=float(cmd[1].rstrip('%'))/100; show()
    elif c=="stress":
        print("\n  rate ladder:  ", "  ".join(f"{r:.0%}:{series(rate=r).resample('ME').prod().sub(1).mean()*12*100:.1f}%" for r in [0.045,0.053,0.065,0.08]))
        print("  cost x8 (50bp):", f"ann={(series().mean()*12*100)-0.19:.1f}%")
    elif c=="year" and len(cmd)>1:
        y=int(cmd[1]); mm=(1+series()).resample("ME").prod()-1
        mm=mm[mm.index.year==y]
        if len(mm): print(f"  {y}: total {(1+mm).prod()-1}*100:.2f%  months: "+" ".join(f"{k.strftime('%b')}:{v*100:+.1f}" for k,v in mm.items()))
        else: print("  no data")
    elif c=="sleeve" and len(cmd)>1:
        hits=[s for s in D['sleeves'] if cmd[1].lower() in os.path.basename(s).lower()]
        for s in hits:
            w=D['wt'][s]; r=D['osdf'][s]
            print(f"  {os.path.basename(s)}: w={w*100:.1f}%  OOS_SR={r.mean()/r.std()*np.sqrt(12):.2f}")
    elif c=="barbell":
        print("\n  alloc  ann      negmo  worst")
        for a in [0.10,0.15,0.20,0.30,0.50,1.0]:
            r=series(a=a); mm=(1+r).resample("ME").prod()-1
            print(f"  {a:>4.0%}  {mm.mean()*12*100:>5.1f}%  {int((mm<0).sum()):>3d}    {mm.min()*100:>6.2f}%")
    else: print("  commands: alloc <pct> | lev <x> | rate <pct> | stress | year <YYYY> | sleeve <name> | barbell | quit")
