"""Run Avellaneda-Lee on a liquid large-cap subset, gate it honestly."""
import sys, numpy as np, pandas as pd, os, time
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_HF_STATARB/scratch')
import al_statarb as AL
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
DATA="/Users/daxu/software/world-trader/tools/quant/data/twelve_big"
OUT="/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_HF_STATARB/sleeves"
champ=E.champ_ref()
UNI=['AAPL','MSFT','GOOGL','GOOG','AMZN','NVDA','META','TSLA','JPM','BAC','C','WFC','GS','MS','XOM','CVX','COP','SLB','OXY','KO','PEP','PG','KMB','JNJ','PFE','MRK','UNH','AMD','INTC','CSCO','ORCL','IBM','DIS','CMCSA','NKE','T','VZ','WMT','HD','MCD','COST','GE','BA','CAT','MMM','HON','UNP','UPS','FDX','AIG','AXP','V','MA']
PRICE={}
for t in UNI:
    p=f"{DATA}/{t}.csv"
    if os.path.exists(p):
        df=pd.read_csv(p); df['date']=pd.to_datetime(df['date'])
        PRICE[t]=df.set_index('date')['close'].astype(float).sort_index()
px=pd.DataFrame(PRICE).ffill().dropna(axis=1)
px=px[(px.index>='2008-01-01')]
print(f"Universe: {px.shape[1]} stocks, {px.shape[0]} days, {px.index.min().date()}..{px.index.max().date()}")
logret=np.log(px/px.shift(1)).replace([np.inf,-np.inf],np.nan)
# restrict to names present for the whole window (avoid entries noise)
present=logret[logret.index>='2010-01-01'].notna().all()
px2=px.loc[:,present]; logret2=logret.loc[:,present]
print(f"Full-history names: {px2.shape[1]}")
t0=time.time()
resid=AL.roll_pca_resid(logret2, lookback=60, n_pc=6)
ss=AL.s_scores(resid, lookback=60)
print(f"PCA+sscore done in {time.time()-t0:.0f}s, resid shape {resid.shape}")
for entry in [1.25, 1.5]:
    for exit_thr in [0.75, 0.5]:
        pos=AL.build_book(ss, entry=entry, exit=exit_thr, long_frac=0.2, short_frac=0.2)
        net,gr,turn=AL.backtest(pos, logret2, cost_bps=10.0)
        nr=net['2010':].dropna()
        # vol target
        nv,_=E.vol_target(nr,vt_ann=0.08)
        st=E.evaluate(nv,champ,'al_statarb')
        print(f"entry={entry} exit={exit_thr}: SR={st['SR']:+.3f} ann={st['ann_geo']*100:+.1f}% MDD={st['MDD']*100:.1f}% "
              f"negy={st['negyr']} corr={st['corr_champ']:+.3f} H=({st['H1_H2'][0]:.2f},{st['H1_H2'][1]:.2f}) turn={turn.mean():.4f}")
