"""Merger-arbitrage (workouts) screen on free SEC data — Buffett 策略三.

Pipeline (built incrementally across /loop fires):
  1. EFTS full-text search: 8-Ks mentioning "merger agreement" (paginated,
     1y window) -> data/arb_hits.json
  2. Fetch each 8-K main document; extract deal terms: target ticker,
     per-share price, close date (regex on text)
  3. Polygon prices -> spread = (deal_price/price - 1) and convergence
     over time after the announcement

This fire: step 1 + a sample of step 2 (term extraction quality check).
"""
from __future__ import annotations
import json, os, sys, time, re, urllib.request
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(HERE)
UA = "Mozilla/5.0 (trade-scout fetcher; research only)"

OUT = "data/arb_hits.json"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def collect(start="2025-08-01", end="2026-08-20", max_pages=80):
    hits, seen = [], set()
    for page in range(max_pages):
        url = (f"https://efts.sec.gov/LATEST/search-index?q=%22merger%20agreement%22"
               f"&forms=8-K&dateRange=custom&startdt={start}&enddt={end}"
               f"&from={page*100}&size=100")
        batch = None
        for attempt in range(4):
            try:
                d = get(url)
                batch = d.get("hits", {}).get("hits", [])
                break
            except Exception:
                time.sleep(3 * (attempt + 1))
        if batch is None:
            print(f"  page {page}: giving up after retries; stopping", flush=True)
            break
        if not batch:
            break
        for h in batch:
            s = h["_source"]
            adsh = s.get("adsh")
            if adsh and adsh not in seen:
                seen.add(adsh)
                hits.append({"adsh": adsh, "file_date": s.get("file_date"),
                             "form": s.get("form"), "items": s.get("items"),
                             "name": (s.get("display_names") or [""])[0],
                             "ciks": s.get("ciks")})
        if page % 10 == 0:
            json.dump(hits, open(OUT, "w"), indent=1)  # incremental save
        print(f"  page {page}: {len(batch)} hits, total {len(hits)}", flush=True)
        time.sleep(0.5)
    json.dump(hits, open(OUT, "w"), indent=1)
    print(f"collected {len(hits)} 8-Ks -> {OUT}")
    return hits

