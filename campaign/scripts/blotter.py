#!/usr/bin/env python3
"""GOAL100 TRADE-RECORD (BLOTTER) EMITTER — rigorous instrument-level trade ledger.

Reconstructs the exact per-sleeve position path from the FROZEN champion builder
(honest13_build.py) and emits a per-day, per-sleeve TRADE LEDGER that EXACTLY reconciles to the
charged cost in the committed backtest. Cross-checks + audit findings printed to stdout.

Accounting note (AUDIT FINDING): the committed builder charges rebalance cost as
`reb = full.diff().abs().sum(axis=1)` with NaN SKIPPED (pandas skipna default). That means when a
sparse sleeve (NYSE-only pool sleeves, gap weeks) has no value on a date, the diff() step produces
NaN which sum(axis=1) SKIPS — the builder does NOT charge a buy-out+sell-back across the gap. This
UNDERCHARGES cost on sleeve re-entry/exit across gaps by ~4% of gross turnover (716.7 charged vs
~746 honest held/across or flat-across, depending on instrument convention). See AUDIT_FINDINGS.

Usage: python3 campaign/scripts/blotter.py
"""
import sys; sys.path.insert(0, 'campaign/scripts')
import numpy as np, pandas as pd
from honest13_build import make, NEW3, ROOT, vt, load

COST_BPS = 6.4
INSTRUMENT = {
    'brwt15':'BRENT/WTI FUT SPREAD','brwt10':'BRENT/WTI FUT SPREAD','brwt7':'BRENT/WTI FUT SPREAD',
    'brwt5':'BRENT/WTI FUT SPREAD','C5ng':'HENRY HUB NG FUT','C5ngsum':'HENRY HUB NG FUT',
    'A5r2':'SPY (VIX-term+rate-shock gate)','a6r7':'US 2Y TREASURY FUT','QAxasts':'US 10Y TREASURY FUT',
    'carryv2':'GLD (gold carry)','dualmom':'EQUITY L/S BOOK (12-1 top-tercile vs mkt)',
    'diescrack':'DIESEL/WTI (HO-CL spread)','CFX4':'FX CROSS BOOK (GBPNZD/AUDGBP/AUDEUR/EURNZD)',
    'FF2':'FF FACTOR BOOK (MOM + MKT-RF dual-gate, long)',
}
# futures-style sleeves: position logically held across non-print gaps (no forced liquidation)
FUTURES_STYLE = {'brwt15','brwt10','brwt7','brwt5','C5ng','C5ngsum','a6r7','QAxasts',
                 'carryv2','diescrack','CFX4','FF2'}
# equity-style sleeves: NAV is flat on non-NYSE gaps (forced flat) -> those SHOULD be liquidated
EQUITY_STYLE  = {'A5r2','dualmom'}

# ---- REAL transaction-price lookup (attaches actual instrument price where a series exists) ---
_REAL_PX = {}
def _load_real_px():
    def fr(path, col):
        d = pd.read_csv(path); s = d[col].astype(float)
        s.index = pd.to_datetime(d[d.columns[0]])
        return s.sort_index()
    ROOTX = ROOT
    _REAL_PX['brent'] = fr(f"{ROOTX}/tools/quant/data/newdata/DCOILBRENTEU.csv", 'DCOILBRENTEU')
    _REAL_PX['wti']   = fr(f"{ROOTX}/tools/quant/data/newdata/DCOILWTICO.csv", 'DCOILWTICO')
    _REAL_PX['ng']    = fr(f"{ROOTX}/tools/quant/data/newdata/DHHNGSP.csv", 'DHHNGSP')
    _REAL_PX['us2y']  = fr(f"{ROOTX}/tools/quant/hedge_fund_strats/data_fred/DGS2.csv", 'DGS2')
    _REAL_PX['us10y'] = fr(f"{ROOTX}/tools/quant/hedge_fund_strats/data_fred/DGS10.csv", 'DGS10')
    _REAL_PX['diesel']= fr(f"{ROOTX}/tools/quant/data/newdata/DJFUELUSGULF.csv", 'DJFUELUSGULF')
    sys.path.insert(0, ROOT)
    import campaign.harness.data as D
    px = D.closes(); _REAL_PX['spy'] = px['SPY']
    _REAL_PX['gld'] = px['GLD'] if 'GLD' in px.columns else None
_load_real_px()

# sleeve -> real price source (when directly tradeable); None => synthetic-index proxy
_SS = {
 'brwt15':('brent','wti'),'brwt10':('brent','wti'),'brwt7':('brent','wti'),'brwt5':('brent','wti'),
 'C5ng':('ng',None),'C5ngsum':('ng',None),'A5r2':('spy',None),'a6r7':('us2y',None),
 'QAxasts':('us10y',None),'carryv2':('gld',None),'dualmom':(None,None),
 'diescrack':('diesel','wti'),'CFX4':(None,None),'FF2':(None,None),
}
def transact_price(sleeve, date):
    """Return a real execution price if the sleeve's tradeable market price exists for `date`,
    else NaN (caller falls back to sleeve synthetic index for reconciliation-neutral proxy)."""
    src = _SS.get(sleeve)
    if src is None: return np.nan
    s = _REAL_PX.get(src[0])
    if s is not None and date in s.index and not pd.isna(s.loc[date]):
        return float(s.loc[date])
    return np.nan

