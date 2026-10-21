"""Panel long-only crypto satellite builder via campaign/bt (charter step 1).
Universe = 12 coins, per-day available (listing-based union; survivorship of the
UNIVERSE SELECTION disclosed in FINDINGS). Weight budget 1.0 split across listed coins.
"""
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'agents/loop_team/HUNT_CRYPTO_SAT')
import numpy as np, pandas as pd
from crypto_lib import COINS, load_coin, tsmom_sig, rev_sig
from bt import engine as E, metrics as M, gates as G


def panel(sig_fn, lb, target=0.10, window=60, vcap=3.0, per_name_cap=1.0,
          long_only=True, bps=6.4, universe=None):
    uni = universe or COINS
    pxs, rss = {}, {}
    for s in uni:
        px = load_coin(s)
        pxs[s] = px
        rss[s] = px.pct_change()
    P = pd.DataFrame(pxs)
    R = pd.DataFrame(rss)
    n_avail = P.notna().sum(axis=1)
    W = {}
    for s in uni:
        sig = sig_fn(P[s], lb)
        pos = E.lag_signal(sig.reindex(P.index).fillna(0.0))
        if long_only:
            pos = pos.clip(lower=0.0)
        scale = E.vol_target_scale(R[[s]].fillna(0.0), target=target, window=window,
                                   cap=vcap)
        w = (pos * scale[s]).clip(lower=-per_name_cap if not long_only else 0.0,
                                  upper=per_name_cap)
        w = w.where(P[s].notna(), 0.0).fillna(0.0)
        W[s] = w
    W = pd.DataFrame(W)
    W = W.div(n_avail.clip(lower=1), axis=0)          # budget 1.0 across listed coins
    wc = E.cap_leverage(W, max_lev=1.0)
    r = (wc * R.fillna(0.0)).sum(axis=1)
    to = E.cost_turnover(wc, bps)
    net = (r - to).dropna()
    # warmup: only after >=3 coins listed and >=window
    ok = (n_avail >= 3) & (np.arange(len(net.index)) >= 0)
    net = net[net.index >= P.dropna(how='all').index[0] + pd.Timedelta(days=window)]
    return wc, net, P, R
