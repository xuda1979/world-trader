"""Generic LLM chat for agent nodes.

Provider priority (first available wins):
  1. xAI Grok         -- XAI_API_KEY (OpenAI-compatible)
  2. OpenAI-compat    -- OPENAI_API_KEY + OPENAI_BASE_URL (any compatible endpoint)
  3. Anthropic-native -- ANTHROPIC_API_KEY (or the Huanxin local proxy via
                        ANTHROPIC_BASE_URL + ANTHROPIC_MODEL=glm5.2)
  4. Huanxin GLM 5.2 direct -- HUANXIN_GLM52_DIRECT=1 bypasses the local
                        proxy and calls the upstream URL directly. Used
                        when the proxy is up but returns null because its
                        own upstream is being retried.

All HTTP errors are caught and returned as None (never raise). The
caller (orchestrator) records the failure in the result's `errors` list.

Models:
  xAI:       grok-4-fast (fast, cheap, good for analyst nodes)
  Anthropic: claude-3-5-haiku-20241022 for analyst nodes (cheap),
             claude-3-5-sonnet-20241022 for research/risk/trader nodes
             (higher reasoning). Overridable via env.
  Huanxin:   glm5.2 (the only model the local proxy exposes)

Env vars (all optional):
  XAI_API_KEY, XAI_BASE_URL, WT_XAI_MODEL
  OPENAI_API_KEY, OPENAI_BASE_URL, WT_OPENAI_MODEL
  ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL,
    ANTHROPIC_MODEL, ANTHROPIC_SMALL_FAST_MODEL,
    ANTHROPIC_DEFAULT_SONNET_MODEL, ANTHROPIC_DEFAULT_OPUS_MODEL,
    ANTHROPIC_DEFAULT_HAIKU_MODEL
  WT_ANTHROPIC_FAST_MODEL, WT_ANTHROPIC_STRONG_MODEL
  HUANXIN_GLM52_DIRECT=1        -- bypass local proxy, call upstream directly
  HUANXIN_GLM52_UPSTREAM_URL    -- the qdlake upstream URL
  HUANXIN_GLM52_UPSTREAM_TOKEN  -- the JWT bearer token
  WT_LLM_RETRIES (default 3)    -- agent-level retry on null/empty response
  WT_LLM_RETRY_BASE (default 0.8) -- base seconds for exponential backoff
"""
from __future__ import annotations
import json, os, ssl, time, urllib.request, urllib.error
from typing import Optional

from wt import core

# ---------------------------------------------------------------------------
# Endpoints and model defaults
# ---------------------------------------------------------------------------

XAI_ENDPOINT = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1/chat/completions")
OPENAI_ENDPOINT = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
ANTHROPIC_ENDPOINT = os.environ.get(
    "ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages")
# Read timeout per HTTP call. Slow reasoning models (e.g. deepseek-v4-pro)
# can exceed the historical 40s on long responses; bump with WT_LLM_TIMEOUT.
LLM_TIMEOUT = int(os.environ.get("WT_LLM_TIMEOUT", "40"))
# If the user set ANTHROPIC_BASE_URL without a /v1/messages suffix, append it.
if not ANTHROPIC_ENDPOINT.endswith("/v1/messages"):
    ANTHROPIC_ENDPOINT = ANTHROPIC_ENDPOINT.rstrip("/") + "/v1/messages"

_DEFAULT_XAI_MODEL = os.environ.get("WT_XAI_MODEL", "grok-4-fast")
_DEFAULT_OPENAI_MODEL = os.environ.get("WT_OPENAI_MODEL", "gpt-4o-mini")
# Respect the project's ANTHROPIC_MODEL / ANTHROPIC_SMALL_FAST_MODEL env vars
# (set by the Huanxin local proxy). Fall back to Claude 3.5 model names.
_DEFAULT_ANTHROPIC_FAST_MODEL = (
    os.environ.get("WT_ANTHROPIC_FAST_MODEL")
    or os.environ.get("ANTHROPIC_SMALL_FAST_MODEL")
    or os.environ.get("ANTHROPIC_MODEL")
    or "claude-3-5-haiku-20241022"
)
_DEFAULT_ANTHROPIC_STRONG_MODEL = (
    os.environ.get("WT_ANTHROPIC_STRONG_MODEL")
    or os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
    or os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL")
    or os.environ.get("ANTHROPIC_MODEL")
    or "claude-3-5-sonnet-20241022"
)
# Huanxin GLM 5.2 direct upstream
_HUANXIN_DIRECT = os.environ.get("HUANXIN_GLM52_DIRECT", "") == "1"
_HUANXIN_UPSTREAM_URL = os.environ.get("HUANXIN_GLM52_UPSTREAM_URL", "")
_HUANXIN_UPSTREAM_TOKEN = os.environ.get("HUANXIN_GLM52_UPSTREAM_TOKEN", "")
_HUANXIN_MODEL = os.environ.get("HUANXIN_GLM52_MODEL", "glm5.2")

