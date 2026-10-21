"""Tool registry: exposes the existing wt scanners as agent-callable tools.

Each tool is (name, description, schema, callable). The agent prompts list
these tools so the LLM knows what it can ask for. All tool calls go through
Python functions (not LLM-generated code) -- the LLM picks the tool and
args, we execute. This is the same pattern used by AutoHedge's
tools_registry.py and Vibe-Trading's tool layer.

Centralizing this means:
  - The agent never duplicates data-fetching code that the CLI already has.
  - New wt modules are auto-discoverable as tools (just add a wrapper here).
  - Tools can be rate-limited / cached in one place.
"""
from __future__ import annotations
import json, time
from typing import Any, Callable, Dict, List, Optional

# In-package imports are lazy to avoid import cycles with wt.* modules
# that themselves import from wt.agent at runtime.

TOOLS: Dict[str, Dict[str, Any]] = {}
_TOOL_CALL_LOG: List[Dict[str, Any]] = []


def _register(name: str, description: str, args: Dict[str, str],
              fn: Callable[..., Any]) -> None:
    TOOLS[name] = {
        "name": name,
        "description": description,
        "args": args,
        "fn": fn,
    }


def list_tools() -> List[str]:
    """Return tool names in stable insertion order."""
    return list(TOOLS.keys())


def call_tool(name: str, **kwargs) -> Any:
    """Execute a registered tool by name. Raises KeyError if unknown.
    All calls are logged for the orchestrator's reflection step."""
    if name not in TOOLS:
        raise KeyError(f"unknown tool: {name!r}; available: {list(TOOLS.keys())}")
    t0 = time.time()
    err = None
    try:
        out = TOOLS[name]["fn"](**kwargs)
        # If the tool returns something huge, summarize before storing in the log
        # so memory doesn't blow up. Full output still goes to the caller.
        return out
    except Exception as e:
        err = repr(e)
        raise
    finally:
        _TOOL_CALL_LOG.append({
            "tool": name, "args": kwargs, "error": err,
            "ms": int((time.time() - t0) * 1000),
        })


def tool_call_log() -> List[Dict[str, Any]]:
    return list(_TOOL_CALL_LOG)


# ---------------------------------------------------------------------------
# Tool: scan_markets
# Run the existing one-command global scan (wt.report.build_report) and
# return the top-N ranked opportunity rows.
# ---------------------------------------------------------------------------

def _tool_scan_markets(top_n: int = 15, live_only: bool = True,
                      no_options: bool = False) -> Dict[str, Any]:
    """Run the full scan pipeline (same as `python tools/scan.py`).

    Thin wrapper around the same wt.report functions the CLI uses, so the
    agent sees exactly what the CLI would show -- no duplicated
    data-fetching logic.
    """
    from wt import report as _r
    # 1. Regime (FRED + VIX + fear-greed)
    regime, _fred_rows, fg, macro = _r.gather_regime(use_fred=True)
    vix = macro.get("VIXCLS") if isinstance(macro, dict) else None
    # 2. Quotes -- the full global universe (crypto RT, US, CN-A, TW, FX)
    quotes = _r.collect_quotes(live_only=live_only)
    # 3. Build scored opportunities (runs the backtest + Bonferroni gate)
    scored, _proxy_notes = _r.build_opportunities(quotes, regime, vix=vix)
    # 4. Enrich -- technicals are cheap and always run; the others are
    #    optional but make the rows much more useful for the agent.
    try:
        scored = _r.enrich_with_technicals(scored, regime, vix=vix)
    except Exception:
        pass
    try:
        scored = _r.enrich_with_news(scored)
    except Exception:
        pass
    try:
        scored = _r.enrich_with_catalysts(scored)
    except Exception:
        pass
    if not no_options:
        try:
            scored = _r.enrich_with_options(scored)
        except Exception:
            pass
    # 5. Trim to top_n -- keep only the fields the agent actually reads,
    #    so the context window stays small.
    slim_rows = []
    for r in scored[:top_n]:
        slim_rows.append({
            k: r.get(k) for k in (
                "sym", "native", "region", "price", "chg",
                "thesis", "rr", "stop", "target", "score", "news",
                "catalyst", "actionable", "t", "oos_sharpe",
                "n_tests", "bonferroni_t",
            ) if k in r
        })
    return {
        "regime": regime,
        "fear_greed": fg,
        "macro": macro if isinstance(macro, dict) else {},
        "vix": vix,
        "rows": slim_rows,
        "n_total": len(scored),
    }


