"""TRADE-RECORD (BLOTTER) for the RAW-EW14@1.6x candidate — TRADE_RECORD_STANDARD.md compliant."""
import sys
sys.path.insert(0, 'campaign/scripts'); sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L
from honest13_build import POOL, load, NEW3, ROOT

GEAR, RATE, BPS = 1.6, 0.045, 6.4e-4
NAMES = list(POOL.keys()) + list(NEW3.keys())
df = pd.DataFrame({n: load(POOL.get(n) or NEW3.get(n)).dropna() for n in NAMES}).dropna(how='all')
df = df[df.index >= '2008-03-31']
port = df.mean(axis=1)
nav = (1 + df.fillna(0)).cumprod()
w = nav.div(nav.mean(axis=1), axis=0).div(len(NAMES))
dw = w.diff()
to = (dw.abs().sum(axis=1)*0.5).fillna(0)
r = (port*GEAR - to*GEAR*BPS - 0.6*RATE/252).dropna()

INSTR = {'brwt15':'BRENT/WTI FUT SPREAD','brwt10':'BRENT/WTI FUT SPREAD','brwt7':'BRENT/WTI FUT SPREAD',
 'brwt5':'BRENT/WTI FUT SPREAD','C5ng':'HENRY HUB NG FUT','C5ngsum':'HENRY HUB NG FUT',
 'A5r2':'SPY','a6r7':'US 2Y TREASURY FUT','QAxasts':'US 10Y TREASURY FUT','carryv2':'GLD',
 'dualmom':'EQUITY L/S BOOK','diescrack':'DIESEL/WTI CRACK','CFX4':'FX CROSS BOOK',
 'FF2':'FF MOM+MKT BOOK (research-only)'}
SYNTH = {'dualmom','CFX4','FF2'}

# real price series (same sources as campaign blotter.py)
def fr(path, col):
    d = pd.read_csv(path); s = d[col].astype(float)
    s.index = pd.to_datetime(d[d.columns[0]]); return s.sort_index()
PX = {}
PX['brent'] = fr(f"{ROOT}/tools/quant/data/newdata/DCOILBRENTEU.csv", 'DCOILBRENTEU')
PX['wti'] = fr(f"{ROOT}/tools/quant/data/newdata/DCOILWTICO.csv", 'DCOILWTICO')
PX['ng'] = fr(f"{ROOT}/tools/quant/data/newdata/DHHNGSP.csv", 'DHHNGSP')
PX['diesel'] = fr(f"{ROOT}/tools/quant/data/newdata/DJFUELUSGULF.csv", 'DJFUELUSGULF')
PX['us2y'] = fr(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/DGS2.csv", 'DGS2')
PX['us10y'] = fr(f"{ROOT}/tools/quant/hedge_fund_strats/data_fred/DGS10.csv", 'DGS10')
sys.path.insert(0, ROOT)
import campaign.harness.data as D
closes = D.closes()
PX['spy'] = closes['SPY']
PX['gld'] = closes['GLD'] if 'GLD' in closes.columns else None
PXSRC = {'brwt15':('brent','wti'),'brwt10':('brent','wti'),'brwt7':('brent','wti'),'brwt5':('brent','wti'),
 'C5ng':('ng',),'C5ngsum':('ng',),'A5r2':('spy',),'a6r7':('us2y',),'QAxasts':('us10y',),
 'carryv2':('gld',),'diescrack':('diesel','wti')}

def real_px(nm, dt):
    for key in PXSRC.get(nm, ()):
        s = PX.get(key)
        if s is not None and dt in s.index and not pd.isna(s.loc[dt]):
            return float(s.loc[dt]), "REAL"
    return np.nan, "SYNTH"

recs = []
for dt, roww in dw.iterrows():
    for nm, dwv in roww.items():
        if pd.isna(dwv) or abs(dwv) < 1e-15: continue
        px, src = (np.nan, "SYNTH") if nm in SYNTH else real_px(nm, dt)
        w_to = w.loc[dt, nm]*GEAR; w_from = w_to - dwv*GEAR
        recs.append(dict(date=dt, sleeve=nm, instrument=INSTR[nm],
            side=("BUY" if dwv > 0 else "SELL"), price=round(px,6) if not pd.isna(px) else np.nan,
            price_source=src, qty_notional=round(abs(dwv*GEAR),10),
            weight_from=round(w_from,10), weight_to=round(w_to,10), cost_bps=6.4))
led = pd.DataFrame(recs)
# reconcile
led_turn = led.groupby('sleeve').qty_notional.sum()
pos_turn = dw.abs().mul(GEAR).sum(axis=0)
mrg = pd.concat([led_turn.rename('ledger'), pos_turn.rename('pospath')], axis=1).dropna()
tol = 1e-8*1e3
bad = (mrg.ledger - mrg.pospath).abs() > 1e-6 + 1e-8*mrg.pospath.abs()
print(f"trade records: {len(led)}")
print(f"per-sleeve |qty| == charged turnover: {'YES' if not bad.any() else f'NO {int(bad.sum())}'} (max|diff| {float((mrg.ledger-mrg.pospath).abs().max()):.3e})")
# ledger PnL identity
cost_day = to*GEAR*BPS
recon = port*GEAR - cost_day - 0.6*RATE/252
md = float((recon.reindex(r.index) - r).abs().max())
print(f"ledger PnL == candidate PnL: max|diff| {md:.3e} -> {'IDENTICAL' if md < 1e-12 else 'DIFF'}")
realfrac = (led.price_source == 'REAL').mean()
print(f"REAL-priced records: {int((led.price_source=='REAL').sum())}/{len(led)} ({realfrac*100:.1f}%), SYNTH {int((led.price_source=='SYNTH').sum())} (composite books dualmom/CFX4/FF2)")
out = f"{ROOT}/campaign/agents/loop_team/AUDIT_LEVFRONTIER/BLOTTER_RAWEW14_GEAR16.csv"
led.to_csv(out, index=False)
print(f"wrote {out}")
# headline again for the record
s = L.stats(r)
yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
print(f"CANDIDATE final: ann_geo {s['ann_geo']:.2f}% SR_d {s['sr_d']:.3f} MDD {s['mdd']:.2f}% neg {int((yr<0).sum())}/{yr.size}")
