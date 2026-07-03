#!/usr/bin/env python3
"""Free market news + price scanner using publicly reachable endpoints.

Direct broker/exchange APIs are often blocked, but many free RSS feeds and a
few open price APIs stay reachable. This aggregates them. Stdlib only.

  python3 scan_news.py            # headlines + crypto snapshot
  python3 scan_news.py --json
"""
from __future__ import annotations
import json, re, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

TIMEOUT = 10
UA = "Mozilla/5.0 (market-scanner; research only)"

# Feeds validated to return REAL article items from this environment (2026-06-23,
# verified via probe_sources.py + item-count check). Grouped by instrument so a
# scan can cover equities, macro, crypto, FX, commodities. Failures are skipped.
FEEDS = {
    # equities / general markets
    "CNBC":          "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "MarketWatch":   "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Nasdaq-Mkts":   "https://www.nasdaq.com/feed/rssoutbound?category=Markets",
    "Nasdaq-Stocks": "https://www.nasdaq.com/feed/rssoutbound?category=Stocks",
    "SeekingAlpha":  "https://seekingalpha.com/feed.xml",
    # macro / central banks
    "FedPress":      "https://www.federalreserve.gov/feeds/press_all.xml",
    "ECB":           "https://www.ecb.europa.eu/rss/press.html",
    "BoE":           "https://www.bankofengland.co.uk/rss/news",
    # crypto
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt":       "https://decrypt.co/feed",
    # FX
    "ForexLive":     "https://www.forexlive.com/feed/",
    "FXStreet":      "https://www.fxstreet.com/rss/news",
    # commodities / energy / metals
    "OilPrice":      "https://oilprice.com/rss/main",
    "Mining.com":    "https://www.mining.com/feed/",
}
# Coinlore numeric ids for crypto majors (open API, no key, unlimited).
COINLORE = {"BTC": 90, "ETH": 80, "SOL": 48543, "XRP": 58, "BNB": 2710,
            "ADA": 257, "DOGE": 2, "LINK": 1975, "AVAX": 44883, "LTC": 1}


def _av_key() -> str:
    """Read AlphaVantage key from env or .env.local (gitignored)."""
    import os
    k = os.environ.get("ALPHAVANTAGE_KEY")
    if k:
        return k
    for path in (".env.local", os.path.join(os.path.dirname(__file__), "..", ".env.local")):
        try:
            for line in open(path):
                if line.startswith("ALPHAVANTAGE_KEY="):
                    return line.split("=", 1)[1].strip()
        except OSError:
            continue
    return ""


def fetch_movers():
    """US equity top gainers/losers/active via AlphaVantage (uses 1 daily call)."""
    key = _av_key()
    if not key:
        return None
    try:
        d = json.loads(_get(f"https://www.alphavantage.co/query?"
                            f"function=TOP_GAINERS_LOSERS&apikey={key}"))
        if "top_gainers" not in d:
            return {"error": d.get("Information") or d.get("Note") or "rate limited"}
        return {k: [{"t": x["ticker"], "price": x["price"],
                     "chg": x["change_percentage"], "vol": x["volume"]}
                    for x in d.get(k, [])[:8]]
                for k in ("top_gainers", "top_losers", "most_actively_traded")}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


def _unescape(s: str) -> str:
    for a, b in [("&amp;", "&"), ("&#x2019;", "\u2019"), ("&#x2018;", "\u2018"),
                 ("&#x2014;", "\u2014"), ("&#xE9;", "\u00e9"), ("&quot;", '"')]:
        s = s.replace(a, b)
    return re.sub(r"&#x[0-9a-fA-F]+;", "", s)


def fetch_feed(name: str, url: str):
    try:
        xml = _get(url)
    except Exception as e:  # noqa: BLE001
        return name, [], str(e)
    items = re.findall(r"<item.*?>(.*?)</item>", xml, re.S)
    out = []
    for it in items[:8]:
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", it)
        if t:
            out.append({"title": _unescape(t.group(1).strip()),
                        "date": (d.group(1).strip() if d else "")})
    return name, out, None


def fetch_crypto():
    rows = {}
    def one(sym, cid):
        try:
            d = json.loads(_get(f"https://api.coinlore.net/api/ticker/?id={cid}"))[0]
            rows[sym] = {"price": float(d["price_usd"]),
                         "h1": float(d["percent_change_1h"]),
                         "h24": float(d["percent_change_24h"]),
                         "d7": float(d["percent_change_7d"])}
        except Exception:  # noqa: BLE001
            rows[sym] = None
    with ThreadPoolExecutor(max_workers=8) as p:
        for s, c in COINLORE.items():
            p.submit(one, s, c)
    return rows


def main() -> int:
    as_json = "--json" in sys.argv
    want_movers = "--movers" in sys.argv
    with ThreadPoolExecutor(max_workers=len(FEEDS)) as p:
        feeds = list(p.map(lambda kv: fetch_feed(*kv), FEEDS.items()))
    crypto = fetch_crypto()
    movers = fetch_movers() if want_movers else None
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if as_json:
        print(json.dumps({"asof": now,
                          "feeds": {n: items for n, items, _ in feeds},
                          "crypto": crypto, "movers": movers}, indent=2))
        return 0

    print(f"=== CRYPTO (Coinlore)  {now} ===")
    for s, r in crypto.items():
        if r:
            print(f"  {s:<5} ${r['price']:>12,.2f}  1h{r['h1']:>6.2f}%  "
                  f"24h{r['h24']:>6.2f}%  7d{r['d7']:>7.2f}%")
    if movers and "error" not in movers:
        labels = {"top_gainers": "TOP GAINERS", "top_losers": "TOP LOSERS",
                  "most_actively_traded": "MOST ACTIVE"}
        print("\n=== US EQUITY MOVERS (AlphaVantage, prev close) ===")
        for k, lbl in labels.items():
            row = "  ".join(f"{x['t']}({x['chg']})" for x in movers.get(k, [])[:6])
            print(f"  {lbl:<12}: {row}")
    elif movers:
        print(f"\n(movers unavailable: {movers['error'][:80]})")
    for name, items, err in feeds:
        print(f"\n=== {name} ===" + (f"  (unreachable: {err})" if err else ""))
        for it in items[:5]:
            print(f"  - {it['title']}  ({it['date']})")
    print("\nresearch only, not financial advice. verify before acting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