_register(
    "scan_markets",
    "Run the full global opportunity scan (US+CN+crypto+FX+futures) and "
    "return the top-N ranked setups with thesis, reward:risk, stop, target, "
    "score, news, and catalyst. This is the primary opportunity-discovery "
    "tool. Use first.",
    {"top_n": "int (default 15): number of top rows to return",
     "live_only": "bool (default True): only include markets that are open now",
     "no_options": "bool (default False): skip options enrichment (faster)"},
    _tool_scan_markets,
)


# ---------------------------------------------------------------------------
# Tool: deep_dive
# Run wt.deepdive on a single ticker for a comprehensive report.
# ---------------------------------------------------------------------------

def _tool_deep_dive(sym: str, region: Optional[str] = None) -> Dict[str, Any]:
    """Run a comprehensive deep-dive on a single ticker.

    Uses wt.deepdive.gather() to pull all the underlying data, then
    deepdive.deep_dive_analysis() for the bull/bear/base case.
    """
    from wt import deepdive as _d
    try:
        data = _d.gather(sym, want_llm=False, want_sec=True, want_hn=True)
    except Exception as e:
        return {"error": f"gather failed: {repr(e)[:200]}"}
    try:
        analysis = _d.deep_dive_analysis(sym, data=data, want_llm=False)
    except Exception as e:
        analysis = {"error": f"analysis failed: {repr(e)[:200]}"}
    # data can be large; keep only the summary fields the agent needs
    slim = {}
    if isinstance(data, dict):
        for k in ("sym", "price", "fundamentals", "headlines", "peers",
                  "catalyst", "iv", "stats"):
            if k in data:
                v = data[k]
                # Cap any nested blob to 800 chars to bound context
                slim[k] = v if not isinstance(v, (dict, list)) else (
                    json.dumps(v, default=str)[:800]
                )
    slim["analysis"] = analysis if isinstance(analysis, dict) else str(analysis)[:800]
    return slim


_register(
    "deep_dive",
    "Run a comprehensive deep-dive on a single ticker: valuation, growth, "
    "quality, momentum, peers, catalysts, options IV, news, and a final "
    "bull/bear/base case. Use after scan_markets to validate a candidate.",
    {"sym": "str: ticker symbol (e.g. 'AAPL', '600519.SS', 'BTC-USD')",
     "region": "str or None: region hint ('US','CN','CRYPTO','FX', ...)"},
    _tool_deep_dive,
)


# ---------------------------------------------------------------------------
# Tool: breaking_news
# Run wt.breaking to surface market-moving news in the last N hours.
# ---------------------------------------------------------------------------

def _tool_breaking_news(hours: int = 24, limit: int = 20) -> Dict[str, Any]:
    """Surface market-moving news from the last N hours.

    Uses wt.deepdive.breaking_news_scan -- the same function the
    `scan.py --breaking` flag uses.
    """
    from wt import deepdive as _d
    try:
        results = _d.breaking_news_scan(want_llm=False,
                                        window_hours=hours,
                                        max_themes=8,
                                        max_tickers_per_theme=limit)
    except Exception as e:
        return {"error": f"breaking_news_scan failed: {repr(e)[:200]}"}
    # results is typically a dict with themes -> list of events/tickers
    items = []
    if isinstance(results, dict):
        for theme, blob in results.items():
            if isinstance(blob, dict):
                for tkr, ev in (blob.get("tickers") or {}).items():
                    if isinstance(ev, dict):
                        items.append({
                            "theme": theme,
                            "sym": tkr,
                            "headline": ev.get("headline", ""),
                            "time": ev.get("time", ""),
                            "impact": ev.get("impact"),
                            "bias": ev.get("bias"),
                        })
            elif isinstance(blob, list):
                for ev in blob:
                    if isinstance(ev, dict):
                        items.append({"theme": theme, **ev})
    return {"items": items[:limit], "hours": hours, "n": len(items)}


