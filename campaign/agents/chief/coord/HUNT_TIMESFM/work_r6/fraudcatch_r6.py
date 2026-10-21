"""HUNT_TIMESFM R6 FRAUD-CATCH harness — my OWN independent engine + metrics.

Charter item (b): reproduce HUNT_COT2's AND HUNT_INTERNATIONAL2's R5 verdicts from published
artifacts with my own code. NOTHING is imported from the two target agents' modules: this
file re-implements the campaign-standard engine semantics (T+1, 6.4bps full |dW|, 0.5%/yr
borrow, trailing-only VT, SR/halves/neg-years/corr) from the contract definitions, and
cross-checks my metrics against bt.metrics (locked by tests/test_fraudcatch_r6.py).

Legs of the reproduction:
  leg1 ARTIFACT SCORING — score the targets' PUBLISHED book CSVs with my metrics.
  leg2 RAW REBUILD — rebuild headline configs from raw data with my own engine; compare
       (a) my rebuild vs their published book (correlation), and (b) my gate numbers vs
       their claimed gate numbers.
  leg3 VERDICT — does each config fail the SAME gates the target said it failed?
"""
import sys
import numpy as np
import pandas as pd

ROOT = '/Users/daxu/software/world-trader'
sys.path.insert(0, f'{ROOT}/campaign')

COST = 6.4e-4          # 6.4 bps one-side on FULL |dW|
BORROW = 0.005         # 0.5 %/yr on short notional
ANN = 252.0

CHAMPION = f'{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv'
PANEL = f'{ROOT}/campaign/agents/chief/coord/DATA_COTMORE/work_r4/trader_count_panel.csv'
NKY = f'{ROOT}/tools/quant/data/newdata/NIKKEI225.csv'
COT2_DIR = f'{ROOT}/campaign/agents/chief/coord/HUNT_COT2'
INTL2_DIR = f'{ROOT}/campaign/agents/chief/coord/HUNT_INTERNATIONAL2'

# COT2 PX_MAP, re-typed from their manifest-pinned convention (read-only reference;
# identical file paths — the mapping is part of the published spec being reproduced)
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
    'univ_5y_note': f'{ROOT}/tools/quant/data/more_etf/IEF.csv',
    'us_5y_note': f'{ROOT}/tools/quant/data/more_etf/IEF.csv',
    'us_10y_note': f'{ROOT}/tools/quant/data/more_etf/IEF.csv',
    'us_tbond': f'{ROOT}/tools/quant/data/more_etf/TLT.csv',
    'eur': f'{ROOT}/tools/quant/data/newdata/DEXUSEU.csv',
    'gbp': f'{ROOT}/tools/quant/data/newdata/DEXUSUK.csv',
    'jpy': f'{ROOT}/tools/quant/data/newdata/DEXJPUS.csv',
}
BREAK_DATES = {'nat_gas_nymex': pd.Timestamp('2022-02-08'),
               'lumber': pd.Timestamp('2023-04-25')}
COL_PREFIX = {
    'Tot_All': 'cnt_Traders_Tot_All',
    'MM_Long': 'cnt_Traders_M_Money_Long_All',
    'Dealer_Long': 'cnt_Traders_Dealer_Long_All',
}
# panel z-column name for a count shorthand (exact panel headers)
ZCOL = {'Tot_All': 'z_Traders_Tot_All',
        'MM_Long': 'z_Traders_M_Money_Long_All',
        'Dealer_Long': 'z_Traders_Dealer_Long_All'}


# ---------------------------------------------------------------- metrics (mine)

def sr(r) -> float:
    r = pd.Series(r).dropna()
    if len(r) < 2:
        return float('nan')
    s = r.std(ddof=1)
    if not np.isfinite(s) or s < 1e-12:
        return 0.0
    return float(r.mean() / s * np.sqrt(ANN))


def halves(r):
    r = pd.Series(r).dropna()
    k = len(r) // 2
    return sr(r.iloc[:k]), sr(r.iloc[k:])


