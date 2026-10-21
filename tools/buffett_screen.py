#!/usr/bin/env python3
"""Buffett-rule screen over US large caps -> top 20.

Operationalizes Warren Buffett's published criteria (letters, CNBC interviews):
  1. Consistent earnings power   -> positive EPS growth + revenue growth
  2. High & stable ROE           -> returnOnEquity >= 15% (best >= 20%)
  3. Defensive leverage          -> low debt/equity (skipped for financials,
                                    where debt is the business model)
  4. Fat & stable margins        -> operating + net margin
  5. Sensible valuation          -> forward P/E <= 25, not paying up
  6. Shareholder-friendly        -> dividends + FCF yield
  7. Size / understandability    -> market cap >= $40B, low-beta tilt

Data: Finnhub /stock/metric + /profile2 (free tier, 60 req/min), disk-cached
30 min so the 10-min /loop is cheap. Yahoo .info is 429-blocked from this IP
(2026-08-22) so it is not used. Composite is a weighted 0-100 score; hard
gates drop junk (weak quality, extreme leverage outside financials, money
losers). Research only — not financial advice.

Usage:
  python tools/buffett_screen.py [--refresh] [--top N] [--json]
"""
from __future__ import annotations
import json, os, sys, time, argparse, urllib.request, urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from wt.core import api_key
from buffett_consistency import annual_eps, FACTS as EDGAR_FACTS  # noqa: E402

CACHE = os.path.join(os.path.dirname(__file__), "logs", "buffett_cache.json")
TTL = 30 * 60  # seconds
BASE = "https://finnhub.io/api/v1"

# ~150 liquid mega/large-cap US names (S&P 100 core + quality large caps)
UNIVERSE = """
AAPL MSFT GOOGL AMZN NVDA META AVGO TSLA BRK-B JPM V MA UNH LLY XOM
PG JNJ HD COST ABBV MRK CVX KO PEP WMT MCD CRM ORCL AMD INTC QCOM
TXN ACN ADBE CSCO INTU NFLX CMCSA DIS AMGN GILD BIIB ISRG UBER SHOP
NOW CAT DE BA GE HON MMM UPS FDX NKE SBUX TGT TJX ROST EL EMR ITW
PH PCAR WM RSG LMT RTX NOC GD LH HCA MDT BSX SYK ABT TMO DHR BDX EW
ZTS VRTX REGN MRNA ABNB ADI APD LIN SHW ECL DOW DD NEE DUK SO D AEP
EXC ED C BAC WFC GS MS SCHW PNC USB TFC AXP BLK ICE MCO SPGI CB PGR
ALL AIG MET TRV PRU KHC MDLZ HSY GIS CPB KMB CL MCK ABC COR CARR
DELL GWW PAYX ADP IT VRSK IR MMC AJG WTW CTAS FAST GRMN CHD CLX
FTNT LRCX IDXX UNP AMAT AON EBAY CSX CMG CDNS MU ODFL KLAC ANET ADSK
AME TTD OTIS CPRT STX MSCI
""".split()  # FTNT..MSCI = 2026-08-22 full-corpus EDGAR sweep additions
UNIVERSE = list(dict.fromkeys(UNIVERSE))  # dedupe, keep order

FINANCIAL = {"Financial Services", "Insurance", "Banks", "Capital Markets"}
FIN_WORDS = ("Bancorp", "Bank", "Insurance", "Financial", "Financials",
             "Capital Markets", "Assurances", "Brokers")


def get_json(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=12) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 403) and i < tries - 1:
                time.sleep(2.5 * (i + 1)); continue
            return {"__err": f"HTTP {e.code}"}
        except Exception as e:
            if i < tries - 1:
                time.sleep(1.5); continue
            return {"__err": str(e)[:120]}
    return {"__err": "failed"}


def load_cache():
    """Return the data dict as-is (no whole-file expiry). Freshness is judged
    PER ENTRY by fetch_pair: a ticker whose last fetch failed keeps its old
    good record and is retried on the next firing — so one name's rate-limit
    burst never blanks another name out of the screen for a full TTL window."""
    if os.path.exists(CACHE):
        try:
            return json.load(open(CACHE)).get("data", {})
        except Exception:
            pass
    return {}


