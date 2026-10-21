#!/usr/bin/env python3
"""RES_COT — canonical COT → price-panel builder (data-engine clean-up).

Builds a clean, daily, tradeable price panel for the COT (Commitments of Traders) markets,
plus a coverage MANIFEST. Consolidates the scattered price sources (more_etf / twelvedata /
twelve_big / data_fred / more_fx) into ONE canonical mapping so the COT engine has a
deterministic instrument backing per market with no ad-hoc lookups.

COT data: tools/quant/data/more_cot/<mkt>_cot.csv — weekly, cols (date, net_noncomm,
net_noncomm_pct_oi, open_interest), 2010+ (net_noncomm = spec net; pct_oi normalizes by OI).

The panel builder FAILS LOUDLY (raises) if a mapped market has no resolvable daily price proxy,
instead of silently emitting a blank-row in the MANIFEST. Daily proxies are resolved by an
ordered search over the known on-disk price families (see load_px below).

Mapping (market -> tradeable daily ETF/price, source):
"""
import os, sys
import pandas as pd, numpy as np
ROOT="/Users/daxu/software/world-trader"
MORECOT=f"{ROOT}/tools/quant/data/more_cot"

# Ordered price-family search roots. First file that exists for a ticker wins.
PX_ROOTS = [
    f"{ROOT}/tools/quant/data/more_etf",   # ETFA daily closes
    f"{ROOT}/tools/quant/data/twelvedata", # SPY/QQQ/GLD/... closes
    f"{ROOT}/tools/quant/data/twelve_big", # long-history twelvedata
    f"{ROOT}/tools/quant/hedge_fund_strats/data_fred",  # FRED daily (dow/eur/gbp/...)
    f"{ROOT}/tools/quant/data/more_fx",    # FX-daily family
]

# canonical COT-market -> daily price symbol. Symbol is resolved across PX_ROOTS in order,
# with per-symbol explicit source overrides where multiple families collide (e.g. SPY lives
# in twelvedata, not more_etf).
MKT2PX = {
  # commodities (ETFs)
  'gold':'GLD','silver':'SLV','copper':'CPER','crude_wti_nymex':'USO','nat_gas_nymex':'UNG',
  'corn':'CORN','soybeans':'SOYB','soybean_oil':'DBA','soybean_meal':'DBA','wheat_hrw':'WEAT',
  'wheat_srw':'WEAT','wheat_hrspring':'WEAT','live_cattle':'DBA','lean_hogs':'DBA',
  'cotton_no2':'DBA','sugar_no11':'DBA','cocoa':'DBA','coffee_c':'DBA','canola':'DBA',
  'oats':'DBA','rough_rice':'DBA','lumber':'DBA',
  # financials (rates/equity/currencies/vol) - proxied by way of SPY/TLT/VIX where daily
  'sp500_emini':'SPY','nasdaq_emini':'QQQ','dow_emini':'DIA','us_10y_note':'TLT','us_2y_note':'IEF',
  'us_5y_note':'IEF','us_tbond':'TLT','eur':'FXE','gbp':'FXB','jpy':'FXY','vix':'VIX',
}
# Explicit symbol -> source-root exceptions (resolved BEFORE generic PX_ROOTS order). These
# pin symbols that exist in multiple families but must use a specific family for span/lint,
# or that have no ETF on disk and resolve to a long-history FRED daily rate.
PX_OVERRIDE = {
    'SPY': f"{ROOT}/tools/quant/data/twelvedata/SPY.csv",   # not in more_etf
    'QQQ': f"{ROOT}/tools/quant/data/more_etf/QQQ.csv",     # longest QQQ span
    'VIX': f"{ROOT}/tools/quant/data/more_vol/VIX.csv",     # long-history VIX
    # CME FX COT backed by the DEX FRED daily rate (no FXE/FXB/FXY ETF on disk)
    'FXE': f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/eur.csv",
    'FXB': f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/gbp.csv",
    'FXY': f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/jpy.csv",
}

def _close_series(path, start):
    """Load a daily close series (close col or first col), sorted, de-duped, from `start`."""
    d = pd.read_csv(path, index_col=0, parse_dates=True)
    c = 'close' if 'close' in d.columns else d.columns[0]
    s = d[c].astype(float).sort_index()
    s = s[~s.index.duplicated(keep='last')]
    s = s[s.index >= pd.Timestamp(start)]
    return s

def load_px_window(mkt, start):
    """Return daily close series for the market's proxy price, from `start`.

    Resolution order: (1) explicit PX_OVERRIDE symbol path, (2) first PX_ROOT file that exists
    for the mapped symbol. Raises if unresolvable (fail-loud — a missing proxy is a data defect,
    not a soft blank).
    """
    px = MKT2PX[mkt]
    # (1) explicit override
    ov = PX_OVERRIDE.get(px)
    if ov and os.path.exists(ov):
        return _close_series(ov, start)
    # (2) ordered search
    for root in PX_ROOTS:
        p = f"{root}/{px}.csv"
        if os.path.exists(p):
            return _close_series(p, start)
    raise FileNotFoundError(
        f"COT market '{mkt}' has mapped price symbol '{px}' but NO price file found in "
        f"PX_ROOTS/overrides. Fix PX_OVERRIDE or add the series (fail-loud, data defect).")

def load_cot(mkt):
    df=pd.read_csv(f"{MORECOT}/{mkt}_cot.csv", parse_dates=['date'])
    df=df.sort_values('date').drop_duplicates('date', keep='last')
    return df.set_index('date')

def build_panel():
    """Return (cot_net frame, cot_pct frame, px frame, manifest) aligned on COT report dates.

    FAILS LOUDLY if any mapped market has no resolvable non-empty daily price proxy — a blank
    px entry in the manifest is a data defect, never a silent soft-pass.
    """
    markets=sorted(os.path.basename(f)[:-8] for f in os.listdir(MORECOT) if f.endswith('_cot.csv'))
    netf={}; pctf={}; pxf={}; manifest=[]
    for m in markets:
        if m not in MKT2PX: continue
        c=load_cot(m)
        netf[m]=c['net_noncomm']
        pctf[m]=c['net_noncomm_pct_oi']
        p=load_px_window(m, str(c.index.min()))
        if p is None or len(p) == 0:
            raise RuntimeError(f"market '{m}' produced empty price proxy (fail-loud data defect)")
        pxf[m]=p
        manifest.append(dict(market=m, mktkey=m, price=MKT2PX[m],
                             cot_start=str(c.index.min().date()), cot_end=str(c.index.max().date()),
                             cot_rows=len(c),
                             px_start=str(p.index.min().date()), px_end=str(p.index.max().date()),
                             px_rows=len(p)))
    net=pd.DataFrame(netf).sort_index()
    pct=pd.DataFrame(pctf).sort_index()
    man=pd.DataFrame(manifest)
    return net, pct, pxf, man

if __name__=='__main__':
    net,pct,pxf,man=build_panel()
    print(f"Hay {len(man)} markets mapped")
    print(man[['market','price','cot_start','cot_end','cot_rows','px_end']].to_string(index=False))
    net.rename_axis('date').to_csv(f"{ROOT}/campaign/team/agents/RES_COT/cot_net_weekly.csv")
    pct.rename_axis('date').to_csv(f"{ROOT}/campaign/team/agents/RES_COT/cot_pct_weekly.csv")
    man.to_csv(f"{ROOT}/campaign/team/agents/RES_COT/MANIFEST.csv", index=False)
    print("wrote cot_net_weekly.csv, cot_pct_weekly.csv, MANIFEST.csv")