_register(
    "breaking_news",
    "Surface market-moving news from the last N hours across all covered "
    "sources (Finnhub, Polygon, yfinance, Stocktwits, Reddit). Use to "
    "understand what is moving prices RIGHT NOW.",
    {"hours": "int (default 6): lookback window",
     "limit": "int (default 20): max items"},
    _tool_breaking_news,
)


# ---------------------------------------------------------------------------
# Tool: llm_sentiment
# Run wt.llm.judge_headlines on a list of headlines for a symbol.
# ---------------------------------------------------------------------------

def _tool_llm_sentiment(sym: str, headlines: List[str]) -> Dict[str, Any]:
    from wt import llm as _l
    out = _l.judge_headlines(sym, headlines)
    if out is None:
        return {"bias": "unknown", "confidence": 0.0,
                "reason": "no provider available or no headlines"}
    out.setdefault("bias", "unknown")
    out.setdefault("confidence", 0.0)
    return out


_register(
    "llm_sentiment",
    "Ask the configured LLM (xAI Grok -> Anthropic fallback) to read a list "
    "of headlines for a symbol and return {bias, confidence, reason}. Use "
    "as a tiebreaker when directional signals conflict.",
    {"sym": "str: ticker symbol",
     "headlines": "list[str]: 3-8 headlines (title only, no body)"},
    _tool_llm_sentiment,
)


# ---------------------------------------------------------------------------
# Tool: list_arb_setups
# Probe all arbitrage modules at once and return any that are currently
# profitable. Cheap way to find delta-neutral carry trades.
# ---------------------------------------------------------------------------

def _tool_list_arb_setups() -> Dict[str, Any]:
    found = {}
    # Each of these modules exposes a scan()/find() function returning a list
    # of opportunity dicts. We guard every call so one broken source doesn't
    # kill the agent.
    # (label, module, function_name) -- function_name because not every
    # module uses `scan` (rv_setups uses scan_rv_pairs, country_crisis
    # uses scan_country_crises).
    probes = [
        ("funding_arb", "wt.funding_arb", "scan"),
        ("spot_arb", "wt.spot_arb", "scan"),
        ("triangular_arb", "wt.triangular_arb", "scan"),
        ("dex_cex_arb", "wt.dex_cex_arb", "scan"),
        ("perp_spot_basis", "wt.perp_spot_basis", "scan"),
        ("stable_depeg", "wt.stable_depeg", "scan"),
        ("curve_depeg", "wt.curve_depeg", "scan"),
        ("calendar_spread", "wt.calendar_spread", "scan"),
        ("kimchi_premium", "wt.kimchi_premium", "scan"),
        ("prediction_market_arb", "wt.prediction_market_arb", "scan"),
        ("defi_rate_arb", "wt.defi_rate_arb", "scan"),
        ("rv_setups", "wt.rv_setups", "scan_rv_pairs"),
        ("stat_arb", "wt.stat_arb", "scan"),
    ]
    for label, modname, fnname in probes:
        try:
            mod = __import__(modname, fromlist=["_"])
            fn = getattr(mod, fnname, None)
            if fn is None:
                # Fall back to `scan` or `find` if the named function
                # isn't present (forward-compat with future renames).
                fn = getattr(mod, "scan", None) or getattr(mod, "find", None)
            if fn is None:
                continue
            res = fn() or []
            # Some scan functions return a tuple (rows, meta); take [0].
            if isinstance(res, tuple) and len(res) >= 1:
                res = res[0]
            if res:
                found[label] = res[:10]
        except Exception as e:
            found[label] = {"error": repr(e)[:200]}
    return {"arbs": found, "n_types": len(found)}


