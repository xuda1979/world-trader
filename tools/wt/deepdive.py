"""Deep-dive analysis for a single ticker.

Aggregates EVERY available data signal on one ticker into a single structured
report. This is the 'in-depth analysis' the user asked for: enough information
collected in one place that a trader (or an LLM judge) can make a real call.

Data gathered (all free, parallel):
  - Price/quote + 20/50/200-day technicals (sources.py + analysis.py)
  - Per-ticker news headlines (news.py: Finnhub + Polygon)
  - Recent SEC filings (altdata.sec_recent_filings -- 8-K, S-1, DEF 14A)
  - Analyst recommendation (altdata.analyst_target -- Finnhub /recommendation)
  - Insider transactions (altdata.insider_transactions -- Finnhub /insider-transactions)
  - Earnings surprises (altdata.earnings_surprise -- Finnhub /stock/earnings)
  - Fundamentals (altdata.basic_metrics -- Finnhub /stock/metric)
  - Upcoming catalysts (catalysts.catalyst_for -- earnings/FDA/IPO/dividend)
  - Peer cluster + themes (peers.peers_of, peers.clusters_of)
  - Hacker News mention count (altdata.hn_mentions)
  - GDELT tone for the company name (news.gdelt_tone)
  - LLM judgment (llm.news_sentiment if a key is set)

Output: a structured dict that report.py can print as a card AND that the LLM
can consume as context for a deep analysis.

The LLM deep_dive_analysis() prompt is broader than the existing
news_sentiment() -- it sees the WHOLE picture (technicals + catalysts + insider
+ analyst + peers + filings) and produces a structured trade thesis.

Research only. Not financial advice.
"""
from __future__ import annotations
import datetime
from concurrent.futures import ThreadPoolExecutor
from . import core, sources, news, altdata, catalysts, peers, llm


def _safe(fn, *args, **kw):
    """Run fn; return (result, None) or (None, err_string). Never raises."""
    try:
        r = fn(*args, **kw)
        if isinstance(r, tuple) and len(r) == 2:
            return r
        return r, None
    except Exception as e:
        return None, core.describe_err(e)


