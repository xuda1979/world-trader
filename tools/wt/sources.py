"""Price/quote sources across many free providers, cross-checked.

Each fetcher returns a normalized dict or (None, err). Where possible we return
OHLC + change% + a timestamp so downstream analysis can score reward:risk and
freshness. Failures are isolated per-source.
"""
from __future__ import annotations
import re, json
from concurrent.futures import ThreadPoolExecutor
from .core import http_get, get_json, describe_err, api_key, now_iso

# ---------------------------------------------------------------- CRYPTO (real-time)
def crypto_coinbase(sym):
    d = get_json(f"https://api.coinbase.com/v2/prices/{sym}-USD/spot")
    return float(d["data"]["amount"])
def crypto_binance(sym):
    d = get_json(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}USDT")
    return {"price": float(d["lastPrice"]), "dp": float(d["priceChangePercent"]),
            "h": float(d["highPrice"]), "l": float(d["lowPrice"])}
def crypto_kraken(sym):
    pair = {"BTC": "XBTUSD"}.get(sym, sym + "USD")
    d = get_json(f"https://api.kraken.com/0/public/Ticker?pair={pair}")
    if d.get("error"): raise ValueError(";".join(d["error"]))
    r = next(iter(d["result"].values()))
    return {"price": float(r["c"][0]), "h": float(r["h"][1]), "l": float(r["l"][1])}

def crypto_quote(sym):
    """Cross-checked crypto quote w/ OHLC from Binance, validated by Coinbase/Kraken."""
    prices = {}
    out = {"price": None, "dp": None, "h": None, "l": None, "ts": None}
    try:
        b = crypto_binance(sym); out.update(b); prices["binance"] = b["price"]
    except Exception: pass
    try: prices["coinbase"] = crypto_coinbase(sym)
    except Exception: pass
    try:
        k = crypto_kraken(sym); prices["kraken"] = k["price"]
        if out["h"] is None: out["h"], out["l"] = k["h"], k["l"]
    except Exception: pass
    if not prices: return None, "all crypto sources failed"
    if out["price"] is None:
        out["price"] = list(prices.values())[0]
    import statistics
    out["price"] = statistics.median(prices.values())
    out["sources"] = prices
    out["c"] = out["price"]
    if out.get("ts") is None:  # crypto spot is live -> stamp with fetch time
        import time
        out["ts"] = int(time.time())
    return out, None

# ---------------------------------------------------------------- China (Sina/Tencent live)
def sina_quote(code):
    txt = http_get(f"https://hq.sinajs.cn/list={code}",
                   headers={"Referer": "https://finance.sina.com.cn"}, decode="gbk")
    m = re.search(r'var hq_str_\w+="([^"]*)"', txt)
    if not m or not m.group(1): return None, "no data (Sina closed/empty)"
    p = m.group(1).split(",")
    if len(p) < 32: return None, "short payload"
    def f(i):
        try: return float(p[i])
        except (IndexError, ValueError): return None
    name, pc, last, hi, lo = p[0], f(2), f(3), f(4), f(5)
    if not last: return None, "no price"
    dp = ((last - pc) / pc * 100) if pc else None
    # p[30]=YYYY-MM-DD, p[31]=HH:MM:SS Beijing time. Convert to UTC epoch so
    # the freshness gate can score staleness, and the display layer can render
    # it back in the instrument's local tz. Without this, requoted CN-A rows
    # carried ts=None and the table showed '--' for quote time even though we
    # had a real, fresh tick.
    ts = _cn_ts(p[31], p[30]) if len(p) > 31 else None
    return {"c": last, "price": last, "dp": dp, "h": hi, "l": lo, "o": f(1),
            "pc": pc, "name": name, "time": p[31] if len(p) > 31 else "",
            "date": p[30] if len(p) > 30 else "",
            "ts": ts}, None

def tencent_quote(code):
    """Cross-check China quote via Tencent qt.gtimg.cn. code like 'sh600519'."""
    txt = http_get(f"https://qt.gtimg.cn/q={code}", decode="gbk")
    m = re.search(r'="([^"]*)"', txt)
    if not m: return None, "no data"
    p = m.group(1).split("~")
    if len(p) < 34: return None, "short payload"
    def f(i):
        try: return float(p[i])
        except (IndexError, ValueError): return None
    return {"c": f(3), "price": f(3), "dp": f(32), "h": f(33), "l": f(34),
            "pc": f(4), "name": p[1]}, None

