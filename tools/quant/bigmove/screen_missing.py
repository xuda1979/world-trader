"""Screen full local universe for Buffett-quality names missing from the 146 list."""
import pandas as pd, numpy as np, json

UNIV = set("""AAPL MSFT GOOGL AMZN NVDA META AVGO TSLA BRK-B JPM V MA UNH LLY XOM PG JNJ HD
COST ABBV MRK CVX KO PEP WMT MCD CRM ORCL AMD INTC QCOM TXN ACN ADBE CSCO INTU NFLX CMCSA
DIS AMGN GILD BIIB ISRG UBER SHOP NOW CAT DE BA GE HON MMM UPS FDX NKE SBUX TGT TJX ROST
EL EMR ITW PH PCAR WM RSG LMT RTX NOC GD LH HCA MDT BSX SYK ABT TMO DHR BDX EW ZTS VRTX
REGN MRNA ABNB ADI APD LIN SHW ECL DOW DD NEE DUK SO D AEP EXC ED C BAC WFC GS MS SCHW
PNC USB TFC AXP BLK ICE MCO SPGI CB PGR ALL AIG MET TRV PRU KHC MDLZ HSY GIS CPB KMB CL
MCK ABC COR CARR DELL GWW PAYX ADP IT VRSK IR MMC AJG WTW CTAS FAST GRMN CHD CLX""".split())

# --- Panel screen at 2026-07-31 (last broad month with prices) ---
df = pd.read_parquet('data/edgar_chars.parquet')
df['month'] = pd.to_datetime(df['month'])
snap = df[df['month'] == '2026-07-31'].copy()
snap['tot_mcap'] = snap['shares'] * snap['mcap']  # mcap col = share price; size = ln(shares*price)
p = snap[(snap.tot_mcap >= 40e9) & (snap.net_income > 0) & (snap.roe.notna()) &
         (snap.roe >= 0.15) & (snap.leverage.fillna(0) <= 0.5)]
p = p[~p.ticker.isin(UNIV)].sort_values('tot_mcap', ascending=False)
print('panel candidates (excl 146):', len(p))
print(p[['ticker', 'tot_mcap', 'roe', 'net_income', 'book_equity', 'leverage']].to_string())
p.to_csv('data/screen_panel_candidates.csv', index=False)

# --- Extended mcap map: finnhub caches + gkx + panel ---
fh_prof = json.load(open('data/finnhub_profiles.json'))
fh_met = json.load(open('data/finnhub_metrics.json'))
g = pd.read_parquet('data/gkx_monthly_panel.parquet')
g['month'] = pd.to_datetime(g['month'])
mcap_map = {}
for k, v in fh_prof.items():
    if v.get('mcap_fh'):
        mcap_map[k] = max(mcap_map.get(k, 0), v['mcap_fh'] * 1e6)
for k, v in fh_met.items():
    if v.get('marketCapitalization'):
        mcap_map[k] = max(mcap_map.get(k, 0), v['marketCapitalization'] * 1e6)
gm = g[g['marketCap'].notna()].sort_values('month').groupby('ticker').tail(1)
for _, r in gm.iterrows():
    mcap_map[r['ticker']] = max(mcap_map.get(r['ticker'], 0), r['marketCap'] * 1e6)
# gkx log_mcap quarter months (exp -> $)
gl = g[g['log_mcap'].notna()].sort_values('month').groupby('ticker').tail(1)
for _, r in gl.iterrows():
    mcap_map[r['ticker']] = max(mcap_map.get(r['ticker'], 0), float(np.exp(r['log_mcap'])))
# panel totals (most precise: shares*price at 2026-07-31)
for _, r in snap.iterrows():
    if np.isfinite(r['tot_mcap']):
        mcap_map[r['ticker']] = max(mcap_map.get(r['ticker'], 0), r['tot_mcap'])

# sanity: MSFT should be ~3.5T in $ units
print('\nmcap units sanity (expect $3.4-3.9T):')
for t in ['MSFT', 'AAPL', 'NVDA', 'JPM']:
    print(f'  {t}: ${mcap_map.get(t, 0)/1e12:.2f}T')

big = {t: v for t, v in mcap_map.items() if v >= 40e9}
print('\nnames with mcap >= 40B:', len(big))

# fundamentals for extended names from full_cache
fc = json.load(open('data/full_cache.json'))
ext = {t: v for t, v in big.items() if t not in set(snap['ticker'])}
print('extended (>=40B, not in panel):', len(ext))
json.dump({t: {'mcap': mcap_map[t], 'book_equity': fc.get(t, {}).get('book_equity', [None])[0],
               'net_income': fc.get(t, {}).get('net_income', [None])[0]} for t in ext},
          open('data/screen_extended.json', 'w'), indent=1)
for t in sorted(ext, key=lambda t: -ext[t]):
    print(f'  {t:6s} ${ext[t]/1e9:6.0f}B')
