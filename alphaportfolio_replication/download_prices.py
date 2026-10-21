"""Download daily OHLCV for the full S&P 500 universe from stockanalysis.com
(no key), store into DuckDB. Caches JSON per symbol."""
import os, time, json, urllib.request, duckdb, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, 'data/wh.duckdb')
DB_P = os.path.join(HERE, 'data/wh_prices.duckdb')
SP500_CSV = '/tmp/sp500.csv'
CACHE_DIR = os.path.join(HERE, 'data/price_cache')
os.makedirs(CACHE_DIR, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0 Safari/537.36'}

def fetch(sym):
    url = f"https://stockanalysis.com/api/symbol/s/{sym}/history?range=10Y"
    req = urllib.request.Request(url, headers=UA)
    d = json.load(urllib.request.urlopen(req, timeout=30))
    return d.get('data') or []

def main():
    con = duckdb.connect(DB_P)
    import pandas as pd
    syms = list(pd.read_csv(SP500_CSV)['Symbol'])
    allrows = []
    ok = fail = skip = 0
    for i, sym in enumerate(syms):
        f = os.path.join(CACHE_DIR, f'{sym}.json')
        if os.path.exists(f):
            try:
                recs = json.load(open(f))
                skip += 1
            except Exception:
                recs = fetch(sym); ok += 1; time.sleep(0.25)
                json.dump(recs, open(f, 'w'))
        else:
            try:
                recs = fetch(sym); ok += 1; time.sleep(0.25)
                json.dump(recs, open(f, 'w'))
            except Exception as e:
                fail += 1
                print(f'[{i}] {sym}: FAIL {e}')
                recs = []
        for r in recs:
            allrows.append({'symbol': sym, 'date': r['t'],
                            'close': r.get('c'), 'adj': r.get('a'),
                            'open': r.get('o'), 'high': r.get('h'),
                            'low': r.get('l'), 'volume': r.get('v')})
        if (i+1) % 100 == 0:
            print(f'[{i+1}/{len(syms)}] fetched={ok} cached={skip} fail={fail}')
    if allrows:
        con.execute("DROP TABLE IF EXISTS daily_prices")
        con.execute("CREATE TABLE daily_prices (symbol VARCHAR, date DATE, close DOUBLE, adj DOUBLE, open DOUBLE, high DOUBLE, low DOUBLE, volume BIGINT)")
        con.register('pr', pd.DataFrame(allrows))
        con.execute("INSERT INTO daily_prices SELECT * FROM pr")
        n = con.execute("SELECT COUNT(*) FROM daily_prices").fetchone()[0]
        print('daily_prices rows:', n)
    print(f'DONE fetched={ok} cached={skip} fail={fail}')

if __name__ == '__main__':
    main()
