"""Deployable runner: LEVERED FLOORED FLAGSHIP (the no-losing-year book, scaled).

Raises annual return of the validated floored flagship (h3+AP 50/50 floored 50%
in T-bills) via modest leverage WITH realistic financing cost, on its LONG
(2008-2026, ~18.6y) window.

  base    : CAGR 7.49%  m-Shrp 1.63  MaxDD -6.2%  no losing years
  x1.25   : CAGR 8.58%  m-Shrp 1.49  MaxDD -7.8%
  x1.5    : CAGR 9.66%  m-Shrp 1.40  MaxDD -9.3%  (stays under 10% DD)
  x2.0    : CAGR 11.80% m-Shrp 1.28  MaxDD -12.3% (meets >=10% return)

Financing cost 3%/yr on the borrowed (lev-1) fraction. HONEST: longer-window
floor, no-losing-year quality preserved at <=1.5x; Sharpe 2.0 remains unreachable
(see RESEARCH_LOG 2026-08-13). x2 gives the $>=10%$ aim at deeper DD.

Usage: python tools/quant/hedge_fund_strats/run_floored_levered.py [--lev 2.0]
Writes: results/floored_levered_daily.csv
"""
import argparse
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parent.parent.parent.parent
RES=ROOT/"tools/quant/hedge_fund_strats/results"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--lev",type=float,default=2.0)
    ap.add_argument("--funding_annual",type=float,default=0.03); a=ap.parse_args()
    r=pd.read_csv(RES/"portfolio_floored_daily.csv",index_col=0,parse_dates=True).iloc[:,0].dropna()
    fund=a.funding_annual/252*(a.lev-1)
    rl=a.lev*r-fund
    out=RES/"floored_levered_daily.csv"
    pd.DataFrame({"daily_return":rl.values},index=rl.index).to_csv(out)
    rm=rl.resample("ME").apply(lambda s:(1+s).prod()-1).dropna()
    eq=(1+rl).cumprod()
    cagr=(1+rl).prod()**(252/len(rl))-1
    dd=(eq/eq.cummax()-1).min(); mshr=rm.mean()/rm.std()*np.sqrt(12)
    yrs=[]
    for y in range(2008,2027):
        sub=rl.loc[str(y)]
        if len(sub): yrs.append((y,float((1+sub).prod()-1)))
    neg=[y for y,v in yrs if v<0]
    print(f"Wrote {out}")
    print(f"LEVERED FLOORED FLAGSHIP x{a.lev}: CAGR {cagr*100:.2f}% | monthlySharpe {mshr:.2f} | MaxDD {dd*100:.2f}% | funding {a.funding_annual*100:.0f}% | negYears {neg}")
    print(f"  window {rl.index[0].date()}..{rl.index[-1].date()} ({len(rl)/252:.1f}y)")

if __name__=="__main__":
    main()
