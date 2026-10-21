"""IDEA 5 (CHARTER_2): industry RELATIVE-STRENGTH vs SPX — ratio momentum on 48 ind/SPY.
Long industries with strongest 63d ratio momentum, short weakest, k=3/6, weekly."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from c1_lib import kf48, bt
from c1r2_lib import evaluate, weekly_positions

ind = kf48(); rets = ind.iloc[:, :48]
# SPX proxy: use value-weighted avg of all 48 industries (cap-weighted market proxy)
mkt = rets.mean(axis=1)
rel = rets.sub(mkt, axis=0)  # daily relative return vs market
for look in [21, 63, 126]:
    rs = rel.rolling(look).sum()
    for k in [3, 6, 10]:
        r = rs.rank(axis=1); n = rel.shape[1]
        w = pd.DataFrame(0.0, index=rs.index, columns=rs.columns)
        w[r > n-k] = 1.0/k; w[r <= k] = -1.0/k
        net, _, _ = bt(weekly_positions(w), rets)
        evaluate(net, f'RS-vs-mkt look{look} k{k} weekly')