def neg_years(r):
    r = pd.Series(r).dropna()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod(min_count=1) - 1)
    yr = yr.where(np.isfinite(yr), -1.0)   # fail-closed, matches bt.metrics
    neg = int((yr < 0).sum())
    return neg, (float(yr.min()) if len(yr) else float('nan'))


def ann_geo(r) -> float:
    r = pd.Series(r).dropna()
    prod = (1 + r).prod(min_count=1)
    if not np.isfinite(prod) or prod <= 0:
        return float('nan')
    return float(prod ** (ANN / len(r)) - 1)


def corr_to_champion(r) -> float:
    c = pd.read_csv(CHAMPION, index_col=0, parse_dates=True).iloc[:, 0]
    df = pd.concat([r, c], axis=1, join='inner').dropna()
    return float(df.iloc[:, 0].corr(df.iloc[:, 1]))


def full_report(r, label='') -> dict:
    r = pd.Series(r).dropna()
    neg, worst = neg_years(r)
    h1, h2 = halves(r)
    return dict(label=label, n=int(len(r)), start=str(r.index.min().date()),
                end=str(r.index.max().date()), sr=round(sr(r), 4),
                ann_pct=round(100 * ann_geo(r), 2), h1=round(h1, 4), h2=round(h2, 4),
                neg_years=neg, worst_year_pct=round(100 * worst, 2),
                corr_champ=round(corr_to_champion(r), 4))


# ---------------------------------------------------------------- engine pieces (mine)

def vt_scale_expanding(gross: pd.DataFrame, target=0.10, window=60, cap=3.0,
                       floor=0.2) -> pd.DataFrame:
    """My re-implementation of the shared bt-engine expanding VT spec:
    scale_t = clip(target / (expanding_std(r[:t-1])*sqrt(ANN)), floor, cap); the shift is
    expressed by using returns UP TO t-1 (computed via shift inside). NaN-free output."""
    vols = gross.expanding(min_periods=window).std(ddof=1) * np.sqrt(ANN)
    scale = target / vols.replace(0.0, np.nan)
    scale = scale.where(vols > 0, 1.0)
    scale = scale.clip(upper=cap).clip(lower=floor).shift(1)
    return scale.fillna(1.0)


def vt_scale_ewm(daily_ret: pd.Series, target=0.10, halflife=63, min_periods=20,
                 max_lev=3.0) -> pd.Series:
    """lib_hunt convention (COT2): EWMA var of trailing returns, shift(1) (today excluded),
    scale = target/ann_vol clip [0, max_lev], warmup NaN -> 0.0."""
    r = pd.Series(daily_ret).sort_index()
    ewm_var = r.pow(2).ewm(halflife=halflife, min_periods=min_periods).mean().shift(1)
    ann_vol = np.sqrt(ewm_var * ANN)
    scale = (target / ann_vol).clip(upper=max_lev)
    return scale.fillna(0.0)


def net_book(W: pd.DataFrame, R: pd.DataFrame):
    """bt-engine convention (used by INTL2): effective weights We = W.shift(1);
    PnL = sum(We*R); cost 6.4bps x FULL |dWe| with entry-day charge (prev row seeded 0);
    borrow 0.5%/yr on current effective short notional. Returns (net Series, We)."""
    We = W.shift(1).fillna(0.0)
    pnl = (We * R).sum(axis=1)
    dW = We.diff().abs().sum(axis=1)
    if len(We):
        dW.iloc[0] = We.iloc[0].abs().sum()      # entry trade charged
    shorts = (-We.clip(upper=0.0)).abs().sum(axis=1)
    borrow = shorts * BORROW / ANN
    return (pnl - dW * COST - borrow).rename('net'), We