_register(
    "list_arb_setups",
    "Probe ALL arbitrage modules (funding, spot, triangular, dex/cex, basis, "
    "depeg, calendar, kimchi, prediction-market, defi-rate, rv, stat-arb) "
    "and return any currently profitable delta-neutral or carry setups. Use "
    "when you want non-directional ideas.",
    {},
    _tool_list_arb_setups,
)


# ---------------------------------------------------------------------------
# Tool: market_sessions
# Which markets are OPEN right now (the actionability gate).
# ---------------------------------------------------------------------------

def _tool_market_sessions() -> Dict[str, Any]:
    """Which markets are OPEN right now (the actionability gate)."""
    from wt import markets as _m
    from datetime import datetime, timezone
    out = {}
    for name in ("CRYPTO", "FX", "US", "CN-A", "TW", "HK"):
        try:
            # is_actionable is the project's canonical "is this market
            # tradeable right now" check. CRYPTO is always 24/7.
            out[name] = bool(_m.is_actionable(name)) if name != "CRYPTO" else True
        except Exception:
            # Fall back to market_status which returns a richer dict
            try:
                ms = _m.market_status(name) or {}
                out[name] = ms.get("open")
            except Exception:
                out[name] = None
    return {"sessions": out, "now_utc": datetime.now(timezone.utc).isoformat()}


_register(
    "market_sessions",
    "Return which markets are OPEN right now (CRYPTO, FX, US, CN-A, TW, HK). "
    "Use before relying on a live quote from a market that may be closed.",
    {},
    _tool_market_sessions,
)


# ---------------------------------------------------------------------------
# Tool: country_crisis
# ---------------------------------------------------------------------------

def _tool_country_crisis() -> Dict[str, Any]:
    """Scan for country-level crisis signals (CDS, FX weakness, capital controls)."""
    from wt import country_crisis as _c
    # The actual function is scan_country_crises (not scan). Fall back
    # to scan/find for forward-compat.
    fn = (getattr(_c, "scan_country_crises", None)
          or getattr(_c, "scan", None)
          or getattr(_c, "find", None))
    if fn is None:
        return {"error": "no scan_country_crises/scan/find function"}
    try:
        res = fn() or []
        if isinstance(res, tuple) and len(res) >= 1:
            res = res[0]
        return {"items": res[:20]}
    except Exception as e:
        return {"error": repr(e)[:200]}


_register(
    "country_crisis",
    "Scan for country-level crisis signals (CDS, FX weakness, capital controls) "
    "that could drive macro trades. Use when building a macro thesis.",
    {},
    _tool_country_crisis,
)


# ---------------------------------------------------------------------------
# Tool: gdelt_crisis_confirm  (added 2026-07-21)
# ---------------------------------------------------------------------------

def _tool_gdelt_crisis_confirm(country: str, hours: int = 48) -> Dict[str, Any]:
    """Confirm a country crisis with GDELT CAMEO-coded geopolitical events.

    Counts material-conflict events (CAMEO 15-20, quad_class=4) and
    computes avg Goldstein impact score over the last `hours` hours.
    A confirmed crisis (material_conflict_n >= 3 OR avg_goldstein <= -3.0)
    means the price-action signal is backed by a real geopolitical catalyst,
    not just a market drop.

    Use AFTER country_crisis surfaces a candidate, to confirm before
    sizing a CrisisShort or CrisisBounce setup."""
    from wt import country_crisis as _c
    try:
        res = _c.gdelt_crisis_confirmation(country, hours=hours)
        # Strip the events list from the agent-facing response (too verbose);
        # keep the counts + confirmation flag.
        return {
            "country": country,
            "material_conflict_n": res.get("material_conflict_n", 0),
            "verbal_conflict_n": res.get("verbal_conflict_n", 0),
            "cooperation_n": res.get("cooperation_n", 0),
            "avg_goldstein": res.get("avg_goldstein"),
            "confirmed": res.get("confirmed", False),
            "event_count": len(res.get("events") or []),
            "err": res.get("err"),
        }
    except Exception as e:
        return {"error": repr(e)[:200]}


