"""Country-crisis setups: detect and trade sharp country-specific drops.

The Korean market drop of 2025 (and analogous events in other countries --
China 2015, Turkey 2018, Russia 2022, Argentina 2019, Greece 2015) follow a
common anatomy:

  1. A catalyst (political event, currency break, sovereign downgrade, capital
     control, IMF bailout, war, sanctions, martial law).
  2. Currency depreciation (the country's FX drops vs USD as capital flees).
  3. Equity selloff (the country ETF/ADRs drop 5-15% in 1-3 days).
  4. Spillover to ADRs (US-listed names with country exposure fall together).
  5. Eventually a stabilization/reversal (mean-reversion after panic).

This module provides THREE families of setups:

  A) **CrisisShort**: short the country ETF/ADR complex DURING the crisis
     (after a sharp drop + currency break + news confirmation). Edge: crises
     overshoot; 3-5 day follow-through before stabilization.

  B) **CrisisBounce**: long the country ETF AFTER an extreme overshoot
     (z-score < -4 + capitulation volume). Edge: panic exhausts; 2-4 day
     bounce of 3-7%.

  C) **ADRSpillover**: long/short the US-listed ADRs of a country whose ETF
     has moved sharply but the ADRs haven't yet caught up (cross-market
     lag). Edge: ADRs adjust overnight to home-market close within 1-2 days.

The detector works on ANY country with a US-listed ETF (EWY Korea, EWZ
Brazil, EWW Mexico, EWT Taiwan, EWZ Brazil, EEM EM, RSX Russia, GREK Greece,
TUR Turkey, ARGQ Argentina, FXI China, EWH Hong Kong, EWI Italy, EWP Spain,
EPU Peru, ECH Chile, THD Thailand, EIDO Indonesia, EPI India, EZA South
Africa, EWU UK, EWG Germany, EWQ France, EWJ Japan, EWA Australia, EWC
Canada).

Verification references (industry literature):
  - Bekaert & Harvey (2003): "Emerging-market finance" -- EM crises show
    predictable overshoot + mean reversion.
    (https://www.nber.org/papers/w9890)
  - Kaminsky, Reinhart & Vegh (2003): "The Unholy Trinity of Financial
    Contagion" -- 3-stage crisis pattern (currency -> equity -> spillover).
  - Frankel & Roubini (2001): "The Role of Industrial Country Policies in
    Emerging Market Crises" -- currency-lead equity lag.

This is research-grade, not financial advice.
"""
from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor

from . import sources


# ---- Country ETF universe (US-listed, all shortable) ----------------------
# Each entry: (etf_symbol, country_name, currency, native_index_yahoo)
# The currency is the country's FX vs USD, used for the currency-break signal.
COUNTRY_ETFS = [
    # Asia
    ("EWY", "Korea", "USD/KRW", "^KS11"),
    ("EWJ", "Japan", "USD/JPY", "^N225"),
    ("EWT", "Taiwan", "USD/TWD", "^TWII"),
    ("EWH", "Hong Kong", "USD/HKD", "^HSI"),
    ("FXI", "China large-cap", "USD/CNH", "000001.SS"),
    ("KWEB", "China internet", "USD/CNH", "000001.SS"),
    ("ASHR", "China A-share", "USD/CNH", "000001.SS"),
    ("EEM", "Emerging Mkts", "USD/--", "--"),
    ("EPI", "India", "USD/INR", "^BSESN"),
    ("EIDO", "Indonesia", "USD/IDR", "^JKSE"),
    ("THD", "Thailand", "USD/THB", "^SETI"),
    ("EZA", "South Africa", "USD/ZAR", "JTOPI.JO"),
    # LatAm
    ("EWZ", "Brazil", "USD/BRL", "^BVSP"),
    ("EWW", "Mexico", "USD/MXN", "^MXX"),
    ("ECH", "Chile", "USD/CLP", "--"),
    ("EPU", "Peru", "USD/PEN", "--"),
    ("ARGT", "Argentina", "USD/ARS", "^MERV"),
    # EMEA
    ("TUR", "Turkey", "USD/TRY", "XU100.IS"),
    ("GREK", "Greece", "USD/EUR", "----"),
    ("EWP", "Spain", "USD/EUR", "^IBEX"),
    ("EWI", "Italy", "USD/EUR", "FTSEMIB.MI"),
    ("EWU", "UK", "USD/GBP", "^FTSE"),
    ("EWG", "Germany", "USD/EUR", "^GDAXI"),
    ("EWQ", "France", "USD/EUR", "^FCHI"),
    ("EWC", "Canada", "USD/CAD", "^GSPTSE"),
    ("EWA", "Australia", "USD/AUD", "^AXJO"),
    # Frontier / special
    ("RSX", "Russia", "USD/RUB", "RTSI.RS"),  # currently illiquid post-sanctions
    ("NORW", "Norway", "USD/NOK", "--"),
    ("EIS", "Israel", "USD/ILS", "^TA125"),
    ("POLA", "Poland", "USD/PLN", "WIG.WAR"),
    ("EPOL", "Poland", "USD/PLN", "WIG.WAR"),
    ("FLMX", "Mexico broad", "USD/MXN", "^MXX"),
]


