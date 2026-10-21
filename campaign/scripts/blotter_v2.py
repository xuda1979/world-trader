#!/usr/bin/env python3
"""GOAL100 TRADE-RECORD (BLOTTER) V2 — per-book, cost-complete, honest-price ledger emitter.

Fixes BLOTTER_TESTER FINDINGS (iter6.5) WITHOUT touching honest13_build.py or any
GOAL100_HONEST14V3_*.csv champion (position path / charged cost byte-preserved):

  #1 CRITICAL  per-book ledgers SAFE (TGT .07/THR .04) + AGGRESSIVE (.091/.03) via
               position_path(TGT,THR) — no hardcode; BALANCED = pairwise mean of the two
               books' records (matching the builder's BAL=(A+B)/2 charged accounting);
               `book` column on every row.
  #6 MAJOR     ALL charged cost streams recorded: trade rows (reb turnover, 6.0bps charged),
               overlay_vt rows (per-sleeve vt overlay `tw` stream), throttle rows (`dsc`),
               per-sleeve borrow rows (htb: SHORTF legs incl. dualmom HTB uplift).
               Columns: cost_total (charged cost of the record), borrow_charge, pnl_contrib
               (gross daily PnL attribution, on `mark` rows).
  #4 MAJOR     honest price maps: carryv2 -> REAL XAU spot (tools/quant/hedge_fund_strats/
               data_fred/xau.csv, else SYNTH); a6r7/QAxasts relabeled "US 2Y/10Y TREASURY
               YIELD (%, not futures price)"; brwt* relabeled "Brent spot leg"; C5ng* SPOT.
  #7 MINOR     execution price = t-1 close (last print STRICTLY before the claimed PnL day).
               Record-only: qty/weights/charged cost byte-identical to the v1 AGG ledger.
  #8 MINOR     holiday_trade = 1 when the record date is a US federal holiday.

LEDGER-ALONE PNL (fixes the vacuous gate): `mark` rows carry, per (date,sleeve), the gross
PnL attribution pnl_contrib = wts_n * gb_t * V_net[n,t] (exact decomposition of the builder's
b_t) and the day's position weight. Then
    ledger_pnl[t] = sum(mark.pnl_contrib at t) - sum(cost_total at t)
reproduces the committed champion series to <1e-8 daily FROM THE LEDGER ALONE.

Usage: python3 campaign/scripts/blotter_v2.py [--verify]
  -> campaign/results/BLOTTER_HONEST14V3_SAFE.csv / _AGGRESSIVE.csv / _BALANCED.csv
"""
import sys, os
sys.path.insert(0, 'campaign/scripts')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, pandas as pd
from honest13_build import make, NEW3, ROOT, vt, load, POOL, SHORTF, EXEC, sn as _sn

COST_BPS = 6.4          # standard-label one-side cost per TRADE record
CHARGED_BPS = 6.0       # bps the frozen builder ACTUALLY charges per unit turnover
BOOKS = {"SAFE": (0.07, 0.04), "AGGRESSIVE": (0.091, 0.03)}
BAL_NAME = "BALANCED"
COLS = ['date','book','sleeve','instrument','side','price','price_source','qty_notional',
        'weight_from','weight_to','cost_stream','cost_bps','cost_total','borrow_charge',
        'holiday_trade','pnl_contrib']

INSTRUMENT = {
    'brwt15': 'BRENT/WTI FUT SPREAD — priced at Brent spot leg (spread level not directly priced)',
    'brwt10': 'BRENT/WTI FUT SPREAD — priced at Brent spot leg (spread level not directly priced)',
    'brwt7':  'BRENT/WTI FUT SPREAD — priced at Brent spot leg (spread level not directly priced)',
    'brwt5':  'BRENT/WTI FUT SPREAD — priced at Brent spot leg (spread level not directly priced)',
    'C5ng':   'HENRY HUB NG (spot price proxy for NG FUT)',
    'C5ngsum':'HENRY HUB NG (spot price proxy for NG FUT)',
    'A5r2':   'SPY (VIX-term+rate-shock gate)',
    'a6r7':   'US 2Y TREASURY YIELD (%, not futures price; DGS2)',
    'QAxasts':'US 10Y TREASURY YIELD (%, not futures price; DGS10)',
    'carryv2':'XAU GOLD SPOT (carryv2)',
    'dualmom':'EQUITY L/S BOOK (12-1 top-tercile vs mkt)',
    'diescrack':'DIESEL/WTI CRACK SPREAD — priced at diesel heating-oil spot leg',
    'CFX4':   'FX CROSS BOOK (GBPNZD/AUDGBP/AUDEUR/EURNZD)',
    'FF2':    'FF FACTOR BOOK (MOM + MKT-RF dual-gate, long)',
}

