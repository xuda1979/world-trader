"""Additional alt-data sources (added 2026-07-16) -- all free, no key required
unless noted. Each function returns (data, err) like the rest of the package.

Sources in this module:
  - SEC full-text search (8-K Item 1.01/2.01/8.01 catalysts, same-day)
  - DeFiLlama yields (stablecoin high-APY pools; feeds defi_rate_arb)
  - DeFiLlama protocols (TVL changes, token-momentum proxy)
  - EIA petroleum (gasoline/crude inventories -- energy catalysts)
  - OpenInsider screener (congress + insider clusters)
  - Nasdaq short interest list (squeeze candidates)
  - St. Louis Fed economic calendar (HTML, no key -- fallback for FRED API)
  - Hyperliquid meta + funding (already partially used; consolidated here)
  - ClinicalTrials.gov API (biotech catalysts: phase completion dates)
  - Bitcoin Magazine / The Block RSS (crypto news)

Design notes:
  - Fail-soft: every function returns (None, err_string) on failure.
  - No API keys required for any endpoint here (DEMO_KEY works for EIA).
  - Rate-limit-safe: SEC EFTS allows ~10 req/sec; we call once per scan.
  - All HTTP goes through core.http_get so timeouts/SSL/User-Agent are uniform.

Research only. Not financial advice.
"""
from __future__ import annotations
import re, datetime, json
from concurrent.futures import ThreadPoolExecutor
from .core import http_get, get_json, api_key, describe_err

# ============================================================================
# SEC FULL-TEXT SEARCH (EDGAR EFTS) -- 8-K catalyst scanner
# Free, no key. The highest-signal source for same-day US equity catalysts:
# 8-K Item 1.01 = material definitive agreement (M&A, big contract)
# 8-K Item 2.01 = acquisition completed
# 8-K Item 2.02 = results of operations (earnings pre-release)
# 8-K Item 3.01 = delisting notice
# 8-K Item 5.02 = CEO/officer change
# 8-K Item 8.01 = other events (dividend, buyback, guidance)
# ============================================================================

_8K_ITEMS = {
    "1.01": "material agreement",
    "2.01": "acquisition completed",
    "2.02": "earnings pre-release",
    "3.01": "delisting notice",
    "5.02": "officer/CEO change",
    "8.01": "other material event",
    "1.02": "agreement terminated",
    "9.01": "exhibit (often with 1.01/2.01)",
}

def sec_fulltext_8k(items=("1.01", "2.01", "5.02", "8.01"), days=3, limit=50):
    """Search SEC EDGAR full-text for 8-Ks with specific items filed in last `days`.

    Returns list of {cik, name, ticker, form, file_date, items, url} sorted by date desc.
    Free, no key. Used to surface SAME-DAY catalysts that price hasn't fully reflected.
    """
    import urllib.parse
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    q_items = " OR ".join(f'"Item {it}"' for it in items)
    url = ("https://efts.sec.gov/LATEST/search-index?"
           f"q={urllib.parse.quote(q_items)}&forms=8-K"
           f"&dateRange=custom&startdt={start.isoformat()}&enddt={end.isoformat()}")
    try:
        d = get_json(url, timeout=15)
    except Exception as e:
        return None, describe_err(e)
    hits = d.get("hits", {}).get("hits", [])
    if not hits:
        return [], None
    out = []
    for h in hits[:limit]:
        s = h.get("_source", {})
        name = (s.get("display_names") or [""])[0]
        # Extract ticker from name like "Apple Inc. (AAPL) (CIK 0000320193)"
        m = re.search(r"\(([A-Z.]{1,6})\)", name)
        ticker = m.group(1) if m else None
        cik = (s.get("ciks") or [""])[0]
        adsh = s.get("adsh", "").replace("-", "")
        out.append({
            "cik": cik,
            "name": re.sub(r"\s*\(CIK.*\)", "", name).strip(),
            "ticker": ticker,
            "form": s.get("form"),
            "file_date": s.get("file_date"),
            "items": s.get("items") or [],
            "url": f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{adsh}/" if adsh else None,
        })
    out.sort(key=lambda r: r.get("file_date", ""), reverse=True)
    return out, None