def net_book_cot2(pos: pd.Series, px: pd.Series):
    """lib_hunt convention (used by COT2 legs): pos indexed on session grid already
    (T+1 mapped upstream); gross = pos.shift(1)*ret; turnover on RAW pos diff with the
    FIRST row's entry NOT charged (diff().fillna(0)); borrow on short.shift(1).
    Returns (net Series, turnover Series)."""
    p = px.reindex(pos.index)
    ret = p.pct_change()
    gross = (pos.shift(1) * ret).fillna(0.0)
    to = pos.diff().abs().fillna(0.0)
    short_lag = (-pos).clip(lower=0.0).shift(1).fillna(0.0)
    net = gross - to * COST - short_lag * BORROW / ANN
    return net.rename('net'), to


def scramble_p(pos: pd.Series, px: pd.Series, n=200, seed=7) -> float:
    """Circular-shift null on the POSITION series (both targets' null family: preserves
    position persistence/turnover, destroys date alignment). p = P(SR_null >= SR_real)."""
    p_ = pd.Series(pos).dropna()
    pr = pd.Series(px).reindex(p_.index)
    real = sr(net_book_cot2(p_, pr)[0])
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        k = int(rng.integers(1, len(p_)))
        null_sr = sr(net_book_cot2(pd.Series(np.roll(p_.values, k), index=p_.index), pr)[0])
        if real <= null_sr:
            cnt += 1
    return (cnt + 1) / (n + 1)


def map_release_to_daily(sig: pd.Series, rel: pd.Series, px: pd.Series) -> pd.Series:
    """COT2 PIT mapping, mine: sig indexed by report_date; rel maps report_date ->
    release_date; position first appears at the FIRST PRICE SESSION STRICTLY AFTER the
    release (searchsorted right); later report wins on same-session collisions; ffill
    across sessions; 0.0 before the first entry."""
    s = pd.Series(sig.values, index=pd.DatetimeIndex(rel.reindex(sig.index).values))
    s = s.dropna()
    s = s[~s.index.duplicated(keep='last')]
    pidx = px.index
    avail = pidx.searchsorted(s.index, side='right')
    keep = avail < len(pidx)
    s2 = pd.Series(s.values[keep], index=pidx[avail[keep]])
    s2 = s2[~s2.index.duplicated(keep='last')]
    return s2.reindex(pidx.union(s2.index)).ffill().reindex(pidx).fillna(0.0)


def pit_expanding_z(cnt: pd.Series, breaks=(), min_periods=26) -> pd.Series:
    """PIT expanding z on report_date-indexed counts: mu/sd expanding, ddof=0, z NaN where
    sd==0 or warmup < min_periods. Break dates SEGMENT the computation (no statistic reads
    across a break): segments are [start,b1), [b1,b2), ..., [bk,end]."""
    cnt = pd.Series(cnt).sort_index()
    cut_points = sorted(pd.Timestamp(b) for b in breaks)
    bounds = [cnt.index.min() - pd.Timedelta(days=1)] + cut_points \
        + [cnt.index.max() + pd.Timedelta(days=1)]
    segs = []
    for lo, hi in zip(bounds[:-1], bounds[1:]):
        seg = cnt[(cnt.index >= lo) & (cnt.index < hi)]
        if seg.empty:
            continue
        mu = seg.expanding(min_periods=min_periods).mean()
        sd = seg.expanding(min_periods=min_periods).std(ddof=0)
        segs.append((seg - mu) / sd.where(sd > 0))
    z = pd.concat(segs).sort_index()
    return z[~z.index.duplicated(keep='last')]


# ---------------------------------------------------------------- INTL2 rebuild (mine)

def load_nky() -> pd.Series:
    df = pd.read_csv(NKY, index_col=0, parse_dates=True)
    s = df.iloc[:, 0].astype(float).sort_index()
    s = s[~s.index.duplicated(keep='last')]
    return s.dropna()


