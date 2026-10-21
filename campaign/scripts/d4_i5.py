import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

gas = L.newdata('GASREGW')          # weekly Monday-dated avg retail price $/gal
wti = L.newdata('DCOILWTICO')
print("GASREGW:", gas.index[0].date(), gas.index[-1].date(), len(gas), "weekday dist:", gas.index.dayofweek.value_counts().to_dict())
print("gaps>10d:", (gas.index.to_series().diff().dt.days > 10).sum())

margin = np.log(gas*42) - np.log(wti.reindex(gas.index, method='ffill', limit=5))
margin = margin.dropna()
print("margin pts:", len(margin), margin.index[0].date(), margin.index[-1].date())

wti_d = L.logret(wti)
idx = wti_d.index
idx = idx[idx >= margin.index[0]]

def weekly_pos(lb, sgn, hold='week'):
    z = (margin - margin.rolling(lb).mean())/margin.rolling(lb).std()
    # daily signal: last Monday print's z
    sig = z.reindex(idx, method='ffill', limit=7)
    pos = (sgn * -z).shift(0)
    pos = pos.reindex(idx, method='ffill', limit=7).fillna(0)
    # T+1: signal print Monday t available after close; earn from next day
    return pos

for lb in [8, 13, 26, 52]:   # weeks
    for sgn in [1, -1]:
        pos = weekly_pos(lb, sgn)
        gross = L.t1_pnl(pos, wti_d.reindex(pos.index).fillna(0))
        # turnover: position changes at ~weekly freq
        net = L.vt10(L.net_turnover(pos, wti_d.reindex(pos.index).fillna(0)))
        s = L.full_stats(net); h1,h2 = L.halves_sr(net)
        print(f"margin z-rev lb{lb}w sgn{sgn}: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} worst {s['worst']:.1f}% H1 {h1:.2f} H2 {h2:.2f}")

# raw t: weekly margin changes autocorr
dm = margin.diff().dropna()
print("weekly margin chg t:", dm.mean()/dm.std()*np.sqrt(len(dm)), "ar1:", dm.autocorr())
