#!/usr/bin/env python3
"""HUNT_FXCARRY2 round-1. FX data only spans 2019-06..2026-08 (2k rows/pair).
Carry proxy: no forward points on disk => use short-rate differential from FRED
(FEDFUNDS vs international policy proxies) — honest: nominal carry approximation.
(a) carry+momentum combo, (b) real carry (CPI-deflated), (d) vol-scaled momentum."""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/work_r1')
from hunt_lib import *
import numpy as np, pandas as pd

FX = f"{ROOT}/tools/quant/data/fx"
PAIRS = ['AUD_USD','EUR_GBP','EUR_USD','GBP_USD','NZD_USD','USD_CAD','USD_CHF','USD_JPY']
px = {p: load_close(f"{FX}/{p}.csv") for p in PAIRS}
rets_d = {p: s.pct_change() for p, s in px.items()}
idx = pd.concat(px.values(), axis=1, join='inner').index

# ---- rates for carry (all FRED, monthly -> daily ffill) ----
FR = f"{ROOT}/tools/quant/data/more_fred"
def fred(sid):
    df = pd.read_csv(f"{FR}/{sid}.csv")
    s = pd.Series(df[df.columns[1]].astype(float).values, index=pd.to_datetime(df[df.columns[0]])).dropna()
    return s.sort_index()

rate = {}   # domestic short rate per currency (approximations available on disk)
rate['USD'] = fred('FF') if False else fred('DFF') if False else None
# available: FEDFUNDS (US), FEDFUNDS-like only for US. Use IR3MIB01M? not on disk.
# Honest fallback: REAL carry via CPI differentials (both monthly, on disk for US only).
# => nominal carry needs int'l rates; try IRLTLT01 long rates we have for AU/CA/CH/GB/JP/NZ
for cc, sid in [('AU','IRLTLT01AUM156N'),('CA','IRLTLT01CAM156N'),('CH','IRLTLT01CHM156N'),
                ('GB','IRLTLT01GBM156N'),('JP','IRLTLT01JPM156N')]:
    try: rate[cc] = fred(sid)
    except Exception as e: print("missing", cc, sid)
us = fred('IRLTLT01USM156N') if True else None
rate['US'] = us

print("== carry signal: long-yield-currency minus USD (long-rate differential proxy) ==")
# USD per-pair rate: US. Foreign: currency country (AUD->AU etc).
C3TO2 = {'AUD':'AU','CAD':'CA','CHF':'CH','GBP':'GB','JPY':'JP','NZD':'NZ',
         'EUR':'DE','USD':'US'}
def ccy(pair):
    a, b = pair.split('_')
    return C3TO2.get(a, a), C3TO2.get(b, b)
carry = {}
for p in PAIRS:
    a, b = ccy(p)
    ra = rate.get(a); rb = rate.get(b)
    if ra is None or rb is None:
        print(f"  {p}: no rate pair -> skip carry"); continue
    diff = (ra - rb)
    diff_d = diff.reindex(idx, method='ffill')
    carry[p] = diff_d
print("pairs with carry:", list(carry))

print("\n== (a) CARRY+MOM combo: sign(long-rate diff) AND 63d momentum agree => 1 else 0 ==")
books = []
for p, cd in carry.items():
    a, b = ccy(p)
    s = px[p]
    mom63 = s.pct_change(63)
    # positive diff => a yields more => long a vs b => for pair quote (a/b), price up = a strengthens
    sig = pd.Series(np.where((cd > 0) & (mom63 > 0), 1.0, np.where((cd < 0) & (mom63 < 0), -1.0, 0.0)), index=s.index)
    net, st = evaluate(sig, rets_d[p], vt=True)
    books.append(net.rename(p))
    print(f"{p:<9} n={st['n']:>5} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} corr={champ_corr(net):.3f}")
book_all = pd.concat(books, axis=1).dropna(how='all').fillna(0.0).mean(axis=1)
st = stat(book_all); yok, yrs = yearly_ok(book_all)
print(f"BOOK-EW   n={st['n']:>5} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')}) corr={champ_corr(book_all):.3f} yearly_ok={yok}")
print("years:", yrs)

print("\n== (b) REAL carry: nominal-rate diff minus CPI-diff (US vs foreign, yoy) ==")
try:
    cpis = {'US': fred('CPALTT01USM657N')}
    for cc, sid in [('AU','CPALTT01AUM657N'),('CA','CPALTT01CAM657N'),('CH','CPALTT01CHM657N'),
                    ('GB','CPALTT01GBM657N'),('JP','CPALTT01JPM657N'),('NZ','CPALTT01CNM657N')]:
        try: cpis[cc] = fred(sid)
        except Exception: pass
    books2 = []
    for p, cd in carry.items():
        a, b = ccy(p)
        ca, cb = cpis.get(a), cpis.get(b)
        if ca is None or cb is None: continue
        infl_a = ca.pct_change(12); infl_b = cb.pct_change(12)
        realdiff = (cd - (infl_a - infl_b).reindex(cd.index, method='ffill'))
        s = px[p]; mom63 = s.pct_change(63)
        sig = pd.Series(np.where((realdiff > 0) & (mom63 > 0), 1.0,
                          np.where((realdiff < 0) & (mom63 < 0), -1.0, 0.0)), index=s.index)
        net, st = evaluate(sig, rets_d[p], vt=True)
        books2.append(net)
        print(f"{p:<9} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f}")
    if books2:
        b2 = pd.concat(books2, axis=1).dropna(how='all').fillna(0.0).mean(axis=1)
        st = stat(b2); yok, _ = yearly_ok(b2)
        print(f"REALCARRY-EW SR={st['sr']:.3f} ann={st['ann']:.4f} negyr={st.get('neg_years')} corr={champ_corr(b2):.3f} yearly_ok={yok}")
except Exception as e:
    print("realcarry skip:", repr(e)[:80])

print("\n== (d) vol-scaled momentum 63d, all 8 pairs ==")
books3 = []
for p in PAIRS:
    s = px[p]; r = rets_d[p]
    mom = s.pct_change(63)
    sig = pd.Series(np.sign(mom), index=s.index)
    net, st = evaluate(sig, r, vt=True)
    books3.append(net)
    print(f"{p:<9} SR={st['sr']:>6.3f} ann={st['ann']:>8.4f} negyr={st.get('neg_years')}")
b3 = pd.concat(books3, axis=1).dropna(how='all').fillna(0.0).mean(axis=1)
st = stat(b3); yok, yrs = yearly_ok(b3)
print(f"MOM-EW    n={st['n']} SR={st['sr']:.3f} ann={st['ann']:.4f} negyr={st.get('neg_years')} h=({st.get('h1')},{st.get('h2')}) corr={champ_corr(b3):.3f} yearly_ok={yok}")
print("years:", yrs)
