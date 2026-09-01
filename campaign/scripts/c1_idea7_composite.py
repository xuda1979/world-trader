"""C1 idea 7: composite of best 3 KF sub-engines (2008+, T+1, 6bps one-side).
Legs: (1) 21d-sign-timed SMALL HiBM-LoBM spread, (2) vol-managed FF UMD (63d var, cap3),
(3) 252d/21d-skip industry momentum L/S top3-bot3, hold 21d.
Run: python3 campaign/scripts/c1_idea7_composite.py"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.scripts.c1_lib import load_kf, kf48, bt, vt, stats, gates, save
from campaign.harness.data import ff_mom
K='/Users/daxu/software/world-trader/tools/quant/data/kenfrench'
COST=6.0/1e4
p25 = load_kf(f'{K}/25_Portfolios_5x5_Daily.csv','Average Value Weighted Returns -- Daily')
v48, e48 = kf48(), kf48('Average Equal Weighted Returns -- Daily')

sv = (p25['SMALL HiBM']-p25['SMALL LoBM']).dropna()
pos = np.sign(sv.rolling(21).mean()).shift(1)
leg1 = ((sv.loc['2008':]*pos.loc['2008':]) - pos.loc['2008':].diff().abs().fillna(0)*COST).dropna()

x = ff_mom()['Mom'].loc['2008':]
scal = (0.10/np.sqrt(x.rolling(63).var()*252)).clip(upper=3.0).shift(1)
leg2 = (x*scal).dropna()

def indmom_hold(src_, rets_, look, topk, hold, skip=0, lo=False):
    mm = src_.shift(skip).rolling(look).sum()
    rk = mm.rank(axis=1, ascending=False); n=mm.shape[1]
    W = pd.DataFrame(0.0, index=mm.index, columns=mm.columns)
    W[rk<=topk]=1.0/topk
    if not lo: W[rk>n-topk]=-1.0/topk
    W = W.where(mm.notna(), 0.0)
    d=np.arange(len(W)); rb=(d%hold==0)
    Wh=W.copy(); Wh[~rb]=np.nan; Wh=Wh.ffill().fillna(0.0)
    return bt(Wh, rets_)[0]
leg3 = indmom_hold(v48, v48.loc['2008':], 252, 3, 21, 21, False)

comp = pd.concat([leg1.rename('l1'), leg2.rename('l2'), leg3.rename('l3')], axis=1, sort=True).dropna()
def to10(s):
    rc = s.expanding(60).std()*np.sqrt(252)
    return (s*(0.10/rc).clip(upper=3.0)).fillna(0)
comp = pd.DataFrame({c: to10(comp[c]) for c in comp.columns})
port = comp.mean(axis=1)
nvt,_ = vt(port)
s = stats(nvt); g = gates(nvt)
print(f"COMPOSITE: vtSR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% H1={g['H1']:.2f} H2={g['H2']:.2f} "
      f"negy={s['negy']} worst={s['worst']:.1f}% corrB={g['corr_blend']:+.2f} scr={g['scramble_p']:.3f} pass={g['all_pass']}")
print('failed:', [k for k,v in g['gates'].items() if not v])
