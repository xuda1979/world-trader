import numpy as np, pandas as pd, pickle
from datetime import date
from dateutil.easter import easter
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT="/Users/daxu/software/world-trader"
st = pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))
BAL, A, B = st['BAL'], st['A'], st['B']
l16 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]

# --- 2a. decompose added rows ---
fix_idx = BAL.index
l16_idx = l16.index
added = fix_idx.difference(l16_idx)
print(f"FIX n={len(fix_idx)}  L16 n={len(l16_idx)}  added={len(added)}  removed={len(l16_idx.difference(fix_idx))}")
pre  = added[added < pd.Timestamp('2008-03-31')]
post = added[added > pd.Timestamp('2026-07-31')]
inw  = added[(added>=pd.Timestamp('2008-03-31')) & (added<=pd.Timestamp('2026-07-31'))]
print(f"added pre-2008-03-31 (warmup/early): {len(pre)}  first {pre[0].date()} last {pre[-1].date()}")
print(f"added in-window recoveries:          {len(inw)}")
print(f"added post-2026-07-31 extension:     {len(post)}  first {post[0].date()} last {post[-1].date()}")

# --- 2b. weekend / federal-holiday scan on ALL FIX rows ---
hol = set(d.date() for d in USFederalHolidayCalendar().holidays(start='2006-01-01', end='2026-12-31'))
wk = [d for d in fix_idx if d.dayofweek>=5]
fh = [d for d in fix_idx if d.date() in hol]
print(f"FIX rows on weekends: {len(wk)}   on US-federal holidays: {len(fh)}")
if fh: print("  federal-holiday rows:", [str(d.date()) for d in fh][:20])

# --- 2c. NYSE-closed-but-not-federal days present in FIX rows? ---
gfs = []
for y in range(2006,2027):
    d = pd.Timestamp(easter(y)) - pd.Timedelta(days=2)
    gfs.append(d.date())
gf_rows = [d for d in fix_idx if d.date() in gfs]
print(f"Good Fridays 2006-2026: {len(gfs)}; FIX rows falling ON Good Friday: {len(gf_rows)}")
if gf_rows: print("  dates:", [str(d.date()) for d in gf_rows])
nyse_closed_extra = [date(2007,1,2), date(2012,10,29), date(2012,10,30), date(2018,12,5), date(2025,1,9)]
hits = [d for d in fix_idx if d.date() in nyse_closed_extra]
print(f"FIX rows on other NYSE full closures (2007-01-02 Ford, 2012-10-29/30 Sandy, 2018-12-05 Bush, 2025-01-09 Carter): {len(hits)}")
if hits: print("  dates:", [(str(d.date()), float(BAL[d])*1e4) for d in hits])

# --- 2d. federal-but-NYSE-OPEN days (Columbus, Veterans) — smeared by sn() ---
columbus = []
for y in range(2006,2027):
    d = pd.Timestamp(year=y, month=10, day=1)
    while d.dayofweek!=0: d += pd.Timedelta(days=1)
    columbus.append(d + pd.Timedelta(weeks=1))  # 2nd Monday
vets = [pd.Timestamp(year=y, month=11, day=11) for y in range(2006,2027)]
vets = [v + pd.Timedelta(days=1) if v.dayofweek==6 else (v - pd.Timedelta(days=2) if v.dayofweek==0 else v) for v in vets]  # observed Fri/Mon per federal rule
# how many of these days fall between FIX rows (i.e. were dropped & smeared)?
dropped_cv = [d for d in columbus+vets if (d>=fix_idx[0]) and (d<=fix_idx[-1]) and (d not in fix_idx) and d.dayofweek<5]
print(f"Columbus/Veterans (federal, NYSE OPEN) days dropped by sn(): {len(dropped_cv)} -> P&L smeared to next kept day")

# --- 2e. in-window recovery-day P&L (adverse-selection recheck) ---
rec = BAL.reindex(inw)
print(f"in-window recovered {len(inw)} days: mean {rec.mean()*1e4:.2f} bp/day, sum {rec.sum()*100:.2f}% cum")
print(f"  FIX in-window (2008-03-31..2026-07-31) n={((fix_idx>=pd.Timestamp('2008-03-31'))&(fix_idx<=pd.Timestamp('2026-07-31'))).sum()}")
