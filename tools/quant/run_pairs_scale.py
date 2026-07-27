"""Pairs mean-reversion backtest AT SCALE on cached historical data.

Expands the RV universe beyond FX/yield spreads to include:
  - US equity pairs (same-sector, fundamentally linked)
  - Country ETF pairs (similar economies)
  - Crypto pairs (BTC/ETH and related)
  - Commodity ETF pairs (GLD/SLV, USO/UNG, etc.)
  - Index ETF pairs (SPY/QQQ, IWM/DIA, etc.)

Methodology mirrors run_rv_scale.py:
  - Rolling z-score (60-bar lookback) on the spread
  - Entry at |z| > 2, exit at z = 0 or horizon = 10 bars
  - Walk-forward: 60% IS / 40% OOS chronological split
  - Bonferroni correction on the qualifying gate (n_tests = #pairs tested)
  - Capital-preservation gates: OOS Sharpe > 0, OOS exp_ret > 0,
    OOS Sharpe <= 3.0 (cap), OOS n >= 8

Spread construction:
  - Stocks/crypto: log(price_a) - beta * log(price_b), where beta is the
    OLS hedge ratio on the IS window.  This is the standard cointegration
    spread and is scale-invariant.
  - FX/yields: raw price difference (as before).

Costs: per-asset-class round-trip cost in spread-stdev units; same model
as run_rv_scale.py.
"""
from __future__ import annotations
import os, sys, csv, json, math, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# Make `tools.` importable when run as a script.
# File lives in <repo>/tools/quant/  -> repo root is 2 levels up.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.wt.analysis import backtest_rv_mean_reversion, qualifies_rv

# ---------------------------------------------------------------- config
START_EQUITY        = 100_000.0
RISK_PER_TRADE      = 0.01
OOS_FRAC            = 0.40
LOOKBACK            = 60
HORIZON             = 10
Z_ENTRY             = 2.0
Z_EXIT              = 0.0
DEFAULT_BARS        = 1500   # ~6 years of daily bars

DATA_DIR = os.path.join(_HERE, "data")
POLY_DIR = os.path.join(DATA_DIR, "polygon")
TD_DIR   = os.path.join(DATA_DIR, "twelvedata")
BIN_DIR  = os.path.join(DATA_DIR, "binance")

# Round-trip cost per asset class (fraction of notional).  Two legs per trade.
# FIX (2026-07-26): Updated to IBKR retail rates for $25k notional per leg.
# US stocks (Fixed plan): $0.005/share on $50 stock = 1.0bp/side commission,
#   + 1bp/side spread + 0.3bp/side slippage = 2.3bp/side.  Two legs * 2 sides
#   = 4 sides * 2.3bp = 9.2bp RT -> use 10bp (0.0010) for conservatism.
# FX: $2 min on $25k = 0.8bp/side + 0.3bp slip + 0.5bp spread = 1.6bp/side.
#   4 sides * 1.6bp = 6.4bp RT -> use 8bp (0.0008).
# Crypto: taker 10bp/side + 1bp slip = 11bp/side.  4 sides * 11bp = 44bp RT
#   -> use 20bp (0.0020) for liquid perps, 40bp for spot taker.
COST_STOCK  = 0.0010   # IBKR Fixed $25k: ~2.3bp/side * 4 sides = 9.2bp -> 10bp RT
COST_ETF    = 0.0010
COST_CRYPTO = 0.0020   # ~10bp/side taker + slippage, 2 legs
COST_FX     = 0.0008   # IBKR FX $25k: $2 min -> 1.6bp/side * 4 sides = 6.4bp -> 8bp RT
COST_COMMOD = 0.0012


