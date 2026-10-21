#!/usr/bin/env python3
"""world-trader: one-command global market opportunity scan.

Surfaces short-term, defined-risk, high reward:risk trade ideas across crypto,
US equities/ETFs, China A-shares (live), Taiwan (live), with macro regime,
expanded news, and alternative data. Stdlib only.

Usage:
  python3 tools/scan.py                 # full scan (regime + quotes + opps)
  python3 tools/scan.py --watch         # LIVE: scan once, then stream a real-time
                                        #       opportunity table (prices refresh)
  python3 tools/scan.py --watch --interval 15   # set refresh seconds (default 20)
  python3 tools/scan.py --news          # also print expanded news headlines
  python3 tools/scan.py --altdata       # also print FRED/COT/funding/curve
  python3 tools/scan.py --full          # everything
  python3 tools/scan.py --quiet         # opportunity table only
  python3 tools/scan.py --no-news-enrich # skip per-candidate news + CATALYSTS
  python3 tools/scan.py --no-options    # skip CBOE straddle / RV-IV edge
  python3 tools/scan.py --no-llm        # skip LLM news-sentiment tiebreaker
  python3 tools/scan.py --doctor        # self-check: keys + every source + modules
  python3 tools/scan.py --no-fred       # skip FRED (regime degrades gracefully)

Run from the repo root so it can find tools/wt and .env.local.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from wt import core, sources, analysis, altdata, news, report
from wt import instruments as inst

def doctor():
    """Self-check: verify keys, modules, and every live source. So you can
    start this like software and immediately see nothing is lost/broken."""
    print(f"=== WORLD-TRADER DOCTOR  {core.now_iso()} ===")
    ok = lambda b: "OK  " if b else "FAIL"
    # 1. API keys present (never print values)
    print("\n[keys] (.env.local)")
    for name in ("ALPHAVANTAGE_KEY", "FINNHUB_KEY", "TWELVEDATA_KEY",
                 "FRED_KEY", "POLYGON_KEY"):
        print(f"  {ok(bool(core.api_key(name)))}  {name}")
    # 2. Modules import
    print("\n[modules]")
    for m in ("core", "markets", "instruments", "sources", "news", "altdata", "analysis", "report"):
        print(f"  OK    wt.{m}")
    # 2b. Market sessions -- which markets are OPEN right now (the actionability gate)
    print("\n[market sessions] (only OPEN markets can produce actionable trades)")
    from wt import markets as _mk
    for m in ("CRYPTO", "FX", "US", "CN-A", "TW", "HK"):
        st = _mk.market_status(m)
        print(f"  {'OPEN' if st['open'] else 'shut'}  {m:7} {st['label']}")
    # 3. Live source probes
    print("\n[live sources]")
    probes = [
        ("crypto (Binance/Coinbase/Kraken)", lambda: sources.crypto_quote("BTC")),
        ("US RT (Nasdaq)",                   lambda: sources.nasdaq_quote("SPY")),
        ("China A-share (Sina)",             lambda: sources.sina_quote("sh600519")),
        ("China A-share (Tencent)",          lambda: sources.tencent_quote("sh600519")),
        ("Taiwan (TWSE)",                    lambda: sources.twse_quote("2330")),
        ("history (Nasdaq)",                 lambda: sources.nasdaq_history("AAPL", 60)),
        ("WIDE US market (Polygon bulk)",    lambda: (lambda g,e: ({"c": len(g["rows"])} if g else None, e))(*sources.polygon_grouped_daily())),
        ("WIDE CN A-share list (Sina bulk)",  lambda: (lambda r,e: ({"c": len(r)} if r else None, e))(*sources.sina_ashare_list(pages=1, num=40))),
        ("CN A-share history (Sina/Tencent)", lambda: sources.cn_history("sh600519", 60)),
        ("Hong Kong RT (Sina rt_hk)",         lambda: sources.hk_quote("00700.HK")),
        ("Hong Kong history (Tencent)",       lambda: sources.hk_history("00700.HK", 60)),
        ("FX RT+history (TwelveData)",       lambda: sources.twelvedata_quote("EUR/USD")),
        ("Finnhub",                          lambda: sources.finnhub_quote("AAPL")),
    ]
    for label, fn in probes:
        try:
            q, err = fn()
            print(f"  {ok(bool(q))}  {label}" + (f"  ({err})" if err else ""))
        except Exception as e:
            print(f"  FAIL  {label}  ({core.describe_err(e)})")
    # 4. Alt-data probes
    print("\n[alt-data]")
    alt = [("FRED VIX", lambda: altdata.fred_latest("VIXCLS")[0]),
           ("Treasury curve", lambda: altdata.treasury_curve()[0]),
           ("CFTC COT", lambda: altdata.cot_summary()[0]),
           ("crypto fear&greed", lambda: altdata.crypto_fear_greed()[0]),
           ("BTC funding/OI", lambda: altdata.crypto_funding("BTC")[0])]
    for label, fn in alt:
        try:
            print(f"  {ok(bool(fn()))}  {label}")
        except Exception as e:
            print(f"  FAIL  {label}  ({core.describe_err(e)})")
    # 5. News probe
    print("\n[news]")
    feeds = news.fetch_all()
    live = sum(1 for _, items, _ in feeds if items)
    print(f"  {ok(live > 0)}  RSS feeds: {live}/{len(feeds)} returning items")
    # per-ticker company news (powers the wide-candidate CATALYSTS section)
    try:
        tn = news.ticker_news("AAPL", want_sentiment=True)
        has = bool(tn.get("count")) or tn.get("net") is not None
        detail = f"{tn.get('count',0)} headlines/7d, sentiment={tn.get('net')}, src={tn.get('src')}"
        print(f"  {ok(has)}  per-ticker news (Finnhub+Polygon)  ({detail})")
    except Exception as e:
        print(f"  FAIL  per-ticker news  ({core.describe_err(e)})")
    # 6. Options probe (CBOE delayed chain -- the new RV/IV edge source)
    print("\n[options]")
    try:
        from wt import options as _opt
        st, err = _opt.straddle("AAPL", max_dte=45)
        if st:
            iv = st.get("iv_call") or st.get("iv_put") or 0
            oi = int((st.get("call_oi") or 0) + (st.get("put_oi") or 0))
            detail = (f"AAPL ATM straddle: dte={st.get('dte')} "
                      f"cost%={st.get('cost_pct'):.2f} iv={iv:.3f} oi={oi}")
            print(f"  OK    CBOE delayed chain  ({detail})")
        else:
            print(f"  FAIL  CBOE delayed chain  ({err})")
    except Exception as e:
        print(f"  FAIL  CBOE delayed chain  ({core.describe_err(e)})")
    # 7. LLM probe (xAI Grok / Anthropic -- the news-sentiment tiebreaker)
    print("\n[llm]")
    try:
        from wt import llm as _llm
        p = _llm.available_provider()
        if p:
            key_name = ("XAI_API_KEY" if p == "xai" else "ANTHROPIC_API_KEY")
            print(f"  OK    LLM provider: {p}  ({key_name} set)")
            # Live probe (1 call, ~2s) -- skip on --no-llm.
            if "--no-llm" not in sys.argv:
                sent = _llm.news_sentiment("AAPL", [
                    "Apple beats Q3 earnings estimates, raises guidance",
                    "iPhone 17 pre-orders exceed expectations"])
                if sent:
                    print(f"  OK    LLM sentiment probe  "
                          f"(bias={sent['bias']} conf={sent['confidence']:.2f} "
                          f"provider={sent.get('provider')})")
                else:
                    print(f"  WARN  LLM sentiment probe  (provider auth failed or "
                          f"returned empty -- check {key_name})")
        else:
            print("  SKIP  LLM provider: none  (set XAI_API_KEY or ANTHROPIC_API_KEY "
                  "in .env.local to enable the news-sentiment tiebreaker)")
    except Exception as e:
        print(f"  FAIL  LLM  ({core.describe_err(e)})")
    print("\ndoctor complete. Run `python3 tools/scan.py` for the full scan.")
    return 0

_TASK_LOG = []
def _log(msg):
    """Append a small task entry for the end-of-scan task log."""
    import datetime as _dt
    _TASK_LOG.append(f"{_dt.datetime.now().strftime('%H:%M:%S')}  {msg}")

def main():
    a = sys.argv[1:]
    if "--doctor" in a or "doctor" in a:
        return doctor()
    if "--help" in a or "-h" in a:
        print(__doc__)
        return 0
    # News + alt-data are NOT optional. Opportunities are rare; missing one
    # because a flag was off is unacceptable. `--full` is the default.
    # (Flags still honored for backwards compat, but no longer required.)
    full = True
    show_news = True
    show_alt = True
    # Allow explicit opt-out only via dedicated flags.
    if "--no-news" in a:
        show_news = False
    if "--no-altdata" in a:
        show_alt = False
    quiet = "--quiet" in a
    use_fred = "--no-fred" not in a
    watch = "--watch" in a
    interval = 20
    if "--interval" in a:
        try: interval = max(5, int(a[a.index("--interval") + 1]))
        except (IndexError, ValueError): pass

    print(f"=== WORLD-TRADER GLOBAL SCAN  {core.now_iso()} ===")
    print("objective: short-term trades with HIGH expected return and LOW sigma "
          "-> maximize per-trade expected Sharpe (E[R]/sigma), risk hard-capped")

    # 1. Regime
    _log("regime: gathering FRED macro / VIX / fear-greed")
    regime, fred_rows, fg, macro = report.gather_regime(use_fred)
    _log(f"regime: {regime['label']} score={regime['score']:+.2f}")
    vix = macro.get("VIXCLS")
    if not quiet:
        print(f"\n-- REGIME: {regime['label']}  (score {regime['score']:+.2f}) --")
        bits = "  ".join(f"{n}={v}({s:+.2f})" for n, v, s in regime["parts"])
        if bits: print("   " + bits)
        if fg: print(f"   crypto fear&greed: {fg['value']} ({fg['label']})")

    # 2. Quotes -- curated core universe (crypto/US-core/China/Taiwan/FX) ...
    _log("quotes: collecting curated universe (crypto/US-core/CN/TW/FX)")
    quotes = report.collect_quotes()
    _log(f"quotes: {len(quotes)} curated instruments fetched")
    # ... PLUS the WIDE funnel: pull the whole US market (~12k tickers) in one
    # Polygon call, pre-screen to the most promising names, and feed them into
    # the same backtest pipeline. `--narrow` disables this for the legacy scan.
    wide_meta = None
    cn_meta = None
    if "--narrow" not in a:
        _log("wide US funnel: pulling ~12k tickers from Polygon, pre-screening top 150")
        wide_quotes, wide_meta = report.collect_wide_us(top_n=150)
        _log(f"wide US funnel: {wide_meta.get('screened','?')} of "
             f"{wide_meta.get('universe','?')} -> top 150 backtested"
             + (f" [err: {wide_meta['err']}]" if wide_meta.get('err') else ""))
        # de-dupe vs curated names already present
        have = {sym for _, sym, _, _ in quotes}
        quotes += [t for t in wide_quotes if t[1] not in have]
        # ... AND the China A-share wide funnel: the whole ~5,500-name A-share
        # market, most-liquid-first, pre-screened and fed to the SAME backtest.
        _log("wide CN funnel: pulling ~5,500 A-shares, pre-screening top 120")
        cn_quotes, cn_meta = report.collect_wide_cn(top_n=120)
        _log(f"wide CN funnel: {cn_meta.get('screened','?')} of "
             f"{cn_meta.get('universe','?')} -> top 120 backtested"
             + (f" [err: {cn_meta['err']}]" if cn_meta.get('err') else ""))
        have = {sym for _, sym, _, _ in quotes}
        quotes += [t for t in cn_quotes if t[1] not in have]
    if not quiet:
        extra = ""
        if wide_meta and not wide_meta.get("err"):
            extra = (f"  [+wide US: {wide_meta['screened']} of "
                     f"{wide_meta['universe']} tickers pre-screened -> top 150]")
        elif wide_meta and wide_meta.get("err"):
            extra = f"  [wide US unavailable: {wide_meta['err']}]"
        if cn_meta and not cn_meta.get("err"):
            extra += (f"  [+wide CN A-share: {cn_meta['screened']} of "
                      f"{cn_meta['universe']} liquid names -> top 120, backtested]")
        elif cn_meta and cn_meta.get("err"):
            extra += f"  [wide CN unavailable: {cn_meta['err']}]"
        print(f"\n-- LIVE QUOTES: {len(quotes)} instruments fetched "
              f"(crypto RT, US, China A-share live, Taiwan live, FX){extra} --")

    # 3. Opportunities
    _log("opportunities: building candidate set from quotes + regime")
    scored, proxy_notes = report.build_opportunities(quotes, regime, vix=vix)
    _log(f"opportunities: {len(scored)} raw candidates")
    # 3b. Backtest expectancy (E[R], sigma, per-trade Sharpe) + technicals.
    #     This is the core of the objective: rank by expected Sharpe, low sigma.
    if "--fast" not in a:
        _log("backtest: enriching with technicals + E[R]/sigma/Sharpe")
        scored = report.enrich_with_technicals(scored, regime, vix=vix)
        # Surface the multiple-testing family size so the bar is transparent.
        fams = [s.get("n_tests", 0) for s in scored if s.get("n_tests")]
        gfams = [s.get("n_tests_global", 0) for s in scored if s.get("n_tests_global")]
        if fams:
            _log(f"backtest: per-candidate family m={max(fams)} "
                 f"(global total={max(gfams) if gfams else 0}) "
                 f"-> Bonferroni t>={analysis._bonferroni_t(max(fams)):.2f}")
        # 3c. Per-candidate NEWS for the rows we'll display: Finnhub headline
        #     flow + Polygon sentiment on the top few. The wide funnel surfaces
        #     dynamic tickers the curated RSS feeds can't cover, so we fetch
        #     company news per opportunity (disable with --no-news-enrich).
        if "--no-news-enrich" not in a:
            _log("news enrichment: Finnhub headlines + Polygon sentiment per candidate")
            scored = report.enrich_with_news(scored)
            _log(f"news enrichment: done ({sum(1 for s in scored if s.get('news') and s['news'].get('latest'))} candidates have fresh headlines)")
        # 3c-bis. Catalyst enrichment: attach nearest earnings/FDA/IPO/dividend
        # event to each top candidate, with a small composite-score boost.
        if "--no-catalysts" not in a:
            _log("catalyst enrichment: scanning Finnhub earnings/FDA/IPO + Polygon dividends")
            n_with = sum(1 for s in scored if s.get("catalyst"))
            scored = report.enrich_with_catalysts(scored)
            n_after = sum(1 for s in scored if s.get("catalyst"))
            _log(f"catalyst enrichment: {n_after} candidates have a near-term catalyst (+{n_after-n_with} new)")
        # 3c-ter. OPTIONS edge: pull ATM straddle (CBOE delayed) for top US
        # candidates and compute RV/IV -> the "cheap options" signal. This is
        # a structurally-independent (vol-regime) edge source, not a reskinned
        # price-momentum setup. Skip with --no-options.
        if "--no-options" not in a:
            _log("options enrichment: pulling ATM straddles (CBOE) for top US candidates")
            n_with = sum(1 for s in scored if s.get("opt"))
            scored = report.enrich_with_options(scored)
            n_after = sum(1 for s in scored if s.get("opt"))
            _log(f"options enrichment: {n_after} candidates have an RV/IV signal (+{n_after-n_with} new)")
    else:
        print("   (--fast: skipping expectancy backtest; rows show R:R only)")
    report.print_opportunity_table(scored)
    # Only show short-restricted proxy notes when those markets are actually
    # actionable (open or just-closed). Otherwise it's noise.
    from wt import markets as _mk
    _actionable = {m for m in ("CN-A", "TW", "HK") if _mk.is_actionable(m)}
    if proxy_notes and _actionable:
        print("\n-- SHORT-RESTRICTED MARKETS -> shortable proxy --")
        for n in proxy_notes[:8]:
            print(f"  * {n}")
    if "--fast" not in a and "--no-news-enrich" not in a:
        _log("catalysts: printing freshest company news for top candidates")
        report.print_catalysts(scored)

    # 3d. LIVE WATCH: the heavy scan/backtest above ran ONCE; now stream the
    #     selected opportunities at real-time prices, repainting in place.
    if watch:
        report.watch(scored, interval=interval)
        return 0

    # 4. Optional sections
    if show_alt:
        _log("alt-data: pulling FRED macro/rates/credit, treasury curve, BTC funding, COT")
        print("\n-- MACRO / RATES / CREDIT (FRED) --")
        for name, sid, v, date in fred_rows:
            if v: print(f"  {core.pad(name,26)} {v:>10}  ({date})")
        curve, err = altdata.treasury_curve()
        if curve:
            print("  UST curve: " + "  ".join(f"{k} {v:.2f}%" for k, v in curve.items()))
        fund, _ = altdata.crypto_funding("BTC")
        if fund:
            print(f"  BTC perp funding: {fund.get('funding_rate',0):+.4f}%  "
                  f"OI {fund.get('open_interest',0):,.0f}")
        cot, _ = altdata.cot_summary()
        if cot:
            print("  CFTC COT large-spec net: " +
                  "  ".join(f"{k} {v['net']:+,.0f}" for k, v in cot.items()))

    # 5. CATALYST CALENDAR -- always on. Earnings/FDA/IPO/dividend events in
    #    the next 14 days. These are bounded-risk windows for short-term trades.
    if "--no-catalysts" not in a:
        _log("catalyst calendar: Finnhub earnings/FDA/IPO + Polygon dividends (14d)")
        from wt import catalysts as _cat
        _cat.print_calendar(days=14, limit=30)

    if show_news:
        _log("expanded news: sweeping all RSS feeds (equities/macro/CB/crypto/FX/commodities/regional)")
        print("\n-- NEWS (expanded feeds) --")
        n_feeds_ok = 0
        n_feeds_err = 0
        for name, items, err in news.fetch_all():
            if err:
                n_feeds_err += 1
                continue
            if not items:
                continue
            n_feeds_ok += 1
            print(f"  [{name}]")
            for it in items[:3]:
                print(f"    - {it['title']}")
        _log(f"expanded news: {n_feeds_ok} feeds ok, {n_feeds_err} feeds failed")
        _log("GDELT: 24h global market tone sweep")
        tone, _ = news.gdelt_tone("stock market crash OR rally")
        if tone:
            print(f"  GDELT market tone (24h): {tone['avg_tone']:+.2f} "
                  f"over {tone['articles']} articles")
            _log(f"GDELT: tone={tone['avg_tone']:+.2f} over {tone['articles']} articles")

    print("\nresearch only, not financial advice. verify before acting.")
    print("\n[scan task log]")
    for t in _TASK_LOG:
        print(f"  - {t}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