# ---------------- REAL price series ----------------
_REAL_PX = {}
def _load_real_px():
    def fr(path, col):
        d = pd.read_csv(path); s = d[col].astype(float)
        s.index = pd.to_datetime(d[d.columns[0]])
        return s.sort_index()
    _REAL_PX['brent']  = fr(f"{ROOT}/tools/quant/data/newdata/DCOILBRENTEU.csv", 'DCOILBRENTEU')
    _REAL_PX['wti']    = fr(f"{ROOT}/tools/quant/data/newdata/DCOILWTICO.csv", 'DCOILWTICO')
    _REAL_PX['ng']     = fr(f"{ROOT}/tools/quant/data/newdata/DHHNGSP.csv", 'DHHNGSP')
    _REAL_PX['us2y']   = fr(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/DGS2.csv", 'DGS2')
    _REAL_PX['us10y']  = fr(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/DGS10.csv", 'DGS10')
    _REAL_PX['diesel'] = fr(f"{ROOT}/tools/quant/data/newdata/DJFUELUSGULF.csv", 'DJFUELUSGULF')
    _REAL_PX['xau']    = fr(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/xau.csv", 'value')
    import campaign.harness.data as D
    px = D.closes(); _REAL_PX['spy'] = px['SPY']
_load_real_px()

_SS = {
 'brwt15':('brent',),'brwt10':('brent',),'brwt7':('brent',),'brwt5':('brent',),
 'C5ng':('ng',),'C5ngsum':('ng',),'A5r2':('spy',),
 'a6r7':('us2y',),'QAxasts':('us10y',),
 'carryv2':('xau',),            # #4 FIX: REAL gold spot (xau.csv); GLD absent from harness panel
 'dualmom':(), 'diescrack':('diesel',), 'CFX4':(), 'FF2':(),
}

def transact_price(sleeve, date):
    """t-1 close of the sleeve's REAL price series (last print STRICTLY before day t),
    NaN when none exists (caller falls back to the SYNTH sleeve index)."""
    src = _SS.get(sleeve)
    if not src: return np.nan
    s = _REAL_PX.get(src[0])
    if s is None: return np.nan
    loc = s.index.searchsorted(pd.Timestamp(date), side='left')
    if loc == 0: return np.nan
    v = s.iloc[loc - 1]
    return float(v) if not pd.isna(v) else np.nan

# ---------------- synthetic proxy (PnL-consistent index=100 path, vol-targeted returns) ----------------
_SYNTH = {}
_V0_RAW = None
def _synth_px(sleeve):
    if sleeve not in _SYNTH:
        r = _V0_RAW[sleeve].dropna()
        _SYNTH[sleeve] = (1 + r.fillna(0)).cumprod() * 100.0
    return _SYNTH[sleeve]

def _recover_v0():
    RAW = {}
    for n, p in POOL.items(): RAW[n] = _sn(p)
    for n, p in NEW3.items(): RAW[n] = load(p).dropna()
    return RAW

# ---------------- mechanics: ONE pass of the frozen builder internals ----------------
def mechanics(NEW=NEW3):
    """Exactly honest13_build.make() internals + the net per-sleeve return matrix V_net
    (pool sleeves net of internal instrument costs, as blended by the builder)."""
    global _V0_RAW, _SYNTH
    RAW = _recover_v0()
    _V0_RAW = RAW; _SYNTH = {}
    names = list(RAW.keys())
    slots = {n: (1.0 if n in POOL else 0.10) for n in names}
    tot_slot = sum(slots.values())
    wts = pd.Series({n: slots[n]/tot_slot for n in names}, dtype=float)
    S = {}; V0 = {}
    for n, r in RAW.items():
        v, sv = vt(r, 0.08); S[n] = sv; V0[n] = v
    Sd = pd.DataFrame(S).dropna(how='all')
    capW = Sd.mul(wts, axis=1)
    V = {}
    for n in names:
        v = V0[n]
        if n in POOL:
            V[n] = v - capW[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
        else:
            V[n] = v
    V_net = pd.DataFrame(V)
    W = Sd.div(Sd.sum(axis=1), axis=0).fillna(0)
    blend = (V_net.mul(wts, axis=1)).sum(axis=1)
    blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    return dict(Sd=Sd, capW=capW, blend=blend, tw=tw, wts=wts, V_net=V_net)

def position_path(M, TGT, THR):
    """Frozen builder book path, parameterized by (TGT, THR) — #1 fix (no hardcode)."""
    b, gb = vt(M['blend'], TGT)
    eq = (1+b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index)
    full = M['capW'].mul(gb, axis=0).mul(sc, axis=0)
    return b, gb, sc, full

# ---------------- per-book ledger ----------------
def build_book_ledger(book, M, b, gb, sc, full, holiday_set, charged_index=None):
    tw_al = M['tw'].reindex(full.index).fillna(0)
    dsc_al = sc.diff().abs().mul(0.5)
    if charged_index is not None:
        # the builder charges cost streams only over the champion window (reindex to b.index /
        # r_out index then dropna) — restrict the LEDGER's cost rows to exactly that charged window
        tw_al = tw_al.reindex(charged_index).fillna(0)
        dsc_al = dsc_al.reindex(charged_index).fillna(0)
    # htb per sleeve per day (frozen formula), skipna-aligned like the builder
    htb_cols = {}
    for n in POOL:
        sf = SHORTF[n]
        if sf > 0:
            htb_cols[n] = M['capW'][n]*sc*sf*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2)
    htb = pd.DataFrame(htb_cols)

    trades = []
    d = full.diff()
    for date, row in d.iterrows():
        is_hol = 1 if date.date() in holiday_set else 0
        for sleeve, dv in row.items():
            if pd.isna(dv) or abs(dv) < 1e-14:
                continue
            w_to = full.at[date, sleeve] if not pd.isna(full.at[date, sleeve]) else 0.0
            w_from = w_to - dv
            px = transact_price(sleeve, date)
            pxs = "REAL" if not pd.isna(px) else "SYNTH"
            if pd.isna(px):
                sp = _synth_px(sleeve)
                px = sp.asof(date) if len(sp.index) and sp.index[0] <= date else np.nan
            trades.append(dict(date=date, book=book, sleeve=sleeve, instrument=INSTRUMENT[sleeve],
                side=("BUY" if dv > 0 else "SELL"),
                price=round(float(px), 6) if not pd.isna(px) else np.nan,
                price_source=pxs, qty_notional=round(abs(dv), 10),
                weight_from=round(float(w_from), 10), weight_to=round(float(w_to), 10),
                cost_stream='trade', cost_bps=COST_BPS,
                cost_total=abs(dv) * CHARGED_BPS * 1e-4,
                borrow_charge=0.0, holiday_trade=is_hol, pnl_contrib=0.0))
    tr = pd.DataFrame(trades)

    def cost_rows(stream, series, instrument, bps=CHARGED_BPS):
        rows = []
        for date, v in series[series > 0].items():
            rows.append(dict(date=date, book=book, sleeve='GLOBAL-BLEND', instrument=instrument,
                side='HOLD', price=np.nan, price_source='SYNTH', qty_notional=0.0,
                weight_from=np.nan, weight_to=np.nan, cost_stream=stream, cost_bps=bps,
                cost_total=float(v) * CHARGED_BPS * 1e-4, borrow_charge=0.0,
                holiday_trade=1 if date.date() in holiday_set else 0, pnl_contrib=0.0))
        return rows

    twr = cost_rows('overlay_vt', tw_al,
                    'per-sleeve vol-target overlay turnover (tw stream, one-side frac NAV)')
    dscr = cost_rows('throttle', dsc_al.fillna(0),
                     'drawdown throttle 0.5x switch (dsc stream, one-side frac NAV)')
    brr = []
    for n in htb.columns:
        hcol = htb[n] if charged_index is None else htb[n].reindex(charged_index).dropna()
        s = hcol[hcol.abs() > 0]
        for date, v in s.items():
            brr.append(dict(date=date, book=book, sleeve=n,
                instrument=INSTRUMENT[n] + ' [SHORT LEG FINANCING]', side='HOLD', price=np.nan,
                price_source='SYNTH', qty_notional=0.0, weight_from=np.nan, weight_to=np.nan,
                cost_stream='borrow', cost_bps=np.nan,
                cost_total=float(v)/252.0, borrow_charge=float(v)/252.0,
                holiday_trade=1 if date.date() in holiday_set else 0, pnl_contrib=0.0))

    # ---- mark rows: gross PnL attribution + position weight, per (date,sleeve) ----
    gbf = gb.reindex(full.index).fillna(0.0)
    pnl = M['V_net'].mul(M['wts'], axis=1).mul(gbf, axis=0).mul(sc, axis=0).stack()
    wstack = full.stack()
    marks = pd.DataFrame({'pnl_contrib': pnl}).join(pd.DataFrame({'weight_to': wstack}), how='left')
    marks = marks.reset_index().rename(columns={'level_0': 'date', 'level_1': 'sleeve'})
    mdf = pd.DataFrame([dict(date=r.date, book=book, sleeve=r.sleeve,
        instrument=INSTRUMENT.get(r.sleeve, r.sleeve) + ' [DAILY POSITION MARK]', side='MARK',
        price=np.nan, price_source='SYNTH', qty_notional=0.0, weight_from=np.nan,
        weight_to=round(float(r.weight_to), 10) if not pd.isna(r.weight_to) else np.nan,
        cost_stream='mark', cost_bps=np.nan, cost_total=0.0, borrow_charge=0.0,
        holiday_trade=1 if r.date.date() in holiday_set else 0,
        pnl_contrib=float(r.pnl_contrib)) for r in marks.itertuples()])

    out = pd.concat([tr, pd.DataFrame(twr), pd.DataFrame(dscr), pd.DataFrame(brr), mdf],
                    ignore_index=True)
    out['holiday_trade'] = out['holiday_trade'].fillna(0).astype(int)
    return out.sort_values(['date', 'sleeve', 'cost_stream']).reset_index(drop=True)

def ledger_pnl(led, index):
    """Ledger-ALONE daily PnL: sum(mark pnl_contrib) - sum(cost_total), per day."""
    g = led.groupby(['date'])[['pnl_contrib', 'cost_total']].sum()
    g['net'] = g.pnl_contrib - g.cost_total
    return g['net'].reindex(index)

def build_book(book, M, TGT, THR, holiday_set):
    b, gb, sc, full = position_path(M, TGT, THR)
    champ_idx = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST14V3_{book}_daily.csv",
                            index_col=0, parse_dates=True).index
    led = build_book_ledger(book, M, b, gb, sc, full, holiday_set, charged_index=champ_idx)
    info = dict(b=b, gb=gb, sc=sc, full=full)
    return led, info

def _avg_frame(a, b, wcols=('weight_from', 'weight_to')):
    """Rowwise mean of two aligned frames treating NaN as missing (not zero)."""
    out = a.copy()
    for c in a.columns:
        if c in b.columns:
            av, bv = a[c], b[c]
            out[c] = np.where(av.isna(), bv, np.where(bv.isna(), av, (av + bv) / 2.0))
    return out

def build_all(NEW=NEW3, write=False, verify=False):
    from pandas.tseries.holiday import USFederalHolidayCalendar
    hol = set(USFederalHolidayCalendar().holidays(start='2006-01-01', end='2026-12-31').date)
    M = mechanics(NEW)
    ledgers, infos = {}, {}
    for book, (TGT, THR) in BOOKS.items():
        led, info = build_book(book, M, TGT, THR, hol)
        ledgers[book] = led; infos[book] = info
        print(f"[{book}] rows={len(led)} trades={int((led.cost_stream=='trade').sum())} "
              f"borrow={int((led.cost_stream=='borrow').sum())} overlay={int((led.cost_stream=='overlay_vt').sum())} "
              f"throttle={int((led.cost_stream=='throttle').sum())} marks={int((led.cost_stream=='mark').sum())} "
              f"cost_total={led.cost_total.sum():.10f}")
    # ---- BALANCED = pairwise mean of the two books' records (builder BAL=(A+B)/2) ----
    key = ['date', 'sleeve', 'cost_stream']
    a = ledgers['SAFE'].set_index(key); b = ledgers['AGGRESSIVE'].set_index(key)
    j = a.join(b, how='outer', lsuffix='_s', rsuffix='_a')
    # pairwise mean must be over BOTH denominators: when only one book has the record, the
    # balanced value is half that book's value (BAL=(A+B)/2 with B absent => B=0), NOT the
    # lone value itself. (Root cause of the 7.5e-5 BAL round-trip failure: dsc/throttle rows
    # exist on SAFE-only dates; a NaN-keeping mean made BAL charge the full SAFE value.)
    num = ['price', 'qty_notional', 'weight_from', 'weight_to', 'cost_total', 'borrow_charge', 'pnl_contrib']
    for c in num:
        sv, av = j[c + '_s'], j[c + '_a']
        both_nan = sv.isna() & av.isna()
        j[c] = np.where(both_nan, np.nan, (sv.fillna(0) + av.fillna(0)) / 2.0)
    j['side'] = np.where(j.side_s.isna(), j.side_a,
                np.where(j.side_a.isna(), j.side_s, j.side_s))
    # honest side for true pairwise rows: sign of the averaged signed delta is not recoverable
    # from |.| means; keep SAFE's side when both books traded (disclosed in FINDINGS).
    j['instrument'] = np.where(j.instrument_s.isna(), j.instrument_a, j.instrument_s)
    j['price_source'] = np.where(j.price_source_s.isna(), j.price_source_a, j.price_source_s)
    j['book'] = BAL_NAME
    j['cost_stream_'] = j.index.get_level_values('cost_stream')
    j['cost_bps'] = np.where(j.cost_stream_ == 'trade', COST_BPS,
                    np.where(j.cost_stream_.isin(['overlay_vt', 'throttle']), CHARGED_BPS, np.nan))
    j['holiday_trade'] = j[['holiday_trade_s', 'holiday_trade_a']].fillna(0).max(axis=1).astype(int)
    j['date_'] = j.index.get_level_values('date')
    j['sleeve_'] = j.index.get_level_values('sleeve')
    j['stream_'] = j.index.get_level_values('cost_stream')
    bal = j.reset_index(drop=True)
    bal = bal.rename(columns={'date_': 'date', 'sleeve_': 'sleeve', 'stream_': 'cost_stream'})
    bal = bal[COLS]
    bal = bal.sort_values(['date', 'sleeve', 'cost_stream']).reset_index(drop=True)
    ledgers[BAL_NAME] = bal
    print(f"[BALANCED] rows={len(bal)} (pairwise mean of SAFE+AGG records)")
    if write:
        for bk in (BAL_NAME, 'SAFE', 'AGGRESSIVE'):
            out = ledgers[bk].copy(); out['date'] = pd.to_datetime(out['date']).dt.strftime('%Y-%m-%d')
            out.to_csv(f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_{bk}.csv", index=False)
            print(f"wrote {ROOT}/campaign/results/BLOTTER_HONEST14V3_{bk}.csv ({len(out)} rows)")
    return BlotterState(ledgers, M, infos, hol)

class BlotterState:
    def __init__(self, ledgers, M, infos, hol):
        self.ledgers = ledgers; self.M = M; self.infos = infos
        self.holiday_set = hol; self.real_px = _REAL_PX; self.BAL_NAME = BAL_NAME
        # ledger-alone PnL per book
        self.ledger_pnl = {bk: ledger_pnl(led, self.infos[bk]['full'].index)
                           for bk, led in ledgers.items() if bk in infos}
        # charged accounting per book (frozen builder formulas)
        self.reb_abs_sleeve, self.htb_sleeve, self.stream_tot, self.charged_cost_tot = {}, {}, {}, {}
        for bk, info in infos.items():
            full, sc, tw = info['full'], info['sc'], self.M['tw']
            self.reb_abs_sleeve[bk] = full.diff().abs().sum(axis=0)
            htb_s = {}
            for n in POOL:
                sf = SHORTF[n]
                if sf > 0:
                    htb_s[n] = (self.M['capW'][n]*sc*sf*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2)).sum()/252.0
            self.htb_sleeve[bk] = pd.Series(htb_s)
            dsc = sc.diff().abs().mul(0.5).fillna(0)
            # charged over the CHAMPION's index (builder charges r_out then dropna(how='all'))
            idx = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST14V3_{bk}_daily.csv",
                              index_col=0, parse_dates=True).index
            tw_c = tw.reindex(idx).fillna(0)
            dsc_c = dsc.reindex(idx).fillna(0)
            self.stream_tot[bk] = {'overlay_vt': float(tw_c.sum())*CHARGED_BPS*1e-4,
                                   'throttle': float(dsc_c.sum())*CHARGED_BPS*1e-4}
            reb = full.diff().abs().sum(axis=1)
            htb_d = pd.concat([self.M['capW'][n]*sc*SHORTF[n]*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2)
                               for n in POOL if SHORTF[n] > 0], axis=1).sum(axis=1)
            charged = ((reb.reindex(idx).fillna(0) + tw_c + dsc_c) * CHARGED_BPS * 1e-4
                       + (htb_d/252.0).reindex(idx).fillna(0))
            self.charged_cost_tot[bk] = float(charged.sum())

