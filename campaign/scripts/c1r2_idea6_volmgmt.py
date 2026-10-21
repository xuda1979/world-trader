"""IDEA 6 (pivot): KF portfolio VOLATILITY-MANAGEMENT overlay engines (Moreira-Muir style),
which Round-1 showed is the only genuine post-2008 phenomenon in this domain.
(a) vol-managed SMB (ME deciles 10) — Round 1 tested UMD only.
(b) vol-managed HML proxy: BIG HiBM - BIG LoBM.
(c) vol-managed market: EW-48 industries (proxy Mkt-RF), scaled by inverse trailing vol.
(d) vol-managed combo: SMBff + HMLbig + UMD each vol-managed, EW.
All net T+1, 6bps on spread turnover."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from c1_lib import load_kf, bt, KF
from c1r2_lib import evaluate
import c1_lib as L

ff = L  # for ff_factors
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import ff_factors, ff_mom

ff_f = ff_factors(); mom_f = ff_mom()
fac = pd.concat([ff_f[['SMB','HML']], mom_f[['Mom']]], axis=1).dropna()

def vol_managed(book, look=21, cap=4.0):
    v = book.rolling(look).std().shift(1) * np.sqrt(252)
    w = (0.10 / v).clip(upper=cap).fillna(0.0)
    pos = pd.DataFrame({'b': w})
    net, gross, to = bt(pos, pd.DataFrame({'b': book}))
    return net, gross

for look in [21, 63]:
    for col in ['SMB', 'HML', 'Mom']:
        book = fac[col]
        net, _ = vol_managed(book, look)
        evaluate(net, f'VM {col} look{look}')
    # EW combo
    books = fac[['SMB','HML','Mom']].copy()
    v = books.rolling(look).std().shift(1) * np.sqrt(252)
    wb = (0.10 / v).clip(upper=4.0)
    legnet = []
    for c in books.columns:
        pos = pd.DataFrame({'b': wb[c]})
        n_, _, _ = bt(pos, pd.DataFrame({'b': books[c]}))
        legnet.append(n_)
    evaluate(sum(legnet)/3, f'VM combo SMB+HML+Mom look{look}')

# (d) vol-managed industry momentum from Round-1 best cell (126/21/hold21 top3-bot3) with
#     aggregate vol overlay: scale entire book by inverse of book's own trailing vol
ind = kf48(); rets = ind.iloc[:, :48]
mom = rets.rolling(126).sum()
r = mom.rank(axis=1); n = rets.shape[1]
w = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
w[r > n-3] = 1.0/3; w[r <= 3] = -1.0/3
from c1r2_lib import weekly_positions
wf = weekly_positions(w)
net, gross, to = bt(wf, rets)
# overlay: inverse vol of the net book itself, trailing 63d
v = net.rolling(63).std().shift(1)*np.sqrt(252)
scale = (0.10/v).clip(upper=3.0).fillna(0.0)
evaluate(net*scale, 'indmom126 with own-vol overlay 63d')