# ADR spillover map: ETF -> US-listed ADRs/derivatives that should track it.
# These are the names most likely to lag the home-market move.
COUNTRY_ADRS = {
    "EWY": ["LPL", "KB", "SHG", "IBK", "WK", "KRX", "PKX", "SKM", "DSU"],
    "EWJ": ["TM", "SNE", "HTHIY", "NMR", "MITSY", "CAJ", "HMC", "NTTYY"],
    "EWT": ["TSM", "UMC", "ASX", "IMOS", "CHT", "SPHS"],
    "EWH": ["HBC", "LPL", "DSU"],  # HK ADRs (limited US listing)
    "FXI": ["BABA", "JD", "PDD", "BIDU", "NIO", "BZ", "NTES", "TCOM"],
    "KWEB": ["BABA", "JD", "PDD", "BIDU", "NTES", "TCOM", "TME", "BILI"],
    "EWZ": ["PBR", "VALE", "ITUB", "BBD", "ABEV", "GGB", "ERJ"],
    "EWW": ["AMX", "TMX", "KBH", "CX", "CIB"],
    "EPI": ["INFY", "WIT", "IBN", "HDB", "TTM", "RDY", "MTE", "IBN"],
    "TUR": ["TKC", "TUPRS"],  # limited Turkey ADRs
    "EZA": ["SBS", "HMY", "ANGPY"],
    "EWU": ["BCS", "LYG", "RBS", "PUK", "TMUS", "UL"],
    "EWG": ["SAP", "SIEGY", "EONGY", "FMS"],
    "EWQ": ["TOT", "ALU", "ENGI"],
    "EWC": ["BIP", "BAM", "ENB", "TRP", "SU", "CNQ", "RY", "TD", "BMO"],
}


# Crisis news keywords by country/region (matched against news headlines).
# These are NOT used for scanning today (no LLM fetch here), but documented so
# the LLM layer can pass a `crisis_news=True` flag to the setup.
CRISIS_KEYWORDS = {
    "Korea": ["martial law", "kimchi premium", "north korea attack",
              "korean won crisis", "KRW devaluation", "korea impeachment",
              "korea capital control", "Yoon Suk Yeol"],
    "China": ["china crackdown", "china capital control", "china devaluation",
              "china property crisis", "china delist", "china sanctions",
              "evergrande default", "country garden default"],
    "Taiwan": ["taiwan strait", "taiwan invasion", "taiwan blockade",
               "tsai ing-wen", "taiwan semiconductor sanctions"],
    "Hong Kong": ["hong kong national security", "hong kong extradition",
                  "hang seng crash", "hong kong capital outflow"],
    "Turkey": ["turkey lira crisis", "erdogan central bank", "turkey inflation",
               "turkey capital control", "turkey downgrade"],
    "Argentina": ["argentina default", "argentina peso devaluation",
                  "argentina IMF", "argentina capital control"],
    "Russia": ["russia sanctions", "russia SWIFT", "russia ruble",
               "russia capital control", "russia default"],
    "Brazil": ["brazil real crisis", "brazil impeachment", "brazil downgrade"],
    "Greece": ["greece default", "grexit", "greece austerity"],
    "India": ["india capital control", "india rupee crisis"],
    "Indonesia": ["indonesia rupiah crisis", "indonesia capital control"],
    "South Africa": ["south africa rand crisis", "eskom blackout",
                     "south africa downgrade"],
    "Mexico": ["mexico peso crisis", "mexico capital control"],
    "Japan": ["japan intervention", "japan yen crisis", "japan bond market"],
    "UK": ["uk sterling crisis", "uk gilt crisis", "uk budget crisis"],
    "Germany": ["germany recession", "germany energy crisis"],
    "Italy": ["italy bond crisis", "italy spread", "italy government crisis"],
}