_register(
    "gdelt_crisis_confirm",
    "Confirm a country-crisis candidate with GDELT geopolitical event data "
    "(CAMEO-coded). Returns material-conflict event count and avg Goldstein "
    "impact score. Use AFTER country_crisis surfaces a candidate, to "
    "distinguish a real geopolitical catalyst from a routine market drop.",
    {"country": "str: country name (e.g. 'Korea', 'Turkey', 'Argentina')",
     "hours": "int: lookback window in hours (default 48)"},
    _tool_gdelt_crisis_confirm,
)


# ---------------------------------------------------------------------------
# Tool: hyperliquid_funding  (the richest single crypto funding source)
# ---------------------------------------------------------------------------

def _tool_hyperliquid_funding(limit: int = 20) -> Dict[str, Any]:
    """Get current Hyperliquid funding rates (perps)."""
    from wt import hyperliquid_funding as _h
    # Actual signature: scan(min_funding_pct_1h=0.01, top_n=30).
    fn = getattr(_h, "scan", None)
    if fn is None:
        return {"error": "no scan function"}
    try:
        # Pass top_n=limit; min_funding_pct_1h=0 keeps everything (we'll
        # trim on our side).
        rows = fn(min_funding_pct_1h=0.0, top_n=limit) or []
        return {"items": rows[:limit]}
    except TypeError:
        # Older signature -- no kwargs.
        try:
            return {"items": (fn() or [])[:limit]}
        except Exception as e:
            return {"error": repr(e)[:200]}
    except Exception as e:
        return {"error": repr(e)[:200]}


_register(
    "hyperliquid_funding",
    "Get current Hyperliquid funding rates (perps). Use to find funding-arb "
    "or directional crypto carry opportunities.",
    {"limit": "int (default 20): max rows"},
    _tool_hyperliquid_funding,
)


# ---------------------------------------------------------------------------
# Tool: sharpe_ranked_setups  (HIGH-SHARPE OBJECTIVE for retail/small capital)
# Re-ranks the top scan rows by cost-adjusted per-trade Sharpe (edge), not
# the composite blend. Use when the user wants the highest-Sharpe trades
# specifically (retail, small account, no HFT -- we want QUALITY edges).
# ---------------------------------------------------------------------------

