import os, csv, json, time

POLY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "polygon")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "pairs_xs_signals.json")
F = 40
H = 20
K = 2

SECTORS = {
    "Technology": ["AAPL","MSFT","GOOGL","META","AMZN","NVDA","AMD","AVGO","INTC","CRM","ADBE","ORCL","NOW","CSCO","TXN","QCOM","MU","AMAT","ARM","PLTR","SNOW","SHOP","DOCU"],
    "Financials": ["JPM","GS","MS","WFC","BAC","SCHW","V","MA"],
    "Healthcare": ["UNH","JNJ","LLY","PFE","ABT","TMO","ABBV","MRK","AMGN","DHR"],
    "Consumer Disc": ["HD","LOW","NKE","MCD","SBUX","TJX","COST","WMT","TGT"],
    "Consumer Staples": ["KO","PEP","CL","PG"],
    "Energy": ["XOM","COP"],
    "Industrials": ["BA","GE","UNP","UPS","LMT","RTX"],
    "Communication": ["T","VZ","DIS","CMCSA"],
    "Utilities": ["NEE","DUK","SO"],
    "Real Estate": ["AMT","PLD"],
}
def load_close(sym):
    fp = os.path.join(POLY, sym + '.csv')
    if not os.path.exists(fp):
        return None
    closes = []
    with open(fp) as fh:
        for row in csv.DictReader(fh):
            try:
                closes.append(float(row['close']))
            except (ValueError, KeyError):
                continue
    return closes if len(closes) >= 100 else None

def build_matrix(sectors):
    raw = {}
    for syms in sectors.values():
        for sym in syms:
            if sym not in raw:
                d = load_close(sym)
                if d:
                    raw[sym] = d
    n = min(len(v) for v in raw.values())
    cal = list(range(n))
    mat = {i: {s: raw[s][i] for s in raw} for i in range(n)}
    return cal, mat, raw

def gen_signals(cal, mat, sectors):
    n = len(cal)
    sigs = {}
    for sec_name, syms in sectors.items():
        avail = [s for s in syms if s in mat[n - 1]]
        if len(avail) < 2 * K:
            continue
        form_rets = {}
        prices = {}
        for s in avail:
            p0 = mat[n - 1 - F][s]
            p1 = mat[n - 1][s]
            if p0 > 0:
                form_rets[s] = p1 / p0 - 1.0
                prices[s] = p1
        ranked = sorted(form_rets, key=form_rets.get, reverse=True)
        if len(ranked) < 2 * K:
            continue
        winners = ranked[:K]
        losers = ranked[-K:]
        ss = {'long': [], 'short': []}
        for rank, sym in enumerate(ranked):
            entry = {'symbol': sym, 'ret_pct': round(form_rets[sym] * 100, 2),
                     'price': round(prices[sym], 2), 'rank': rank + 1}
            if sym in winners:
                ss['long'].append(entry)
            elif sym in losers:
                ss['short'].append(entry)
        sigs[sec_name] = ss
    return sigs

def main():
    print('Cross-Sectional Momentum Signals (%dd formation, top-%d):' % (F, K))
    cal, mat, _ = build_matrix(SECTORS)
    sigs = gen_signals(cal, mat, SECTORS)
    out = {'generated': time.strftime('%Y-%m-%d %H:%M:%S %Z'),
           'config': {'formation_days': F, 'hold_days': H, 'top_k': K},
           'sectors': sigs}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as fh:
        json.dump(out, fh, indent=2)
    for sec in sorted(sigs):
        print('  %s:' % sec)
        for s in sigs[sec]['long']:
            print('    LONG  %-6s  %+6.1f%%  $%.2f' % (s['symbol'], s['ret_pct'], s['price']))
        for s in sigs[sec]['short']:
            print('    SHORT %-6s  %+6.1f%%  $%.2f' % (s['symbol'], s['ret_pct'], s['price']))
    tl = sum(len(s['long']) for s in sigs.values())
    ts = sum(len(s['short']) for s in sigs.values())
    print()
    print('  Portfolio: %d long + %d short across %d sectors' % (tl, ts, len(sigs)))
    print('  Saved to %s' % OUT)

if __name__ == '__main__':
    main()
