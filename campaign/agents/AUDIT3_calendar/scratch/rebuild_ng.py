"""AUDIT3 independent rebuild of natgas weekday sleeves from raw DHHNGSP.
Spec per meta: Mon+? check map: code says Wed- Thu- Fri+. calm k=2.5 vs trailing 90d sigma
(shifted), T+1, 6bps/side on |dpos|, expanding vt10 min60 cap3."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader')
from campaign.agents.B2_highfreq.gates import vol_target

COST = 6e-4
D = '/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
MONTHS = list(range(4, 11))

def build(summer=False, k=2.5, truncate_2008=False, legs=(-1.0, -1.0, +1.0),
          dows=(2, 3, 4)):
    s = pd.read_csv(D, index_col=0, parse_dates=True).iloc[:, 0]
    s = pd.to_numeric(s, errors='coerce'); s = s[s > 0].dropna().sort_index()
    lr = np.log(s).diff(); idx = lr.index
    pos = pd.Series(0.0, index=idx)
    for d, v in zip(dows, legs):
        pos[idx.dayofweek == d] = v
    if summer:
        pos[~idx.month.isin(MONTHS)] = 0.0
    thr = lr.rolling(90).std().shift(1) * k
    pos = pos.mask(lr.abs() > thr, 0.0)
    gr = pos * lr.shift(-1)
    turn = pos.diff().abs(); turn.iloc[0] = abs(pos.iloc[0])
    net = (gr - turn * COST).dropna()
    if truncate_2008:
        net = net[net.index >= '2008-01-01']
    scaled, _ = vol_target(net)
    return scaled.dropna()

if __name__ == '__main__':
    import pickle
    out = {}
    out['C5ng_trunc'] = build(truncate_2008=True)
    out['C5ngsum_trunc'] = build(summer=True, truncate_2008=True)
    out['C5ng_full'] = build()
    out['C5ngsum_full'] = build(summer=True)
    with open('/Users/daxu/software/world-trader/campaign/agents/AUDIT3_calendar/scratch/rebuilt.pkl', 'wb') as f:
        pickle.dump(out, f)
    for k_, v in out.items():
        print(k_, len(v), v.index.min().date(), v.index.max().date())
