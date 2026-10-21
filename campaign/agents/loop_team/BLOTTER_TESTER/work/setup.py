import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make, NEW3, NEW2, vt, POOL, EXEC, SHORTF
import honest13_build as H

# FULL reconstruction of BALANCED = (SAFE(TGT .07 THR .04) + AGG(TGT .091 THR .03))/2
Sd, capW, blend, tw, wts = make(NEW3)
books = {}
for name,(TGT,THR) in {'SAFE':(0.07,0.04),'AGG':(0.091,0.03)}.items():
    b, gb = vt(blend, TGT)
    eq = (1+b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index)
    full = capW.mul(gb, axis=0).mul(sc, axis=0)
    books[name] = (b, gb, sc, full)

# honest "rebuild" of committed champion r_out for each book (full cost model)
def r_out_of(name):
    b, gb, sc, full = books[name]
    reb = full.diff().abs().sum(axis=1)
    b2 = b*sc
    dsc = sc.diff().abs()*0.5
    out = b2 - (tw.reindex(b2.index).fillna(0)+dsc.fillna(0))*6e-4 - reb.reindex(b2.index).fillna(0)*6e-4
    terms=[]
    for n in POOL:
        sf = SHORTF[n]
        if sf>0: terms.append(capW[n]*sc*sf*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2))
    htb = pd.concat(terms,axis=1).sum(axis=1)
    return (out - htb.reindex(out.index).fillna(0)/252).dropna(how='all'), reb

rA, rebA = r_out_of('SAFE')
rB, rebB = r_out_of('AGG')
BAL = ((rA+rB)/2).dropna()
print('BALANCED rebuild n =', len(BAL))

champ = pd.read_csv('/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv', index_col=0, parse_dates=True).iloc[:,0]
j = pd.concat([champ.rename('champ'), BAL.rename('rebuild')],axis=1,join='inner').dropna()
print('join rows:', len(j), 'max|diff| =', float((j.champ-j.rebuild).abs().max()))