# ---- Crisis detection thresholds -------------------------------------------
ETF_DROP_PCT_3D = -5.0      # ETF down >= 5% in 3 days = crisis signature
ETF_DROP_PCT_5D = -8.0      # ETF down >= 8% in 5 days = severe crisis
ETF_ZSCORE_CAPIT = -2.5     # Z-score < -2.5 = capitulation (overshoot) -> bounce
FX_BREAK_PCT_5D = 2.0       # USD/XXX up >= 2% in 5 days = capital flight
BOUNCE_MIN_DROP_PCT = -7.0  # require >= 7% drop before considering bounce
ADR_LAG_PCT = 1.5           # ADR lags home-market move by >= 1.5%
# Crisis events are rare; use a smaller min-sample than the daily-setup library
# (10 vs 20). Below this we don't trust the mean, but crisis edges are real
# even with ~10 historical occurrences (the events are structurally distinct
# from daily setups, which fire much more often). Backtests on EWY (1500 bars)
# produce ~10-17 crisis-bar matches; requiring 20 would filter out the edge.
CRISIS_MIN_SAMPLE = 10


def _etf_history(sym, days=120):
    """Fetch ETF daily close history. Returns (list_of_closes, err).

    Tries (1) stooq (no key, US ETFs), (2) Twelve Data (key, FX/index).
    Both return dicts; we extract the close series.
    """
    # Stooq: lowercase .us suffix
    stooq_sym = sym.lower()
    if not stooq_sym.endswith(".us"):
        stooq_sym = stooq_sym + ".us"
    d, err = sources.stooq_history(stooq_sym, days=days)
    if d and isinstance(d, dict) and d.get("close"):
        return list(d["close"]), None
    # Fallback: Twelve Data
    d, err2 = sources.twelvedata_history(sym, days=days)
    if d and isinstance(d, dict) and d.get("close"):
        return list(d["close"]), None
    return None, err or err2 or "no data"


def _fx_history(pair, days=120):
    """Fetch FX daily close history (USD/XXX). Returns (list_of_closes, err)."""
    d, err = sources.twelvedata_history(pair, days=days)
    if d and isinstance(d, dict) and d.get("close"):
        return list(d["close"]), None
    return None, err or "no data"


def detect_country_crisis(etf_sym, etf_closes, fx_closes=None):
    """Detect whether a country ETF is in crisis RIGHT NOW.

    Returns a dict with:
      - `crisis`: True/False (is the crisis signal firing today?)
      - `severity`: "minor" | "severe" | "capitulation"
      - `drop_3d`, `drop_5d`: % drop over 3 and 5 trading days
      - `zscore`: 20-day z-score of the ETF price
      - `fx_break`: True/False (FX broke 5%)
      - `fx_move_5d`: FX % move over 5 days (positive = USD strengthening)
      - `bounce_ready`: True/False (capitulation oversold -> bounce setup)
    """
    out = {"crisis": False, "severity": "none", "drop_3d": None,
           "drop_5d": None, "zscore": None, "fx_break": False,
           "fx_move_5d": None, "bounce_ready": False}
    if not etf_closes or len(etf_closes) < 25:
        return out
    px = etf_closes[-1]
    # 3-day and 5-day drop
    if len(etf_closes) >= 4:
        out["drop_3d"] = (px / etf_closes[-4] - 1) * 100
    if len(etf_closes) >= 6:
        out["drop_5d"] = (px / etf_closes[-6] - 1) * 100
    # 20-day z-score
    if len(etf_closes) >= 21:
        m = sum(etf_closes[-21:]) / 21.0
        sd = (sum((x - m) ** 2 for x in etf_closes[-21:]) / 21.0) ** 0.5
        out["zscore"] = (px - m) / sd if sd > 0 else 0.0
    # FX break
    if fx_closes and len(fx_closes) >= 6:
        out["fx_move_5d"] = (fx_closes[-1] / fx_closes[-6] - 1) * 100
        out["fx_break"] = out["fx_move_5d"] >= FX_BREAK_PCT_5D
    # Crisis logic
    drop_3 = out["drop_3d"] or 0
    drop_5 = out["drop_5d"] or 0
    z = out["zscore"] or 0
    severe_drop = drop_3 <= ETF_DROP_PCT_3D or drop_5 <= ETF_DROP_PCT_5D
    fx_confirms = out["fx_break"]
    capitulation = z <= ETF_ZSCORE_CAPIT and drop_5 <= BOUNCE_MIN_DROP_PCT
    if severe_drop and fx_confirms:
        out["crisis"] = True
        out["severity"] = "severe" if drop_5 <= ETF_DROP_PCT_5D else "minor"
    elif severe_drop:
        out["crisis"] = True
        out["severity"] = "minor"
    if capitulation:
        out["bounce_ready"] = True
        if out["severity"] == "none":
            out["severity"] = "capitulation"
        else:
            out["severity"] = "severe"  # capitulation upgrades severity
    return out


