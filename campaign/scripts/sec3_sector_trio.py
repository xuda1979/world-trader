#!/usr/bin/env python3
"""SEC3_sector_trio — HUNT_CROSSASSET2 (loop iter6) NEAR-MISS deliverable. NOT champion-eligible.
3-book sector-relative z-reversion on REAL ETF closes (twelvedata): XLB/XLF, XLB/XLI, XLF/XLI.
Position per book/leg: w = clip(-z_lb(15)/1.5, +-0.5) on leg A, -w on leg B; spread = ln(A/B).
T+1: pos.shift(1). Costs 6.0bps/side on |dw|/2 summed per leg. Borrow 0.5%/yr on short legs.
EW across 3 books. Eval 2008+.
GATES (iter6 charter): SR 0.667 PASS | H1 0.89/H2 0.33 PASS | negy 8/19 worst -3.60% FAIL
| 200x 10d-block position-lag scramble p=0.000 (seeds 0/1/2) PASS | ac1 -0.052 PASS
| uniqR 1.000 PASS | corr to HONEST14V3_BALANCED +0.016 PASS => 6/7, FAILS yearly gate.
ALSO DISCLOSED: OOS17+ SR 0.266 / OOS20+ 0.177 / OOS23+ 0.242 (edge concentrated 2008-2016);
LOYO min -1.055 (2016). Delivered for chair review ONLY (FXD1 precedent). No PASS claimed."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
ROOT='/Users/daxu/software/world-trader'
TD=f'{ROOT}/tools/quant/data/twelvedata'
COST=6.0/1e4; BORROW=0.005/252

def etf(t):
    df=pd.read_csv(f'{TD}/{t}.csv',index_col=0,parse_dates=True)
    v=pd.to_numeric(df['close'],errors='coerce'); v=v[v>0]
    return v[~v.index.duplicated(keep='last')].sort_index()

def mkbook(A,B,lb=15,cap=1.5):
    rets=pd.DataFrame({0:A.pct_change(),1:B.pct_change()}).fillna(0)
    sp=np.log(A/B)
    m=sp.rolling(lb).mean(); s=sp.rolling(lb).std(); z=(sp-m)/s
    w=(-z/cap).clip(-0.5,0.5).fillna(0)
    pos=pd.DataFrame({0:w,1:-w}); ps=pos.shift(1).fillna(0)
    gross=(ps*rets).sum(axis=1)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    bor=BORROW*ps.clip(upper=0.0).abs().sum(axis=1)
    return gross-turn*COST-bor

def main():
    X={t:etf(t) for t in ['XLB','XLF','XLI']}
    books=[('XLB','XLF'),('XLB','XLI'),('XLF','XLI')]
    r=pd.concat([mkbook(X[a],X[b]) for a,b in books],axis=1).mean(axis=1)
    r=r[r.index>='2008-01-01']
    out=f'{ROOT}/campaign/agents/loop_team/HUNT_CROSSASSET2/sleeves/SEC3_sector_trio_zrev_daily.csv'
    r.round(12).to_frame('ret').to_csv(out)
    print('wrote',out,'n=',len(r),'SR=%.4f'%(r.mean()/r.std()*np.sqrt(252)))

if __name__=='__main__':
    main()
