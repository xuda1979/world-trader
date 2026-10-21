"""Peer / competitor map + theme detector for CROSS-ASSET SPILLOVER trades.

The intuition (user example): "a Chinese company just recycled a rocket, then
SpaceX's stock dropped." A catalyst on company A often moves company B through
competition, supply-chain, sector, or sentiment linkage -- even when B is never
named in the headline. The scanner's per-ticker news fetch can't see this,
because it queries by symbol.

This module provides:
  - PEERS:    hand-curated peer clusters for the most spillover-prone names
              (space, EV, semis, biotech, mega-cap tech, China ADRs, crypto ETFs)
  - THEMES:   keyword -> (watch_tickers, rationale) map. When a headline
              matches a theme keyword, the listed tickers become candidates
              for a directional bet (typically short the incumbent / long the
              disruptor, depending on the news tone).
  - peers_of(sym):  return peer tickers for a symbol (or []).
  - themes_for(headlines):  return theme matches in a list of headlines.
  - spillover_candidates(feed_items):  one-call: feed -> {ticker: [reasons]}.

This is a SIGNAL GENERATOR, not a strategy. The actual entry/stop/target still
flows through the backtested setups in analysis.py. Spillover candidates are
injected into the wide universe so the existing funnel can score them with
the same reward:risk + Sharpe/t/OOS gate every other candidate passes.

All data here is static and free (no API calls). It is a knowledge base that
makes the existing news feed actionable for thin-name spillovers.

Research only. Not financial advice.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# PEER CLUSTERS
# ---------------------------------------------------------------------------
# Each cluster is a set of tickers that tend to move together on the SAME
# catalyst. When news flags one member, the others become spillover candidates.
# Ticklish by design: we keep clusters TIGHT (3-8 names) so noise stays low.

PEERS = {
    # --- Space ---
    "SPACE": ["RKLB", "SPCE", "ASTR", "LMT", "NOC", "GD", "BA"],
    # SpaceX is private; the spillover on a SpaceX milestone is usually:
    #   - negative for pure-play listed competitors (RKLB, SPCE, ASTR)
    #   - mixed for primes (LMT/NOC/GD/BA) -- they have their own space programs
    # We expose the listed names; the news-tone decides direction.

    # --- EV / Tesla ecosystem ---
    "EV":    ["TSLA", "RIVN", "LCID", "NIO", "XPEV", "LI", "F", "GM",
              "STLA", "TM", "HMC", "BYD", "BYDDY"],
    # Battery / materials (spillover from EV demand news)
    "BATT":  ["LAC", "SQM", "ALB", "LTHM", "PLL", "ICHR", "BLDP", "PLUG",
              "FCEL", "BE"],
    # Charging (spillover from EV adoption news)
    "CHRG":  ["CHPT", "BLNK", "EVGO", "WBX", "CCJ"],

    # --- Semiconductors ---
    "SEMI":  ["NVDA", "AMD", "INTC", "TSM", "ASML", "MU", "QCOM", "AVGO",
              "TXN", "AMAT", "LRCX", "KLAC", "MRVL", "ARM", "SMCI"],
    # AI accelerators (tighter subgroup; high co-movement on AI capex news)
    "AI":    ["NVDA", "AMD", "AVGO", "MRVL", "ARM", "SMCI", "PLTR", "SOUN",
              "BBAI", "ACHR"],
    # Memory (commodity; co-moves on pricing news)
    "MEM":   ["MU", "WDC", "STX", "NXPI", "SWKS"],

    # --- Magnificent 7 + close peers ---
    "MAG7":  ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
    "CLOUD": ["AMZN", "MSFT", "GOOGL", "CRM", "NOW", "SNOW", "DDOG", "NET",
              "MDB", "FSLR", "PLTR"],

    # --- China ADRs (regulatory / macro spillover) ---
    "CN_ADR":["BABA", "JD", "PDD", "BIDU", "NIO", "XPEV", "LI", "TME", "BILI",
              "NTES", "BEKE", "TAL", "FUTU", "TCOM", "YMM"],
    # When one China ADR gets regulatory news, the whole complex tends to move.
    # KWEB ETF is the proxy; the scanner already supports it.

    # --- Biotech (FDA announcement spillover to competitors) ---
    "BIO":   ["MRNA", "BNTX", "PFE", "JNJ", "LLY", "MRK", "AZN", "GILD",
              "AMGN", "BIIB", "REGN", "VRTX"],
    # Weight-loss drugs (huge theme; competitor read-through)
    "GLP1":  ["LLY", "NVO", "PFE", "AMGN", "ROG"],
    # CRISPR / gene editing
    "GENE":  ["CRSP", "NTLA", "BEAM", "EDIT", "VERV", "PRME"],

    # --- Oil & energy ---
    "OIL":   ["XOM", "CVX", "COP", "SLB", "EOG", "PSX", "MPC", "VLO", "OXY",
              "PXD", "FANG", "HES"],
    # Refiners (different economics; spillover from crack-spread news)
    "REF":   ["PSX", "MPC", "VLO", "DK", "HFC", "PBF", "CVI"],
    # Uranium (small tight cluster; high spillover)
    "URA":   ["CCJ", "UUUU", "DNN", "UEC", "URG", "NXE", "PDN"],

    # --- Crypto equities (spillover from BTC/ETH moves) ---
    "CRYP_E":["COIN", "MSTR", "MARA", "RIOT", "CLSK", "HUT", "BITF", "HIVE",
              "CAN", "WGMI", "SMLR"],

    # --- Banks / regional (contagion risk) ---
    "BANK":  ["JPM", "BAC", "WFC", "C", "GS", "MS", "USB", "PNC", "TFC",
              "KEY", "FITB", "CFG"],
    # 2023-style regional bank contagion cluster
    "R BANK":["KRE", "KBE", "PACW", "WAL", "FHN", "ZION", "CFG", "KEY"],

    # --- Airlines (group moves on travel/fuel news) ---
    "AIR":   ["DAL", "UAL", "LUV", "AAL", "JBLU", "SAVE", "ALK", "HA"],
    # Cruise (similar; high-fixed-cost, fuel-sensitive)
    "CRUISE":["CCL", "RCL", "NCLH"],

    # --- Defense (geopolitical spillover) ---
    "DEF":   ["LMT", "NOC", "RTX", "GD", "BA", "TDG", "HII", "KTOS", "LHX"],

    # --- Meme / retail-favorite (sentiment spillover) ---
    "MEME":  ["GME", "AMC", "BBBYQ", "FFIE", "MSTR", "COIN", "HOOD", "SOFI",
              "PLUG", "NOK"],

    # --- Semiconductor export-control / chip-war cluster ---
    # On US chip-export bans to China, domestic SEMI names gap up while
    # China-exposed names (TSM, ASML via tooling, QCOM handsets) gap down.
    "CHIP_EXP": ["NVDA", "AMD", "INTC", "TSM", "ASML", "AMAT", "LRCX", "KLAC",
                 "MRVL", "AVGO", "QCOM", "TXN", "ARM", "SMCI", "MU", "NXPI",
                 "SWKS", "MPWR", "ON", "ADI"],

    # --- Pharma patent cliff / generic entry ---
    # Patent expiry of a blockbuster drug: long generic makers, short the
    # originator. Well-known by healthcare-focused funds (Baker Bros, BVF).
    "PHARMA_GEN": ["TEVA", "VTRS", "ENDP", "PRGO", "AGRX", "SND", "HZNP",
                   "TECH", "IQV", "CRL", "ILMN", "VEEV"],

    # --- Cybersecurity breach cluster ---
    # A major breach lifts the whole cyber complex (PAN, CRWD, ZS, S) on
    # expected security-spend acceleration. Used by hedge funds post-2020.
    "CYBER":  ["PANW", "CRWD", "ZS", "S", "FTNT", "CHKP", "TENB", "RPD",
               "QLYS", "NEWR", "NET", "DDOG", "CYBR", "Senti"],

    # --- Payments / fintech regulation ---
    # CFPB/Reg-E action on interchange or BNPL: short networks (V/MA),
    # long disruptors that benefit from lower barriers (SQ/DLO/AFRM).
    "PAYMENTS": ["V", "MA", "PYPL", "SQ", "AFRM", "UPST", "FIS", "FISV",
                 "GPN", "WEX", "DLO", "NU", "PAGS", "MELI", "STNE", "EBANX"],

    # --- China ADRs (regulatory / delisting / VIE spillover) ---
    # Any action against one China ADR drags the whole KWEB complex.
    "CHINA_ADR": ["BABA", "JD", "PDD", "BIDU", "TME", "BILI", "NTES", "FUTU",
                  "TCOM", "BEKE", "DIDI", "NIO", "XPEV", "LI", "WB", "NTLA",
                  "TAL", "EDU", "HUYA", "DOYU", "YMM", "ZH", "KC"],

    # --- Utilities / rate-sensitive ---
    "UTIL":   ["NEE", "DUK", "SO", "D", "AEP", "SRE", "XEL", "WEC", "EIX",
               "PEG", "ED", "WMB", "ET", "O", "SPG", "VTR", "MPW"],

    # --- Agriculture / fertilizer ---
    "AGRI":   ["CF", "MOS", "NTR", "FMC", "ADM", "BG", "CTVA", "SYNN",
               "UAN", "SQM", "ICL"],

    # --- Pandemic / bio-defense / diagnostics ---
    # Outbreak headlines (WHO PHEIC) lift diagnostics + mRNA + PPE names,
    # short travel/cruise/airlines. This is the COVID-19 playbook.
    "PANDMIC": ["MRNA", "BNTX", "PFE", "JNJ", "GILD", "REGN", "ILMN", "DGX",
                "LH", "ABT", "TMO", "QGEN", "BIO", "VEEV", "NVAX", "INO",
                "CODX", "APT", "VBMX", "AMRX"],

    # --- Housing / homebuilders (rate-driven) ---
    "HOUSING": ["DHI", "LEN", "PHM", "NVR", "KBH", "TOL", "MTH", "TMHC",
                "RDFN", "Z", "ZG", "OPEN", "RICK", "BLD", "TREX", "LL",
                "HD", "LOW", "WHR", "MHK"],

    # --- Shipping / maritime (supply-chain disruption) ---
    # Red Sea / Panama drought / port strike: front-end freight rates spike.
    "SHIP":   ["ZIM", "MAERSK-B.CO", "CICOY", "CMCSA", "CCL", "RCL", "NCLH",
               "MATX", "KEX", "UPS", "FDX", "JBHT", "XPO", "ARCB", "SAIA"],

    # --- KOREA exposure (political-risk spillover) ---
    # When Korea political risk spikes (martial law, DPRK, FX), the EWY ADR
    # complex + listed Korean ADRs and Korea-exposed names sell off together.
    "KOREA":  ["EWY", "EWY-IV", "LPL", "KB", "SHG", "IBK", "WK", "KRX",
               "PKX", "KSU", "KCTIE", "LPL", "SKM", "KIM", "ILK", "NHK",
               "NTR", "SSNLF"],

    # --- Nuclear / SMR (AI-power-demand theme) ---
    "NUKE":   ["CCJ", "UUUU", "DNN", "UEC", "URG", "NXE", "PDN", "SMR",
               "OKLO", "BWXT", "CLE", "LEU"],
}

# Reverse index: ticker -> cluster names it belongs to
_TICKER_CLUSTERS: dict[str, list[str]] = {}
for _cluster, _tickers in PEERS.items():
    for _t in _tickers:
        _TICKER_CLUSTERS.setdefault(_t, []).append(_cluster)

def peers_of(sym):
    """Return peer tickers for a given symbol (excluding itself). Empty list if
    the symbol is not in any cluster."""
    sym = str(sym).upper()
    clusters = _TICKER_CLUSTERS.get(sym, [])
    out = []
    seen = {sym}
    for c in clusters:
        for t in PEERS.get(c, []):
            if t not in seen:
                out.append(t)
                seen.add(t)
    return out

def clusters_of(sym):
    """Return the cluster names a ticker belongs to."""
    sym = str(sym).upper()
    return list(_TICKER_CLUSTERS.get(sym, []))

# ---------------------------------------------------------------------------
# THEME KEYWORDS
# ---------------------------------------------------------------------------
# Each theme: (keywords, watch_tickers, default_direction_hint, rationale)
# default_direction_hint: 'short_incumbent' / 'long_disruptor' / 'mixed'
#   - this is ONLY a hint for the report card; the actual trade direction is
#     decided by the news tone (positive/negative) and the analysis gate.
# When ANY keyword matches a headline, the watch_tickers become candidates.

THEMES = {
    "rocket_reuse": {
        "keywords": ["rocket landing", "reusable rocket", "booster recovery",
                     "rocket recycle", "fairing recovery", "caught booster",
                     " Mechazilla", "chopsticks catch"],
        "watch":    ["RKLB", "SPCE", "ASTR", "LMT", "NOC"],
        "hint":     "short_incumbent",
        "rationale": "Reusable-booster milestone by SpaceX pressures listed "
                     "pure-play launch competitors (RKLB/SPCE/ASTR) and mixed "
                     "for primes (LMT/NOC) with their own reusable programs.",
    },
    "starship_test": {
        "keywords": ["starship", "super heavy", "ift-", "starship launch",
                     "starship explosion", "starship success"],
        "watch":    ["RKLB", "SPCE", "ASTR", "BA", "LMT", "NOC", "GD"],
        "hint":     "mixed",
        "rationale": "Starship test outcome moves space-exposed names; success "
                     "negative for listed competitors, failure positive (gap "
                     "closed). BA has Starliner exposure (mixed).",
    },
    "ev_price_war": {
        "keywords": ["ev price cut", "tesla price cut", "ev discount",
                     "tesla discount", "byd price cut", "ev price war",
                     "price cut", "cuts price", "cuts model", "lowers price",
                     "ev margin"],
        "watch":    ["TSLA", "BYD", "BYDDY", "NIO", "XPEV", "LI", "RIVN",
                     "LCID", "F", "GM"],
        "hint":     "mixed",
        "rationale": "An EV price cut compresses margins industry-wide; the "
                     "cutter may gain share (positive) while peers lose (negative).",
    },
    "ai_capex": {
        "keywords": ["ai capex", "hyperscaler capex", "gpu order", "h100 demand",
                     "blackwell", "ai accelerator", "ai infrastructure spend",
                     "stargate", "ai data center"],
        "watch":    ["NVDA", "AMD", "AVGO", "MRVL", "ARM", "SMCI", "PLTR",
                     "EQIX", "DLR", "VRT"],
        "hint":     "long_disruptor",
        "rationale": "AI capex headline lifts the whole AI supply chain: GPU "
                     "vendors (NVDA/AMD), networking (AVGO/MRVL), power/cooling "
                     "(VRT), and data-center REITs (EQIX/DLR).",
    },
    "china_regulatory": {
        "keywords": ["china crackdown", "china regulator", "china antitrust",
                     "china fine", "china gaming ban", "china data security",
                     "cyberspace administration of china", "cac ruling"],
        "watch":    ["BABA", "JD", "PDD", "BIDU", "TME", "BILI", "NTES",
                     "FUTU", "TCOM", "KWEB"],
        "hint":     "short_incumbent",
        "rationale": "China regulatory action on one ADR usually drags the "
                     "whole complex; KWEB is the liquid proxy.",
    },
    "china_stimulus": {
        "keywords": ["china stimulus", "china rate cut", "pboc cut", "rrr cut",
                     "china property rescue", "china infrastructure spending",
                     "china consumer support"],
        "watch":    ["BABA", "JD", "PDD", "BIDU", "NIO", "XPEV", "LI",
                     "FXI", "KWEB", "MCHI", "ASHR", "CNY"],
        "hint":     "long_disruptor",
        "rationale": "China stimulus lifts the whole ADR complex and CN ETFs; "
                     "consumer/e-commerce (BABA/JD/PDD) and EVs (NIO/XPEV/LI) "
                     "are the most elastic.",
    },
    "fda_approval": {
        "keywords": ["fda approval", "fda clears", "fda grants",
                     "positive phase", "positive topline", "phase 3 success",
                     "phase 2 success", " pdufa"],
        "watch":    [],  # filled dynamically from catalysts.FDA calendar
        "hint":     "long_disruptor",
        "rationale": "FDA approval for company X lifts peers with the same "
                     "indication; competitor Read-Through is one of the most "
                     "consistent short-term biotech spillovers.",
    },
    "fda_rejection": {
        "keywords": ["fda rejection", "fda crl", "complete response letter",
                     "clinical hold", "phase 3 failure", "phase 2 failure",
                     "adverse event", "trial halted"],
        "watch":    [],
        "hint":     "short_incumbent",
        "rationale": "FDA rejection / trial failure for company X often lifts "
                     "competitors (their drug is now relatively more valuable) "
                     "and hits the whole subsector's sentiment.",
    },
    "merger_announcement": {
        "keywords": ["acquires", "to acquire", "merger agreement", "buyout",
                     "taken private", " tender offer", " shares for $"],
        "watch":    [],  # filled dynamically: peers of the target/acro
        "hint":     "long_disruptor",
        "rationale": "An M&A announcement often lifts PEERS of the target "
                     "(expectation of further consolidation) and sometimes "
                     "hits the acquirer (deal premium / dilution).",
    },
    "oil_supply_shock": {
        "keywords": ["opec cut", "opec+ cut", "saudi cut", "oil supply cut",
                     "pipeline attack", "refinery fire", "refinery explosion",
                     "strait of hormuz", "red sea tanker",
                     "production cut", "output cut", "supply cut",
                     "opec+", "opec surprise", "saudi arabia cut"],
        "watch":    ["XOM", "CVX", "COP", "SLB", "EOG", "OXY", "PXD", "XLE",
                     "USO", "BNO"],
        "hint":     "long_disruptor",
        "rationale": "Oil supply shock lifts integrateds (XOM/CVX/COP), "
                     "shale (EOG/OXY/PXD), and the XLE/USO ETFs.",
    },
    "oil_demand_shock": {
        "keywords": ["recession fear", "demand destruction", "china slowdown",
                     "oil demand cut", "iea demand"],
        "watch":    ["XOM", "CVX", "COP", "SLB", "EOG", "OXY", "PXD", "XLE",
                     "USO", "BNO"],
        "hint":     "short_incumbent",
        "rationale": "Demand-shock headlines hit the same oil complex on the "
                     "short side.",
    },
    "crypto_etf_flow": {
        "keywords": ["btc etf inflow", "btc etf outflow", "eth etf inflow",
                     " spot bitcoin etf", "ibit inflow", "fbtc inflow",
                     "crypto adoption", "treasury bitcoin"],
        "watch":    ["COIN", "MSTR", "MARA", "RIOT", "CLSK", "HUT", "BITF",
                     "HIVE", "SMLR", "BITO", "BITQ"],
        "hint":     "long_disruptor",
        "rationale": "Crypto ETF flow / adoption headlines lift crypto-equity "
                     "complex (COIN/MSTR/miners) and crypto ETFs.",
    },
    "bank_run": {
        "keywords": ["bank run", "deposit flight", "deposit outflow",
                     "bank failure", "fdic seizure", "bank takeover"],
        "watch":    ["KRE", "KBE", "PACW", "WAL", "FHN", "ZION", "CFG",
                 "KEY", "JPM", "BAC"],
        "hint":     "short_incumbent",
        "rationale": "Bank-run headlines trigger regional-bank contagion; "
                     "deposit flight to majors (JPM/BAC) can lift them.",
    },
    "geopolitical": {
        "keywords": ["taiwan strait", "south china sea", "russia ukraine",
                     "middle east escalation", "iran israel", "north korea",
                     " nato ", "article 5"],
        "watch":    ["LMT", "NOC", "RTX", "GD", "BA", "TDG", "HII", "KTOS",
                     "ITA", "GLD", "TLT"],
        "hint":     "long_disruptor",
        "rationale": "Geopolitical escalation lifts defense (ITA components) "
                     "and safe havens (GLD/TLT).",
    },
    "rate_decision": {
        "keywords": ["fed cuts rates", "fed raises rates", "fed hold",
                     "fomc decision", "powell says", "ecb cuts", "ecb hikes",
                     "boj hike", "boj intervention"],
        "watch":    ["SPY", "QQQ", "TLT", "GLD", "DXY", "IWM", "XLF", "XLE"],
        "hint":     "mixed",
        "rationale": "Central-bank decision moves broad ETFs; cuts = risk-on, "
                     "hikes = risk-off. Trade via ETFs (cheap, liquid).",
    },
}

# Build a keyword -> theme index for fast matching
_KW_INDEX = []
for _name, _spec in THEMES.items():
    for _kw in _spec["keywords"]:
        _KW_INDEX.append((_kw.lower(), _name))

def themes_for(headlines):
    """Return list of {theme, keyword, headline} for matched headlines.

    headlines: iterable of strings.
    Returns one entry per (headline, theme) match (a single headline can match
    multiple themes). Deduplicates by (theme, headline)."""
    out = []
    seen = set()
    for h in headlines:
        if not h:
            continue
        low = str(h).lower()
        for kw, theme in _KW_INDEX:
            if kw in low:
                key = (theme, h)
                if key in seen:
                    continue
                seen.add(key)
                out.append({"theme": theme, "keyword": kw.strip(),
                            "headline": h})
    return out

def spillover_candidates(feed_items, hours=24):
    """One-call: feed -> {ticker: [reasons]} for cross-asset spillover.

    Given fetch_all() output (list of (name, items, err) tuples), find theme
    matches in the headlines and return a dict:

        {ticker: [{"theme": ..., "headline": ..., "hint": ..., "rationale": ...}, ...]}

    Downstream the report can inject these tickers as candidates and let the
    existing scoring gate decide whether they're actually tradeable.
    """
    # Pass (feed, title, date) through to the matcher so downstream impact
    # scoring can count DISTINCT feeds per theme.
    headlines = []
    for name, items, err in feed_items:
        if err or not items:
            continue
        for it in items:
            t = (it.get("title") or "").strip()
            if t:
                headlines.append({"feed": name, "title": t,
                                  "date": it.get("date", "")})
    matches = themes_for([h["title"] for h in headlines])
    # Build a title -> (feed, date) index so we can attach feed info to each match
    by_title: dict[str, list] = {}
    for h in headlines:
        by_title.setdefault(h["title"], []).append(h)
    out: dict[str, list] = {}
    for m in matches:
        spec = THEMES.get(m["theme"])
        if not spec:
            continue
        # find which feed(s) ran this headline
        hits = by_title.get(m["headline"], [])
        feeds_for_hit = list(dict.fromkeys(h["feed"] for h in hits)) or ["?"]
        date_for_hit = (hits[0]["date"] if hits else "")
        for t in spec.get("watch", []):
            out.setdefault(t, []).append({
                "theme": m["theme"],
                "keyword": m["keyword"],
                "headline": m["headline"],
                "feed": feeds_for_hit[0],
                "feeds": feeds_for_hit,
                "date": date_for_hit,
                "hint": spec.get("hint", "mixed"),
                "rationale": spec.get("rationale", ""),
            })
    return out

if __name__ == "__main__":
    # quick smoke: print cluster sizes
    for c, ts in sorted(PEERS.items()):
        print(f"{c:8} {len(ts):2}  {', '.join(ts)}")
    print()
    # theme self-test
    test = ["SpaceX catches Starship booster with chopsticks",
            "Tesla cuts Model Y price in China",
            "OPEC+ announces surprise production cut"]
    for m in themes_for(test):
        print(f"  theme={m['theme']:20} kw={m['keyword']!r}")
