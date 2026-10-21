"""S2: Nikkei 225 calendar/overnight split. FRED NIKKEI225 is the daily CLOSE (level).
True overnight/intraday split impossible without OHLC. Stage-0 proxies instead:
(a) day-of-week conditioned LONG; (b) Turn-of-month long. T+1 via calendar signal."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/SKILL_ALPHAAGM/scratch')
from lib import stats, sr_d, champion_corr, load_champion, BPS

nk = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/newdata/NIKKEI225.csv')
nk.columns = ['date','close']
nk['date'] = pd.to_datetime(nk['date'])
nk = nk.set_index('date').sort_index()
print("rows:", len(nk), nk.index.min().date(), nk.index.max().date())
r = nk['close'].pct_change()
champ = load_champion()

def calibook(mask, name, pool_ret=None):
    pr = pool_ret if pool_ret is not None else r
    W = pd.Series(np.where(mask, 1.0, 0.0), index=r.index).shift(1).fillna(0)
    turn = W.diff().abs().fillna(0)
    b = W*pr - turn*BPS
    b = b[b.index>='2008-01-01']
    st = stats(b, name)
    print(name, st, "| corr to V3:", champion_corr(b, champ))
    return b

dow = r.index.dayofweek
# (a) day-of-week: historically Tue/Wed weaker for NKY in some eras; test each DOW long-only
for d in range(5):
    calibook(dow==d, f"NKY dow{d} long-only")

# (b) turn-of-month
grp = r.index.to_period('M')
rim = r.groupby(grp).cumcount(); nim = r.groupby(grp).transform('size')
calibook((rim>=nim-4)|(rim<=2), "NKY turn-of-month")