def gather(sym, *, want_llm=True, want_sec=True, want_hn=True,
           want_gdelt=True, want_peers=True, days_news=7):
    """Gather all available data on a single ticker. Returns a structured dict.

    All sections are fetched in parallel; each section carries its own error
    so a single failure never blocks the rest. This is the data-collection
    half of the deep-dive; deep_dive_analysis() (LLM) consumes this dict.
    """
    sym = str(sym).upper()
    out = {"sym": sym, "ts": core._now_iso() if hasattr(core, "_now_iso") else None}

    # ---- parallel fetch (one call per section) ----
    sections: dict = {}
    def _register(key, fn, *args, **kw):
        sections[key] = (fn, args, kw)

    # Price/quote (try multiple sources; first success wins)
    def _quote():
        # Prefer Finnhub for US, Sina for CN, etc. -- let sources.quote pick.
        if hasattr(sources, "quote"):
            return sources.quote(sym)
        # Fallback: direct finnhub_quote
        if hasattr(sources, "finnhub_quote"):
            return sources.finnhub_quote(sym)
        return None, "no quote fn"

    _register("quote", _quote)
    _register("news",  news.ticker_news, sym, False, days_news)
    _register("catalyst", catalysts.catalyst_for, sym, 30)
    _register("analyst", altdata.analyst_target, sym)
    _register("insider", altdata.insider_transactions, sym, 8)
    _register("earnings", altdata.earnings_surprise, sym, 4)
    _register("fundamentals", altdata.basic_metrics, sym)
    if want_sec:
        _register("sec_filings", altdata.sec_recent_filings, sym, 90)
    if want_hn:
        _register("hn", altdata.hn_mentions, sym, 14)

    # Peer cluster + themes (cheap; static)
    if want_peers:
        out["peers"] = peers.peers_of(sym)
        out["clusters"] = peers.clusters_of(sym)
    else:
        out["peers"] = []
        out["clusters"] = []

    # GDELT tone (separate because it uses company name, not ticker)
    if want_gdelt:
        # Resolve company name from Finnhub profile
        cname = None
        k = core.api_key("FINNHUB_KEY")
        if k:
            try:
                d = core.get_json(f"https://finnhub.io/api/v1/stock/profile2?symbol={sym}&token={k}", timeout=6)
                cname = (d.get("name") or "").strip()
            except Exception:
                pass
        if cname:
            _register("gdelt_tone", news.gdelt_tone, cname, 48)
        else:
            _register("gdelt_tone", news.gdelt_tone, sym, 48)

    # ---- run all in parallel ----
    def _one(item):
        key, (fn, args, kw) = item
        v, err = _safe(fn, *args, **kw)
        return key, (v if v is not None else {"err": err})
    with ThreadPoolExecutor(max_workers=min(10, len(sections))) as p:
        results = list(p.map(_one, sections.items()))
    out.update(dict(results))

    # ---- LLM judgment (optional, after everything else is gathered) ----
    if want_llm:
        headlines = []
        n = out.get("news") or {}
        for h in (n.get("headlines") or []):
            t = h.get("title") if isinstance(h, dict) else str(h)
            if t:
                headlines.append(t)
        # also include 8-K item descriptions as 'headlines' for the LLM
        sec = out.get("sec_filings") or []
        if isinstance(sec, list):
            for f in sec[:3]:
                items = f.get("items") or ""
                if items:
                    headlines.append(f"SEC {f.get('form','')} filed ({items})")
        try:
            out["llm"] = llm.news_sentiment(sym, headlines)
        except Exception as e:
            out["llm"] = {"err": core.describe_err(e)}

    return out


def deep_dive_analysis(sym, data=None, *, want_llm=True):
    """Generate a deep trade-thesis analysis for `sym`.

    If `data` is None, calls gather() first. If want_llm and an LLM key is set,
    asks the LLM to produce a structured thesis consuming the FULL data picture:
    technicals + news + catalysts + insider + analyst + filings + peers.
    Returns {thesis, bias, confidence, key_catalysts, risks, suggested_entry,
             suggested_stop, suggested_target, provider}.

    The LLM never decides the trade; the backtested gate in analysis.py does.
    The thesis is INFORMATIONAL -- it surfaces the qualitative picture the
    numbers can't capture (e.g. 'CEO sold $20M last week + 8-K filed Item 5.02
    = leadership change risk; technicals bullish but catalyst headwind')."""
    if data is None:
        data = gather(sym, want_llm=False)  # we'll call LLM ourselves below
    if not want_llm:
        return {"data": data, "thesis": None, "err": "LLM disabled"}

    # Build a compact text summary of the data for the LLM prompt
    summary = _summarize_for_llm(sym, data)
    if not summary:
        return {"data": data, "thesis": None, "err": "no data to summarize"}

    # Pick a provider (xAI first, Anthropic fallback)
    result = None
    for provider in ("xai", "anthropic"):
        key = core.api_key("XAI_API_KEY" if provider == "xai" else "ANTHROPIC_API_KEY")
        if not key:
            continue
        try:
            if provider == "xai":
                result = _xai_thesis(sym, summary)
            else:
                result = _anthropic_thesis(sym, summary)
            if result:
                result["provider"] = provider
                break
        except Exception:
            result = None
    return {"data": data, "thesis": result}


# ---------------------------------------------------------------------------
# LLM prompts and providers
# ---------------------------------------------------------------------------
_SYSTEM = (
    "You are a disciplined short-term trader. Holding period is <= 1 day. "
    "You synthesize technicals, news flow, SEC filings, insider activity, "
    "analyst sentiment, and peer/themes into a CONCISE trade thesis. "
    "You are skeptical: a single rumor is 0.3 confidence max. "
    "You respect the backtested gate; your job is to surface qualitative "
    "factors the numbers miss. You NEVER recommend holding through a major "
    "scheduled catalyst. Respond ONLY with the JSON object specified."
)

