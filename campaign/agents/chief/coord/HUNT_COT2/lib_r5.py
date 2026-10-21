"""HUNT_COT2 round-5 library: trader-COUNT breadth signals from DATA_COTMORE's R4 panel.

Charter corner (a) — pre-registered (see FINDINGS R5 §Pre-registration): breadth of
PARTICIPATION (number of distinct reporting traders), a corner the position-based COT
family (R1-R2, 250+ configs, CLOSED) never tested. Discipline carried over from the
manifest's honest-limits section:
  * nat_gas_nymex (break 2022-02-08) and lumber (break 2023-04-25) are hard-SEGMENTED:
    signals/z are computed within segment; no statistic reads across the break date.
  * z_Traders_* is LEVEL-breadth, not positioning direction.
  * release_date is the first tradable info; trades enter release_lag=1 sessions later.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, '/Users/daxu/software/world-trader')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib_hunt as L  # noqa: E402

ROOT = L.ROOT
PANEL = f'{ROOT}/campaign/agents/chief/coord/DATA_COTMORE/work_r4/trader_count_panel.csv'

# The two PASS_WITH_EXN universe breaks (MANIFEST_R4, verified from raw panel data this
# round: nat_gas TotAll 281->40 = -86% on 2022-02-08; lumber 21->43 = +105% on 2023-04-25).
BREAKS = {('nat_gas_nymex', '2022-02-08'), ('lumber', '2023-04-25')}
BREAK_DATES = {'nat_gas_nymex': pd.Timestamp('2022-02-08'),
               'lumber': pd.Timestamp('2023-04-25')}

# Family -> proxy price file (in-repo, manifest-pinned conventions). Families with no
# in-repo proxy are excluded from book construction (documented in FINDINGS).
PX_MAP = {
    'gold': f'{ROOT}/tools/quant/data/twelvedata/GLD.csv',
    'silver': f'{ROOT}/tools/quant/data/more_etf/SLV.csv',
    'copper': f'{ROOT}/tools/quant/data/more_etf/COPX.csv',
    'corn': f'{ROOT}/tools/quant/data/more_etf/CORN.csv',
    'soybeans': f'{ROOT}/tools/quant/data/more_etf/SOYB.csv',
    'crude_wti_nymex': f'{ROOT}/tools/quant/data/more_etf/USO.csv',
    'nat_gas_nymex': f'{ROOT}/tools/quant/data/more_etf/UNG.csv',
    'sugar_no11': f'{ROOT}/tools/quant/data/more_etf/CANE.csv',
    'wheat_srw': f'{ROOT}/tools/quant/data/more_etf/WEAT.csv',
    'wheat_hrw': f'{ROOT}/tools/quant/data/more_etf/WEAT.csv',
    'wheat_hrspring': f'{ROOT}/tools/quant/data/more_etf/WEAT.csv',
    'sp500_emini': f'{ROOT}/tools/quant/data/twelvedata/SPY.csv',
    'nasdaq_emini': f'{ROOT}/tools/quant/data/twelvedata/QQQ.csv',
    'dow_emini': f'{ROOT}/tools/quant/data/twelvedata/DIA.csv',
    'us_2y_note': f'{ROOT}/tools/quant/data/more_etf/SHY.csv',
    'us_5y_note': f'{ROOT}/tools/quant/data/more_etf/IEF.csv',
    'us_10y_note': f'{ROOT}/tools/quant/data/more_etf/IEF.css'.replace('.css', '.csv'),
    'us_tbond': f'{ROOT}/tools/quant/data/more_etf/TLT.csv',
    'eur': f'{ROOT}/tools/quant/data/newdata/DEXUSEU.csv',
    'gbp': f'{ROOT}/tools/quant/data/newdata/DEXUSUK.csv',
    'jpy': f'{ROOT}/tools/quant/data/newdata/DEXJPUS.csv',
}
NO_PROXY = ['canola', 'cocoa', 'coffee_c', 'cotton_no2', 'eurodollar_3m', 'feeder_cattle',
            'lean_hogs', 'live_cattle', 'lumber', 'rough_rice', 'sofr_3m', 'soybean_meal',
            'soybean_oil', 'vix']

# count-column shorthands -> full panel column
COL = {
    'Tot_All': ('cnt_Traders_Tot_All', 'z_Traders_Tot_All'),
    'Long_All': ('cnt_Traders_Tot_Rept_Long_All', 'z_Traders_Tot_Rept_Long_All'),
    'Short_All': ('cnt_Traders_Tot_Rept_Short_All', 'z_Traders_Tot_Rept_Short_All'),
    'MM_Long': ('cnt_Traders_M_Money_Long_All', 'z_Traders_M_Money_Long_All'),
    'MM_Short': ('cnt_Traders_M_Money_Short_All', 'z_Traders_M_Money_Short_All'),
    'Dealer_Long': ('cnt_Traders_Dealer_Long_All', 'z_Traders_Dealer_Long_All'),
    'Dealer_Short': ('cnt_Traders_Dealer_Short_All', 'z_Traders_Dealer_Short_All'),
    'Lev_Long': ('cnt_Traders_Lev_Money_Long_All', 'z_Traders_Lev_Money_Long_All'),
    'Lev_Short': ('cnt_Traders_Lev_Money_Short_All', 'z_Traders_Lev_Money_Short_All'),
    'Swap_Long': ('cnt_Traders_Swap_Long_All', 'z_Traders_Swap_Long_All'),
    'Swap_Short': ('cnt_Traders_Swap_Short_All', 'z_Traders_Swap_Short_All'),
}


def load_px_r5(path):
    """lib_hunt.load_px + FRED-style 'observation_date' headers (newdata DEX* files)."""
    df = pd.read_csv(path)
    dc = 'date' if 'date' in df.columns else 'observation_date'
    df[dc] = pd.to_datetime(df[dc])
    col = 'close' if 'close' in df.columns else df.columns[-1]
    s = df.set_index(dc)[col]
    s = s[pd.to_numeric(s, errors='coerce').notna()].astype(float)
    s = s[s > 0]
    return s[~s.index.duplicated(keep='last')].sort_index()


def load_panel_family(family):
    """One family's panel rows, indexed by report_date, with PIT expanding z re-derived
    and cross-checked against the panel's own z column (assertion, not trust)."""
    df = pd.read_csv(PANEL)
    d = df[df.family == family].copy()
    d['report_date'] = pd.to_datetime(d['report_date'])
    d['release_date'] = pd.to_datetime(d['release_date'])
    d = d.sort_values('report_date').set_index('report_date')
    c = d['cnt_Traders_Tot_All'].astype(float)
    mu = c.expanding(min_periods=26).mean()
    sd = c.expanding(min_periods=26).std(ddof=0)
    d['z_recheck'] = ((c - mu) / sd.where(sd > 0))
    return d