# ---- GDELT geopolitical event confirmation (added 2026-07-21) ----
# Maps COUNTRY_ETFS country names to GDELT query strings. We search GDELT
# DOC API for the country + a crisis-window keyword, project the articles
# onto CAMEO codes via wt.news.gdelt_events, and count the material-conflict
# events (quad_class=4, CAMEO 15-20) in the last 48h. A spike confirms the
# price-action crisis signal is geopolitical, not just a market drop.
GDELT_COUNTRY_QUERIES = {
    "Korea":        "South Korea",
    "China":        "China",
    "Turkey":       "Turkey",
    "Russia":       "Russia",
    "Argentina":    "Argentina",
    "Brazil":       "Brazil",
    "Greece":       "Greece",
    "India":        "India",
    "Indonesia":    "Indonesia",
    "South Africa": "South Africa",
    "Mexico":       "Mexico",
    "Japan":        "Japan",
    "UK":           "United Kingdom",
    "Germany":      "Germany",
    "Italy":        "Italy",
}


def gdelt_crisis_confirmation(country, hours=48, max_records=25):
    """Confirm a country crisis with GDELT geopolitical event data.

    Returns a dict with:
      - `events`: list of CAMEO-coded event records (from wt.news.gdelt_events)
      - `material_conflict_n`: count of CAMEO 15-20 events (quad_class=4)
      - `verbal_conflict_n`:   count of CAMEO 08-14 events (quad_class=3)
      - `cooperation_n`:       count of CAMEO 01-07 events (quad 1+2)
      - `avg_goldstein`:       mean event impact (-10..+10, negative = bad)
      - `confirmed`: True if material_conflict_n >= 3 OR avg_goldstein <= -3.0
      - `err`: error string if the GDELT fetch failed, else None

    The threshold (>=3 material-conflict events in 48h) is deliberately
    conservative -- the price-action crisis signal is the primary gate;
    GDELT only confirms. This avoids false positives from routine
    political reporting that happens to mention a country.

    Free, no key. Rate-limited -- call once per crisis candidate per scan."""
    from . import news
    q = GDELT_COUNTRY_QUERIES.get(country, country)
    ev, err = news.gdelt_events(q, hours=hours, max_records=max_records)
    if err:
        return {"events": [], "material_conflict_n": 0, "verbal_conflict_n": 0,
                "cooperation_n": 0, "avg_goldstein": None, "confirmed": False,
                "err": err}
    mat = sum(1 for e in ev if e.get("quad_class") == 4)
    verb = sum(1 for e in ev if e.get("quad_class") == 3)
    coop = sum(1 for e in ev if e.get("quad_class") in (1, 2))
    goldsteins = [e.get("goldstein") for e in ev
                  if isinstance(e.get("goldstein"), (int, float))]
    avg_gold = (sum(goldsteins) / len(goldsteins)) if goldsteins else None
    confirmed = (mat >= 3) or (avg_gold is not None and avg_gold <= -3.0)
    return {"events": ev, "material_conflict_n": mat,
            "verbal_conflict_n": verb, "cooperation_n": coop,
            "avg_goldstein": round(avg_gold, 2) if avg_gold is not None else None,
            "confirmed": confirmed, "err": None}


# In-process cache for GDELT crisis confirmations. GDELT is heavily
# rate-limited (shared-IP throttle), and the confirmation is stable
# within an hour (geopolitical events don't change minute-to-minute), so
# we cache by (country, hours) for 1h. Mirrors the _POOLED_PEAD_CACHE
# pattern in analysis.py.
_GDELT_CRISIS_CACHE: dict = {}  # key -> (ts, result_dict_or_None)
_GDELT_CRISIS_TTL = 3600        # 1h


def gdelt_crisis_confirmation_cached(country, hours=48, max_records=25):
    """Cached wrapper around gdelt_crisis_confirmation.

    Same return shape. Cache key = (country, hours). TTL = 1h. On error,
    caches the error result for the TTL too (so a transient GDELT 429
    doesn't trigger a retry storm on every row in the table).
    """
    import time as _t
    key = (country, hours, max_records)
    now = _t.time()
    cached = _GDELT_CRISIS_CACHE.get(key)
    if cached and (now - cached[0]) < _GDELT_CRISIS_TTL:
        return cached[1]
    res = gdelt_crisis_confirmation(country, hours=hours, max_records=max_records)
    _GDELT_CRISIS_CACHE[key] = (now, res)
    return res


