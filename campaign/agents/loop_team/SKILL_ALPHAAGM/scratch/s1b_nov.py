"""S1b: seasonal effects on FF 25 pools (long-only, T+1). P1=SMALL LoBM (col0), P25=BIG HiBM (col24)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/SKILL_ALPHAAGM/scratch')
from lib import stats, sr_d, champion_corr, load_champion, BPS

lines = open('/tmp/ska_zip25/25_Portfolios_5x5_Daily.csv').readlines()
hdr_i = 18
data = []
for ln in lines[hdr_i+2:]:
    parts = ln.strip().split(',')
    if len(parts) != 26: break
    data.append(parts)
raw = pd.DataFrame(data).astype(float)
raw[0] = pd.to_datetime(raw[0], format='%Y%m%d')
raw = raw.set_index(0)
r = raw/100.0
r.columns = ['P%d'%i for i in range(25)]
r = r[r.index >= '2006-01-01']
champ = load_champion()

def seasonal(months_hold, pool, name):
    m = pd.Series(r.index.month, index=r.index)
    W = pd.Series(np.where(m.isin(months_hold), 1.0, 0.0), index=r.index)
    W = W.shift(1).fillna(0)
    turn = W.diff().abs().fillna(0)
    b = (W*r[pool] - turn*BPS)
    b = b[b.index>='2008-01-01']
    print(name, stats(b, name)); print("  corr to V3:", champion_corr(b, champ))
    yv = (1+b).groupby(b.index.year).apply(lambda x:(1+x).prod()-1)
    print("  yearly:", {k: round(v,4) for k,v in yv.items()})
    return b

b_nov = seasonal([11,12,1], 'P0', "P1(SmallGrowth) Nov-Jan")
seasonal([12], 'P24', "P25(BigValue) Dec-only")
# Turn-of-month on P1
grp = r.index.to_period('M')
rim = r.groupby(grp).cumcount()
nim = r.groupby(grp)['P0'].transform('size')
W = pd.Series(np.where((rim >= nim-4) | (rim <= 2), 1.0, 0.0), index=r.index).shift(1).fillna(0)
turn = W.diff().abs().fillna(0)
b_tom = W*r['P0'] - turn*BPS
b_tom = b_tom[b_tom.index>='2008-01-01']
print("P1 turn-of-month:", stats(b_tom, "P1-TOM")); print("  corr:", champion_corr(b_tom, champ))
