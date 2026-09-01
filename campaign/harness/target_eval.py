"""Target-metric OOS eval for the 40%/SR2/MaxDD8 no-leverage goal.

The single honest scorer for full portfolios (blends) AND individual sleeves.
All metrics measured three ways:
  - FULL  : 2008-2026 whole window
  - TRAIN : 2008-2015  (first half)
  - TEST  : 2016-2026  (second half, out-of-sample)
  - WALK  : 2-scheme walk-forward (annual refit) if weights provided
Usage:
  python target_eval.py <daily_returns.csv>          # single portfolio/blend
  python target_eval.py --blend dir_of_sleeve_csv *w
CSV contract: [date, ret] daily net returns.
"""
import sys, os, glob
import numpy as np, pandas as pd

def load_ret(path):
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index)
    col = "ret" if "ret" in df.columns else df.columns[0]
    s = df[col].astype(float).replace([np.inf,-np.inf], np.nan).dropna()
    return s[~s.index.duplicated(keep="last")]

def monthly(r):
    return r.resample("ME").apply(lambda x:(1+x).prod()-1)

def metrics(r):
    """SR_m, ann CAGR, MaxDD daily, MaxDD monthly, vol_d."""
    r = r.dropna()
    if len(r) < 200: return None
    m = monthly(r)
    sr_m = m.mean()/m.std()*np.sqrt(12) if m.std()>0 else 0.0
    cagr = (1+r).prod()**(252/len(r))-1
    ard  = r.mean()*252                      # arithmetic annual
    eq = (1+r).cumprod(); dd_d = (eq/eq.cummax()-1).min()
    eqm = (1+m).cumprod(); dd_m = (eqm/eqm.cummax()-1).min()
    return dict(sr_m=float(sr_m), cagr=float(cagr), ann_arith=float(ard),
                dd_daily=float(dd_d), dd_monthly=float(dd_m),
                vol_d=float(r.std()*np.sqrt(252)),
                n=len(r), start=str(r.index[0].date()), end=str(r.index[-1].date()))

def split(r, d0="2016-01-01"):
    tr = r[r.index < d0]; te = r[r.index >= d0]
    return tr, te

def score_single(r, label=""):
    res = {"full": metrics(r)}
    tr, te = split(r)
    res["train"] = metrics(tr); res["test"] = metrics(te)
    return res

def fmt(res):
    out=[]
    for k in ["full","train","test"]:
        s = res.get(k); 
        if not s: out.append(f"  {k}: too short"); continue
        out.append(f"  {k:<6} SR_m={s['sr_m']:.2f} CAGR={s['cagr']*100:5.1f}% arith={s['ann_arith']*100:5.1f}% "
                   f"MaxDD_d={s['dd_daily']*100:5.1f}% MaxDD_m={s['dd_monthly']*100:5.1f}% vol_d={s['vol_d']*100:4.1f}% n={s['n']}")
    return "\n".join(out)

if __name__ == "__main__":
    args = sys.argv[1:]
    for a in args:
        r = load_ret(a)
        print(f"== {os.path.basename(a)} {r.index.min().date()}..{r.index.max().date()} ==")
        print(fmt(score_single(r)))