def _summarize_for_llm(sym, data):
    """Build a compact text summary of the gathered data for the LLM."""
    parts = [f"TICKER: {sym}"]
    # quote
    q = data.get("quote")
    if isinstance(q, dict) and q.get("c") is not None:
        parts.append(f"PRICE: {q.get('c')} (chg {q.get('dp')}%)")
    # news
    n = data.get("news") or {}
    if isinstance(n, dict) and n.get("count"):
        parts.append(f"NEWS: {n.get('count')} articles in last 7d; latest: {n.get('latest')}")
        if n.get("net") is not None:
            parts.append(f"NEWS sentiment: net={n.get('net')} (pos={n.get('pos')}, neg={n.get('neg')})")
    # catalyst
    c = data.get("catalyst")
    if isinstance(c, dict) and c.get("date"):
        parts.append(f"CATALYST: {c.get('kind')} on {c.get('date')} -- {c.get('detail','')[:80]}")
    # analyst
    a = data.get("analyst")
    if isinstance(a, dict) and a.get("n_analysts"):
        if a.get("score") is not None:
            parts.append(f"ANALYSTS: score={a.get('score')} (-2..+2), n={a.get('n_analysts')}, strong_buy={a.get('strong_buy')}, sell={a.get('sell')}")
        elif a.get("mean") is not None:
            parts.append(f"ANALYSTS: mean target={a.get('mean')} vs last={a.get('last')} (implied {a.get('implied_upside_pct')}%)")
    # insider
    ins = data.get("insider")
    if isinstance(ins, dict) and (ins.get("n_buys") or ins.get("n_sells")):
        parts.append(f"INSIDER: buys={ins.get('n_buys')}, sells={ins.get('n_sells')}, net_shares={ins.get('net_shares')}")
    # earnings
    e = data.get("earnings")
    if isinstance(e, list) and e:
        last = e[0]
        parts.append(f"EARNINGS last qtr: actual={last.get('actual')} vs est={last.get('estimate')} (surprise {last.get('surprise_pct')}%)")
    # fundamentals
    fnd = data.get("fundamentals")
    if isinstance(fnd, dict) and fnd.get("market_cap"):
        parts.append(f"FUND: mcap={fnd.get('market_cap')}, P/E={fnd.get('pe_ttm')}, beta={fnd.get('beta')}, 52w {fnd.get('52w_low')}-{fnd.get('52w_high')}")
    # SEC filings
    sec = data.get("sec_filings")
    if isinstance(sec, list) and sec:
        recent = "; ".join(f"{x.get('form')} {x.get('filed')} ({x.get('items','')[:30]})" for x in sec[:3])
        parts.append(f"SEC FILINGS: {recent}")
    # peers
    if data.get("peers"):
        parts.append(f"PEERS: {', '.join(data['peers'][:6])}")
    if data.get("clusters"):
        parts.append(f"CLUSTERS: {', '.join(data['clusters'])}")
    # HN
    h = data.get("hn")
    if isinstance(h, dict) and h.get("count"):
        parts.append(f"HN: {h.get('count')} stories (tech-sentiment proxy)")
    # GDELT
    g = data.get("gdelt_tone")
    if isinstance(g, dict) and g.get("articles"):
        parts.append(f"GDELT tone: {g.get('avg_tone')} over {g.get('articles')} articles")
    return "\n".join(parts) if len(parts) > 1 else None


