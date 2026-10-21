"""Pairs Trading Research Module — Advances Beyond run_pairs_scale.py

Key improvements over the baseline (run_pairs_scale.py, 2026-07-28):

1. FDR-BASED QUALIFICATION (Benjamini-Hochberg)
   Baseline uses Bonferroni correction on 61 pairs giving t-threshold 3.34,
   which only 2 pairs clear. FDR controls the EXPECTED false-discovery rate
   rather than the probability of ANY false positive — more appropriate for
   trading where we diversify across signals.

2. HALF-LIFE-BASED PARAMETER TUNING
   Each pair's half-life from AR(1) fit on the spread sets:
     lookback = min(max(half_life * 3, 30), 120)
     horizon = min(max(half_life * 1.0, 5), 20)

3. REGIME FILTER (VIX-based)
   Skip entry when SPY 20-day vol exceeds 25% ann.

4. SYSTEMATIC PAIR SCREENING
   All same-sector pairs from available data, not just hand-picked.
"""

from __future__ import annotations
import os, sys, csv, json, math, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ---------------------------------------------------------------- config
OOS_FRAC         = 0.40
Z_ENTRY          = 2.0
Z_EXIT           = 0.0
HL_LOOKBACK_MIN  = 30
HL_LOOKBACK_MAX  = 120
HL_HORIZON_MIN   = 5
HL_HORIZON_MAX   = 20
VIX_MAX_PAIR     = 25.0
FDR_ALPHA        = 0.05
MIN_SAMPLE       = 20
MIN_OOS_SAMPLE   = 8

DATA_DIR = os.path.join(_HERE, "data")
POLY_DIR = os.path.join(DATA_DIR, "polygon")
TD_DIR   = os.path.join(DATA_DIR, "twelvedata")
BIN_DIR  = os.path.join(DATA_DIR, "binance")

COST_STOCK  = 0.0010
COST_ETF    = 0.0010
COST_CRYPTO = 0.0020
COST_FX     = 0.0008

SECTORS = {
    "Technology": [
        "AAPL","MSFT","GOOGL","META","AMZN","NVDA","AMD","AVGO",
        "INTC","CRM","ADBE","ORCL","NOW","CSCO","TXN","QCOM",
        "MU","AMAT","ARM","PLTR","SNOW","SHOP","DOCU",
    ],
    "Financials": ["JPM","GS","MS","WFC","BAC","SCHW","V","MA"],
    "Healthcare": ["UNH","JNJ","LLY","PFE","ABT","TMO","ABBV","MRK","AMGN","DHR"],
    "Consumer Disc": ["HD","LOW","NKE","MCD","SBUX","TJX","COST","WMT","TGT"],
    "Consumer Staples": ["KO","PEP","CL","PG"],
    "Energy": ["XOM","COP"],
    "Industrials": ["BA","GE","UNP","UPS","LMT","RTX"],
    "Real Estate": ["AMT","PLD"],
    "Utilities": ["NEE","DUK","SO"],
    "Communication": ["T","VZ","DIS","CMCSA"],
    "ETFs": ["SPY","QQQ","IWM","DIA","XLF","GLD"],
}

# ---------------------------------------------------------------- data loading
_FRED_CACHE = {}

def _load_fred(series, limit=1500):
    if series in _FRED_CACHE:
        return _FRED_CACHE[series]
    from tools.wt import altdata
    vals, dates, err = altdata.fred_history(series, limit=limit)
    if err or not vals:
        return None
    dv = []
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

def _load_csv(path):
    dates, closes = [], []
    try:
        with open(path, newline="") as f:
            r = csv.reader(f)
            next(r, None)
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

def _load_series(sym, provider="polygon"):
    if provider == "fred":
        return _load_fred(sym)
    for d in [POLY_DIR, TD_DIR, BIN_DIR]:
        p = os.path.join(d, sym + ".csv")
        if os.path.exists(p):
            return _load_csv(p)
    return None