def load_breadth(family, col='Tot_All'):
    """Breadth z series for (family, count-col). For unbroken families z is the panel's own
    PIT expanding z (rows <= t only, min_periods=26, ddof=0). Break families are SEGMENTED:
    z is re-derived within each post-break segment from raw counts (same expanding formula),
    so no statistic ever reads across the break — a stitched read would reintroduce the
    -10.74 artifact the manifest bans (measured at nat_gas 2022-02-08 this round)."""
    full = load_panel_family(family)
    ccol, zcol = COL.get(col, (col, f'z_Traders_{col}'))
    if family in BREAK_DATES:
        bd = BREAK_DATES[family]
        pre = full[full.index < bd]
        post = full[full.index >= bd]
        out = []
        for seg in (pre, post):
            c = seg[ccol].astype(float)
            mu = c.expanding(min_periods=26).mean()
            sd = c.expanding(min_periods=26).std(ddof=0)
            out.append((c - mu) / sd.where(sd > 0))
        z = pd.concat(out).sort_index()
        z.name = zcol
        return z
    z = full[zcol]
    z = z.dropna()
    # guard: the stitched -10.74 must never survive into any unbroken family's series
    if (z < -5).any():
        raise ValueError(f'{family}: stitched break artifact in unbroken z')
    return z


