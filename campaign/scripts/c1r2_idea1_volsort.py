"""IDEA 1 (CHARTER_2): 48-industry vol-sorted rotation — long low-vol industries, short high-vol.
Lookbacks 21/63/126d trailing vol, k=6/10 industries per side, weekly & daily rebalance."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from c1_lib import kf48, bt
from c1r2_lib import evaluate, weekly_positions

ind = kf48()
rets = ind.iloc[:, :48]  # VW returns
results = []
for look in [21, 63, 126]:
    vol = rets.rolling(look).std()
    ranks = vol.rank(axis=1)
    n = rets.shape[1]
    for k in [6, 10]:
        lo = (ranks <= k)    # low vol industries
        hi = (ranks > n - k) # high vol industries
        w = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
        w[lo] = 1.0/k
        w[hi] = -1.0/k
        for reb, wf in [('daily', w), ('weekly', weekly_positions(w))]:
            net, gross, to = bt(wf, rets)
            ev = evaluate(net, f'volsort L{look} k{k} {reb}')
            results.append((ev['sr'] if ev else np.nan, look, k, reb, ev))
results.sort(key=lambda x: -x[0] if not np.isnan(x[0]) else 9)
print('\nTOP 5:')
for sr, look, k, reb, ev in results[:5]:
    print(f'  L{look} k{k} {reb}: SR {sr}')
print('\nBOTTOM 3:')
for sr, look, k, reb, ev in results[-3:]:
    print(f'  L{look} k{k} {reb}: SR {sr}')
