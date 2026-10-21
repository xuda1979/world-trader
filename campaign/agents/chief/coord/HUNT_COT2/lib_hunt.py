"""HUNT_COT2 round-1 library: clean-forward COT loaders, timing, costs (6.4bps full |dW| + 0.5%/yr borrow)."""
import sys, os, glob, csv, io, zipfile
sys.path.insert(0, '/Users/daxu/software/world-trader')
import numpy as np, pandas as pd

ROOT = '/Users/daxu/software/world-trader'
COTDIR = f'{ROOT}/tools/quant/data/more_cot'
RAW = f'{COTDIR}/_raw'
COST = 6.4e-4          # one-side on FULL |dW| traded notional (TRADE_RECORD_STANDARD)
BORROW = 0.005         # 0.5%/yr on short notional

# 9 charter markets -> price proxies (charter lines 16-19)
MARKETS9 = ['gold','silver','copper','corn','soybeans','nat_gas_nymex','wti','sugar','wheat']
COTFILE = {'wti':'crude_wti_nymex', 'sugar':'sugar_no11', 'wheat':'wheat_srw'}  # family names
PX9 = {'gold': f'{ROOT}/tools/quant/data/twelvedata/GLD.csv',
       'silver': f'{ROOT}/tools/quant/data/more_etf/SLV.csv',
       'copper': f'{ROOT}/tools/quant/hedge_fund_strats/data_fred/copx.csv',
       'corn': f'{ROOT}/tools/quant/data/more_etf/CORN.csv',
       'soybeans': f'{ROOT}/tools/quant/data/more_etf/SOYB.csv',
       'nat_gas_nymex': f'{ROOT}/tools/quant/data/more_etf/UNG.csv',
       'wti': f'{ROOT}/tools/quant/data/more_etf/USO.csv',
       'sugar': f'{ROOT}/tools/quant/data/more_etf/CANE.csv',
       'wheat': f'{ROOT}/tools/quant/data/more_etf/WEAT.csv'}

def fam(market):
    return COTFILE.get(market, market)

def load_cot(market):
    df = pd.read_csv(f'{COTDIR}/{fam(market)}_cot.csv', parse_dates=['date'])
    return df.set_index('date').sort_index()

def _parse_disagg_zip(zp):
    """Parse a disagg zip -> list of rows (market, report_date, oi, mmL, mmS, pmL, pmS, swL, swS)."""
    z = zipfile.ZipFile(zp)
    lines = z.read(z.namelist()[0]).decode('latin-1').splitlines()
    cols = next(csv.reader(io.StringIO(lines[0].lower())))
    idx = {c: i for i, c in enumerate(cols)}
    need = ['market_and_exchange_names', 'report_date_as_yyyy-mm-dd', 'open_interest_all',
            'm_money_positions_long_all', 'm_money_positions_short_all',
            'prod_merc_positions_long_all', 'prod_merc_positions_short_all',
            'swap_positions_long_all', 'swap__positions_short_all']
    if any(c not in idx for c in need):
        return []   # older format -> skip (2010+ files have all)
    out = []
    for line in lines[1:]:
        if not line.strip(): continue
        try:
            p = next(csv.reader(io.StringIO(line)))
        except csv.Error:
            continue
        if len(p) <= max(idx.values()): continue
        def g(k):
            v = p[idx[k]].replace(',', '').strip()
            return int(v) if v else 0
        try:
            out.append((p[idx['market_and_exchange_names']].strip(), p[idx['report_date_as_yyyy-mm-dd']],
                        g('open_interest_all'),
                        g('m_money_positions_long_all'), g('m_money_positions_short_all'),
                        g('prod_merc_positions_long_all'), g('prod_merc_positions_short_all'),
                        g('swap_positions_long_all'), g('swap__positions_short_all')))
        except (ValueError, IndexError):
            continue
    return out

# audited exact-name matcher from the legacy builder (repo source of truth; keyword lookalikes
# like MICRO GOLD / ICE WTI / HENRY HUB must NOT match - different contracts, different OI)
sys.path.insert(0, f'{ROOT}/tools/quant/data/more_cot')
import cot_matcher as _CM

def match_family(name):
    return _CM.match_market(name)

