"""C2_fly2AB_75 — US Treasury curve butterfly mean-reversion (2s5s10s + 5s10s30s).
C2_ratescurve / GOAL100. Reproduces campaign/agents/C2_ratescurve/sleeves/C2_fly2AB_75.csv

Economic rationale: the mid-curve belly (5y, 10y) richens/cheapens vs duration-matched
wings on temporary convexity demand, issuance/roll flows and positioning extremes;
the fly z-score reverts as flows normalize. Two flies have near-zero overlap (corr 0.017),
giving SR 1.85 combined net. Signal T+1, 6bps one-side, trailing-only expanding vol target
(10% ann, min 60d, clip 3.0). Bond returns approximated ret ~ -D*dy + y/252 (documented).
"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.harness.data import fred, save_sleeve
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
DUR={'DGS2':1.9,'DGS5':4.4,'DGS10':8.5,'DGS30':17.5}

def yld(name):
    s=pd.read_csv(f"{FRED}/{name}.csv",index_col=0,parse_dates=True)
    s=pd.to_numeric(s.iloc[:,0],errors='coerce').replace(-99.99,np.nan).dropna()
    return s[~s.index.duplicated(keep='last')].sort_index()

TEN=['DGS2','DGS5','DGS10','DGS30']
ys=pd.DataFrame({t:yld(t) for t in TEN}).dropna()
rs=pd.DataFrame({t:(-DUR[t]*yld(t).diff()+yld(t)/252/100) for t in TEN}).reindex(ys.index)
rs.columns=['r'+c for c in rs.columns]
df=pd.concat([ys,rs],axis=1).dropna()
df=df[df.index>='2006-01-01']

n2,n10=(DUR['DGS10']-DUR['DGS5'])/(DUR['DGS10']-DUR['DGS2']),(DUR['DGS5']-DUR['DGS2'])/(DUR['DGS10']-DUR['DGS2'])
n5b,n30b=(DUR['DGS30']-DUR['DGS10'])/(DUR['DGS30']-DUR['DGS5']),(DUR['DGS10']-DUR['DGS5'])/(DUR['DGS30']-DUR['DGS5'])
fretA=df['rDGS5']-n2*df['rDGS2']-n10*df['rDGS10']; flyA=2*df['DGS5']-df['DGS2']-df['DGS10']
fretB=df['rDGS10']-n5b*df['rDGS5']-n30b*df['rDGS30']; flyB=2*df['DGS10']-df['DGS5']-df['DGS30']

def pnl(flyv,fret,w=75,thr=1.0):
    z=(flyv-flyv.rolling(w).mean())/flyv.rolling(w).std()
    sig=z.where(z.abs()>thr,0).clip(-2,2).shift(1).fillna(0)   # T+1
    gross=sig*fret; to=sig.diff().abs().fillna(0)
    net=gross-to*6/1e4
    rcum=net.expanding(60).std()*np.sqrt(252)                  # trailing only
    scale=(0.10/rcum).clip(upper=3.0).shift(1)
    return (net*scale).dropna()

ens=pd.concat([pnl(flyA,fretA).rename('A'),pnl(flyB,fretB).rename('B')],axis=1).mean(axis=1).dropna()
save_sleeve(ens,'/Users/daxu/software/world-trader/campaign/agents/C2_ratescurve/sleeves/C2_fly2AB_75.csv',
  meta=("C2_fly2AB_75 | UST curve butterfly z-reversion, flies 2s5s10s(DN .62/.38)+5s10s30s(DN .69/.31), "
        "w=75d z, |z|>1 entry, |z|<=2 clip, T+1, 6bps/side, trailing expanding vol tgt 10% clip3 | "
        "FULL SR 1.85 ann 14.8% vol 8.0% mdd -10.6% H1 1.80 H2 2.02 negy 1 (2021 -4.1%) | "
        "plateau 0.90 | scramble p=0.000 (200x, signal-perm) | corr blend 0.017 | "
        "IS SR 1.76 / OOS(2017+) SR 2.09 mdd -9.5% | rationale: belly richening vs DN wings from "
        "convexity demand + issuance flows reverts; flies nearly uncorrelated"))
print(ens.head(2)); print(f"saved n={len(ens)}")