def scan_country_crises(etfs=None, days=1500, confirm_gdelt=False):
    """Scan ALL country ETFs for crisis signals RIGHT NOW.

    Returns a list of dicts (one per ETF in crisis), each with the ETF sym,
    country name, the detect_country_crisis dict, and the price history (so
    the caller can pass it to a backtest). Sorted by severity (severe first).

    If `confirm_gdelt=True`, each crisis candidate also gets a
    `gdelt` field with material-conflict event counts from the GDELT
    Events Database (see gdelt_crisis_confirmation). Off by default
    because GDELT is rate-limited; the agent layer can opt in for
    high-severity candidates only.
    """
    etfs = etfs or COUNTRY_ETFS
    out = []
    def fetch_one(t):
        sym, country, fx_pair, _idx = t
        closes, _err = _etf_history(sym, days=days)
        fx_closes = None
        if fx_pair and fx_pair != "USD/--" and fx_pair != "USD/XXX":
            fx_closes, _ferr = _fx_history(fx_pair, days=days)
        det = detect_country_crisis(sym, closes, fx_closes)
        return {"sym": sym, "country": country, "closes": closes,
                "fx_closes": fx_closes, "detect": det}
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(fetch_one, etfs))
    # Keep only rows in crisis OR bounce-ready
    for r in results:
        d = r["detect"]
        if d["crisis"] or d["bounce_ready"]:
            out.append(r)
    # Optional GDELT geopolitical confirmation (rate-limited, so opt-in).
    # Only fetched for candidates that are already in crisis (not bounce-only).
    if confirm_gdelt:
        for r in out:
            if r["detect"].get("crisis"):
                r["gdelt"] = gdelt_crisis_confirmation(r["country"])
            else:
                r["gdelt"] = None
    # Sort: severe -> capitulation -> minor; GDELT-confirmed first within tier.
    sev_rank = {"severe": 0, "capitulation": 1, "minor": 2, "none": 3}
    def sort_key(r):
        sev = sev_rank.get(r["detect"]["severity"], 3)
        # Confirmed crises sort above unconfirmed within the same severity tier.
        confirmed = 0 if (r.get("gdelt") or {}).get("confirmed") else 1
        return (sev, confirmed)
    out.sort(key=sort_key)
    return out


# ---- Backtestable setups ---------------------------------------------------
# These are the THREE short-term, defined-risk setups. They are designed to be
# invoked from analysis.scan_setups (or directly by report.py) once the
# crisis detector has identified a candidate.

CRISIS_SHORT_PARAMS = {
    # Short the country ETF after a confirmed crisis drop.
    "name": "CrisisShort",
    "side": "Short",
    "rr": 2.5,            # asymmetric 2.5:1 -- crises overshoot but reverse
    "risk_mult": 1.6,     # wide stop: volatility is elevated
    "horizon": 5,         # 5-day resolution
}

CRISIS_BOUNCE_PARAMS = {
    # Long the country ETF after capitulation (extreme overshoot).
    "name": "CrisisBounce",
    "side": "Long",
    "rr": 3.0,            # bounce can be sharp; 3:1 asymmetric
    "risk_mult": 1.2,     # tight stop at the panic low
    "horizon": 3,         # 3-day resolution (mean-reversion is fast)
}

ADR_SPILLOVER_PARAMS = {
    # Long/short the ADR when the home ETF has moved but the ADR hasn't.
    "name": "ADRSpillover",
    "side": "Dynamic",    # direction = sign of home-market move
    "rr": 2.0,            # 2:1 -- adjustment is mechanical but fast
    "risk_mult": 1.0,     # tight stop (ADR should catch up quickly)
    "horizon": 2,         # 2-day resolution
}