def _xai_thesis(sym, summary):
    """xAI Grok deep-dive thesis. Returns dict or None."""
    import json
    key = core.api_key("XAI_API_KEY")
    if not key:
        return None
    prompt = (f"{summary}\n\n"
              "Produce a short-term (<= 1 day) trade thesis. JSON only:\n"
              '{"bias": "long"|"short"|"no_trade", '
              '"confidence": 0.0-1.0, '
              '"thesis": "one sentence", '
              '"key_catalysts": ["c1", "c2"], '
              '"risks": ["r1", "r2"], '
              '"avoid_holding_through": "catalyst name or null"}')
    body = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    resp = core.http_post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        body=json.dumps(body).encode("utf-8"),
        timeout=25,
    )
    if not resp:
        return None
    d = json.loads(resp)
    text = (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return _parse_thesis_json(text)


def _anthropic_thesis(sym, summary):
    """Anthropic Claude deep-dive thesis. Returns dict or None."""
    import json
    key = core.api_key("ANTHROPIC_API_KEY")
    if not key:
        return None
    prompt = (f"{summary}\n\n"
              "Produce a short-term (<= 1 day) trade thesis. JSON only:\n"
              '{"bias": "long"|"short"|"no_trade", '
              '"confidence": 0.0-1.0, '
              '"thesis": "one sentence", '
              '"key_catalysts": ["c1", "c2"], '
              '"risks": ["r1", "r2"], '
              '"avoid_holding_through": "catalyst name or null"}')
    body = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 400,
        "system": _SYSTEM,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = core.http_post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key,
                 "anthropic-version": "2023-06-01",
                 "Content-Type": "application/json"},
        body=json.dumps(body).encode("utf-8"),
        timeout=25,
    )
    if not resp:
        return None
    d = json.loads(resp)
    content = (d.get("content") or [{}])[0].get("text", "")
    return _parse_thesis_json(content)