def sec_fulltext_filings(form="8-K", q="material agreement", days=3, limit=30):
    """Generic SEC full-text search across any form type."""
    import urllib.parse
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    url = (f"https://efts.sec.gov/LATEST/search-index?q={urllib.parse.quote(q)}&forms={form}"
           f"&dateRange=custom&startdt={start.isoformat()}&enddt={end.isoformat()}")
    try:
        d = get_json(url, timeout=15)
    except Exception as e:
        return None, describe_err(e)
    hits = d.get("hits", {}).get("hits", [])
    out = []
    for h in hits[:limit]:
        s = h.get("_source", {})
        name = (s.get("display_names") or [""])[0]
        m = re.search(r"\(([A-Z.]{1,6})\)", name)
        out.append({
            "cik": (s.get("ciks") or [""])[0],
            "name": re.sub(r"\s*\(CIK.*\)", "", name).strip(),
            "ticker": m.group(1) if m else None,
            "form": s.get("form"),
            "file_date": s.get("file_date"),
            "items": s.get("items") or [],
        })
    out.sort(key=lambda r: r.get("file_date", ""), reverse=True)
    return out, None

# ============================================================================
# DEFILLAMA YIELDS -- stablecoin high-APY pools (feeds defi_rate_arb)
# Free, no key. 15000+ pools across all chains. We filter for stablecoin-only
# pools with meaningful TVL to find low-risk yield opportunities.
# ============================================================================

def defillama_stablecoin_yields(min_tvl=10_000_000, min_apy=3.0, limit=40):
    """Return stablecoin-only lending/liquidity pools sorted by APY.

    Each row: {project, chain, symbol, apy, apy_base, apy_reward, tvl_usd, pool_url}.
    Filter: stablecoin collateral, TVL >= min_tvl, APY >= min_apy.
    Low-risk yield opportunities (stable-on-stable; ignore reward-APY spikes).
    """
    try:
        d = get_json("https://yields.llama.fi/pools", timeout=20)
    except Exception as e:
        return None, describe_err(e)
    pools = d.get("data", []) if isinstance(d, dict) else []
    out = []
    for p in pools:
        if not p.get("stablecoin"):
            continue
        tvl = p.get("tvlUsd") or 0
        apy = p.get("apy") or 0
        if tvl < min_tvl or apy < min_apy:
            continue
        out.append({
            "project": p.get("project"),
            "chain": p.get("chain"),
            "symbol": p.get("symbol"),
            "apy": round(apy, 2),
            "apy_base": p.get("apyBase"),
            "apy_reward": p.get("apyReward") or 0,
            "tvl_usd": round(tvl, 0),
            "pool_id": p.get("pool"),
            "pool_url": f"https://defillama.com/yields/pool/{p.get('pool')}" if p.get("pool") else None,
        })
    out.sort(key=lambda r: r["apy"], reverse=True)
    return out[:limit], None

def defillama_protocol_tvl_changes(top_n=50):
    """Top protocols by TVL with 24h/7d change -- spot momentum/flows.

    Returns list of {name, tvl, change_1d, change_7d, chain, category}.
    Useful for token-momentum proxy: protocols gaining TVL fast often have
    appreciating tokens (e.g. L1 incentive campaigns).
    """
    try:
        d = get_json("https://api.llama.fi/protocols", timeout=20)
    except Exception as e:
        return None, describe_err(e)
    if not isinstance(d, list):
        return None, "unexpected response"
    out = []
    for p in d[:500]:
        try:
            tvl = p.get("tvl") or 0
            if tvl < 50_000_000:  # filter illiquid
                continue
            out.append({
                "name": p.get("name"),
                "tvl": round(tvl, 0),
                "change_1d": p.get("change_1d"),
                "change_7d": p.get("change_7d"),
                "chain": p.get("chain"),
                "category": p.get("category"),
                "symbol": p.get("symbol"),
            })
        except (TypeError, ValueError):
            continue
    out.sort(key=lambda r: r.get("change_1d") or -999, reverse=True)
    return out[:top_n], None