# Agent-level retry config (on top of any provider-internal retries)
_RETRIES = max(1, int(os.environ.get("WT_LLM_RETRIES", "3")))
_RETRY_BASE = float(os.environ.get("WT_LLM_RETRY_BASE", "0.8"))

# Insecure SSL context for self-signed certs (Huanxin upstream has had expired
# certs in the past). Only used when HUANXIN_GLM52_INSECURE=1.
_INSECURE_SSL = os.environ.get("HUANXIN_GLM52_INSECURE", "") == "1"
_INSECURE_CTX = None
if _INSECURE_SSL:
    _INSECURE_CTX = ssl.create_default_context()
    _INSECURE_CTX.check_hostname = False
    _INSECURE_CTX.verify_mode = ssl.CERT_NONE


def _log(msg: str) -> None:
    """Stderr log, prefixed so the user can filter."""
    import sys
    sys.stderr.write(f"[agent.llm_chat] {msg}\n")
    sys.stderr.flush()


# ---------------------------------------------------------------------------
# Provider: xAI Grok (OpenAI-compatible)
# ---------------------------------------------------------------------------

def _xai_chat(system: str, user: str, model: str, temperature: float = 0.2,
              max_tokens: int = 1500,
                         disable_thinking: bool = False) -> Optional[str]:
    key = core.api_key("XAI_API_KEY")
    if not key:
        return None
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        resp = core.http_post(
            XAI_ENDPOINT,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            body=json.dumps(body).encode("utf-8"),
            timeout=LLM_TIMEOUT,
        )
    except Exception as e:
        _log(f"xai error: {repr(e)[:200]}")
        return None
    if not resp:
        return None
    try:
        d = json.loads(resp)
        return (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
    except (json.JSONDecodeError, IndexError, KeyError):
        return None


# ---------------------------------------------------------------------------
# Provider: OpenAI-compatible (generic -- any /v1/chat/completions endpoint)
# ---------------------------------------------------------------------------

def _openai_compat_chat(system: str, user: str, model: str,
                        temperature: float = 0.2,
                        max_tokens: int = 1500,
                         disable_thinking: bool = False) -> Optional[str]:
    key = core.api_key("OPENAI_API_KEY")
    if not key:
        return None
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        resp = core.http_post(
            OPENAI_ENDPOINT,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            body=json.dumps(body).encode("utf-8"),
            timeout=LLM_TIMEOUT,
        )
    except Exception as e:
        _log(f"openai-compat error: {repr(e)[:200]}")
        return None
    if not resp:
        return None
    try:
        d = json.loads(resp)
        return (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
    except (json.JSONDecodeError, IndexError, KeyError):
        return None


# ---------------------------------------------------------------------------
# Provider: Anthropic-native (or the Huanxin local proxy speaking Anthropic)
# ---------------------------------------------------------------------------

def _anthropic_chat(system: str, user: str, model: str, temperature: float = 0.2,
                    max_tokens: int = 1500,
                    disable_thinking: bool = False) -> Optional[str]:
    key = core.api_key("ANTHROPIC_API_KEY")
    if not key:
        return None
    body = {
        "model": model,
        "system": system,
        "messages": [{"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if disable_thinking:
        # Reasoning models (e.g. deepseek-v4-pro) spend the whole token
        # budget on hidden thinking blocks and return no visible text.
        # Contract-style nodes (structured JSON in/out) don't need the
        # chain of thought -- turn it off for speed and completeness.
        body["thinking"] = {"type": "disabled"}
    try:
        resp = core.http_post(
            ANTHROPIC_ENDPOINT,
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            body=json.dumps(body).encode("utf-8"),
            timeout=LLM_TIMEOUT,
        )
    except Exception as e:
        _log(f"anthropic error: {repr(e)[:200]}")
        return None
    if not resp:
        return None
    try:
        d = json.loads(resp)
    except json.JSONDecodeError as e:
        _log(f"anthropic JSON decode err: {repr(e)[:200]} resp[:200]={resp[:200]!r}")
        return None
    if d is None:
        # The Huanxin local proxy returns `null` (4 bytes) when its own
        # upstream is being retried / is down. Treat as a transient failure.
        _log("anthropic returned null (proxy upstream down?)")
        return None
    content = d.get("content") or [{}]
    # Anthropic returns a list of content blocks; concatenate text blocks
    parts = [b.get("text", "") for b in content
             if isinstance(b, dict) and b.get("type") == "text"]
    return "".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# Provider: Huanxin GLM 5.2 DIRECT (bypasses the local proxy)
# ---------------------------------------------------------------------------

def _huanxin_direct_chat(system: str, user: str, model: str,
                         temperature: float = 0.2,
                         max_tokens: int = 1500,
                         disable_thinking: bool = False) -> Optional[str]:
    """Call the Huanxin GLM 5.2 upstream directly, bypassing the local proxy.

    Used when the proxy is up but returns null because its own upstream
    retry loop exhausted. We do our own retry here.
    """
    if not _HUANXIN_UPSTREAM_URL or not _HUANXIN_UPSTREAM_TOKEN:
        return None
    body = json.dumps({
        "model": model or _HUANXIN_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    # The Huanxin upstream wants `Authorization: <token>` (no Bearer prefix)
    # when the token is a JWT, and `Authorization: Bearer <token>` when it's
    # an opaque key. Try both.
    for auth_header in (_HUANXIN_UPSTREAM_TOKEN,
                        f"Bearer {_HUANXIN_UPSTREAM_TOKEN}"):
        req = urllib.request.Request(
            _HUANXIN_UPSTREAM_URL,
            headers={"Authorization": auth_header,
                     "Content-Type": "application/json"},
            data=body, method="POST")
        try:
            with urllib.request.urlopen(
                req, timeout=LLM_TIMEOUT,
                context=_INSECURE_CTX if _INSECURE_SSL else None
            ) as r:
                raw = r.read()
                if not raw or raw == b"null":
                    continue
                d = json.loads(raw)
                # OpenAI-compatible response shape
                choices = d.get("choices") or []
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                # Anthropic-compatible response shape (fallback)
                content = d.get("content") or []
                parts = [b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text"]
                if parts:
                    return "".join(parts)
                return None
        except urllib.error.HTTPError as e:
            _log(f"huanxin-direct HTTP {e.code} (auth={auth_header[:20]}...): "
                 f"{e.read()[:150].decode('utf-8','replace')}")
            continue
        except Exception as e:
            _log(f"huanxin-direct err: {repr(e)[:200]}")
            continue
    return None


# ---------------------------------------------------------------------------
# Top-level chat() with provider priority + agent-level retry
# ---------------------------------------------------------------------------

def chat(system: str, user: str, strong: bool = False,
         temperature: float = 0.2, max_tokens: int = 1500,
         disable_thinking: bool = False) -> Optional[str]:
    """Send a single-turn chat to the best available provider.

    Args:
        system: system prompt.
        user: user-turn prompt (usually the rendered template).
        strong: if True, use the higher-reasoning model tier (research/
            risk/trader/reflector nodes). If False, use the cheap/fast tier
            (analyst nodes).
        temperature: 0.0-1.0. Lower = more deterministic.
        max_tokens: response cap.
        disable_thinking: if True, request no hidden chain-of-thought
            (Anthropic-style `thinking: disabled`). Contract-style JSON
            nodes use this so reasoning models return text instead of
            burning the whole budget on thinking blocks.

    Returns:
        Model text response, or None if no provider available / all failed.
    """
    # Build the provider chain in priority order. Each entry is
    # (name, callable). The callable returns Optional[str].
    providers = []
    if core.api_key("XAI_API_KEY"):
        providers.append(("xai", _xai_chat))
    if core.api_key("OPENAI_API_KEY"):
        providers.append(("openai", _openai_compat_chat))
    if _HUANXIN_DIRECT and _HUANXIN_UPSTREAM_URL and _HUANXIN_UPSTREAM_TOKEN:
        providers.append(("huanxin_direct", _huanxin_direct_chat))
    if core.api_key("ANTHROPIC_API_KEY"):
        providers.append(("anthropic", _anthropic_chat))

    if not providers:
        return None

    # Agent-level retry: if every provider returns None/empty, wait and try
    # again, up to _RETRIES times. This absorbs transient backend blips
    # (the Huanxin backend in particular has ~30% 500-rate that the proxy
    # retries internally, but sometimes the proxy itself gives up).
    last_err = None
    for attempt in range(_RETRIES):
        for name, fn in providers:
            model = _pick_model(name, strong)
            try:
                out = fn(system, user, model=model,
                         temperature=temperature, max_tokens=max_tokens,
                         disable_thinking=disable_thinking)
            except Exception as e:
                _log(f"{name} raised: {repr(e)[:200]}")
                out = None
                last_err = e
            if out and out.strip():
                return out
            # Empty / null response -- try next provider
        if attempt + 1 < _RETRIES:
            delay = min(_RETRY_BASE * (2 ** attempt), 8.0)
            _log(f"all providers returned empty (attempt {attempt+1}/{_RETRIES}); "
                 f"sleeping {delay:.1f}s and retrying")
            time.sleep(delay)
    if last_err:
        _log(f"all providers failed after {_RETRIES} retries; last err: "
             f"{repr(last_err)[:200]}")
    return None


def _pick_model(provider: str, strong: bool) -> str:
    """Pick the model for a given provider + tier."""
    if provider == "xai":
        return _DEFAULT_XAI_MODEL
    if provider == "openai":
        return _DEFAULT_OPENAI_MODEL
    if provider == "huanxin_direct":
        return _HUANXIN_MODEL
    if provider == "anthropic":
        return _DEFAULT_ANTHROPIC_STRONG_MODEL if strong else _DEFAULT_ANTHROPIC_FAST_MODEL
    return ""


def available_provider() -> Optional[str]:
    """Return the name of the first available provider, or None."""
    if core.api_key("XAI_API_KEY"):
        return "xai"
    if core.api_key("OPENAI_API_KEY"):
        return "openai"
    if _HUANXIN_DIRECT and _HUANXIN_UPSTREAM_URL and _HUANXIN_UPSTREAM_TOKEN:
        return "huanxin_direct"
    if core.api_key("ANTHROPIC_API_KEY"):
        return "anthropic"
    return None


def probe_llm() -> dict:
    """Test every configured provider and return a status dict.
    Used by `agent_cli.py --probe-llm` for diagnostics.
    """
    out = {"providers": {}, "recommended": available_provider()}
    # Simple test prompt that any model should handle
    sys_p = "You are a test echo. Reply with the exact JSON requested."
    usr_p = 'Reply with exactly: {"ok": true}'
    for name, fn, model in (
        ("xai", _xai_chat, _DEFAULT_XAI_MODEL),
        ("openai", _openai_compat_chat, _DEFAULT_OPENAI_MODEL),
        ("huanxin_direct", _huanxin_direct_chat, _HUANXIN_MODEL),
        ("anthropic", _anthropic_chat,
         _DEFAULT_ANTHROPIC_FAST_MODEL),
    ):
        # Skip providers that aren't configured
        if name == "xai" and not core.api_key("XAI_API_KEY"):
            out["providers"][name] = {"configured": False}
            continue
        if name == "openai" and not core.api_key("OPENAI_API_KEY"):
            out["providers"][name] = {"configured": False}
            continue
        if name == "huanxin_direct" and not (_HUANXIN_DIRECT and
                                              _HUANXIN_UPSTREAM_URL and
                                              _HUANXIN_UPSTREAM_TOKEN):
            out["providers"][name] = {"configured": False}
            continue
        if name == "anthropic" and not core.api_key("ANTHROPIC_API_KEY"):
            out["providers"][name] = {"configured": False}
            continue
        out["providers"][name] = {"configured": True, "model": model,
                                   "endpoint": "varies"}
        try:
            t0 = time.time()
            resp = fn(sys_p, usr_p, model=model, max_tokens=40,
                      temperature=0.0)
            out["providers"][name]["latency_ms"] = int((time.time() - t0) * 1000)
            if resp and resp.strip():
                out["providers"][name]["status"] = "ok"
                out["providers"][name]["response_preview"] = resp[:200]
            else:
                out["providers"][name]["status"] = "empty"
                out["providers"][name]["response_preview"] = ""
        except Exception as e:
            out["providers"][name]["status"] = "error"
            out["providers"][name]["error"] = repr(e)[:200]
    return out


def parse_json_response(text: Optional[str]) -> Optional[dict]:
    """Parse a JSON object from an LLM response that may contain prose or
    code fences. Returns dict or None."""
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip()
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b < 0 or b <= a:
        return None
    try:
        return json.loads(t[a:b+1])
    except json.JSONDecodeError:
        return None
