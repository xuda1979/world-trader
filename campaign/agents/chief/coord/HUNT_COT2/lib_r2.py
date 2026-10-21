"""HUNT_COT2 round-2 library: matched-horizon holds (4/8/13wk), TFF dealer/lev-money, CIT
index-trader fade, and a champion-regime overlay. Reuses lib_hunt's timing/cost/gate engine
(21 green round-1 tests) unchanged."""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_COT2')
import numpy as np, pandas as pd
import lib_hunt as L

ROOT = L.ROOT
COTDIR = L.COTDIR

# ---------------- round-2 datasets ----------------

# (b) TFF: dealer extreme-short fade + lev-money crowding follow, across financial futures
# with a tradeable price proxy in-repo. 13 TFF families exist; VIX has no shortable proxy
# (index, not ETF) and eurodollar/SOFR have no on-repo proxy -> excluded (documented).
TFF_BASKET = [
    ('sp500_emini', 'SPY'),
    ('nasdaq_emini', 'QQQ'),
    ('dow_emini', 'DIA'),
    ('us_2y_note', 'SHY'),
    ('us_5y_note', 'IEF'),
    ('us_10y_note', 'IEF'),
    ('us_tbond', 'TLT'),
    ('eur', 'EUR_USD'),
    ('gbp', 'GBP_USD'),
    ('jpy', 'JPY_PROXY'),
]
TFF_PX = {
    'sp500_emini': f'{ROOT}/tools/quant/data/twelvedata/SPY.csv',
    'nasdaq_emini': f'{ROOT}/tools/quant/data/twelvedata/QQQ.csv',
    'dow_emini': f'{ROOT}/tools/quant/data/twelvedata/DIA.csv',
    'us_2y_note': f'{ROOT}/tools/quant/data/more_etf/SHY.csv',
    'us_5y_note': f'{ROOT}/tools/quant/data/more_etf/IEF.csv',
    'us_10y_note': f'{ROOT}/tools/quant/data/more_etf/IEF.csv',
    'us_tbond': f'{ROOT}/tools/quant/data/more_etf/TLT.csv',
    'eur': f'{ROOT}/tools/quant/data/newdata/DEXUSEU.csv',
    'gbp': f'{ROOT}/tools/quant/data/newdata/DEXUSUK.csv',
    'jpy': f'{ROOT}/tools/quant/data/more_cot/_jpy_proxy.csv',
    '_raw_dexjpus': f'{ROOT}/tools/quant/data/newdata/DEXJPUS.csv',
    '_raw_dexuseu': f'{ROOT}/tools/quant/data/newdata/DEXUSEU.csv',
    '_raw_dexusuk': f'{ROOT}/tools/quant/data/newdata/DEXUSUK.csv',
}

# (c) CIT: 13 cit_* files exist; only these families have a tradeable proxy in-repo
# (softs cattle/coffee/cocoa/cotton/hogs/soybean oil/meal/HRW wheat have none -> excluded).
CIT_BASKET = ['corn', 'soybeans', 'sugar_no11', 'wheat_srw']
CIT_PX = {
    'corn': L.PX9['corn'], 'soybeans': L.PX9['soybeans'],
    'sugar_no11': L.PX9['sugar'], 'wheat_srw': L.PX9['wheat'],
}


def load_tff(market, category):
    df = pd.read_csv(f'{COTDIR}/tff_{market}_{category}.csv', parse_dates=['date'])
    df = df.rename(columns={'open_interest': 'oi'})
    return df.set_index('date').sort_index()


def load_cit(market):
    df = pd.read_csv(f'{COTDIR}/cit_{market}.csv', parse_dates=['date'])
    return df.set_index('date').sort_index()


def load_px_fred(path):
    """FRED newdata CSVs: observation_date,<SERIES_ID>. Returns clean close series."""
    df = pd.read_csv(path, parse_dates=['observation_date'])
    s = df.set_index('observation_date').iloc[:, 0]
    s = s[s > 0]
    return s[~s.index.duplicated(keep='last')].sort_index()


# FRED newdata CSVs are observation_date,<SERIES> (load_px_fred); everything else is date,close/value
_FRED_KEYS = {'eur', 'gbp', '_raw_dexuseu', '_raw_dexusuk', '_raw_dexjpus'}


def px_loader(market):
    """Unified price accessor for TFF_PX entries: FRED-style vs ohlc/value csv.
    Routing must be by explicit key set, NOT substring ('eur' points at a FRED file but
    contains no '_raw_dex' substring)."""
    if market in _FRED_KEYS:
        return load_px_fred(TFF_PX[market])
    return L.load_px(TFF_PX[market])


