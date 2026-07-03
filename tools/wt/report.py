"""Assemble the full market snapshot and the ranked opportunity table.

Pipeline (objective = fast, high reward:risk, low-risk short-term trades):
  1. Pull regime inputs (FRED/curve/fear-greed) -> classify risk-on/off.
  2. Pull live/real-time quotes across crypto, US, China, Taiwan, ETFs.
  3. (optional) Pull daily history for technicals on key names.
  4. Score every instrument's best long/short R:R; apply shortability rules
     (long-only markets -> proxy suggestions).
  5. Blend into a composite quality score; rank; print the bar + top ideas.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from . import core, sources, analysis, altdata, news, markets, instruments as inst
from . import catalysts

def _fnum(v):
    try: return float(v)
    except (TypeError, ValueError): return None

# Max age (seconds) a quote may have and still be "actionable", per market. An
# open market with a stale feed is just as useless as a closed one, so we gate
# on BOTH market-open AND data-freshness. Crypto/FX tick continuously; equities
# get a wider window because a just-closed session is still tradeable next open.
MAX_AGE_S = {
    "CRYPTO": 15 * 60,        # 15 min -- real-time book
    "FX":     30 * 60,        # 30 min
    "US":     8 * 3600,       # within the current/just-closed session
    "CN-A":   8 * 3600,
    "TW":     8 * 3600,
    "HK":     8 * 3600,
    "DEFAULT": 8 * 3600,
}

def is_tradeable_now(s, now=None):
    """A row is tradeable ONLY if (a) its market is open or just-closed AND
    (b) its quote is fresh enough for that market. This is the core trading
    rule: never surface a stale price as if it were actionable."""
    mkt = inst.market_of(s["sym"])
    if not markets.is_actionable(mkt, now):
        return False
    age = core.age_seconds(s.get("ts"))
    if age is None:                      # no timestamp -> cannot trust freshness
        return False
    return age <= MAX_AGE_S.get(mkt, MAX_AGE_S["DEFAULT"])

def gather_regime(use_fred=True):
    """Return (regime dict, raw macro rows, fear_greed)."""
    macro = {}
    rows = []
    if use_fred and core.api_key("FRED_KEY"):
        rows = altdata.fred_all()
        for name, sid, v, date in rows:
            macro[sid] = _fnum(v)
    fg, _ = altdata.crypto_fear_greed()
    btc, _ = sources.crypto_quote("BTC")
    btc7d = None  # coinlore not used here; leave to regime defaults
    regime = analysis.classify_regime(
        vix=macro.get("VIXCLS"), hy_spread=macro.get("BAMLH0A0HYM2"),
        curve=macro.get("T10Y2Y"),
        dxy_chg=None, btc_7d=btc7d)
    return regime, rows, fg, macro

def collect_quotes(live_only=False):
    """Fetch a broad set of quotes. Returns list of (label, sym, native, q)."""
    out = []
    # crypto (real-time)
    for s in inst.CRYPTO[:12]:
        q, err = sources.crypto_quote(s)
        if q: out.append((f"Crypto: {s}", s, "", q))
    # US real-time via Nasdaq (ETFs + megacaps + sectors + region/macro ETFs)
    us = (inst.US_EQUITY + inst.US_SECTORS + inst.REGION_ETF + inst.MACRO_ETF)
    for label, sym, native, q, err in sources.fetch_many(sources.nasdaq_quote, us, workers=12):
        if q: out.append((label, sym, native, q))
    # China A-shares (Sina live)
    for label, sym, native, q, err in sources.fetch_many(sources.sina_quote, inst.CHINA_A, workers=8):
        if q: out.append((label, sym, native, q))
    # Taiwan (TWSE live)
    for label, sym, native, q, err in sources.fetch_many(sources.twse_quote, inst.TAIWAN, workers=6):
        if q: out.append((label, sym, native, q))
    # Hong Kong (Sina rt_hk live; freely shortable -> long & short both actionable)
    for label, sym, native, q, err in sources.fetch_many(sources.hk_quote, inst.HK_STOCKS, workers=10):
        if q: out.append((label, sym, native, q))
    # FX majors (Twelve Data) -- real backtestable market, freely shortable
    for sym in inst.FX_MAJORS:
        q, err = sources.twelvedata_quote(sym)
        if q: out.append((f"FX: {sym}", sym, "", q))
    return out

def collect_wide_us(top_n=150):
    """STAGE 1 of the wide funnel: pull the ENTIRE US market (~12k tickers) in one
    Polygon grouped-daily call, cheaply pre-screen every name, and return the
    top_n most promising as quote rows (same shape as collect_quotes()).

    This is how we scan thousands of instruments per run without thousands of
    calls: one bulk snapshot for breadth, then spend the expensive backtest
    budget only on the best candidates (stage 2 happens in enrich_with_technicals).
    Returns (quote_rows, meta) where meta has universe size + screened count.
    """
    grp, err = sources.polygon_grouped_daily()
    if not grp:
        return [], {"err": err, "universe": 0, "screened": 0}
    rows = grp["rows"]
    ranked = []
    for r in rows:
        sc = analysis.prescreen_score(r)
        if sc is None:
            continue
        ranked.append((sc, r))
    ranked.sort(key=lambda x: -x[0])
    picks = ranked[:top_n]
    out = []
    for sc, r in picks:
        sym = r["T"]
        o, h, l, c = r.get("o"), r.get("h"), r.get("l"), r.get("c")
        dp = ((c - o) / o * 100) if o else None
        # grouped-daily is end-of-day for `date`; stamp ts to that close.
        ts = int(r["t"] / 1000) if r.get("t") else None
        q = {"c": c, "price": c, "o": o, "h": h, "l": l, "dp": dp, "ts": ts,
             "prescreen": sc}
        out.append((f"US: {sym}", sym, "", q))
    return out, {"err": None, "universe": len(rows), "screened": len(ranked),
                 "date": grp["date"]}

# China A-share prescreen: like the US one but liquidity is measured in CNY
# turnover (the node list gives it directly) rather than reconstructed $-volume.
CN_MIN_PRICE = 2.0        # skip sub-¥2 penny names
CN_MIN_TURNOVER = 8e7     # >= ¥80M traded today -> genuinely liquid

def _cn_prescreen(r):
    o, h, l, c = r.get("o"), r.get("h"), r.get("l"), r.get("c")
    amt = r.get("amount") or 0
    if not o or not c or not h or not l or h <= l or c < CN_MIN_PRICE:
        return None
    if amt < CN_MIN_TURNOVER:
        return None
    import math
    rng = (h - l) / c
    move = abs(c - o) / o
    liq = min(1.0, math.log10(amt) / 11.0)   # 0..1, saturates ~¥100B
    return round((rng * 0.6 + move * 0.4) * (0.5 + 0.5 * liq) * 100, 3)

def collect_wide_cn(top_n=120, pages=6):
    """STAGE 1 of the China funnel: pull the whole A-share market (~5,500 names,
    most-liquid-first) in a few bulk calls, pre-screen every name, and return the
    top_n as quote rows (same shape as collect_quotes()). This is the Asian
    counterpart to collect_wide_us -- so China finally gets thousands of shots at
    the bar, backtested, instead of a curated dozen. Returns (rows, meta)."""
    rows, err = sources.sina_ashare_list(pages=pages)
    if not rows:
        return [], {"err": err, "universe": 0, "screened": 0}
    ranked = []
    for r in rows:
        sc = _cn_prescreen(r)
        if sc is not None:
            ranked.append((sc, r))
    ranked.sort(key=lambda x: -x[0])
    out = []
    for sc, r in ranked[:top_n]:
        sym = r["T"]
        q = {"c": r["c"], "price": r["c"], "o": r["o"], "h": r["h"], "l": r["l"],
             "dp": r.get("dp"), "ts": r.get("ts"), "prescreen": sc}
        out.append((f"CN: {r['name']}", sym, r.get("name", ""), q))
    return out, {"err": None, "universe": len(rows), "screened": len(ranked)}

def build_opportunities(quotes, regime, vix=None):
    """Score, apply shortability, rank by composite. Returns (ranked, proxy_notes)."""
    scored, proxy_notes = [], []
    for label, sym, native, q in quotes:
        rr = analysis.score_rr(q.get("c"), q.get("h"), q.get("l"), q.get("dp"),
                               vix=vix, atr_val=None)
        if not rr:
            continue
        mkt = inst.market_of(sym)
        if rr["side"] == "Short" and not inst.SHORT_ALLOWED.get(mkt, True):
            px = inst.SHORT_PROXY.get(mkt, [])
            plist = ", ".join(f"{t} ({d})" for t, d in px) or "a shortable US ETF/ADR"
            nm = f"{label} {native}".strip()
            proxy_notes.append(f"{nm} ({sym}): bearish setup but {mkt} is "
                               f"long-only/short-restricted -> proxy: {plist}")
            continue
        # Drop degenerate rows where the stop is inside noise (risk < floor):
        # their R:R is a meaningless artifact, not a real low-risk edge.
        # FX majors move ~0.2%/day, so their honest floor is lower than equities;
        # we still let the backtest + t-stat/OOS gates judge them on merit.
        floor = analysis.RISK_MIN_FX if mkt == "FX" else analysis.RISK_MIN
        if rr["risk"] < floor:
            continue
        comp = analysis.composite_score(rr, tech=None, rs=None,
                                        regime_score=regime["score"])
        age, flag = core.freshness(q.get("ts"))
        scored.append({"label": label, "sym": sym, "native": native, "rr": rr,
                       "comp": comp, "price": q.get("c"), "dp": q.get("dp"),
                       "tech": None, "fresh": flag, "ts": q.get("ts"),
                       "live": age is not None and age <= core.MAX_STALE_S})
    # Rank: qualifying first, then by composite quality (not raw R:R, which can
    # be inflated by tight noise-level stops).
    scored.sort(key=lambda x: (not x["rr"]["passes"], -x["comp"], -x["rr"]["rr"]))
    return scored, proxy_notes

def enrich_with_technicals(scored, regime, top_n=20, vix=None):
    """Attach technicals + relative strength AND backtest each candidate across a
    LIBRARY of setups. Rank by per-trade Sharpe.

    The objective: HIGH expected return, SMALL standard deviation -> BIG
    per-trade expected Sharpe. For each candidate we measure TWO kinds of edge
    over ~1.5y of daily bars:
      (a) the baseline unconditional breakout geometry (backtest_expectancy), and
      (b) every CONDITIONAL setup in analysis.scan_setups() whose entry signal is
          FIRING on the latest bar -- oversold bounce, breakout, trend pullback...
    We keep whichever measured edge is best (qualifying first, then Sharpe), so a
    name can be surfaced via the specific strategy that actually has an edge in
    it right now -- far more shots at the SAME strict bar than one fixed rule.

      - US equities/ETFs  -> Polygon/Nasdaq daily history, RS vs SPY
      - Crypto            -> Binance daily klines, RS vs BTC (always-live)
      - FX majors         -> TwelveData daily history
    Non-covered rows (China A-share / Taiwan) lack free history -> no
    expectancy estimate, so they cannot rank above measured edges.
    """
    spy_hist, _ = sources.nasdaq_history("SPY", 200)
    spy_close = spy_hist["close"] if spy_hist else None
    btc_hist, _ = sources.binance_klines("BTC", limit=200)
    btc_close = btc_hist["close"] if btc_hist else None

    us = [s for s in scored if inst.market_of(s["sym"]) == "US"][:max(top_n, 150)]
    cx = [s for s in scored if inst.market_of(s["sym"]) == "CRYPTO"][:top_n]

    def _process(s, h, bench_close, market):
        tech = analysis.tech_pack(h["high"], h["low"], h["close"])
        rs = analysis.relative_strength(h["close"], bench_close) if bench_close else None
        # (a) baseline unconditional geometry from the live intraday R:R.
        base_bt = analysis.backtest_expectancy(
            h["high"], h["low"], h["close"],
            risk_frac=s["rr"]["risk"], reward_frac=s["rr"]["reward"],
            side=s["rr"]["side"], market=market)
        # (b) conditional strategy library -- only setups firing on the last bar.
        setups = analysis.scan_setups(h["high"], h["low"], h["close"],
                                      market=market, vix=vix, require_firing=True)
        return tech, rs, base_bt, setups

    def work_us(s):
        # Polygon history scales to ~150 names on one provider; fall back to
        # Nasdaq for the curated core names if Polygon misses one.
        h, _ = sources.polygon_history(s["sym"])
        if not h:
            h, _ = sources.nasdaq_history(s["sym"], 400)
        if not h: return s, None
        return s, _process(s, h, spy_close, "US")

    def work_cx(s):
        h, _ = sources.binance_klines(s["sym"], limit=400)
        if not h: return s, None
        return s, _process(s, h, btc_close, "CRYPTO")

    def work_fx(s):
        h, _ = sources.twelvedata_history(s["sym"], 400)
        if not h: return s, None
        return s, _process(s, h, None, "FX")

    def work_cn(s):
        # A-shares are LONG-ONLY for foreign/retail -> keep only long setups so we
        # never surface an un-actionable short. History via Sina (Tencent fallback).
        h, _ = sources.cn_history(s["sym"], 400)
        if not h: return s, None
        tech = analysis.tech_pack(h["high"], h["low"], h["close"])
        base_bt = None
        if s["rr"]["side"] == "Long":
            base_bt = analysis.backtest_expectancy(
                h["high"], h["low"], h["close"], risk_frac=s["rr"]["risk"],
                reward_frac=s["rr"]["reward"], side="Long", market="CN")
        setups = [sb for sb in analysis.scan_setups(
                    h["high"], h["low"], h["close"], market="CN", vix=vix,
                    require_firing=True) if sb["side"] == "Long"]
        return s, (tech, None, base_bt, setups)

    def work_hk(s):
        # HK is freely shortable -> both long & short setups are actionable.
        # History via Tencent hkfqkline; benchmark RS not wired (no HSI history here).
        h, _ = sources.hk_history(s["sym"], 400)
        if not h: return s, None
        return s, _process(s, h, None, "HK")

    fx = [s for s in scored if inst.market_of(s["sym"]) == "FX"][:top_n]
    cn = [s for s in scored if inst.market_of(s["sym"]) == "CN-A"][:max(top_n, 120)]
    hk = [s for s in scored if inst.market_of(s["sym"]) == "HK"][:max(top_n, 60)]
    jobs = [(work_us, us), (work_cx, cx), (work_fx, fx), (work_cn, cn), (work_hk, hk)]
    tested = []   # every backtest run -> the multiple-testing family (Bonferroni)
    with ThreadPoolExecutor(max_workers=10) as p:
        for fn, group in jobs:
            for s, res in p.map(fn, group):
                if not res:
                    continue
                tech, rs, base_bt, setups = res
                s["tech"] = tech
                s["rs"] = rs
                # Build the option set: baseline geometry + each firing setup.
                # Each option is (bt, rr, setup_name); every bt joins the family.
                options = []
                if base_bt:
                    options.append((base_bt, s["rr"], None))
                    tested.append(base_bt)
                for sb in setups:
                    rr2 = analysis.rr_from_setup(s.get("price"), sb)
                    if rr2:
                        options.append((sb, rr2, sb["setup"]))
                        tested.append(sb)
                s["_options"] = options
                s["comp"] = analysis.composite_score(
                    s["rr"], tech=tech, rs=rs, regime_score=regime["score"])
    # Multiple-testing correction: the more setups we backtested this scan, the
    # stricter the t-stat a single row must clear to be called an edge.
    n_tests = max(1, len(tested))
    for s in scored:
        s["n_tests"] = n_tests
        # Pick the best option for this candidate: qualifying first, then Sharpe.
        opts = s.pop("_options", [])
        best = None
        for bt, rr, name in opts:
            q = analysis.qualifies_family(bt, n_tests)
            key = (not q, -(bt["edge"] if bt else -9), -(bt["exp_ret"] if bt else -9))
            if best is None or key < best[0]:
                best = (key, bt, rr, name)
        if best:
            _, bt, rr, name = best
            s["rr"] = rr
            s["bt"] = bt
            s["setup"] = name
            s["sharpe"] = bt["edge"] if bt else None
            s["exp_ret"] = bt["exp_ret"] if bt else None
            s["sd"] = bt["sd"] if bt else None
            s["p_win"] = bt["p_win"] if bt else None
            s["tstat"] = bt["tstat"] if bt else None
            s["oos_exp"] = bt.get("oos_exp_ret") if bt else None
            s["oos_sharpe"] = bt.get("oos_edge") if bt else None
            # recompute composite for the chosen setup's direction/geometry
            s["comp"] = analysis.composite_score(
                rr, tech=s.get("tech"), rs=s.get("rs"), regime_score=regime["score"])
        s["qualifies"] = analysis.qualifies_family(s.get("bt"), n_tests)
    # Rank by the objective: qualifying first, then biggest per-trade Sharpe,
    # then highest expected return. Rows with no expectancy estimate sink.
    scored.sort(key=lambda x: (
        not x.get("qualifies", False),
        -(x.get("sharpe") if x.get("sharpe") is not None else -9),
        -(x.get("exp_ret") if x.get("exp_ret") is not None else -9)))
    return scored

# ---------------------------------------------------------------- news enrichment
def select_display_rows(scored, below_limit=10, require_open=True, now=None):
    """Which rows the table will actually print: fully-qualifying rows, plus the
    best positive-expectancy near-misses. Near-misses are ranked OOS-positive
    first, then by a gentle fresh-catalyst tiebreaker (news aligned with the
    trade side), then by in-sample Sharpe.

    THE TRADING RULE: by default (require_open=True) we ONLY surface rows whose
    market is open/just-closed with a fresh quote -- a stale price (e.g. Friday's
    US close shown on Sunday) is not actionable and must never appear as an
    opportunity. Pass require_open=False only for diagnostics/research.
    """
    pool = [s for s in scored if (not require_open) or is_tradeable_now(s, now)]
    passing = [s for s in pool if s.get("qualifies")]
    below = [s for s in pool
             if not s.get("qualifies")
             and s.get("exp_ret") is not None and s.get("exp_ret") > 0
             and s["rr"]["risk"] <= 0.20]
    below.sort(key=lambda x: (
        (x.get("oos_sharpe") or -9) <= 0,
        -(x.get("oos_sharpe") if x.get("oos_sharpe") is not None else -9),
        -(x.get("news_align") or 0),
        -(x.get("sharpe") if x.get("sharpe") is not None else -9)))
    return passing, below[:below_limit]

def _news_alignment(s):
    """+1 if news sentiment agrees with the trade side, -1 if it contradicts,
    0 if neutral/unknown. Used only as a gentle tiebreaker among near-misses --
    never to override the statistical (Sharpe/t/OOS) ranking."""
    n = s.get("news")
    if not n or n.get("net") is None:
        return 0
    return n["net"] if s["rr"]["side"] == "Long" else -n["net"]

def enrich_with_news(scored, days=7, enrich_n=14, sentiment_budget=4):
    """Attach per-candidate company news to the rows the table will display.

    The wide funnel surfaces dynamic tickers the 26 curated RSS feeds can't
    cover, so we fetch news PER candidate:
      - Finnhub company-news (60/min) for every displayed row -> headline flow,
        recency, source breadth (parallel; fast).
      - Polygon per-ticker SENTIMENT (5/min) for the top few rows only -> a
        positive/negative read with reasoning (sequential, budgeted, 429-safe).
    Sets s['news'] (dict) and s['news_align'] (gentle tiebreaker). Returns scored.
    """
    passing, below = select_display_rows(scored)
    targets, ids = [], set()
    # Company-news APIs (Finnhub/Polygon) are EQUITY-only: a bare crypto symbol
    # like SOL collides with an unrelated stock (SOL = Emeren Group), and FX
    # pairs ("EUR/USD") aren't companies. So per-ticker news only applies to US
    # equities -- which is exactly where the wide funnel's dynamic tickers live.
    # Crypto/FX get their context from the dedicated RSS/GDELT --news section.
    for s in passing + below[:enrich_n]:
        if inst.market_of(s["sym"]) == "US" and id(s) not in ids:
            targets.append(s); ids.add(id(s))
    if not targets:
        return scored

    def fh(s):
        n, _ = news.finnhub_company_news(s["sym"], days=days)
        return s, (n or {})
    with ThreadPoolExecutor(max_workers=8) as p:
        for s, n in p.map(fh, targets):
            s["news"] = {"count": n.get("count", 0), "latest": n.get("latest"),
                         "latest_ts": n.get("latest_ts"),
                         "sources": n.get("sources", 0),
                         "headlines": n.get("headlines", []),
                         "net": None, "pos": 0, "neg": 0, "reasoning": None,
                         "src": "finnhub" if n else None}
    # Polygon sentiment for the most important rows only (passing first), within
    # the 5/min budget. Sequential + 429-tolerant so a spent budget degrades to
    # "headlines only" rather than erroring.
    budget = sentiment_budget
    for s in targets:
        if budget <= 0:
            break
        pg, _ = news.polygon_ticker_sentiment(s["sym"])
        if pg and (pg.get("net") is not None or pg.get("count")):
            nd = s.setdefault("news", {})
            nd["net"], nd["pos"], nd["neg"] = pg.get("net"), pg.get("pos", 0), pg.get("neg", 0)
            nd["reasoning"] = pg.get("reasoning")
            nd["src"] = (nd.get("src") + "+polygon") if nd.get("src") else "polygon"
            if not nd.get("latest") and pg.get("latest"):
                nd["latest"] = pg["latest"]
        budget -= 1
    for s in targets:
        s["news_align"] = _news_alignment(s)
    return scored

def enrich_with_catalysts(scored, days=14, enrich_n=40):
    """Attach the nearest upcoming catalyst (earnings/FDA/IPO/dividend) to each
    of the top `enrich_n` candidates, and apply a small composite-score boost
    for rows with a catalyst inside `days`. Mutates and returns `scored`.

    Why this matters: a dated catalyst gives a short-term trade a *defined
    exit window* (close before the event, or ride through it with a stop).
    That converts an open-ended risk into a bounded one -- exactly the shape
    our objective rewards. The boost is small and capped so a catalyst never
    overrides the statistical (Sharpe/t/OOS) ranking; it only breaks ties
    among near-misses and reframes the trade plan."""
    if not scored:
        return scored
    import datetime as _dt
    targets = [s for s in scored[:enrich_n] if s.get("sym")]
    syms = [s["sym"] for s in targets]
    cal = catalysts.for_symbols(syms, days=days)
    by_sym = {}
    for c in cal:
        # keep nearest catalyst per sym
        s_key = (c.get("sym") or "").upper()
        if s_key and (s_key not in by_sym or c["date"] < by_sym[s_key]["date"]):
            by_sym[s_key] = c
    today = _dt.date.today()
    for s in targets:
        c = by_sym.get(str(s["sym"]).upper())
        if not c:
            continue
        s["catalyst"] = c
        try:
            d_cat = _dt.date.fromisoformat(c["date"])
            s["catalyst_days"] = (d_cat - today).days
        except (ValueError, TypeError):
            s["catalyst_days"] = None
        # apply composite boost (kind-weighted: ERN/FDA > DIV)
        if s.get("catalyst_days") is not None and 0 <= s["catalyst_days"] <= days:
            kind = c.get("kind", "")
            base = 5.0 if kind in ("earnings", "fda") else 2.0
            boost = base * max(0.0, 1.0 - (s["catalyst_days"] / max(1, days)))
            s["comp"] = round((s.get("comp") or 0) + boost, 1)
    return scored

# ---------------------------------------------------------------- printing
def _tech_brief(s):
    """Compact technical read for the table: winning setup + RSI + trend."""
    t = s.get("tech")
    bits = []
    setup = s.get("setup")
    if setup:                       # the specific strategy that has the edge
        bits.append(f"[{setup}]")
    if not t:
        return " ".join(bits) or "--"
    r = t.get("rsi14")
    if r is not None:
        tag = "os" if r < 35 else "ob" if r > 65 else ""
        bits.append(f"RSI{r:.0f}{tag}")
    last, s20, s50 = t.get("last"), t.get("sma20"), t.get("sma50")
    if last and s20 and s50:
        trend = "up" if last > s20 > s50 else "dn" if last < s20 < s50 else "mix"
        bits.append(trend)
    rs = s.get("rs")
    if rs is not None:
        bits.append(f"RS{rs:+.0f}")
    return " ".join(bits) or "--"

def _news_brief(s):
    """Compact news read for the table: sentiment glyph + article count + age of
    the latest headline. '+ n12 2h' (bullish, 12 articles, 2h old), '- n5 1d',
    '= n8' (mixed), '. n0' (quiet), '--' (not enriched)."""
    n = s.get("news")
    if not n:
        return "--"
    net = n.get("net")
    glyph = "+" if net == 1 else "-" if net == -1 else "=" if net == 0 else "."
    cnt = n.get("count") or 0
    age = ""
    ts = n.get("latest_ts")
    if ts:
        import time
        h = (time.time() - ts) / 3600
        age = f"{h:.0f}h" if h < 48 else f"{h/24:.0f}d"
    return f"{glyph} n{cnt}" + (f" {age}" if age else "")

def _px(v):
    """Adaptive price format: enough decimals for the magnitude, no clutter."""
    if v is None:
        return "--"
    a = abs(v)
    d = 2 if a >= 100 else 3 if a >= 1 else 5 if a >= 0.01 else 8
    return f"{v:.{d}f}"

def _short_et(ts):
    """'MM-DD HH:MM' from a quote ts (compact vs the full ET string)."""
    e = core.est_time(ts)          # 'YYYY-MM-DD HH:MM ET' or ''
    return e[5:16] if len(e) >= 16 else "--"

def _clip(s, n):
    s = str(s)
    return s if len(s) <= n else s[:n-1].rstrip() + "\u2026"

def print_opportunity_table(scored):
    """Print the ranked opportunities as two clean, bordered, row-numbered
    tables -- a PLAN table (what to do) and an EVIDENCE table (is the edge real,
    how risky) -- keyed by the same '#'. Fixed-grid and narrow, so nothing wraps
    and a stop can never be misread against the wrong instrument.
    """
    passing, below = select_display_rows(scored)
    rows = passing + below
    n_pass = len(passing)

    print("\n=== OPPORTUNITIES (ranked by per-trade expected Sharpe = E[R]/sigma) ===")
    opens = markets.open_markets()
    print(f"  markets open now ({core.now_iso()}): "
          f"{', '.join(sorted(opens)) if opens else 'NONE'}")
    print(f"  YOUR BAR to qualify: E[R]>=+{analysis.EXP_MIN*100:.0f}%/trade, "
          f"sigma<={analysis.SD_MAX*100:.0f}%, Sharpe>={analysis.SHARPE_MIN:.2f}, "
          f"n>={analysis.MIN_SAMPLE}, t>={analysis.TSTAT_MIN:.0f} (Bonferroni-adj.), OOS Sharpe>0")

    if not rows:
        if not opens:
            print("  >> ALL TRACKED MARKETS CLOSED -- no actionable trade. "
                  "Crypto is 24/7; FX/US/Asia resume next open.")
        elif opens == {"CRYPTO"}:
            print("  >> only CRYPTO open and no positive-expectancy crypto edge measured "
                  "-- stand aside.")
        else:
            print(f"  >> markets open ({', '.join(sorted(opens))}) but no positive-expectancy "
                  "edge measured this scan -- stand aside. An empty table is the honest answer.")
        return

    if n_pass == 0:
        print("  >> NOTHING cleared your bar this scan. The rows below are the best")
        print("     MEASURED edges only -- they are NOT signals. DO NOT trade them.")
    else:
        print(f"  >> {n_pass} candidate(s) CLEARED your bar (#1-#{n_pass}). "
              f"Rows below #{n_pass} are near-misses -- NOT actionable.")

    # ---- Table 1: the trade plan ----
    plan_hdr = ["#", "Instrument", "Sym", "Mkt", "Dir", "Setup",
                "Price", "Quote(ET)", "Chg%", "Entry", "Stop", "Target", "R:R", "Risk%",
                "Catalyst"]
    plan_al = ["right", "left", "left", "left", "left", "left",
               "right", "left", "right", "right", "right", "right", "right", "right",
               "left"]
    plan_rows = []
    for i, s in enumerate(rows, 1):
        rr = s["rr"]
        # catalyst cell: "ERN 5d" / "FDA 12d" / "DIV 3d" / blank
        cat_cell = ""
        c = s.get("catalyst")
        if c and s.get("catalyst_days") is not None:
            tag = {"earnings": "ERN", "fda": "FDA", "ipo": "IPO",
                   "dividend": "DIV"}.get(c.get("kind", ""), c.get("kind", "")[:3].upper())
            cat_cell = f"{tag} {s['catalyst_days']}d"
        plan_rows.append([
            f"{i}", _clip(s["label"], 22), s["sym"], inst.market_of(s["sym"]),
            rr["side"], s.get("setup") or "range",
            _px(s.get("price")), _short_et(s.get("ts")), _fmt(s.get("dp"), "%", 1),
            _px(rr["entry"]), _px(rr["stop"]), _px(rr["target"]),
            f"{rr['rr']:.1f}", _fmt(rr["risk"]*100, "%", 2),
            cat_cell])
    print("\n-- TRADE PLAN --")
    print(core.table(plan_hdr, plan_rows, plan_al))

    # ---- Table 2: the evidence (same # key) ----
    ev_hdr = ["#", "Sym", "Verdict", "E[R]%", "sigma%", "Sharpe", "t", "oosS",
              "Win%", "n", "ATR%", "Kelly%", "Data"]
    ev_al = ["right", "left", "left", "right", "right", "right", "right",
             "right", "right", "right", "right", "right", "left"]
    ev_rows = []
    for i, s in enumerate(rows, 1):
        pct = lambda v, d=2: _fmt(v*100 if v is not None else None, "%", d)
        ev_rows.append([
            f"{i}", s["sym"], "PASS" if s.get("qualifies") else "below",
            pct(s.get("exp_ret")), pct(s.get("sd")),
            _fmt(s.get("sharpe"), "", 2), _fmt(s.get("tstat"), "", 1),
            _fmt(s.get("oos_sharpe"), "", 2),
            _fmt(s.get("p_win")*100 if s.get("p_win") is not None else None, "%", 0),
            str(s.get("bt", {}).get("n", "--")) if s.get("bt") else "--",
            _fmt(_atr_pct(s), "%", 1), _fmt(_kelly_pct(s), "%", 1), s["fresh"]])
    print("\n-- EDGE & RISK (evidence for the SAME numbered rows) --")
    print(core.table(ev_hdr, ev_rows, ev_al))

    no_bt = sum(1 for s in scored if s.get("sharpe") is None)
    if no_bt:
        print(f"  note: {no_bt} live instruments have no free daily history "
              "(China A-share/Taiwan) -> no expectancy, excluded from ranking.")

# ---------------------------------------------------------------- live watch mode
def refresh_prices(rows, workers=12):
    """Re-pull a FRESH live quote for each already-selected row and recompute its
    trade geometry off the new price. The edge stats (E[R], sigma, Sharpe, t, the
    chosen setup, side and risk fraction) come from the one-time backtest and do
    NOT change tick-to-tick -- only price does -- so a live refresh is cheap: one
    quote call per displayed instrument, then re-derive entry/stop/target.

    Mutates each row in place (price, dp, ts, fresh, live, rr geometry) and
    returns rows. This is the hot loop behind `watch`."""
    def one(s):
        q, err = sources.requote(s["sym"])
        return s, q
    with ThreadPoolExecutor(max_workers=workers) as p:
        results = list(p.map(one, rows))
    for s, q in results:
        if not q or q.get("c") is None:
            # keep the last-known price but mark it stale via freshness()
            continue
        price = q.get("c")
        s["price"] = price
        s["dp"] = q.get("dp")
        s["ts"] = q.get("ts")
        age, flag = core.freshness(q.get("ts"))
        s["fresh"] = flag
        s["live"] = age is not None and age <= core.MAX_STALE_S
        # recompute the concrete plan off the fresh price, keeping the backtested
        # setup's side / risk / reward-multiple fixed.
        rr = s.get("rr") or {}
        risk = rr.get("risk")
        side = rr.get("side")
        rrm = rr.get("rr")
        if risk and side and rrm:
            reward = rrm * risk
            if side == "Long":
                stop, tgt = price * (1 - risk), price * (1 + reward)
            else:
                stop, tgt = price * (1 + risk), price * (1 - reward)
            rr = dict(rr)
            rr.update({"entry": price, "stop": stop, "target": tgt, "reward": reward})
            s["rr"] = rr
    return rows

def watch(scored, interval=20, iterations=None):
    """REAL-TIME opportunity monitor. Runs the heavy scan/backtest ONCE (already
    done -> `scored`), then loops: every `interval`s it re-quotes just the
    displayed rows, recomputes their live entry/stop/target, and repaints the
    table in place with a live clock. Ctrl-C to stop.

    `iterations` caps the number of repaints (None = run until interrupted).
    This is what makes the table a live tape rather than a frozen snapshot."""
    # Lock in the selection from the one-time backtest so we're not re-ranking on
    # noisy intraday ticks -- we monitor the SAME candidates, just at live prices.
    rows = select_display_rows(scored)[0] + select_display_rows(scored)[1]
    if not rows:
        print("\n-- LIVE WATCH -- no actionable rows to monitor "
              "(no open market with a measured edge). Nothing to stream.")
        return
    i = 0
    try:
        while iterations is None or i < iterations:
            refresh_prices(rows)
            # repaint: clear screen, print header + the two tables from live rows.
            sys = __import__("sys")
            sys.stdout.write("\x1b[2J\x1b[H")   # clear + home
            print(f"=== WORLD-TRADER LIVE WATCH  {core.now_iso()} "
                  f"(refresh {interval}s, Ctrl-C to stop) ===")
            opens = markets.open_markets()
            print(f"  markets open now: {', '.join(sorted(opens)) if opens else 'NONE'}"
                  f"   monitoring {len(rows)} candidate(s)")
            _print_watch_tables(rows)
            print("\nresearch only, not financial advice. prices refresh live above.")
            i += 1
            if iterations is not None and i >= iterations:
                break
            __import__("time").sleep(interval)
    except KeyboardInterrupt:
        print("\n-- live watch stopped --")
    return rows

def _print_watch_tables(rows):
    """Render the PLAN + EDGE tables for an already-selected, freshly-requoted set
    of rows (shared by watch())."""
    plan_hdr = ["#", "Instrument", "Sym", "Mkt", "Dir", "Setup",
                "Price", "Quote(ET)", "Chg%", "Entry", "Stop", "Target", "R:R", "Risk%"]
    plan_al = ["right", "left", "left", "left", "left", "left",
               "right", "left", "right", "right", "right", "right", "right", "right"]
    plan_rows = []
    for i, s in enumerate(rows, 1):
        rr = s["rr"]
        live = "*" if s.get("live") else " "
        plan_rows.append([
            f"{i}", _clip(s["label"], 22), s["sym"], inst.market_of(s["sym"]),
            rr["side"], s.get("setup") or "range",
            _px(s.get("price")), _short_et(s.get("ts")) + live, _fmt(s.get("dp"), "%", 1),
            _px(rr["entry"]), _px(rr["stop"]), _px(rr["target"]),
            f"{rr['rr']:.1f}", _fmt(rr["risk"]*100, "%", 2)])
    print("\n-- TRADE PLAN (live) --")
    print(core.table(plan_hdr, plan_rows, plan_al))
    ev_hdr = ["#", "Sym", "Verdict", "E[R]%", "sigma%", "Sharpe", "t", "oosS",
              "Win%", "n", "ATR%", "Kelly%", "Data"]
    ev_al = ["right", "left", "left", "right", "right", "right", "right",
             "right", "right", "right", "right", "right", "left"]
    ev_rows = []
    for i, s in enumerate(rows, 1):
        pct = lambda v, d=2: _fmt(v*100 if v is not None else None, "%", d)
        ev_rows.append([
            f"{i}", s["sym"], "PASS" if s.get("qualifies") else "below",
            pct(s.get("exp_ret")), pct(s.get("sd")),
            _fmt(s.get("sharpe"), "", 2), _fmt(s.get("tstat"), "", 1),
            _fmt(s.get("oos_sharpe"), "", 2),
            _fmt(s.get("p_win")*100 if s.get("p_win") is not None else None, "%", 0),
            str(s.get("bt", {}).get("n", "--")) if s.get("bt") else "--",
            _fmt(_atr_pct(s), "%", 1), _fmt(_kelly_pct(s), "%", 1), s["fresh"]])
    print("\n-- EDGE & RISK (from one-time backtest; * = live tick) --")
    print(core.table(ev_hdr, ev_rows, ev_al))

def _fmt(v, suffix="", dec=2):
    return (f"{v:.{dec}f}{suffix}") if v is not None else "--"

def _atr_pct(s):
    """Daily ATR(14) as % of price -> the instrument's typical volatility."""
    t = s.get("tech")
    px = s.get("price")
    if not t or not px:
        return None
    a = t.get("atr14")
    return (a / px * 100) if a else None