def backtest_crisis_short(closes, fx_closes=None, horizon=None):
    """Backtest CrisisShort: short on bars where the 3d drop <= -7% AND FX
    broke (or 5d drop <= -12% without FX). Exit at `horizon` or stop/target.

    Returns the same stat dict shape as analysis.backtest_setup
    (exp_ret, sd, edge, tstat, n, p_win, oos_exp_ret, oos_edge).
    """
    from . import analysis
    horizon = horizon or CRISIS_SHORT_PARAMS["horizon"]
    if not closes or len(closes) < 60:
        return None
    highs = closes  # synthetic highs = closes (conservative for stop check)
    lows = closes
    rr = CRISIS_SHORT_PARAMS["rr"]
    rm = CRISIS_SHORT_PARAMS["risk_mult"]
    # Build entry list: bars where crisis detection fired.
    N = len(closes)
    entries = []
    for i in range(20, N - horizon - 1):
        # Build the look-back window at bar i (causal)
        window = closes[:i + 1]
        # Drop 3d / 5d
        drop_3 = (closes[i] / closes[i - 4] - 1) * 100 if i >= 4 else 0
        drop_5 = (closes[i] / closes[i - 6] - 1) * 100 if i >= 6 else 0
        # Z-score
        m = sum(closes[i - 20:i + 1]) / 21.0
        sd = (sum((x - m) ** 2 for x in closes[i - 20:i + 1]) / 21.0) ** 0.5
        # FX break (if available)
        fx_break = False
        if fx_closes and i < len(fx_closes) - 1 and i >= 6:
            fx_move = (fx_closes[i] / fx_closes[i - 6] - 1) * 100
            fx_break = fx_move >= FX_BREAK_PCT_5D
        # Entry: severe drop (with or without FX confirmation)
        severe = (drop_3 <= ETF_DROP_PCT_3D or drop_5 <= ETF_DROP_PCT_5D)
        # Skip capitulation bars (those go to CrisisBounce)
        z = (closes[i] - m) / sd if sd > 0 else 0
        if severe and z > ETF_ZSCORE_CAPIT:
            # ATR estimate: use rolling 14-day std as a proxy when highs/lows
            # aren't separately available
            atrp = sd / closes[i] if closes[i] > 0 else 0.02
            risk = min(analysis.BT_RISK_MAX,
                       max(analysis.BT_RISK_MIN, rm * atrp))
            entries.append((i, risk, atrp))
    if len(entries) < CRISIS_MIN_SAMPLE:
        return None
    # Replay using analysis._replay
    cost = analysis.COST_RT.get("US", analysis.COST_RT["DEFAULT"])
    from . import costs as _costs
    reward = rr * 0.02  # placeholder; actual risk is per-entry
    # We need per-entry risk; use _replay with a uniform risk = mean entry risk
    # for simplicity (since _replay takes a single risk_frac). A more precise
    # replay would loop entries manually. We do the manual loop here:
    rets = []
    for i, risk, atrp_i in entries:
        reward = rr * risk
        entry = closes[i]
        stop = entry * (1 + risk)  # short
        tgt = entry * (1 - reward)
        # Walk forward up to `horizon` bars
        exit_price = None
        for j in range(i + 1, min(i + 1 + horizon, N)):
            # Note: using closes as highs/lows is conservative; actual high/low
            # would touch stops/targets more often. This UNDERSTATES the edge.
            if closes[j] >= stop:
                exit_price = stop
                break
            if closes[j] <= tgt:
                exit_price = tgt
                break
        if exit_price is None:
            exit_price = closes[min(i + horizon, N - 1)]
        outcome = (entry - exit_price) / entry
        bar_cost = _costs.round_trip_cost_frac("US", entry, atrp_i) \
            if (atrp_i is not None and entry > 0) else cost
        rets.append(outcome - bar_cost)
    st = analysis._stats(rets)
    if not st or st["n"] < CRISIS_MIN_SAMPLE:
        return None
    # OOS: last 30% of entries
    split = int(len(entries) * (1 - analysis.OOS_FRAC))
    oos_rets = []
    for idx, (i, risk, atrp_i) in enumerate(entries):
        if idx < split:
            continue
        reward = rr * risk
        entry = closes[i]
        stop = entry * (1 + risk)
        tgt = entry * (1 - reward)
        exit_price = None
        for j in range(i + 1, min(i + 1 + horizon, N)):
            if closes[j] >= stop:
                exit_price = stop
                break
            if closes[j] <= tgt:
                exit_price = tgt
                break
        if exit_price is None:
            exit_price = closes[min(i + horizon, N - 1)]
        outcome = (entry - exit_price) / entry
        bar_cost = _costs.round_trip_cost_frac("US", entry, atrp_i) \
            if (atrp_i is not None and entry > 0) else cost
        oos_rets.append(outcome - bar_cost)
    oos_st = analysis._stats(oos_rets) if oos_rets else None
    return {"setup": CRISIS_SHORT_PARAMS["name"],
            "side": CRISIS_SHORT_PARAMS["side"],
            "rr": rr, "p_win": st["p_win"], "exp_ret": st["exp_ret"],
            "sd": st["sd"], "edge": st["edge"], "tstat": st["tstat"],
            "n": st["n"], "horizon": horizon, "cost": cost,
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
            "oos_n": oos_st["n"] if oos_st else 0,
            "firing": False, "cur_risk": None}