def rebuild_intl(name: str):
    """My MOM_*/CAL_* rebuild per the published spec: weights from NKY closes up to t
    (truncation-invariant variants for the date-based configs), bt-engine net_book, VT
    expanding on the GROSS book, trim to first live effective-weight day."""
    px = load_nky()
    ret = px.pct_change()
    idx = px.index
    if name.startswith('MOM_'):
        lb = int(name.split('_')[1].replace('LF', '').replace('LS', ''))
        mode = 'LS' if name.endswith('LS') else 'LF'
        mom = px - px.shift(lb)
        w = pd.Series(np.where(mom > 0, 1.0, 0.0), index=idx)
        if mode == 'LS':
            w[mom < 0] = -1.0
        w[mom.isna()] = 0.0
    elif name == 'CAL_SELLMAY':
        on = ~idx.month.isin([5, 6, 7, 8, 9])
        w = pd.Series(on.astype(float), index=idx)
    elif name == 'CAL_TOM_dates':
        on = (idx.day >= 28) | (idx.day <= 3)
        w = pd.Series(on.astype(float), index=idx)
    elif name == 'CAL_TOY_dates':
        on = ((idx.month == 12) & (idx.day >= 25)) | ((idx.month == 1) & (idx.day <= 5))
        w = pd.Series(on.astype(float), index=idx)
    else:
        raise ValueError(f'unhandled config {name}')
    W = w.to_frame('NKY')
    R = ret.to_frame('NKY')
    net0, We0 = net_book(W, R)
    gross = (We0['NKY'] * R['NKY'])
    s = vt_scale_expanding(gross.to_frame('g'))['g']
    We = We0.mul(s, axis=0)
    pnl = We['NKY'] * R['NKY']
    dW = We['NKY'].diff().abs()
    dW.iloc[0] = We['NKY'].iloc[0]
    shorts = (-We['NKY'].clip(upper=0)).abs()
    net = (pnl - dW * COST - shorts * BORROW / ANN).rename('net')
    live = We != 0
    first = live[live.any(axis=1)].index.min()
    return net[net.index >= first], We['NKY'][We.index >= first]


# ---------------------------------------------------------------- COT2 rebuild (mine)

_PANEL = None


def _panel():
    global _PANEL
    if _PANEL is None:
        zcols = sorted(ZCOL.values())
        p = pd.read_csv(PANEL, usecols=['family', 'report_date', 'release_date']
                        + list(COL_PREFIX.values()) + zcols)
        for c in ('report_date', 'release_date'):
            p[c] = pd.to_datetime(p[c])
        _PANEL = p.sort_values('report_date')
    return _PANEL


def _family_z(fam: str, col: str, d: pd.DataFrame) -> pd.Series:
    """The published spec's z source for (family, col), per lib_r5.load_breadth: BREAK
    families are ALWAYS re-derived as SEGMENTED expanding z from raw counts (the panel's
    stitched column is never read across a break); unbroken families read the panel's own
    PIT z column."""
    bd = BREAK_DATES.get(fam)
    if bd is not None:
        cc = COL_PREFIX[col]
        out = []
        for seg in (d[d.report_date < bd], d[d.report_date >= bd]):
            c = pd.Series(seg[cc].astype(float).values,
                          index=pd.DatetimeIndex(seg.report_date.values))
            mu = c.expanding(min_periods=26).mean()
            sd = c.expanding(min_periods=26).std(ddof=0)
            out.append((c - mu) / sd.where(sd > 0))
        return pd.concat(out).sort_index().dropna()
    zc = ZCOL[col]
    z = pd.Series(d[zc].astype(float).values, index=pd.DatetimeIndex(d.report_date.values))
    return z.dropna()


