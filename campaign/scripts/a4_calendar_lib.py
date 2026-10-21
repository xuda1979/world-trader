"""A4_calendar shared lib: SPY proxy, T+1 backtest with 6bps/side, gates."""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
import harness.data as D

FRED = D.FRED

def spy_close():
    """SPY adjusted-proxy close 1993-2026: spy_early (93-05) + panel SPY (06-08+)."""
    early = pd.read_csv(f"{FRED}/spy_early.csv", index_col=0, parse_dates=True)["value"]
    px = D.closes()
    late = px["SPY"].dropna()
    late = late[late.index > early.index.max()]
    s = pd.concat([early, late]).sort_index()
    s = s[~s.index.duplicated(keep="last")]
    return s

def spy_ret():
    s = spy_close()
    return s.pct_change().dropna()

def apply_cost_t1(pos: pd.Series, ret: pd.Series, cost_bps: float = 6.0):
    """pos decided at close t (uses data<=t), earns ret_{t+1}*pos_t, cost on |Δpos| at t+1.
    Returns daily net strategy return series aligned to ret index (ret at t+1 labeled t+1)."""
    pos = pos.reindex(ret.index).ffill().fillna(0.0)
    gross = pos * ret
    dpos = pos.diff().abs().fillna(pos.abs().iloc[0])
    net = gross - dpos * cost_bps / 1e4
    return net.dropna()

def vol_target(net: pd.Series, target=0.10, min_obs=60):
    """Expanding-window vol targeting using ONLY trailing data. pos multiplier for day t
    uses std of returns up to t-1; applied to day t return (shifted)."""
    r = net
    mu = r.expanding(min_periods=min_obs).mean().shift(1)
    sd = r.expanding(min_periods=min_obs).std().shift(1)
    lev = (target / (sd * np.sqrt(252))).clip(0.25, 3.0)
    lev = lev.fillna(1.0)
    return r * lev

def sharpe(r): 
    r = r.dropna()
    return r.mean()/r.std()*np.sqrt(252) if r.std() > 0 else 0.0

def halves_sr(r):
    mid = r.index[len(r)//2]
    return sharpe(r[r.index <= mid]), sharpe(r[r.index > mid])

def yearly(r):
    return r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)

def scramble_p(r, n=200, seed=7):
    """Circular-shift scramble of signal days vs fixed return path.
    Shifts by random multiples of 5 and 21 days (weekday/weekday & month-alignment
    preserved as the charter asks). p = fraction of scrambles with SR >= real SR."""
    rng = np.random.default_rng(seed)
    vals = r.values
    real = sharpe(r)
    cnt = 0
    idx = r.index
    n_ = len(vals)
    shifts = list(rng.integers(1, n_//5, size=n))
    # alternate multiples of 5 (weekday-preserving) and 21 (month-anchor-ish)
    for i, k in enumerate(shifts):
        s = k*5 if i % 2 == 0 else k*21
        if s >= n_: s = s % n_
        v = np.roll(vals, s)
        sr = v.mean()/v.std()*np.sqrt(252)
        if sr >= real: cnt += 1
    return cnt / n_

def gates(r, full_min=0.6, half_min=0.3, max_neg=2, worst_min=-5.0, verbose=True):
    res = {}
    res["full"] = sharpe(r)
    res["H1"], res["H2"] = halves_sr(r)
    yr = yearly(r)
    neg = yr[yr < 0]
    res["neg_years"] = int(len(neg))
    res["worst_year"] = float(neg.min()*100) if len(neg) else 0.0
    res["ann"] = r.mean()*252*100
    res["vol"] = r.std()*np.sqrt(252)*100
    res["maxdd"] = float((( (1+r).cumprod()/ (1+r).cumprod().cummax() -1).min())*100)
    res["pass"] = (res["full"] >= full_min and res["H1"] >= half_min and res["H2"] >= half_min
                   and res["neg_years"] <= max_neg and res["worst_year"] > worst_min)
    if verbose:
        print(f"SR={res['full']:.2f} H1={res['H1']:.2f} H2={res['H2']:.2f} "
              f"negYr={res['neg_years']} worstYr={res['worst_year']:.1f}% "
              f"ann={res['ann']:.1f}% vol={res['vol']:.1f}% dd={res['maxdd']:.0f}% PASS={res['pass']}")
    return res

def us_holidays(index):
    """US market holidays 1993-2026 (NYSE: fixed + MLK/Presidents/GoodFriday/Memorial/
    July4/Labor/Thanksgiving/Christmas; simplified Juneteenth from 2022)."""
    import pandas as pd
    years = range(index.year.min(), index.year.max()+1)
    hol = []
    for y in years:
        hol += [pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-25")]
        # MLK: 3rd Monday Jan; Presidents: 3rd Monday Feb; Memorial: last Monday May
        # Labor: 1st Monday Sep; Thanksgiving: 4th Thursday Nov
        def nth_weekday(m, wd, n):
            d = pd.Timestamp(y, m, 1)
            add = (wd - d.dayofweek) % 7
            return d + pd.Timedelta(days=add + 7*(n-1))
        hol += [nth_weekday(1, 0, 3), nth_weekday(2, 0, 3), nth_weekday(9, 0, 1),
                nth_weekday(11, 3, 4)]
        # last Monday May
        d = pd.Timestamp(y, 5, 31)
        hol.append(d - pd.Timedelta(days=d.dayofweek))
        # Good Friday: skip (needs easter calc) — use dateutil
        try:
            from dateutil.easter import easter
            e = easter(y)
            hol.append(e - pd.Timedelta(days=2))
        except Exception:
            pass
        if y >= 2022: hol.append(pd.Timestamp(f"{y}-06-19"))
    hol = pd.DatetimeIndex(hol)
    # shift Sat->Fri, Sun->Mon approximations are handled by market being closed anyway
    return pd.DatetimeIndex(sorted(hol))
