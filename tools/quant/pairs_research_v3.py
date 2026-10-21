
"""Pairs Trading Research v3 -- Unified Kalman + Portfolio Construction + Rolling WF

v1: Systematic screening, half-life calibration, VIX regime filter, FDR
v2: Kalman dynamic hedge ratio, Engle-Granger cointegration, FX-specific gates
v3: Portfolio-level allocation (risk parity, min-variance, equal-weight),
     rolling walk-forward backtest, multi-exit comparison, correlation analysis
"""

from __future__ import annotations
import os, sys, csv, json, math, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ================================================================ CONFIG
OOS_FRAC = 0.40
Z_ENTRY = 2.0
Z_EXIT = 0.0
HL_LOOKBACK_MIN = 30
HL_LOOKBACK_MAX = 120
HL_HORIZON_MIN = 5
HL_HORIZON_MAX = 20
VIX_MAX_PAIR = 25.0
FDR_ALPHA = 0.05
MIN_SAMPLE = 20
MIN_OOS_SAMPLE = 8

KALMAN_DELTA = 1e-5
KALMAN_VT = 1e-3
EG_MAX_LAG = 5

DATA_DIR = os.path.join(_HERE, "data")
POLY_DIR = os.path.join(DATA_DIR, "polygon")
TD_DIR = os.path.join(DATA_DIR, "twelvedata")
BIN_DIR = os.path.join(DATA_DIR, "binance")

COST_STOCK = 0.0010
COST_ETF = 0.0010
COST_CRYPTO = 0.0020
COST_FX = 0.0008

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

# ================================================================ DATA LOADING
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
    idx_b = {}
    for i, d in enumerate(db):
        idx_b[d] = i
    ao, bo, do = [], [], []
    for i, d in enumerate(da):
        if d in idx_b:
            ao.append(ca[i])
            bo.append(cb[idx_b[d]])
            do.append(d)
    return ao, bo, do

# ================================================================ HALF-LIFE
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

def _build_spread_ols(kind, a, b):
    if kind == "DIFF":
        return [a[i] - b[i] for i in range(len(a))]
    la = [math.log(x) for x in a]
    lb = [math.log(x) for x in b]
    beta = _ols_beta(la, lb)
    return [la[i] - beta * lb[i] for i in range(len(la))]

# ================================================================ KALMAN FILTER
def _ols(y, x):
    n = len(x)
    if n < 10:
        return 0.0, 1.0, [0.0]*n
    mx = sum(x)/n; my = sum(y)/n
    num = sum((x[i]-mx)*(y[i]-my) for i in range(n))
    den = sum((x[i]-mx)**2 for i in range(n))
    if den <= 0:
        return my, 0.0, [y[i]-my for i in range(n)]
    beta = num/den; alpha = my - beta*mx
    res = [y[i] - alpha - beta*x[i] for i in range(n)]
    return alpha, beta, res

def kalman_spread(y_vals, x_vals, delta=1e-5, vt=1e-3):
    if len(y_vals) < 30:
        ly = [math.log(v) for v in y_vals]; lx = [math.log(v) for v in x_vals]
        beta_s = _ols_beta(ly, lx)
        spread = [ly[i] - beta_s * lx[i] for i in range(len(y_vals))]
        return [beta_s] * len(y_vals), spread
    ly = [math.log(v) for v in y_vals]; lx = [math.log(v) for v in x_vals]
    init_n = min(30, len(y_vals))
    init_beta = _ols_beta(ly[:init_n], lx[:init_n])
    init_alpha = (sum(ly[:init_n]) - init_beta * sum(lx[:init_n])) / init_n
    alpha, beta = init_alpha, init_beta
    P00, P01, P10, P11 = 1.0, 0.0, 0.0, 1.0
    Q00, Q11, R = delta * 10.0, delta, vt
    n = len(y_vals)
    betas, spread_out = [0.0]*n, [0.0]*n
    for t in range(n):
        alpha_pred, beta_pred = alpha, beta
        P00_pred = P00 + Q00; P01_pred = P01
        P10_pred = P10; P11_pred = P11 + Q11
        y_pred = alpha_pred + beta_pred * lx[t]
        innovation = ly[t] - y_pred
        S = P00_pred + 2.0 * P01_pred * lx[t] + P11_pred * lx[t] * lx[t] + R
        if S < 1e-15:
            betas[t] = beta_pred; spread_out[t] = innovation
            continue
        K0 = (P00_pred + P01_pred * lx[t]) / S
        K1 = (P10_pred + P11_pred * lx[t]) / S
        alpha = alpha_pred + K0 * innovation
        beta = beta_pred + K1 * innovation
        P00 = (1.0 - K0) * P00_pred - K0 * lx[t] * P10_pred
        P01 = (1.0 - K0) * P01_pred - K0 * lx[t] * P11_pred
        P10 = -K1 * P00_pred + (1.0 - K1 * lx[t]) * P10_pred
        P11 = -K1 * P01_pred + (1.0 - K1 * lx[t]) * P11_pred
        betas[t] = beta; spread_out[t] = innovation
    return betas, spread_out

