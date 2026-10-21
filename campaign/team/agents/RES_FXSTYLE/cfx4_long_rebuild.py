#!/usr/bin/env python3
"""Rebuild the CFX4 4-book FX cross z-reversion on the LONG fx_hist data (1999+).

The committed CFX4 (HUNT_CARRYFX) is built from tools/quant/data/fx (2019+ only), which is why
the champion's IS-solver (<2017) computes its SR=0 and weights it zero. All 8 underlying pairs
exist in tools/quant/data/fx_hist back to 1999, so the SAME construction can be rebuilt with
pre-2017 history -> it can earn a real IS weight and raise champion Sharpe.

Faithful to c11_deliver.py: 4 books (GBP_USD/NZD_USD, AUD_USD/GBP_USD, AUD_USD/EUR_USD,
EUR_USD/NZD_USD), each = mean over 2 z-lookbacks (21,63), EW composite, T+1, 6bps/side, 0.5%/yr
borrow, no carry.
"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd

ROOT='/Users/daxu/software/world-trader'
FXH=f"{ROOT}/tools/quant/data/fx_hist"
COST=6.0/1e4
BOOKS=[('GBP_USD','NZD_USD'),('AUD_USD','GBP_USD'),('AUD_USD','EUR_USD'),('EUR_USD','NZD_USD')]
LBS=(21,63)

def load_close(pairs):
    d={}
    for p in pairs:
        df=pd.read_csv(f"{FXH}/{p}.csv", index_col=0, parse_dates=True)['close'].astype(float)
        df=df[df.index.dayofweek<5]
        df=df[~df.index.duplicated(keep='last')].sort_index()
        d[p]=df
    idx=None
    for p,df in d.items():
        i=df.index; idx=i if idx is None else idx.intersection(i)
    return pd.DataFrame({p:d[p].reindex(idx) for p in pairs})

def zsig(C,a,b,lb=42):
    sp=np.log(C[a])-np.log(C[b])
    rol=sp.rolling(lb)
    z=(sp-rol.mean())/rol.std()
    return (2.0*(-z)).clip(-2.0,2.0)/2.0

def build():
    C=load_close(['GBP_USD','NZD_USD','AUD_USD','EUR_USD'])
    R=C.pct_change()
    nets=[]
    for (a,b) in BOOKS:
        W=sum([zsig(C,a,b,lb) for lb in LBS])/len(LBS)
        sig=W.shift(1)
        net=sig*(R[a]-R[b])-2*sig.diff().abs()*COST-0.005/252*sig.abs()
        nets.append(net)
    return pd.concat(nets,axis=1).mean(axis=1).dropna(), C

def main():
    net,C=build()
    print(f"CFX4-long: n={len(net)} {net.index.min().date()}..{net.index.max().date()}")
    # metrics full + IS/OOS
    def seg(r):
        ann=((1+r).prod()**(252/len(r))-1); sr=r.mean()/r.std()*252**0.5
        nav=(1+r).cumprod(); mdd=(nav/nav.cummax()-1).min()
        return round(sr,3), round(ann*100,2), round(mdd*100,2)
    print("  full: SR={0} ann={1}% MDD={2}%".format(*seg(net)))
    for lab,sl in [('IS<2017',net.index<'2017-01-01'),('OOS>=2017',net.index>='2017-01-01')]:
        r=net[sl]
        print(f"  {lab}: n={len(r)} SR={seg(r)[0]} ann={seg(r)[1]}%")
    net.rename('ret').to_frame().to_csv(f"{ROOT}/campaign/team/agents/RES_FXSTYLE/sleeves/CFX4_long1999_dtf2163_net.csv")
    print("emitted CFX4_long1999_dtf2163_net.csv")

if __name__=='__main__':
    main()