def load_hedger(market, cache={}):
    """Re-parse raw disagg zips -> weekly df indexed by REPORT date with mm/pm/swap nets and %OI
    for ONE charter family (exact audited market names only). Cached in-process.
    Same-date collisions resolved by cot_matcher.priority_of (e.g. physical NATGAS over HENRY HUB)."""
    key = 'ALL'
    if key not in cache:
        rows = []
        for zp in sorted(glob.glob(os.path.join(RAW, 'fut_disagg_txt_*.zip'))):
            rows.extend(_parse_disagg_zip(zp))
        df = pd.DataFrame(rows, columns=['mkt','date','oi','mmL','mmS','pmL','pmS','swL','swS'])
        df['family'] = df['mkt'].map(match_family)
        df = df[df['family'].notna()].copy()
        df['prio'] = df['mkt'].map(lambda n: _CM.priority_of(n)[0])
        df['date'] = pd.to_datetime(df['date'])
        # collision resolution identical to build_cot: lowest rule-rank wins on same family+date
        df = df.sort_values(['family','date','prio']).drop_duplicates(subset=['family','date'], keep='first')
        df = df.set_index('date').sort_index()
        for who in ['mm','pm','sw']:
            df[f'{who}_net'] = df[f'{who}L'] - df[f'{who}S']
            df[f'{who}_pct'] = df[f'{who}_net'] / df['oi']
        cache[key] = df
    return cache[key][cache[key]['family'] == fam(market)]

def load_px(path):
    df = pd.read_csv(path, parse_dates=['date'])
    col = 'close' if 'close' in df.columns else 'value'   # copx.csv (FRED-style) uses 'value'
    s = df.set_index('date')[col]
    s = s[s > 0]
    return s[~s.index.duplicated(keep='last')].sort_index()

def ls_ratio(long_pos, short_pos):
    """Scale-free long/short asymmetry L/(L+S); 0.5 = neutral (also defined at L+S==0)."""
    tot = np.asarray(long_pos, dtype=float) + np.asarray(short_pos, dtype=float)
    out = np.where(tot > 0, np.asarray(long_pos, dtype=float) / np.where(tot > 0, tot, 1.0), 0.5)
    return out if np.ndim(long_pos) > 0 or np.ndim(short_pos) > 0 else float(out)

def release_shift(report_date):
    """CFTC report date (Tuesday) -> release date (Friday, +3 calendar days) when data is first public.
    If +3d lands on a price-calendar holiday, signal_to_daily's searchsorted snaps LATER (never earlier)."""
    return pd.to_datetime(report_date) + pd.Timedelta(days=3)

def release_shift_series(sig):
    """Apply release_shift to every index date of a weekly signal series/dataframe column.
    Holiday-week reports (8 Monday reports in the 9 files) can collide with the adjacent
    Tuesday report on the same effective session after +3d snapping -> keep the LATER report."""
    s = sig.dropna()
    out = pd.Series(s.values, index=[release_shift(d) for d in s.index], name=s.name)
    return out[~out.index.duplicated(keep='last')]

def signal_to_daily(sig, prices, release_lag=1):
    """sig indexed by RELEASE date (Friday = report+3d; pass load_cot dates through release_shift).
    release_lag=1 (headline, c3-audited PIT-safe): position first set at close of the NEXT session
    after release (Monday) -> first P&L Tuesday; never any same-week overlap.
    release_lag=0 (borderline): position set at release-session close -> first P&L next session; NOT used for headline.
    Positions forward-fill across price days; gross_ret shifts pos by 1 day for P&L."""
    s = sig.sort_index().dropna()
    if len(s) == 0:
        return pd.Series(0.0, index=prices.index)
    pidx = prices.index
    pos_dates = s.index
    if release_lag > 0:
        avail = pidx.searchsorted(pos_dates, side='right')   # first session STRICTLY after release
    else:
        avail = pidx.searchsorted(pos_dates, side='left')    # first session on/after release
    keep = avail < len(pidx)
    s2 = pd.Series(s.values[keep], index=pidx[avail[keep]])
    # several pre-price-history releases can snap to the SAME first session (searchsorted right=0);
    # PIT convention: the LATEST report wins at that session (newest info at first tradable close)
    s2 = s2[~s2.index.duplicated(keep='last')]
    daily = s2.reindex(pidx.union(s2.index)).ffill().reindex(pidx).fillna(0.0)
    return daily

