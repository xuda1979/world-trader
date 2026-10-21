"""A09: crisis replay — V7 weights through 2008 & 2020 using full sleeve histories."""
import pandas as pd, numpy as np, os, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
sl=D['sleeves']; wt=D['wt']; ddf=D['ddf']
scen={}
# 2020 COVID: Feb 20 - Mar 31 2020
win=ddf[(ddf.index>="2020-02-20")&(ddf.index<="2020-03-31")]
if len(win)>10:
    r=(1+win[sl].dot(wt)).prod()-1
    scen["2020_COVID"]=float(r*1.6)
# 2018 vol spike: Feb 2018
win=ddf[(ddf.index>="2018-02-01")&(ddf.index<="2018-02-15")]
if len(win)>3:
    scen["2018_volspike"]=float(((1+win[sl].dot(wt)).prod()-1)*1.6)
# 2008 proxy: use only sleeves with pre-2009 data, renormalized
pre={}
for s in sl:
    try:
        d=pd.read_csv(os.path.join(D['ROOT'],s),index_col=0,parse_dates=[0])
        c="ret" if "ret" in d.columns else d.columns[0]
        ss=d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
        ss=ss[ss.index<"2009-01-01"]
        if len(ss)>500: pre[s]=ss
    except: pass
# 2008 proxy: renormalize weights over long-history sleeves, align on common dates
live=list(pre.keys())
common_ix=None
if live:
    for s in live:
        ix=pre[s].index
        common_ix=ix if common_ix is None else common_ix.intersection(ix)
if live and common_ix is not None and len(common_ix)>30:
    w8=wt[live]/wt[live].sum()
    X08=pd.DataFrame({s:pre[s].reindex(common_ix) for s in live}).fillna(0)
    win=(X08.index>="2008-09-01")&(X08.index<="2008-12-31")
    if win.sum()>30:
        r08=(1+X08[win].dot(w8)).prod()-1
        scen["2008_proxy_sleeves"]=dict(n=len(live),
            unlevered=float(r08*1.6),
            sleeves=[os.path.basename(s) for s in live])
# 2022 rates: Jan-Oct 2022
win=ddf[(ddf.index>="2022-01-01")&(ddf.index<="2022-10-31")]
scen["2022_rates"]=float(((1+win[sl].dot(wt)).prod()-1)*1.6)
for k,v in scen.items():
    print(f"  {k}: {v if not isinstance(v,dict) else v}")
print("KEY: 2008 proxy = %s" % (f"{scen['2008_proxy_sleeves']['unlevered']*100:+.1f}% over Sep-Dec 2008 "
      f"from {scen['2008_proxy_sleeves']['n']} long-history sleeves" if isinstance(scen.get('2008_proxy_sleeves'),dict) else "n/a"))
save("agent09_crisis_replay",scen)