def save_cache(data, bump_ts=False):
    """Persist cache; only bump the freshness clock when new data was fetched
    (a cache-hit run must NOT push out the expiry — else the /loop's every-10-
    min firing would keep the cache warm forever and it would never refresh)."""
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    if not bump_ts and os.path.exists(CACHE):
        try:
            prev = json.load(open(CACHE))
            ts = prev.get("ts", 0)
        except Exception:
            ts = 0
    else:
        ts = time.time()
    with open(CACHE, "w") as f:
        json.dump({"ts": ts, "data": data}, f)


def fetch_pair(sym, token, cache, refresh, need_profile):
    """Fetch finnhub metric (always); profile2 only when sector/name unknown.
    Runs in a 3-worker pool: finnhub free tier is 60 req/min and each call
    takes ~3s, so 3 workers lands just under the cap without sleeping."""
    hit = cache.get(sym)
    if (not refresh and hit and hit.get("metric") and not hit.get("__err")
            and time.time() - hit.get("ts", 0) < TTL):
        return hit, "cache"
    m = get_json(f"{BASE}/stock/metric?symbol={sym}&metric=all&token={token}")
    rec = {"metric": m.get("metric") or {}, "ts": time.time()}
    if m.get("__err"):
        rec["__err"] = m["__err"]
    if need_profile and not rec.get("__err"):
        p = get_json(f"{BASE}/stock/profile2?symbol={sym}&token={token}")
        rec["profile"] = p if not p.get("__err") else {}
    if rec.get("__err") and hit and hit.get("metric") and not hit.get("__err"):
        return hit, "cache"  # transient failure: keep the last good record
    cache[sym] = rec
    return rec, "live"


# static financial-sector classification (banks/insurers/brokers/AM/exchanges/
# networks -> high leverage is the business model, so the D/E gate is skipped).
# Loaded from a JSON file next to this script; built by offline knowledge (see
# buffett_sectors.json). Tickers absent from it get a live profile2 fetch once,
# then the result is persisted back into the cache.
SECTOR_FILE = os.path.join(os.path.dirname(__file__), "buffett_sectors.json")
NAME_FILE = os.path.join(os.path.dirname(__file__), "quant", "bigmove",
                         "data", "sec_company_tickers.json")
NAME_OVERRIDES = {"AEP": "American Electric Power", "ABC": "Cencora",
                  "MMC": "Marsh & McLennan"}