def gross_ret(pos, prices):
    p = prices.reindex(pos.index)
    ret = p.pct_change()
    return (pos.shift(1) * ret).fillna(0.0)   # pos set at close(t) earns t->t+1: NO lookahead; row0 NaN -> 0

def net_ret(pos, prices, cost=COST, borrow=BORROW):
    to = pos.diff().abs().fillna(0.0)  # one-side turnover on FULL |dW|
    gross = gross_ret(pos, prices)
    short_notional = (-pos).clip(lower=0.0)
    fee = to * cost + short_notional.shift(1).fillna(0.0) * borrow / 252.0
    return gross - fee, to

# ---------- charter aggregates (a)-(d) ----------

WEEKS_PER_YEAR = 52

def _frame(x, index=None, columns=None):
    if isinstance(x, pd.Series):
        return x.to_frame(x.name or 'v')
    return pd.DataFrame(x, index=index, columns=columns)

def cross_market_rank_positions(mm_pct, oi, k=3):
    """(a) CROSS-MARKET COT: each report week, rank spec net %OI ACROSS the 9 markets;
    LONG the k most-crowded-SHORT markets (most negative spec net %OI), SHORT the k
    most-crowded-LONG markets (most positive), equal weight 1/k each leg, self-exclusive.
    mm_pct: DataFrame [report_date x market] of spec net %OI; oi same shape (used for
    tie-break robustness, not weighting). Returns DataFrame of positions same shape."""
    mm = pd.DataFrame(mm_pct)
    n = mm.shape[1]
    assert 2 * k <= n, f"k={k} too big for {n} markets"
    w = 1.0 / k
    ranks = mm.rank(axis=1)          # 1 = most crowded SHORT
    pos = pd.DataFrame(0.0, index=mm.index, columns=mm.columns)
    longs = ranks <= k               # most crowded short -> long (fade spec crowding)
    shorts = ranks > (n - k)         # most crowded long -> short
    pos = pos.mask(longs, w).mask(shorts, -w)
    return pos

def _zscore_frame(df, lookback, min_periods=None):
    mp = lookback if min_periods is None else min_periods
    mu = df.rolling(lookback, min_periods=mp).mean().shift(1)   # trailing-only: excludes today
    sd = df.rolling(lookback, min_periods=mp).std().shift(1)
    return (df - mu) / sd

def hedger_fade_positions(pm_pct, lookback=12, cap=2.0):
    """(b) SWAP/COMMERCIAL fade: commercials are the smart counterparty -> LONG markets where
    hedgers are crowded SHORT (low pm_pct z), SHORT where crowded LONG. Position = -z/cap
    clipped to [-1, 1]; z from trailing-only window (excludes current obs)."""
    z = _zscore_frame(pm_pct, lookback)
    return (-z / cap).clip(-1.0, 1.0).fillna(0.0)

def oi_change_overlay(oi, lookback=8):
    """(c) OI-change regime overlay in [0,1]: growth of open interest (new-money conviction)
    scales exposure; flat/falling OI -> 0. growth = oi / oi.shift(lookback) - 1 (trailing).
    Normalizer is the trailing mean growth, VALID ONLY when positive (a negative mean with
    negative growth would otherwise produce a spurious positive ratio)."""
    growth = (oi / oi.shift(lookback) - 1.0)
    denom = growth.rolling(52, min_periods=13).mean().shift(1)
    ov = (growth / denom.where(denom > 0)).clip(lower=0.0)
    return ov.fillna(0.0).clip(upper=1.0)

def spec_asymmetry_positions(long_pct=None, short_pct=None, lookback=12, cap=2.0, net_pct=None, oi=None):
    """(d) spec LONG vs SHORT asymmetry: L/(L+S) ratio (scale-free, 0.5 neutral) is NOT the same
    as net %OI once gross positioning varies; fade high-L-share crowding. Raises on net-only
    input (net == L_pct - S_pct is mathematically identical to the already-dead net signal)."""
    if long_pct is None or short_pct is None:
        raise ValueError("need separate long_pct & short_pct (net-only input has no new information)")
    ratio = long_pct / (long_pct + short_pct)
    z = _zscore_frame(ratio, lookback)
    return (-z / cap).clip(-1.0, 1.0).fillna(0.0)