def _tool_sharpe_ranked_setups(top_n: int = 15, live_only: bool = True,
                                min_sharpe: float = 0.0) -> Dict[str, Any]:
    """Re-rank scan results by cost-adjusted per-trade Sharpe.

    Runs the same scan pipeline as scan_markets, then re-sorts the rows by
    `edge` (the cost-adjusted per-trade Sharpe from the backtest, which
    already nets out IBKR retail commission + spread). Rows with no
    backtest or Sharpe below min_sharpe are dropped. Returns the top_n by
    Sharpe with the Kelly fraction for each so the agent can size positions
    for a small account.
    """
    from wt import report as _r
    # 1. Regime + quotes + scored rows (same pipeline as scan_markets)
    try:
        regime, _fred_rows, fg, macro = _r.gather_regime(use_fred=True)
        vix = macro.get("VIXCLS") if isinstance(macro, dict) else None
        quotes = _r.collect_quotes(live_only=live_only)
        scored, _proxy_notes = _r.build_opportunities(quotes, regime, vix=vix)
    except Exception as e:
        return {"error": f"scan pipeline failed: {repr(e)[:200]}"}
    # 2. Re-rank by edge (cost-adjusted per-trade Sharpe). Keep only rows
    #    that have a backtest and clear min_sharpe.
    items = []
    for s in scored:
        bt = s.get("bt")
        if not bt:
            continue
        edge = bt.get("edge")
        if edge is None or edge < min_sharpe:
            continue
        rr = s.get("rr", {}) if isinstance(s.get("rr"), dict) else {}
        items.append({
            "sym": s.get("sym"),
            "region": s.get("region"),
            "price": s.get("price"),
            "setup": s.get("setup"),
            "side": rr.get("side"),
            "rr": rr.get("rr"),
            "edge": round(edge, 3),               # cost-adjusted per-trade Sharpe
            "exp_ret": round(bt.get("exp_ret", 0), 4),
            "p_win": round(bt.get("p_win", 0), 3),
            "tstat": round(bt.get("tstat", 0), 2),
            "n": bt.get("n"),
            "oos_edge": round(bt.get("oos_edge") or 0, 3),
            "oos_n": bt.get("oos_n"),
            "oos_exp": round(bt.get("oos_exp_ret") or 0, 4),
            "qualifies": s.get("qualifies"),
            "kelly_full": _kelly(bt.get("p_win"), rr.get("rr")),
        })
    # Sort by edge (cost-adjusted Sharpe) descending, tiebreak by OOS edge
    items.sort(key=lambda x: (x.get("edge") or -9, x.get("oos_edge") or -9,
                                x.get("exp_ret") or -9), reverse=True)
    return {
        "regime": regime if isinstance(regime, dict) else {},
        "vix": vix,
        "objective": "high-sharpe (cost-adjusted per-trade edge, retail commission net)",
        "rows": items[:top_n],
        "n_total": len(items),
        "note": ("Rows are ranked by `edge` = cost-adjusted per-trade Sharpe "
                 "(nets IBKR retail commission + spread). Use kelly_position_size "
                 "to convert each row's p_win/rr into a dollar ticket for the "
                 "small account."),
    }


def _kelly(p, rr):
    """Safe Kelly fraction; returns None on bad input."""
    try:
        from wt import analysis as _a
        k = _a.kelly_fraction(p, rr)
        return round(k, 4) if k is not None else None
    except Exception:
        return None


_register(
    "sharpe_ranked_setups",
    "Re-rank the global scan by COST-ADJUSTED per-trade Sharpe (edge), not "
    "the composite blend. Use when the objective is HIGH SHARPE specifically "
    "(retail, small account, no HFT -- we want quality edges, not fat R:R "
    "with low win rate). Each row includes kelly_full for sizing.",
    {"top_n": "int (default 15): number of top-Sharpe rows to return",
     "live_only": "bool (default True): only markets open now",
     "min_sharpe": "float (default 0.0): drop rows with edge below this"},
    _tool_sharpe_ranked_setups,
)


# ---------------------------------------------------------------------------
# Tool: kelly_position_size  (SMALL CAPITAL position sizer)
# Converts a setup's (p_win, rr) + account equity into a concrete dollar
# ticket using HALF-Kelly, capped at 20% of equity, with the retail
# commission bite reported so we never take a trade where the $0.35 IBKR
# minimum eats the edge.
# ---------------------------------------------------------------------------

