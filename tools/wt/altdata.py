"""Alternative & macro data: FRED, CFTC COT, crypto funding/OI, fear&greed,
Treasury yield curve. All free. These feed the regime classifier and add an
edge beyond price (positioning, sentiment, financial conditions).
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from .core import http_get, get_json, api_key, describe_err

# ---------------------------------------------------------------- FRED macro
FRED_SERIES = [
    ("DGS3MO", "US 3M yield"), ("DGS2", "US 2Y yield"), ("DGS10", "US 10Y yield"),
    ("DGS30", "US 30Y yield"), ("T10Y2Y", "10Y-2Y spread"),
    ("T10Y3M", "10Y-3M spread"), ("DFF", "Fed funds"),
    ("VIXCLS", "VIX"), ("BAMLH0A0HYM2", "US HY credit spread"),
    ("BAMLC0A0CM", "US IG credit spread"), ("DCOILWTICO", "WTI oil"),
    ("DCOILBRENTEU", "Brent oil"), ("DEXUSEU", "USD/EUR"),
    ("DTWEXBGS", "Broad USD index"), ("NFCI", "Fin conditions index"),
    ("WALCL", "Fed balance sheet"), ("M2SL", "M2 money supply"),
    ("UNRATE", "Unemployment rate"), ("CPIAUCSL", "CPI"), ("T5YIE", "5Y inflation breakeven"),
]
def fred_latest(sid):
    k = api_key("FRED_KEY")
    if not k: return None, None
    try:
        d = get_json(f"https://api.stlouisfed.org/fred/series/observations?"
                     f"series_id={sid}&api_key={k}&file_type=json&sort_order=desc&limit=1")
        o = d.get("observations", [{}])[0]
        return o.get("value"), o.get("date")
    except Exception:
        return None, None

def fred_all():
    def one(it):
        sid, name = it; v, date = fred_latest(sid); return name, sid, v, date
    with ThreadPoolExecutor(max_workers=8) as p:
        return list(p.map(one, FRED_SERIES))

def fred_history(sid, limit=500):
    """Historical observations for a FRED series (oldest first). Returns
    (values_list, dates_list, err). Skips non-numeric values ('.'  for FRED).
    Used by the RV scanner for yield-curve spreads (e.g., 2s10s = DGS10-DGS2).

    Fetches the most recent `limit` observations (sort_order=desc) then reverses
    to oldest-first for the backtest. FRED's `sort_order=asc&limit=N` returns
    the FIRST N obs (1960s for old series), not the most recent N -- a subtle
    gotcha that produces useless 50-year-old data."""
    k = api_key("FRED_KEY")
    if not k: return None, None, "no key"
    try:
        d = get_json(f"https://api.stlouisfed.org/fred/series/observations?"
                     f"series_id={sid}&api_key={k}&file_type=json"
                     f"&sort_order=desc&limit={limit}")
    except Exception as e:
        return None, None, str(e)[:50]
    obs = d.get("observations", [])
    vals, dates = [], []
    for o in obs:
        v = o.get("value")
        try:
            vals.append(float(v)); dates.append(o.get("date"))
        except (TypeError, ValueError):
            continue
    if len(vals) < 30:
        return None, None, "too few obs"
    vals.reverse(); dates.reverse()  # oldest-first for backtests
    return vals, dates, None

# ---------------------------------------------------------------- Treasury curve
def treasury_curve():
    """Latest daily par yield curve from Treasury.gov (XML, no key)."""
def treasury_curve():
    """Latest par yield curve. Primary: Treasury.gov XML. Fallback: FRED
    (DGS3MO/DGS2/DGS10/DGS30), which is reliable here."""
    import datetime as _dt, re as _re
    yr = _dt.date.today().year
    url = ("https://home.treasury.gov/resource-center/data-chart-center/"
           "interest-rates/pages/xml?data=daily_treasury_yield_curve&"
           f"field_tdr_date_value={yr}")
    out = {}
    try:
        xml = http_get(url, timeout=12)
        entries = _re.findall(r"<m:properties>(.*?)</m:properties>", xml, _re.S)
        if entries:
            last = entries[-1]
            for tag, key in [("BC_3MONTH", "3M"), ("BC_2YEAR", "2Y"),
                             ("BC_10YEAR", "10Y"), ("BC_30YEAR", "30Y")]:
                m = _re.search(rf"<d:{tag}>([\d.]+)</d:{tag}>", last)
                if m: out[key] = float(m.group(1))
    except Exception:
        pass
    if out:
        return out, None
    # Fallback: build the curve from FRED series.
    for sid, key in [("DGS3MO", "3M"), ("DGS2", "2Y"),
                     ("DGS10", "10Y"), ("DGS30", "30Y")]:
        v, _ = fred_latest(sid)
        try:
            if v not in (None, "."): out[key] = float(v)
        except (TypeError, ValueError):
            pass
    return (out or None), (None if out else "no data (treasury + FRED both failed)")

# ---------------------------------------------------------------- crypto funding/OI
def crypto_funding(sym="BTC"):
    """Binance perp funding rate + open interest (positioning/leverage signal)."""
    out = {}
    try:
        d = get_json(f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={sym}USDT")
        out["funding_rate"] = float(d.get("lastFundingRate", 0)) * 100  # %
        out["mark"] = float(d.get("markPrice", 0))
    except Exception as e:
        return None, describe_err(e)
    try:
        oi = get_json(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={sym}USDT")
        out["open_interest"] = float(oi.get("openInterest", 0))
    except Exception:
        pass
    return out, None

# ---------------------------------------------------------------- fear & greed
def crypto_fear_greed():
    try:
        d = get_json("https://api.alternative.me/fng/?limit=1")
        v = d["data"][0]
        return {"value": int(v["value"]), "label": v["value_classification"]}, None
    except Exception as e:
        return None, describe_err(e)

# ---------------------------------------------------------------- CFTC COT (positioning)
def cot_summary():
    """Latest CFTC Commitments of Traders disaggregated futures-only (large spec
    net positioning) for a few benchmark markets, from the public Socrata API."""
    url = ("https://publicreporting.cftc.gov/resource/6dca-aqww.json?"
           "$select=market_and_exchange_names,report_date_as_yyyy_mm_dd,"
           "noncomm_positions_long_all,noncomm_positions_short_all"
           "&$order=report_date_as_yyyy_mm_dd%20DESC&$limit=200")
    try:
        rows = get_json(url, timeout=15)
    except Exception as e:
        return None, describe_err(e)
    want = {"E-MINI S&P 500": "ES", "GOLD": "Gold", "WTI-PHYSICAL": "WTI",
            "BITCOIN": "BTC", "10-YEAR U.S. TREASURY NOTES": "UST10Y"}
    out = {}
    for r in rows:
        name = r.get("market_and_exchange_names", "")
        for key, lbl in want.items():
            if key in name and lbl not in out:
                try:
                    lng = float(r["noncomm_positions_long_all"])
                    sht = float(r["noncomm_positions_short_all"])
                    out[lbl] = {"net": lng - sht, "long": lng, "short": sht,
                                "date": r.get("report_date_as_yyyy_mm_dd", "")[:10]}
                except (KeyError, ValueError):
                    pass
    return (out or None), (None if out else "no matching markets")