# ---------------------------- China WIDE funnel (ALL ~5,500 A-shares, bulk) -----
def _cn_ts(ticktime, datestr=None):
    """Beijing HH:MM:SS -> UTC epoch (so the freshness gate can trust it).

    If `datestr` is given (YYYY-MM-DD, e.g. Sina's p[30]) use it as the
    calendar day; otherwise assume today. Dating from the explicit date is
    safer around midnight Beijing time and when replaying a payload captured
    before 00:00 UTC."""
    import datetime, time, re
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Shanghai")
    except Exception:
        tz = datetime.timezone(datetime.timedelta(hours=8))
    try:
        hh, mm, ss = (int(x) for x in str(ticktime).split(":"))
        if datestr:
            y, mo, d = (int(x) for x in re.split(r"[-/]", str(datestr))[:3])
            dt = datetime.datetime(y, mo, d, hh, mm, ss, tzinfo=tz)
        else:
            now = datetime.datetime.now(tz)
            dt = now.replace(hour=hh, minute=mm, second=ss, microsecond=0)
        return int(dt.timestamp())
    except Exception:
        return int(time.time())

def sina_ashare_list(pages=6, num=100, sort="amount"):
    """STAGE 1 of the China funnel: the ENTIRE A-share market, paginated & sorted
    by turnover (most liquid first) from Sina's market-center node API. A few
    pages (num*pages) cover the tradeable, liquid names out of ~5,500 listings.

    Returns (rows, err) where each row already carries o/h/l/c + turnover + a live
    timestamp -- everything the cheap pre-screen needs, in bulk (no per-name call).
    """
    out = []
    base = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            "Market_Center.getHQNodeData?node=hs_a&symbol=&_s_r_a=page"
            f"&sort={sort}&asc=0&num={num}")
    for pg in range(1, pages + 1):
        try:
            arr = get_json(f"{base}&page={pg}", headers={"Referer": "https://finance.sina.com.cn"})
        except Exception as e:
            if out: break
            return None, describe_err(e)
        if not isinstance(arr, list) or not arr:
            break
        for r in arr:
            def f(k):
                try: return float(r.get(k))
                except (TypeError, ValueError): return None
            c = f("trade")
            if not c:
                continue
            out.append({"T": r.get("symbol"), "name": r.get("name", ""),
                        "o": f("open"), "h": f("high"), "l": f("low"), "c": c,
                        "amount": f("amount"), "v": f("volume"),
                        "dp": f("changepercent"),
                        "ts": _cn_ts(r.get("ticktime"))})
    return (out or None), (None if out else "no A-share rows")

def sina_history(sym, days=400):
    """Daily OHLC history for an A-share (or index) via Sina kline JSON. Powers
    the China backtest -- the piece that lets A-shares get an E[R]/Sharpe like US
    names. Returns (lists dict, err), oldest-first."""
    n = min(max(days, 30), 1000)
    url = ("https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
           f"CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen={n}")
    try:
        arr = get_json(url, headers={"Referer": "https://finance.sina.com.cn"})
    except Exception as e:
        return None, describe_err(e)
    if not isinstance(arr, list) or len(arr) < 20:
        return None, "too few bars"
    H, L, C, V, D = [], [], [], [], []
    for b in arr:
        try:
            H.append(float(b["high"])); L.append(float(b["low"]))
            C.append(float(b["close"])); V.append(float(b.get("volume", 0)))
            D.append(b["day"])
        except (KeyError, ValueError):
            continue
    if len(C) < 20:
        return None, "too few valid bars"
    return {"date": D, "high": H, "low": L, "close": C, "vol": V}, None

