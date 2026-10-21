"""
sec_fundamentals.py
-------------------
Pull annual (10-K / FY) fundamental values from the FREE SEC EDGAR XBRL
companyfacts API and build a monthly-aligned fundamental panel in DuckDB.

Data are released under SEC terms (public domain). Free, no key required.
"""
import json, time, urllib.request, os, gzip
import pandas as pd

UA = {'User-Agent': 'world-trader research daxu@example.com'}

# canonical US-GAAP tags per characteristic
# (name -> list of candidate XBRL tags, first present wins)
TAG_GROUPS = {
    # balance sheet (instant)
    'equity':      ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
    'total_assets':['Assets', 'AssetsTotal'],
    'payables':    ['AccountsPayableCurrent', 'AccountsPayable'],
    'receivables': ['AccountsReceivableNetCurrent', 'AccountsReceivableNet'],
    'inventory':   ['InventoryNet', 'Inventory'],
    'ppent':       ['PropertyPlantAndEquipmentNet', 'PropertyPlantAndEquipmentNetIncludingFinanceLeaseRightOfUseAsset'],
    'current_assets': ['AssetsCurrent'],
    'current_liab':['LiabilitiesCurrent'],
    'cash':        ['CashAndCashEquivalentsAtCarryingValue'],
    'debt':        ['LongTermDebtCurrent', 'LongTermDebtNoncurrent'],
    'shares':      ['CommonStockSharesOutstanding'],
    'retained':    ['RetainedEarningsAccumulatedDeficit'],
    # income statement (duration)
    'net_income':  ['NetIncomeLoss', 'ProfitLoss'],
    'revenue':     ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'],
    'op_income':   ['OperatingIncomeLoss', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'],
    'dep_amort':   ['DepreciationDepletionAndAmortization', 'DepreciationAmortizationAndAccretionNet'],
    'cogs':        ['CostOfGoodsAndServicesSold'],
    'tax':         ['IncomeTaxExpenseBenefit'],
    'interest':    ['InterestExpense'],
    # cash flow (duration)
    'capex':       ['PaymentsToAcquirePropertyPlantAndEquipment'],
    'd_and_a':     ['DepreciationAmortizationAndAccretionNet'],
}


def _grab(usgaap, tag):
    """Return list of (fy, value) annual entries for tag (annual instant/duration)."""
    for cand in TAG_GROUPS[tag]:
        if cand in usgaap:
            units = usgaap[cand].get('units', {})
            # prefer USD dollar values; some tags also exist in 'shares'/'pure' units
            vals = (units.get('USD') or units.get('usd')
                    or units.get('shares') or units.get('pure') or [])
            out = {}
            for e in vals:
                form = e.get('form', '')
                # annual 10-K report
                if form not in ('10-K',):
                    continue
                fy = e.get('fy')
                if fy is None:
                    continue
                try:
                    val = float(e['val'])
                except (ValueError, TypeError):
                    continue  # non-numeric unit/value for this tag; skip
                if val != val:  # NaN
                    continue
                # for many tags entries repeat (e.g. from different filings); keep latest
                out[fy] = val
            return out
    return {}


def companyfacts(cik):
    """Fetch companyfacts JSON for a CIK (10-digit padded string)."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read()
        if raw[:2] == b'\x1f\x8b':          # gzip magic bytes
            raw = gzip.decompress(raw)
        return json.loads(raw)


def extract_annual(cik):
    """Return DataFrame indexed by fy of annual fundamentals for one CIK."""
    d = companyfacts(cik)
    usgaap = d.get('facts', {}).get('us-gaap', {})
    series = {}
    for tag in TAG_GROUPS:
        series[tag] = _grab(usgaap, tag)
    # union of fiscal years
    fys = set()
    for v in series.values():
        fys.update(v.keys())
    if not fys:
        return pd.DataFrame()
    fys = sorted(fys)
    out = pd.DataFrame({t: [series[t].get(fy, None) for fy in fys] for t in series}, index=pd.Index(fys, name='fy'))
    out['cik'] = cik
    return out


if __name__ == '__main__':
    import sys
    cik = sys.argv[1] if len(sys.argv) > 1 else '0000320193'
    df = extract_annual(cik)
    print(df.head(10).to_string())
    print('rows:', len(df))