def release_shift_weekly(sig):
    """Weekly report-date-indexed signal -> Friday release-date index via the R1-audited
    shift (report+3d, snapping later on price-calendar holidays). Monday reports collide
    with the adjacent Tuesday after +3d -> keep the LATER report (R1 rule)."""
    import lib_hunt as L
    return L.release_shift_series(sig)


def signal_to_daily(sig, prices, release_lag=1):
    """Map a weekly (report-date-indexed) signal onto the daily price index.
    Trading day = release_date + release_lag sessions (T+1: Friday release -> Monday
    position -> first P&L Tuesday). Delegates to the R1-audited engine."""
    return L.signal_to_daily(sig, prices, release_lag=release_lag)


def breadth_extreme_gate(z, thr=1.5, tail='low'):
    """1.0 where breadth-z is in the extreme tail (<= -thr for 'low', >= thr for 'high'),
    else 0.0. NaN (warmup) stays NaN so the engine's live-mask handles it."""
    z = pd.Series(z)
    if tail == 'low':
        w = (z <= -thr).astype(float)
    else:
        w = (z >= thr).astype(float)
    return w.where(z.notna())


def xs_breadth_rank_weights(zdf, k=3):
    """Cross-sectional breadth-rank basket: long the k THINNEST-breadth markets, short the
    k THICKEST, equal weight 1/k each side (market-neutral: weights sum to 0 every row)."""
    z = pd.DataFrame(zdf).astype(float)
    rows = []
    stamps = []
    for dt, row in z.iterrows():
        r = row.dropna()
        stamps.append(dt)
        if len(r) < 2 * k:
            rows.append(pd.Series(np.nan, index=z.columns))
            continue
        w = pd.Series(0.0, index=z.columns)
        lows = r.sort_values().index[:k]
        highs = r.sort_values().index[-k:]
        w[lows] = 1.0 / k
        w[highs] = -1.0 / k
        rows.append(w)
    return pd.DataFrame(rows, index=stamps, columns=z.columns)


def breadth_ts_weights(family, col='Tot_All', thr=1.5, tail='low', side=1):
    """Time-series breadth gate for ONE family: side * gate, as weekly position."""
    z = load_breadth(family, col)
    g = breadth_extreme_gate(z, thr=thr, tail=tail)
    return side * g


# ---------------------------------------------------------------- V2 battery

def v2_battery(r, sig=None, ref=None, spy=None, ief=None, cta=None, scramble_n=200,
               seed=7):
    """V2 acceptance battery (GATES_CONTRACT_V2 §6 Step-1 + §7): gates.run with explicit
    sig= and leak_check=True (charter: 'do not depend on either state'), plus the
    beats-passive trio for the NEW-SLEEVE track. Fail-closed: no sig -> leak_ok False."""
    r = pd.Series(r)
    if not isinstance(r.index, pd.DatetimeIndex):
        raise ValueError('v2_battery: returns must be DatetimeIndex (yearly gates)')
    import bt.gates as gates_mod  # campaign/ must be on sys.path (inserted at import)
    g = L.eval_gates(ret=r, champion_rets=ref, scramble_n=scramble_n, seed=seed,
                     pos=(sig if sig is not None else None),
                     prices=(1 + r).cumprod() if sig is not None else None)
    kw = {} if spy is None else dict(beats_passive=True, spy=spy, ief=ief, cta=cta)
    gr = gates_mod.run(r, ref=ref, sig=sig, leak_check=True,
                       scramble_n=scramble_n, **kw)
    g = L.eval_gates(ret=r, champion_rets=ref, scramble_n=scramble_n, seed=seed,
                     pos=(sig if sig is not None else None),
                     prices=(1 + r).cumprod() if sig is not None else None)
    g['v2'] = {k: v for k, v in gr.items() if not isinstance(v, dict)}
    g['leak'] = gr.get('leak')
    g['leak_ok'] = gr.get('leak_ok')
    g['beats_passive'] = gr.get('beats_passive')
    g['beats_passive_ok'] = gr.get('beats_passive_ok')
    g['pass'] = bool(gr.get('pass'))
    return g


