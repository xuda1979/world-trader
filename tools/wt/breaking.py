"""Breaking-news catalyst engine.

Goal: when big news breaks (e.g. "Kimi-3 released", "PBOC cuts RRR", "Fed
emergency cut"), detect it within minutes, identify the affected tickers in
BOTH the US and China markets, and produce tradeable candidate ideas with
directional bias + rationale.

This module is the glue between three pieces of infrastructure that already
exist in this repo:

  1. `news.fetch_all()` -- the 109-feed RSS library (now includes CN tech/AI)
  2. `peers.THEMES` -- keyword -> watch_tickers maps for spillover candidates
  3. `llm.news_sentiment` / `deepdive.deep_dive_analysis` -- LLM thesis layer

What this module ADDS on top:

  * EVENT_TYPES: a typed taxonomy of high-impact catalysts (AI model release,
    FDA, M&A, regulatory, geopolitical, central-bank, earnings, etc.) with
    severity weights and default directional hints per theme.
  * COMPANY_ALIASES: name -> ticker map for both US and China names that
    frequently appear in headlines but aren't tickered in the headline text
    (e.g. "Moonshot AI" -> 688628.SH, "DeepSeek" -> private, but its
    competitors like BABA/00700.HK are tradeable).
  * `detect_events(items_by_feed, hours=...)` -- scans ALL RSS headlines,
    matches against EVENT_TYPES + THEMES + COMPANY_ALIASES, returns a list
    of deduplicated BreakingEvent dicts.
  * `resolve_tickers(event)` -- expands a detected event into a concrete
    ticker list with directional bias per ticker.
  * Event-cache (JSON file at tools/logs/breaking-events.json) so repeated
    runs only surface NEW events (the watch loop doesn't re-alert on the
    same Kimi-3 headline every 5 minutes).
  * `watch_once(...)` -- single-pass detect -> enrich -> alert. Used by both
    the `--breaking-watch` CLI mode and the 5-min launchd job.
  * `watch_loop(interval=...)` -- blocking loop with dedup, for foreground use.

Design principles (inherited from the rest of the repo):
  * Hard gate stays in analysis.py -- this module SURFACES candidates, it
    does not approve trades. Every ticker it emits must still clear the
    backtested Sharpe/t/OOS gate before going into the opportunity table.
  * LLM is a tiebreaker, never the decision-maker.
  * Failures are isolated: one bad feed or one bad LLM call never breaks
    the loop.
  * Stdlib only.

Research only. Not financial advice.
"""
from __future__ import annotations
import hashlib, html, json, os, re, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from . import core, news, peers, llm, deepdive, alerts


def _clean_title(s):
    """Strip HTML tags + unescape entities. Some feeds (FiercePharma, etc.)
    include raw <a href>...</a> in their titles."""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", str(s))
    return html.unescape(s).strip()


# ============================================================================
# Event taxonomy
# ============================================================================
# Each event type has:
#   keywords:    lowercase phrases that, when found in a headline, suggest
#                this event type fired. Multi-word phrases are matched as
#                substrings; single tokens use word-boundary match.
#   severity:    1-5 base weight (5 = market-wide shock, 1 = niche catalyst).
#   default_hint: default directional hint for the theme as a whole, used
#                when no per-ticker hint is available. "long" / "short" / "mixed".
#   rationale:   human-readable one-liner for the report.