def tencent_history(sym, days=400):
    """Fallback daily OHLC for an A-share via Tencent kline. Returns (lists, err)."""
    n = min(max(days, 30), 800)
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           f"param={sym},day,,,{n},qfq")
    try:
        d = get_json(url)
    except Exception as e:
        return None, describe_err(e)
    node = (d.get("data") or {}).get(sym) or {}
    rows = node.get("qfqday") or node.get("day") or []
    if len(rows) < 20:
        return None, "too few bars"
    H, L, C, V, D, O = [], [], [], [], [], []
    for b in rows:  # [date, open, close, high, low, volume]
        try:
            D.append(b[0]); O.append(float(b[1])); C.append(float(b[2]))
            H.append(float(b[3])); L.append(float(b[4]))
            V.append(float(b[5]) if len(b) > 5 else 0)
        except (IndexError, ValueError):
            continue
    if len(C) < 20:
        return None, "too few bars"
    return {"date": D, "open": O, "high": H, "low": L, "close": C, "vol": V}, None

def cn_history(sym, days=400):
    """A-share daily history: Sina primary, Tencent fallback."""
    h, e = sina_history(sym, days)
    if h:
        return h, None
    return tencent_history(sym, days)

# ---------------------------------------------------------------- Hong Kong (live + history)
def _hk_code(sym):
    """Normalize '00700.HK' / '700.HK' / '00700' -> zero-padded 5-digit '00700'."""
    s = str(sym).upper().replace(".HK", "").strip()
    return s.zfill(5) if s.isdigit() else s

def hk_quote(sym):
    """Live HK quote via Sina rt_hk (GBK). HK is freely shortable, so both long
    and short setups are actionable. Returns (dict, err)."""
    import datetime
    code = _hk_code(sym)
    try:
        txt = http_get(f"https://hq.sinajs.cn/list=rt_hk{code}",
                       headers={"Referer": "https://finance.sina.com.cn"}, decode="gbk")
    except Exception as e:
        return None, describe_err(e)
    m = re.search(r'="([^"]*)"', txt)
    if not m or not m.group(1):
        return None, "no data (HK closed/empty)"
    p = m.group(1).split(",")
    if len(p) < 19:
        return None, "short payload"
    def f(i):
        try: return float(p[i])
        except (IndexError, ValueError): return None
    last = f(6)
    if not last:
        return None, "no price"
    ts = None
    try:  # p[17]=YYYY/MM/DD, p[18]=HH:MM:SS in HK time (UTC+8)
        tz = datetime.timezone(datetime.timedelta(hours=8))
        dt = datetime.datetime.strptime(p[17] + " " + p[18], "%Y/%m/%d %H:%M:%S")
        ts = int(dt.replace(tzinfo=tz).timestamp())
    except Exception:
        pass
    return {"c": last, "price": last, "o": f(2), "h": f(4), "l": f(5),
            "pc": f(3), "dp": f(8), "name": p[1], "ts": ts}, None

def hk_history(sym, days=400):
    """Daily OHLC history for an HK stock via Tencent hkfqkline. Returns (lists,
    err), oldest-first. This is what lets HK names get a backtested E[R]/Sharpe."""
    code = _hk_code(sym)
    n = min(max(days, 30), 800)
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get?"
           f"param=hk{code},day,,,{n},qfq")
    d = None
    for attempt in range(2):            # endpoint is occasionally flaky -> retry
        try:
            d = get_json(url); break
        except Exception as e:
            err = describe_err(e)
    if not d:
        return None, err
    node = (d.get("data") or {}).get(f"hk{code}") or {}
    rows = node.get("qfqday") or node.get("day") or []
    if len(rows) < 20:
        return None, "too few bars"
    H, L, C, V, D, O = [], [], [], [], [], []
    for b in rows:  # [date, open, close, high, low, volume, {optional dividend}]
        try:
            D.append(b[0]); O.append(float(b[1])); C.append(float(b[2]))
            H.append(float(b[3])); L.append(float(b[4]))
            V.append(float(b[5]) if len(b) > 5 else 0)
        except (IndexError, ValueError):
            continue
    if len(C) < 20:
        return None, "too few bars"
    return {"date": D, "open": O, "high": H, "low": L, "close": C, "vol": V}, None

