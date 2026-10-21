#!/usr/bin/env python3
"""Global, all-instrument market snapshot from free sources.

Covers (data where reachable, news everywhere):
  - Equities/indices: US, Europe, Japan, China/HK, India, Brazil, etc.
  - FX: majors + EM (ECB API unlimited; AlphaVantage real-time bid/ask)
  - Commodities/futures: oil, gas, metals, ags (AV + news feeds)
  - Bonds/rates: Treasury, ECB yields, central-bank feeds
  - Crypto: majors (Coinlore, unlimited)
  - Options/vol: VIX & vol regime via news (no free chain data here)

AlphaVantage free tier ~25 calls/day, 5/min -> used sparingly via --av N.
Stdlib only.
  python3 global_markets.py            # news + crypto + ECB FX (no AV calls)
  python3 global_markets.py --av 6     # also pull up to 6 AV quotes (global eq/fx)
"""
from __future__ import annotations
import json, os, re, sys, urllib.request, urllib.error, ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

UA = "Mozilla/5.0 (global-markets; research only)"
TIMEOUT = 10
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
        return r.read().decode("utf-8", "replace")

def av_key():
    k = os.environ.get("ALPHAVANTAGE_KEY")
    if k: return k
    for p in (".env.local", os.path.join(os.path.dirname(__file__), "..", ".env.local")):
        try:
            for line in open(p):
                if line.startswith("ALPHAVANTAGE_KEY="):
                    return line.split("=",1)[1].strip()
        except OSError: pass
    return ""

# ---- Crypto (Coinlore, unlimited) ----
COINLORE = {"BTC":90,"ETH":80,"SOL":48543,"XRP":58,"BNB":2710,"ADA":257,
            "DOGE":2,"AVAX":44883,"LINK":1975,"LTC":1}
def crypto():
    out={}
    def one(s,c):
        try:
            d=json.loads(_get(f"https://api.coinlore.net/api/ticker/?id={c}"))[0]
            out[s]=(float(d["price_usd"]),float(d["percent_change_24h"]),float(d["percent_change_7d"]))
        except Exception: out[s]=None
    with ThreadPoolExecutor(max_workers=10) as p:
        for s,c in COINLORE.items(): p.submit(one,s,c)
    return out

# ---- FX via ECB (EUR base, unlimited, official daily) ----
def ecb_fx():
    pairs={"USD":"USD","JPY":"JPY","GBP":"GBP","CNY":"CNY","INR":"INR","BRL":"BRL",
           "CHF":"CHF","AUD":"AUD","CAD":"CAD","KRW":"KRW","MXN":"MXN","ZAR":"ZAR"}
    out={}
    def one(code):
        try:
            url=(f"https://data-api.ecb.europa.eu/service/data/EXR/D.{code}.EUR.SP00.A"
                 f"?lastNObservations=1&format=jsondata")
            d=json.loads(_get(url))
            series=d["dataSets"][0]["series"]
            obs=next(iter(series.values()))["observations"]
            val=next(iter(obs.values()))[0]
            out[f"EUR/{code}"]=val
        except Exception: out[f"EUR/{code}"]=None
    with ThreadPoolExecutor(max_workers=12) as p:
        for c in pairs: p.submit(one,c)
    return out

# ---- Global equities/FX/commodities via AlphaVantage (budgeted) ----
# Representative all-country basket; quote = (price, chg%, day).
AV_EQUITY = [
    ("RELIANCE.BSE","India: Reliance"), ("PETR4.SAO","Brazil: Petrobras"),
    ("INFY.BSE","India: Infosys"), ("ITUB","Brazil: Itau (ADR)"),
    ("BABA","China: Alibaba (ADR)"), ("TSM","Taiwan: TSMC (ADR)"),
    ("SAP","Germany: SAP (ADR)"), ("TM","Japan: Toyota (ADR)"),
    ("SHEL","UK: Shell (ADR)"), ("SPY","US: S&P500 ETF"),
    ("EWZ","Brazil ETF"), ("FXI","China large-cap ETF"),
    ("EWJ","Japan ETF"), ("EWG","Germany ETF"), ("INDA","India ETF"),
]
AV_FX = [("EUR","USD"),("USD","JPY"),("GBP","USD"),("USD","CNY"),("USD","BRL"),("USD","INR")]
AV_COMMOD = [("WTI","WTI Oil"),("BRENT","Brent"),("NATURAL_GAS","NatGas"),("COPPER","Copper")]

