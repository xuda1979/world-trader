"""Incremental Graham net-net (烟蒂股) screen over the FULL SEC companyfacts
corpus (data/edgar_facts_full/) — the complete current-filer population
(~8k names) that iter1's buffett_smallcap_screener.py never saw (it only
covered ~530 names with local prices). This is the definitive answer to
"are there ANY net-nets in the entire free-data universe?"

Point-in-time-safe for the LIVE screen: uses the most recent fact FILED
before today (no lookahead). NCAV per the iter1 convention:
    NCAV = cur_assets - (assets - book_equity)      (= current assets - total liab)
    net-net trigger: market_cap < NCAV              (Buffett's cigar-butt rule)

Prices: (a) local price panel when the ticker has history; (b) yfinance
batch otherwise, cached to data/full_prices.json (capped per run — the
fetch job at 2 req/s + yfinance at ~1 req/s stays polite).

Run each loop fire while edgar_full_fetch.py fills the corpus.
Output: data/full_screen.json + console table.
"""
from __future__ import annotations
import os, sys, json, time, glob, urllib.request
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(HERE)
from edgar_fundamentals import parse_facts

FULL = os.path.join(HERE, "data", "edgar_facts_full")
CACHE = os.path.join(HERE, "data", "full_cache.json")
PRICE_CACHE = os.path.join(HERE, "data", "full_prices.json")
OUT = os.path.join(HERE, "data", "full_screen.json")
MAX_PRICE_FETCH = 50  # new Finnhub/yfinance prices per run

def load_local_prices():
    try:
        from pipeline_common import load_ohlcv
        P = load_ohlcv(min_history=200)
        return P["close"].iloc[-1].dropna().to_dict()
    except Exception as e:
        print(f"  (local price panel unavailable: {e})")
        return {}

