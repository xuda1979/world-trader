"""Expanded news: many RSS feeds + GDELT tone. Verified-reachable feeds only at
runtime (failures skipped). Grouped by domain so a scan spans equities, macro,
central banks, crypto, FX, commodities, and regional markets.
"""
from __future__ import annotations
import re, datetime
from concurrent.futures import ThreadPoolExecutor
from .core import http_get, get_json, api_key, describe_err

FEEDS = {
    # --- equities / general markets ---
    "MarketWatch":   "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Nasdaq-Mkts":   "https://www.nasdaq.com/feed/rssoutbound?category=Markets",
    "Nasdaq-Stocks": "https://www.nasdaq.com/feed/rssoutbound?category=Stocks",
    "SeekingAlpha":  "https://seekingalpha.com/feed.xml",
    "Investing":     "https://www.investing.com/rss/news_25.rss",
    "Yahoo-Fin":     "https://finance.yahoo.com/news/rssindex",
    "Benzinga":      "https://www.benzinga.com/feed",
    "Zerohedge":     "https://feeds.feedburner.com/zerohedge/feed",
    # --- macro / central banks ---
    "FedPress":      "https://www.federalreserve.gov/feeds/press_all.xml",
    "ECB":           "https://www.ecb.europa.eu/rss/press.html",
    "BoE":           "https://www.bankofengland.co.uk/rss/news",
    "BoJ":           "https://www.boj.or.jp/en/rss/whatsnew.xml",
    "IMF":           "https://www.imf.org/external/rss/feeds.aspx?category=news",
    # --- crypto ---
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt":       "https://decrypt.co/feed",
    "TheBlock":      "https://www.theblock.co/rss.xml",
    "CoinDesk":      "https://www.coindesk.com/arc/outboundfeeds/rss/",
    # --- FX ---
    "ForexLive":     "https://www.forexlive.com/feed/",
    "FXStreet":      "https://www.fxstreet.com/rss/news",
    # --- commodities / energy / metals ---
    "OilPrice":      "https://oilprice.com/rss/main",
    "Mining.com":    "https://www.mining.com/feed/",
    "Kitco":         "https://www.kitco.com/rss/KitcoNews.xml",
    # --- regional ---
    "JapanTimes":    "https://www.japantimes.co.jp/feed/",
    "SCMP-Biz":      "https://www.scmp.com/rss/92/feed",
    "ET-Markets":    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Livemint":      "https://www.livemint.com/rss/markets",
}

def _unescape(s):
    s = s.replace("<![CDATA[", "").replace("]]>", "")
    for a, b in [("&amp;", "&"), ("&#x2019;", "\u2019"), ("&#x2018;", "\u2018"),
                 ("&#x2014;", "\u2014"), ("&quot;", '"'), ("&#39;", "'"),
                 ("&apos;", "'"), ("&lt;", "<"), ("&gt;", ">")]:
        s = s.replace(a, b)
    return re.sub(r"&#x?[0-9a-fA-F]+;", "", s).strip()

def fetch_feed(name, url):
    try:
        xml = http_get(url, timeout=10)
    except Exception as e:
        return name, [], str(e)[:40]
    items = re.findall(r"<item.*?>(.*?)</item>", xml, re.S)[:8]
    out = []
    for it in items:
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", it)
        if t:
            out.append({"title": _unescape(t.group(1).strip()),
                        "date": (d.group(1).strip() if d else "")})
    return name, out, None

def fetch_all(feeds=None):
    feeds = feeds or FEEDS
    with ThreadPoolExecutor(max_workers=min(16, len(feeds))) as p:
        return list(p.map(lambda kv: fetch_feed(*kv), feeds.items()))

# ---- GDELT: global news tone/volume for a query (free, no key) ----
def gdelt_tone(query="stock market", hours=24):
    """Average tone & article volume for a topic over recent hours."""
    url = ("https://api.gdeltproject.org/api/v2/doc/doc?query="
           + query.replace(" ", "%20")
           + f"&mode=tonechart&format=json&timespan={hours}h")
    try:
        d = get_json(url, timeout=12)
    except Exception as e:
        return None, str(e)[:40]
    bins = d.get("tonechart") or []
    if not bins: return None, "no data"
    total = sum(b.get("count", 0) for b in bins)
    if not total: return None, "no articles"
    wtone = sum(b.get("bin", 0) * b.get("count", 0) for b in bins) / total
    return {"avg_tone": round(wtone, 2), "articles": total}, None