# ================================================================ ENGLE-GRANGER
def adf_stat(residuals, max_lag=5):
    n = len(residuals)
    if n < 20:
        return 0.0, 1.0
    dy = [residuals[i] - residuals[i-1] for i in range(1, n)]
    y_lag1 = residuals[:-1]
    best_lag, best_var = 0, float("inf")
    for lag in range(max_lag + 1):
        if n - lag - 2 < 10: continue
        Y = dy[lag:]; T = len(Y)
        X_rows = []
        for i in range(lag, len(dy)):
            row = [y_lag1[i]]
            for j in range(1, lag + 1):
                row.append(dy[i - j] if i - j >= 0 else 0.0)
            X_rows.append(row)
        K = len(X_rows[0])
        XtX = [[sum(X_rows[t][i]*X_rows[t][j] for t in range(T)) for j in range(K)] for i in range(K)]
        XtY = [sum(X_rows[t][i]*Y[t] for t in range(T)) for i in range(K)]
        A = [row[:] for row in XtX]; b = XtY[:]
        ok = True
        for col in range(K):
            pivot = col
            for row in range(col+1, K):
                if abs(A[row][col]) > abs(A[pivot][col]): pivot = row
            if abs(A[pivot][col]) < 1e-15: ok = False; break
            A[col], A[pivot] = A[pivot], A[col]
            b[col], b[pivot] = b[pivot], b[col]
            for row in range(col+1, K):
                factor = A[row][col] / A[col][col]
                for j in range(col, K): A[row][j] -= factor * A[col][j]
                b[row] -= factor * b[col]
        if not ok: continue
        coeffs = [0.0]*K
        for row in range(K-1, -1, -1):
            s = b[row]
            for j in range(row+1, K): s -= A[row][j] * coeffs[j]
            coeffs[row] = s / A[row][row]
        Yhat = [sum(coeffs[j]*X_rows[t][j] for j in range(K)) for t in range(T)]
        sse = sum((Y[t] - Yhat[t])**2 for t in range(T))
        var = sse / max(T-K, 1)
        if var < best_var: best_var = var; best_lag = lag
    lag = best_lag
    Y = dy[lag:]; T = len(Y)
    X_rows = []
    for i in range(lag, len(dy)):
        row = [y_lag1[i]]
        for j in range(1, lag + 1):
            row.append(dy[i - j] if i - j >= 0 else 0.0)
        X_rows.append(row)
    K = len(X_rows[0]) if X_rows else 1
    if T < 10: return 0.0, 1.0
    XtX = [[sum(X_rows[t][i]*X_rows[t][j] for t in range(T)) for j in range(K)] for i in range(K)]
    XtY = [sum(X_rows[t][i]*Y[t] for t in range(T)) for i in range(K)]
    A, b = [row[:] for row in XtX], XtY[:]
    for col in range(K):
        pivot = col
        for row in range(col+1, K):
            if abs(A[row][col]) > abs(A[pivot][col]): pivot = row
        if abs(A[pivot][col]) < 1e-15: return 0.0, 1.0
        A[col], A[pivot] = A[pivot], A[col]
        b[col], b[pivot] = b[pivot], b[col]
        for row in range(col+1, K):
            factor = A[row][col] / A[col][col]
            for j in range(col, K): A[row][j] -= factor * A[col][j]
            b[row] -= factor * b[col]
    coeffs = [0.0]*K
    for row in range(K-1, -1, -1):
        s = b[row]
        for j in range(row+1, K): s -= A[row][j] * coeffs[j]
        coeffs[row] = s / A[row][row]
    gamma = coeffs[0]
    Yhat = [sum(coeffs[j]*X_rows[t][j] for j in range(K)) for t in range(T)]
    sse = sum((Y[t] - Yhat[t])**2 for t in range(T))
    sigma2 = sse / max(T-K, 1)
    x1_ss = sum(X_rows[t][0]**2 for t in range(T))
    se_gamma = math.sqrt(sigma2 / x1_ss) if x1_ss > 1e-15 else 1.0
    adf = gamma / se_gamma if se_gamma > 1e-15 else 0.0
    T_obs = len(residuals)
    if T_obs > 200: c10, c05, c01 = -2.57, -2.86, -3.43
    elif T_obs > 100: c10, c05, c01 = -2.80, -3.10, -3.60
    elif T_obs > 50: c10, c05, c01 = -3.04, -3.34, -3.90
    else: c10, c05, c01 = -3.20, -3.50, -4.10
    if adf <= c01: pval = 0.005
    elif adf <= c05: pval = 0.01 + (adf - c01)/(c05 - c01)*0.04
    elif adf <= c10: pval = 0.05 + (adf - c05)/(c10 - c05)*0.05
    else: pval = 0.10 + (adf - c10)/(0.0 - c10)*0.40; pval = min(pval, 0.99)
    return adf, max(0.001, min(0.99, pval))

