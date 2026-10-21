from __future__ import annotations
import math, statistics


def _ols_beta(y, x):
    n = len(x)
    if n < 10: return 1.0
    sxy = sum(x[i] * y[i] for i in range(n))
    sxx = sum(x[i] * x[i] for i in range(n))
    return sxy / sxx if sxx > 0 else 1.0


def kalman_spread(y_vals, x_vals, delta=1e-5, vt=1e-3):
    if len(y_vals) < 30:
        beta_s = _ols_beta([math.log(v) for v in y_vals], [math.log(v) for v in x_vals])
        la = [math.log(v) for v in y_vals]; lb = [math.log(v) for v in x_vals]
        spread = [la[i] - beta_s * lb[i] for i in range(len(y_vals))]
        return [beta_s] * len(y_vals), spread
    ly = [math.log(v) for v in y_vals]; lx = [math.log(v) for v in x_vals]
    init_n = min(30, len(y_vals))
    init_beta = _ols_beta(ly[:init_n], lx[:init_n])
    init_alpha = (sum(ly[:init_n]) - init_beta * sum(lx[:init_n])) / init_n
    alpha = init_alpha; beta = init_beta
    P00 = 1.0; P01 = 0.0; P10 = 0.0; P11 = 1.0
    Q00 = delta * 10.0; Q11 = delta; R = vt
    n = len(y_vals)
    betas = [0.0] * n; spread_out = [0.0] * n
    for t in range(n):
        alpha_pred = alpha; beta_pred = beta
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


def ols_residuals(y, x):
    n = len(x)
    if n < 10: return 0.0, 1.0, [0.0]*n
    mx = sum(x)/n; my = sum(y)/n
    num = sum((x[i]-mx)*(y[i]-my) for i in range(n))
    den = sum((x[i]-mx)**2 for i in range(n))
    if den <= 0: return my, 0.0, [y[i]-my for i in range(n)]
    beta = num/den; alpha = my - beta*mx
    res = [y[i] - alpha - beta*x[i] for i in range(n)]
    return alpha, beta, res


def adf_stat(residuals, max_lag=5):
    n = len(residuals)
    if n < 20: return 0.0, 1.0
    dy = [residuals[i] - residuals[i-1] for i in range(1, n)]
    y_lag1 = residuals[:-1]
    best_lag = 0; best_var = float("inf")
    for lag in range(max_lag + 1):
        if n - lag - 2 < 10: continue
        Y = dy[lag:]
        T = len(Y)
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
    Y = dy[lag:]
    T = len(Y)
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
    alpha, beta, res = ols_residuals(y, x)
    adf, pval = adf_stat(res, max_lag)
    return (pval < 0.10), adf, pval, beta
