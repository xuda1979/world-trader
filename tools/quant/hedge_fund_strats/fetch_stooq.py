"""Fetch daily OHLCV from Stooq (free) for futures / ETFs / indices.

Stooq serves a SHA-256 proof-of-work challenge (JS anti-bot) before data.
This script solves it headlessly: parse `c` and `d` from the challenge page,
brute-force n so that sha256(c + str(n)) starts with d hex zeros, POST the
solution to /__verify (which sets a cookie), then fetch the CSV with the
same session. No browser required.

Usage:
    python tools/quant/hedge_fund_strats/fetch_stooq.py SYMBOL [SYMBOL...] --out DIR

Symbols (Stooq convention, .f = futures):
    es.f (S&P500 e-mini), nq.f (Nasdaq), ym.f (Dow), cl.f (crude), gc.f (gold),
    si.f (silver), hg.f (copper), ng.f (nat gas), rb.f (gasoline), ho.f (heat),
    zb.f (30y T-bond), zn.f (10y T-note), zf.f (5y note), 6e.f (EUR), 6j.f (JPY),
    6b.f (GBP), 6c.f (CAD), 6a.f (AUD), zc.f (corn), zs.f (soybeans), zw.f (wheat)
"""

import sys
import os
import re
import json
import hashlib
import time
import urllib.request
from urllib.parse import urlencode, quote
from http.cookiejar import CookieJar

BASE = "https://stooq.com"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def solve_pow(c: str, d: int) -> int:
    """Brute-force n: hex(sha256(c + n)) starts with d zeros."""
    prefix = "0" * d
    n = 0
    t0 = time.time()
    while True:
        h = hashlib.sha256((c + str(n)).encode()).hexdigest()
        if h.startswith(prefix):
            return n
        n += 1
        if n % 100000 == 0:
            print(f"  PoW: {n} tries ({time.time()-t0:.1f}s)", flush=True)


def get_cookie():
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = list(UA.items())
    # 1. Hit a page to receive the challenge
    req = urllib.request.Request(f"{BASE}/q/d/l/?s=es.f&i=d", headers=UA)
    html = opener.open(req, timeout=30).read().decode(errors="ignore")
    m = re.search(r'const c="([^"]+)",d=(\d+)', html)
    if not m:
        # Maybe already verified (data returned)
        if "Date,Open" in html:
            return opener, True
        raise RuntimeError("No PoW challenge found in response")
    c, d = m.group(1), int(m.group(2))
    print(f"  PoW challenge: d={d}, solving...")
    n = solve_pow(c, d)
    # 2. POST solution (Origin/Referer required — 403 without them)
    body = urlencode({"c": c, "n": n}).encode()
    req = urllib.request.Request(f"{BASE}/__verify", data=body,
                                 headers={**UA, "Content-Type": "application/x-www-form-urlencoded",
                                          "Origin": BASE, "Referer": BASE + "/"})
    r = opener.open(req, timeout=30).read().decode(errors="ignore")
    print(f"  verify response: {r[:60]!r}")
    return opener, False


def fetch(symbol: str, opener, out_dir: str) -> str:
    url = f"{BASE}/q/d/l/?s={quote(symbol)}&i=d"
    req = urllib.request.Request(url, headers=UA)
    data = opener.open(req, timeout=60).read().decode(errors="ignore")
    lines = [l for l in data.strip().split("\n") if l]
    if len(lines) < 2 or "Date" not in lines[0]:
        raise RuntimeError(f"{symbol}: bad response ({len(lines)} lines, {lines[0][:80]!r})")
    path = os.path.join(out_dir, f"{symbol.replace('.f','')}.csv")
    with open(path, "w") as f:
        f.write(data)
    print(f"  {symbol}: {len(lines)-1} rows -> {path}")
    return path


def main():
    args = sys.argv[1:]
    out_dir = "data_stooq"
    if "--out" in args:
        i = args.index("--out")
        out_dir = args[i + 1]
        args = args[:i] + args[i + 2:]
    os.makedirs(out_dir, exist_ok=True)
    if not args:
        print(__doc__)
        sys.exit(1)
    opener, already = get_cookie()
    for s in args:
        for attempt in range(3):
            try:
                fetch(s, opener, out_dir)
                break
            except Exception as e:
                print(f"  {s} attempt {attempt+1} failed: {e}", flush=True)
                time.sleep(2)
    print("done")


if __name__ == "__main__":
    main()
