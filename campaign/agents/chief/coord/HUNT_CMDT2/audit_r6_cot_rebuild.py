"""R6 fraud-catch audit (HUNT_CMDT2): independently rebuild HUNT_COT2's R5 trader-count
books C9 (dealerLong HIGH 1.5, 10 fin fams) and C3 (Tot_All LOW 2.0, 21 fams) from the RAW
panel with code written from the documented spec — no lib_r5/lib_hunt imports.

Spec (HUNT_COT2 FINDINGS R5 + lib_r5 docstrings):
  z     = PIT expanding (min_periods=26, ddof=0) on the raw count column; break families
          (nat_gas_nymex 2022-02-08, lumber 2023-04-25) segmented, z re-derived per segment.
  gate  = 1.0 where z >= thr (tail=high) / z <= -thr (tail=low), else 0; warmup NaN.
  timing= report_date -> panel release_date -> position at close of FIRST session STRICTLY
          after release (T+1) -> first P&L the session after that. Latest report wins dups.
  costs = 6.4e-4 one-side on FULL |dW| + 0.5%/yr borrow on short notional (shift 1).
  book  = EW mean of per-family positions/returns (skipna, fillna 0), vol target 10% ann,
          EWMA halflife 63 min_periods 20 TRAILING (shift 1), clip <= 3, leading warmup 0.
Prints: panel-z crosscheck, book max|dev| vs saved CSV, and full stat block.
"""
import numpy as np
import pandas as pd

ROOT = '/Users/daxu/software/world-trader'
PANEL = f'{ROOT}/campaign/agents/chief/coord/DATA_COTMORE/work_r4/trader_count_panel.csv'
CHAMP = f'{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv'
BOOKS = f'{ROOT}/campaign/agents/chief/coord/HUNT_COT2'
OUT = f'{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/work_r6'
import os
os.makedirs(OUT, exist_ok=True)

BREAKS = {'nat_gas_nymex': pd.Timestamp('2022-02-08'),
          'lumber': pd.Timestamp('2023-04-25')}

PX = {
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
    'us_10y_note': f'{ROOT}/tools/quant/data/more_etf/IEF.csv',
    'us_tbond': f'{ROOT}/tools/quant/data/more_etf/TLT.csv',
    'eur': f'{ROOT}/tools/quant/data/newdata/DEXUSEU.csv',
    'gbp': f'{ROOT}/tools/quant/data/newdata/DEXUSUK.csv',
    'jpy': f'{ROOT}/tools/quant/data/newdata/DEXJPUS.csv',
}
FIN = ['eur', 'gbp', 'jpy', 'sp500_emini', 'nasdaq_emini', 'dow_emini',
       'us_2y_note', 'us_5y_note', 'us_10y_note', 'us_tbond']
ALL = sorted(PX.keys())

COLNAME = {'Tot_All': ('cnt_Traders_Tot_All', 'z_Traders_Tot_All'),
           'Dealer_Long': ('cnt_Traders_Dealer_Long_All', 'z_Traders_Dealer_Long_All')}


def load_px(path):
    df = pd.read_csv(path)
    dc = 'date' if 'date' in df.columns else 'observation_date'
    df[dc] = pd.to_datetime(df[dc])
    col = 'close' if 'close' in df.columns else df.columns[-1]
    s = df.set_index(dc)[col]
    s = s[pd.to_numeric(s, errors='coerce').notna()].astype(float)
    s = s[s > 0]
    return s[~s.index.duplicated(keep='last')].sort_index()


_panel_cache = {}


def fam_frame(family):
    if family not in _panel_cache:
        df = pd.read_csv(PANEL, low_memory=False)
        df = df[df.family == family].copy()
        df['report_date'] = pd.to_datetime(df['report_date'])
        df['release_date'] = pd.to_datetime(df['release_date'])
        _panel_cache[family] = df.sort_values('report_date').set_index('report_date')
    return _panel_cache[family]


def my_z(family, ccol):
    """MY OWN expanding z from the raw count column (segmented at breaks)."""
    d = fam_frame(family)
    if family in BREAKS:
        bd = BREAKS[family]
        segs = (d[d.index < bd], d[d.index >= bd])
    else:
        segs = (d,)
    out = []
    for seg in segs:
        c = seg[ccol].astype(float)
        mu = c.expanding(min_periods=26).mean()
        sd = c.expanding(min_periods=26).std(ddof=0)
        out.append((c - mu) / sd.where(sd > 0))
    return pd.concat(out).sort_index()


def signal_to_daily(sig, px_index):
    """First session STRICTLY after each release date; latest wins dups; ffill; 0 fill."""
    s = sig.sort_index().dropna()
    avail = px_index.searchsorted(s.index, side='right')
    keep = avail < len(px_index)
    s2 = pd.Series(s.values[keep], index=px_index[avail[keep]])
    s2 = s2[~s2.index.duplicated(keep='last')]
    return s2.reindex(px_index.union(s2.index)).ffill().reindex(px_index).fillna(0.0)


