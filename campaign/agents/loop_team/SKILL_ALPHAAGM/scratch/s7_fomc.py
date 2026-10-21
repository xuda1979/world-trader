"""S7: Pre-FOMC drift — D4 tested FOMC x natgas/gold (SR 0.53 best); SPY equity version + intraday-proxy
(close-to-close T+1 hold over announcement window, buy prior close T+1) NOT in findings — quick falsify.
POSITIVE CONTROL: 2008-2015 literature window to check the anomaly even exists in this data."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/SKILL_ALPHAAGM/scratch')
from lib import stats, champion_corr, load_champion, BPS

spy = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelvedata/SPY.csv')
spy['date'] = pd.to_datetime(spy['date']); spy = spy.set_index('date').sort_index()
print("SPY:", len(spy), spy.index.min().date(), spy.index.max().date())
fomc = []
for c in ('day1','day2'):
    col = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/newdata/fomc_dates.csv')[c]
    fomc += pd.to_datetime(col).dt.strftime('%Y-%m-%d').tolist()
fomc = set(fomc)
champ = load_champion()
r = spy['close'].pct_change()
is_fomc = pd.Series([d.strftime('%Y-%m-%d') in fomc for d in r.index], index=r.index)
# T+1: know the calendar in advance -> hold positions on FOMC days. Position set at t-1 for day t (calendar known).
W = pd.Series(np.where(is_fomc.shift(0), 1.0, 0.0), index=r.index).shift(1).fillna(0)
turn = W.diff().abs().fillna(0)
b = W*r - turn*BPS
b = b[b.index>='2008-01-01']
print("SPY pre-FOMC hold (all 2008+):", stats(b, "fomc"))
print("corr:", champion_corr(b, champ))
yrs = sorted(set(b.index.year)); yv = pd.Series([(1+b[b.index.year==y]).prod()-1 for y in yrs], index=yrs)
print("yearly:", {k: round(v,4) for k,v in yv.items()})
# positive control: literature window 2008-2015 raw mean ann
f = b[b.index<='2015-12-31']
print("2008-2015 subwindow SR:", round(f.mean()/f.std()*np.sqrt(252),3), "n days held:", int(W.reindex(b.index).sum()))
# per-ann drift: avg return on fomc days vs all days
held = r[b.index][W.reindex(b.index)>0]
allr = r[b.index]
print("mean fomc-day bp:", round(held.mean()*1e4,2), "vs all-day bp:", round(allr.mean()*1e4,2))