EVENT_TYPES = {
    "AI_MODEL_RELEASE": {
        "keywords": [
            "kimi", "deepseek", "qwen", "ernie", "glm-4", "chatglm",
            "moonshot ai", "zhipu ai", "minimax", "baichuan",
            "claude 4", "claude opus", "gpt-5", "gpt-6",
            "gemini ultra", "gemini 2", "llama 4", "mistral large",
            "releases new ai model", "unveils ai model", "launches ai model",
            "open-sources ai model", "frontier model",
        ],
        "severity": 4,
        "default_hint": "long",
        "rationale": "Frontier-AI model release. Lifts the AI supply chain: "
                     "GPU vendors (NVDA/AMD), power/cooling (VRT/SMCI), and "
                     "the releasing company's listed peers. In China, lifts "
                     "the releasing lab's parent and competitors.",
    },
    "AI_CAPEX": {
        "keywords": ["ai capex", "ai data center", "stargate", "ai compute",
                     "gpu order", "nvidia order", "amd order",
                     "hyperscaler capex", "ai infrastructure spend"],
        "severity": 4,
        "default_hint": "long",
        "rationale": "AI capex headline lifts the whole AI supply chain: GPU "
                     "vendors, networking, power/cooling, data-center REITs.",
    },
    "FDA_APPROVAL": {
        "keywords": ["fda approves", "fda approval", "approved by fda",
                     "fda clears", "fda grants", "positive phase 3",
                     "positive phase iii", "trial success", "trial met endpoint"],
        "severity": 5,
        "default_hint": "long",
        "rationale": "FDA approval / positive trial. Lifts the sponsor and "
                     "weighs on competitors with rival programs.",
    },
    "FDA_REJECTION": {
        "keywords": ["fda rejects", "fda rejection", "crl", "complete response letter",
                     "clinical hold", "trial failure", "trial missed endpoint",
                     "phase 3 failure", "negative phase 3"],
        "severity": 5,
        "default_hint": "short",
        "rationale": "FDA rejection / trial failure. Hits the sponsor hard; "
                     "can lift competitors with rival programs.",
    },
    "MA_DEAL": {
        "keywords": ["acquires ", "to acquire", "buyout", "merger agreement",
                     "take-private", "going private", "deal to buy",
                     "agrees to buy", "agrees to acquire"],
        "severity": 5,
        "default_hint": "long",
        "rationale": "M&A deal. Target typically pops to a premium; acquirer "
                     "mixed. Competitors can rerate on sector consolidation.",
    },
    "CHINA_REGULATORY": {
        "keywords": ["china crackdown", "china regulator", "china antitrust",
                     "china fine", "china gaming ban", "china data security",
                     "cyberspace administration of china", "cac ruling",
                     "china probe", "china investigation"],
        "severity": 4,
        "default_hint": "short",
        "rationale": "China regulatory action. Hits the whole China ADR "
                     "complex (KWEB components) and the named company's A-share peers.",
    },
    "CHINA_STIMULUS": {
        "keywords": ["china stimulus", "pboc cuts", "pboc raises",
                     "rrr cut", "rate cut in china", "china infrastructure push",
                     "china property rescue", "china consumption stimulus"],
        "severity": 4,
        "default_hint": "long",
        "rationale": "China stimulus / PBOC easing. Lifts China large-cap "
                     "(FXI/ASHR), China internet (KWEB), and commodity names.",
    },
    "CENTRAL_BANK": {
        "keywords": ["fed cuts rates", "fed raises rates", "fed hold",
                     "fomc decision", "powell says", "ecb cuts", "ecb hikes",
                     "boj hike", "boj intervention", "emergency rate cut",
                     "emergency rate hike"],
        "severity": 5,
        "default_hint": "mixed",
        "rationale": "Central-bank decision moves broad ETFs; cuts = risk-on, "
                     "hikes = risk-off. Trade via ETFs (cheap, liquid).",
    },
    "GEOPOLITICAL": {
        "keywords": ["sanctions", "export controls", "tariff hike",
                     "trade war", "invasion", "military strike",
                     "diplomatic severed", "embargo", "chip ban",
                     "semi export ban", "technology export ban"],
        "severity": 4,
        "default_hint": "mixed",
        "rationale": "Geopolitical escalation lifts defense (ITA components), "
                     "safe havens (GLD/TLT), and can hit the sanctioned country's ADRs.",
    },
    "OIL_SUPPLY_SHOCK": {
        "keywords": ["opec cut", "opec+ cut", "opec surprise cut",
                     "production cut", "pipeline attack", "refinery fire",
                     "oil embargo", "strait of hormuz", "red sea attack"],
        "severity": 4,
        "default_hint": "long",
        "rationale": "Oil supply shock lifts XLE/XOP components; weighs on "
                     "airlines/cruises. Trade via USO/XLE/energy equities.",
    },
    "BANK_RUN": {
        "keywords": ["bank run", "deposit flight", "bank failure",
                     "bank seized", "fdic seizes", "bank collapse"],
        "severity": 5,
        "default_hint": "short",
        "rationale": "Bank-run headline hits the named bank and can spread to "
                     "regional banks (KRE); flight-to-safety lifts TLT/TLT.",
    },
    "EARNINGS_SURPRISE": {
        "keywords": ["earnings beat", "earnings miss", "big earnings surprise",
                     "revenue beat", "revenue miss", "guidance raised",
                     "guidance cut", "raises full-year guidance",
                     "cuts full-year guidance"],
        "severity": 3,
        "default_hint": "mixed",
        "rationale": "Earnings surprise drives 1-5 day drift (PEAD). The "
                     "scanner's PEAD setup already covers this quantitatively.",
    },
    "ROCKET_REUSE": {
        "keywords": ["rocket landing", "reusable rocket", "booster recovery",
                     "rocket recycle", "fairing recovery", "caught booster",
                     "mechazilla", "chopsticks catch"],
        "severity": 3,
        "default_hint": "short",
        "rationale": "Rocket-reuse milestone: a Chinese reuse success weighs "
                     "on SpaceX-adjacent names (RKLB/SPCE); SpaceX test result "
                     "is mixed for the same complex.",
    },
    "EV_PRICE_WAR": {
        "keywords": ["ev price cut", "ev price war", "tesla cuts",
                     "byd cuts", "xpeng cuts", "nio cuts",
                     "ev discount", "ev incentive"],
        "severity": 3,
        "default_hint": "mixed",
        "rationale": "EV price-war headline: cuts hurt margins for the whole "
                     "EV complex (Tesla + Chinese EVs); battery plays can benefit from volume.",
    },
    "CRYPTO_ETF_FLOW": {
        "keywords": ["bitcoin etf inflow", "bitcoin etf outflow",
                     "eth etf inflow", "spot bitcoin etf",
                     "spot eth etf approved", "crypto etf record"],
        "severity": 3,
        "default_hint": "long",
        "rationale": "Crypto ETF flow headlines drive BTC/ETH spot and coinbase/MSTR.",
    },
}