# ---------------------------------------------------------------- Taiwan (TWSE live)
def twse_quote(code):
    url = (f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?"
           f"ex_ch=tse_{code}.tw&json=1&delay=0")
    try:
        d = get_json(url)
    except Exception as e:
        return None, describe_err(e)
    arr = d.get("msgArray") or []
    if not arr: return None, "no data (TWSE closed?)"
    m = arr[0]
    def f(k):
        try: return float(m.get(k))
        except (TypeError, ValueError): return None
    last = f("z")
    if last is None:
        bid = (m.get("b", "") or "").split("_")[0]; ask = (m.get("a", "") or "").split("_")[0]
        try: last = (float(bid) + float(ask)) / 2
        except (TypeError, ValueError): last = None
    if last is None: return None, "no price"
    pc = f("y"); dp = ((last - pc) / pc * 100) if pc else None
    # TWSE: m["d"]="YYYYMMDD" (e.g. "20260703"), m["t"]="HH:MM:SS" Taipei time
    # (UTC+8). Parse to UTC epoch so the freshness gate works. Without this,
    # every TW quote carried ts=None and showed "--" as quote time.
    ts = None
    try:
        import datetime as _dt, re
        d = str(m.get("d") or ""); t = str(m.get("t") or "")
        if d and t:
            y, mo, dd = int(d[:4]), int(d[4:6]), int(d[6:8])
            hh, mm, ss = (int(x) for x in t.split(":"))
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo("Asia/Taipei")
            except Exception:
                tz = _dt.timezone(_dt.timedelta(hours=8))
            ts = int(_dt.datetime(y, mo, dd, hh, mm, ss, tzinfo=tz).timestamp())
    except Exception:
        ts = None
    return {"c": last, "price": last, "dp": dp, "h": f("h"), "l": f("l"),
            "o": f("o"), "pc": pc, "time": m.get("t"), "date": m.get("d"),
            "name": m.get("n"), "ts": ts}, None

# ---------------------------------------------------------------- US real-time (Nasdaq)
NQ_CLASS = {s: "etf" for s in (
    "SPY QQQ IWM DIA EWZ FXI KWEB ASHR EWJ EWG EWU EWT INDA EEM EWY EWH "
    "GLD SLV USO UNG DBC CPER TLT IEF HYG LQD UUP VXX "
    "XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC SMH").split()}
def nasdaq_quote(sym):
    cls = NQ_CLASS.get(sym, "stocks")
    try:
        d = get_json(f"https://api.nasdaq.com/api/quote/{sym}/info?assetclass={cls}")
    except Exception as e:
        return None, describe_err(e)
    data = d.get("data")
    if not data: return None, "no data"
    p = data.get("primaryData", {})
    raw = (p.get("lastSalePrice") or "").replace("$", "").replace(",", "")
    try: price = float(raw)
    except ValueError: return None, "no price"
    try: dp = float((p.get("percentageChange") or "").replace("%", ""))
    except ValueError: dp = None
    # Only stamp ts when Nasdaq actually serves a real-time intraday trade time.
    # A date-only stamp (e.g. 'Jun 29, 2026') with isRealTime=False is the prior
    # close, NOT a live price -- emitting it as `ts` would let a stale quote slip
    # past the freshness gate, so we leave ts=None and let the gate exclude it.
    rt = bool(p.get("isRealTime"))
    raw_ts = p.get("lastTradeTimestamp")
    ts = raw_ts if (rt and raw_ts and any(c == ":" for c in str(raw_ts))) else None
    return {"c": price, "price": price, "dp": dp, "h": None, "l": None,
            "rt": rt, "status": data.get("marketStatus"),
            "ts": ts, "name": data.get("companyName")}, None

# ---------------------------------------------------------------- Stooq (global EOD, no key)
def stooq_quote(sym):
    """Stooq CSV: works for US (.us), many intl, futures, indices, FX. EOD."""
    raw = http_get(f"https://stooq.com/q/l/?s={sym.lower()}&f=sd2t2ohlcv&h&e=csv")
    lines = [ln for ln in raw.strip().splitlines() if ln]
    if len(lines) < 2 or "," not in lines[1]:
        return None, "no data/challenge"
    c = lines[1].split(",")
    if len(c) < 8 or c[6] in ("", "N/D"):
        return None, "no close"
    def f(i):
        try: return float(c[i])
        except (IndexError, ValueError): return None
    o, h, l, close = f(3), f(4), f(5), f(6)
    dp = ((close - o) / o * 100) if o else None
    return {"c": close, "price": close, "o": o, "h": h, "l": l, "dp": dp,
            "v": f(7), "date": c[1], "time": c[2], "ts": None}, None