def vol_target_scale(daily_ret, target=0.10, max_lev=3.0, halflife=63):
    """(g) vol target: TRAILING-ONLY realized vol (shift(1) so today's ret excluded), EWMA,
    scale = target/ann_vol clipped to [0, max_lev]."""
    r = pd.Series(daily_ret).sort_index()
    ewm_var = r.pow(2).ewm(halflife=halflife, min_periods=20).mean().shift(1)
    ann_vol = np.sqrt(ewm_var * 252.0)
    scale = (target / ann_vol).clip(upper=max_lev)
    return scale.fillna(0.0)

def _sr(r):
    r = pd.Series(r).dropna()
    if len(r) < 20 or r.std() == 0: return 0.0
    return float(r.mean() / r.std() * np.sqrt(252))

def eval_gates(ret, champion_rets=None, scramble_n=200, seed=7, pos=None, prices=None):
    """ALL GATES_CONTRACT gates on a NET daily return series. Fail-closed dict.
    Scramble gate needs the underlying (pos, prices) to build a SIGNAL-scramble null; a
    return-only series fails the gate (return permutation is not a valid null)."""
    ret = pd.Series(ret).dropna()
    years = ret.groupby(ret.index.year)
    yr_sum = years.sum()
    neg = yr_sum[yr_sum < 0]
    h1 = ret[ret.index < ret.index[len(ret)//2]]
    h2 = ret[ret.index >= ret.index[len(ret)//2]]
    g = {
        'n_days': int(len(ret)),
        'start': str(ret.index.min().date()), 'end': str(ret.index.max().date()),
        'sr_full': _sr(ret),
        'ann_ret': float(ret.mean() * 252),
        'ann_vol': float(ret.std() * np.sqrt(252)),
        'mdd': float((ret.cumsum() - ret.cumsum().cummax()).min()) if len(ret) else 0.0,
        'neg_years': int(len(neg)),
        'neg_years_gt5pct': int((neg < -0.05).sum()),
        'sr_h1': _sr(h1), 'sr_h2': _sr(h2),
        'pass_halves': bool(_sr(h1) >= 0.5 and _sr(h2) >= 0.5),
        'pass_yearly': bool(len(neg) <= 2 and (neg > -0.05).all() if len(neg) else True),
    }
    g['pass_sr'] = bool(g['sr_full'] >= 1.0)
    if pos is not None and prices is not None:
        g['scramble_p'] = scramble_pvalue(pos, prices, n=scramble_n, seed=seed)
        g['pass_scramble'] = bool(g['scramble_p'] < 0.05)
    else:
        # fail-closed: a return-only series CANNOT support a signal-scramble null (any permutation
        # of returns preserves mean & std exactly -> SR identical -> p degenerate). Gate FAILS.
        g['scramble_p'] = float('nan')
        g['pass_scramble'] = False
        g['scramble_note'] = 'no signal provided -> fail-closed'
    g['pass_all'] = bool(g['pass_sr'] and g['pass_halves'] and g['pass_yearly'] and g['pass_scramble'])
    if champion_rets is not None:
        ch = pd.Series(champion_rets).dropna()
        j = pd.concat([ret, ch], axis=1, join='inner').dropna()
        c = float(j.iloc[:, 0].corr(j.iloc[:, 1])) if len(j) > 30 else float('nan')
        g['corr_champ'] = c
        g['pass_corr'] = bool(abs(c) < 0.15)          # 0.15-0.35 -> corr_ok_secondary
        g['corr_ok_secondary'] = bool(0.15 <= abs(c) < 0.35)
    return g

def scramble_pvalue(pos, prices, n=200, seed=7):
    """Signal-scramble null: CIRCULAR SHIFT of the daily POSITION series against the price series.
    Preserves position persistence (turnover/cost structure realistic) while destroying the
    date alignment between signal and returns -> null SR distribution.
    Real net SR must exceed the null's 95th pctile (p<0.05) to pass.
    NOTE: a return-only permutation would be degenerate (mean/std preserved exactly -> null SR
    identical to real SR -> p==1 always); the POSITION series is what must be scrambled."""
    p = pd.Series(pos).dropna()
    pr = pd.Series(prices).reindex(p.index)
    real = _sr(net_ret(p, pr)[0])
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        k = int(rng.integers(1, len(p)))
        null_sr = _sr(net_ret(pd.Series(np.roll(p.values, k), index=p.index), pr)[0])
        if real <= null_sr: cnt += 1
    return (cnt + 1) / (n + 1)
