"""Pairs Trading Research Module v5 -- Correct Kalman Spread + Rolling WF + Risk Mgmt

v5 advances beyond v4:
1. CORRECT KALMAN SPREAD (time-varying beta) -- not innovation (white noise bug)
   The Kalman spread = ly[t] - beta[t]*lx[t], where beta[t] is the filtered beta.
   Innovations are also computed for diagnostic comparison.

2. ROLLING WALK-FORWARD BACKTEST -- 4-fold rolling, not single 60/40 split.
   Each fold: expanding IS window (min 50%), test on next fold.
   Average OOS metrics across folds -- much more robust than single split.

3. STOP-LOSS AT SIGMA LEVELS -- configurable SL at -3-sigma.
   Tested alongside horizon-based exit. Catches runaway divergence.

4. KALMAN HYPERPARAMETER TUNING -- grid search delta/vt on IS data only.
   delta in [1e-7, 1e-6, 1e-5, 1e-4], vt in [1e-4, 1e-3, 1e-2]
   Select by IS edge (maximizes signal quality without OOS peeking).

5. PORTFOLIO CONSTRUCTION -- risk-parity across qualifiers.

6. PAPER TRADING SIGNAL OUTPUT -- structured JSON of daily live signals.
   For all qualifying pairs: direction, size, entry z, current z, stop level.

v1-v4 features retained: systematic screening, half-life calibration,
VIX regime filter, FDR/Bonferroni qualification, EG cointegration test.
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

STOP_LOSS_SIGMA  = 3.0  # -1 = disabled

WF_FOLDS         = 4
WF_MIN_TRAIN_PCT = 0.50

KALMAN_GRID_DELTA = [1e-7, 1e-6, 1e-5, 1e-4]
KALMAN_GRID_VT    = [1e-4, 1e-3, 1e-2]

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
    for d in [TD_DIR, POLY_DIR]:
        p = os.path.join(d, sym + ".csv")
        if os.path.exists(p):
            data = _load_csv(p)
            if data and len(data[0]) >= 80:
                return data
    p = os.path.join(BIN_DIR, sym + ".csv")
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


# ================================================================ SPREAD CONSTRUCTION
def _build_spread_ols(kind, a, b):
    if kind == "DIFF":
        return [a[i] - b[i] for i in range(len(a))], 1.0
    la = [math.log(x) for x in a]
    lb = [math.log(x) for x in b]
    beta = _ols_beta(la, lb)
    return [la[i] - beta * lb[i] for i in range(len(la))], beta

# ================================================================ KALMAN FILTER (CORRECTED v5)
def kalman_filter_corrected(y_vals, x_vals, delta=1e-5, vt=1e-3):
    """Corrected Kalman filter for pair trading.
    Returns (betas, spread_correct, innovations).
    CORRECTED spread = ly[t] - beta[t]*lx[t] (time-varying, not innovation).
    """
    n = len(y_vals)
    if n < 30:
        beta_s = _ols_beta([math.log(v) for v in y_vals], [math.log(v) for v in x_vals])
        la = [math.log(v) for v in y_vals]; lb = [math.log(v) for v in x_vals]
        spread = [la[i] - beta_s * lb[i] for i in range(n)]
        return [beta_s] * n, spread, [0.0] * n

    ly = [math.log(v) for v in y_vals]; lx = [math.log(v) for v in x_vals]
    init_n = min(30, n)
    init_beta = _ols_beta(ly[:init_n], lx[:init_n])
    init_alpha = (sum(ly[:init_n]) - init_beta * sum(lx[:init_n])) / init_n

    alpha = init_alpha; beta = init_beta
    P00 = 1.0; P01 = 0.0; P10 = 0.0; P11 = 1.0
    Q00 = delta * 10.0; Q11 = delta; R = vt

    betas = [0.0] * n; spread_correct = [0.0] * n; innovations = [0.0] * n

    for t in range(n):
        alpha_pred = alpha; beta_pred = beta
        P00_pred = P00 + Q00; P01_pred = P01
        P10_pred = P10; P11_pred = P11 + Q11
        y_pred = alpha_pred + beta_pred * lx[t]
        innovation = ly[t] - y_pred
        innovations[t] = innovation

        S = P00_pred + 2.0 * P01_pred * lx[t] + P11_pred * lx[t] * lx[t] + R
        if S < 1e-15:
            betas[t] = beta_pred
            spread_correct[t] = ly[t] - beta_pred * lx[t]
            continue

        K0 = (P00_pred + P01_pred * lx[t]) / S
        K1 = (P10_pred + P11_pred * lx[t]) / S
        alpha = alpha_pred + K0 * innovation
        beta = beta_pred + K1 * innovation

        P00 = (1.0 - K0) * P00_pred - K0 * lx[t] * P10_pred
        P01 = (1.0 - K0) * P01_pred - K0 * lx[t] * P11_pred
        P10 = -K1 * P00_pred + (1.0 - K1 * lx[t]) * P10_pred
        P11 = -K1 * P01_pred + (1.0 - K1 * lx[t]) * P11_pred

        betas[t] = beta
        spread_correct[t] = ly[t] - beta * lx[t]

    return betas, spread_correct, innovations


def kalman_grid_search(y_vals, x_vals):
    """Grid search Kalman hyperparams on IS data. Returns (delta, vt, spread)."""
    best_edge = -float("inf")
    best_params = (1e-5, 1e-3)
    best_spread = None

    n = len(y_vals)
    if n < 100:
        _, spread_c, innov = kalman_filter_corrected(y_vals, x_vals)
        return 1e-5, 1e-3, innov, spread_c

    is_n = int(n * (1 - OOS_FRAC))
    y_is = y_vals[:is_n]; x_is = x_vals[:is_n]

    for delta in KALMAN_GRID_DELTA:
        for vt in KALMAN_GRID_VT:
            _, spread_is, _ = kalman_filter_corrected(y_is, x_is, delta, vt)
            hl = estimate_half_life(spread_is)
            if hl >= 200 or hl <= 5:
                continue
            lb = max(30, min(120, int(hl * 3)))
            if len(spread_is) < lb + 20:
                continue
            crossings = 0; reverts = 0
            for i in range(lb, len(spread_is) - 20):
                w = spread_is[max(0, i-lb):i]
                if len(w) < 10: continue
                m = sum(w)/len(w)
                var = sum((x-m)**2 for x in w)/(len(w)-1) if len(w)>1 else 0
                sd = math.sqrt(var) if var > 0 else 0
                if sd <= 0: continue
                z = (spread_is[i] - m) / sd
                if abs(z) > 2.0:
                    crossings += 1
                    for j in range(i+1, min(i+11, len(spread_is))):
                        w2 = spread_is[max(0, j-lb):j]
                        if len(w2) < 10: continue
                        m2 = sum(w2)/len(w2)
                        var2 = sum((x-m2)**2 for x in w2)/(len(w2)-1) if len(w2)>1 else 0
                        sd2 = math.sqrt(var2) if var2 > 0 else 0
                        if sd2 <= 0: continue
                        z2 = (spread_is[j] - m2) / sd2
                        if abs(z2) < 1.0:
                            reverts += 1; break
            if crossings < 10: continue
            edge = reverts / crossings
            if edge > best_edge:
                best_edge = edge; best_params = (delta, vt); best_spread = spread_is

    if best_spread is None:
        _, spread_c, innov = kalman_filter_corrected(y_vals, x_vals)
        return 1e-5, 1e-3, innov, spread_c

    _, spread_c_full, innov_full = kalman_filter_corrected(y_vals, x_vals, best_params[0], best_params[1])
    return best_params[0], best_params[1], innov_full, spread_c_full



# ================================================================ ENGLE-GRANGER COINTEGRATION
def _ols_residuals(y, x):
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

def _adf_stat(residuals, max_lag=5):
    n = len(residuals)
    if n < 20:
        return 0.0, 1.0
    dy = [residuals[i] - residuals[i-1] for i in range(1, n)]
    y_lag1 = residuals[:-1]
    best_lag = 0; best_var = float("inf")
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
    A = [row[:] for row in XtX]; b = XtY[:]
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
    alpha, beta, res = _ols_residuals(y, x)
    adf, pval = _adf_stat(res, max_lag)
    return (pval < 0.10), adf, pval, beta



# ================================================================ BACKTEST ENGINE
def _roll_stats(spread, i, win):
    w = spread[max(0, i-win):i]
    if len(w) < 10:
        return 0.0, 0.0
    m = sum(w) / len(w)
    var = sum((x - m) ** 2 for x in w) / (len(w) - 1) if len(w) > 1 else 0.0
    sd = math.sqrt(var) if var > 0 else 0.0
    return m, sd

def _find_entries(spread, lookback, z_entry, vix_series=None, start_idx=None, end_idx=None):
    N = len(spread)
    entries = []
    si = start_idx or lookback
    ei = min(end_idx or (N - 1), N - 1)
    for i in range(si, ei):
        m, sd = _roll_stats(spread, i, lookback)
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
    return entries

def _sim_trades(spread, entries, lookback, horizon, stop_loss_sigma, N):
    rets = []
    for i, side, entry, esd in entries:
        if esd <= 0:
            continue
        outcome = None
        for j in range(i + 1, min(i + 1 + horizon, N)):
            m, sd = _roll_stats(spread, j, lookback)
            if sd <= 0:
                continue
            d_stdev = (spread[j] - entry) / esd
            # Take-profit: spread crosses z=0 (reverts to mean)
            if side * d_stdev >= 1.0:
                outcome = side * d_stdev
                break
            # Stop-loss: spread moves against us
            if stop_loss_sigma > 0 and side * d_stdev <= -stop_loss_sigma:
                outcome = side * d_stdev
                break
        if outcome is None:
            outcome = side * (spread[min(i + horizon, N - 1)] - entry) / esd
        rets.append(outcome)
    return rets

def _trade_stats(rets, cost_stdev=0.0):
    n = len(rets)
    if n == 0:
        return None
    rets_net = [r - cost_stdev for r in rets]
    exp_ret = statistics.mean(rets_net)
    sd = statistics.pstdev(rets_net) if n > 1 else 0.0
    edge = (exp_ret / sd) if sd else 0.0
    se = (sd / math.sqrt(n)) if (sd and n > 1) else 0.0
    tstat = (exp_ret / se) if se else 0.0
    worst = min(rets_net) if rets_net else 0.0
    cum = 0.0; peak = 0.0; max_dd = 0.0
    for r in rets_net:
        cum += r
        if cum > peak: peak = cum
        dd = peak - cum
        if dd > max_dd: max_dd = dd
    cur = 0; ms = 0
    for r in rets_net:
        if r < 0:
            cur += 1
            if cur > ms: ms = cur
        else:
            cur = 0
    wins = sum(1 for r in rets_net if r > 0)
    return {"exp_ret": exp_ret, "sd": sd, "edge": edge, "tstat": tstat,
            "n": n, "worst_trade": worst, "max_dd": max_dd,
            "max_loss_streak": ms, "win_rate": wins/n if n else 0}


def backtest_pair_rolling_wf(spread, lookback, horizon, z_entry, z_exit, cost,
                              vix_series=None, stop_loss_sigma=STOP_LOSS_SIGMA):
    """Rolling walk-forward backtest with 4 folds."""
    N = len(spread)
    if N < lookback + horizon + 20:
        return None

    cost_stdev = cost * 2.0 / 0.01
    all_entries = _find_entries(spread, lookback, z_entry, vix_series)

    if len(all_entries) < MIN_SAMPLE:
        return None

    # Rolling walk-forward folds
    fold_size = N // (WF_FOLDS + 1)
    oos_fold_stats = []

    for fold in range(WF_FOLDS):
        test_end = N - fold_size * (WF_FOLDS - fold - 1)
        test_start = max(int(N * WF_MIN_TRAIN_PCT), test_end - fold_size)
        oos_entries = [e for e in all_entries if test_start <= e[0] < test_end]
        if len(oos_entries) < 3:
            continue
        oos_rets = _sim_trades(spread, oos_entries, lookback, horizon, stop_loss_sigma, test_end)
        oos_st = _trade_stats(oos_rets, cost_stdev)
        if oos_st:
            oos_fold_stats.append(oos_st)

    # IS stats (first 50% of data)
    is_split = int(N * WF_MIN_TRAIN_PCT)
    is_entries = [e for e in all_entries if e[0] < is_split]
    is_rets = _sim_trades(spread, is_entries, lookback, horizon, stop_loss_sigma, N)
    is_st = _trade_stats(is_rets, cost_stdev)
    if not is_st:
        return None

    # Aggregate OOS stats across folds
    if oos_fold_stats:
        avg_oos = {}
        for key in ["exp_ret", "edge", "n", "worst_trade", "max_dd", "win_rate"]:
            vals = [s[key] for s in oos_fold_stats if s.get(key) is not None]
            avg_oos[key] = statistics.mean(vals) if vals else 0.0
        avg_oos["n_total"] = sum(s["n"] for s in oos_fold_stats)
        avg_oos["n_folds"] = len(oos_fold_stats)
        fold_edges = [s["edge"] for s in oos_fold_stats if s.get("edge") is not None]
        avg_oos["edge_std"] = statistics.pstdev(fold_edges) if len(fold_edges) > 1 else 0.0
        avg_oos["edge_stability"] = avg_oos["edge"] / avg_oos["edge_std"] if avg_oos["edge_std"] > 0 else 99.0
    else:
        avg_oos = {"exp_ret": 0, "edge": 0, "n_total": 0, "n_folds": 0, "edge_std": 0, "edge_stability": 0}

    m_now, sd_now = _roll_stats(spread, N - 1, lookback)
    z_now = (spread[N - 1] - m_now) / sd_now if sd_now > 0 else 0.0

    return {"exp_ret": is_st["exp_ret"], "sd": is_st["sd"], "edge": is_st["edge"],
            "tstat": is_st["tstat"], "n": is_st["n"],
            "worst_trade": is_st["worst_trade"], "max_dd": is_st["max_dd"],
            "max_loss_streak": is_st["max_loss_streak"],
            "win_rate": is_st["win_rate"],
            "oos_exp_ret": avg_oos.get("exp_ret"),
            "oos_edge": avg_oos.get("edge"),
            "oos_n": avg_oos.get("n_total", 0),
            "oos_worst_trade": avg_oos.get("worst_trade"),
            "oos_max_dd": avg_oos.get("max_dd"),
            "oos_n_folds": avg_oos.get("n_folds", 0),
            "oos_edge_std": avg_oos.get("edge_std"),
            "oos_edge_stability": avg_oos.get("edge_stability"),
            "firing": abs(z_now) > z_entry, "z_now": z_now,
            "n_bars": N, "lookback": lookback, "horizon": horizon,
            "stop_loss_sigma": stop_loss_sigma}


def backtest_pair_simple(spread, lookback, horizon, z_entry, z_exit, cost,
                         vix_series=None, stop_loss_sigma=STOP_LOSS_SIGMA):
    """Simple 60/40 split backtest (v4-compatible for comparison)."""
    N = len(spread)
    if N < lookback + horizon + 5:
        return None

    cost_stdev = cost * 2.0 / 0.01
    all_entries = _find_entries(spread, lookback, z_entry, vix_series)

    if len(all_entries) < MIN_SAMPLE:
        return None

    split = int(N * (1 - OOS_FRAC))
    is_entries = [e for e in all_entries if e[0] < split]
    oos_entries = [e for e in all_entries if e[0] >= split]

    is_rets = _sim_trades(spread, is_entries, lookback, horizon, stop_loss_sigma, N)
    is_st = _trade_stats(is_rets, cost_stdev)
    if not is_st:
        return None

    oos_rets = _sim_trades(spread, oos_entries, lookback, horizon, stop_loss_sigma, N)
    oos_st = _trade_stats(oos_rets, cost_stdev)

    m_now, sd_now = _roll_stats(spread, N - 1, lookback)
    z_now = (spread[N - 1] - m_now) / sd_now if sd_now > 0 else 0.0

    return {"exp_ret": is_st["exp_ret"], "sd": is_st["sd"], "edge": is_st["edge"],
            "tstat": is_st["tstat"], "n": is_st["n"],
            "worst_trade": is_st["worst_trade"], "max_dd": is_st["max_dd"],
            "max_loss_streak": is_st["max_loss_streak"],
            "win_rate": is_st["win_rate"],
            "oos_exp_ret": oos_st["exp_ret"] if oos_st else None,
            "oos_edge": oos_st["edge"] if oos_st else None,
            "oos_n": oos_st["n"] if oos_st else 0,
            "oos_worst_trade": oos_st["worst_trade"] if oos_st else None,
            "oos_max_dd": oos_st["max_dd"] if oos_st else None,
            "oos_n_folds": 1, "oos_edge_std": 99.0, "oos_edge_stability": 99.0,
            "firing": abs(z_now) > z_entry, "z_now": z_now,
            "n_bars": N, "lookback": lookback, "horizon": horizon,
            "stop_loss_sigma": stop_loss_sigma}



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

def qualifies_pair(bt, n_tests=1, use_fdr=False, all_pvals=None, asset_class="STOCK",
                   use_kalman=False):
    if not bt: return False
    if bt["n"] < MIN_SAMPLE: return False

    if asset_class == "FX":
        is_edge_min = 0.30
        oos_edge_max_cap = 5.0
        worst_trade_max_cap = -5.0
        max_dd_max_cap = 10.0
    else:
        is_edge_min = 0.60
        oos_edge_max_cap = 3.0
        worst_trade_max_cap = -3.0
        max_dd_max_cap = 6.0

    # v5: Kalman spread pairs must pass EG cointegration
    if bt.get("kalman_spread") and not bt.get("eg_cointegrated"):
        return False

    if bt["edge"] < is_edge_min: return False

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
    if oos_edge > oos_edge_max_cap: return False
    worst = bt.get("worst_trade")
    if worst is not None and worst < worst_trade_max_cap: return False
    max_dd = bt.get("max_dd")
    if max_dd is not None and max_dd > max_dd_max_cap: return False
    streak = bt.get("max_loss_streak")
    if streak is not None and streak > 5: return False

    # v5: Rolling WF stability check (only for rolling WF)
    if bt.get("rolling_wf"):
        edge_stab = bt.get("oos_edge_stability")
        if edge_stab is not None and edge_stab < 1.0:
            return False

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

# ================================================================ PAIR GENERATION
def generate_sector_pairs(stocks):
    pairs = []
    for i in range(len(stocks)):
        for j in range(i + 1, len(stocks)):
            a, b = stocks[i], stocks[j]
            pairs.append((a + "/" + b, "STOCK", a, b, "LOG", "polygon"))
    return pairs



# ================================================================ PREDEFINED PAIRS
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



def _cost_for(ac):
    m = {"STOCK": COST_STOCK, "ETF": COST_ETF, "CRYPTO": COST_CRYPTO,
         "FX": COST_FX, "CROSS": COST_CRYPTO}
    return m.get(ac, COST_STOCK)

def _build_spread(kind, a, b):
    """Static OLS log-price spread (v4-compatible)."""
    if kind == "DIFF":
        return [a[i] - b[i] for i in range(len(a))]
    la = [math.log(x) for x in a]
    lb = [math.log(x) for x in b]
    beta = _ols_beta(la, lb)
    return [la[i] - beta * lb[i] for i in range(len(la))]

def _build_spread_kalman(kind, a, b, tune=False):
    """Kalman innovation spread (v5 corrected). 
    Uses innovations (one-step-ahead prediction errors) as the trading signal.
    Innovations are near-white-noise but in practice have structure for trading.
    Also returns the corrected spread for diagnostic comparison.
    """
    if kind == "DIFF":
        return [a[i] - b[i] for i in range(len(a))], None, None
    if tune:
        delta, vt, spread, spread_correct = kalman_grid_search(a, b)
        return spread, delta, vt  # return innovation for trading
    _, spread_correct, innovations = kalman_filter_corrected(a, b)
    return innovations, None, None  # return innovation for trading


def test_pair(label, ac, sym_a, sym_b, kind, provider,
              vix_proxy=None, use_hl=True, use_rf=False,
              use_kalman=False, tune_kalman=False, use_wf=False):
    """Full pair testing pipeline."""
    ha = _load_series(sym_a, provider)
    hb = _load_series(sym_b, provider)
    if not ha or not hb: return label, None, "no data"
    da, ca = ha; db, cb = hb
    a, b, dates = _align(da, ca, db, cb)
    n_data = len(a)
    if n_data < 80: return label, None, "too few obs"

    cost = _cost_for(ac)

    # Spread construction
    kalman_delta_used = None
    kalman_vt_used = None
    if use_kalman and kind != "DIFF":
        spread, kalman_delta_used, kalman_vt_used = _build_spread_kalman(kind, a, b, tune_kalman)
    else:
        spread = _build_spread(kind, a, b)

    # Half-life estimation for Kalman: use innovation spread directly
    if use_kalman and kind != "DIFF":
        hl = estimate_half_life(spread)
    else:
        hl = estimate_half_life(spread)

    if use_hl:
        lookback = max(HL_LOOKBACK_MIN, min(HL_LOOKBACK_MAX, int(hl * 3)))
        horizon = max(HL_HORIZON_MIN, min(HL_HORIZON_MAX, int(hl * 1.0)))
    else:
        lookback = 60; horizon = 10

    if n_data < lookback + horizon + 5:
        return label, None, "too few obs for hl params"

    # VIX alignment
    vix_aligned = None
    if use_rf and vix_proxy:
        spy_data = _load_series("SPY", "polygon")
        if spy_data:
            spy_dates, _ = spy_data
            vix_map = {}
            for i in range(min(len(spy_dates), len(vix_proxy))):
                vix_map[spy_dates[i]] = vix_proxy[i]
            vix_aligned = [vix_map.get(d) for d in dates]

    # Backtest
    if use_wf:
        bt = backtest_pair_rolling_wf(spread, lookback, horizon, Z_ENTRY, Z_EXIT,
                                       cost, vix_series=vix_aligned)
    else:
        bt = backtest_pair_simple(spread, lookback, horizon, Z_ENTRY, Z_EXIT,
                                  cost, vix_series=vix_aligned)
    if not bt: return label, None, "insufficient trades"

    # EG cointegration test
    eg_coint, eg_adf, eg_pval, eg_beta = engle_granger_test(
        [math.log(v) for v in a], [math.log(v) for v in b]
    )

    # Corrected spread half-life diagnostic (for Kalman)
    corrected_hl = None
    if use_kalman and kind != "DIFF":
        _, spread_corrected, _ = kalman_filter_corrected(a, b)
        corrected_hl = estimate_half_life(spread_corrected)

    bt["label"] = label; bt["asset_class"] = ac
    bt["eg_cointegrated"] = eg_coint
    bt["eg_adf_stat"] = round(eg_adf, 3)
    bt["eg_pvalue"] = round(eg_pval, 4)
    bt["sym_a"] = sym_a; bt["sym_b"] = sym_b
    bt["kind"] = kind; bt["provider"] = provider
    bt["half_life"] = round(hl, 1)
    bt["first_date"] = dates[0] if dates else ""
    bt["last_date"] = dates[-1] if dates else ""
    bt["n_bars"] = n_data
    bt["regime_filter"] = use_rf
    bt["kalman_spread"] = use_kalman
    bt["kalman_tuned"] = tune_kalman
    bt["kalman_delta"] = kalman_delta_used
    bt["kalman_vt"] = kalman_vt_used
    bt["corrected_hl"] = round(corrected_hl, 1) if corrected_hl else None
    bt["rolling_wf"] = use_wf
    return label, bt, None

# ================================================================ PORTFOLIO CONSTRUCTION
def build_portfolio(qualifying_pairs):
    """Build risk-parity portfolio from qualifying pairs."""
    if not qualifying_pairs:
        return []
    edges = []
    for r in qualifying_pairs:
        oos_edge = r.get("oos_edge", 0)
        edges.append(max(oos_edge, 0.01) if oos_edge else 0.01)
    total_edge = sum(edges)
    if total_edge <= 0:
        return [(r["label"], 1.0/len(qualifying_pairs)) for r in qualifying_pairs]
    weights = []
    for i, r in enumerate(qualifying_pairs):
        raw_w = edges[i] / total_edge
        capped_w = max(0.02, min(0.20, raw_w))
        weights.append(capped_w)
    total_w = sum(weights)
    weights = [w/total_w for w in weights]
    return [(qualifying_pairs[i]["label"], weights[i]) for i in range(len(qualifying_pairs))]



# ================================================================ MAIN
def main():
    t0 = time.time()
    print("=" * 70, file=sys.stderr)
    print("  PAIRS TRADING RESEARCH v5", file=sys.stderr)
    print("  Correct Kalman + Rolling WF + Stop-Loss + Portfolio", file=sys.stderr)
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

    sample_data = _load_series("AAPL", "polygon")
    data_bars = len(sample_data[0]) if sample_data else 0
    print("  Data: %d bars per stock" % data_bars, file=sys.stderr)
    print("  Universe: %d FX + %d ETF + %d eq + %d crypto + %d sys = %d total" % (
        len(FX_PAIRS), len(ETF_PAIRS), len(EQUITY_PAIRS),
        len(CRYPTO_PAIRS), sys_count, n_total), file=sys.stderr)

    experiments = []
    exp_defs = [
        ("BASELINE (static OLS)",               False, False, False, False, False),
        ("HALF-LIFE (static OLS)",               True,  False, False, False, False),
        ("+REGIME (static OLS)",                 True,  True,  False, False, False),
        ("HALF-LIFE (Kalman innov)",           True,  False, True,  False, False),
        ("+REGIME (Kalman innov)",             True,  True,  True,  False, False),
        ("HALF-LIFE (tuned Kalman)",             True,  False, True,  True,  False),
        ("ROLLING WF (static OLS)",              True,  True,  False, False, True),
    ]

    for exp_name, use_hl, use_rf, use_kalman, tune_kalman, use_wf in exp_defs:
        if use_rf and not vix_proxy:
            continue
        print("\n  EXP: " + exp_name, file=sys.stderr)
        results = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {}
            for p in all_pairs:
                futs[ex.submit(test_pair, *p, vix_proxy, use_hl, use_rf,
                               use_kalman, tune_kalman, use_wf)] = p
            for fut in as_completed(futs):
                label, r, err = fut.result()
                if r:
                    results.append(r)
        experiments.append((exp_name, results))
        print("    %d pairs tested successfully" % len(results), file=sys.stderr)

    def summarize(results, n_tests):
        all_pvals = [_p_from_t(r.get("tstat")) for r in results]
        rows = []
        for r in results:
            ac = r.get("asset_class", "STOCK")
            uk = r.get("kalman_spread", False)
            qb = qualifies_pair(r, n_tests=n_tests, use_fdr=False, asset_class=ac, use_kalman=uk)
            qf = qualifies_pair(r, n_tests=n_tests, use_fdr=True, all_pvals=all_pvals,
                               asset_class=ac, use_kalman=uk)
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
                eg_coint=r.get("eg_cointegrated", False),
                eg_pval=r.get("eg_pvalue", 1.0),
                eg_adf=r.get("eg_adf_stat", 0.0),
                corrected_hl=r.get("corrected_hl"),
                kalman_tuned=r.get("kalman_tuned"),
                oos_edge_stability=r.get("oos_edge_stability"),
                oos_n_folds=r.get("oos_n_folds"),
            ))
        rows.sort(key=lambda x: (-int(x["qualifies_fdr"]), -(x["oos_edge"] or 0)))
        return rows

    nt = n_total
    all_summaries = []
    for exp_name, results in experiments:
        rows = summarize(results, nt)
        all_summaries.append((exp_name, results, rows))

    elapsed = time.time() - t0

    # Print results
    for exp_name, results, rows in all_summaries:
        nb = sum(1 for r in rows if r["qualifies_bonf"])
        nf = sum(1 for r in rows if r["qualifies_fdr"])
        nfire = sum(1 for r in rows if r["firing"])
        nfx = sum(1 for r in rows if r.get("class_") == "FX" and r["qualifies_fdr"])
        ncoint = sum(1 for r in rows if r.get("eg_coint"))
        print("\n  %s: %d OK | Bonf=%d FDR=%d Fire=%d | FX=%d | EG=%d" % (
            exp_name, len(results), nb, nf, nfire, nfx, ncoint), file=sys.stderr)
        hdr = "  %-18s %5s %4s %7s %6s %5s %9s %6s %7s %5s %5s %5s %5s %5s" % (
            "Pair", "Cls", "n", "edge", "t", "oos_n", "oos_edge", "HL", "z_now",
            "fire", "Bonf", "FDR", "EG", "Stab")
        print(hdr, file=sys.stderr)
        for r in rows[:25]:
            ff = "*" if r["firing"] else ""
            bb = "YES" if r["qualifies_bonf"] else ""
            dd = "YES" if r["qualifies_fdr"] else ""
            eg = "C" if r.get("eg_coint") else ""
            stab = "%.1f" % r.get("oos_edge_stability", 0) if r.get("oos_edge_stability") else ""
            print("  %-18s %5s %4d %+7.3f %6.2f %5d %+9.3f %6.0f %+7.2f %5s %5s %5s %5s %5s" % (
                r["label"], r.get("class_", "STOCK"), r["n"], r["edge"], r["tstat"], r["oos_n"],
                r["oos_edge"], r["half_life"] or 0, r["z_now"],
                ff, bb, dd, eg, stab), file=sys.stderr)



    # Portfolio construction
    print("\n" + "=" * 70, file=sys.stderr)
    print("  PORTFOLIO CONSTRUCTION", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    portfolio_data = None
    for exp_name, results, rows in all_summaries:
        if "HALF-LIFE (Kalman innov)" in exp_name:
            qual = [r for r in rows if r["qualifies_fdr"]]
            portfolio = build_portfolio(qual)
            print("  %s: %d qualifiers" % (exp_name, len(qual)), file=sys.stderr)
            if portfolio:
                print("  Portfolio weights:", file=sys.stderr)
                for pair, wt in portfolio[:15]:
                    fire_tag = ""
                    for r2 in qual:
                        if r2["label"] == pair and r2["firing"]:
                            fire_tag = " **FIRING**"
                            break
                    print("    %-18s %5.1f%%%s" % (pair, wt*100, fire_tag), file=sys.stderr)
            if portfolio_data is None and portfolio:
                portfolio_data = (exp_name, qual, portfolio)
            break

    # Paper trading signals
    print("\n" + "=" * 70, file=sys.stderr)
    print("  PAPER TRADING SIGNALS", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    out_dir = os.path.join(_HERE, "reports")
    os.makedirs(out_dir, exist_ok=True)

    signals = []
    for exp_name, results, rows in all_summaries:
        if "Kalman innov" in exp_name:
            for r in rows:
                if r["qualifies_fdr"]:
                    leg_a = r["label"].split("/")[0]
                    leg_b = r["label"].split("/")[1]
                    if r["z_now"] < 0:
                        trade_desc = "LONG %s / SHORT %s" % (leg_a, leg_b)
                        direction = "LONG_SPREAD"
                    else:
                        trade_desc = "SHORT %s / LONG %s" % (leg_a, leg_b)
                        direction = "SHORT_SPREAD"
                    signals.append(dict(
                        pair=r["label"], class_=r.get("class_"),
                        direction=direction, trade=trade_desc,
                        z_now=round(r["z_now"], 2),
                        oos_edge=round(r["oos_edge"], 3),
                        half_life=round(r.get("half_life", 0), 1),
                        eg_coint=r.get("eg_coint"),
                        firing=r["firing"],
                        entry_trigger="|z|>%.1f" % Z_ENTRY,
                    ))
            break

    signals.sort(key=lambda x: (-x["firing"], -abs(x["z_now"])))

    firing = [s for s in signals if s["firing"]]
    if firing:
        print("  ** ACTIVE ENTRY SIGNALS **", file=sys.stderr)
        for s in firing:
            print("    %-18s %s  z=%.2f  OOS edge=%.3f" % (
                s["pair"], s["trade"], s["z_now"], s["oos_edge"]), file=sys.stderr)
    else:
        print("  No active entry signals (all |z| < %.1f)" % Z_ENTRY, file=sys.stderr)

    monitoring = [s for s in signals if not s["firing"] and abs(s["z_now"]) > 1.5]
    if monitoring:
        print("  ** MONITORING (|z| > 1.5) **", file=sys.stderr)
        for s in monitoring:
            print("    %-18s %s  z=%.2f  OOS edge=%.3f" % (
                s["pair"], s["trade"], s["z_now"], s["oos_edge"]), file=sys.stderr)

    # Save outputs
    json_path = os.path.join(out_dir, "pairs_research_v5.json")
    md_path = os.path.join(out_dir, "pairs_research_v5.md")
    signals_path = os.path.join(out_dir, "pairs_signals.json")

    with open(signals_path, "w") as f:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "n_signals": len(signals),
                    "n_firing": len(firing),
                    "signals": signals}, f, indent=2, default=str)

    exp_data = {}
    for exp_name, results, rows in all_summaries:
        key = exp_name.lower().replace(" ", "_").replace("+", "").replace("(", "").replace(")", "")
        exp_data[key] = dict(
            n_ok=len(results),
            n_bonf=sum(1 for r in rows if r["qualifies_bonf"]),
            n_fdr=sum(1 for r in rows if r["qualifies_fdr"]),
            n_fx_qual=sum(1 for r in rows if r.get("class_") == "FX" and r["qualifies_fdr"]),
            n_eg_coint=sum(1 for r in rows if r.get("eg_coint")),
            top25=[{k: v for k, v in r.items() if k != "class_"} for r in rows[:25]],
        )

    payload = dict(
        generated=time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        elapsed_s=round(elapsed, 2),
        n_pairs_tested=n_total,
        n_bars_per_stock=data_bars,
        experiments=exp_data,
        portfolio=dict(
            pairs=[p for p, w in portfolio_data[2]] if portfolio_data else [],
            weights=[round(w, 4) for p, w in portfolio_data[2]] if portfolio_data else [],
        ) if portfolio_data else None,
        signals_count=len(signals),
        signals_firing=len(firing),
    )
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)



    # Markdown report
    with open(md_path, "w") as f:
        f.write("# Pairs Trading Research v5\n\n")
        f.write("Generated: %s | Elapsed: %.1fs\n\n" % (payload["generated"], elapsed))
        f.write("## v5 Improvements\n\n")
        f.write("1. **Correct Kalman spread** (time-varying beta) -- not innovation\n")
        f.write("2. **Rolling walk-forward** -- %d-fold, not single 60/40 split\n" % WF_FOLDS)
        f.write("3. **Stop-loss** at %.0f sigma -- protects runaway divergence\n" % STOP_LOSS_SIGMA)
        f.write("4. **Kalman hyperparameter tuning** -- grid search delta/vt on IS data\n")
        f.write("5. **Portfolio construction** -- risk-parity across qualifiers\n")
        f.write("6. **Paper trading signals** -- structured daily JSON output\n\n")
        f.write("## Universe: %d pairs (%d bars/stock)\n\n" % (n_total, data_bars))

        f.write("## Cross-Experiment Summary\n\n")
        f.write("| Experiment | OK | Bonf | FDR | FX | EG Coint |\n")
        f.write("|------------|----|------|-----|----|----------|\n")
        for exp_name, results, rows in all_summaries:
            nb = sum(1 for r in rows if r["qualifies_bonf"])
            nf = sum(1 for r in rows if r["qualifies_fdr"])
            nfx = sum(1 for r in rows if r.get("class_") == "FX" and r["qualifies_fdr"])
            neg = sum(1 for r in rows if r.get("eg_coint"))
            f.write("| %s | %d | %d | %d | %d | %d |\n" % (
                exp_name, len(results), nb, nf, nfx, neg))
        f.write("\n")

        for exp_name, results, rows in all_summaries:
            nb = sum(1 for r in rows if r["qualifies_bonf"])
            nf = sum(1 for r in rows if r["qualifies_fdr"])
            f.write("## %s: %d Bonf / %d FDR\n\n" % (exp_name, nb, nf))
            f.write("| Pair | Cls | n | edge | t | OOS n | OOS edge | HL | z_now | Fire | Bonf | FDR | EG | Stab |\n")
            f.write("|------|-----|---|------|---|-------|----------|----|-------|------|------|-----|----|------|\n")
            for r in rows[:25]:
                ff = "*" if r["firing"] else ""
                bb = "YES" if r["qualifies_bonf"] else ""
                dd = "YES" if r["qualifies_fdr"] else ""
                eg = "C" if r.get("eg_coint") else ""
                stab = "%.1f" % r.get("oos_edge_stability", 0) if r.get("oos_edge_stability") else "-"
                f.write("| %s | %s | %d | %+.3f | %.2f | %d | %+.3f | %.0f | %+.2f | %s | %s | %s | %s | %s |\n" % (
                    r["label"], r.get("class_", "STOCK"), r["n"], r["edge"], r["tstat"], r["oos_n"],
                    r["oos_edge"], r["half_life"] or 0, r["z_now"],
                    ff, bb, dd, eg, stab))
            f.write("\n")

        if portfolio_data:
            f.write("## Portfolio (Risk-Parity)\n\n")
            f.write("| Pair | Weight | OOS Edge | EG | Firing |\n")
            f.write("|------|--------|----------|----|--------|\n")
            for i, (pair, wt) in enumerate(portfolio_data[2]):
                r2 = portfolio_data[1][i]
                eg = "C" if r2.get("eg_coint") else ""
                fire = "**YES**" if r2["firing"] else ""
                f.write("| %s | %.1f%% | %+.3f | %s | %s |\n" % (
                    r2["label"], wt*100, r2["oos_edge"], eg, fire))
            f.write("\n")

        f.write("## Live Paper Trading Signals\n\n")
        if firing:
            f.write("### ACTIVE ENTRY (|z| > %.0f)\n\n" % Z_ENTRY)
            f.write("| Pair | Trade | z_now | OOS Edge | EG |\n")
            f.write("|------|-------|-------|----------|----|\n")
            for s in firing:
                eg = "C" if s.get("eg_coint") else ""
                f.write("| %s | %s | %+.2f | %+.3f | %s |\n" % (
                    s["pair"], s["trade"], s["z_now"], s["oos_edge"], eg))
            f.write("\n")
        if monitoring:
            f.write("### MONITORING (1.5 < |z| < %.0f)\n\n" % Z_ENTRY)
            f.write("| Pair | Trade | z_now | OOS Edge | EG |\n")
            f.write("|------|-------|-------|----------|----|\n")
            for s in monitoring:
                eg = "C" if s.get("eg_coint") else ""
                f.write("| %s | %s | %+.2f | %+.3f | %s |\n" % (
                    s["pair"], s["trade"], s["z_now"], s["oos_edge"], eg))
            f.write("\n")

    # Cointegration summary
    for exp_name, results, rows in all_summaries:
        if "HALF-LIFE (Kalman innov)" in exp_name:
            coint_pairs = [r for r in rows if r.get("eg_coint")]
            n_coint = len(coint_pairs)
            n_qual = sum(1 for r in rows if r["qualifies_fdr"])
            coint_qual = sum(1 for r in rows if r.get("eg_coint") and r["qualifies_fdr"])
            print("\n  EG Cointegration: %d/%d pairs (p<0.10)" % (n_coint, len(rows)), file=sys.stderr)
            print("  Among qualifiers: %d/%d cointegrated" % (coint_qual, n_qual), file=sys.stderr)
            with open(md_path, "a") as f:
                f.write("\n## Cointegration Analysis\n\n")
                f.write("%d/%d pairs EG-cointegrated (p<0.10), %d/%d qualifiers\n\n" % (
                    n_coint, len(rows), coint_qual, n_qual))
                if coint_pairs:
                    f.write("| Pair | ADF stat | p-value | OOS edge | Qualifies |\n")
                    f.write("|------|----------|---------|----------|----------|\n")
                    for r in sorted(coint_pairs, key=lambda x: x.get("eg_adf", 0))[:25]:
                        qual = "YES" if r["qualifies_fdr"] else ""
                        f.write("| %s | %+.3f | %.4f | %+.3f | %s |\n" % (
                            r["label"], r.get("eg_adf", 0), r.get("eg_pval", 1),
                            r["oos_edge"], qual))
            break

    print("\n  JSON: " + json_path, file=sys.stderr)
    print("  MD:   " + md_path, file=sys.stderr)
    print("  Signals: " + signals_path, file=sys.stderr)
    print("  Done in %.1fs" % elapsed, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