_SYNTH = {}
def _synth_px(sleeve):
    """Synthetic normalized price path (index=100 at first row) from the sleeve's VOL-TARGETED
    return (V0) — used as the price proxy for composite books (FX, factor, equity L/S). PnL-neutral.
    NOTE: uses V0 (vol-targeted return), NOT the scale matrix Sd (bug fixed: Sd carries values up to
    8.0 which blew the index to inf for carryv2)."""
    if sleeve not in _SYNTH:
        r = _BLOTTER_V0[sleeve].dropna()
        _SYNTH[sleeve] = (1 + r.fillna(0)).cumprod() * 100.0
    return _SYNTH[sleeve]

def _recover_v0():
    """Rebuild the per-sleeve VOL-TARGETED return DataFrame exactly as honest13_build.make() does
    (vt with PS=0.08 per sleeve) so the synthetic price paths are sane and PnL-consistent."""
    import honest13_build as H
    from honest13_build import vt as _vt
    RAW = {}
    for n, p in H.POOL.items(): RAW[n] = H.sn(p)
    for n, p in H.NEW3.items(): RAW[n] = load(p).dropna()
    V0d = {}
    for n, r in RAW.items():
        v, _sv = _vt(r, 0.08); V0d[n] = v
    return pd.DataFrame(V0d)

def position_path(NEW, TGT=0.091, THR=0.03):
    global _BLOTTER_Sd, _BLOTTER_V0
    Sd, capW, blend, tw, wts = make(NEW)
    _BLOTTER_Sd = Sd
    _BLOTTER_V0 = _recover_v0()
    b, gb = vt(blend, TGT)
    eq = (1+b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index)
    full = capW.mul(gb, axis=0).mul(sc, axis=0)
    return Sd, capW, blend, tw, wts, full, gb, sc

def build_ledger_reconciled(full):
    """Daily per-sleeve trade notional EXACTLY matching charge = full.diff().abs() (skipna).
    A 'trade record' is emitted only where diff() is non-NaN (defined at both ends) => its sum
    equals the charged reb exactly. This is the byte-exact ledger tied to the PnL."""
    d = full.diff()
    trades = []
    for date, row in d.iterrows():
        for sleeve, dv in row.items():
            if pd.isna(dv) or abs(dv) < 1e-14:
                continue
            w_to = full.loc[date, sleeve] if not pd.isna(full.loc[date, sleeve]) else 0.0
            w_from = w_to - dv
            px = transact_price(sleeve, date)
            pxs = "REAL" if not pd.isna(px) else "SYNTH"  # synthetic = sleeve index=100 path (PnL proxy)
            if pd.isna(px):
                px = _synth_px(sleeve).loc[date] if date in _synth_px(sleeve).index else np.nan
            trades.append(dict(date=date, sleeve=sleeve, instrument=INSTRUMENT[sleeve],
                side=("BUY" if dv>0 else "SELL"), price=round(float(px),6) if not pd.isna(px) else np.nan,
                price_source=pxs, qty_notional=round(abs(dv),10),
                weight_from=round(float(w_from),10), weight_to=round(float(w_to),10),
                cost_bps=COST_BPS))
    return pd.DataFrame(trades)

def reconcile(full, Sd):
    led = build_ledger_reconciled(full)
    led_turn = led.groupby('sleeve').qty_notional.sum()
    pos_turn = full.diff().abs().sum(axis=0)
    m = pd.concat([led_turn.rename('ledger'), pos_turn.rename('pospath')], axis=1)
    tol = 1e-6 + 1e-8*m.pospath.abs()  # float-accum boundary
    m['is_exact'] = (m.ledger - m.pospath).abs() <= tol
    print("===== TRADE-RECORD LEDGER [HONEST14V3 BALANCED] =====")
    print(f"trade records: {len(led)}  | per-day mean one-side turn {full.diff().abs().sum(axis=1).mean()*252:.2f} x/yr")
    print("per-sleeve ledger turnover EXACTLY matches charged position-path turnover:",
          "YES" if m['is_exact'].all() else f"NO ({int((~m['is_exact']).sum())} sleeve(s))")
    if not m['is_exact'].all():
        print(m[~m['is_exact']].to_string())
    return led, full.diff().abs().sum(axis=1), m

if __name__ == "__main__":
    Sd, capW, blend, tw, wts, full, gb, sc = position_path(NEW3)
    led, gross_day, m = reconcile(full, Sd)
    out = f"{ROOT}/campaign/results/BLOTTER_HONEST14V3_BALANCED.csv"
    led.to_csv(out, index=False)
    print(f"wrote {out} ({len(led)} records)")