def build_jpy_proxy(path=None):
    """CME yen futures are quoted USD per JPY; DEXJPUS is yen per USD -> proxy = 1/DEXJPUS.
    Written once to more_cot/_jpy_proxy.csv so the loader path is uniform."""
    raw = load_px_fred(TFF_PX['_raw_dexjpus'])
    s = pd.Series(1.0 / raw.values, index=raw.index)
    s = s[s > 0]
    s = s[~s.index.duplicated(keep='last')].sort_index()
    if path is None:
        path = TFF_PX['jpy']
    pd.DataFrame({'date': s.index, 'value': s.values}).to_csv(path, index=False)
    return s


def ensure_jpy_proxy():
    import os
    if not os.path.exists(TFF_PX['jpy']):
        build_jpy_proxy()
    return TFF_PX['jpy']


# ---------------- (a) horizon matching ----------------

def weekly_hold(pos_wide, hold_weeks):
    """Downsample a weekly report-date position panel to every hold_weeks-th report, then
    forward-fill so each held position persists for exactly hold_weeks weeks (rebalance only
    on update weeks -> turnover/costs scale 1/hold). Index (report dates) is preserved."""
    if hold_weeks <= 1:
        return pos_wide.copy()
    upd = pos_wide.index[::hold_weeks]
    held = pos_wide.loc[upd]
    return held.reindex(pos_wide.index).ffill().fillna(0.0)


# ---------------- (d) champion regime overlay ----------------

def overlay_scale_daily(crowd_weekly, daily_index, mode='scale', extreme_hi=0.85, cut=0.5,
                        extreme_lo=None, floor=-1.0):
    """Map a weekly aggregate spec-crowding series (in [0,1] percentile space) to a DAILY
    exposure scale applied with the SAME clean release chain as everything else:
    report Tue -> +3d release -> position changeable at the NEXT session close.
    mode='scale': crowding > extreme_hi -> exposure cut to `cut` (de-crowd tilt).
    mode='flip' : crowding > extreme_hi -> exposure inverted (-1) (fade the crowd).
    Sessions before the first available release -> 1.0 (neutral: no info yet)."""
    if extreme_lo is None:
        extreme_lo = 1.0 - extreme_hi
    rel = L.release_shift_series(crowd_weekly.rename('c'))
    s = rel.copy()
    if mode == 'scale':
        s = pd.Series(np.where(s.values > extreme_hi, cut, 1.0), index=s.index)
    elif mode == 'flip':
        s = pd.Series(np.where(s.values > extreme_hi, -1.0, 1.0), index=s.index)
    else:
        raise ValueError(mode)
    unit = pd.Series(1.0, index=daily_index)
    held = L.signal_to_daily(s, unit, release_lag=1)
    # signal_to_daily fillna(0) marks pre-first-release sessions; neutral there must be 1.0 —
    # but ONLY there: cut=0.0 is a legal in-sample scale (go flat on extreme crowding) and the
    # old blanket replace(0->1) silently undid it.
    started = L.signal_to_daily(pd.Series(1.0, index=rel.index), unit, release_lag=1)
    return held.where(started > 0, 1.0)


def champion_overlay(champ_ret, crowd_weekly, mode='scale', extreme_hi=0.85, cut=0.5):
    """Scale champion daily returns by the overlay scale (same dates). Returns the overlaid
    return series (gross overlay application; cost of the extra turnover is charged by the
    caller if it rebalances positions -- here scaling a return stream only)."""
    scale = overlay_scale_daily(crowd_weekly, champ_ret.index, mode=mode, extreme_hi=extreme_hi, cut=cut)
    return champ_ret * scale.reindex(champ_ret.index).fillna(1.0)


# ---------------- generic book backtest (any market set) ----------------