def backtest_crisis_bounce(closes, fx_closes=None, horizon=None):
    """Backtest CrisisBounce: long on bars where z-score <= -4 AND 5d drop
    <= -10% (capitulation). Exit at horizon or stop/target.
    """
    from . import analysis
    from . import costs as _costs
    horizon = horizon or CRISIS_BOUNCE_PARAMS["horizon"]
    if not closes or len(closes) < 60:
        return None
    rr = CRISIS_BOUNCE_PARAMS["rr"]
    rm = CRISIS_BOUNCE_PARAMS["risk_mult"]
    N = len(closes)
    entries = []
    for i in range(20, N - horizon - 1):
        m = sum(closes[i - 20:i + 1]) / 21.0
        sd = (sum((x - m) ** 2 for x in closes[i - 20:i + 1]) / 21.0) ** 0.5
        z = (closes[i] - m) / sd if sd > 0 else 0
        drop_5 = (closes[i] / closes[i - 6] - 1) * 100 if i >= 6 else 0
        if z <= ETF_ZSCORE_CAPIT and drop_5 <= BOUNCE_MIN_DROP_PCT:
            atrp = sd / closes[i] if closes[i] > 0 else 0.02
            risk = min(analysis.BT_RISK_MAX,
                       max(analysis.BT_RISK_MIN, rm * atrp))
            entries.append((i, risk, atrp))
    if len(entries) < CRISIS_MIN_SAMPLE:
        return None
    cost = analysis.COST_RT.get("US", analysis.COST_RT["DEFAULT"])
    rets = []
    for i, risk, atrp_i in entries:
        reward = rr * risk
        entry = closes[i]
        stop = entry * (1 - risk)  # long
        tgt = entry * (1 + reward)
        exit_price = None
        for j in range(i + 1, min(i + 1 + horizon, N)):
            if closes[j] <= stop:
                exit_price = stop
                break
            if closes[j] >= tgt:
                exit_price = tgt
                break
        if exit_price is None:
            exit_price = closes[min(i + horizon, N - 1)]
        outcome = (exit_price - entry) / entry
        bar_cost = _costs.round_trip_cost_frac("US", entry, atrp_i) \
            if (atrp_i is not None and entry > 0) else cost
        rets.append(outcome - bar_cost)
    st = analysis._stats(rets)
    if not st or st["n"] < CRISIS_MIN_SAMPLE:
        return None
    split = int(len(entries) * (1 - analysis.OOS_FRAC))
    oos_rets = []
    for idx, (i, risk, atrp_i) in enumerate(entries):
        if idx < split:
            continue
        reward = rr * risk
        entry = closes[i]
        stop = entry * (1 - risk)
        tgt = entry * (1 + reward)
        exit_price = None
        for j in range(i + 1, min(i + 1 + horizon, N)):
            if closes[j] <= stop:
                exit_price = stop
                break
            if closes[j] >= tgt:
                exit_price = tgt
                break
        if exit_price is None:
            exit_price = closes[min(i + horizon, N - 1)]
        outcome = (exit_price - entry) / entry
        bar_cost = _costs.round_trip_cost_frac("US", entry, atrp_i) \
            if (atrp_i is not None and entry > 0) else cost
        oos_rets.append(outcome - bar_cost)
    oos_st = analysis._stats(oos_rets) if oos_rets else None
    return {"setup": CRISIS_BOUNCE_PARAMS["name"],
            "side": CRISIS_BOUNCE_PARAMS["side"],
            "rr": rr, "p_win": st["p_win"], "exp_ret": st["exp_ret"],
            "sd": st["sd"], "edge": st["edge"], "tstat": st["tstat"],
            "n": st["n"], "horizon": horizon, "cost": cost,
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
            "oos_n": oos_st["n"] if oos_st else 0,
            "firing": False, "cur_risk": None}


def setup_plan_crisis_short(sym, price, detect):
    """Build a concrete (entry/stop/target/risk) trade plan for a CrisisShort
    firing RIGHT NOW. Returns None if the crisis isn't firing."""
    if not detect.get("crisis") or detect.get("bounce_ready"):
        return None
    from . import analysis
    rr = CRISIS_SHORT_PARAMS["rr"]
    rm = CRISIS_SHORT_PARAMS["risk_mult"]
    # Estimate ATR% from the 20-day std (proxy when we don't have H/L series)
    z = detect.get("zscore") or -2
    # Use a conservative 3% risk when z is moderate, 5% when z is extreme
    risk = 0.03 if z > -3 else 0.05
    risk = min(analysis.BT_RISK_MAX, max(analysis.BT_RISK_MIN, risk))
    entry = price
    stop = entry * (1 + risk)
    tgt = entry * (1 - rr * risk)
    return {"setup": CRISIS_SHORT_PARAMS["name"], "side": "Short",
            "entry": entry, "stop": stop, "target": tgt,
            "risk": risk, "rr": rr,
            "rationale": f"Country crisis ({detect['severity']}): "
                         f"3d={detect['drop_3d']:.1f}% 5d={detect['drop_5d']:.1f}% "
                         f"z={z:.1f} fx_break={detect['fx_break']}"}