def _tool_kelly_position_size(sym: str, p_win: float, rr: float,
                               equity_usd: float, region: str = "US",
                               risk_frac: Optional[float] = None,
                               price: Optional[float] = None) -> Dict[str, Any]:
    """Small-capital position sizer for a single setup.

    Inputs:
      sym        -- the ticker (for reference in the output)
      p_win      -- historical win rate from the backtest (0-1)
      rr         -- live reward:risk ratio
      equity_usd -- current account equity in USD
      region     -- market (US/CN/HK/FX/CRYPTO) for the commission model
      risk_frac  -- stop distance as a fraction of price (e.g. 0.03 = 3% stop)
      price      -- live price (for share count). If None, shares=None.

    Returns the full kelly_position_size dict (kelly_full, kelly_used,
    notional_usd, shares, commission_bps, dollar_risk_usd, skip_reason)
    plus the sym and a human-readable ticket string.
    """
    from wt import analysis as _a
    market = (region or "US").upper()
    # If price isn't given, try to fetch it
    if price is None:
        try:
            from wt import sources as _src
            q = _src.requote(sym, market=market)
            if isinstance(q, dict):
                price = q.get("price") or q.get("last")
        except Exception:
            pass
    out = _a.kelly_position_size(p_win, rr, equity_usd,
                                  risk_frac=risk_frac, price=price,
                                  market=market)
    out["sym"] = sym
    out["region"] = market
    out["equity_usd"] = equity_usd
    # Human-readable ticket
    if out.get("skip_reason") and out.get("kelly_full", 0) <= 0:
        out["ticket"] = f"SKIP {sym}: {out['skip_reason']}"
    elif out.get("shares") is not None and out["shares"] > 0:
        out["ticket"] = (f"BUY {out['shares']} {sym} @ ~${price:.2f} "
                          f"= ${out['notional_usd']:.0f} "
                          f"(half-Kelly {out['kelly_used']*100:.1f}% of equity, "
                          f"~{out.get('commission_bps')}bps commission)")
    else:
        out["ticket"] = f"SKIP {sym}: {out.get('skip_reason', 'cannot size')}"
    return out


_register(
    "kelly_position_size",
    "Small-capital position sizer. Converts (p_win, rr) + account equity "
    "into a HALF-Kelly dollar ticket, capped at 20% of equity, with the "
    "retail IBKR commission bite reported. Use AFTER picking a setup to "
    "size the trade for our small account. If the commission bite exceeds "
    "the edge, skip_reason will say so.",
    {"sym": "str: the ticker",
     "p_win": "float: historical win rate from backtest (0-1)",
     "rr": "float: live reward:risk ratio",
     "equity_usd": "float: current account equity in USD",
     "region": "str (default 'US'): market for commission model",
     "risk_frac": "float (optional): stop distance as fraction of price",
     "price": "float (optional): live price (fetched if omitted)"},
    _tool_kelly_position_size,
)


# ---------------------------------------------------------------------------
# Tool: options_chain -- ATM straddle + IV for a US ticker
# ---------------------------------------------------------------------------

def _tool_options_chain(sym: str, max_dte: int = 30) -> Dict[str, Any]:
    """Get the ATM straddle (price, IV, expected move) for a US ticker."""
    from wt import options as _o
    try:
        # straddle returns dict with iv, expected_move_pct, etc.
        sd = _o.straddle(sym, max_dte=max_dte)
        if not isinstance(sd, dict):
            return {"error": f"straddle returned {type(sd).__name__}"}
        # Trim any oversized fields
        out = {}
        for k, v in sd.items():
            if isinstance(v, (dict, list)):
                out[k] = json.dumps(v, default=str)[:400]
            else:
                out[k] = v
        return out
    except Exception as e:
        return {"error": f"options.straddle failed: {repr(e)[:200]}"}


_register(
    "options_chain",
    "Get the ATM straddle (price, implied volatility, expected move %) for a "
    "US ticker. Use to judge whether options are cheap or expensive and to "
    "size a defined-risk options trade.",
    {"sym": "str: US ticker (e.g. 'AAPL', 'TSLA')",
     "max_dte": "int (default 30): max days to expiry"},
    _tool_options_chain,
)


# ---------------------------------------------------------------------------
# Tool: peers -- peer cluster for a ticker
# ---------------------------------------------------------------------------