def book_backtest_generic(pos_wide, px_map, vt=True, champion_rets=None, label='',
                          scramble_n=200, seed=7, release_lag=1):
    """pos_wide: [report_date x market] weekly target weights -> lib_hunt daily engine.
    px_map: market -> price csv path (or callables). Same timing/costs/gates as round 1."""
    daily_pos, daily_net, daily_gross = {}, {}, {}
    for m in pos_wide.columns:
        src = px_map[m]
        if isinstance(src, pd.Series):
            px = src.sort_index()          # in-memory series (tests) — no disk round-trip
        else:
            px = src() if callable(src) else L.load_px(src)
        col = pos_wide[m].dropna()
        if col.empty:
            continue
        rel = L.release_shift_series(col)
        dp = L.signal_to_daily(rel, px, release_lag=release_lag)
        # signal_to_daily fillna(0)s every pre-signal session, so a market whose price history
        # predates its first release (gbp/jpy 1971 vs TFF 2010) would otherwise inject decades of
        # fake-flat 0 positions: SR diluted ~sqrt(live/total) and sr_h1 pinned to exactly 0.00.
        # `started` is 1.0 from the first tradable session onward -> mask pre-signal to NaN.
        started = L.signal_to_daily(pd.Series(1.0, index=rel.index), px, release_lag=release_lag)
        live_m = started > 0
        nr, to = L.net_ret(dp, px)
        r = px.reindex(dp.index).pct_change()
        daily_pos[m] = dp.where(live_m)
        daily_net[m] = nr.where(live_m)
        daily_gross[m] = (dp.shift(1) * r).where(live_m)
    dp = pd.DataFrame(daily_pos).sort_index()
    dn = pd.DataFrame(daily_net).sort_index()
    dg = pd.DataFrame(daily_gross).sort_index()
    if dp.shape[1] == 0:
        return None, None
    book_pos = dp.mean(axis=1, skipna=True).fillna(0.0)
    book_net = dn.mean(axis=1, skipna=True).fillna(0.0)
    book_gross = dg.mean(axis=1, skipna=True).fillna(0.0)
    if vt:
        scale = L.vol_target_scale(book_net, target=0.10, max_lev=3.0)
        book_pos = book_pos * scale.reindex(book_pos.index).fillna(0.0)
        book_net = book_net * scale.reindex(book_net.index).fillna(0.0)
        book_gross = book_gross * scale.reindex(book_gross.index).fillna(0.0)
    live = dp.notna().any(axis=1)
    live = live[live].index
    book_pos, book_net = book_pos[book_pos.index >= live[0]], book_net[book_net.index >= live[0]]
    book_gross = book_gross[book_gross.index >= live[0]]
    g = L.eval_gates(book_net, champion_rets=champion_rets, scramble_n=scramble_n, seed=seed,
                     pos=book_pos, prices=(1 + book_gross).cumprod())
    g['turnover_yr'] = float(dp.diff().abs().sum().sum() / max(len(dp) / 252.0, 1e-9))
    g['label'] = label
    return g, book_net


# ---------------- aggregate crowding + overlay null ----------------

def crowd_percentile(agg, window=104):
    """Time-series percentile of an aggregate crowding level within a TRAILING window that
    EXCLUDES today (shift(1)) -> [0,1] regime indicator, NaN until the window is full.
    agg: weekly series indexed by REPORT date."""
    s = pd.Series(agg).dropna().sort_index()
    v = s.values
    out = np.full(len(v), np.nan)
    for i in range(window, len(v)):
        w = v[i - window:i]              # the `window` observations STRICTLY BEFORE i
        out[i] = float(np.mean(w < v[i]))
    return pd.Series(out, index=s.index, name='crowd_pct')


def overlay_scramble_pvalue(champ_ret, crowd_weekly, mode='scale', extreme_hi=0.85, cut=0.5,
                            n=200, seed=7):
    """Null for the champion-regime overlay: CIRCULAR SHIFT of the weekly crowd series against
    champion returns, rebuilding the overlay each draw. Preserves crowd persistence/autocorrelation
    and the overlay's exact scale path length, destroys date alignment -> null SR distribution.
    The overlaid SR must exceed the null's 95th pctile (p<0.05) to claim the regime is real.
    Also honest in reverse: an uncorrelated champion + random-looking crowd FAILS this gate."""
    champ = pd.Series(champ_ret).dropna()
    s = pd.Series(crowd_weekly).dropna().sort_index()
    overlaid = champ * overlay_scale_daily(s, champ.index, mode=mode,
                                           extreme_hi=extreme_hi, cut=cut).reindex(champ.index).fillna(1.0)
    real = L._sr(overlaid)
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        k = int(rng.integers(1, len(s)))
        ns = pd.Series(np.roll(s.values, k), index=s.index)
        ov = champ * overlay_scale_daily(ns, champ.index, mode=mode,
                                         extreme_hi=extreme_hi, cut=cut).reindex(champ.index).fillna(1.0)
        if real <= L._sr(ov): cnt += 1
    return (cnt + 1) / (n + 1)
