import numpy as np, pandas as pd, pickle
from datetime import date
from dateutil.easter import easter
ROOT="/Users/daxu/software/world-trader"
st = pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))
BAL = st['BAL']
POOL = {
 "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10": "campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7" :"campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5" :"campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng"  :"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2"  :"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7"  :"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0); df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)
raw = {n: load(p) for n,p in POOL.items()}

gfs = [ (pd.Timestamp(easter(y)) - pd.Timedelta(days=2)) for y in range(2007,2027) ]
print("=== Good Friday rows: which sleeves have raw data, and raw returns (bp) ===")
for gf in gfs[-6:]:  # last 6 GFs
    have = [n for n,r in raw.items() if gf in r.index]
    vals = {n: round(float(raw[n][gf])*1e4,1) for n in have}
    nxt = gf + pd.Timedelta(days=4)  # Monday
    vals_next = {n: round(float(raw[n][nxt])*1e4,1) for n in have if nxt in raw[n].index}
    print(f"{gf.date()} FIX_BAL={float(BAL[gf])*1e4:.1f}bp sleeves={len(have)} raw={vals}")
    print(f"   following-Mon raw: {vals_next}")

print()
print("=== 2018-12-05 attribution ===")
d = pd.Timestamp('2018-12-05')
for n,r in raw.items():
    if d in r.index: print(f"  {n}: {float(r[d])*1e4:.1f}bp")
print("  FIX_BAL that day:", f"{float(BAL[d])*1e4:.1f}bp")

print()
print("=== in-window weekdays STILL missing from FIX (no row at all) ===")
hol = set(x.date() for x in pd.date_range('2006-01-01','2026-12-31', freq=None)[:0]) # placeholder
from pandas.tseries.holiday import USFederalHolidayCalendar
holset = set(d.date() for d in USFederalHolidayCalendar().holidays(start='2006-01-01', end='2026-12-31'))
alldays = pd.bdate_range('2008-03-31','2026-07-31')
miss = [d for d in alldays if d not in BAL.index and d.dayofweek<5 and d.date() not in holset]
print(f"non-federal weekdays in window missing from FIX: {len(miss)}")
for d in miss:
    have = [n for n,r in raw.items() if d in r.index]
    print(f"  {d.date()} dow={d.dayofweek} sleeves_with_data={have}")