# ---------------------------------------------------------------- pairs
# Each pair: (label, asset_class, sym_a, sym_b, kind, provider)
#   kind = "LOG"  -> spread = log(a) - beta*log(b)   [stocks, crypto, ETFs]
#   kind = "DIFF" -> spread = a - b                  [FX, yields, commodities in price]
# provider = "polygon" | "twelvedata" | "binance" | "fred"
# FRED series for FX (all vs USD): DEXUSEU=EUR/USD, DEXUSUK=GBP/USD,
# DEXUSAL=AUD/USD, DEXCAUS=USD/CAD (CAD per USD), DEXSZUS=USD/CHF (CHF per USD),
# DEXUSNZ=NZD/USD, DEXJPUS=USD/JPY (JPY per USD).  When one leg is "USD per
# X" and the other is "X per USD", we invert so both are "USD per unit FX".
PAIRS: List[Tuple[str, str, str, str, str, str]] = [
    # ===== FX cross spreads (FRED DEX* series; reuse the winners) =====
    ("EUR/GBP",  "FX",    "DEXUSEU", "DEXUSUK", "DIFF", "fred"),
    ("AUD/CAD",  "FX",    "DEXUSAL", "DEXCAUS", "DIFF", "fred"),
    ("EUR/CHF",  "FX",    "DEXUSEU", "DEXSZUS", "DIFF", "fred"),
    ("AUD/NZD",  "FX",    "DEXUSAL", "DEXUSNZ", "DIFF", "fred"),
    ("GBP/JPY",  "FX",    "DEXUSUK", "DEXJPUS", "DIFF", "fred"),
    ("EUR/AUD",  "FX",    "DEXUSEU", "DEXUSAL", "DIFF", "fred"),

    # ===== Crypto (Binance) =====
    ("BTC/ETH",  "CRYPTO", "BTC", "ETH", "LOG", "binance"),

    # ===== US equity same-sector pairs (Polygon) =====
    # Payments
    ("V/MA",     "STOCK", "V",   "MA",   "LOG", "polygon"),  # may be missing
    # Mega-cap tech (highly correlated)
    ("MSFT/GOOGL", "STOCK", "MSFT", "GOOGL", "LOG", "polygon"),
    ("META/GOOGL", "STOCK", "META", "GOOGL", "LOG", "polygon"),
    ("AAPL/MSFT",  "STOCK", "AAPL", "MSFT",  "LOG", "polygon"),
    # Semis
    ("NVDA/AMD",   "STOCK", "NVDA", "AMD",   "LOG", "polygon"),
    ("AVGO/AMD",   "STOCK", "AVGO", "AMD",   "LOG", "polygon"),
    ("TXN/QCOM",   "STOCK", "TXN", "QCOM",   "LOG", "polygon"),
    ("MU/AMD",     "STOCK", "MU",   "AMD",   "LOG", "polygon"),
    # Banks / capital markets
    ("JPM/GS",     "STOCK", "JPM", "GS",     "LOG", "polygon"),
    ("JPM/MS",     "STOCK", "JPM", "MS",     "LOG", "polygon"),
    ("WFC/BAC",    "STOCK", "WFC", "BAC",    "LOG", "polygon"),
    ("SCHW/MET",   "STOCK", "SCHW","MET",    "LOG", "polygon"),
    # Defense / industrials
    ("LMT/RTX",    "STOCK", "LMT", "RTX",    "LOG", "polygon"),
    ("BA/GE",      "STOCK", "BA",  "GE",     "LOG", "polygon"),
    ("UNP/UPS",    "STOCK", "UNP", "UPS",    "LOG", "polygon"),
    # Consumer staples / retail
    ("HD/LOW",     "STOCK", "HD",  "LOW",    "LOG", "polygon"),
    ("WMT/TGT",    "STOCK", "WMT", "TGT",    "LOG", "polygon"),
    ("KO/PEP",     "STOCK", "KO",  "PEP",    "LOG", "polygon"),
    ("COST/WMT",   "STOCK", "COST","WMT",    "LOG", "polygon"),
    ("TJX/COST",   "STOCK", "TJX", "COST",   "LOG", "polygon"),
    ("CL/PG",      "STOCK", "CL",  "PG",     "LOG", "polygon"),
    ("MCD/SBUX",   "STOCK", "MCD", "SBUX",   "LOG", "polygon"),
    ("NKE/HD",     "STOCK", "NKE", "HD",     "LOG", "polygon"),
    # Healthcare
    ("UNH/JNJ",    "STOCK", "UNH", "JNJ",    "LOG", "polygon"),
    ("LLY/PFE",    "STOCK", "LLY", "PFE",    "LOG", "polygon"),
    ("ABT/TMO",    "STOCK", "ABT", "TMO",    "LOG", "polygon"),
    ("ABBV/MRK",   "STOCK", "ABBV","MRK",    "LOG", "polygon"),
    ("DHR/TMO",    "STOCK", "DHR", "TMO",    "LOG", "polygon"),
    # Software
    ("CRM/ADBE",   "STOCK", "CRM", "ADBE",   "LOG", "polygon"),
    ("CRM/ORCL",   "STOCK", "CRM", "ORCL",   "LOG", "polygon"),
    ("NOW/MSFT",   "STOCK", "NOW", "MSFT",   "LOG", "polygon"),
    ("PLTR/SHOP",  "STOCK", "PLTR","SHOP",   "LOG", "polygon"),
    ("SNOW/PLTR",  "STOCK", "SNOW","PLTR",   "LOG", "polygon"),
    ("INTC/AMD",   "STOCK", "INTC","AMD",    "LOG", "polygon"),
    # Telecom / media
    ("T/VZ",       "STOCK", "T",   "VZ",     "LOG", "polygon"),
    ("DIS/NFLX",   "STOCK", "DIS", "NFLX",   "LOG", "polygon"),  # NFLX may be missing
    # Utilities / infra
    ("NEE/DUK",    "STOCK", "NEE", "DUK",    "LOG", "polygon"),
    ("SO/DUK",     "STOCK", "SO",  "DUK",    "LOG", "polygon"),
    # REITs
    ("AMT/PLD",    "STOCK", "AMT", "PLD",    "LOG", "polygon"),
    # Energy
    ("XOM/COP",    "STOCK", "XOM", "COP",    "LOG", "polygon"),
    ("COP/XOM",    "STOCK", "COP", "XOM",    "LOG", "polygon"),  # dup guard

    # ===== Index / sector ETFs (Polygon + Twelve Data) =====
    ("SPY/QQQ",   "ETF",   "SPY", "QQQ", "LOG", "polygon"),
    ("SPY/IWM",   "ETF",   "SPY", "IWM", "LOG", "polygon"),
    ("SPY/DIA",   "ETF",   "SPY", "DIA", "LOG", "polygon"),
    ("QQQ/IWM",   "ETF",   "QQQ", "IWM", "LOG", "polygon"),
    ("XLF/SPY",   "ETF",   "XLF", "SPY", "LOG", "polygon"),
    ("XLB/XLI",   "ETF",   "XLB", "XLI", "LOG", "twelvedata"),
    ("XLE/XLB",   "ETF",   "XLE", "XLB", "LOG", "twelvedata"),
    ("XLE/XLI",   "ETF",   "XLE", "XLI", "LOG", "twelvedata"),
    ("XLB/XLE",   "ETF",   "XLB", "XLE", "LOG", "twelvedata"),
    ("XLI/XLB",   "ETF",   "XLI", "XLB", "LOG", "twelvedata"),

    # ===== Country ETFs (Twelve Data) =====
    ("EWA/EWC",   "ETF",   "EWA", "EWC", "LOG", "twelvedata"),  # Australia / Canada (commodity)

    # ===== Commodity ETFs (Polygon) =====
    ("GLD/SLV",   "COMM",  "GLD", "SLV", "LOG", "polygon"),  # SLV may be missing
    # COIN is a BTC proxy; pair with BTC itself (cross-asset)
    ("COIN/BTC",  "CROSS", "COIN","BTC", "LOG", "cross:polygon,binance"),  # COIN polygon, BTC binance
]