def main():
    files = sorted(glob.glob(os.path.join(FULL, "*.json")))
    if not files:
        print("no files yet in edgar_facts_full/")
        return
    # reads the incremental cache built by build_full_cache.py (run it first;
    # re-parsing raw companyfacts per fire is too slow once corpus is big)
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE))
        except Exception:
            pass
    rows = []
    for t, rec in cache.items():
        ca = rec.get("cur_assets"); a = rec.get("assets"); be = rec.get("book_equity")
        sh = rec.get("shares"); cash = rec.get("cash")
        if not (ca and a and be):
            continue  # needs all three NCAV inputs
        ncav = ca[0] - (a[0] - be[0])
        # staleness: NCAV report period more than 18 months old (e.g. foreign
        # filers that switched IFRS tags, or post-hoc balance-sheet gaps) ->
        # misaligned mcap/NCAV false positives (DDI lesson)
        p = rec.get("ncav_period")
        stale = p is None or (pd.Timestamp(p) < pd.Timestamp.today() - pd.Timedelta(days=548))
        # shares staleness: cover-page share count filed long before the NCAV
        # report (ACMR: shares from 2019 vs 2026-06-30 balance sheet) -> mcap
        # wildly wrong. Flag if shares filed > 400 days before report period.
        shares_stale = bool(sh) and p is not None and bool(sh[1]) and (
            pd.Timestamp(sh[1]) < pd.Timestamp(p) - pd.Timedelta(days=400))
        rows.append({"ticker": t, "ncav": ncav,
                     "shares": sh[0] if sh else np.nan,
                     "cash": cash[0] if cash else np.nan,
                     "ncav_period": p, "stale": stale,
                     "shares_stale": shares_stale})
    df = pd.DataFrame(rows)
    # shares sanity: <10k shares on a listed company = parse artifact (FOXA
    # parsed as 1 share -> mcap = price); would poison every ratio
    n_bad = int((df["shares"] < 1e4).sum())
    df = df[df["shares"] >= 1e4].copy()
    print(f"{len(cache)} cached of {len(files)} files; "
          f"NCAV-input names: {len(df)} (shares-artifacts dropped: {n_bad}), "
          f"NCAV>0: {int((df.ncav > 0).sum())}, "
          f"stale: {int(df.stale.sum())}")

    cand = df[df["ncav"] > 0].copy()
    if len(cand) == 0:
        json.dump({"as_of": str(pd.Timestamp.today().date()), "n_files": len(files),
                   "n_parsed": len(df), "n_candidates": 0}, open(OUT, "w"))
        print("no NCAV>0 candidates yet")
        return

    # prices: local panel first, yfinance for the rest (capped)
    local = load_local_prices()
    cand["price"] = cand["ticker"].map(local)
    cache = {}
    if os.path.exists(PRICE_CACHE):
        try:
            cache = json.load(open(PRICE_CACHE))
        except Exception:
            pass
    to_fetch = cand[cand["price"].isna() & cand["ticker"].notna()]
    to_fetch = to_fetch.sort_values("ncav", ascending=False).head(MAX_PRICE_FETCH)
    if len(to_fetch):
        got = 0
        # primary: Finnhub quote (60 req/min free tier; key in .env.local)
        fk = None
        for p in ("/Users/daxu/software/world-trader/.env.local",
                  "/Users/daxu/software/world-trader/.env"):
            if os.path.exists(p):
                for line in open(p):
                    if line.startswith("FINNHUB_KEY="):
                        fk = line.strip().split("=", 1)[1]
                        break
            if fk:
                break
        if not fk:
            print("  no FINNHUB_KEY -> price leg disabled")
        for t in to_fetch["ticker"]:
            if t in cache:
                continue
            if fk:
                try:
                    q = json.load(urllib.request.urlopen(
                        f"https://finnhub.io/api/v1/quote?symbol={t}&token={fk}",
                        timeout=15))
                    c = q.get("c")
                    if c and c > 0:
                        cache[t] = float(c)
                        got += 1
                except Exception:
                    pass
            time.sleep(1.1)  # 60/min cap
        if got == 0 and fk:
            # fallback: yfinance (may be IP-throttled)
            import yfinance as yf
            for t in to_fetch["ticker"]:
                if t in cache:
                    continue
                try:
                    h = yf.Ticker(t).history(period="5d", interval="1d")
                    if len(h):
                        cache[t] = float(h["Close"].iloc[-1])
                        got += 1
                except Exception:
                    pass
                time.sleep(0.6)
        print(f"  got {got} new prices", flush=True)
        json.dump(cache, open(PRICE_CACHE, "w"))
    cand["price"] = cand["price"].fillna(cand["ticker"].map(cache))
    priced = cand[cand["price"].notna() & cand["price"] > 0].copy()
    priced["mcap"] = priced["shares"] * priced["price"]
    priced["ncav_mc_ratio"] = priced["ncav"] / priced["mcap"]
    priced["netnet"] = (priced["ncav_mc_ratio"] > 1.0) & ~priced["stale"]
    priced = priced.sort_values("ncav_mc_ratio", ascending=False)

    # absurd ratios (>20x) = almost certainly XBRL tag artifacts (UPC:
    # $53.6B cur_assets for a 563K-share micro pharma). Flag, don't count.
    priced["artifact"] = priced["ncav_mc_ratio"] > 20.0
    priced["netnet"] = priced["netnet"] & ~priced["shares_stale"].fillna(False)
    nn = priced[priced["netnet"] & ~priced["artifact"]]
    artifacts = priced[priced["artifact"]]
    stale_nn = priced[(priced["ncav_mc_ratio"] > 1.0) & (priced["stale"] | priced["shares_stale"].fillna(False))]
    print(f"priced: {len(priced)} | NET-NETS (clean): {len(nn)} | "
          f"artifacts: {len(artifacts)} | stale-flagged: {len(stale_nn)}")
    if len(artifacts):
        print(f"  artifact suspects: {artifacts[['ticker','ncav_mc_ratio']].head(6).to_string(index=False)}")
    if len(priced):
        r = priced["ncav_mc_ratio"]
        buckets = [">2x", "1-2x", "0.5-1x", "<0.5x"]
        counts = [int((r > 2).sum()), int(((r > 1) & (r <= 2)).sum()),
                  int(((r > 0.5) & (r <= 1)).sum()), int((r <= 0.5).sum())]
        print("  ratio dist:", dict(zip(buckets, counts)))
    cols = ["ticker", "price", "mcap", "ncav", "ncav_mc_ratio", "cash"]
    if len(nn):
        with pd.option_context("display.float_format",
                               lambda x: f"{x:,.0f}" if abs(x) >= 1e3 else f"{x:.2f}",
                               "display.max_columns", None, "display.width", 220):
            print(nn[cols].head(20).to_string(index=False))
    if len(stale_nn):
        print(f"stale-flagged net-net-looking (period {stale_nn.ncav_period.tolist()[:5]}):")
        with pd.option_context("display.float_format",
                               lambda x: f"{x:,.0f}" if abs(x) >= 1e3 else f"{x:.2f}",
                               "display.max_columns", None, "display.width", 220):
            print(stale_nn[cols].head(10).to_string(index=False))
    # near-misses (0.5-1.0) worth price-verification
    near = priced[(priced.ncav_mc_ratio > 0.5) & (priced.ncav_mc_ratio <= 1.0)]
    print(f"near-misses (0.5-1.0x NCAV): {len(near)}")
    if len(near):
        with pd.option_context("display.float_format",
                               lambda x: f"{x:,.0f}" if abs(x) >= 1e3 else f"{x:.2f}",
                               "display.max_columns", None, "display.width", 220):
            print(near[cols].head(10).to_string(index=False))
    json.dump({"as_of": str(pd.Timestamp.today().date()), "n_files": len(files),
               "n_parsed": len(df), "n_candidates": int((df.ncav > 0).sum()),
               "n_priced": len(priced), "n_netnets": len(nn),
               "netnets": nn[cols].head(50).to_dict("records"),
               "near_misses": near[cols].head(50).to_dict("records")},
              open(OUT, "w"), indent=1, default=float)
    print(f"wrote {OUT}")

if __name__ == "__main__":
    main()