# ============================================================================
# Company alias -> ticker map
# ============================================================================
# Headlines name companies by name, not ticker. This map resolves the most
# common ones that move markets but aren't in the headline as a ticker.
# Each entry: alias (lowercase) -> list of {ticker, market, role}
#   role: "subject" (the company named in the headline), "competitor",
#         "supplier", "beneficiary", "victim"
# The resolver returns ALL roles; the bias-assignment step uses the role to
# decide long/short per ticker.

COMPANY_ALIASES = {
    # --- Chinese AI labs (frontier-model releases move these) ---
    "moonshot ai": [
        {"ticker": "BABA", "market": "US", "role": "competitor",
         "note": "Alibaba Cloud hosts Qwen -- a Moonshot competitor"},
        {"ticker": "sh688628", "market": "CN-A", "role": "subject",
         "note": "Kingsoft Office (WPS AI) -- often mis-tagged as Moonshot parent"},
        {"ticker": "KWEB", "market": "US", "role": "beneficiary",
         "note": "China internet ETF -- lifts on CN AI tailwind"},
    ],
    "kimi": [
        {"ticker": "BABA", "market": "US", "role": "competitor"},
        {"ticker": "sh688628", "market": "CN-A", "role": "beneficiary"},
        {"ticker": "KWEB", "market": "US", "role": "beneficiary"},
        {"ticker": "FXI", "market": "US", "role": "beneficiary"},
    ],
    "deepseek": [
        {"ticker": "BABA", "market": "US", "role": "competitor"},
        {"ticker": "002230.SZ", "market": "CN-A", "role": "beneficiary",
         "note": "iFlytek -- CN AI competitor"},
        {"ticker": "NVDA", "market": "US", "role": "victim",
         "note": "DeepSeek's efficiency narrative hit NVDA Jan-2025"},
        {"ticker": "KWEB", "market": "US", "role": "beneficiary"},
    ],
    "qwen": [
        {"ticker": "BABA", "market": "US", "role": "subject"},
        {"ticker": "sh688628", "market": "CN-A", "role": "competitor"},
        {"ticker": "KWEB", "market": "US", "role": "beneficiary"},
    ],
    "ernie": [
        {"ticker": "BIDU", "market": "US", "role": "subject"},
        {"ticker": "KWEB", "market": "US", "role": "beneficiary"},
    ],
    "chatglm": [
        {"ticker": "002230.SZ", "market": "CN-A", "role": "competitor"},
        {"ticker": "KWEB", "market": "US", "role": "beneficiary"},
    ],
    "zhipu ai": [
        {"ticker": "002230.SZ", "market": "CN-A", "role": "competitor"},
        {"ticker": "KWEB", "market": "US", "role": "beneficiary"},
    ],
    # --- Frontier labs (US) ---
    "openai": [
        {"ticker": "MSFT", "market": "US", "role": "subject"},
        {"ticker": "NVDA", "market": "US", "role": "beneficiary"},
        {"ticker": "AMD", "market": "US", "role": "beneficiary"},
    ],
    "anthropic": [
        {"ticker": "AMZN", "market": "US", "role": "subject"},
        {"ticker": "GOOGL", "market": "US", "role": "competitor"},
        {"ticker": "NVDA", "market": "US", "role": "beneficiary"},
    ],
    "google deepmind": [
        {"ticker": "GOOGL", "market": "US", "role": "subject"},
        {"ticker": "NVDA", "market": "US", "role": "beneficiary"},
    ],
    "mistral": [
        {"ticker": "MSFT", "market": "US", "role": "competitor"},
        {"ticker": "NVDA", "market": "US", "role": "beneficiary"},
    ],
    # --- Chinese EV makers ---
    "byd": [
        {"ticker": "002594.SZ", "market": "CN-A", "role": "subject"},
        {"ticker": "BYDDY", "market": "US", "role": "subject"},
        {"ticker": "TSLA", "market": "US", "role": "competitor"},
        {"ticker": "NIO", "market": "US", "role": "competitor"},
        {"ticker": "XPEV", "market": "US", "role": "competitor"},
        {"ticker": "LI", "market": "US", "role": "competitor"},
    ],
    "nio": [
        {"ticker": "NIO", "market": "US", "role": "subject"},
        {"ticker": "sh9866", "market": "HK", "role": "subject"},
        {"ticker": "TSLA", "market": "US", "role": "competitor"},
        {"ticker": "XPEV", "market": "US", "role": "competitor"},
        {"ticker": "LI", "market": "US", "role": "competitor"},
    ],
    "xpeng": [
        {"ticker": "XPEV", "market": "US", "role": "subject"},
        {"ticker": "sh9868", "market": "HK", "role": "subject"},
        {"ticker": "TSLA", "market": "US", "role": "competitor"},
    ],
    "li auto": [
        {"ticker": "LI", "market": "US", "role": "subject"},
        {"ticker": "sh2015", "market": "HK", "role": "subject"},
        {"ticker": "TSLA", "market": "US", "role": "competitor"},
    ],
    # --- Chinese internet ADRs (frequently named in headlines) ---
    "alibaba": [
        {"ticker": "BABA", "market": "US", "role": "subject"},
        {"ticker": "sh9988", "market": "HK", "role": "subject"},
        {"ticker": "JD", "market": "US", "role": "competitor"},
        {"ticker": "PDD", "market": "US", "role": "competitor"},
    ],
    "tencent": [
        {"ticker": "sh0700", "market": "HK", "role": "subject"},
        {"ticker": "TCEHY", "market": "US", "role": "subject"},
        {"ticker": "BABA", "market": "US", "role": "competitor"},
        {"ticker": "NTES", "market": "US", "role": "competitor"},
    ],
    "baidu": [
        {"ticker": "BIDU", "market": "US", "role": "subject"},
        {"ticker": "sh9888", "market": "HK", "role": "subject"},
    ],
    "jd.com": [
        {"ticker": "JD", "market": "US", "role": "subject"},
        {"ticker": "sh9618", "market": "HK", "role": "subject"},
        {"ticker": "BABA", "market": "US", "role": "competitor"},
    ],
    "pdd": [
        {"ticker": "PDD", "market": "US", "role": "subject"},
        {"ticker": "BABA", "market": "US", "role": "competitor"},
        {"ticker": "JD", "market": "US", "role": "competitor"},
    ],
    # --- Oil / OPEC ---
    "saudi aramco": [
        {"ticker": "XLE", "market": "US", "role": "beneficiary"},
        {"ticker": "XOM", "market": "US", "role": "beneficiary"},
        {"ticker": "CVX", "market": "US", "role": "beneficiary"},
    ],
    # --- Banks (for bank_run events) ---
    "silicon valley bank": [
        {"ticker": "KRE", "market": "US", "role": "victim"},
        {"ticker": "SIVB", "market": "US", "role": "subject"},
    ],
    "first republic": [
        {"ticker": "KRE", "market": "US", "role": "victim"},
        {"ticker": "FRC", "market": "US", "role": "subject"},
    ],
    # --- Pharma (FDA events) ---
    "eli lilly": [
        {"ticker": "LLY", "market": "US", "role": "subject"},
        {"ticker": "NVO", "market": "US", "role": "competitor"},
        {"ticker": "PFE", "market": "US", "role": "competitor"},
    ],
    "novo nordisk": [
        {"ticker": "NVO", "market": "US", "role": "subject"},
        {"ticker": "LLY", "market": "US", "role": "competitor"},
        {"ticker": "PFE", "market": "US", "role": "competitor"},
    ],
    "novo": [
        {"ticker": "NVO", "market": "US", "role": "subject"},
        {"ticker": "LLY", "market": "US", "role": "competitor"},
    ],
    "pfizer": [
        {"ticker": "PFE", "market": "US", "role": "subject"},
        {"ticker": "MRK", "market": "US", "role": "competitor"},
    ],
    "moderna": [
        {"ticker": "MRNA", "market": "US", "role": "subject"},
        {"ticker": "BNTX", "market": "US", "role": "competitor"},
    ],
    # --- Mega-cap tech (frequently named in headlines) ---
    "nvidia": [
        {"ticker": "NVDA", "market": "US", "role": "subject"},
        {"ticker": "AMD", "market": "US", "role": "competitor"},
        {"ticker": "AVGO", "market": "US", "role": "competitor"},
    ],
    "apple": [
        {"ticker": "AAPL", "market": "US", "role": "subject"},
        {"ticker": "MSFT", "market": "US", "role": "competitor"},
    ],
    "microsoft": [
        {"ticker": "MSFT", "market": "US", "role": "subject"},
        {"ticker": "GOOGL", "market": "US", "role": "competitor"},
    ],
    "tesla": [
        {"ticker": "TSLA", "market": "US", "role": "subject"},
        {"ticker": "F", "market": "US", "role": "competitor"},
        {"ticker": "GM", "market": "US", "role": "competitor"},
    ],
}


