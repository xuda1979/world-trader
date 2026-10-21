"""S4: 10y TIPS vs 10y nominal (breakeven RV) — T+1 only. tools/quant/hedge_fund_strats/data_fred/DFII10 + DGS10."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/SKILL_ALPHAAGM/scratch')
from lib import stats, champion_corr, load_champion, BPS

base = '/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred/'
t = pd.read_csv(base+'DFII10.csv'); n = pd.read_csv(base+'DGS10.csv')
for df in (t, n):
    df.columns = ['date','y']; df['date']=pd.to_datetime(df['date']); df.set_index('date', inplace=True)
y = pd.concat([pd.to_numeric(t['y'],errors='coerce').rename('tips'), pd.to_numeric(n['y'],errors='coerce').rename('nom')],axis=1).dropna().sort_index()
y = y[y.index>='2004-01-01']
print("rows:", len(y), y.index.min().date(), y.index.max().date())
D = 8.5
rt = -D*y['tips'].diff()/100
rn = -D*y['nom'].diff()/100
champ = load_champion()
be = y['nom']-y['tips']
for win in (21, 63, 126):
    for mode in ('zrev','mom'):
        z = (be - be.rolling(win).mean())/be.rolling(win).std()
        if mode=='zrev': sig = -np.clip(z.shift(1),-2,2)/2
        else: sig = np.sign(z.shift(1))
        w_n = 0.5*sig; w_t = -0.5*sig
        gross = w_n*rn + w_t*rt
        turn = (w_n.diff().abs()+w_t.diff().abs()).fillna(0)
        borrow = np.clip(-(w_n+w_t),0,None)*0.005/252
        b = (gross-turn*BPS-borrow); b = b[b.index>='2008-01-01']
        st = stats(b, f"be-{mode}{win}")
        print(f"breakeven {mode} win={win}: SR_d {st['SR_d']} ann {st['ann_geo']} MDD {st['MDD']} negy {st['negy']} worst {st['worst_yr']} H1 {st['H1']} H2 {st['H2']} ac1 {st['ac1']} uniqR {st['uniqR']} corr {champion_corr(b, champ)}")