def _kelly_pct(s):
    """Kelly optimal stake % (negative -> no edge, skip)."""
    bt = s.get("bt")
    if not bt:
        return None
    k = analysis.kelly_fraction(bt.get("p_win"), s["rr"]["rr"])
    return (k * 100) if k is not None else None


def print_catalysts(scored, limit=10):
    """Print the freshest company news (the 'relevant news for them') for the
    top candidates the table displayed -- the actual headline + age + source +,
    where available, a sentiment reason. This is the readable catalyst the
    compact News column can't fit, sourced so the user can verify.
    """
    import time
    def _clip(s, n):
        s = str(s)
        return s if len(s) <= n else s[:n].rstrip() + "\u2026"
    passing, below = select_display_rows(scored)
    rows = passing + below
    shown = [s for s in rows if s.get("news") and s["news"].get("latest")]
    if not shown:
        return
    print("\n-- CATALYSTS (latest company news for top candidates; verify before acting) --")
    for s in shown[:limit]:
        n = s["news"]
        tag = {1: "[+]", -1: "[-]", 0: "[=]"}.get(n.get("net"), "   ")
        side = s["rr"]["side"]
        print(f"  {core.pad(s['sym'], 7)} {core.pad(side, 5)} {tag}  {_clip(n['latest'], 104)}")
        meta = []
        ts = n.get("latest_ts")
        if ts:
            h = (time.time() - ts) / 3600
            meta.append(f"{h:.0f}h ago" if h < 48 else f"{h/24:.0f}d ago")
        if n.get("sources"):
            meta.append(f"{n['sources']} src")
        if n.get("count"):
            meta.append(f"{n['count']} articles/7d")
        if meta:
            print(f"          ({'  '.join(meta)})")
        if n.get("reasoning"):
            print(f"          why: {_clip(n['reasoning'], 112)}")