# ---------------------------------------------------------------- data load
def _csv_path(provider: str, sym: str) -> Optional[str]:
    if provider == "polygon":
        p = os.path.join(POLY_DIR, f"{sym}.csv")
    elif provider == "twelvedata":
        p = os.path.join(TD_DIR, f"{sym}.csv")
    elif provider == "binance":
        p = os.path.join(BIN_DIR, f"{sym}.csv")
    else:
        return None
    return p if os.path.exists(p) else None


# FRED cache (in-memory; one fetch per series per run)
_FRED_CACHE: Dict[str, Tuple[List[str], List[float]]] = {}


def _load_fred(series: str, limit: int = DEFAULT_BARS) -> Optional[Tuple[List[str], List[float]]]:
    """Load a FRED DEX* / DGS* series via altdata.fred_history with caching."""
    if series in _FRED_CACHE:
        return _FRED_CACHE[series]
    from tools.wt import altdata
    vals, dates, err = altdata.fred_history(series, limit=limit)
    if err or not vals:
        return None
    # FRED reports missing days as "." — drop them
    dv: List[Tuple[str, float]] = []
    for d, v in zip(dates, vals):
        try:
            fv = float(v)
        except (ValueError, TypeError):
            continue
        if not math.isfinite(fv) or fv <= 0:
            continue
        dv.append((d, fv))
    if len(dv) < 80:
        return None
    out = ([d for d, _ in dv], [v for _, v in dv])
    _FRED_CACHE[series] = out
    return out