# ============================================================================
# Event cache (dedup across runs)
# ============================================================================

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
_CACHE_PATH = os.path.join(_CACHE_DIR, "breaking-events.json")
_CACHE_TTL_SECONDS = 6 * 3600  # forget an event after 6h so re-coverage is surfaced


def _load_cache():
    try:
        with open(_CACHE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_cache(cache):
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(_CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=2, default=str)
    except Exception as e:
        # Cache is best-effort; never fail the scan over it.
        pass


def _event_id(event):
    """Stable hash for dedup. Two events with the same (type, primary_keyword,
    top-headline) are the same event."""
    key = f"{event.get('event_type')}|{event.get('primary_keyword','')}|{event.get('top_headline','')[:120]}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


# ============================================================================
# Detection
# ============================================================================

# Pre-build keyword index for fast substring match
_KW_INDEX = []
for _etype, _spec in EVENT_TYPES.items():
    for _kw in _spec["keywords"]:
        _KW_INDEX.append((_kw.lower(), _etype, _kw))
# Also index company aliases
_ALIAS_INDEX = [(alias.lower(), alias) for alias in COMPANY_ALIASES.keys()]
# Sort longest-first so "moonshot ai" matches before "ai"
_KW_INDEX.sort(key=lambda x: -len(x[0]))
_ALIAS_INDEX.sort(key=lambda x: -len(x[0]))


def _match_event_types(headline):
    """Return list of (event_type, matched_keyword) for a single headline."""
    if not headline:
        return []
    low = str(headline).lower()
    hits = []
    seen_types = set()
    for kw, etype, original in _KW_INDEX:
        if etype in seen_types:
            continue
        # Multi-word phrase: substring match
        if " " in kw or kw in ("crL".lower(),):
            if kw in low:
                hits.append((etype, original))
                seen_types.add(etype)
        else:
            # Single token: word-boundary match to avoid false positives
            # (e.g. "fed" shouldn't match "fedex")
            if re.search(r"\b" + re.escape(kw) + r"\b", low):
                hits.append((etype, original))
                seen_types.add(etype)
    return hits


def _match_companies(headline):
    """Return list of (alias, matched_text) for a single headline."""
    if not headline:
        return []
    low = str(headline).lower()
    hits = []
    seen = set()
    for kw, alias in _ALIAS_INDEX:
        if alias in seen:
            continue
        if kw in low:
            hits.append((alias, kw))
            seen.add(alias)
    return hits


def _parse_date(s):
    """Best-effort parse of an RSS pubDate into epoch seconds."""
    if not s:
        return 0
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
        try:
            d = datetime.strptime(s.strip(), fmt)
            return d.timestamp()
        except ValueError:
            continue
    # Fallback: try datetime.fromisoformat
    try:
        return datetime.fromisoformat(s.strip()).timestamp()
    except Exception:
        return 0


def detect_events(items_by_feed, hours=6):
    """Scan ALL fetched RSS items and return a list of BreakingEvent dicts.

    items_by_feed: list of (name, items, err) tuples from news.fetch_all().
    hours: only consider items within this many recent hours.

    A BreakingEvent is a dict:
      {
        event_id: str,         # stable hash for dedup
        event_type: str,       # key from EVENT_TYPES
        severity: int,         # 1-5
        hint: str,             # "long"/"short"/"mixed"
        rationale: str,        # one-liner
        primary_keyword: str,  # the keyword that matched
        top_headline: str,     # most recent matching headline
        top_headline_date: str,
        n_feeds: int,          # distinct feeds covering this
        n_headlines: int,      # total matching headlines
        feeds: [str, ...],     # feed names
        headlines: [{title, feed, date}, ...],  # up to 5 most recent
        companies_mentioned: [alias, ...],      # COMPANY_ALIASES keys
        detected_at: float,    # epoch seconds
      }
    """
    now = time.time()
    cutoff = now - hours * 3600

    # Group hits by event_type
    by_type: dict[str, list] = {}
    for feed_name, items, err in items_by_feed:
        if err or not items:
            continue
        for it in items:
            title = _clean_title(it.get("title", ""))
            date_s = it.get("date", "")
            ts = _parse_date(date_s)
            # If date is missing, include (better to false-positive than miss breaking news)
            if ts and ts < cutoff:
                continue
            for etype, kw in _match_event_types(title):
                by_type.setdefault(etype, []).append({
                    "title": title, "feed": feed_name,
                    "date": date_s, "ts": ts,
                    "keyword": kw,
                })

    # Build events
    events = []
    for etype, hits in by_type.items():
        spec = EVENT_TYPES[etype]
        # Sort by timestamp desc (undated items treated as now)
        hits.sort(key=lambda h: h["ts"] if h["ts"] else now, reverse=True)
        feeds = sorted({h["feed"] for h in hits})
        headlines = [{"title": h["title"], "feed": h["feed"],
                      "date": h["date"]} for h in hits[:5]]
        # Collect companies mentioned across all hits
        companies = set()
        for h in hits:
            for alias, _ in _match_companies(h["title"]):
                companies.add(alias)
        top = hits[0]
        event = {
            "event_type": etype,
            "severity": spec["severity"],
            "hint": spec["default_hint"],
            "rationale": spec["rationale"],
            "primary_keyword": top["keyword"],
            "top_headline": top["title"],
            "top_headline_date": top["date"],
            "n_feeds": len(feeds),
            "n_headlines": len(hits),
            "feeds": feeds,
            "headlines": headlines,
            "companies_mentioned": sorted(companies),
            "detected_at": now,
        }
        event["event_id"] = _event_id(event)
        events.append(event)

    # Sort by (severity desc, n_feeds desc, n_headlines desc)
    events.sort(key=lambda e: (e["severity"], e["n_feeds"], e["n_headlines"]),
                reverse=True)
    return events


# ============================================================================
# Ticker resolution + bias assignment
# ============================================================================

def resolve_tickers(event):
    """Expand a BreakingEvent into a concrete ticker list with bias per ticker.

    Returns list of {ticker, market, role, bias, note}.
    bias is "long"/"short"/"mixed" derived from event.hint + role:
      - subject + long hint  -> long
      - subject + short hint -> short
      - competitor + long hint -> mixed (could win or lose share)
      - beneficiary + long hint -> long
      - victim + long hint -> short (the loser)
      - subject + mixed hint -> mixed
    """
    hint = event.get("hint", "mixed")
    out = []
    seen_tickers = set()

    # 1. Tickers from companies mentioned in the headlines
    for alias in event.get("companies_mentioned", []):
        for entry in COMPANY_ALIASES.get(alias, []):
            t = entry["ticker"]
            if t in seen_tickers:
                continue
            seen_tickers.add(t)
            role = entry.get("role", "subject")
            bias = _bias_from_role_and_hint(role, hint)
            out.append({
                "ticker": t,
                "market": entry.get("market", "US"),
                "role": role,
                "bias": bias,
                "note": entry.get("note", ""),
                "source": f"alias:{alias}",
            })

    # 2. Tickers from the matching THEME's watch list (peers.THEMES)
    # Map our event_type to a peers.THEMES key where one exists
    theme_map = {
        "AI_MODEL_RELEASE": "ai_capex",
        "AI_CAPEX": "ai_capex",
        "FDA_APPROVAL": "fda_approval",
        "FDA_REJECTION": "fda_rejection",
        "MA_DEAL": "merger_announcement",
        "CHINA_REGULATORY": "china_regulatory",
        "CHINA_STIMULUS": "china_stimulus",
        "CENTRAL_BANK": "rate_decision",
        "GEOPOLITICAL": "geopolitical",
        "OIL_SUPPLY_SHOCK": "oil_supply_shock",
        "BANK_RUN": "bank_run",
        "ROCKET_REUSE": "rocket_reuse",
        "EV_PRICE_WAR": "ev_price_war",
        "CRYPTO_ETF_FLOW": "crypto_etf_flow",
    }
    theme_key = theme_map.get(event["event_type"])
    if theme_key:
        spec = peers.THEMES.get(theme_key, {})
        for t in spec.get("watch", []):
            if t in seen_tickers:
                continue
            seen_tickers.add(t)
            theme_hint = spec.get("hint", hint)
            out.append({
                "ticker": t,
                "market": _infer_market(t),
                "role": "theme_watch",
                "bias": _bias_from_role_and_hint("theme_watch", theme_hint),
                "note": spec.get("rationale", "")[:120],
                "source": f"theme:{theme_key}",
            })

    return out


def _bias_from_role_and_hint(role, hint):
    """Combine a ticker's role in the event with the event's directional hint
    to produce a per-ticker bias."""
    hint = _normalize_hint(hint)
    if role == "subject":
        return hint
    if role == "beneficiary":
        return "long" if hint in ("long", "mixed") else "short"
    if role == "victim":
        return "short" if hint == "long" else "long"
    if role == "competitor":
        # Competitor direction is genuinely ambiguous; mark mixed and let the
        # backtest gate + LLM tiebreaker decide.
        return "mixed"
    if role == "theme_watch":
        return hint
    return "mixed"


def _normalize_hint(hint):
    """Normalize a hint string to one of: long, short, mixed.
    Accepts the peers.THEMES style values: 'long_disruptor', 'short_incumbent'."""
    if not hint:
        return "mixed"
    h = str(hint).lower().strip()
    if h.startswith("long"):
        return "long"
    if h.startswith("short"):
        return "short"
    return "mixed"


def _infer_market(t):
    """Infer the market for a ticker string."""
    from . import instruments
    return instruments.market_of(t)


# ============================================================================
# LLM enrichment (optional; degrades gracefully if no key)
# ============================================================================

def enrich_with_llm(event, max_tickers=3):
    """For the top resolved tickers, attach an LLM sentiment judgment.

    Returns the event with a 'llm' field per ticker:
      {ticker: {bias, confidence, reason, provider}}
    Failures are silent -- the hard gate stays in analysis.py.
    """
    tickers = event.get("resolved_tickers", [])[:max_tickers]
    out = {}
    for t in tickers:
        sym = t["ticker"]
        # Build headline set for this ticker: the event's headlines + a
        # per-ticker Finnhub fetch (best-effort).
        headlines = [h["title"] for h in event.get("headlines", [])]
        try:
            fh, _ = news.ticker_news(sym, want_sentiment=False)
            if fh.get("headlines"):
                headlines = headlines + list(fh["headlines"])[:5]
        except Exception:
            pass
        if not headlines:
            continue
        try:
            res = llm.news_sentiment(sym, headlines)
            if res:
                out[sym] = res
        except Exception:
            continue
    return out


# ============================================================================
# Watch loop
# ============================================================================

def watch_once(*, hours=6, min_severity=3, min_feeds=1, want_llm=True,
               dispatch=True, cache=None):
    """Single-pass detect -> resolve -> enrich -> alert.

    Returns list of NEW BreakingEvents (after dedup against the cache).

    Args:
      hours:           RSS lookback window.
      min_severity:    drop events below this severity (1-5).
      min_feeds:       drop events with fewer than this many distinct feeds.
                       Set to 1 to catch single-feed scoops; 2-3 for higher confidence.
      want_llm:        if True, attach LLM sentiment to top tickers per event.
      dispatch:        if True, dispatch an alert for each new event.
      cache:           pre-loaded cache dict (loads from disk if None).

    Research only. Not financial advice.
    """
    # 1. Fetch all feeds
    items = news.fetch_all()

    # 2. Detect events
    events = detect_events(items, hours=hours)

    # 3. Filter by severity + corroboration
    events = [e for e in events
              if e["severity"] >= min_severity and e["n_feeds"] >= min_feeds]

    # 4. Dedup against cache
    if cache is None:
        cache = _load_cache()
    now = time.time()
    # Prune stale cache entries
    cache = {k: v for k, v in cache.items()
             if (now - v.get("first_seen", 0)) < _CACHE_TTL_SECONDS}
    new_events = []
    for e in events:
        eid = e["event_id"]
        if eid in cache:
            # Already alerted. Optionally bump count.
            cache[eid]["last_seen"] = now
            cache[eid]["count"] = cache[eid].get("count", 1) + 1
            continue
        # New event!
        cache[eid] = {
            "event_type": e["event_type"],
            "primary_keyword": e["primary_keyword"],
            "top_headline": e["top_headline"],
            "first_seen": now,
            "last_seen": now,
            "count": 1,
        }
        new_events.append(e)
    _save_cache(cache)

    # 5. Resolve tickers + enrich
    for e in new_events:
        e["resolved_tickers"] = resolve_tickers(e)
        if want_llm and e["resolved_tickers"]:
            try:
                e["llm"] = enrich_with_llm(e)
            except Exception:
                e["llm"] = {}
        else:
            e["llm"] = {}

    # 6. Dispatch alerts
    if dispatch and new_events:
        for e in new_events:
            try:
                _dispatch_event_alert(e)
            except Exception:
                pass

    return new_events


def watch_loop(*, interval=300, **kwargs):
    """Blocking loop: detect new breaking events every `interval` seconds.

    Use this for foreground watching. For background use the launchd job
    (breaking_watch.sh -> watch_once).
    """
    import sys
    print(f"breaking-news watch loop: polling every {interval}s. Ctrl-C to stop.")
    sys.stdout.flush()
    cache = _load_cache()
    try:
        while True:
            try:
                new = watch_once(cache=cache, **kwargs)
                if new:
                    print(f"\n[{datetime.now().isoformat(timespec='seconds')}] "
                          f"{len(new)} new breaking event(s):")
                    print_events(new)
                else:
                    print(f"[{datetime.now().isoformat(timespec='seconds')}] "
                          f"no new events (cache size={len(cache)})")
                sys.stdout.flush()
            except Exception as e:
                # Never crash the loop on a single failure.
                print(f"[watch_loop error] {core.describe_err(e)}")
                sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[watch_loop] stopped by user")


def _dispatch_event_alert(event):
    """Dispatch an alert for a single new breaking event."""
    subject = f"BREAKING: {event['event_type'].replace('_',' ').title()} -- {event['primary_keyword']}"
    body_lines = [
        f"Event: {event['event_type']}",
        f"Severity: {event['severity']}/5",
        f"Feeds: {event['n_feeds']} distinct ({', '.join(event['feeds'][:3])})",
        f"Headlines: {event['n_headlines']}",
        f"Hint: {event['hint']}",
        f"Rationale: {event['rationale']}",
        "",
        "Top headlines:",
    ]
    for h in event["headlines"][:5]:
        body_lines.append(f"  - [{h['feed']}] {h['title'][:120]}")
    if event.get("companies_mentioned"):
        body_lines.append("")
        body_lines.append(f"Companies mentioned: {', '.join(event['companies_mentioned'])}")
    if event.get("resolved_tickers"):
        body_lines.append("")
        body_lines.append("Tradeable tickers (still must clear the backtest gate):")
        for t in event["resolved_tickers"][:8]:
            llm_str = ""
            if event.get("llm", {}).get(t["ticker"]):
                l = event["llm"][t["ticker"]]
                llm_str = f" [LLM: {l.get('bias','?')} conf={l.get('confidence',0):.2f}]"
            body_lines.append(
                f"  {t['ticker']:10} ({t['market']:5}) bias={t['bias']:5} "
                f"role={t['role']:12}{llm_str}"
            )
            if t.get("note"):
                body_lines.append(f"      note: {t['note']}")
    body_lines.append("")
    body_lines.append("Research only. Not financial advice. Verify before acting.")
    body = "\n".join(body_lines)
    alerts.dispatch(subject, body)


# ============================================================================
# Printing
# ============================================================================

def print_events(events, max_width=100):
    """Human-readable report of breaking events."""
    if not events:
        print("\n=== BREAKING NEWS: no high-impact events detected ===")
        return
    print(f"\n=== BREAKING NEWS: {len(events)} event(s) ===")
    for i, e in enumerate(events, 1):
        print(f"\n[{i}] {e['event_type'].replace('_',' ').title()}  "
              f"(severity {e['severity']}/5, {e['n_feeds']} feeds, "
              f"{e['n_headlines']} headlines)")
        print(f"    hint: {e['hint']}  -- {e['rationale']}")
        print(f"    top:  {e['top_headline'][:max_width]}")
        if e.get("companies_mentioned"):
            print(f"    companies: {', '.join(e['companies_mentioned'])}")
        if e.get("resolved_tickers"):
            print(f"    tradeable tickers (must still clear backtest gate):")
            for t in e["resolved_tickers"][:6]:
                llm_str = ""
                if e.get("llm", {}).get(t["ticker"]):
                    l = e["llm"][t["ticker"]]
                    llm_str = f" [LLM:{l.get('bias','?')}/{l.get('confidence',0):.2f}]"
                print(f"      {t['ticker']:10} ({t['market']:5}) bias={t['bias']:5} "
                      f"role={t['role']:12}{llm_str}")
                if t.get("note"):
                    print(f"        {t['note'][:max_width-8]}")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if "--loop" in args:
        interval = 300
        if "--interval" in args:
            try:
                interval = max(60, int(args[args.index("--interval") + 1]))
            except (IndexError, ValueError):
                pass
        watch_loop(interval=interval,
                   want_llm=("--no-llm" not in args),
                   min_severity=int(args[args.index("--min-severity") + 1]) if "--min-severity" in args else 3,
                   min_feeds=int(args[args.index("--min-feeds") + 1]) if "--min-feeds" in args else 1)
    else:
        # Single pass
        hours = int(args[args.index("--hours") + 1]) if "--hours" in args else 6
        min_severity = int(args[args.index("--min-severity") + 1]) if "--min-severity" in args else 3
        min_feeds = int(args[args.index("--min-feeds") + 1]) if "--min-feeds" in args else 1
        new = watch_once(hours=hours, min_severity=min_severity, min_feeds=min_feeds,
                         want_llm=("--no-llm" not in args),
                         dispatch=("--no-alert" not in args))
        print_events(new)
        print(f"\n[{datetime.now().isoformat(timespec='seconds')}] {len(new)} new event(s). "
              f"Cache at: {_CACHE_PATH}")