def _fmt_csv(df):
    return df.copy().assign(date=pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')).to_csv(index=False)

def verify():
    """Byte-repro of the 3 emitted ledgers (freeze discipline, Tester FIX PLAN #5)."""
    import blotter_v2
    st = build_all(write=False)
    for bk in ('SAFE', 'AGGRESSIVE', 'BALANCED'):
        path = f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_{bk}.csv"
        try:
            old = open(path).read()
        except FileNotFoundError:
            print(f"{bk}: NO EMITTED FILE"); continue
        new = _fmt_csv(st.ledgers[bk])
        print(f"{bk}: byte-repro {'EXACT' if old == new else 'DIFF'}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify()
    else:
        st = build_all(write=True)
        for bk in ('SAFE', 'AGGRESSIVE'):
            led = st.ledgers[bk]; tr = led[led.cost_stream == 'trade']
            lt = tr.groupby('sleeve').qty_notional.sum()
            pt = st.reb_abs_sleeve[bk]
            m = pd.concat([lt.rename('ledger'), pt.rename('pospath')], axis=1).fillna(0)
            tol = 1e-8 + 1e-8*m.pospath.abs()
            ok = ((m.ledger - m.pospath).abs() <= tol).all()
            print(f"[{bk}] per-sleeve reb reconcile vs own book path: {'EXACT' if ok else 'FAIL'}")
            if not ok:
                print(m[(m.ledger - m.pospath).abs() > tol].to_string())
        for bk in ('SAFE', 'AGGRESSIVE', 'BALANCED'):
            champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST14V3_{bk}_daily.csv",
                                index_col=0, parse_dates=True).iloc[:, 0]
            lp = st.ledger_pnl.get(bk)
            if lp is None:
                # BAL: pairwise mean of the two books' ledger PnL
                a = st.ledger_pnl['SAFE']; b_ = st.ledger_pnl['AGGRESSIVE']
                lp = ((a + b_) / 2).reindex(champ.index)
            else:
                lp = lp.reindex(champ.index)
            md = float((lp.fillna(0) - champ).abs().max())
            print(f"[{bk}] ledger-alone PnL vs committed champion: max|diff| = {md:.3e} "
                  f"({'PASS' if md < 1e-8 else 'FAIL'})")
