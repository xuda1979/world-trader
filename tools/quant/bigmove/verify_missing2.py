"""Final verification: FY margins/ROE from companyfacts + mcap merge + gates."""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FULL = os.path.join(HERE, 'data', 'edgar_facts_full')

REV_TAGS = ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues',
            'SalesRevenueNet', 'RevenueFromContractWithCustomerIncludingAssessedTax',
            'RevenuesNetOfInterestExpense', 'RevenuesAndOperatingLeaseRevenue']
NI_TAG, EQ_TAG, EPS_TAG = 'NetIncomeLoss', 'StockholdersEquity', 'EarningsPerShareDiluted'

def annual_rows(d, tag):
    node = d.get('facts', {}).get('us-gaap', {}).get(tag)
    if not node:
        return {}
    out = {}
    for u, vals in node.get('units', {}).items():
        if 'USD' not in u:
            continue
        for v in vals:
            if '10-K' not in v.get('form', '') and v.get('fp', '') != 'FY':
                continue
            try:
                val = float(v.get('val'))
            except (TypeError, ValueError):
                continue
            out[v.get('end')] = val
    return out

def latest_equity(d):
    node = d.get('facts', {}).get('us-gaap', {}).get(EQ_TAG)
    if not node:
        return None, None
    best = None
    for u, vals in node.get('units', {}).items():
        if 'USD' not in u:
            continue
        for v in vals:
            try:
                val = float(v.get('val'))
            except (TypeError, ValueError):
                continue
            filed = v.get('filed') or v.get('end')
            if best is None or filed > best[1]:
                best = (val, filed, v.get('end'))
    return (best[0], best[2]) if best else (None, None)

def pick_rev_tag(d, fy_end):
    """Revenue tag whose annual series covers the latest FY; prefer more years."""
    fy_ts = pd.Timestamp(fy_end)
    best = None
    for tag in REV_TAGS:
        m = annual_rows(d, tag)
        if not m:
            continue
        last = max(m.keys())
        if abs((pd.Timestamp(last) - fy_ts).days) > 120:
            continue
        if best is None or len(m) > best[1]:
            best = (tag, len(m), m)
    return best if best else (None, None, {})

def analyze(t):
    fp = os.path.join(FULL, f'{t}.json')
    if not os.path.exists(fp):
        return {'ticker': t, 'error': 'no companyfacts file'}
    d = json.load(open(fp))
    ni = annual_rows(d, NI_TAG)
    if not ni:
        return {'ticker': t, 'error': 'no annual NetIncomeLoss facts'}
    fy_end = max(ni.keys())
    fy = int(fy_end[:4])
    ni_fy = ni[fy_end]
    rev_tag, n_rev_yrs, rev = pick_rev_tag(d, fy_end)
    eq, eq_period = latest_equity(d)
    eps = annual_rows(d, EPS_TAG)
    eps_years = {int(k[:4]): v for k, v in eps.items()}
    win = range(fy - 9, fy + 1)
    eps_n = sum(1 for y in win if y in eps_years)
    eps_pos = sum(1 for y in win if y in eps_years and eps_years[y] > 0)
    stale = fy_end < '2024-01-01'
    roe = ni_fy / eq if (eq and eq > 0) else np.nan
    rev_fy = rev.get(fy_end) if rev else None
    margin = ni_fy / rev_fy if (rev_fy and rev_fy > 0) else np.nan
    rev_keys = sorted(rev.keys()) if rev else []
    growth = None
    if len(rev_keys) >= 2:
        g0, g1 = rev[rev_keys[0]], rev[rev_keys[-1]]
        if g0 and g1 and g0 > 0:
            span = (pd.Timestamp(rev_keys[-1]) - pd.Timestamp(rev_keys[0])).days / 365.25
            growth = (g1 / g0) ** (1 / max(span, 1)) - 1
    return {'ticker': t, 'name': d.get('entityName'), 'fy_end': fy_end, 'fy_ni': ni_fy,
            'fy_rev': rev_fy, 'rev_tag': rev_tag, 'equity': eq, 'eq_period': eq_period,
            'roe_fy': roe, 'margin_fy': margin, 'eps_n': eps_n, 'eps_pos': eps_pos,
            'rev_yr0': rev_keys[0] if rev_keys else None, 'rev_years': len(rev_keys),
            'rev_growth_cagr': growth, 'stale': stale, 'error': None}

if __name__ == '__main__':
    mcap_map = json.load(open('data/screen_mcap_map.json'))
    cand = pd.read_csv('data/screen_panel_candidates.csv')
    ext = json.load(open('data/screen_extended.json'))
    drop146 = set('GS PEP EMR MMC PCAR AEP PAYX ED'.split())
    foreign = set('AAIGF AGPPF AGRPF ABLZF AACAF AAUKF'.split())
    no_price = ['FICO', 'OTIS', 'AME', 'DHI', 'KLAC', 'ANET', 'ADSK', 'MCHP', 'TTD',
                'ORLY', 'ROP', 'VEEV', 'STZ', 'ODFL', 'PHM', 'MSCI', 'EQIX', 'SNPS',
                'CDNS', 'CPRT', 'GWW', 'FAST', 'KLAC']
    pool = sorted(set(list(cand['ticker']) + [t for t in ext if t not in drop146 and t not in foreign] + no_price))
    rows = []
    for t in pool:
        r = analyze(t)
        r['mcap'] = mcap_map.get(t)
        r['in_panel'] = t in set(cand['ticker'])
        rows.append(r)
    out = pd.DataFrame(rows)
    out.to_json('data/verify_missing2.json', orient='records', indent=1)
    for _, r in out.iterrows():
        if r['error']:
            print(f"{r['ticker']:5s} {r['error']}")
            continue
        mc = f"${r['mcap']/1e9:.0f}B" if r['mcap'] else 'no-price'
        rev = r['fy_rev'] / 1e9 if r['fy_rev'] else np.nan
        print(f"{r['ticker']:5s} {mc:>8s} fy={r['fy_end']} NI={r['fy_ni']/1e9:6.1f}B rev={rev:7.1f}B "
              f"roe={r['roe_fy']:.2f} mg={r['margin_fy']:.2f} eps={r['eps_pos']}/{r['eps_n']} "
              f"g={r['rev_growth_cagr']*100 if r['rev_growth_cagr'] is not None else float('nan'):.1f}% "
              f"[{r['rev_years']}y] tag={r['rev_tag']} stale={r['stale']}")
