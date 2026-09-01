import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import champion_build as cb

POOL12 = {k: v for k, v in cb.POOL.items() if k not in ("H21_f5", "H21_br", "A5r2", "A5r4")}
START = "2007-01-01"

_cache = {}
def _pool_norm():
    if "V" not in _cache:
        V, S = {}, {}
        for n, p in POOL12.items():
            r = cb.load(p)
            v, s = cb.vt(r, 0.10)
            V[n] = v; S[n] = s
        Vn = pd.DataFrame(V); Sn = pd.DataFrame(S)
        W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
        u = Vn.mean(axis=1)
        u = u[u.index >= START]
        tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1).reindex(u.index).fillna(0)
        _cache["V"] = V; _cache["u"] = u; _cache["tw"] = tw
    return _cache["u"], _cache["tw"]

def construct20(TGT, THR, cost_bps=6, FR=0.5, LB=126):
    """Returns (net_ret_series, position_multiplier s_t)."""
    u, tw = _pool_norm()
    COST = cost_bps / 10000
    b, sc_vt = cb.vt(u, TGT)
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(LB).max().shift(1)
    tdd = eq.shift(1) / rm - 1
    th = pd.Series(np.where(tdd < -THR, FR, 1.0), index=b.index)
    b = b * th
    s = sc_vt * th                      # full position multiplier
    dsc = th.diff().abs() * 0.5
    tot = tw + dsc.fillna(0)
    net = (b - tot * COST).dropna()
    return net, s.reindex(net.index).fillna(0), u.reindex(net.index).fillna(0)

def stats(r):
    return cb.stats(r)

def yearly(r):
    return r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)

def dd_series(r):
    return (1 + r).cumprod() / (1 + r).cumprod().cummax() - 1

def maxdd_in(r, a, b):
    w = r[(r.index >= a) & (r.index <= b)]
    if len(w) == 0: return np.nan
    return dd_series(w).min()
