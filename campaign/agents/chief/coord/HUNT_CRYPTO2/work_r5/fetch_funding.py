"""R5 charter (a): fetch keyless crypto funding-rate history for the carry/perp-basis corner.

Endpoints (audit of the charter roster first, then the only keyless >=8y extension):
  1. OKX   /api/v5/public/funding-rate-history  (altdata5 okx_funding_history) -- CAPPED 3mo
  2. CB INTX /api/v1/instruments/<SYM>/funding   -- CAPPED ~3mo (25/page, start ignored)
  3. Kraken futures /derivatives/api/v3/histofunding -- HTTP 404 keyless (dead)
  4. BitMEX /api/v1/funding (keyless) -- full history since 2016-05 (depth extension, the
     ONLY source with >=8y of effect per the R4 TimesFM span lesson). Disclosed as a
     non-roster addition in FINDINGS; roster endpoints still fetched for the record.

Writes: work_r5/data/{inst}_funding.csv  (date,funding_rate_8h)
        work_r5/data/fetch_manifest.json (endpoint, url, rows, span, sha)
"""
import sys, os, json, time, hashlib
TOOLS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     '..', '..', '..', '..', '..', '..', 'tools'))
sys.path.insert(0, TOOLS)
from wt import altdata5 as a5  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(OUT, exist_ok=True)
manifest = {}


def utcdate(ms):
    return time.strftime('%Y-%m-%d', time.gmtime(ms / 1000.0))


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()[:16]


# ---------------- 1. OKX roster (3-month cap) ----------------
for inst in ["BTC-USDT-SWAP", "ETH-USDT-SWAP"]:
    rows, err = a5.okx_funding_history(inst=inst, limit=100)
    rec = dict(endpoint="https://www.okx.com/api/v5/public/funding-rate-history?instId=%s&limit=100" % inst,
               via="altdata5.okx_funding_history", rows=0)
    if err:
        rec['error'] = err
    else:
        allr, cursor = list(rows), rows[0]['ts']
        for _ in range(3):  # known cap ~3 months; 3 extra pages prove it
            d, e = a5._clean_json(rec['endpoint'] + "&after=%d" % cursor)
            if e:
                break
            pr, e2 = a5._parse_okx_funding(d)
            if e2 or not pr or pr[0]['ts'] >= cursor:
                break
            allr += pr
            cursor = pr[0]['ts']
            time.sleep(0.3)
        uniq = {r['ts']: r['rate'] for r in allr}
        ts = sorted(uniq)
        rec.update(rows=len(ts), span=[utcdate(ts[0]), utcdate(ts[-1])])
        p = os.path.join(OUT, "okx_%s_funding.csv" % inst.split('-')[0])
        with open(p, 'w') as f:
            f.write("date,funding_rate_8h\n")
            for t in ts:
                f.write("%s,%r\n" % (time.strftime('%Y-%m-%d %H:%M', time.gmtime(t / 1000)), uniq[t]))
        rec['file'] = p
        rec['sha16'] = sha_file(p)
    manifest["okx_" + inst] = rec
    print("OKX", inst, rec.get('rows'), rec.get('span', rec.get('error')))
    time.sleep(0.3)

# ---------------- 2. Coinbase INTX roster (25/page, start ignored) ----------------
for sym in ["BTC-PERP", "ETH-PERP"]:
    base = "https://api.international.coinbase.com/api/v1/instruments/%s/funding" % sym
    rec = dict(endpoint=base, via="raw GET (altdata5._clean_get)", rows=0)
    allr, offset = [], 0
    for _ in range(4):  # prove the cap
        t, e = a5._clean_get(base + "?limit=25&result_offset=%d" % offset)
        if e:
            rec['error'] = e
            break
        r = json.loads(t).get('results', [])
        if not r:
            break
        allr += r
        offset += 25
        time.sleep(0.3)
    if allr:
        seen, rows = set(), []
        for x in allr:
            k = x['event_time']
            if k not in seen:
                seen.add(k)
                rows.append((k, float(x['funding_rate'])))
        rows.sort()
        rec.update(rows=len(rows), span=[rows[0][0][:10], rows[-1][0][:10]])
        p = os.path.join(OUT, "cbintx_%s_funding.csv" % sym.split('-')[0])
        with open(p, 'w') as f:
            f.write("date,funding_rate_8h\n")
            for k, v in rows:
                f.write("%s,%r\n" % (k, v))
        rec['file'] = p
        rec['sha16'] = sha_file(p)
    manifest["cbintx_" + sym] = rec
    print("CBINTX", sym, rec.get('rows'), rec.get('span', rec.get('error')))

# ---------------- 3. Kraken futures roster probe (recorded dead) ----------------
t, e = a5._clean_get("https://futures.kraken.com/derivatives/api/v3/histofunding?tickers=pf_xbtusd")
manifest["kraken_histofunding"] = dict(endpoint="https://futures.kraken.com/derivatives/api/v3/histofunding?tickers=pf_xbtusd",
                                       error=(str(e) if e else "unexpected-ok"))
print("KRAKEN histofunding:", str(e))

# ---------------- 4. BitMEX (>=8y depth extension) ----------------
BM_INST = ["XBTUSD", "ETHUSD"]


def bitmex_funding_all(sym, start=None):
    """Paginate /api/v1/funding oldest->newest with startTime; count<=500/page."""
    out, url = [], "https://www.bitmex.com/api/v1/funding?symbol=%s&count=500&reverse=false" % sym
    if start:
        url += "&startTime=%s" % start
    while True:
        txt, err = a5._clean_get(url)
        if err:
            return out, err
        page = json.loads(txt)
        if not page:
            break
        out += page
        if len(page) < 500:
            break
        last = page[-1]['timestamp']
        url = ("https://www.bitmex.com/api/v1/funding?symbol=%s&count=500&reverse=false&startTime=%s"
               % (sym, last))
        time.sleep(0.25)
    # dedupe on timestamp (last page overlaps at the boundary)
    seen, uniq = set(), []
    for r in out:
        if r['timestamp'] not in seen:
            seen.add(r['timestamp'])
            uniq.append(r)
    uniq.sort(key=lambda r: r['timestamp'])
    return uniq, None


for sym in BM_INST:
    rows, err = bitmex_funding_all(sym)
    rec = dict(endpoint="https://www.bitmex.com/api/v1/funding?symbol=%s&count=500&reverse=false (paginated)" % sym,
               via="raw GET paginated", rows=0)
    if err:
        rec['error'] = err
    else:
        rec.update(rows=len(rows),
                   span=[rows[0]['timestamp'][:10], rows[-1]['timestamp'][:10]])
        p = os.path.join(OUT, "bitmex_%s_funding.csv" % sym.lower())
        with open(p, 'w') as f:
            f.write("date,funding_rate_8h\n")
            for r in rows:
                f.write("%s,%r\n" % (r['timestamp'][:13].replace('T', ' '), r['fundingRate']))
        rec['file'] = p
        rec['sha16'] = sha_file(p)
    manifest["bitmex_" + sym] = rec
    print("BITMEX", sym, rec.get('rows'), rec.get('span', rec.get('error')))

with open(os.path.join(OUT, 'fetch_manifest.json'), 'w') as f:
    json.dump(manifest, f, indent=1, default=str)
print("manifest written:", os.path.join(OUT, 'fetch_manifest.json'))