def engle_granger_test(y, x, max_lag=5):
    alpha, beta, res = _ols(y, x)
    adf, pval = adf_stat(res, max_lag)
    return (pval < 0.10), adf, pval, beta

# ================================================================ BACKTEST ENGINE
def _cost_for(ac):
    m = {"STOCK": COST_STOCK, "ETF": COST_ETF, "CRYPTO": COST_CRYPTO,
         "FX": COST_FX, "CROSS": COST_CRYPTO}
    return m.get(ac, COST_STOCK)

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
                d_stdev = (spread[j] - entry) / esd
                if side * d_stdev >= 1.5:
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
        best = max(rets) if rets else 0.0
        wins = sum(1 for r in rets if r > 0)
        win_rate = wins / n if n > 0 else 0.0
        avg_win = statistics.mean([r for r in rets if r > 0]) if wins > 0 else 0.0
        n_loss = n - wins
        avg_loss = statistics.mean([r for r in rets if r <= 0]) if n_loss > 0 else 0.0
        if avg_loss != 0 and n_loss > 0:
            profit_factor = abs(avg_win * wins / (avg_loss * n_loss))
        else:
            profit_factor = float("inf") if wins > 0 else 0.0
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
        ann_factor = math.sqrt(252 / horizon) if horizon > 0 else 1.0
        sharpe = edge * ann_factor if edge else 0.0
        return {
            "exp_ret": exp_ret, "sd": sd, "edge": edge, "tstat": tstat,
            "n": n, "worst_trade": worst, "best_trade": best,
            "win_rate": win_rate, "profit_factor": profit_factor,
            "avg_win": avg_win, "avg_loss": avg_loss,
            "max_dd": max_dd, "max_loss_streak": ms,
            "sharpe_ann": sharpe, "total_return": cum,
        }

    st = _stats(sim(entries))
    if not st:
        return None

    split = int(N * (1 - OOS_FRAC))
    oos_entries = [e for e in entries if e[0] >= split]
    oos_st = _stats(sim(oos_entries))

    m_now, sd_now = roll_stats(N - 1, lookback)
    z_now = (spread[N - 1] - m_now) / sd_now if sd_now > 0 else 0.0

    return {
        "exp_ret": st["exp_ret"], "sd": st["sd"], "edge": st["edge"],
        "tstat": st["tstat"], "n": st["n"],
        "worst_trade": st["worst_trade"], "max_dd": st["max_dd"],
        "max_loss_streak": st["max_loss_streak"],
        "win_rate": st["win_rate"], "profit_factor": st["profit_factor"],
        "sharpe_ann": st["sharpe_ann"], "total_return": st["total_return"],
        "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
        "oos_edge": oos_st["edge"] if oos_st else None,
        "oos_n": oos_st["n"] if oos_st else 0,
        "oos_worst_trade": oos_st["worst_trade"] if oos_st else None,
        "oos_max_dd": oos_st["max_dd"] if oos_st else None,
        "oos_win_rate": oos_st["win_rate"] if oos_st else None,
        "oos_sharpe_ann": oos_st["sharpe_ann"] if oos_st else None,
        "firing": abs(z_now) > z_entry, "z_now": z_now,
        "n_bars": N, "lookback": lookback, "horizon": horizon,
    }