def _parse_thesis_json(text):
    """Parse the LLM JSON response. Returns dict or None."""
    import json
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        # strip language tag
        if t.startswith("json"):
            t = t[4:]
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b < 0 or b <= a:
        return None
    try:
        d = json.loads(t[a:b+1])
    except json.JSONDecodeError:
        return None
    bias = str(d.get("bias", "")).lower().strip()
    if bias not in ("long", "short", "no_trade"):
        return None
    try:
        conf = float(d.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    return {
        "bias": bias,
        "confidence": conf,
        "thesis": str(d.get("thesis", "")).strip()[:300],
        "key_catalysts": [str(x).strip()[:80] for x in (d.get("key_catalysts") or [])][:5],
        "risks": [str(x).strip()[:80] for x in (d.get("risks") or [])][:5],
        "avoid_holding_through": d.get("avoid_holding_through"),
    }


# ---------------------------------------------------------------------------
# Pretty-printer for CLI use
# ---------------------------------------------------------------------------
def print_deep_dive(sym, data=None, *, want_llm=True, max_width=78):
    """Print a human-readable deep-dive card for `sym`. Used by scan.py --deep."""
    if data is None:
        data = gather(sym, want_llm=want_llm)
    sym = str(sym).upper()
    line = "=" * max_width
    print(f"\n{line}\nDEEP DIVE: {sym}\n{line}")
    # Quote
    q = data.get("quote")
    if isinstance(q, dict) and q.get("c") is not None:
        chg = q.get("dp")
        chg_str = f" ({chg:+.2f}%)" if isinstance(chg, (int, float)) else ""
        print(f"  Price: {q.get('c')}{chg_str}  H={q.get('h')} L={q.get('l')} O={q.get('o')}")
    # Clusters + peers
    if data.get("clusters"):
        print(f"  Clusters: {', '.join(data['clusters'])}")
    if data.get("peers"):
        print(f"  Peers: {', '.join(data['peers'][:8])}")
    # Catalyst
    c = data.get("catalyst")
    if isinstance(c, dict) and c.get("date"):
        print(f"  Catalyst: [{c.get('kind','')}] {c.get('date')} -- {(c.get('detail') or '')[:70]}")
    else:
        print(f"  Catalyst: (none in next 30d)")
    # News
    n = data.get("news") or {}
    if isinstance(n, dict) and n.get("count"):
        print(f"  News: {n.get('count')} articles/7d; latest: {(n.get('latest') or '')[:70]}")
        if n.get("net") is not None:
            print(f"  News sentiment: net={n.get('net')} (pos={n.get('pos')}, neg={n.get('neg')})")
    # Analyst
    a = data.get("analyst")
    if isinstance(a, dict) and a.get("n_analysts"):
        if a.get("score") is not None:
            print(f"  Analysts: score={a.get('score')} (-2..+2), n={a.get('n_analysts')}, strong_buy={a.get('strong_buy')}, sell={a.get('sell')}")
        elif a.get("mean") is not None:
            print(f"  Analyst target: mean={a.get('mean')} vs last={a.get('last')} (implied {a.get('implied_upside_pct')}%)")
    # Insider
    ins = data.get("insider")
    if isinstance(ins, dict) and (ins.get("n_buys") or ins.get("n_sells")):
        print(f"  Insider (60d): buys={ins.get('n_buys')}, sells={ins.get('n_sells')}, net={ins.get('net_shares')} sh")
        for tx in (ins.get("recent") or [])[:3]:
            print(f"    {tx.get('date')} {tx.get('kind'):4} {tx.get('shares',0):>+10.0f} @ {tx.get('price')} -- {tx.get('owner','')[:24]}")
    # Earnings
    e = data.get("earnings")
    if isinstance(e, list) and e:
        last = e[0]
        print(f"  Last earnings ({last.get('period')}): actual={last.get('actual')} vs est={last.get('estimate')} (surprise {last.get('surprise_pct')}%)")
    # Fundamentals
    fnd = data.get("fundamentals")
    if isinstance(fnd, dict) and fnd.get("market_cap"):
        print(f"  Fund: mcap={fnd.get('market_cap')}, P/E={fnd.get('pe_ttm')}, beta={fnd.get('beta')}, 52w {fnd.get('52w_low')}-{fnd.get('52w_high')}")
    # SEC filings
    sec = data.get("sec_filings")
    if isinstance(sec, list) and sec:
        print(f"  SEC filings (last 90d): {len(sec)}")
        for f in sec[:3]:
            print(f"    {f.get('form'):6} {f.get('filed')} items={f.get('items','')[:50]}")
    # HN
    h = data.get("hn")
    if isinstance(h, dict) and h.get("count"):
        print(f"  Hacker News: {h.get('count')} stories (tech-sentiment proxy)")
        for s in (h.get("stories") or [])[:2]:
            print(f"    pts={s.get('points'):>4}  {(s.get('title') or '')[:60]}")
    # GDELT
    g = data.get("gdelt_tone")
    if isinstance(g, dict) and g.get("articles"):
        print(f"  GDELT tone (48h): {g.get('avg_tone')} over {g.get('articles')} articles")
    # LLM
    ll = data.get("llm")
    if isinstance(ll, dict) and ll.get("bias"):
        print(f"  LLM: bias={ll.get('bias')} conf={ll.get('confidence')} -- {(ll.get('reason') or '')[:70]}")
    print(line)


# ---------------------------------------------------------------------------
# BREAKING NEWS scan (added 2026-07-12)
# ---------------------------------------------------------------------------
# The user insight: "whenever there are big breaking news in the world, there
# might be impact to some financial instruments. In these cases, you should do
# research and analysis so we can find good trade opportunities, i.e., highly
# profitable with low risks short term trading opportunity with good liquidity."
#
# This function:
#   1. Fetches ALL RSS feeds (cheap, parallel).
#   2. Scores each headline by IMPACT (theme match + keyword severity + source
#      breadth -- how many distinct feeds report the same theme in the last
#      `window_hours`).
#   3. For each high-impact theme, finds the watch_tickers (peers.THEMES).
#   4. For each watch ticker, runs the FULL deep-dive pipeline (gather + LLM
#      thesis). Filters to LIQUID names only (market cap > $500M, or ETF).
#   5. Returns a structured {theme, headline, ticker_analyses: [...]} list,
#      sorted by impact score.
#
# The output is a research report, NOT a trade signal. Each ticker's thesis
# still respects the backtested gate (analysis.py) -- this just surfaces which
# tickers deserve a deeper look based on the breaking-news picture.

# Liquidity filter: skip illiquid names for breaking-news trades (the user
# specifically asked for "good liquidity"). $500M market cap is a reasonable
# floor for short-term trades (tight bid/ask, borrowable, no pump-and-dump risk).
MIN_MARKET_CAP_BN = 500  # $500M
# ETFs are always considered liquid regardless of fund size.
_ETF_TICKERS = {
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "VEA", "VWO", "EEM", "EFA",
    "XLE", "XLF", "XLI", "XLK", "XLB", "XLP", "XLU", "XLV", "XLY", "XLC",
    "KWEB", "FXI", "MCHI", "ASHR", "CNY", "EWJ", "EWY", "EWZ", "INDA",
    "USO", "BNO", "GLD", "SLV", "TLT", "HYG", "LQD", "BITO", "BITQ",
    "KRE", "KBE", "ITA", "XME", "XOP", "OIH", "SMH", "SOXX", "IBB",
}

def _is_liquid(sym, fundamentals):
    """Decide if a ticker is liquid enough for a short-term breaking-news trade."""
    sym_u = str(sym).upper()
    if sym_u in _ETF_TICKERS:
        return True
    if not fundamentals:
        return False  # no data -> can't confirm liquidity -> skip
    mcap = fundamentals.get("market_cap")
    if mcap is None:
        return False
    # Finnhub market_cap is in MILLIONS. So 500 means $500M.
    try:
        return float(mcap) >= MIN_MARKET_CAP_BN
    except (TypeError, ValueError):
        return False

def _headline_impact_score(headlines, theme, hours=24):
    """Score a theme's breaking-news impact: 0-100.

    Higher = more sources covering it in the last `hours`. A single headline
    in one feed is low-impact (could be noise); the same theme across 4+ feeds
    is high-impact (genuine breaking news)."""
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=hours)).strftime("%a, %d %b %Y") if hours else ""
    distinct_feeds = set()
    distinct_headlines = set()
    for h in headlines:
        # h is a dict with feed, title, date
        if cutoff and (h.get("date") or "") < cutoff:
            continue
        distinct_feeds.add(h.get("feed"))
        distinct_headlines.add(h.get("title", "")[:80])
    # 50 pts for first feed, 10 pts per additional feed, cap 100
    score = min(100, 50 + 10 * max(0, len(distinct_feeds) - 1))
    return score, len(distinct_feeds), len(distinct_headlines)

