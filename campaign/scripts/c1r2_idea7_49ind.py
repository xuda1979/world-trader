"""IDEA 7 (pivot): 49-industry dataset + 25ff size-x-value legs as TS books, plus
BEST-OF-ROUND-1 revisit: sv25 small-value spread timing w=21 sign with regime filter.
New twist on R1 finding: gate sv25 spread-momentum by market vol (VIX-free proxy: trailing
21d EW-48 realized vol) — trade only when vol regime favorable."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from c1_lib import kf49, load_kf, bt, KF
from c1r2_lib import evaluate, weekly_positions

ind49 = kf49()
rets = ind49.iloc[:, :49]
# 49-industry momentum: cross-sectional, look126 skip21 hold21 top3-bot3 weekly (R1 best cell family)
mom = rets.rolling(126).sum() - rets.rolling(21).sum()
r = mom.rank(axis=1); n = rets.shape[1]
w = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
w[r > n-3] = 1.0/3; w[r <= 3] = -1.0/3
net, _, _ = bt(weekly_positions(w), rets)
evaluate(net, '49ind mom 126-21 top3-bot3 weekly')
# and 49ind vol-sorted long-low (from Idea-1 family but 49)
vol = rets.rolling(63).std()
rk = vol.rank(axis=1)
w2 = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
w2[rk <= 6] = 1.0/6; w2[rk > 43] = -1.0/6
net2, _, _ = bt(weekly_positions(w2), rets)
evaluate(net2, '49ind volsort L63 k6 weekly')

# --- sv25 regime-filtered ---
p25 = load_kf(f'{KF}/25_Portfolios_5x5_Daily.csv', 'Average Value Weighted Returns -- Daily')
sv = p25['SMALL HiBM'] - p25['SMALL LoBM']
pos = np.sign(sv.rolling(21).sum()).rename('sv')
pos = pd.DataFrame({'sv': pos})
net3, _, _ = bt(pos, pd.DataFrame({'sv': sv}))
evaluate(net3, 'sv25 w21 sign (R1 best, recheck)')
# regime filter: mkt realized vol trailing 21d; trade only when vol < expanding 75th pct
mktv = rets.pow(2).mean(axis=1).pow(0.5)
rv = mktv.rolling(21).mean()
q75 = rv.expanding(min_periods=252).quantile(0.75)
gate = (rv <= q75)
pos_g = pos['sv'].where(gate.reindex(pos.index).fillna(False), 0.0)
pos_g = pd.DataFrame({'sv': pos_g})
net4, _, _ = bt(pos_g, pd.DataFrame({'sv': sv}))
evaluate(net4, 'sv25 w21 sign gated mkt-vol<75pct')
# gate v<50pct
q50 = rv.expanding(min_periods=252).quantile(0.50)
pos_g2 = pos['sv'].where((rv <= q50).reindex(pos.index).fillna(False), 0.0)
net5, _, _ = bt(pd.DataFrame({'sv': pos_g2}), pd.DataFrame({'sv': sv}))
evaluate(net5, 'sv25 w21 sign gated mkt-vol<50pct')