# ---------------------------------------------------------------- Finnhub (intl + OHLC)
def finnhub_quote(sym):
    k = api_key("FINNHUB_KEY")
    if not k: return None, "no key"
    try:
        d = get_json(f"https://finnhub.io/api/v1/quote?symbol={sym}&token={k}")
    except Exception as e:
        return None, describe_err(e)
    if "error" in d: return None, str(d["error"])[:50]
    if not d.get("c"): return None, "no data (free-tier unsupported)"
    return {"c": d["c"], "price": d["c"], "dp": d.get("dp"), "h": d.get("h"),
            "l": d.get("l"), "o": d.get("o"), "pc": d.get("pc"),
            "ts": d.get("t")}, None

# ---------------------------------------------------------------- FX (Twelve Data)
def twelvedata_quote(sym):
    """Real-time FX (and some indices) quote via Twelve Data. sym like 'EUR/USD'."""
    k = api_key("TWELVEDATA_KEY")
    if not k: return None, "no key"
    try:
        d = get_json(f"https://api.twelvedata.com/quote?symbol={sym}&apikey={k}")
    except Exception as e:
        return None, describe_err(e)
    if d.get("status") == "error" or "close" not in d:
        return None, str(d.get("message", "no data"))[:50]
    def f(key):
        try: return float(d[key])
        except (KeyError, TypeError, ValueError): return None
    c = f("close")
    if c is None: return None, "no close"
    return {"c": c, "price": c, "o": f("open"), "h": f("high"), "l": f("low"),
            "dp": f("percent_change"), "ts": d.get("timestamp")}, None

def requote(sym, market=None):
    """Fetch a SINGLE fresh live quote for `sym`, dispatching to the right
    provider by market. This is the hot path for the real-time watch loop: given
    a symbol already selected by the (expensive) backtest, re-pull just its price
    cheaply so the on-screen entry/stop/target track the live tape.
    Returns (quote_dict, err) -- same quote shape the collect_* funcs produce."""
    from . import instruments as _inst
    m = market or _inst.market_of(sym)
    try:
        if m == "CRYPTO": return crypto_quote(sym)
        if m == "FX":     return twelvedata_quote(sym)
        if m == "CN-A":   return sina_quote(sym)
        if m == "HK":     return hk_quote(sym)
        if m == "TW":     return twse_quote(sym)
        # US (and anything else with a Nasdaq-listed real-time feed)
        return nasdaq_quote(sym)
    except Exception as e:
        return None, describe_err(e)

def twelvedata_history(sym, days=400):
    """Daily OHLC history via Twelve Data (FX/indices). Returns (lists dict, err)."""
    k = api_key("TWELVEDATA_KEY")
    if not k: return None, "no key"
    n = min(max(days, 30), 5000)
    try:
        d = get_json(f"https://api.twelvedata.com/time_series?symbol={sym}"
                     f"&interval=1day&outputsize={n}&apikey={k}")
    except Exception as e:
        return None, describe_err(e)
    if d.get("status") == "error":
        return None, str(d.get("message", "error"))[:50]
    vals = d.get("values") or []
    if len(vals) < 20:
        return None, "too few bars"
    # Twelve Data returns newest-first; reverse to oldest-first for technicals.
    vals = list(reversed(vals))
    H, L, C, D, O = [], [], [], [], []
    for v in vals:
        try:
            O.append(float(v.get("open") or 0.0))
            H.append(float(v["high"])); L.append(float(v["low"]))
            C.append(float(v["close"])); D.append(v["datetime"])
        except (KeyError, ValueError):
            continue
    if len(C) < 20:
        return None, "too few valid bars"
    return {"date": D, "open": O, "high": H, "low": L, "close": C,
            "vol": [0]*len(C)}, None