def build_book(families, col, tail, thr):
    ccol, zcol = COLNAME[col]
    pos_d, net_d = {}, {}
    for f in families:
        d = fam_frame(f)
        z = my_z(f, ccol)
        if z.dropna().empty:
            print(f'  {f}: empty z -> skipped')
            continue
        # crosscheck my z vs the panel's own z column (unbroken families only)
        if f not in BREAKS:
            both = pd.concat([z, d[zcol]], axis=1, keys=['mine', 'panel']).dropna()
            dev = float((both['mine'] - both['panel']).abs().max())
            tag = 'OK' if dev < 1e-9 else f'DEV {dev:.2e}'
            print(f'  {f}: z crosscheck vs panel col max|dev|={dev:.3e} [{tag}] n={len(both)}')
        w = (z >= thr).astype(float) if tail == 'high' else (z <= -thr).astype(float)
        w = w.where(z.notna())
        rel = pd.Series(d['release_date'].reindex(w.index).values, index=w.index)
        w2 = w.copy()
        w2.index = pd.DatetimeIndex(rel.values)
        # lib_r5 convention: warmup-NaN gate rows are dropped BEFORE the live mask is
        # built, so the book starts at the first DEFINED z (not the first release).
        w2 = w2.dropna()
        px = load_px(PX[f])
        dp = signal_to_daily(w2, px.index)
        started = signal_to_daily(pd.Series(1.0, index=w2.index), px.index)
        live = started > 0
        r = px.pct_change()
        gross = (dp.shift(1) * r).fillna(0.0)
        to = dp.diff().abs().fillna(0.0)
        short = (-dp).clip(lower=0.0)
        fee = to * 6.4e-4 + short.shift(1).fillna(0.0) * 0.005 / 252.0
        nr = gross - fee
        pos_d[f] = dp.where(live)
        net_d[f] = nr.where(live)
    dp = pd.DataFrame(pos_d).sort_index()
    dn = pd.DataFrame(net_d).sort_index()
    bp = dp.mean(axis=1, skipna=True).fillna(0.0)
    bn = dn.mean(axis=1, skipna=True).fillna(0.0)
    ewm_var = bn.pow(2).ewm(halflife=63, min_periods=20).mean().shift(1)
    vol = np.sqrt(ewm_var * 252.0)
    scale = (0.10 / vol).clip(upper=3.0).fillna(0.0)
    bp = bp * scale
    bn = bn * scale
    livemask = dp.notna().any(axis=1)
    start = livemask[livemask].index[0]
    return bp[bp.index >= start], bn[bn.index >= start], list(dp.columns)


def stats(b, champ):
    b = b.dropna()
    n = len(b)
    sr = b.mean() / b.std(ddof=0) * np.sqrt(252)
    h1, h2 = b.iloc[:n // 2], b.iloc[n // 2:]
    yr = b.groupby(b.index.year).sum()
    common = b.index.intersection(champ.index)
    corr = b.reindex(common).corr(champ.reindex(common))
    return dict(n=n, start=str(b.index.min().date()), end=str(b.index.max().date()),
                SR=round(float(sr), 3), ann=round(float(b.mean() * 252 * 100), 2),
                H1=round(float(h1.mean() / h1.std(ddof=0) * np.sqrt(252)), 2),
                H2=round(float(h2.mean() / h2.std(ddof=0) * np.sqrt(252)), 2),
                negyr=int((yr < 0).sum()), worst=round(float(yr.min() * 100), 2),
                corr=round(float(corr), 4))


champ = pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']

print('=== REBUILD C9: dealerLong-count HIGH thr 1.5, 10 fin-proxy families ===')
bp9, bn9, fams9 = build_book(FIN, 'Dealer_Long', 'high', 1.5)
print(f'families used: {len(fams9)} {fams9}')
saved9 = pd.read_csv(f'{BOOKS}/r5_book_C9_ts_dealerLong_high_15.csv',
                     index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([bn9, saved9], axis=1, keys=['mine', 'saved']).dropna()
print(f'book vs saved CSV: n_common={len(j)} max|dev|={float((j.mine - j.saved).abs().max()):.3e} '
      f'corr={float(j.mine.corr(j.saved)):.6f}')
print('mine :', stats(bn9, champ))
print('saved:', stats(saved9, champ))
bn9.rename('my_rebuild_C9_net').to_csv(f'{OUT}/my_rebuild_C9_net.csv')

print()
print('=== REBUILD C3: Tot_All-count LOW thr 2.0, 21 proxy families ===')
bp3, bn3, fams3 = build_book(ALL, 'Tot_All', 'low', 2.0)
print(f'families used: {len(fams3)}')
saved3 = pd.read_csv(f'{BOOKS}/r5_book_C3_ts_tot_low_20.csv',
                     index_col=0, parse_dates=True).iloc[:, 0]
j3 = pd.concat([bn3, saved3], axis=1, keys=['mine', 'saved']).dropna()
print(f'book vs saved CSV: n_common={len(j3)} max|dev|={float((j3.mine - j3.saved).abs().max()):.3e} '
      f'corr={float(j3.mine.corr(j3.saved)):.6f}')
print('mine :', stats(bn3, champ))
print('saved:', stats(saved3, champ))
bn3.rename('my_rebuild_C3_net').to_csv(f'{OUT}/my_rebuild_C3_net.csv')

print()
print('=== BREAK numbers from raw panel (charter-mandated) ===')
for fam, bd in BREAKS.items():
    d = fam_frame(fam)
    pre = d.loc[d.index < bd].iloc[-1]
    post = d.loc[d.index >= bd].iloc[0]
    ta0, ta1 = pre['cnt_Traders_Tot_All'], post['cnt_Traders_Tot_All']
    oi0, oi1 = pre['open_interest'], post['open_interest']
    print(f'{fam} {post.name.date()}: TotAll {ta0}->{ta1} = {(ta1/ta0-1)*100:+.0f}pct | '
          f'OI {oi0:,.0f}->{oi1:,.0f} = {(oi1/oi0-1)*100:+.0f}pct')
