#!/usr/bin/env python3
"""FXD1_KRWTRI — HUNT_FXDEPO deliverable (reproducible).
3-book EM/Scandinavian cross z-reversion: KRW/SEK, KRW/CHF, KRW/NOK.
Spread = ln(DEXKOUS/DEXSDUS) etc. (USD-per-local quotes; cross = quotient).
Position per book: w = clip(-z_lb, +-cap)/cap per LEG, lb = (21,63) averaged, cap=2.
T+1: pos.shift(1) * (r_A - r_B). Costs 6bps/side on |dw|/2 per leg. Borrow 0.5%/yr shorts.
EW across 3 books. Eval from 2008-01-01 (data 1999+; warmup included in-file from 2008).
Charter gates (iter6): SR>=0.6 PASS 0.870 | H1 1.07/H2 0.61 PASS | negy 8 FAIL (>2, all >-5%)
| poslag 10d-block scramble p=0.000 PASS | ac1 -0.014 PASS | uniqR 1.000 PASS | corr +0.005 PASS.
DELIVERED AS NEAR-MISS CANDIDATE (6/7 gates; fails yearly-count gate only).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
ROOT='/Users/daxu/software/world-trader'
ND=f'{ROOT}/tools/quant/data/newdata'
COST=6.0/1e4; BORROW=0.005/252

def dex(name):
    df=pd.read_csv(f'{ND}/{name}.csv',index_col=0,parse_dates=True)
    v=pd.to_numeric(df.iloc[:,0],errors='coerce'); v=v[v>0]
    return v[~v.index.duplicated(keep='last')].sort_index()

def zpos(spread, lb, cap=2.0):
    m=spread.rolling(lb).mean(); s=spread.rolling(lb).std()
    return (-(spread-m)/s/cap).clip(-0.5,0.5)

def net_of_book(pos, r):
    common=pos.index.intersection(r.index)
    p=pos.reindex(common).fillna(0.0); rr=r.reindex(common).fillna(0.0)
    ps=p.shift(1).fillna(0.0)
    gross=(ps*rr).sum(axis=1)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    bor=BORROW*ps.clip(upper=0.0).abs().sum(axis=1)
    return (gross-turn*COST-bor)

def main():
    px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
    lp=np.log(px); rets=px.pct_change()
    books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]
    rs=[]
    for a,b in books:
        sp=lp[a]-lp[b]
        pos=sum(zpos(sp,lb,2.0) for lb in (21,63))/2
        rs.append(net_of_book(pd.DataFrame({a:pos,b:-pos}),
                              pd.DataFrame({a:rets[a],b:rets[b]})).fillna(0))
    r=pd.concat(rs,axis=1).sum(axis=1)/len(books)
    r=r[r.index>='2008-01-01']
    out=f'{ROOT}/campaign/agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_raw_daily.csv'
    r.round(12).to_frame('ret').to_csv(out)
    print('wrote',out,'n=',len(r),'SR=%.3f'%(r.mean()/r.std()*np.sqrt(252)))

if __name__=='__main__':
    main()