def _tool_peers(sym: str) -> Dict[str, Any]:
    """Return the peer cluster for a ticker (for relative-value comparison)."""
    from wt import peers as _p
    try:
        ps = _p.peers_of(sym)
        return {"peers": ps if isinstance(ps, list) else [str(ps)][:20]}
    except Exception as e:
        return {"error": f"peers.peers_of failed: {repr(e)[:200]}"}


_register(
    "peers",
    "Return the peer cluster for a ticker. Use to find relative-value "
    "trades (long the cheap one, short the expensive one in the same cluster).",
    {"sym": "str: ticker symbol"},
    _tool_peers,
)


# ---------------------------------------------------------------------------
# Tool: catalysts -- earnings/FDA/IPO/dividend calendar
# ---------------------------------------------------------------------------

def _tool_catalysts(days: int = 14) -> Dict[str, Any]:
    """Return the catalyst calendar (earnings/FDA/IPO/dividends)."""
    from wt import catalysts as _c
    out = {}
    try:
        out["earnings"] = _c.earnings_calendar(days=days) or []
    except Exception as e:
        out["earnings_error"] = repr(e)[:200]
    try:
        out["ipo"] = _c.ipo_calendar(days=days) or []
    except Exception as e:
        out["ipo_error"] = repr(e)[:200]
    try:
        out["fda"] = _c.fda_calendar(days=days) or []
    except Exception as e:
        out["fda_error"] = repr(e)[:200]
    # Trim each list to first 15 entries to bound context
    for k in ("earnings", "ipo", "fda"):
        if isinstance(out.get(k), list):
            out[k] = out[k][:15]
    return out


_register(
    "catalysts",
    "Return the catalyst calendar (earnings / FDA / IPO) for the next N days. "
    "Use to find ticker-specific event-driven trades.",
    {"days": "int (default 14): look-ahead window in days"},
    _tool_catalysts,
)


# ---------------------------------------------------------------------------
# Tool: portfolio -- current Alpaca paper positions (for risk manager)
# ---------------------------------------------------------------------------

def _tool_portfolio() -> Dict[str, Any]:
    """Return the current Alpaca paper-trading portfolio snapshot."""
    from wt import alpaca_paper as _ap
    try:
        acct = _ap.account()
    except Exception as e:
        return {"error": f"alpaca.account failed: {repr(e)[:200]}",
                "hint": "set ALPACA_PAPER_KEY / ALPACA_PAPER_SECRET to enable"}
    try:
        pos = _ap.positions()
    except Exception as e:
        pos = []
    return {
        "account": acct if isinstance(acct, dict) else {"raw": str(acct)[:400]},
        "positions": pos if isinstance(pos, list) else [],
        "n_positions": len(pos) if isinstance(pos, list) else 0,
    }


_register(
    "portfolio",
    "Return the current Alpaca paper-trading account + open positions. Use "
    "to check existing exposure before sizing a new trade (risk-manager input).",
    {},
    _tool_portfolio,
)


# ---------------------------------------------------------------------------
# Render tool catalog as a prompt string for the LLM
# ---------------------------------------------------------------------------

def render_tool_catalog() -> str:
    """Return a compact string describing all tools, for inclusion in prompts."""
    lines = []
    for name, t in TOOLS.items():
        arg_str = ", ".join(f"{k}: {v}" for k, v in t["args"].items()) or "(no args)"
        lines.append(f"- {name}({arg_str}) -- {t['description']}")
    return "\n".join(lines)


def render_tool_call_log() -> str:
    """Return a compact string of all tool calls made so far (for reflection)."""
    if not _TOOL_CALL_LOG:
        return "(no tool calls yet)"
    lines = []
    for i, c in enumerate(_TOOL_CALL_LOG, 1):
        args_str = json.dumps(c["args"], default=str)[:120]
        status = "ok" if not c["error"] else f"ERR {c['error']}"
        lines.append(f"{i}. {c['tool']}({args_str}) -> {status} [{c['ms']}ms]")
    return "\n".join(lines)
