"""E2_eventcal shared lib: calendar-event books, T+1, 6bps/side, gates, decorrelation."""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
import harness.data as D

FRED = D.FRED
COST = 6.0
BLEND = "/Users/daxu/software/world-trader/campaign/results/GOAL100_CHAMPION_BALANCED_daily.csv"

def spy_close():
    early = pd.read_csv(f"{FRED}/spy_early.csv", index_col=0, parse_dates=True)["value"]
    late = D.closes()["SPY"].dropna()
    late = late[late.index > early.index.max()]
    s = pd.concat([early, late]).sort_index()
    return s[~s.index.duplicated(keep="last")]

def spy_ret():
    return spy_close().pct_change().dropna()

def nth_weekday(y, m, wd, n):
    d = pd.Timestamp(y, m, 1)
    return d + pd.Timedelta(days=((wd - d.dayofweek) % 7) + 7 * (n - 1))

def last_weekday(y, m, wd):
    if m == 12: nxt = pd.Timestamp(y + 1, 1, 1)
    else: nxt = pd.Timestamp(y, m + 1, 1)
    d = nxt - pd.Timedelta(days=1)
    return d - pd.Timedelta(days=((d.dayofweek - wd) % 7))

def all_weekdays(idx):
    return idx

def book_net(pos_earn: pd.Series, ret: pd.Series, cost_bps: float = COST):
    """pos_earn indexed by EARNING day t (calendar-known in advance => no lookahead;
    position for day t was set at close t-1). net_t = pos_t*ret_t - |pos_t-pos_{t-1}|*cost."""
    p = pos_earn.reindex(ret.index).fillna(0.0)
    gross = p * ret
    dpos = p.diff().abs().fillna(p.abs().iloc[0])
    return gross - dpos * cost_bps / 1e4

def vol_target(net: pd.Series, target=0.10, min_obs=60):
    sd = net.expanding(min_periods=min_obs).std().shift(1) * np.sqrt(252)
    lev = (target / sd).clip(upper=3.0).fillna(1.0)
    return net * lev

def sharpe(r):
    r = r.dropna()
    return r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else 0.0

def full_stats(r):
    r = r.dropna()
    eq = (1 + r).cumprod(); dd = (eq / eq.cummax() - 1).min()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return dict(ann=r.mean() * 252 * 100, vol=r.std() * np.sqrt(252) * 100,
                sr=sharpe(r), mdd=dd * 100, negy=int((yr < 0).sum()),
                worst=yr.min() * 100, years=len(yr),
                yearly={int(k): round(v * 100, 1) for k, v in yr.items()})

def halves_sr(r):
    mid = r.index[len(r) // 2]
    return sharpe(r[r.index <= mid]), sharpe(r[r.index > mid])

def scramble_p(r, n=200, seed=7):
    """Circular-shift scramble (shifts multiples of 5 (weekday-preserving) and 21 days).
    p = fraction of scrambles with SR >= real."""
    rng = np.random.default_rng(seed)
    vals = r.dropna().values; real = sharpe(r)
    cnt = 0; n_ = len(vals)
    shifts = rng.integers(1, max(2, n_ // 5), size=n)
    for i, k in enumerate(shifts):
        s = k * 5 if i % 2 == 0 else k * 21
        if s >= n_: s = s % n_
        v = np.roll(vals, s)
        sr = v.mean() / v.std() * np.sqrt(252)
        if sr >= real: cnt += 1
    return cnt / n_

_blend_cache = None
def blend_ret():
    global _blend_cache
    if _blend_cache is None:
        b = pd.read_csv(BLEND, index_col=0, parse_dates=True)["ret"]
        _blend_cache = b
    return _blend_cache

def corr_to_blend(r):
    b = blend_ret()
    df = pd.concat([r, b], axis=1, join="inner").dropna()
    if len(df) < 250: return np.nan, len(df)
    return df.corr().iloc[0, 1], len(df)

def evaluate(net, name, start=None, verbose=True):
    """Full gate battery per GOAL100 brief. net = net-of-cost daily series (pre-vol-target)."""
    if start: net = net[net.index >= pd.Timestamp(start)]
    vt = vol_target(net)
    s = full_stats(vt)
    h1, h2 = halves_sr(vt)
    pv = scramble_p(vt)
    c, nobs = corr_to_blend(vt)
    yr = vt.groupby(vt.index.year).apply(lambda x: (1 + x).prod() - 1)
    g = dict(sr10=s["sr"] >= 1.0, h1=h1 >= 0.5, h2=h2 >= 0.5,
             negy=s["negy"] <= 2 and s["worst"] > -5.0, scramble=pv < 0.05)
    res = dict(name=name, ann=round(s["ann"], 2), vol=round(s["vol"], 1), sr=round(s["sr"], 2),
               mdd=round(s["mdd"], 1), h1=round(h1, 2), h2=round(h2, 2),
               negy=s["negy"], worst=round(s["worst"], 1), years=s["years"],
               scramble_p=round(pv, 3), corr=round(c, 3), corr_n=nobs,
               gates=g, all_pass=all(g.values()), yearly=s["yearly"])
    if verbose:
        print(f"[{name}] ann={s['ann']:.2f}% vol={s['vol']:.1f}% SR={s['sr']:.2f} dd={s['mdd']:.1f}% "
              f"H1={h1:.2f} H2={h2:.2f} negYr={s['negy']} worst={s['worst']:.1f}% "
              f"scr_p={pv:.3f} corr={c:.3f}(n={nobs}) PASS={res['all_pass']}")
    return res

def save(net, vt, name, meta, agent="E2_eventcal"):
    path = f"/Users/daxu/software/world-trader/campaign/agents/{agent}/sleeves/{name}.csv"
    D.save_sleeve(vt, path, meta)
    print("SAVED", path)
    return path
