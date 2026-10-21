import sys, numpy as np, pandas as pd, os
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_HF_STATARB/scratch')
import al_statarb as ALF, al_proper as ALP
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
DATA="/Users/daxu/software/world-trader/tools/quant/data/twelve_big"
UNI=['AAPL','MSFT','GOOGL','GOOG','AMZN','NVDA','META','TSLA','JPM','BAC','C','WFC','GS','MS','XOM','CVX','KO','PEP','PG','JNJ','PFE','MRK','UNH','AMD','INTC','CSCO','ORCL','IBM','DIS','CMCSA','NKE','WMT','HD','MCD','COST','GE','BA','CAT','HON','UNP','AXP','V','MA','T','VZ']
PRICE={}
for t in UNI:
    p=f"{DATA}/{t}.csv"
    if os.path.exists(p):
        df=pd.read_csv(p); df['date']=pd.to_datetime(df['date']); PRICE[t]=df.set_index('date')['close'].astype(float).sort_index()
px=pd.DataFrame(PRICE).ffill()
present=px[px.index>='2011-01-01'].notna().all(); px=px.loc[:,present]
lr=np.log(px/px.shift(1)).replace([np.inf,-np.inf],np.nan)
resid=ALF.roll_pca_resid(lr,60,6)
champ=E.champ_ref()
print(f"Universe {resid.shape[1]} names, {resid.shape[0]} days")
for sign in [+1,-1]:
    for en,ex in [(1.25,0.75),(1.5,0.75),(1.0,0.5)]:
        net,gr,turn,pos=ALP.run(resid,entry=en,exit_t=ex,sign=sign)
        nr=net['2011':].dropna(); nv,_=E.vol_target(nr,vt_ann=0.08)
        st=E.evaluate(nv,champ,'al')
        print(f"sign={sign:+d} en={en} ex={ex}: grossSR={gr['2011':].dropna().mean()/gr['2011':].dropna().std()*np.sqrt(252):+.3f} "
              f"netSR={st['SR']:+.3f} ann={st['ann_geo']*100:+.1f}% negy={st['negyr']} corr={st['corr_champ']:+.3f} turn={turn.mean():.2f} uniq={st['uniqR']:.2f}")