def av_quote(sym):
    k=av_key()
    d=json.loads(_get(f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={sym}&apikey={k}"))
    q=d.get("Global Quote",{})
    if not q or not q.get("05. price"):
        info=d.get("Information") or d.get("Note") or d.get("Error Message") or "no data"
        return None, info[:60]
    return (q["05. price"], q["10. change percent"], q["07. latest trading day"]), None

def av_fx(frm,to):
    k=av_key()
    d=json.loads(_get(f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={frm}&to_currency={to}&apikey={k}"))
    r=d.get("Realtime Currency Exchange Rate",{})
    if not r: return None, "limit/none"
    return (r.get("5. Exchange Rate"), r.get("6. Last Refreshed")), None

# ---- Finnhub (60 calls/min): global equities + crypto WITH intraday high/low ----
def finnhub_key():
    k=os.environ.get("FINNHUB_KEY")
    if k: return k
    for p in (".env.local", os.path.join(os.path.dirname(__file__), "..", ".env.local")):
        try:
            for line in open(p):
                if line.startswith("FINNHUB_KEY="):
                    return line.split("=",1)[1].strip()
        except OSError: pass
    return ""

# Global equity basket across countries (Finnhub: US tickers + ADRs for intl).
FH_EQUITY = [
    ("SPY","US: S&P500"),("QQQ","US: Nasdaq100"),("IWM","US: Russ2000"),
    ("AAPL","US: Apple"),("NVDA","US: Nvidia"),("GOOGL","US: Alphabet"),
    ("TSM","Taiwan: TSMC"),("BABA","China: Alibaba"),("PDD","China: PDD"),
    ("SAP","Germany: SAP"),("SHEL","UK: Shell"),("TM","Japan: Toyota"),
    ("SONY","Japan: Sony"),("RELIANCE.NS","India: Reliance"),("PETR4.SA","Brazil: Petrobras"),
    ("EWZ","Brazil ETF"),("FXI","China ETF"),("EWJ","Japan ETF"),
    ("EWG","Germany ETF"),("INDA","India ETF"),("EEM","EM ETF"),
    ("GLD","Gold ETF"),("USO","Oil ETF"),("SLV","Silver ETF"),("TLT","US 20Y Bond ETF"),
]
def finnhub_quote(sym):
    k=finnhub_key()
    try:
        d=json.loads(_get(f"https://finnhub.io/api/v1/quote?symbol={sym}&token={k}"))
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)[:40]
    if "error" in d: return None, str(d["error"])[:50]
    if not d.get("c"): return None, "no data (unsupported on free tier)"
    return d, None  # keys: c(current) d(chg) dp(chg%) h(high) l(low) o(open) pc(prevclose)

# ---- Nasdaq API (no key): real-time US equities/ETFs during market hours ----
NQ_CLASS = {  # asset class required by api.nasdaq.com (etf vs stocks)
    "SPY":"etf","QQQ":"etf","IWM":"etf","DIA":"etf","EWZ":"etf","FXI":"etf",
    "EWJ":"etf","EWG":"etf","INDA":"etf","EEM":"etf","GLD":"etf","USO":"etf",
    "SLV":"etf","TLT":"etf",
}
def _nq_class(sym): return NQ_CLASS.get(sym, "stocks")
def nasdaq_quote(sym):
    """Real-time US quote w/ isRealTime + marketStatus. Returns (dict, err)."""
    cls=_nq_class(sym)
    url=f"https://api.nasdaq.com/api/quote/{sym}/info?assetclass={cls}"
    try:
        d=json.loads(_get(url))
    except Exception as e:
        return None, str(e)[:40]
    data=d.get("data")
    if not data: return None, "no data"
    p=data.get("primaryData",{})
    raw=(p.get("lastSalePrice") or "").replace("$","").replace(",","")
    try: price=float(raw)
    except ValueError: return None, "no price"
    chg=(p.get("percentageChange") or "").replace("%","")
    try: dp=float(chg)
    except ValueError: dp=None
    return {"price":price,"dp":dp,"rt":bool(p.get("isRealTime")),
            "status":data.get("marketStatus"),"ts":p.get("lastTradeTimestamp")}, None

# ---- TWSE official API (no key): real-time Taiwan-listed shares (e.g. 2330 TSMC) ----
def twse_quote(code):
    """Live TWSE quote. code like '2330'. Returns (dict, err) in TWD."""
    url=(f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?"
         f"ex_ch=tse_{code}.tw&json=1&delay=0")
    try:
        d=json.loads(_get(url))
    except Exception as e:
        return None, str(e)[:40]
    arr=d.get("msgArray") or []
    if not arr: return None, "no data (TWSE closed?)"
    m=arr[0]
    def f(k):
        try: return float(m.get(k))
        except (TypeError,ValueError): return None
    last=f("z")
    if last is None:  # between matches: use bid/ask midpoint
        bid=(m.get("b","") or "").split("_")[0]; ask=(m.get("a","") or "").split("_")[0]
        try: last=(float(bid)+float(ask))/2
        except (TypeError,ValueError): last=None
    if last is None: return None, "no price"
    pc=f("y")
    dp=((last-pc)/pc*100) if pc else None
    return {"price":last,"dp":dp,"h":f("h"),"l":f("l"),"o":f("o"),"pc":pc,
            "time":m.get("t"),"date":m.get("d"),"name":m.get("n")}, None

# ---- Sina (no key): real-time China A-shares + HK + US via gb_ prefix ----
# China A-share basket: (sina_code, English label, 中文名). sh=Shanghai, sz=Shenzhen.
SINA_CN = [
    ("sh600519","China: Kweichow Moutai","贵州茅台"),
    ("sz300750","China: CATL","宁德时代"),
    ("sh601318","China: Ping An Insurance","中国平安"),
    ("sh600036","China: China Merchants Bank","招商银行"),
    ("sh688981","China: SMIC (STAR)","中芯国际"),
    ("sz000858","China: Wuliangye","五粮液"),
    ("sz000333","China: Midea Group","美的集团"),
    ("sh601899","China: Zijin Mining","紫金矿业"),
    ("sh600900","China: Yangtze Power","长江电力"),
    ("sz002594","China: BYD","比亚迪"),
]
def sina_quote(code):
    """Live Sina quote. code like 'sh600519'. Returns (dict, err). GBK-decoded name."""
    url=f"https://hq.sinajs.cn/list={code}"
    req=urllib.request.Request(url, headers={"User-Agent":UA,
        "Referer":"https://finance.sina.com.cn"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
            txt=r.read().decode("gbk","replace")
    except Exception as e:
        return None, str(e)[:40]
    m=re.search(r'var hq_str_\w+="([^"]*)"', txt)
    if not m or not m.group(1):
        return None, "no data (Sina closed/empty)"
    p=m.group(1).split(",")
    if len(p) < 32:
        return None, "short payload"
    def f(i):
        try: return float(p[i])
        except (IndexError,ValueError): return None
    name=p[0]; pc=f(2); last=f(3); hi=f(4); lo=f(5)
    if not last: return None, "no price"
    dp=((last-pc)/pc*100) if pc else None
    tm=p[31] if len(p)>31 else ""
    return {"price":last,"dp":dp,"h":hi,"l":lo,"pc":pc,"name":name,"time":tm}, None

# ---- Shortability by market + shortable proxy for long-only markets ----
# In practice (foreign/retail via Stock Connect), China A-shares are LONG-ONLY:
# northbound shorting is prohibited and 融券 is heavily restricted. Express a
# bearish China view via a US-listed, freely-shortable ETF/ADR instead.
SHORT_ALLOWED = {
    "CN-A":  False,  # Shanghai/Shenzhen A-shares: long-only in practice
    "HK":    True,   # Hong Kong: shortable (designated list only, treat as ok)
    "TW":    False,  # Taiwan: SBL restricted/uptick -> treat short as not actionable
    "US":    True,   # US equities/ETFs/ADRs: freely shortable
    "CRYPTO":True,   # crypto: shortable via perps/margin
}
# When a bearish signal lands in a long-only market, suggest a shortable proxy.
SHORT_PROXY = {
    "CN-A": [("FXI","China large-cap ETF"),("KWEB","China internet ETF"),
             ("ASHR","CSI 300 A-share ETF"),("YINN/YANG","China 3x bull/bear")],
    "TW":   [("EWT","Taiwan ETF"),("TSM","TSMC ADR (NYSE, shortable)")],
}
def market_of(sym):
    """Classify a symbol's home market for shortability rules."""
    s=str(sym)
    if s.startswith(("sh","sz")):       return "CN-A"
    if re.fullmatch(r"\d{4}", s):       return "TW"     # bare 4-digit -> TWSE
    if s.endswith(".HK"):               return "HK"
    if "/" in s or s in COINLORE:       return "CRYPTO"
    return "US"

# ---- Opportunity scoring: quantified reward:risk filter ----
# Thresholds defining "huge return / low risk" (really: defined-risk asymmetry).
RR_MIN      = 3.0    # reward:risk must be >= 3:1
RISK_MAX    = 0.03   # stop distance <= 3% of entry (defined, tight risk)
RISK_MIN    = 0.005  # floor: stop must be >=0.5% away, else R:R is a degenerate artifact
REWARD_MIN  = 0.06   # target move >= 6% short-term
VIX_MAX     = 25.0   # above this, broad regime too unstable for "low risk" longs
MAX_STALE_S = 15*60  # data must be <=15 min old DURING market hours, else unusable

def quote_age_s(ts):
    """Seconds since a quote's epoch timestamp; None if no/zero ts."""
    if not ts:
        return None
    try:
        return (datetime.now(timezone.utc) - datetime.fromtimestamp(int(ts), timezone.utc)).total_seconds()
    except Exception:
        return None

def freshness_label(ts):
    """Return (age_seconds, human_flag). Flags whether a quote is RT/STALE/CLOSED."""
    age = quote_age_s(ts)
    if age is None:
        return None, "no-ts"
    mins = age/60
    if age <= MAX_STALE_S:
        return age, f"RT {mins:.0f}m"
    if age <= 16*3600:           # within a day-ish => market likely closed, last print
        return age, f"CLOSED {mins/60:.1f}h"
    return age, f"STALE {mins/60:.1f}h"

def score_opportunity(c, h, l, dp, vix=None):
    """Quantify both a long and a short idea from intraday OHLC.

    Long:  entry=c, stop=today's low, target = c + R:R-projected swing (use day range).
    Short: entry=c, stop=today's high, target symmetric.
    Returns the better-qualifying side as a dict, or None if neither passes.
    The 'target' is a measured-move proxy = entry +/- (day range), a conservative
    short-term objective; real targets should be refined with swing levels.
    """
    if not c or not h or not l or h <= l:
        return None
    rng = h - l
    cands = []
    # LONG: risk to today's low, reward = one day-range up (measured move).
    if c > l:
        risk = (c - l) / c
        target = c + rng
        reward = (target - c) / c
        rr = (target - c) / (c - l) if (c - l) > 0 else 0
        cands.append(("Long", c, l, target, risk, reward, rr))
    # SHORT: risk to today's high, reward = one day-range down.
    if c < h:
        risk = (h - c) / c
        target = max(c - rng, 0.01)
        reward = (c - target) / c
        rr = (h - c) and (c - target) / (h - c) or 0
        cands.append(("Short", c, h, target, risk, reward, rr))
    best = None
    for side, entry, stop, target, risk, reward, rr in cands:
        # regime gate: don't flag longs when VIX too high (low-risk claim invalid)
        if side == "Long" and vix is not None and vix > VIX_MAX:
            continue
        passes = (rr >= RR_MIN and RISK_MIN <= risk <= RISK_MAX
                  and reward >= REWARD_MIN)
        row = {"side": side, "entry": entry, "stop": stop, "target": target,
               "risk": risk, "reward": reward, "rr": rr, "passes": passes}
        if best is None or rr > best["rr"]:
            best = row
    return best

# ---- Twelve Data (800/day, 8/min): real-time FX + indices ----
def _key(name):
    k=os.environ.get(name)
    if k: return k
    for p in (".env.local", os.path.join(os.path.dirname(__file__), "..", ".env.local")):
        try:
            for line in open(p):
                if line.startswith(name+"="):
                    return line.split("=",1)[1].strip()
        except OSError: pass
    return ""

TD_FX = ["EUR/USD","USD/JPY","GBP/USD","USD/CHF","USD/CNH","USD/BRL","USD/INR","USD/MXN"]
TD_IDX = ["DAX","FTSE","DJI"]  # free-tier-supported index symbols vary
def td_quote(sym):
    k=_key("TWELVEDATA_KEY")
    try:
        d=json.loads(_get(f"https://api.twelvedata.com/quote?symbol={sym}&apikey={k}"))
    except Exception as e:
        return None, str(e)[:40]
    if d.get("close"):
        return (d["close"], d.get("percent_change","?")), None
    return None, str(d.get("message","no data"))[:45]

# ---- FRED (unlimited): bonds, rates, yield curve, VIX, macro ----
FRED_SERIES = [("DGS10","US 10Y yield"),("DGS2","US 2Y yield"),
               ("T10Y2Y","10Y-2Y spread"),("DFF","Fed funds"),
               ("VIXCLS","VIX"),("DGS30","US 30Y yield"),
               ("BAMLH0A0HYM2","US HY credit spread"),("DCOILBRENTEU","Brent oil")]
def fred_latest(sid):
    k=_key("FRED_KEY")
    try:
        d=json.loads(_get(f"https://api.stlouisfed.org/fred/series/observations?"
                          f"series_id={sid}&api_key={k}&file_type=json&sort_order=desc&limit=1"))
        o=d.get("observations",[{}])[0]
        return o.get("value"), o.get("date")
    except Exception:
        return None, None

# ---- Polygon.io (5/min free): prev-day aggregates + options snapshot/Greeks ----
POLY_AGG = [("SPY","US: S&P500 ETF"),("QQQ","US: Nasdaq100 ETF"),
            ("DIA","US: Dow ETF"),("IWM","US: Russ2000 ETF"),
            ("GLD","Gold ETF"),("USO","Oil ETF"),("TLT","US 20Y Bond ETF")]
def poly_prev(sym):
    k=_key("POLYGON_KEY")
    try:
        d=json.loads(_get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/prev?apiKey={k}"))
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)[:40]
    res=d.get("results") or []
    if not res: return None, str(d.get("message") or d.get("status") or "no data")[:45]
    r=res[0]
    chg=(r["c"]-r["o"])/r["o"]*100 if r.get("o") else 0.0
    return {"c":r["c"],"o":r["o"],"h":r["h"],"l":r["l"],"v":r.get("v",0),"dp":chg}, None

def poly_options_snapshot(underlying):
    """Most active near-the-money contracts w/ Greeks for one underlying (1 call)."""
    k=_key("POLYGON_KEY")
    try:
        d=json.loads(_get(f"https://api.polygon.io/v3/snapshot/options/{underlying}"
                          f"?limit=10&apiKey={k}"))
    except Exception as e:
        return None, str(e)[:40]
    res=d.get("results") or []
    if not res:
        msg=str(d.get("message") or d.get("status") or "no data")
        if "not entitled" in msg.lower() or d.get("status")=="NOT_AUTHORIZED":
            return None, "options Greeks require paid Polygon tier (free=stocks/ETF only)"
        return None, msg[:60]
    rows=[]
    for o in res[:8]:
        det=o.get("details",{}); g=o.get("greeks",{}); day=o.get("day",{})
        rows.append({"tk":det.get("ticker",""),"type":det.get("contract_type",""),
                     "strike":det.get("strike_price"),"exp":det.get("expiration_date"),
                     "iv":o.get("implied_volatility"),"delta":g.get("delta"),
                     "gamma":g.get("gamma"),"theta":g.get("theta"),
                     "oi":o.get("open_interest"),"vol":day.get("volume")})
    return rows, None

def main():
    args=sys.argv[1:]
    av_budget=0
    if "--av" in args:
        try: av_budget=int(args[args.index("--av")+1])
        except: av_budget=6
    use_fh = "--no-fh" not in args
    use_td = "--no-td" not in args
    use_fred = "--no-fred" not in args
    use_poly = "--no-poly" not in args
    now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"=== GLOBAL MARKETS SNAPSHOT  {now} ===\n")


    c=crypto()
    print("-- CRYPTO (Coinlore, USD) --")
    for s,v in c.items():
        if v: print(f"  {s:<5} ${v[0]:>11,.2f}  24h{v[1]:>6.2f}%  7d{v[2]:>7.2f}%")

    fx=ecb_fx()
    print("\n-- FX (ECB official daily, EUR base) --")
    line=[]
    for k,v in fx.items():
        if v: line.append(f"{k}={float(v):.4f}")
    print("  " + "  ".join(line))

    fh_rows=[]
    if use_fh and finnhub_key():
        print("\n-- GLOBAL EQUITIES / ETFs (Finnhub, intraday w/ high-low) --")
        def fh_one(item):
            sym,name=item; q,err=finnhub_quote(sym); return name,sym,q,err
        with ThreadPoolExecutor(max_workers=8) as p:
            fh_rows=list(p.map(fh_one,FH_EQUITY))
        for name,sym,q,err in fh_rows:
            if q:
                print(f"  {name:<18} {sym:<13} ${q['c']:>9.2f}  {q['dp']:>7.2f}%  "
                      f"H {q['h']:.2f} / L {q['l']:.2f}")
            else:
                print(f"  {name:<18} {sym:<13} -- {err}")

    # ---- Real-time overlay: Nasdaq (US, market-hours RT) + TWSE (Taiwan live) ----
    use_rt = "--no-rt" not in args
    if use_rt:
        print("\n-- REAL-TIME OVERLAY (Nasdaq US RT-flag + TWSE Taiwan live) --")
        rt_us = [("SPY","US: S&P500"),("QQQ","US: Nasdaq100"),("AAPL","US: Apple"),
                 ("NVDA","US: Nvidia"),("TSM","Taiwan: TSMC (NYSE ADR)"),
                 ("BABA","China: Alibaba ADR")]
        def nq_one(item):
            sym,name=item; q,err=nasdaq_quote(sym); return name,sym,q,err
        with ThreadPoolExecutor(max_workers=6) as p:
            for name,sym,q,err in p.map(nq_one,rt_us):
                if q:
                    flag=("RT-LIVE" if q["rt"] else f"{q['status']} (delayed/last)")
                    dp=f"{q['dp']:+.2f}%" if q['dp'] is not None else "?"
                    print(f"  {name:<24} {sym:<6} ${q['price']:>9.2f}  {dp:<8} [{flag}]")
                else:
                    print(f"  {name:<24} {sym:<6} -- {err}")
    # ---- China A-shares LIVE (Sina, real-time during China hours, 中文名) ----
    cn_rows=[]
    if use_rt:
        print("\n-- CHINA A-SHARES LIVE (Sina, real-time, long-only market) "
              "[中文名] --")
        def sn_one(item):
            code,name,zh=item; q,err=sina_quote(code); return name,zh,code,q,err
        with ThreadPoolExecutor(max_workers=8) as p:
            cn_rows=list(p.map(sn_one,SINA_CN))
        for name,zh,code,q,err in cn_rows:
            if q:
                dp=f"{q['dp']:+.2f}%" if q['dp'] is not None else "?"
                hl=(f"H {q['h']:.2f}/L {q['l']:.2f}"
                    if q['h'] and q['l'] else "")
                print(f"  {name:<26} {zh:<5} {code:<9} "
                      f"¥{q['price']:>9.2f}  {dp:<8} {hl}  @{q['time']} CN [LIVE]")
            else:
                print(f"  {name:<26} {zh:<5} {code:<9} -- {err}")

    # ---- Taiwan LIVE (TWSE official, real-time during Taiwan hours, 中文名) ----
    tw_rows=[]
    if use_rt:
        print("\n-- TAIWAN LISTED LIVE (TWSE official, real-time) [中文名] --")
        TWSE_CN = [("2330","Taiwan: TSMC","台積電"),
                   ("2317","Taiwan: Hon Hai/Foxconn","鴻海"),
                   ("2454","Taiwan: MediaTek","聯發科"),
                   ("2308","Taiwan: Delta Electronics","台達電"),
                   ("2412","Taiwan: Chunghwa Telecom","中華電")]
        def tw_one(item):
            code,name,zh=item; q,err=twse_quote(code); return name,zh,code,q,err
        with ThreadPoolExecutor(max_workers=5) as p:
            tw_rows=list(p.map(tw_one,TWSE_CN))
        for name,zh,code,q,err in tw_rows:
            if q:
                dp=f"{q['dp']:+.2f}%" if q['dp'] is not None else "?"
                hl=(f"H {q['h']:.0f}/L {q['l']:.0f}" if q['h'] and q['l'] else "")
                print(f"  {name:<26} {zh:<5} {code:<6} "
                      f"NT${q['price']:>8.2f}  {dp:<8} {hl}  @{q['time']} TW [LIVE]")
            else:
                print(f"  {name:<26} {zh:<5} {code:<6} -- {err}")

    vix_val=None
    if use_fred and _key("FRED_KEY"):
        print("\n-- BONDS / RATES / VOL (FRED) --")
        def fr_one(item):
            sid,name=item; v,date=fred_latest(sid); return name,v,date
        with ThreadPoolExecutor(max_workers=8) as p:
            rows=list(p.map(fr_one,FRED_SERIES))
        for name,v,date in rows:
            if v: print(f"  {name:<22} {v:>9}  ({date})")
            if v and name=="VIX":
                try: vix_val=float(v)
                except: pass

    if use_td and _key("TWELVEDATA_KEY"):
        print("\n-- FX real-time + INDICES (Twelve Data, 8/min) --")
        line=[]
        for s in TD_FX[:8]:
            q,err=td_quote(s)
            if q: line.append(f"{s}={float(q[0]):.4f}({float(q[1]):+.2f}%)")
        print("  " + "  ".join(line) if line else "  (rate limited; retry)")

    if use_poly and _key("POLYGON_KEY"):
        print("\n-- US INDEX/SECTOR ETFs (Polygon prev-day OHLCV) --")
        for sym,name in POLY_AGG:
            q,err=poly_prev(sym)
            if q:
                print(f"  {name:<20} {sym:<5} ${q['c']:>9.2f}  {q['dp']:>6.2f}%  "
                      f"H {q['h']:.2f} / L {q['l']:.2f}  vol {q['v']/1e6:.1f}M")
            else:
                print(f"  {name:<20} {sym:<5} -- {err}")
        print("\n-- OPTIONS / GREEKS (Polygon snapshot, SPY) --")
        rows,err=poly_options_snapshot("SPY")
        if rows:
            for o in rows:
                iv=f"{o['iv']*100:.1f}%" if o['iv'] is not None else "?"
                dl=f"{o['delta']:+.2f}" if o['delta'] is not None else "?"
                th=f"{o['theta']:+.3f}" if o['theta'] is not None else "?"
                print(f"  {o['type']:<4} K{o['strike']} exp{o['exp']}  IV {iv:<6} "
                      f"delta {dl}  theta {th}  OI {o['oi']}  vol {o['vol']}")
        else:
            print(f"  -- {err}")

    if av_budget>0:
        used=0
        for sym,name in AV_EQUITY:
            if used>=av_budget: break
            q,err=av_quote(sym); used+=1
            if q: print(f"  {name:<26} {sym:<14} ${q[0]:>9}  {q[1]:>9}  ({q[2]})")
            else:
                print(f"  {name:<26} {sym:<14} -- {err}")
                if "rate" in err.lower() or "limit" in err.lower() or "premium" in err.lower():
                    print("  (AlphaVantage limit reached; stopping AV calls)"); break
        print(f"  [used {used} AV calls]")
    else:
        print("\n-- GLOBAL EQUITIES: skipped (run with --av N to spend AlphaVantage calls) --")

    # ---- Quantified opportunity table (reward:risk filter) ----
    print("\n=== OPPORTUNITY TABLE (quantified reward:risk) ===")
    print(f"   thresholds: R:R>={RR_MIN:.0f}  risk<={RISK_MAX*100:.0f}%  "
          f"reward>={REWARD_MIN*100:.0f}%  VIX<{VIX_MAX:.0f} for longs"
          + (f"  | VIX now {vix_val:.1f}" if vix_val is not None else ""))
    scored=[]
    proxy_notes=[]   # bearish signals in long-only markets -> shortable proxy
    def consider(name, sym, q):
        """q must have c/h/l/dp. Apply shortability rules; collect proxy notes."""
        s=score_opportunity(q.get("c"),q.get("h"),q.get("l"),q.get("dp"),vix_val)
        if not s: return
        mkt=market_of(sym)
        if s["side"]=="Short" and not SHORT_ALLOWED.get(mkt, True):
            # Un-shortable market: this short idea is NOT actionable on the
            # underlying. Record a proxy suggestion instead and drop the row.
            proxies=SHORT_PROXY.get(mkt, [])
            plist=", ".join(f"{t} ({d})" for t,d in proxies) or "a shortable US ETF/ADR"
            proxy_notes.append(
                f"{name} ({sym}): bearish setup but {mkt} is long-only/short-restricted "
                f"-> express via shortable proxy: {plist}")
            return
        s["price"]=q.get("c"); s["dp"]=q.get("dp"); s["mkt"]=mkt
        age,flag=freshness_label(q.get("t"))
        s["age"]=age; s["fresh"]=flag
        s["live"]=(age is not None and age<=MAX_STALE_S)
        scored.append((name,sym,s))
    # Finnhub global basket
    for name,sym,q,err in fh_rows:
        if q: consider(name, sym, q)
    # China A-shares (Sina live): long-only -> shorts auto-converted to proxy notes
    for name,zh,code,q,err in cn_rows:
        if q:
            consider(f"{name} {zh}", code,
                     {"c":q["price"],"h":q["h"],"l":q["l"],"dp":q["dp"]})
    # Taiwan (TWSE live): SBL-restricted -> shorts auto-converted to proxy notes
    for name,zh,code,q,err in tw_rows:
        if q:
            consider(f"{name} {zh}", code,
                     {"c":q["price"],"h":q["h"],"l":q["l"],"dp":q["dp"]})
    qualifying=[x for x in scored if x[2]["passes"]]
    qualifying.sort(key=lambda x:-x[2]["rr"])
    # data-freshness summary: how many quotes are <=15min old?
    live_n=sum(1 for _,_,s in scored if s.get("live"))
    print(f"   data freshness: {live_n}/{len(scored)} quotes <=15min "
          f"(MAX_STALE={MAX_STALE_S//60}min); stale rows flagged CLOSED/STALE below")
    hdr=(f"  {'Instrument':<18}{'Sym':<13}{'Dir':<6}{'Price':>9}{'Chg%':>7}"
         f"{'Entry':>9}{'Stop':>9}{'Target':>9}{'Risk%':>7}{'Rwd%':>7}{'R:R':>6}  Data")
    if qualifying:
        print(hdr)
        for name,sym,s in qualifying:
            print(f"  {name:<18}{sym:<13}{s['side']:<6}{s['price']:>9.2f}"
                  f"{s['dp']:>6.1f}%{s['entry']:>9.2f}"
                  f"{s['stop']:>9.2f}{s['target']:>9.2f}{s['risk']*100:>6.1f}%"
                  f"{s['reward']*100:>6.1f}%{s['rr']:>6.1f}  {s.get('fresh','?')}")
    else:
        print("  (empty -- no instrument meets the threshold this scan)")
        # near-misses: rank by reward (the binding constraint today), risk in-band
        nm=[x for x in scored if RISK_MIN <= x[2]["risk"] <= RISK_MAX]
        nm.sort(key=lambda x:-x[2]["reward"])
        if nm:
            print("  near-misses (in-band risk, reward too small to qualify):")
            for name,sym,s in nm[:3]:
                print(f"    {name:<18}{sym:<10}{s['side']:<6}price {s['price']:.2f}"
                      f"({s['dp']:+.1f}%)  R:R {s['rr']:.1f}  "
                      f"risk {s['risk']*100:.1f}%  rwd {s['reward']*100:.1f}%  "
                      f"[{s.get('fresh','?')}]")

    # ---- Shortable-proxy suggestions for long-only / short-restricted markets ----
    if proxy_notes:
        print("\n-- SHORT-RESTRICTED MARKETS: use a shortable proxy --")
        print("   (China A-shares are long-only via Connect; Taiwan SBL-restricted.")
        print("    A bearish view is expressed by SHORTING the US-listed ETF/ADR.)")
        for n in proxy_notes:
            print(f"  * {n}")

    print("\nresearch only, not financial advice. verify before acting.")
    return 0

if __name__=="__main__": sys.exit(main())