# ============================================================================
# Per-TICKER news (the wide funnel surfaces dynamic names; the 26 RSS feeds
# above can't cover them, so we fetch company-specific news per candidate).
#   - Finnhub company-news (60 req/min): broad coverage incl. microcaps; gives
#     headline flow + recency. Primary, used for every displayed candidate.
#   - Polygon news insights (5 req/min): carries a per-ticker SENTIMENT
#     (positive/negative/neutral + reasoning). Used sparingly (rows passing the
#     bar) since the budget is tiny and the wide funnel already uses Polygon.
# ============================================================================
def finnhub_company_news(sym, days=7, keep=6):
    """Recent company-specific headlines for ONE ticker (Finnhub, ~60/min).
    Returns (dict, err): count, latest headline + epoch ts, distinct sources,
    and up to `keep` recent {title, ts, source, url}. Empty dict if no news."""
    k = api_key("FINNHUB_KEY")
    if not k:
        return None, "no key"
    to = datetime.date.today()
    frm = to - datetime.timedelta(days=days)
    url = (f"https://finnhub.io/api/v1/company-news?symbol={sym}"
           f"&from={frm.isoformat()}&to={to.isoformat()}&token={k}")
    try:
        arr = get_json(url, timeout=12)
    except Exception as e:
        return None, describe_err(e)
    if not isinstance(arr, list):
        return None, "bad payload"
    arr = [a for a in arr if a.get("headline")]
    if not arr:
        return {"count": 0, "latest": None, "latest_ts": None, "sources": 0,
                "headlines": []}, None
    arr.sort(key=lambda a: a.get("datetime", 0), reverse=True)
    heads = [{"title": a.get("headline", ""), "ts": a.get("datetime"),
              "source": a.get("source", ""), "url": a.get("url", "")}
             for a in arr[:keep]]
    srcs = len({a.get("source") for a in arr if a.get("source")})
    return {"count": len(arr), "latest": arr[0].get("headline"),
            "latest_ts": arr[0].get("datetime"), "sources": srcs,
            "headlines": heads}, None

def polygon_ticker_sentiment(sym, limit=10):
    """Per-ticker news SENTIMENT via Polygon insights (5/min -> use sparingly).
    Returns (dict, err): net in {-1,0,+1}/None, pos/neg counts, a reasoning
    string, and the latest title + utc. Empty dict if no insights/news."""
    k = api_key("POLYGON_KEY")
    if not k:
        return None, "no key"
    url = (f"https://api.polygon.io/v2/reference/news?ticker={sym}"
           f"&order=desc&limit={limit}&apiKey={k}")
    try:
        j = get_json(url, timeout=12)
    except Exception as e:
        return None, describe_err(e)
    res = j.get("results") or []
    if not res:
        return {"count": 0, "net": None, "pos": 0, "neg": 0, "latest": None,
                "latest_utc": None, "reasoning": None}, None
    pos = neg = 0
    pos_why = neg_why = None
    for art in res:
        for ins in (art.get("insights") or []):
            if ins.get("ticker") != sym:
                continue
            s = ins.get("sentiment")
            if s == "positive":
                pos += 1; pos_why = pos_why or ins.get("sentiment_reasoning")
            elif s == "negative":
                neg += 1; neg_why = neg_why or ins.get("sentiment_reasoning")
    net = None
    if pos or neg:
        net = 1 if pos > neg else -1 if neg > pos else 0
    reasoning = pos_why if net == 1 else neg_why if net == -1 else (pos_why or neg_why)
    return {"count": len(res), "net": net, "pos": pos, "neg": neg,
            "latest": res[0].get("title"),
            "latest_utc": res[0].get("published_utc"),
            "reasoning": reasoning}, None

def ticker_news(sym, days=7, want_sentiment=False):
    """Merged per-candidate news: fast Finnhub headline flow + (optionally)
    Polygon per-ticker sentiment. Always returns a dict (never None) so callers
    can attach it unconditionally; fields are None/0 when nothing is found."""
    out = {"count": 0, "latest": None, "latest_ts": None, "sources": 0,
           "headlines": [], "net": None, "pos": 0, "neg": 0, "reasoning": None,
           "src": None, "err": None}
    fh, err = finnhub_company_news(sym, days=days)
    if fh:
        for key in ("count", "latest", "latest_ts", "sources", "headlines"):
            out[key] = fh[key]
        out["src"] = "finnhub"
    else:
        out["err"] = err
    if want_sentiment:
        pg, _ = polygon_ticker_sentiment(sym)
        if pg:
            out["net"], out["pos"], out["neg"] = pg["net"], pg["pos"], pg["neg"]
            out["reasoning"] = pg["reasoning"]
            if not out["latest"] and pg["latest"]:
                out["latest"], out["latest_ts"] = pg["latest"], None
            if not out["count"]:
                out["count"] = pg["count"]
            out["src"] = (out["src"] + "+polygon") if out["src"] else "polygon"
    return out