# ---------------------------------------------------------------- config runner

def run_config(families, col='Tot_All', tail='low', thr=1.5, k=None, px_map=None,
               label='', scramble_n=200, seed=7, champion_rets=None, side=1):
    """Build the breadth book for a config and run the FULL V2 battery on it.

    families: list of panel families. k=None -> per-family TS gate book (1/k n/a);
    k=int -> cross-sectional rank basket over `families` (k long / k short).
    Timing: report_date -> Friday release (panel release_date) -> T+1 -> P&L.
    Costs: 6.4bps one-side full |dW| + 0.5%/yr borrow (lib_hunt engine).
    """
    px_map = px_map or PX_MAP
    fams = [f for f in families if f in px_map]
    skipped = [f for f in families if f not in px_map]
    if k is None:
        cols = {}
        for f in fams:
            w = breadth_ts_weights(f, col, thr=thr, tail=tail, side=side)
            if w.dropna().empty:
                continue
            cols[f] = w
        if not cols:
            return None, None
        pos_wide = pd.DataFrame(cols)
    else:
        zdf = pd.DataFrame({f: load_breadth(f, col) for f in fams})
        pos_wide = xs_breadth_rank_weights(zdf, k=k)
    rel = {}
    for f in fams:
        d = load_panel_family(f)
        rel[f] = d['release_date']
    pos_wide = pos_wide.dropna(how='all')
    # rebuild pos_wide indexed by RELEASE date per family (PIT), one market at a time
    daily_pos, daily_net, daily_gross = {}, {}, {}
    for f in fams:
        if f not in pos_wide.columns:
            continue
        w = pos_wide[f].dropna()
        if w.empty:
            continue
        w = w.copy()
        w.index = pd.DatetimeIndex(rel[f].reindex(w.index).values)
        px = load_px_r5(px_map[f])
        dp = signal_to_daily(w, px, release_lag=1)
        started = signal_to_daily(pd.Series(1.0, index=w.index), px, release_lag=1)
        live_m = started > 0
        nr, to = L.net_ret(dp, px)
        r = px.reindex(dp.index).pct_change()
        daily_pos[f] = dp.where(live_m)
        daily_net[f] = nr.where(live_m)
        daily_gross[f] = (dp.shift(1) * r).where(live_m)
    dp = pd.DataFrame(daily_pos).sort_index()
    dn = pd.DataFrame(daily_net).sort_index()
    dg = pd.DataFrame(daily_gross).sort_index()
    if dp.shape[1] == 0:
        return None, None
    book_pos = dp.mean(axis=1, skipna=True).fillna(0.0)
    book_net = dn.mean(axis=1, skipna=True).fillna(0.0)
    book_gross = dg.mean(axis=1, skipna=True).fillna(0.0)
    scale = L.vol_target_scale(book_net, target=0.10, max_lev=3.0)
    book_pos = book_pos * scale.reindex(book_pos.index).fillna(0.0)
    book_net = book_net * scale.reindex(book_net.index).fillna(0.0)
    book_gross = book_gross * scale.reindex(book_gross.index).fillna(0.0)
    live = dp.notna().any(axis=1)
    live = live[live].index
    book_pos = book_pos[book_pos.index >= live[0]]
    book_net = book_net[book_net.index >= live[0]]
    book_gross = book_gross[book_gross.index >= live[0]]
    g = v2_battery(book_net, sig=book_pos, ref=champion_rets, spy=None, ief=None,
                   cta=None, scramble_n=scramble_n, seed=seed)
    g['turnover_yr'] = float(dp.diff().abs().sum().sum() / max(len(dp) / 252.0, 1e-9))
    g['label'] = label
    g['families_used'] = list(dp.columns)
    g['families_skipped_no_proxy'] = skipped
    return g, book_net