def breaking_news_scan(want_llm=True, window_hours=24, max_themes=8, max_tickers_per_theme=5):
    """Detect breaking-news themes and deep-dive each affected ticker.

    Returns a list of {theme, hint, rationale, impact_score, n_feeds,
    n_headlines, top_headlines, ticker_analyses: [...]} sorted by impact_score
    descending. ticker_analyses is a list of {sym, liquid, data, thesis}
    (one per watch ticker that passed the liquidity filter).

    The deep-dive per ticker is the SAME gather() + deep_dive_analysis() used
    by `scan.py --deep SYM`, so the LLM sees the full picture (technicals +
    news + catalysts + insider + analyst + filings + peers) and produces a
    structured thesis.
    """
    # 1. Fetch all feeds
    feeds = news.fetch_all()
    # 2. Find theme matches across all headlines
    cands = peers.spillover_candidates(feeds)
    if not cands:
        return []
    # 3. Group by theme
    by_theme: dict = {}
    for t, reasons in cands.items():
        for r in reasons:
            by_theme.setdefault(r["theme"], []).append({
                "ticker": t, "headline": r["headline"],
                "feed": r.get("feed", "?"),
                "date": r.get("date", ""),
            })
    # 4. Score each theme and deep-dive top tickers
    results = []
    for theme, hits in by_theme.items():
        spec = peers.THEMES.get(theme, {})
        headlines_for_theme = [{"feed": h["feed"], "title": h["headline"],
                                "date": h.get("date", "")} for h in hits]
        score, n_feeds, n_headlines = _headline_impact_score(headlines_for_theme, theme, window_hours)
        # collect distinct tickers for this theme, in order of appearance
        tickers_seen = []
        seen = set()
        for h in hits:
            t = h["ticker"]
            if t not in seen:
                tickers_seen.append(t)
                seen.add(t)
        # cap tickers per theme
        tickers_seen = tickers_seen[:max_tickers_per_theme]
        # deep-dive each ticker (sequential to bound LLM cost)
        ticker_analyses = []
        for t in tickers_seen:
            data = gather(t, want_llm=False)  # gather without LLM first
            liquid = _is_liquid(t, data.get("fundamentals"))
            thesis = None
            if want_llm and liquid:
                res = deep_dive_analysis(t, data=data, want_llm=True)
                thesis = res.get("thesis")
            ticker_analyses.append({
                "sym": t, "liquid": liquid,
                "price": (data.get("quote") or {}).get("c"),
                "market_cap": (data.get("fundamentals") or {}).get("market_cap"),
                "data": data,
                "thesis": thesis,
            })
        # top headlines for display
        top_headlines = list(dict.fromkeys(h["headline"] for h in hits))[:5]
        results.append({
            "theme": theme,
            "hint": spec.get("hint", "mixed"),
            "rationale": spec.get("rationale", ""),
            "impact_score": score,
            "n_feeds": n_feeds,
            "n_headlines": n_headlines,
            "top_headlines": top_headlines,
            "ticker_analyses": ticker_analyses,
        })
    results.sort(key=lambda r: r["impact_score"], reverse=True)
    return results[:max_themes]