def rebuild_cot2(label: str):
    """My COT2 breadth rebuild for the three published configs (C1/C3/C9): z from the
    published-spec source (_family_z), tail gate on z, release->T+1 daily mapping per
    family, per-leg lib_hunt net, legs LIVE FROM FIRST RELEASE onward (gate-off days
    contribute 0.0 to the cross-leg mean and carry their exit costs), equal-weight mean
    book, EWMA VT on the NET book, trim to first live leg."""
    cfg = {'C1': ('Tot_All', 'low', 1.5), 'C3': ('Tot_All', 'low', 2.0),
           'C9': ('Dealer_Long', 'high', 1.5)}[label]
    col, tail, thr = cfg
    fin = {'eur', 'gbp', 'jpy', 'sp500_emini', 'nasdaq_emini', 'dow_emini', 'us_2y_note',
           'us_5y_note', 'us_10y_note', 'us_tbond', 'crude_wti_nymex', 'nat_gas_nymex',
           'copper', 'gold', 'silver'}
    pan = _panel()
    fams = sorted(f for f in pan.family.unique() if f in PX_MAP)
    if label == 'C9':
        fams = [f for f in fams if f in fin]
    legs, firsts = {}, {}
    for fam in fams:
        d = pan[pan.family == fam].sort_values('report_date')
        z = _family_z(fam, col, d)
        if z.empty:
            continue
        sig = (z <= -thr).astype(float) if tail == 'low' else (z >= thr).astype(float)
        if not sig.any():
            continue
        px = _load_px(PX_MAP[fam])
        rel = d.set_index('report_date')['release_date']
        daily = map_release_to_daily(sig, rel, px)
        started = map_release_to_daily(pd.Series(1.0, index=sig.index), rel, px)
        live = started > 0
        if not live.any():
            continue
        net, _ = net_book_cot2(daily, px)
        firsts[fam] = daily.index[live][0]
        legs[fam] = net.where(live)
    if not legs:
        raise RuntimeError(f'{label}: no legs built')
    dn = pd.DataFrame(legs).sort_index()
    book = dn.mean(axis=1, skipna=True).fillna(0.0)
    scale = vt_scale_ewm(book)
    book = book * scale
    first = min(firsts.values())
    return book[book.index >= first]


def _load_px(path: str) -> pd.Series:
    df = pd.read_csv(path)
    dc = 'date' if 'date' in df.columns else 'observation_date'
    df[dc] = pd.to_datetime(df[dc])
    col = 'close' if 'close' in df.columns else df.columns[-1]
    s = df.set_index(dc)[col]
    s = s[pd.to_numeric(s, errors='coerce').notna()].astype(float)
    s = s[s > 0]
    return s[~s.index.duplicated(keep='last')].sort_index()


# ---------------------------------------------------------------- scoring + compare

INTL2_CLAIMS = {  # from INTL2 FINDINGS R5 table + .meta.json files
    'MOM_252_LF': dict(sr=0.7354, h1=1.1845, h2=0.3284, negyr=22, ann=7.7),
    'MOM_63_LF': dict(sr=0.630, h1=1.21, h2=0.25, negyr=26, ann=6.2),
    'MOM_126_LF': dict(sr=0.577, h1=1.02, h2=0.25, negyr=32, ann=5.6),
    'CAL_SELLMAY': dict(sr=0.535, h1=0.96, h2=0.30, negyr=25, ann=5.4),
    'MOM_252_LS': dict(sr=0.440, h1=0.77, h2=0.19, negyr=34, ann=4.6),
    'CAL_TOM_dates': dict(sr=0.402, h1=0.84, h2=0.27, negyr=24, ann=3.9),
    'CAL_TOM_rank3': dict(sr=0.369, h1=0.95, h2=0.12, negyr=28, ann=3.4),
    'CAL_TOY_rank5': dict(sr=0.347, h1=0.87, h2=0.02, negyr=30, ann=3.1),
    'CAL_TOY_dates': dict(sr=0.267, h1=0.37, h2=0.24, negyr=31, ann=1.9),
}
COT2_CLAIMS = {  # from r5_output.log (the R5 record)
    'C1': dict(sr=0.243, h1=0.328, h2=0.214, negyr=6, ann=1.03),
    'C3': dict(sr=0.335, h1=0.296, h2=0.388, negyr=3, ann=0.81),
    'C9': dict(sr=0.590, h1=0.788, h2=0.554, negyr=3, ann=2.76),
}