def _align(da, ca, db, cb):
    idx_b = dict()
    for i, d in enumerate(db):
        idx_b[d] = i
    ao, bo, do = [], [], []
    for i, d in enumerate(da):
        if d in idx_b:
            ao.append(ca[i])
            bo.append(cb[idx_b[d]])
            do.append(d)
    return ao, bo, do

# ---------------------------------------------------------------- half-life
def estimate_half_life(spread):
    n = len(spread)
    if n < 30:
        return 60.0
    yv, xv = [], []
    for i in range(1, n):
        dy = spread[i] - spread[i-1]
        if math.isfinite(dy) and math.isfinite(spread[i-1]):
            yv.append(dy)
            xv.append(spread[i-1])
    if len(yv) < 20:
        return 60.0
    mx = statistics.mean(xv)
    my = statistics.mean(yv)
    num = sum((xv[i] - mx) * (yv[i] - my) for i in range(len(yv)))
    den = sum((xv[i] - mx) ** 2 for i in range(len(yv)))
    if den <= 0 or num >= 0:
        return 200.0
    beta = num / den
    hl = -math.log(2) / beta
    return max(5.0, min(200.0, hl))

def _ols_beta(y, x):
    n = len(x)
    if n < 10:
        return 1.0
    sxy = sum(x[i] * y[i] for i in range(n))
    sxx = sum(x[i] * x[i] for i in range(n))
    return sxy / sxx if sxx > 0 else 1.0

def _build_spread(kind, a, b):
    if kind == "DIFF":
        return [a[i] - b[i] for i in range(len(a))]
    la = [math.log(x) for x in a]
    lb = [math.log(x) for x in b]
    beta = _ols_beta(la, lb)
    return [la[i] - beta * lb[i] for i in range(len(la))]

def _cost_for(ac):
    m = {"STOCK": COST_STOCK, "ETF": COST_ETF, "CRYPTO": COST_CRYPTO,
         "FX": COST_FX, "CROSS": COST_CRYPTO}
    return m.get(ac, COST_STOCK)