# ------------------------------------------------ Polygon (WHOLE US MARKET bulk)
def polygon_grouped_daily(date=None):
    """ENTIRE US equity market for one trading day in ONE call (~12k tickers).

    This is the wide-scan unlock: instead of looping thousands of symbols, we
    pull every ticker's daily OHLCV at once. Returns (rows, err) where each row
    is dict(T=ticker, o,h,l,c, v=volume, vw=vwap, n=trades). If `date` is None we
    walk back from today to the most recent day that has data (skips weekends/
    holidays). Free tier: end-of-day, 5 calls/min.
    """
    import datetime
    k = api_key("POLYGON_KEY")
    if not k:
        return None, "no key"
    days = [date] if date else None
    if days is None:
        today = datetime.date.today()
        days = [(today - datetime.timedelta(d)).isoformat() for d in range(1, 6)]
    last_err = "no data"
    for d in days:
        url = (f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/"
               f"{d}?adjusted=true&apiKey={k}")
        try:
            j = get_json(url)
        except Exception as e:
            last_err = describe_err(e)
            continue
        if j.get("status") in ("OK", "DELAYED") and j.get("results"):
            return {"date": d, "rows": j["results"]}, None
        last_err = j.get("message") or j.get("status") or "empty"
    return None, last_err

def polygon_history(sym, start="2025-01-01", end=None, limit=500):
    """Daily OHLC history for ONE ticker (the deep stage). Returns (lists, err)."""
    import datetime
    k = api_key("POLYGON_KEY")
    if not k:
        return None, "no key"
    end = end or datetime.date.today().isoformat()
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/"
           f"{start}/{end}?adjusted=true&sort=asc&limit={limit}&apiKey={k}")
    try:
        j = get_json(url)
    except Exception as e:
        return None, describe_err(e)
    r = j.get("results") or []
    if len(r) < 20:
        return None, "too few bars"
    H = [b["h"] for b in r]; L = [b["l"] for b in r]
    C = [b["c"] for b in r]; V = [b.get("v", 0) for b in r]
    D = [b["t"] for b in r]; O = [b.get("o") for b in r]
    return {"date": D, "open": O, "high": H, "low": L, "close": C, "vol": V}, None

# ---------------------------------------------------------------- batch helpers
def fetch_many(fn, items, workers=10):
    """Map fn over items (each (sym,label,native)). Returns list of
    (label,sym,native,q,err).

    ROBUSTNESS: a single flaky source must NEVER crash the whole scan. Some
    fetchers (e.g. sina_quote) call http_get directly and can raise on timeout;
    we catch per-item here so one dead endpoint degrades to an `err` row instead
    of aborting the run (which previously lost the entire opportunity table)."""
    def one(it):
        sym, label, native = it
        try:
            q, err = fn(sym)
        except Exception as e:
            return label, sym, native, None, describe_err(e)
        return label, sym, native, q, err
    with ThreadPoolExecutor(max_workers=workers) as p:
        return list(p.map(one, items))

# ---------------------------------------------------------------- history (for technicals)
def stooq_history(sym, days=260):
    """Daily OHLC history from Stooq CSV (no key). Returns (lists dict, err).
    sym examples: 'spy.us', 'aapl.us', '^spx' may not work -> prefer ETFs."""
    raw = http_get(f"https://stooq.com/q/d/l/?s={sym.lower()}&i=d")
    lines = [ln for ln in raw.strip().splitlines() if ln]
    if len(lines) < 3 or not lines[0].lower().startswith("date"):
        return None, "no history/challenge"
    H, L, C, V, D, O = [], [], [], [], [], []
    for ln in lines[1:]:
        c = ln.split(",")
        if len(c) < 6: continue
        try:
            D.append(c[0]); O.append(float(c[1])); H.append(float(c[2])); L.append(float(c[3]))
            C.append(float(c[4])); V.append(float(c[5]) if c[5] not in ("", "N/D") else 0)
        except ValueError:
            continue
    if len(C) < 20: return None, "too few bars"
    sl = slice(-days, None)
    return {"date": D[sl], "open": O[sl], "high": H[sl], "low": L[sl],
            "close": C[sl], "vol": V[sl]}, None