def fetch_8k_text(adsh, ciks):
    """Main document text of an 8-K from its index page."""
    cik = str(ciks[0] if ciks else 0).zfill(10)
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-', '')}/"
    idx = get(url + "index.json")
    docs = [d for d in idx.get("directory", {}).get("item", [])
            if d["name"].lower().endswith(".htm")]
    docs.sort(key=lambda d: d.get("size", 0), reverse=True)
    main = next((d for d in docs if "8k" in d["name"].lower()), docs[0] if docs else None)
    if not main:
        return None
    txt_url = url + main["name"]
    req = urllib.request.Request(txt_url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8", "replace")
    return re.sub(r"<[^>]+>", " ", raw)

def extract_terms(text):
    """Deal-term extraction: per-share price (par-value boilerplate filtered),
    target/entity name, deal context. Returns dict + ticker set."""
    terms = {}
    # all per-share candidates with 60 chars of context
    cands = []
    for m in re.finditer(r"\$\s*([\d,]+\.?\d*)\s*per share", text):
        ctx = text[max(0, m.start() - 60):m.end() + 30].lower()
        if "par value" in ctx or "par amount" in ctx:
            continue  # legal boilerplate
        cands.append(float(m.group(1).replace(",", "")))
    if cands:
        # the real deal price is the material number; 0.01-style values are
        # notional/indemnity language — take the largest non-trivial one
        big = [c for c in cands if c >= 0.5]
        terms["deal_ps"] = max(big) if big else max(cands)
    ticks = set(re.findall(r"\b([A-Z]{2,5})\b", text))
    return terms, ticks

DEALS_FILE = "data/arb_deals.json"

def ticker_of(name):
    """First parenthesized all-caps token in the display name (SOUN, SOUNW -> SOUN)."""
    m = re.search(r"\(([A-Z][A-Z0-9]*)(?:,\s*[A-Z0-9]+)*\)", name)
    return m.group(1) if m else None

def process_batch(hits, start=0, n=40, out=DEALS_FILE):
    """Fetch filing texts, extract deal terms, append to the deals file."""
    deals = []
    if os.path.exists(out):
        try:
            deals = json.load(open(out))
        except Exception:
            pass
    seen = {d["adsh"] for d in deals}
    done = 0
    for h in hits[start:start + n]:
        if h["adsh"] in seen:
            continue
        try:
            txt = fetch_8k_text(h["adsh"], h.get("ciks") or [])
        except Exception:
            txt = None
        if txt:
            t, _ = extract_terms(txt)
            if t.get("deal_ps"):
                deals.append({"adsh": h["adsh"], "file_date": h["file_date"],
                              "name": h["name"][:60], "ticker": ticker_of(h["name"]),
                              "deal_ps": t["deal_ps"]})
                seen.add(h["adsh"])
        done += 1
        if done % 10 == 0:
            json.dump(deals, open(out, "w"), indent=1)
        time.sleep(0.25)
    json.dump(deals, open(out, "w"), indent=1)
    print(f"processed {done} filings; {len(deals)} deals total -> {out}")
    return deals

def spreads(deals_file=DEALS_FILE, out="data/arb_spreads.json"):
    """Current price + spread for every deal with a ticker (Polygon, cached)."""
    import urllib.request as u
    PK = None
    for p in ("/Users/daxu/software/world-trader/.env.local",
              "/Users/daxu/software/world-trader/.env"):
        if os.path.exists(p):
            for line in open(p):
                if line.startswith("POLYGON_KEY="):
                    PK = line.strip().split("=", 1)[1]
                    break
        if PK:
            break
    deals = json.load(open(deals_file))
    cache = {}
    if os.path.exists("data/poly_cache.json"):
        try:
            cache = json.load(open("data/poly_cache.json"))
        except Exception:
            pass
    rows = []
    for d in deals:
        t = d.get("ticker")
        if not t or d["deal_ps"] <= 0:
            continue
        if t not in cache:
            url = (f"https://api.polygon.io/v2/aggs/ticker/{t}/range/1/day/"
                   f"2025-01-01/2026-08-20?apiKey={PK}")
            try:
                r = json.load(u.urlopen(url, timeout=20))
                rs = r.get("results") or []
                cache[t] = [{"d": pd.Timestamp(x["t"], unit="ms").date().isoformat(),
                             "c": x["c"]} for x in rs]
            except Exception:
                cache[t] = []
            time.sleep(12.2)
    json.dump(cache, open("data/poly_cache.json", "w"))
    for d in deals:
        t = d.get("ticker")
        if not t or d["deal_ps"] <= 0:
            continue
        rs = cache.get(t, [])
        if not rs:
            continue
        last = rs[-1]["c"]
        ann = pd.Timestamp(d["file_date"])
        p_ann = next((x["c"] for x in rs if pd.Timestamp(x["d"]) <= ann), None) or rs[0]["c"]
        rows.append({"ticker": t, "deal_ps": d["deal_ps"], "ann": d["file_date"],
                     "px_ann": round(p_ann, 2), "px_now": last,
                     "spr_ann_pct": round((d["deal_ps"] / p_ann - 1) * 100, 1),
                     "ret_60d_pct": round((last / p_ann - 1) * 100, 1)})
    rows.sort(key=lambda r: r["spr_ann_pct"])
    json.dump(rows, open(out, "w"), indent=1)
    for r in rows:
        print(f"  {r['ticker']:6s} deal ${r['deal_ps']:7.2f} ann {r['ann']} "
              f"px_ann {r['px_ann']:7.2f} px_now {r['px_now']:7.2f} "
              f"spr@ann {r['spr_ann_pct']:7.1f}% ret_to_now {r['ret_60d_pct']:7.1f}%")
    print(f"wrote {out} ({len(rows)} deals)")
    return rows

if __name__ == "__main__":
    hits = collect()
    process_batch(hits, start=0, n=40)
    spreads()