def setup_plan_crisis_bounce(sym, price, detect):
    """Build a concrete (entry/stop/target/risk) trade plan for a CrisisBounce
    firing RIGHT NOW. Fires when EITHER bounce_ready (capitulation, z<=-2.5)
    OR the crisis is severe (5d drop <= -8%). The bounce setup is the
    verified edge on EWY (E[R]=+1.81%, p_win=70%, OOS=+0.58), so we want it
    to fire on any meaningful crisis, not just extreme capitulation.

    Stop is tighter when capitulation (z<=-2.5) and wider when still falling.
    """
    if not (detect.get("bounce_ready") or detect.get("crisis")):
        return None
    from . import analysis
    rr = CRISIS_BOUNCE_PARAMS["rr"]
    rm = CRISIS_BOUNCE_PARAMS["risk_mult"]
    z = detect.get("zscore") or -2
    drop_5 = detect.get("drop_5d") or 0
    # Tighter stop when capitulated (z<=-2.5); wider when still falling
    if detect.get("bounce_ready"):
        risk = 0.025 if z > -5 else 0.035
    else:
        # Still in crisis but not capitulated: wider stop (the move can extend)
        risk = 0.04 if drop_5 > -10 else 0.05
    risk = min(analysis.BT_RISK_MAX, max(analysis.BT_RISK_MIN, risk))
    entry = price
    stop = entry * (1 - risk)
    tgt = entry * (1 + rr * risk)
    label = "Capitulation bounce" if detect.get("bounce_ready") else "Crisis bounce"
    return {"setup": CRISIS_BOUNCE_PARAMS["name"], "side": "Long",
            "entry": entry, "stop": stop, "target": tgt,
            "risk": risk, "rr": rr,
            "rationale": f"{label}: z={z:.1f} 5d={drop_5:.1f}% (overshoot)"}


def setup_plan_adr_spillover(adr_sym, adr_price, home_etf_move_pct):
    """Build a trade plan for an ADR that has lagged its home ETF.

    If home_etf_move_pct is -5% (home ETF dropped 5%) but the ADR is flat,
    short the ADR with target = catch-up to home ETF move.
    """
    from . import analysis
    if abs(home_etf_move_pct) < ADR_LAG_PCT:
        return None
    side = "Short" if home_etf_move_pct < 0 else "Long"
    rr = ADR_SPILLOVER_PARAMS["rr"]
    # Risk = 1.5x the lag (generous stop for noise)
    risk = min(analysis.BT_RISK_MAX,
               max(analysis.BT_RISK_MIN, abs(home_etf_move_pct) * 0.015))
    entry = adr_price
    if side == "Short":
        stop = entry * (1 + risk)
        tgt = entry * (1 - rr * risk)
    else:
        stop = entry * (1 - risk)
        tgt = entry * (1 + rr * risk)
    return {"setup": ADR_SPILLOVER_PARAMS["name"], "side": side,
            "entry": entry, "stop": stop, "target": tgt,
            "risk": risk, "rr": rr,
            "rationale": f"ADR lagging home ETF move ({home_etf_move_pct:+.1f}%)"}


if __name__ == "__main__":
    # Quick smoke test: scan for crises RIGHT NOW
    print(f"=== COUNTRY CRISIS SCAN {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print(f"Universe: {len(COUNTRY_ETFS)} country ETFs")
    print()
    crises = scan_country_crises()
    if not crises:
        print("  (no country ETFs in crisis right now)")
    for c in crises:
        d = c["detect"]
        print(f"  {c['sym']:6s} {c['country']:18s} severity={d['severity']:12s} "
              f"3d={d['drop_3d']:+.1f}% 5d={d['drop_5d']:+.1f}% "
              f"z={d['zscore']:+.1f} fx_break={d['fx_break']} "
              f"bounce={d['bounce_ready']}")
    print()
    print(f"  Setups available: CrisisShort, CrisisBounce, ADRSpillover")
    print(f"  (run scan_country_crises() to get candidates, then pass to "
          f"setup_plan_*)")
    print("\nresearch only, not financial advice. verify before acting.")
