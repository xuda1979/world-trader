"""MARGINAL VALUE TEST of FXD1_KRWTRI_raw at champion level (charter iter5 convention):
blend GOAL100_HONEST14V3_BALANCED with FXD1 at sleeve-slot-style weights: since the champion
already blends internally, use the simple mix: blend = (1-w)*champ + w*(FXD1*10) ? NO —
campaign convention for marginal diagnostics (FF2/BASIS2): add the new sleeve as a fraction of
total capital: r_new_champ = champ*(1-w) + FXD1*w (FXD1 raw at its 4.2% vol, vt-adjusted?).
Report SR_d, SR_m, ann_geo, MDD, neg yrs for w in {0.02,0.05,0.10,0.15}. Use poolvt variant too.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

champ=load_champion()
raw=pd.read_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_raw_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
vt=pd.read_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_poolvt_daily.csv',index_col=0,parse_dates=True).iloc[:,0]

def sr_m(r):
    m=(1+r).resample('ME').prod()-1
    return m.mean()/m.std()*np.sqrt(12)

def stats(r):
    r=r.dropna()
    eq=(1+r).cumprod()
    return dict(sr=r.mean()/r.std()*np.sqrt(252), srm=sr_m(r),
                ann=(eq.iloc[-1])**(252/len(r))-1,
                mdd=(eq/eq.cummax()-1).min(),
                negy=int(((1+r).groupby(r.index.year).apply(lambda x:(1+x).prod()-1)<0).sum()))

st=stats(champ)
print('champion:      SR_d %.3f SR_m %.3f ann %.1f%% MDD %.2f%% negy %d'%(st['sr'],st['srm'],st['ann']*100,st['mdd']*100,st['negy']))
for w in [0.02,0.05,0.10,0.15]:
    for tag,sl in [('raw',raw),('vt',vt)]:
        b=champ*(1-w)+sl.reindex(champ.index).fillna(0)*w
        s=stats(b)
        print(f'w={w:.2f} {tag}: SR_d {s["sr"]:.3f} SR_m {s["srm"]:.3f} ann {s["ann"]*100:.1f}% MDD {s["mdd"]*100:.2f}% negy {s["negy"]}')
