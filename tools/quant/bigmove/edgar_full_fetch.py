"""Fetch SEC EDGAR companyfacts for the ENTIRE current-filer population
(SEC company_tickers.json ∪ company_tickers_exchange.json, ~10.4k unique CIKs),
FREE data. The existing edgar_facts/ corpus only covers ~600 names WITH local
prices — Buffett's micro-cap "无人区" (the other ~10k filers) was never
fetched. This closes that gap.

Resumable + rate-limited (SEC polite limit 10 req/s; we do 2/s with retry
backoff). Raw payloads go to data/edgar_facts_full/{TICKER}.json so
parse_facts() in edgar_fundamentals.py can build the point-in-time panel
unchanged. Progress in data/edgar_full_progress.json.

Usage:
    python edgar_full_fetch.py [--limit N]   # N = smoke-test first N tickers
"""
from __future__ import annotations
import json, os, sys, time, re, threading
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "edgar_facts_full")
PROG = os.path.join(HERE, "data", "edgar_full_progress.json")
UA = "Mozilla/5.0 (trade-scout fetcher; research only)"
RPS = 2.0    # per-worker request spacing
WORKERS = 4  # aggregate ~8 req/s; SEC fair-access limit is 10/s

def fetch_one(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def build_pairs():
    """All current SEC filers with tickers, deduped by CIK. Prefer the ticker
    spelling that appears in the repo's us_stock_list when both exist."""
    norm = lambda s: re.sub(r"[^A-Z0-9]", "", s.upper())
    out = {}  # cik -> ticker
    for fn, fields in (("sec_company_tickers.json", "ct"),
                       ("sec_company_tickers_exchange.json", "ex")):
        fp = os.path.join(HERE, "data", fn)
        if not os.path.exists(fp):
            continue
        d = json.load(open(fp))
        rows = d["data"] if isinstance(d, dict) and "data" in d else [
            [v["cik_str"], v.get("title"), v["ticker"], ""] for v in d.values()]
        for r in rows:
            cik, ticker = r[0], r[2]
            if isinstance(cik, str):
                cik = int(cik)
            out.setdefault(cik, ticker.upper())
    lst = json.load(open(os.path.join(HERE, "data", "us_stock_list.json")))
    want = {norm(t) for t in lst}
    # prefer the repo's ticker spelling for its own names
    for cik, tick in list(out.items()):
        n = norm(tick)
        if n in want:
            continue
        hits = [t for t in lst if norm(t) == n]
        if hits:
            out[cik] = hits[0].upper()
    pairs = list(out.items())
    # deterministic shuffle: unbiased sample of the population in every early
    # batch (default CIK order fetches megacaps first — useless for micro-cap
    # hunting). Same seed on resume keeps the same remaining order.
    rng = __import__("random").Random(42)
    rng.shuffle(pairs)
    return pairs

def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    pairs = build_pairs()
    if limit:
        pairs = pairs[:limit]
    os.makedirs(OUT, exist_ok=True)
    done = {f[:-5] for f in os.listdir(OUT) if f.endswith(".json")}
    prog = {"total": len(pairs), "done": len(done), "errors": [], "started": time.time()}
    if os.path.exists(PROG):
        try:
            prog = json.load(open(PROG))
        except Exception:
            pass
    errs = set(prog.get("errors", []))
    t0 = time.time()
    lock = threading.Lock()
    counters = {"n": 0}

    def fetch_item(item):
        cik, t = item
        if t in done or t in errs:
            return
        fp = os.path.join(OUT, f"{t}.json")
        last_err = None
        for attempt in range(4):
            try:
                raw = fetch_one(cik)
                with open(fp, "wb") as f:
                    f.write(raw)
                with lock:
                    done.add(t)
                break
            except urllib.error.HTTPError as e:
                last_err = f"HTTP{e.code}"
                if e.code == 404:          # no XBRL on file (delisted/pre-XBRL)
                    with lock:
                        errs.add(t)
                    return
                time.sleep(2 * (attempt + 1))  # 429 / 5xx backoff
            except Exception as e:
                last_err = f"{type(e).__name__}: {str(e)[:80]}"
                time.sleep(1)
        else:
            with lock:  # all retries exhausted — record and skip in later runs
                errs.add(t)
        time.sleep(1.0 / RPS)
        with lock:
            counters["n"] += 1
            if counters["n"] % 200 == 0:
                prog.update({"done": len(done), "errors": sorted(errs),
                             "elapsed_s": round(time.time() - t0)})
                json.dump(prog, open(PROG, "w"))
                print(f"  {len(done)}/{len(pairs)} done ({len(errs)} errors), "
                      f"{round((time.time()-t0)/60,1)} min", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(fetch_item, pairs))
    prog.update({"done": len(done), "errors": sorted(errs),
                 "elapsed_s": round(time.time() - t0)})
    json.dump(prog, open(PROG, "w"))
    print(f"fetch finished: {len(done)}/{len(pairs)} done, {len(errs)} errors")

if __name__ == "__main__":
    main()