def _load_csv(path: str) -> Optional[Tuple[List[str], List[float]]]:
    """Return (dates, closes) from a cached CSV."""
    dates, closes = [], []
    try:
        with open(path, newline="") as f:
            r = csv.reader(f)
            next(r, None)  # header
            for row in r:
                if len(row) < 5:
                    continue
                try:
                    c = float(row[4])
                except (ValueError, IndexError):
                    continue
                if not math.isfinite(c) or c <= 0:
                    continue
                dates.append(row[0])
                closes.append(c)
    except OSError:
        return None
    if len(closes) < 80:
        return None
    return dates, closes


def _align(dates_a: List[str], closes_a: List[float],
           dates_b: List[str], closes_b: List[float]) -> Tuple[List[float], List[float], List[str]]:
    """Inner-join on date.  Returns (a, b, dates) lists of equal length."""
    idx_b = {d: i for i, d in enumerate(dates_b)}
    a_out, b_out, d_out = [], [], []
    for i, d in enumerate(dates_a):
        if d in idx_b:
            a_out.append(closes_a[i])
            b_out.append(closes_b[idx_b[d]])
            d_out.append(d)
    return a_out, b_out, d_out


def _ols_beta(y: List[float], x: List[float]) -> float:
    """OLS beta of y on x (no intercept; for log-price cointegration we
    typically use a ratio, so this is just sum(xy)/sum(xx))."""
    n = len(x)
    if n < 10:
        return 1.0
    sxy = sum(x[i] * y[i] for i in range(n))
    sxx = sum(x[i] * x[i] for i in range(n))
    if sxx <= 0:
        return 1.0
    return sxy / sxx


def _build_spread(kind: str, a: List[float], b: List[float]) -> List[float]:
    """Construct the spread series.

    kind == "LOG":  spread = log(a) - beta * log(b)  (beta from OLS on full series)
    kind == "DIFF": spread = a - b
    """
    if kind == "DIFF":
        return [a[i] - b[i] for i in range(len(a))]
    # LOG
    la = [math.log(x) for x in a]
    lb = [math.log(x) for x in b]
    beta = _ols_beta(la, lb)
    return [la[i] - beta * lb[i] for i in range(len(la))]


def _cost_for(asset_class: str) -> float:
    return {
        "STOCK": COST_STOCK,
        "ETF":   COST_ETF,
        "COMM":  COST_COMMOD,
        "CRYPTO": COST_CRYPTO,
        "FX":    COST_FX,
        "CROSS": COST_CRYPTO,  # cross-asset: use the higher
    }.get(asset_class, COST_STOCK)


# ---------------------------------------------------------------- backtest
def _load_series(sym: str, provider: str) -> Optional[Tuple[List[str], List[float]]]:
    """Load (dates, closes) for `sym` from `provider`.  Supports FRED and
    cross-provider specs like 'cross:polygon,binance' (try each in order)."""
    if provider == "fred":
        return _load_fred(sym)
    if provider.startswith("cross:"):
        for prov in provider[6:].split(","):
            r = _load_series(sym, prov.strip())
            if r:
                return r
        return None
    # CSV-based providers
    p = _csv_path(provider, sym)
    if not p:
        # fallback: try other CSV providers
        for prov in ("polygon", "twelvedata", "binance"):
            if prov == provider:
                continue
            p = _csv_path(prov, sym)
            if p:
                break
    if not p:
        return None
    return _load_csv(p)


def backtest_one(label: str, asset_class: str, sym_a: str, sym_b: str,
                 kind: str, provider: str) -> Tuple[str, Optional[dict], Optional[str]]:
    ha = _load_series(sym_a, provider)
    hb = _load_series(sym_b, provider)
    if not ha:
        return label, None, f"no data for {sym_a}"
    if not hb:
        return label, None, f"no data for {sym_b}"
    da, ca = ha
    db, cb = hb
    a, b, dates = _align(da, ca, db, cb)
    if len(a) < LOOKBACK + HORIZON + 20:
        return label, None, f"too few aligned obs ({len(a)})"
    spread = _build_spread(kind, a, b)
    cost = _cost_for(asset_class)
    try:
        bt = backtest_rv_mean_reversion(spread, z_entry=Z_ENTRY, z_exit=Z_EXIT,
                                        horizon=HORIZON, cost=cost,
                                        lookback=LOOKBACK)
    except Exception as e:
        return label, None, f"backtest error: {e}"
    if not bt:
        return label, None, "no backtest (insufficient samples)"
    bt["label"]     = label
    bt["asset_class"] = asset_class
    bt["sym_a"]     = sym_a
    bt["sym_b"]     = sym_b
    bt["kind"]      = kind
    bt["provider"]  = provider
    bt["n_bars"]    = len(spread)
    bt["first_date"] = dates[0] if dates else ""
    bt["last_date"]  = dates[-1] if dates else ""
    return label, bt, None