def print_breaking_news(results, want_llm=True, max_width=78):
    """Print breaking-news scan results as a human-readable report."""
    if not results:
        print("\n=== BREAKING NEWS SCAN: no high-impact themes detected ===")
        return
    line = "=" * max_width
    print(f"\n{line}\n=== BREAKING NEWS SCAN (cross-asset spillover) ===\n{line}")
    for r in results:
        print(f"\n--- THEME: {r['theme']}  (impact {r['impact_score']}/100, "
              f"{r['n_feeds']} feeds, {r['n_headlines']} headlines) ---")
        print(f"  hint: {r['hint']}")
        print(f"  rationale: {r['rationale'][:200]}")
        print(f"  top headlines:")
        for h in r["top_headlines"][:3]:
            print(f"    - {h[:90]}")
        print(f"  affected tickers (liquidity-filtered):")
        for ta in r["ticker_analyses"]:
            liq_tag = "LIQUID" if ta["liquid"] else "illiquid-skip"
            mc = ta.get("market_cap")
            mc_str = f"${mc:.0f}M" if mc is not None else "?"
            print(f"    [{liq_tag:11}] {ta['sym']:6} px={ta.get('price')} mcap={mc_str}")
            th = ta.get("thesis")
            if th:
                print(f"      LLM: bias={th.get('bias')} conf={th.get('confidence')} "
                      f"-- {th.get('thesis','')[:100]}")
                if th.get("avoid_holding_through"):
                    print(f"      AVOID HOLDING THROUGH: {th.get('avoid_holding_through')}")
    print(line)

if __name__ == "__main__":
    import sys
    if "--breaking" in sys.argv:
        results = breaking_news_scan(want_llm=("--no-llm" not in sys.argv))
        print_breaking_news(results, want_llm=("--no-llm" not in sys.argv))
    else:
        sym = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
        print_deep_dive(sym, want_llm=("--no-llm" not in sys.argv))
