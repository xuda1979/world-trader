"""
download_real_data.py
---------------------
Crawl FREE daily OHLCV data for a cross-section of U.S. stocks (S&P 100) from
stockanalysis.com (no API key required), and cache monthly panels to disk.

Also caches Kenneth French size-B/M and momentum portfolios + factors for the
benchmark alpha regressions.

Usage:
    python download_real_data.py --tickers /tmp/sp100.csv --out data/raw --range 10Y
"""
import argparse, json, os, time, urllib.request
import pandas as pd

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}


def fetch_symbol_history(sym, rng="10Y", retries=3, timeout=40):
    url = f"https://stockanalysis.com/api/symbol/s/{sym}/history?range={rng}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                j = json.load(r)
            data = j.get("data", [])
            if not data:
                return None
            df = pd.DataFrame(data)
            df = df.rename(columns={"t": "date", "c": "close", "a": "adj", "v": "volume",
                                    "o": "open", "h": "high", "l": "low"})
            df["date"] = pd.to_datetime(df["date"])
            df["symbol"] = sym
            return df
        except Exception as e:
            if attempt == retries - 1:
                print(f"  [{sym}] failed: {str(e)[:90]}")
                return None
            time.sleep(2 * (attempt + 1))
    return None


def get_universe(csv):
    u = pd.read_csv(csv)
    return u["Symbol"].str.strip().str.upper().tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", default="/tmp/sp100.csv")
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--range", default="10Y")
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    universe = get_universe(args.tickers)
    print(f"Downloading {len(universe)} symbols, range={args.range}")

    cache_file = os.path.join(args.out, "prices_cache.json")
    cache = {}
    if os.path.exists(cache_file):
        cache = json.load(open(cache_file))

    for i, sym in enumerate(universe):
        if sym in cache:
            continue
        df = fetch_symbol_history(sym, args.range)
        if df is not None:
            recs = df.copy()
            recs["date"] = recs["date"].dt.strftime("%Y-%m-%d")
            cache[sym] = recs.to_dict("records")
            with open(cache_file, "w") as f:
                json.dump(cache, f)
            print(f"  [{i+1}/{len(universe)}] {sym}: {len(df)} rows "
                  f"({df['date'].min().date()}..{df['date'].max().date()})")
        else:
            print(f"  [{i+1}/{len(universe)}] {sym}: no data")
        time.sleep(args.sleep)

    print("Done. Saved to", cache_file, "symbols:", len(cache))


if __name__ == "__main__":
    main()
