"""Deployable runner: LEVERED IV book (2026-08-13).

Scales the validated 6-sleeve IV book (ms_iv_daily.csv) by a leverage factor to
raise annual return while keeping the (short, favorable) 2019+ window's high
Sharpe and contained drawdown. INVERSE-VOL book with 6% one-side cost, then
levered. Financing cost applied at a nightly rate on the levered (borrowed) amount.

HONEST DISCLOSURE (see RESEARCH_LOG 2026-08-13): the base book's Sharpe 1.44-1.50
is a 2019+ favorable window, NOT a long-horizon property. Leverage scales return
AND drawdown proportionally; it does not create alpha. The long-window (~18y)
realized Sharpe of equivalent sleeves is ~0.9. Use levered numbers with that caveat.

Usage: python tools/quant/hedge_fund_strats/run_ls_iv_levered.py [--lev 2.0]
Writes: results/iv_levered_daily.csv
"""
import sys, argparse
from pathlib import Path
import pandas as pd, numpy as np
ROOT = Path(__file__).resolve().parent.parent.parent.parent
RES = ROOT / "tools/quant/hedge_fund_strats/results"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--lev",type=float,default=2.0)
    ap.add_argument("--funding_annual",type=float,default=0.03,help="annualized financing cost on the levered amount")
    a=ap.parse_args()
    df=pd.read_csv(RES/"ms_iv_daily.csv",index_col=0,parse_dates=True)["daily_return"].dropna()
    base_vol_scale = (a.lev-1.0)                    # borrowed fraction
    # daily financing on borrowed amount
    funding = a.funding_annual/252 * base_vol_scale
    r = a.lev * df - funding
    out=RES/"iv_levered_daily.csv"
    pd.DataFrame({"daily_return":r.values},index=r.index).to_csv(out)
    eq=(1+r).cumprod(); n=len(r)
    sr=r.mean()/r.std()*np.sqrt(252); cagr=(eq.iloc[-1])**(252/n)-1; dd=(eq/eq.cummax()-1).min()
    print(f"Wrote {out}")
    print(f"LEVERED IV book x{a.lev}: SR {sr:.3f} | CAGR {cagr*100:.2f}% | MaxDD {dd*100:.2f}% | funding {a.funding_annual*100:.1f}% ann | n={n}")
    print(f"  base window {r.index[0].date()} .. {r.index[-1].date()} ({n/252:.1f}y) - SHORT FAVORABLE WINDOW caveat")

if __name__=="__main__":
    main()