def load_sectors():
    try:
        with open(SECTOR_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def load_names():
    """Ticker -> company name from the SEC company tickers file (free, local)."""
    names = {}
    try:
        with open(NAME_FILE) as f:
            for rec in json.load(f).values():
                names[rec.get("ticker")] = rec.get("title")
    except Exception:
        pass
    names.update(NAME_OVERRIDES)
    return names


def screen(sym, rec, sectors):
    """Return (score, reasons) or (None, fail_reason)."""
    if rec.get("__err"):
        return None, rec["__err"]
    m = rec["metric"]; p = rec.get("profile") or {}
    # finnhub marketCapitalization is in USD *millions*
    mc = (m.get("marketCapitalization") or p.get("marketCapitalization") or 0) * 1e6
    if not mc:
        return None, "no market cap"
    if mc < 35e9:
        return None, f"cap {mc/1e9:.0f}B < $35B gate"
    sector = p.get("finnhubIndustry") or ""
    name = p.get("name")
    is_fin = sectors.get(sym, False) or any(
        w.lower() in (sector.lower() or "none") or w.lower() in (name or "").lower()
        for w in FIN_WORDS)

    # finnhub /stock/metric returns ratios as PERCENT (42.99 = 42.99%)
    roe = m.get("roeTTM")
    nm = m.get("netProfitMarginTTM")
    om = m.get("operatingMarginTTM")
    if roe is None or nm is None or om is None:
        return None, f"missing quality (roe={roe} nm={nm} om={om})"
    roe, nm, om = roe / 100.0, nm / 100.0, om / 100.0
    if roe < 0.05 or nm < 0.02:
        return None, f"weak quality roe={roe:.1%} nm={nm:.1%}"
    d2e = m.get("debtEquityTTM")
    if d2e is None:
        d2e = m.get("totalDebt/totalEquityQuarterly")
    if not is_fin and d2e is not None and d2e > 2.5:
        return None, f"d/e {d2e:.2f} too high"

    # sub-scores 0..100
    s_roe = min(100, max(0, (roe - 0.10) / 0.15 * 100))          # 10%->0, 25%+->100
    s_mar = min(100, max(0, (om + nm) / 2 / 0.20 * 100))         # avg margin 20%->100
    if is_fin or d2e is None:
        s_dbt = 60.0
    else:
        s_dbt = min(100, max(0, 100 - d2e * 40))                 # 0->100, 1.0->60, 2.5->0
    eg = m.get("epsGrowthTTMYoy"); rg = m.get("revenueGrowthTTMYoy")
    if eg is None or rg is None:
        s_grw = 40.0
    else:
        eg, rg = eg / 100.0, rg / 100.0
        s_grw = min(100, max(0, (eg + rg) / 2 / 0.15 * 100))     # 15% combo->100
    fpe = m.get("forwardPE")
    if fpe is None or fpe <= 0:
        s_val = 30.0
    elif fpe <= 15:
        s_val = 100.0
    elif fpe <= 25:
        s_val = 100 - (fpe - 15) / 10 * 55
    else:
        s_val = max(0, 45 - (fpe - 25) / 10 * 45)
    dy = (m.get("dividendYieldIndicatedAnnual") or 0) / 100.0
    s_cap = min(100, dy / 0.06 * 100)                            # 6% yield->100
    beta = m.get("beta")
    s_def = 100.0 if beta is None else min(100, max(40, 100 - max(0, beta - 1.0) * 90))

    score = 0.30 * s_roe + 0.20 * s_mar + 0.15 * s_dbt + 0.15 * s_grw + \
            0.10 * s_val + 0.05 * s_cap + 0.05 * s_def
    return round(score, 1), {"roe": roe, "nm": nm, "om": om, "d2e": d2e, "fpe": fpe,
                             "eg": eg, "rg": rg, "dy": dy, "mc": mc, "sector": sector,
                             "name": p.get("name"), "beta": beta}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--buy", action="store_true",
                    help="buy mode: drop fwd P/E > 30 (valuation discipline), fill to --top")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    token = api_key("FINNHUB_KEY")
    if not token:
        sys.exit("no FINNHUB_KEY in .env.local")

    cache = {} if args.refresh else load_cache()
    sectors = load_sectors()
    names = load_names()
    live = 0
    import threading
    from concurrent.futures import ThreadPoolExecutor

    def one(s):
        nonlocal live
        need_profile = s not in sectors and not (cache.get(s, {}).get("profile"))
        _, how = fetch_pair(s, token, cache, args.refresh, need_profile)
        if how == "live":
            with threading.Lock():
                live += 1
        return s

    with ThreadPoolExecutor(max_workers=3) as ex:
        for _ in ex.map(one, UNIVERSE):
            pass
    if live:
        print(f"  {live}/{len(UNIVERSE)} live fetches (rest from cache)", file=sys.stderr)
    save_cache(cache, bump_ts=live > 0)

    ranked = []
    for s in UNIVERSE:
        sc, why = screen(s, cache.get(s) or {}, sectors)
        if sc is not None:
            ranked.append((sc, s, why))
    ranked.sort(key=lambda r: -r[0])
    top = ranked[: max(args.top, 30)]

    # Buffett rule #1 overlay: 10-year EPS consistency from local EDGAR facts.
    # TTM growth alone is misleading (cyclicals in recovery score too high);
    # adjust score: -1pt per loss year in the last 10, -5 per 1.0 CV above 0.8.
    eps_hist = {}
    for sc, s, w in top:
        fp = os.path.join(EDGAR_FACTS, f"{s}.json")
        if not os.path.exists(fp):
            continue
        pairs = annual_eps(fp)
        if not pairs:
            continue
        vals = [v for _, v in pairs]
        pos = sum(1 for v in vals if v > 0)
        mean = sum(vals) / len(vals)
        cv = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5 / abs(mean) if mean else 9.9
        ups = sum(1 for a, b in zip(vals[1:], vals[:-1]) if b > a)
        eps_hist[s] = {"pos": pos, "n": len(vals), "ups": ups, "cv": cv,
                       "hist": " ".join(f"{y}:{v:,.1f}" for y, v in pairs[:5])}
        w["eps_adj"] = 10 * (pos / 10.0 - 1) - 5 * max(0.0, cv - 0.8)
    for sc, s, w in top:
        if "eps_adj" in w:
            w["score_adj"] = round(sc + w["eps_adj"], 1)
        else:
            w["score_adj"] = sc
    top.sort(key=lambda r: -r[2].get("score_adj", r[0]))
    if args.buy:
        # BUY mode: same quality ranking, but refuse to pay up — drop anything
        # above the 30x fwd P/E discipline cap and fill to args.top from the
        # ranked pool (quality is worthless if the price is wrong).
        buyable = [r for r in top
                   if (r[2].get("fpe") or 999) <= 30.0]
        top = buyable[: args.top] if len(buyable) >= args.top else top[: args.top]
    else:
        top = top[: args.top]

    if args.json:
        out = [{"rank": i + 1, "symbol": s, "score": w.get("score_adj", sc),
                "name": names.get(s),
                "sector": w.get("sector"), "roe": w.get("roe"), "opMargin": w.get("om"),
                "netMargin": w.get("nm"), "debtEquity": w.get("d2e"), "fwdPE": w.get("fpe"),
                "epsGrowth": w.get("eg"), "revenueGrowth": w.get("rg"),
                "divYield": w.get("dy"), "mcapB": round(w.get("mc", 0) / 1e9, 1)}
               for i, (sc, s, w) in enumerate(top)]
        print(json.dumps(out, indent=2))
        return

    print(f"# Buffett-rule top {len(top)} US stocks  ({time.strftime('%Y-%m-%d %H:%M')}  "
          f"universe={len(UNIVERSE)} passed={len(ranked)} live={live})  [finnhub]")
    print("Rules: ROE>=5% & NPM>=2% gates, D/E<=2.5 (ex-financials), FwdP/E<=25 ideal, "
          "cap>=$35B | research only, not advice\n")
    hdr = (f"{'#':>2} {'SYM':<6} {'SCORE':>5} {'ROE':>6} {'OPM':>5} {'NPM':>5} "
           f"{'D/E':>5} {'FwdPE':>6} {'EG':>5} {'RG':>5} {'Div':>4} {'Cap$B':>7} "
           f"{'10y':>9}  Company")
    print(hdr); print("-" * len(hdr))
    for i, (sc, s, w) in enumerate(top):
        tag = "FIN" if sectors.get(s) else "-"
        e = eps_hist.get(s)
        e10 = f"{e['pos']}/{e['n']}({e['cv']:.2f})" if e else "-"
        print(f"{i+1:>2} {s:<6} {w['score_adj']:>5.1f} {w['roe']:>6.1%} {w['om']:>5.1%} "
              f"{w['nm']:>5.1%} {w['d2e'] if w['d2e'] is not None else 0:>5.2f} "
              f"{w['fpe'] if w['fpe'] is not None else 0:>6.1f} "
              f"{w['eg'] or 0:>5.1%} {w['rg'] or 0:>5.1%} {w['dy']*100 or 0:>4.1f} "
              f"{w['mc']/1e9:>7.0f} {e10:>9}  {names.get(s, '?')[:44]}")
    drops = [(s, screen(s, cache.get(s) or {}, sectors)[1]) for s in UNIVERSE
             if screen(s, cache.get(s) or {}, sectors)[0] is None][:8]
    print("\nDropped examples:", "; ".join(f"{s}: {r}" for s, r in drops))

    # drift vs previous run (for the 10-min /loop)
    LAST = os.path.join(os.path.dirname(__file__), "logs", "buffett_last_run.json")
    now_syms = [s for _, s, _ in top]
    try:
        prev = json.load(open(LAST))["top"]
        moved_in = [s for s in now_syms if s not in prev]
        moved_out = [s for s in prev if s not in now_syms]
        if moved_in or moved_out:
            print("vs last run: in:", ",".join(moved_in), " out:", ",".join(moved_out))
        else:
            print("vs last run: top-20 unchanged")
    except Exception:
        pass
    os.makedirs(os.path.dirname(LAST), exist_ok=True)
    json.dump({"ts": time.time(), "top": now_syms}, open(LAST, "w"))


if __name__ == "__main__":
    main()