def polygon_intraday(sym, interval=5, days=60):
    """Intraday OHLCV history for ONE ticker via Polygon aggregates.

    interval: bar size in minutes (5 is the free-tier-friendly default; 1 is
              allowed but burns the 5 calls/min budget fast). days: how many
              trading days back to fetch (Polygon free allows 2y; we default
              to 60 trading days = ~8400 5-min bars, plenty for ORB stats).

    Returns (dict, err) where dict has parallel lists date/open/high/low/close/vol
    PLUS a 'session' list tagging each bar to its calendar date (so ORB can
    group bars by trading day). Bar timestamps are UTC ms epochs.
    """
    import datetime, time
    k = api_key("POLYGON_KEY")
    if not k:
        return None, "no key"
    end = datetime.date.today().isoformat()
    start = (datetime.date.today() - datetime.timedelta(days=int(days * 1.5) + 10)).isoformat()
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/{interval}/minute/"
           f"{start}/{end}?adjusted=true&sort=asc&limit=50000&apiKey={k}")
    try:
        j = get_json(url)
    except Exception as e:
        return None, describe_err(e)
    r = j.get("results") or []
    if len(r) < 100:
        return None, "too few bars"
    O = []; H = []; L = []; C = []; V = []; D = []; S = []
    for b in r:
        try:
            ts = b["t"] / 1000.0  # ms -> s
            # tag each bar to its NY-session date (UTC date is wrong for pre-9:30 bars)
            ny = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone(
                datetime.timedelta(hours=-5))).date().isoformat()
            O.append(float(b["o"])); H.append(float(b["h"]))
            L.append(float(b["l"])); C.append(float(b["c"]))
            V.append(float(b.get("v", 0))); D.append(b["t"])
            S.append(ny)
        except (KeyError, TypeError, ValueError):
            continue
    if len(C) < 100:
        return None, "too few bars after parse"
    return {"date": D, "open": O, "high": H, "low": L, "close": C,
            "vol": V, "session": S, "interval": interval}, None

def nasdaq_history(sym, days=180):
    """Daily OHLC history from Nasdaq (no key) for technicals. Replaces Stooq
    (now JS-challenged). Returns (lists dict, err)."""
    import datetime as _dt
    cls = NQ_CLASS.get(sym, "stocks")
    today = _dt.date.today()
    frm = today - _dt.timedelta(days=int(days*1.6)+10)  # cushion for weekends/holidays
    url = (f"https://api.nasdaq.com/api/quote/{sym}/historical?assetclass={cls}"
           f"&fromdate={frm}&todate={today}&limit={days+40}")
    try:
        d = get_json(url)
    except Exception as e:
        return None, describe_err(e)
    rows = (((d.get("data") or {}).get("tradesTable") or {}).get("rows")) or []
    if not rows:
        return None, "no history"
    H, L, C, V, D, O = [], [], [], [], [], []
    def num(s):
        try: return float(str(s).replace("$", "").replace(",", ""))
        except (TypeError, ValueError): return None
    for r in reversed(rows):  # API is newest-first; we want oldest-first
        c = num(r.get("close")); h = num(r.get("high")); l = num(r.get("low"))
        o = num(r.get("open"))
        if c is None or h is None or l is None:
            continue
        D.append(r.get("date")); O.append(o); H.append(h); L.append(l); C.append(c)
        V.append(num(r.get("volume")) or 0)
    if len(C) < 20:
        return None, "too few bars"
    return {"date": D, "open": O, "high": H, "low": L, "close": C, "vol": V}, None

def binance_klines(sym, interval="1d", limit=180):
    """Daily OHLC history for a crypto symbol (real-time market, 24/7). Returns
    (lists dict, err). Powers technicals for crypto -- the always-tradeable book."""
    try:
        rows = get_json(f"https://api.binance.com/api/v3/klines?"
                        f"symbol={sym}USDT&interval={interval}&limit={limit}")
    except Exception as e:
        return None, describe_err(e)
    if not rows:
        return None, "no klines"
    H, L, C, V, D, O = [], [], [], [], [], []
    for k in rows:  # [openTime,open,high,low,close,volume,...]
        try:
            O.append(float(k[1])); H.append(float(k[2])); L.append(float(k[3]))
            C.append(float(k[4])); V.append(float(k[5])); D.append(k[0])
        except (IndexError, ValueError):
            continue
    if len(C) < 20:
        return None, "too few bars"
    return {"date": D, "open": O, "high": H, "low": L, "close": C, "vol": V}, None