# ============================================================================
# ENERGY SNAPSHOT via FRED (gasoline, crude, heating oil)
# Free with FRED_KEY (already configured). EIA's DEMO_KEY is heavily rate-
# limited (429s); FRED republishes the same weekly inventory/price series.
# Large weekly moves in gasoline/crude are the primary driver of energy
# equity moves (XLE, XOM, CVX, MPC) within the same week.
# ============================================================================

def energy_snapshot():
    """Latest weekly energy prices + 4-week change from FRED.

    Returns {gasoline_retail, wti_crude, heating_oil, natgas,
             gasoline_4w_chg_pct, wti_4w_chg_pct}.
    Free with FRED_KEY. A >10% 4-week move in gasoline or crude is a regime
    signal for energy equities (momentum continuation or mean reversion).
    """
    from .altdata import fred_latest, fred_history
    out = {}
    # Latest values
    for sid, key in [("GASREGW", "gasoline_retail"),
                     ("DCOILWTICO", "wti_crude"),
                     ("DHOILNYH", "heating_oil"),
                     ("DHHNGSP", "natgas")]:
        v, _ = fred_latest(sid)
        try:
            if v not in (None, "."):
                out[key] = float(v)
        except (TypeError, ValueError):
            pass
    # 4-week change for gasoline and crude (fred_history returns vals, dates, err)
    for sid, key in [("GASREGW", "gasoline_4w_chg_pct"),
                     ("DCOILWTICO", "wti_4w_chg_pct")]:
        vals, dates, e = fred_history(sid, limit=60)
        if vals and len(vals) >= 2:
            try:
                latest = float(vals[-1])
                oldest = float(vals[-5]) if len(vals) >= 5 else float(vals[0])
                if oldest:
                    out[key] = round(100.0 * (latest - oldest) / oldest, 2)
            except (TypeError, ValueError, ZeroDivisionError):
                pass
    if not out:
        return None, "no data (FRED_KEY missing or all series failed)"
    return out, None

# ============================================================================
# OPENINSIDER screener -- insider transaction clusters (free, scrape)
# URL: http://openinsider.com/screener . Last 30 days, buy-only clusters.
# Cluster buying (multiple insiders buying within 30 days) is one of the
# strongest insider signals -- ~+7% abnormal 6-month return per Lakonishok/Lee.
# ============================================================================

