"""S3: Propane seasonal short (inventories peak Nov-Mar). FRED DPROPANEMBTX (hedge_fund_strats full history).
Disclosure: NO storage/inventory data -> this is a CALENDAR-seasonal short, weaker premise (fail-closed disclosed)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/SKILL_ALPHAAGM/scratch')
from lib import stats, champion_corr, load_champion, BPS

df = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DPROPANEMBTX.csv')
df.columns = ['date','px']
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date').sort_index()
df = df[df['px'] != '.']
df['px'] = df['px'].astype(float)
print("rows:", len(df), df.index.min().date(), df.index.max().date())
r = df['px'].pct_change()
champ = load_champion()
m = pd.Series(r.index.month, index=r.index)
W = pd.Series(np.where((m>=11)|(m<=3), -1.0, 0.0), index=r.index).shift(1).fillna(0)
turn = W.diff().abs().fillna(0)
borrow = np.clip(W,0,None)*0.005/252  # short leg
b = W*r - turn*BPS - borrow
b = b[b.index>='2008-01-01']
print("Propane winter-short:", stats(b, "propane-winter-short"))
print("corr to V3:", champion_corr(b, champ))
yrs = sorted(set(b.index.year))
yv = pd.Series([(1+b[b.index.year==y]).prod()-1 for y in yrs], index=yrs)
print("yearly:", {k: round(v,4) for k,v in yv.items()})