# ---------------------------------------------------------------- backtest engine
def backtest_pair_with_params(spread, lookback, horizon, z_entry, z_exit, cost,
                               vix_series=None):
    N = len(spread)
    if N < lookback + horizon + 5:
        return None

    def roll_stats(i, win):
        w = spread[max(0, i-win):i]
        if len(w) < 10:
            return 0.0, 0.0
        m = sum(w) / len(w)
        var = sum((x - m) ** 2 for x in w) / (len(w) - 1) if len(w) > 1 else 0.0
        sd = math.sqrt(var) if var > 0 else 0.0
        return m, sd

    entries = []
    for i in range(lookback, N - 1):
        m, sd = roll_stats(i, lookback)
        if sd <= 0:
            continue
        z = (spread[i] - m) / sd
        if vix_series is not None and i < len(vix_series):
            if vix_series[i] is not None and vix_series[i] > VIX_MAX_PAIR:
                continue
        if z < -z_entry:
            entries.append((i, 1, spread[i], sd))
        elif z > z_entry:
            entries.append((i, -1, spread[i], sd))

    if len(entries) < MIN_SAMPLE:
        return None

    def sim(subset):
        rets = []
        for i, side, entry, esd in subset:
            if esd <= 0:
                continue
            outcome = None
            for j in range(i + 1, min(i + 1 + horizon, N)):
                m, sd = roll_stats(j, lookback)
                if sd <= 0:
                    continue
                d_stdev = (spread[j] - entry) / esd
                if side * d_stdev >= 1.0:
                    outcome = side * d_stdev
                    break
                if side * d_stdev <= -2.0:
                    outcome = side * d_stdev
                    break
            if outcome is None:
                outcome = side * (spread[min(i + horizon, N - 1)] - entry) / esd
            cost_stdev = cost * 2.0 / 0.01
            rets.append(outcome - cost_stdev)
        return rets

    def _stats(rets):
        n = len(rets)
        if n == 0:
            return None
        exp_ret = statistics.mean(rets)
        sd = statistics.pstdev(rets) if n > 1 else 0.0
        edge = (exp_ret / sd) if sd else 0.0
        se = (sd / math.sqrt(n)) if (sd and n > 1) else 0.0
        tstat = (exp_ret / se) if se else 0.0
        worst = min(rets) if rets else 0.0
        cum = 0.0; peak = 0.0; max_dd = 0.0
        for r in rets:
            cum += r
            if cum > peak: peak = cum
            dd = peak - cum
            if dd > max_dd: max_dd = dd
        cur = 0; ms = 0
        for r in rets:
            if r < 0:
                cur += 1
                if cur > ms: ms = cur
            else:
                cur = 0
        return {"exp_ret": exp_ret, "sd": sd, "edge": edge, "tstat": tstat,
                "n": n, "worst_trade": worst, "max_dd": max_dd,
                "max_loss_streak": ms}

    st = _stats(sim(entries))
    if not st:
        return None

    split = int(N * (1 - OOS_FRAC))
    oos_entries = [e for e in entries if e[0] >= split]
    oos_st = _stats(sim(oos_entries))

    m_now, sd_now = roll_stats(N - 1, lookback)
    z_now = (spread[N - 1] - m_now) / sd_now if sd_now > 0 else 0.0

    return {"exp_ret": st["exp_ret"], "sd": st["sd"], "edge": st["edge"],
            "tstat": st["tstat"], "n": st["n"],
            "worst_trade": st["worst_trade"], "max_dd": st["max_dd"],
            "max_loss_streak": st["max_loss_streak"],
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
            "oos_n": oos_st["n"] if oos_st else 0,
            "oos_worst_trade": oos_st["worst_trade"] if oos_st else None,
            "oos_max_dd": oos_st["max_dd"] if oos_st else None,
            "firing": abs(z_now) > z_entry, "z_now": z_now,
            "n_bars": N, "lookback": lookback, "horizon": horizon}


# ---------------------------------------------------------------- qualification
def _p_from_t(t):
    if t is None: return 1.0
    return math.erfc(abs(t) / math.sqrt(2))