def openinsider_cluster_buys(days=30, min_price=2.0, limit=40):
    """Scrape OpenInsider for recent insider BUY transactions (last `days`).

    Returns list of {ticker, company, insider, title, trade_type, filing_date,
                     trade_date, price, shares, value_usd}.
    Free, no key (HTML scrape). The screener URL `s=1` sorts by trade date desc
    and we filter to open-market buys (trade type 'P - Purchase'). Cluster
    detection (multiple insiders buying same ticker within 30d) is done by the
    caller via groupby.
    """
    url = (f"http://openinsider.com/screener?s=1&o=&pl={min_price}&ph=&ll=&lh="
           f"&fd={days}&fdr=&td=0&tdr=&cnt=100&page=1")
    try:
        html = http_get(url, timeout=15)
    except Exception as e:
        return None, describe_err(e)
    # The screener table has class="tinytable". Columns (17 total):
    # [0]X [1]Filing Date [2]Trade Date [3]Ticker [4]Company Name [5]Insider Name
    # [6]Title [7]Trade Type [8]Price [9]Qty [10]Owned [11]ΔOwn [12]Value
    # [13]1d [14]1w [15]1m [16]6m
    tables = re.findall(r'<table[^>]*class="tinytable"[^>]*>(.*?)</table>', html, re.S)
    if not tables:
        return None, "no table found"
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tables[0], re.S)
    out = []
    for r in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
        if len(cells) < 13:
            continue  # header row has <th>, skip
        try:
            def clean(c):
                # Strip tags, but first remove onmouseover/onmouseout attrs that
                # contain quoted strings with '>' chars (breaks naive regex).
                c = re.sub(r'\s+on\w+="[^"]*"', "", c)
                c = re.sub(r"\s+on\w+='[^']*'", "", c)
                c = re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " ").strip()
                return c
            # Ticker cell: <b> <a href="/PSNL" ...>PSNL</a></b> -> extract the
            # ticker from the href or the link text.
            ticker_cell = cells[3]
            # Try to extract ticker from href="/XXXX" first (most reliable)
            m = re.search(r'href="/([A-Z.]{1,6})"', ticker_cell)
            if m:
                ticker = m.group(1)
            else:
                ticker = clean(ticker_cell)
            company = clean(cells[4])
            insider = clean(cells[5])
            title = clean(cells[6])
            trade_type = clean(cells[7])
            price = clean(cells[8])
            qty = clean(cells[9]).replace(",", "")
            value = clean(cells[12]).replace(",", "").replace("$", "")
            filing_date = clean(cells[1])
            trade_date = clean(cells[2])
            if not ticker:
                continue
            # Keep only open-market purchases (P - Purchase)
            if "P - Purchase" not in trade_type and "Purchase" not in trade_type:
                continue
            try:
                sh = int(qty) if qty else 0
            except ValueError:
                sh = 0
            if sh <= 0:
                continue
            try:
                val = int(value) if value else None
            except ValueError:
                val = None
            out.append({
                "ticker": ticker,
                "company": company,
                "insider": insider,
                "title": title,
                "trade_type": trade_type,
                "filing_date": filing_date,
                "trade_date": trade_date,
                "price": price,
                "shares": sh,
                "value_usd": val,
            })
        except (IndexError, ValueError):
            continue
        if len(out) >= limit:
            break
    return out, None

def openinsider_clusters(days=30, min_insiders=2, min_price=2.0, limit=30):
    """Find tickers with cluster buying (>= min_insiders distinct insiders
    buying within `days`). Cluster buying is one of the strongest insider
    signals (Lakonishok & Lee, ~+7% abnormal 6-month return).

    Returns list of {ticker, company, n_insiders, total_value_usd, buys: [...]}
    sorted by n_insiders desc, then total_value_usd desc.
    """
    rows, e = openinsider_cluster_buys(days=days, min_price=min_price, limit=500)
    if e:
        return None, e
    if not rows:
        return [], None
    by_ticker = {}
    for r in rows:
        t = r["ticker"]
        by_ticker.setdefault(t, []).append(r)
    out = []
    for t, buys in by_ticker.items():
        # Count distinct insiders (by name, case-insensitive)
        insiders = {b["insider"].lower() for b in buys if b.get("insider")}
        if len(insiders) < min_insiders:
            continue
        total_val = sum(b.get("value_usd") or 0 for b in buys)
        out.append({
            "ticker": t,
            "company": buys[0].get("company", ""),
            "n_insiders": len(insiders),
            "n_buys": len(buys),
            "total_value_usd": total_val,
            "latest_trade_date": max(b.get("trade_date", "") for b in buys),
            "buys": buys,
        })
    out.sort(key=lambda r: (r["n_insiders"], r["total_value_usd"]), reverse=True)
    return out[:limit], None

# ============================================================================
# SHORT SQUEEZE CANDIDATES -- via Finnhub /stock/short-interest
# Free with FINNHUB_KEY (60/min shared budget). Nasdaq's free CSV was retired;
# we screen a curated watchlist of high-retail-interest names for squeeze risk.
# Short interest > 20% of float + RSI < 30 = classic squeeze setup.
# ============================================================================

