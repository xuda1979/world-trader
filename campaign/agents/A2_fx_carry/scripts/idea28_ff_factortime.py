"""Charter 3: monthly factor timing on FF Mkt/SMB/HML/Mom. 252d lookback momentum of each factor,
hold best factor next month at 2x (documented; vt on top per contract g). Decision at last trading
day of month m uses factor returns <= that day (FF factors are public same day). T+1 by convention."""
import sys; sys.path.insert(0, __file__.rsplit("/",1)[0])
from r4_lib import *

FF = pd.concat([ff_factors()[["Mkt-RF","SMB","HML"]], ff_mom()[["Mom"]]], axis=1).dropna()
RETS = FF  # factor returns (excess for Mkt; SMB/HML/Mom are L/S spreads -> cash leg ignored, documented)

def monthly_positions(lb, k=1, absmin=0.0):
    m = (1+RETS).resample("ME").prod() - 1.0          # monthly factor returns
    mom = m.rolling(lb).apply(lambda x: (1+x).prod()-1, raw=False)
    mom = mom.shift(1)                                 # month m+1 signal uses months <= m (publish ok)
    pos = pd.DataFrame(0.0, index=mom.index, columns=mom.columns)
    for dt, row in mom.iterrows():
        r = row.dropna()
        if len(r) == 0: continue
        best = r.idxmax()
        if r[best] > absmin: pos.loc[dt, best] = 2.0
    return pos

def sleeve(pos, vt):
    # daily: hold chosen factor over next month; decision-date convention with next-day start
    daily = pos.reindex(pd.bdate_range(RETS.index[0], RETS.index[-1])).ffill()
    # shift monthly decision to first daily bday of next month (signal known at month close)
    daily = daily.shift(1).fillna(0.0)
    daily = daily.loc[daily.index.intersection(RETS.index)]
    rets_d = RETS.reindex(daily.index).fillna(0.0)
    gross = (daily * rets_d).sum(axis=1)
    to = daily.diff().abs().sum(axis=1).fillna(0)
    net = cost(gross, to)
    return vol_target(net, vt).dropna()

for lb in (126, 252, 378):
    for vt in (0.10, 0.20):
        r = sleeve(monthly_positions(lb), vt)
        g = full_gates(r); c, n = corr_to_champ(r)
        pr(f"FF-best1-lb{lb}-2x-vt{int(vt*100)}", g, c, f"n={n}")