def score_published_books() -> pd.DataFrame:
    """leg1: score every published book CSV with MY metrics; compare to claims."""
    rows = []
    for name, claim in INTL2_CLAIMS.items():
        f = f'{INTL2_DIR}/sleeves/INTL_R5_{name}.csv'
        r = pd.read_csv(f, index_col=0, parse_dates=True).iloc[:, 0]
        rep = full_report(r, name)
        rep.update(claimed_sr=claim['sr'], d_sr=round(rep['sr'] - claim['sr'], 4),
                   claimed_h1=claim['h1'], claimed_h2=claim['h2'],
                   d_halves=round(max(abs(rep['h1'] - claim['h1']),
                                      abs(rep['h2'] - claim['h2'])), 4),
                   claimed_negyr=claim['negyr'], negyr_match=int(rep['neg_years'] == claim['negyr']))
        rows.append(rep)
    for key, fname in [('C1', 'r5_book_C1_ts_tot_low_15.csv'),
                       ('C3', 'r5_book_C3_ts_tot_low_20.csv'),
                       ('C9', 'r5_book_C9_ts_dealerLong_high_15.csv')]:
        r = pd.read_csv(f'{COT2_DIR}/{fname}', index_col=0, parse_dates=True).iloc[:, 0]
        rep = full_report(r, f'COT2_{key}')
        claim = COT2_CLAIMS[key]
        rep.update(claimed_sr=claim['sr'], d_sr=round(rep['sr'] - claim['sr'], 4),
                   claimed_h1=claim['h1'], claimed_h2=claim['h2'],
                   d_halves=round(max(abs(rep['h1'] - claim['h1']),
                                      abs(rep['h2'] - claim['h2'])), 4),
                   claimed_negyr=claim['negyr'], negyr_match=int(rep['neg_years'] == claim['negyr']))
        rows.append(rep)
    return pd.DataFrame(rows)


def compare_rebuilds() -> pd.DataFrame:
    """leg2: my raw rebuilds vs published books (correlation + SR delta)."""
    rows = []
    for key, fname in [('C1', 'r5_book_C1_ts_tot_low_15.csv'),
                       ('C3', 'r5_book_C3_ts_tot_low_20.csv'),
                       ('C9', 'r5_book_C9_ts_dealerLong_high_15.csv')]:
        mine = rebuild_cot2(key)
        pub = pd.read_csv(f'{COT2_DIR}/{fname}', index_col=0, parse_dates=True).iloc[:, 0]
        j = pd.concat([mine, pub], axis=1, join='inner').dropna()
        cov = len(j) / max(len(pub), 1)
        rows.append(dict(config=f'COT2_{key}', n_pub=len(pub), n_mine=int(len(mine)),
                         overlap=int(len(j)), overlap_frac=round(cov, 3),
                         corr=round(float(j.iloc[:, 0].corr(j.iloc[:, 1])), 4),
                         sr_pub=round(sr(pub), 4), sr_mine=round(sr(mine), 4),
                         d_sr=round(sr(mine) - sr(pub), 4),
                         start_mine=str(mine.index.min().date()),
                         start_pub=str(pub.index.min().date())))
    for name in ['MOM_252_LF', 'CAL_SELLMAY', 'CAL_TOM_dates', 'CAL_TOY_dates']:
        mine, _ = rebuild_intl(name)
        pub = pd.read_csv(f'{INTL2_DIR}/sleeves/INTL_R5_{name}.csv',
                          index_col=0, parse_dates=True).iloc[:, 0]
        j = pd.concat([mine, pub], axis=1, join='inner').dropna()
        cov = len(j) / max(len(pub), 1)
        rows.append(dict(config=f'INTL2_{name}', n_pub=len(pub), n_mine=int(len(mine)),
                         overlap=int(len(j)), overlap_frac=round(cov, 3),
                         corr=round(float(j.iloc[:, 0].corr(j.iloc[:, 1])), 4),
                         sr_pub=round(sr(pub), 4), sr_mine=round(sr(mine), 4),
                         d_sr=round(sr(mine) - sr(pub), 4),
                         start_mine=str(mine.index.min().date()),
                         start_pub=str(pub.index.min().date())))
    return pd.DataFrame(rows)