# ================================================================ QUALIFICATION
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
        z = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= ph:
        q = p - 0.5; r = q*q
        z = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
            (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        z = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    return max(2.0, z)

def qualifies_pair(bt, n_tests=1, use_fdr=False, all_pvals=None):
    if not bt: return False
    ac = bt.get("asset_class", "STOCK")
    if ac == "FX":
        is_edge_min, oos_edge_max, worst_trade_min, max_dd_max = 0.30, 5.0, -5.0, 10.0
    else:
        is_edge_min, oos_edge_max, worst_trade_min, max_dd_max = 0.60, 3.0, -3.0, 6.0
    if bt["n"] < MIN_SAMPLE: return False
    if bt["edge"] < is_edge_min: return False
    if use_fdr and all_pvals is not None:
        m = len(all_pvals); sp = sorted(all_pvals); kmax = 0
        for k in range(1, m + 1):
            if sp[k - 1] <= (k / m) * FDR_ALPHA: kmax = k
        if kmax == 0: return False
        thresh = sp[kmax - 1]
        if _p_from_t(bt.get("tstat")) > thresh: return False
    else:
        if (bt.get("tstat") or 0) < _bonferroni_t(n_tests): return False
    oos_n = bt.get("oos_n") or 0
    if oos_n < MIN_OOS_SAMPLE: return False
    oos_exp = bt.get("oos_exp_ret")
    if oos_exp is None or oos_exp <= 0: return False
    oos_edge = bt.get("oos_edge")
    if oos_edge is None or oos_edge <= 0: return False
    if oos_edge > oos_edge_max: return False
    worst = bt.get("worst_trade")
    if worst is not None and worst < worst_trade_min: return False
    max_dd = bt.get("max_dd")
    if max_dd is not None and max_dd > max_dd_max: return False
    streak = bt.get("max_loss_streak")
    if streak is not None and streak > 5: return False
    return True

# ================================================================ VIX PROXY
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

# ================================================================ PAIR DEFINITIONS
def generate_sector_pairs(stocks):
    pairs = []
    for i in range(len(stocks)):
        for j in range(i + 1, len(stocks)):
            a, b = stocks[i], stocks[j]
            pairs.append((a + "/" + b, "STOCK", a, b, "LOG", "polygon"))
    return pairs

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

# ================================================================ PAIR BACKTEST RUNNER
def backtest_pair(label, ac, sym_a, sym_b, kind, provider,
                   vix_proxy=None, use_hl=True, use_rf=False, use_kalman=False):
    ha = _load_series(sym_a, provider)
    hb = _load_series(sym_b, provider)
    if not ha or not hb: return label, None, "no data"
    da, ca = ha; db, cb = hb
    a, b, dates = _align(da, ca, db, cb)
    if len(a) < 80: return label, None, "too few obs"
    if use_kalman and kind != "DIFF":
        _, spread = kalman_spread(a, b, KALMAN_DELTA, KALMAN_VT)
    else:
        spread = _build_spread_ols(kind, a, b)
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
    bt = backtest_pair_with_params(spread, lookback, horizon, Z_ENTRY, Z_EXIT, cost,
                                    vix_series=vix_aligned)
    if not bt: return label, None, "insufficient trades"
    eg_coint, eg_adf, eg_pval, eg_beta = engle_granger_test(
        [math.log(v) for v in a], [math.log(v) for v in b], EG_MAX_LAG)
    bt["label"] = label; bt["asset_class"] = ac
    bt["sym_a"] = sym_a; bt["sym_b"] = sym_b
    bt["kind"] = kind; bt["provider"] = provider
    bt["half_life"] = round(hl, 1)
    bt["first_date"] = dates[0] if dates else ""
    bt["last_date"] = dates[-1] if dates else ""
    bt["regime_filter"] = use_rf; bt["kalman_spread"] = use_kalman
    bt["eg_cointegrated"] = eg_coint; bt["eg_adf_stat"] = round(eg_adf, 3)
    bt["eg_pvalue"] = round(eg_pval, 4)
    return label, bt, None