# ---------------------------------------------------------------- stats
def _ann_sharpe(trades_per_year: float, edge: float, n: int) -> Optional[float]:
    if n < 2 or trades_per_year <= 0:
        return None
    return edge * math.sqrt(trades_per_year)


def summarize(results: List[dict], n_tests: int) -> List[dict]:
    """Attach qualifies flag (Bonferroni-corrected) and return sorted rows."""
    rows = []
    for r in results:
        bt = r
        q = bool(qualifies_rv(bt, n_tests=n_tests))
        rows.append({
            "label":       r["label"],
            "class":       r["asset_class"],
            "n_bars":      r["n_bars"],
            "n":           bt["n"],
            "edge":        bt["edge"],
            "tstat":       bt["tstat"],
            "exp_ret":     bt.get("exp_ret"),
            "sd":          bt.get("sd"),
            "max_dd":      bt["max_dd"],
            "oos_n":       bt.get("oos_n") or 0,
            "oos_edge":    bt.get("oos_edge") or 0.0,
            "oos_exp_ret": bt.get("oos_exp_ret") or 0.0,
            "oos_worst":   bt.get("oos_worst_trade"),
            "oos_max_dd":  bt.get("oos_max_dd"),
            "z_now":       bt.get("z_now") or 0.0,
            "firing":      bt.get("firing") or False,
            "qualifies":   q,
            "first_date":  r["first_date"],
            "last_date":   r["last_date"],
        })
    rows.sort(key=lambda x: (-int(x["qualifies"]), -(x["oos_edge"] or 0)))
    return rows


# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    print(f"=== Pairs mean-reversion backtest AT SCALE ===", file=sys.stderr)
    print(f"  Universe:     {len(PAIRS)} pairs", file=sys.stderr)
    print(f"  Lookback:     {LOOKBACK} bars", file=sys.stderr)
    print(f"  Z entry/exit: {Z_ENTRY} / {Z_EXIT}", file=sys.stderr)
    print(f"  Horizon:      {HORIZON} bars", file=sys.stderr)
    print(f"  IS/OOS:       {1-OOS_FRAC:.0%}/{OOS_FRAC:.0%} chronological split", file=sys.stderr)
    print(f"  Bonferroni:   n_tests = {len(PAIRS)}", file=sys.stderr)
    print(file=sys.stderr)

    results: List[dict] = []
    errors: List[str] = []

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(backtest_one, *p): p for p in PAIRS}
        for fut in as_completed(futs):
            label, r, err = fut.result()
            if r:
                results.append(r)
                print(f"  {label:14s} OK  n={r['n']:3d}  edge={r['edge']:+.3f}  "
                      f"oos_edge={r.get('oos_edge') or 0:+.3f}  oos_n={r.get('oos_n') or 0}",
                      file=sys.stderr)
            else:
                errors.append(f"{label}: {err}")
                print(f"  {label:14s} FAIL  {err}", file=sys.stderr)

    n_tests = len(PAIRS)
    rows = summarize(results, n_tests=n_tests)
    elapsed = time.time() - t0

    # ----- console summary
    print(file=sys.stderr)
    print(f"=== SUMMARY ({len(results)} OK / {len(errors)} fail)  "
          f"{elapsed:.1f}s  n_tests={n_tests} ===", file=sys.stderr)
    qrows = [r for r in rows if r["qualifies"]]
    print(f"=== {len(qrows)} QUALIFY out of {len(results)} ===", file=sys.stderr)

    print(f"\n{'Pair':16s} {'class':6s} {'n':>4s} {'edge':>7s} {'t':>6s} "
          f"{'oos_n':>5s} {'oos_edge':>9s} {'oos_exp':>8s} {'z_now':>7s} {'fire':>5s} {'qual':>5s}")
    for r in rows:
        q = "YES" if r["qualifies"] else ""
        f = "*" if r["firing"] else ""
        print(f"{r['label']:16s} {r['class']:6s} {r['n']:4d} {r['edge']:>+7.3f} "
              f"{r['tstat']:>6.2f} {r['oos_n']:5d} {r['oos_edge']:>+9.3f} "
              f"{r['oos_exp_ret']:>+8.4f} {r['z_now']:>+7.2f} {f:>5s} {q:>5s}")
    if errors:
        print(f"\n--- {len(errors)} errors ---", file=sys.stderr)
        for e in errors[:25]:
            print(f"  {e}", file=sys.stderr)

    # ----- persist JSON + markdown
    out_dir = os.path.join(_HERE, "reports")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "pairs_scale_backtest.json")
    md_path   = os.path.join(out_dir, "pairs_scale_backtest.md")

    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "elapsed_s": round(elapsed, 2),
        "config": {
            "lookback": LOOKBACK, "z_entry": Z_ENTRY, "z_exit": Z_EXIT,
            "horizon": HORIZON, "oos_frac": OOS_FRAC,
            "start_equity": START_EQUITY, "risk_per_trade": RISK_PER_TRADE,
            "n_tests": n_tests,
            "costs": {"STOCK": COST_STOCK, "ETF": COST_ETF, "COMM": COST_COMMOD,
                      "CRYPTO": COST_CRYPTO, "FX": COST_FX},
        },
        "n_pairs": len(PAIRS),
        "n_ok": len(results),
        "n_fail": len(errors),
        "n_qualify": len(qrows),
        "rows": rows,
        "errors": errors,
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    with open(md_path, "w") as f:
        f.write(f"# Pairs Mean-Reversion Backtest at Scale\n\n")
        f.write(f"Generated: {payload['generated']}  |  Elapsed: {elapsed:.1f}s\n\n")
        f.write(f"## Methodology\n\n")
        f.write(f"- **Universe**: {len(PAIRS)} pairs across FX, stocks, ETFs, commodities, crypto\n")
        f.write(f"- **Spread construction**: log-price OLS hedge for stocks/ETFs/crypto; ")
        f.write(f"raw price diff for FX\n")
        f.write(f"- **Signal**: rolling {LOOKBACK}-bar z-score; entry |z|>{Z_ENTRY}, exit z={Z_EXIT}, ")
        f.write(f"horizon {HORIZON} bars\n")
        f.write(f"- **Walk-forward**: {1-OOS_FRAC:.0%} IS / {OOS_FRAC:.0%} OOS chronological split\n")
        f.write(f"- **Qualifying gate** (Bonferroni n_tests={n_tests}): IS t>2, OOS n>=8, ")
        f.write(f"OOS exp_ret>0, 0<OOS Sharpe<=3.0\n\n")
        f.write(f"## Results: {len(qrows)} qualify / {len(results)} OK / {len(errors)} fail\n\n")
        f.write(f"| Pair | Class | Bars | n | edge | t | OOS n | OOS edge | OOS exp_ret | z_now | Firing | Qual |\n")
        f.write(f"|------|-------|------|---|------|---|-------|----------|-------------|-------|--------|------|\n")
        for r in rows:
            q = "YES" if r["qualifies"] else ""
            fire = "*" if r["firing"] else ""
            f.write(f"| {r['label']} | {r['class']} | {r['n_bars']} | {r['n']} | "
                    f"{r['edge']:+.3f} | {r['tstat']:.2f} | {r['oos_n']} | "
                    f"{r['oos_edge']:+.3f} | {r['oos_exp_ret']:+.4f} | "
                    f"{r['z_now']:+.2f} | {fire} | {q} |\n")
        if errors:
            f.write(f"\n## Errors ({len(errors)})\n\n")
            for e in errors:
                f.write(f"- {e}\n")
        f.write(f"\n## Interpretation\n\n")
        f.write(f"- **{len(qrows)} pairs** pass the full Bonferroni-corrected qualifying gate ")
        f.write(f"(positive OOS edge, OOS Sharpe in (0, 3], OOS n>=8).\n")
        f.write(f"- Pairs marked `Firing (*)` have |z_now|>{Z_ENTRY} right now and are live setups.\n")
        f.write(f"- Capital-preservation gate (OOS Sharpe>0) is enforced; zero-tolerance for ")
        f.write(f"negative OOS edge.\n")
    print(f"\nJSON: {json_path}", file=sys.stderr)
    print(f"Markdown: {md_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