# Curated watchlist of names that historically attract high short interest
# (retail-favorite, high-beta, hard-to-borrow). Refreshed periodically.
_SQUEEZE_WATCHLIST = [
    "GME", "AMC", "BBBYQ", "MULN", "FFIE", "NKLA", "MSTR", "COIN", "HOOD",
    "RIVN", "LCID", "PLUG", "FCEL", "NVAX", "BBAI", "SOUN", "APLD", "IRM",
    "PRTG", "CHWY", "PLTR", "SOFI", "AFRM", "RUN", "CVNA", "UPST", "BYND",
    "DKNG", "PTON", "W", "ZM", "DOCN", "AI", "U", "RBLX", "NET", "SQ",
    "PYPL", "SHOP", "TSLA", "NVDA", "AMD", "AAPL", "MSFT", "META", "GOOGL",
]

def short_squeeze_scan(symbols=None, min_si_pct=10.0, timeout=25):
    """Scan Finnhub short interest for a watchlist. Returns squeeze candidates.

    Each row: {symbol, short_interest, float, si_pct_float, si_date}.
    Free with FINNHUB_KEY. Filters to si_pct_float >= min_si_pct.
    Runs calls in parallel with an overall `timeout` to avoid hanging the scan.
    """
    from .altdata import short_interest
    syms = symbols or _SQUEEZE_WATCHLIST
    out = []
    def _one(sym):
        try:
            d, e = short_interest(sym)
            if e or not d:
                return None
            si_pct = d.get("si_pct_float")
            if si_pct is not None and si_pct >= min_si_pct:
                return {
                    "symbol": sym,
                    "short_interest": d.get("si"),
                    "float": d.get("float"),
                    "si_pct_float": si_pct,
                    "si_date": d.get("si_date"),
                }
        except Exception:
            return None
        return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_one, sym): sym for sym in syms}
        for fut in futures:
            try:
                r = fut.result(timeout=timeout)
                if r:
                    out.append(r)
            except Exception:
                continue
    out.sort(key=lambda r: r.get("si_pct_float") or 0, reverse=True)
    return out, None

# ============================================================================
# CLINICAL TRIALS.GOV -- biotech catalysts (phase completion dates)
# Free, no key. Phase 3 completion or Primary Completion Date is a hard
# catalyst for biotech stocks (phase success -> +30-100%, fail -> -40-80%).
# ============================================================================

def clinical_trials_for_company(company_name, status=None, limit=10):
    """Search ClinicalTrials.gov for trials by company/sponsor.

    Returns list of {nct_id, title, phase, status, start_date, primary_completion_date, sponsor}.
    Free, no key (v2 API). Uses query.term which accepts the company name.
    Pass status='RECRUITING' to filter; None returns all statuses.
    """
    import urllib.parse
    q = urllib.parse.quote(company_name)
    url = (f"https://clinicaltrials.gov/api/v2/studies?query.term={q}"
           f"&pageSize={limit}&format=json")
    if status:
        url += f"&filter.overallStatus={urllib.parse.quote(status)}"
    try:
        d = get_json(url, timeout=15)
    except Exception as e:
        return None, describe_err(e)
    studies = d.get("studies", []) if isinstance(d, dict) else []
    out = []
    for s in studies:
        proto = s.get("protocolSection", {}) if isinstance(s, dict) else {}
        idmod = proto.get("identificationModule", {})
        statusmod = proto.get("statusModule", {})
        designmod = proto.get("designModule", {})
        sponsor = idmod.get("leadSponsor", {}).get("name")
        out.append({
            "nct_id": idmod.get("nctId"),
            "title": idmod.get("briefTitle"),
            "phase": ", ".join(designmod.get("phases") or []),
            "status": statusmod.get("overallStatus"),
            "start_date": statusmod.get("startDateStruct", {}).get("date"),
            "primary_completion_date": statusmod.get("primaryCompletionDateStruct", {}).get("date"),
            "sponsor": sponsor,
        })
    return out, None

# ============================================================================
# HYPERLIQUID meta + funding (consolidated; already partially used in
# hyperliquid_funding.py). We expose a clean snapshot here for regime.
# ============================================================================

