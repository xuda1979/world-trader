"""Bulk-download SEC EDGAR companyfacts for all S&P 500 CIKs -> DuckDB.
Politely rate-limited (1.5s/symbol) per SEC fair-use guidance.
Caches raw JSONs to data/sec_fundamentals_cache and appends annual panels to a
parquet file, then upserts into DuckDB."""
import os, time, json, sys, duckdb, pandas as pd
import sec_fundamentals as sf

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, 'data/wh.duckdb')
CACHE_DIR = os.path.join(HERE, 'data/sec_fundamentals_cache')
PARQUET = os.path.join(HERE, 'data/fundamentals_annual.parquet')
os.makedirs(CACHE_DIR, exist_ok=True)

def extract_df(data, cik, symbol):
    usgaap = data.get('facts', {}).get('us-gaap', {})
    series = {t: sf._grab(usgaap, t) for t in sf.TAG_GROUPS}
    fys = set()
    for v in series.values():
        fys.update(v.keys())
    if not fys:
        return None
    fys = sorted(fys)
    out = pd.DataFrame({t: [series[t].get(fy) for fy in fys] for t in series},
                       index=pd.Index(fys, name='fy'))
    out['cik'] = cik; out['symbol'] = symbol
    return out

def to_rows(df, symbol, cik):
    rows = []
    for fy in df.index:
        r = {'symbol': symbol, 'cik': cik, 'fy': int(fy)}
        for t in df.columns:
            if t in ('symbol', 'cik'):
                continue
            v = df.loc[fy, t]
            try:
                fv = float(v)
                r[t] = None if fv != fv else fv
            except (ValueError, TypeError):
                r[t] = None
        rows.append(r)
    return rows

def main():
    con = duckdb.connect(DB)
    univ = con.execute("SELECT symbol, cik FROM universe ORDER BY symbol").fetchdf()
    all_rows = []
    ok = fail = skip = 0
    for i, (sym, cik) in enumerate(zip(univ['symbol'], univ['cik'])):
        cik = str(cik).zfill(10)
        f = os.path.join(CACHE_DIR, f'{sym}_{cik}.json')
        if os.path.exists(f):
            data = json.load(open(f))
            skip += 1
        else:
            try:
                data = sf.companyfacts(cik)
                json.dump(data, open(f, 'w'))
                ok += 1
            except Exception as e:
                fail += 1
                print(f'[{i}] {sym}: FAIL {e}')
                continue
            time.sleep(1.5)
        df = extract_df(data, cik, sym)
        if df is not None:
            all_rows.extend(to_rows(df, sym, cik))
        if (i + 1) % 50 == 0:
            print(f'[{i+1}/{len(univ)}] fetched={ok} cached={skip} fail={fail}')
            if all_rows:
                pd.DataFrame(all_rows).to_parquet(PARQUET)
    if all_rows:
        pd.DataFrame(all_rows).to_parquet(PARQUET)
    print(f'DONE fetched={ok} cached={skip} fail={fail}')

if __name__ == '__main__':
    main()