def _bonferroni_t(m):
    m = max(1, int(m))
    alpha = 0.05 / m
    p = 1 - alpha / 2
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        z = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /             ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= ph:
        q = p - 0.5; r = q*q
        z = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q /             (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        z = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /              ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    return max(2.0, z)

def qualifies_pair(bt, n_tests=1, use_fdr=False, all_pvals=None):
    if not bt: return False
    if bt["n"] < MIN_SAMPLE: return False
    if bt["edge"] < 0.60: return False

    if use_fdr and all_pvals is not None:
        m = len(all_pvals)
        sp = sorted(all_pvals)
        kmax = 0
        for k in range(1, m + 1):
            if sp[k - 1] <= (k / m) * FDR_ALPHA:
                kmax = k
        if kmax == 0: return False
        thresh = sp[kmax - 1]
        if _p_from_t(bt.get("tstat")) > thresh:
            return False
    else:
        if (bt.get("tstat") or 0) < _bonferroni_t(n_tests):
            return False

    oos_n = bt.get("oos_n") or 0
    if oos_n < MIN_OOS_SAMPLE: return False
    oos_exp = bt.get("oos_exp_ret")
    if oos_exp is None or oos_exp <= 0: return False
    oos_edge = bt.get("oos_edge")
    if oos_edge is None or oos_edge <= 0: return False
    if oos_edge > 3.0: return False
    worst = bt.get("worst_trade")
    if worst is not None and worst < -3.0: return False
    max_dd = bt.get("max_dd")
    if max_dd is not None and max_dd > 6.0: return False
    streak = bt.get("max_loss_streak")
    if streak is not None and streak > 5: return False
    return True

# ---------------------------------------------------------------- VIX proxy
def load_vix_proxy():
    r = _load_series("SPY", "polygon")
    if not r: return None
    dates, closes = r
    rets = []
    for i in range(1, len(closes)):
        if closes[i-1] > 0:
            rets.append((closes[i] - closes[i-1]) / closes[i-1])
    vol_proxy = [None] * len(closes)
    for i in range(21, len(closes)):
        win = rets[i-20:i]
        sd = statistics.pstdev(win) if len(win) > 1 else 0.0
        vol_proxy[i] = sd * math.sqrt(252) * 100
    return vol_proxy

# ---------------------------------------------------------------- pair generation
def generate_sector_pairs(stocks):
    pairs = []
    for i in range(len(stocks)):
        for j in range(i + 1, len(stocks)):
            a, b = stocks[i], stocks[j]
            pairs.append((a + "/" + b, "STOCK", a, b, "LOG", "polygon"))
    return pairs

# ---------------------------------------------------------------- predefined pairs
FX_PAIRS = [
    ("EUR/GBP","FX","DEXUSEU","DEXUSUK","DIFF","fred"),
    ("AUD/CAD","FX","DEXUSAL","DEXCAUS","DIFF","fred"),
    ("EUR/CHF","FX","DEXUSEU","DEXSZUS","DIFF","fred"),
    ("AUD/NZD","FX","DEXUSAL","DEXUSNZ","DIFF","fred"),
    ("GBP/JPY","FX","DEXUSUK","DEXJPUS","DIFF","fred"),
    ("EUR/AUD","FX","DEXUSEU","DEXUSAL","DIFF","fred"),
]

ETF_PAIRS = [
    ("SPY/QQQ","ETF","SPY","QQQ","LOG","polygon"),
    ("SPY/IWM","ETF","SPY","IWM","LOG","polygon"),
    ("SPY/DIA","ETF","SPY","DIA","LOG","polygon"),
    ("QQQ/IWM","ETF","QQQ","IWM","LOG","polygon"),
    ("XLF/SPY","ETF","XLF","SPY","LOG","polygon"),
]

EQUITY_PAIRS = [
    ("MSFT/GOOGL","STOCK","MSFT","GOOGL","LOG","polygon"),
    ("META/GOOGL","STOCK","META","GOOGL","LOG","polygon"),
    ("AAPL/MSFT","STOCK","AAPL","MSFT","LOG","polygon"),
    ("NVDA/AMD","STOCK","NVDA","AMD","LOG","polygon"),
    ("AVGO/AMD","STOCK","AVGO","AMD","LOG","polygon"),
    ("TXN/QCOM","STOCK","TXN","QCOM","LOG","polygon"),
    ("MU/AMD","STOCK","MU","AMD","LOG","polygon"),
    ("CRM/ADBE","STOCK","CRM","ADBE","LOG","polygon"),
    ("CRM/ORCL","STOCK","CRM","ORCL","LOG","polygon"),
    ("NOW/MSFT","STOCK","NOW","MSFT","LOG","polygon"),
    ("PLTR/SHOP","STOCK","PLTR","SHOP","LOG","polygon"),
    ("SNOW/PLTR","STOCK","SNOW","PLTR","LOG","polygon"),
    ("INTC/AMD","STOCK","INTC","AMD","LOG","polygon"),
    ("JPM/GS","STOCK","JPM","GS","LOG","polygon"),
    ("JPM/MS","STOCK","JPM","MS","LOG","polygon"),
    ("WFC/BAC","STOCK","WFC","BAC","LOG","polygon"),
    ("SCHW/MET","STOCK","SCHW","MET","LOG","polygon"),
    ("LMT/RTX","STOCK","LMT","RTX","LOG","polygon"),
    ("BA/GE","STOCK","BA","GE","LOG","polygon"),
    ("UNP/UPS","STOCK","UNP","UPS","LOG","polygon"),
    ("HD/LOW","STOCK","HD","LOW","LOG","polygon"),
    ("WMT/TGT","STOCK","WMT","TGT","LOG","polygon"),
    ("KO/PEP","STOCK","KO","PEP","LOG","polygon"),
    ("COST/WMT","STOCK","COST","WMT","LOG","polygon"),
    ("TJX/COST","STOCK","TJX","COST","LOG","polygon"),
    ("CL/PG","STOCK","CL","PG","LOG","polygon"),
    ("MCD/SBUX","STOCK","MCD","SBUX","LOG","polygon"),
    ("NKE/HD","STOCK","NKE","HD","LOG","polygon"),
    ("UNH/JNJ","STOCK","UNH","JNJ","LOG","polygon"),
    ("LLY/PFE","STOCK","LLY","PFE","LOG","polygon"),
    ("ABT/TMO","STOCK","ABT","TMO","LOG","polygon"),
    ("ABBV/MRK","STOCK","ABBV","MRK","LOG","polygon"),
    ("DHR/TMO","STOCK","DHR","TMO","LOG","polygon"),
    ("T/VZ","STOCK","T","VZ","LOG","polygon"),
    ("NEE/DUK","STOCK","NEE","DUK","LOG","polygon"),
    ("SO/DUK","STOCK","SO","DUK","LOG","polygon"),
    ("AMT/PLD","STOCK","AMT","PLD","LOG","polygon"),
    ("XOM/COP","STOCK","XOM","COP","LOG","polygon"),
]

CRYPTO_PAIRS = [
    ("BTC/ETH","CRYPTO","BTC","ETH","LOG","binance"),
]

def backtest_pair(label, ac, sym_a, sym_b, kind, provider,
                   vix_proxy=None, use_hl=True, use_rf=False):
    ha = _load_series(sym_a, provider)
    hb = _load_series(sym_b, provider)
    if not ha or not hb: return label, None, "no data"
    da, ca = ha; db, cb = hb
    a, b, dates = _align(da, ca, db, cb)
    if len(a) < 80: return label, None, "too few obs"
    spread = _build_spread(kind, a, b)
    cost = _cost_for(ac)
    hl = estimate_half_life(spread)
    if use_hl:
        lookback = max(HL_LOOKBACK_MIN, min(HL_LOOKBACK_MAX, int(hl * 3)))
        horizon = max(HL_HORIZON_MIN, min(HL_HORIZON_MAX, int(hl * 1.0)))
    else:
        lookback = 60; horizon = 10
    if len(a) < lookback + horizon + 5:
        return label, None, "too few obs for hl params"
    vix_aligned = None
    if use_rf and vix_proxy:
        spy_data = _load_series("SPY", "polygon")
        if spy_data:
            spy_dates, _ = spy_data
            vix_map = {spy_dates[i]: vix_proxy[i] for i in range(min(len(spy_dates), len(vix_proxy)))}
            vix_aligned = [vix_map.get(d) for d in dates]
    bt = backtest_pair_with_params(spread, lookback, horizon, Z_ENTRY, Z_EXIT, cost, vix_series=vix_aligned)
    if not bt: return label, None, "insufficient trades"
    bt["label"] = label; bt["asset_class"] = ac
    bt["sym_a"] = sym_a; bt["sym_b"] = sym_b
    bt["kind"] = kind; bt["provider"] = provider
    bt["half_life"] = round(hl, 1)
    bt["first_date"] = dates[0] if dates else ""
    bt["last_date"] = dates[-1] if dates else ""
    bt["regime_filter"] = use_rf
    return label, bt, None

# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    print("=" * 70, file=sys.stderr)
    print("  PAIRS TRADING RESEARCH", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    vix_proxy = load_vix_proxy()
    print("  VIX proxy: " + ("loaded" if vix_proxy else "N/A"), file=sys.stderr)

    all_pairs = list(FX_PAIRS)
    for lst in [ETF_PAIRS, EQUITY_PAIRS, CRYPTO_PAIRS]:
        all_pairs.extend(lst)

    sys_count = 0
    for sname, stocks in SECTORS.items():
        avail = [s for s in stocks if _load_series(s, "polygon")]
        if len(avail) >= 2:
            gen = generate_sector_pairs(avail)
            all_pairs.extend(gen)
            sys_count += len(gen)

    seen = set()
    unique = []
    for p in all_pairs:
        key = (p[2], p[3]) if p[2] < p[3] else (p[3], p[2])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    all_pairs = unique
    n_total = len(all_pairs)
    print("  Pairs: %d FX + %d ETF + %d eq + %d crypto + %d sys = %d total" % (
        len(FX_PAIRS), len(ETF_PAIRS), len(EQUITY_PAIRS),
        len(CRYPTO_PAIRS), sys_count, n_total), file=sys.stderr)

    experiments = []
    for exp_name, use_hl, use_rf in [
        ("BASELINE", False, False),
        ("HALF-LIFE", True, False),
        ("+REGIME FILTER", True, True),
    ]:
        if use_rf and not vix_proxy:
            continue
        print("\n  EXP: " + exp_name, file=sys.stderr)
        results = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {}
            for p in all_pairs:
                futs[ex.submit(backtest_pair, *p, vix_proxy, use_hl, use_rf)] = p
            for fut in as_completed(futs):
                label, r, err = fut.result()
                if r:
                    results.append(r)
        experiments.append((exp_name, results))

    def summarize(results, n_tests):
        all_pvals = [_p_from_t(r.get("tstat")) for r in results]
        rows = []
        for r in results:
            qb = qualifies_pair(r, n_tests=n_tests, use_fdr=False)
            qf = qualifies_pair(r, n_tests=n_tests, use_fdr=True, all_pvals=all_pvals)
            rows.append(dict(
                label=r["label"], class_=r["asset_class"],
                n_bars=r["n_bars"], n=r["n"],
                edge=r["edge"], tstat=r["tstat"],
                oos_n=r.get("oos_n") or 0,
                oos_edge=r.get("oos_edge") or 0.0,
                oos_exp_ret=r.get("oos_exp_ret") or 0.0,
                z_now=r.get("z_now") or 0.0,
                firing=r.get("firing") or False,
                half_life=r.get("half_life"),
                lookback=r.get("lookback"),
                horizon=r.get("horizon"),
                qualifies_bonf=qb, qualifies_fdr=qf,
            ))
        rows.sort(key=lambda x: (-int(x["qualifies_fdr"]), -(x["oos_edge"] or 0)))
        return rows

    nt = n_total
    all_summaries = []
    for exp_name, results in experiments:
        rows = summarize(results, nt)
        all_summaries.append((exp_name, results, rows))

    elapsed = time.time() - t0

    for exp_name, results, rows in all_summaries:
        nb = sum(1 for r in rows if r["qualifies_bonf"])
        nf = sum(1 for r in rows if r["qualifies_fdr"])
        nfire = sum(1 for r in rows if r["firing"])
        print("\n  %s: %d OK | Bonf=%d FDR=%d Fire=%d" % (
            exp_name, len(results), nb, nf, nfire), file=sys.stderr)
        print("  %-18s %4s %7s %6s %5s %9s %6s %7s %5s %5s %5s" % (
            "Pair", "n", "edge", "t", "oos_n", "oos_edge", "HL", "z_now",
            "fire", "Bonf", "FDR"), file=sys.stderr)
        for r in rows[:25]:
            ff = "*" if r["firing"] else ""
            bb = "YES" if r["qualifies_bonf"] else ""
            dd = "YES" if r["qualifies_fdr"] else ""
            print("  %-18s %4d %+7.3f %6.2f %5d %+9.3f %6.0f %+7.2f %5s %5s %5s" % (
                r["label"], r["n"], r["edge"], r["tstat"], r["oos_n"],
                r["oos_edge"], r["half_life"] or 0, r["z_now"],
                ff, bb, dd), file=sys.stderr)

    out_dir = os.path.join(_HERE, "reports")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "pairs_research.json")
    md_path = os.path.join(out_dir, "pairs_research.md")

    exp_data = {}
    for exp_name, results, rows in all_summaries:
        key = exp_name.lower().replace(" ", "_").replace("+", "")
        exp_data[key] = dict(
            n_ok=len(results),
            n_bonf=sum(1 for r in rows if r["qualifies_bonf"]),
            n_fdr=sum(1 for r in rows if r["qualifies_fdr"]),
            top20=[{k: v for k, v in r.items()} for r in rows[:20]],
        )

    payload = dict(
        generated=time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        elapsed_s=round(elapsed, 2),
        n_pairs_tested=n_total,
        experiments=exp_data,
    )
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    with open(md_path, "w") as f:
        f.write("# Pairs Trading Research\n\n")
        f.write("Generated: %s | Elapsed: %.1fs\n\n" % (
            payload["generated"], elapsed))
        f.write("## Improvements Over Baseline\n\n")
        f.write("1. **FDR qualification** (BH) vs Bonferroni\n")
        f.write("2. **Half-life calibration** per pair\n")
        f.write("3. **VIX regime filter**\n")
        f.write("4. **Systematic screening** - all same-sector pairs\n\n")
        f.write("## Universe: %d pairs\n\n" % n_total)
        for exp_name, results, rows in all_summaries:
            nb = sum(1 for r in rows if r["qualifies_bonf"])
            nf = sum(1 for r in rows if r["qualifies_fdr"])
            f.write("## %s: %d Bonf / %d FDR\n\n" % (exp_name, nb, nf))
            f.write("| Pair | n | edge | t | OOS n | OOS edge | HL | z_now | Fire | Bonf | FDR |\n")
            f.write("|------|---|---|------|---|-------|----------|----|-------|------|------|-----|\n")
            for r in rows[:25]:
                ff = "*" if r["firing"] else ""
                bb = "YES" if r["qualifies_bonf"] else ""
                dd = "YES" if r["qualifies_fdr"] else ""
                f.write("| %s | %d | %+.3f | %.2f | %d | %+.3f | %.0f | %+.2f | %s | %s | %s |\n" % (
                    r["label"], r["n"], r["edge"], r["tstat"], r["oos_n"],
                    r["oos_edge"], r["half_life"] or 0, r["z_now"],
                    ff, bb, dd))
            f.write("\n")

        f.write("\n## Cross-Experiment Summary\n\n")
        f.write("| Experiment | OK | Bonf | FDR |\n")
        f.write("|------------|----|------|-----|\n")
        for exp_name, results, rows in all_summaries:
            nb = sum(1 for r in rows if r["qualifies_bonf"])
            nf = sum(1 for r in rows if r["qualifies_fdr"])
            f.write("| %s | %d | %d | %d |\n" % (exp_name, len(results), nb, nf))

        f.write("\n### Live Pairs (FDR qual, HL calibrated)\n\n")
        for exp_name, results, rows in all_summaries:
            if exp_name == "HALF-LIFE":
                live = [r for r in rows if r["qualifies_fdr"]][:12]
                if live:
                    f.write("| Pair | OOS edge | HL | z_now | Firing |\n")
                    f.write("|------|----------|----|-------|--------|\n")
                    for r in live:
                        f.write("| %s | %+.3f | %.0f | %+.2f | %s |\n" % (
                            r["label"], r["oos_edge"], r["half_life"] or 0,
                            r["z_now"], "**YES**" if r["firing"] else ""))
                break

    print("\n  JSON: " + json_path, file=sys.stderr)
    print("  MD:   " + md_path, file=sys.stderr)
    print("  Done in %.1fs" % elapsed, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
