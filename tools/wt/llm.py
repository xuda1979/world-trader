"""LLM-powered news sentiment for the top opportunity candidates.

The directional backtest + Sharpe/t/OOS gate is the scientific core -- nothing
here overrides it. The LLM adds ONE bit of edge: it reads the same Finnhub
headlines the scanner already pulls and judges whether they support the trade
direction (bullish for a long, bearish for a short). That judgment is wired as
a *gentle tiebreaker* among near-miss rows, never as a qualifying signal.

WHY: a row at Sharpe 0.35 (just below the 0.40 bar) with strongly-aligned news
is a better bet than a row at Sharpe 0.35 with contradicting news. The LLM is
cheap, fast (1-3s/call), and works on free-form text where rule-based sentiment
fails. The Finnhub/Polygon sentiment we already have is a coarse +/-1 count;
the LLM gives a structured (bias, confidence, reason) with reasoning.

PROVIDERS (priority order, first available wins):
  1. xAI Grok  -- XAI_API_KEY  (https://api.x.ai/v1/chat/completions, OpenAI-compatible)
  2. Anthropic -- ANTHROPIC_API_KEY (https://api.anthropic.com/v1/messages)
  3. (none)    -- returns None, scanner degrades gracefully to rule-based sentiment

DESIGN:
  - Provider-agnostic news_sentiment(sym, headlines) -> dict or None
  - 30-min per-symbol cache (headlines don't change fast enough to re-burn tokens)
  - Structured JSON output with bias in {bull, bear, neutral}, confidence [0,1]
  - Never raises; on any error returns None so the scanner continues
  - Only called for the top N rows (enrich_n=5 by default) to bound cost

This is research-only signal, not financial advice. The LLM can be wrong; the
hard gate (Sharpe/t/OOS) still decides what surfaces.
"""
from __future__ import annotations
import json, os, time, threading
from . import core

_CACHE: dict = {}
_LOCK = threading.Lock()
_CACHE_TTL = 30 * 60   # 30 min per symbol

# Provider priority -- first with a key wins. Add OpenAI/local LLM here later.
_PROVIDERS = ("xai", "anthropic")


def _cache_get(sym):
    now = time.time()
    with _LOCK:
        hit = _CACHE.get(sym)
        if hit and (now - hit[0]) < _CACHE_TTL:
            return hit[1]
    return None

def _cache_put(sym, val):
    with _LOCK:
        _CACHE[sym] = (time.time(), val)


def news_sentiment(sym, headlines):
    """Judge whether the given headlines support a LONG or SHORT on `sym`.

    Args:
        sym: ticker, e.g. 'AAPL' (used only for cache key + prompt context)
        headlines: list of strings (titles only; no bodies). 3-8 is ideal.

    Returns dict or None:
        {bias: 'bull'|'bear'|'neutral', confidence: float [0,1],
         reason: str, provider: str}  -- or None if no provider / no headlines /
        every provider failed. Never raises.
    """
    if not headlines:
        return None
    # dedupe + cap at 8 to bound prompt size
    seen = set()
    hs = []
    for h in headlines:
        h = str(h).strip()
        if h and h not in seen:
            seen.add(h)
            hs.append(h)
    if not hs:
        return None
    hs = hs[:8]

    cached = _cache_get(sym)
    if cached is not None:
        return cached

    result = None
    for provider in _PROVIDERS:
        try:
            if provider == "xai" and core.api_key("XAI_API_KEY"):
                result = _xai_sentiment(sym, hs)
            elif provider == "anthropic" and core.api_key("ANTHROPIC_API_KEY"):
                result = _anthropic_sentiment(sym, hs)
            if result:
                result["provider"] = provider
                break
        except Exception as e:
            # Never let an LLM failure crash the scan -- log and try next provider.
            result = None
            continue

    _cache_put(sym, result)
    return result


# ---------------------------------------------------------------- xAI (Grok)
def _xai_sentiment(sym, headlines):
    """xAI Grok via the OpenAI-compatible /v1/chat/completions endpoint.
    Uses JSON mode for structured output. Returns dict or None."""
    key = core.api_key("XAI_API_KEY")
    if not key:
        return None
    prompt = _build_prompt(sym, headlines)
    body = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
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
        timeout=20,
    )
    if not resp:
        return None
    d = json.loads(resp)
    content = (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return _parse_json_sentiment(content)


# ---------------------------------------------------------------- Anthropic
def _anthropic_sentiment(sym, headlines):
    """Anthropic Claude via /v1/messages. Uses tool_use for structured output.
    Returns dict or None."""
    key = core.api_key("ANTHROPIC_API_KEY")
    if not key:
        return None
    prompt = _build_prompt(sym, headlines)
    body = {
        "model": "claude-3-5-haiku-20241022",   # cheap + fast for sentiment
        "max_tokens": 200,
        "system": _SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = core.http_post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key,
                 "anthropic-version": "2023-06-01",
                 "Content-Type": "application/json"},
        body=json.dumps(body).encode("utf-8"),
        timeout=20,
    )
    if not resp:
        return None
    d = json.loads(resp)
    content = (d.get("content") or [{}])[0].get("text", "")
    return _parse_json_sentiment(content)


# ---------------------------------------------------------------- shared
_SYSTEM_PROMPT = (
    "You are a financial news sentiment analyst. Read the given headlines for a "
    "stock and judge whether they support a LONG (bullish) or SHORT (bearish) "
    "trade over the next 1-5 trading days. Respond ONLY with a JSON object: "
    '{"bias": "bull"|"bear"|"neutral", "confidence": 0.0-1.0, "reason": "one short sentence"}. '
    "confidence=0.0 if headlines are mixed/irrelevant, 0.5 if mildly aligned, "
    "0.9 if clearly and strongly aligned. Be skeptical: a single rumor is 0.3 max. "
    "No prose outside the JSON."
)

def _build_prompt(sym, headlines):
    hs = "\n".join(f"- {h}" for h in headlines)
    return (f"Stock: {sym}\nRecent headlines (last 7 days):\n{hs}\n\n"
            f"Judge the net sentiment for a 1-5 day directional trade. JSON only.")


def _parse_json_sentiment(text):
    """Robustly extract the JSON object from the model's response. Returns dict
    with keys (bias, confidence, reason) or None if unparseable."""
    if not text:
        return None
    # strip code fences if present
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip()
    # find the first {...} block
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b < 0 or b <= a:
        return None
    try:
        d = json.loads(t[a:b+1])
    except json.JSONDecodeError:
        return None
    bias = str(d.get("bias", "")).lower().strip()
    if bias not in ("bull", "bear", "neutral"):
        return None
    try:
        conf = float(d.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    reason = str(d.get("reason", "")).strip()[:200]
    return {"bias": bias, "confidence": conf, "reason": reason}


def available_provider():
    """Return the name of the first available LLM provider, or None. Used by
    the doctor self-check and to short-circuit enrich_with_llm when no key."""
    for p in _PROVIDERS:
        if p == "xai" and core.api_key("XAI_API_KEY"):
            return "xai"
        if p == "anthropic" and core.api_key("ANTHROPIC_API_KEY"):
            return "anthropic"
    return None