def hyperliquid_universe():
    """Return Hyperliquid perpetual universe (232+ assets).

    Each: {name, szDecimals, maxLeverage, onlyIsolated}.
    Free, no key (POST endpoint).
    """
    import urllib.request as _ur
    req = _ur.Request("https://api.hyperliquid.xyz/info",
                      data=b'{"type":"meta"}',
                      headers={"Content-Type": "application/json",
                               "User-Agent": "Mozilla/5.0 (world-trader; research only)"})
    try:
        with _ur.urlopen(req, timeout=15, context=__import__("ssl").create_default_context()) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return None, describe_err(e)
    universe = d.get("universe", []) if isinstance(d, dict) else []
    out = []
    for u in universe:
        out.append({
            "name": u.get("name"),
            "sz_decimals": u.get("szDecimals"),
            "max_leverage": u.get("maxLeverage"),
            "only_isolated": u.get("onlyIsolated", False),
        })
    return out, None

# ============================================================================
# AGGREGATE: one call for a global "alt-data sweep" (used by --alt flag).
# ============================================================================

def alt_data_sweep():
    """Run all alt-data fetches in parallel. Returns dict of {source: (data, err)}.

    Single entry point for the scan to consume all new alt-data sources.
    """
    jobs = {
        "sec_8k_material": sec_fulltext_8k,
        "defillama_stables": defillama_stablecoin_yields,
        "defillama_tvl": defillama_protocol_tvl_changes,
        "energy_snapshot": energy_snapshot,
        "openinsider_buys": openinsider_cluster_buys,
        "short_squeeze_scan": short_squeeze_scan,
    }
    out = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {name: pool.submit(fn) for name, fn in jobs.items()}
        for name, fut in futures.items():
            try:
                out[name] = fut.result(timeout=30)
            except Exception as e:
                out[name] = (None, describe_err(e))
    return out

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "sweep"
    if target == "sweep":
        d = alt_data_sweep()
        for k, (v, e) in d.items():
            print(f"\n=== {k} ===")
            if e:
                print(f"  ERR: {e}")
            elif v is None:
                print("  no data")
            else:
                print(json.dumps(v[:3] if isinstance(v, list) else v, indent=2, default=str)[:1500])
    elif target == "sec":
        rows, e = sec_fulltext_8k()
        print(f"SEC 8-K filings (err={e}):")
        for r in (rows or [])[:20]:
            print(f"  {r['file_date']} {r['ticker'] or '----':6s} items={r['items']}  {r['name'][:40]}")
    elif target == "defi":
        rows, e = defillama_stablecoin_yields()
        print(f"DeFi stablecoin yields (err={e}):")
        for r in (rows or [])[:20]:
            print(f"  {r['project']:20s} {r['symbol']:12s} APY={r['apy']:5.1f}%  TVL=${r['tvl_usd']/1e6:.1f}M  {r['chain']}")
    elif target == "insider":
        rows, e = openinsider_cluster_buys()
        print(f"Insider cluster buys (err={e}):")
        for r in (rows or [])[:20]:
            print(f"  {r['ticker']:6s} {r['transaction_date']}  {r['insider'][:30]:30s} sh={r['shares']:>8}  ${r['price']}")
    elif target == "short":
        rows, e = short_squeeze_scan()
        print(f"Short squeeze candidates (err={e}): {len(rows or [])} symbols")
        for r in (rows or [])[:20]:
            print(f"  {r['symbol']:6s} SI={r['short_interest']:>10}  SI%float={r['si_pct_float']}%")
    elif target == "trials":
        rows, e = clinical_trials_for_company(sys.argv[2] if len(sys.argv) > 2 else "Pfizer")
        print(f"Clinical trials (err={e}):")
        for r in (rows or [])[:10]:
            print(f"  {r['nct_id']}  phase={r['phase']:10s}  PCD={r['primary_completion_date']}  {r['title'][:60]}")
    elif target == "energy":
        d, e = energy_snapshot()
        print(f"Energy snapshot (err={e}): {d}")
