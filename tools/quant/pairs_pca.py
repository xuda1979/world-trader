#!/usr/bin/env python3
"""PCA Statistical Arbitrage -- Trade residuals from sector-level PCA."""
import os, sys, csv, json, math, random, statistics, time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

POLYGON_DIR = os.path.join(_HERE, 'data', 'polygon')
REPORT_DIR = os.path.join(_HERE, 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

MIN_STOCKS = 4
MIN_BARS = 100
COST_BPS = 3.8
N_SCRAMBLE = 8

SECTORS = {
    'TECH': ['AAPL','MSFT','GOOGL','META','AMZN','NVDA','AVGO','ORCL',
             'CRM','ADBE','CSCO','INTC','AMD','QCOM','TXN','MU','NOW',
             'SNOW','PLTR','SHOP','ARM','AMAT'],
    'FINANCIAL': ['JPM','BAC','WFC','GS','MS','SCHW','V','MA'],
    'HEALTHCARE': ['JNJ','PFE','MRK','ABBV','AMGN','LLY','TMO','DHR','ABT','UNH'],
    'CONSUMER': ['HD','NKE','MCD','SBUX','TJX','COST','WMT','TGT','DIS','CMCSA'],
}

def load_returns(tickers):
    data = {}
    min_len = float('inf')
    for t in tickers:
        fp = os.path.join(POLYGON_DIR, t + '.csv')
        if not os.path.exists(fp):
            continue
        closes = []
        with open(fp) as f:
            for row in csv.DictReader(f):
                try:
                    closes.append(float(row['close']))
                except (ValueError, KeyError):
                    continue
        if len(closes) < MIN_BARS:
            continue
        logs = [math.log(c) for c in closes]
        rets = [logs[i] - logs[i-1] for i in range(1, len(logs))]
        data[t] = rets
        min_len = min(min_len, len(rets))
    if len(data) < MIN_STOCKS:
        return None, 0
    for t in data:
        data[t] = data[t][-min_len:]
    return data, min_len


def simple_pca(returns_matrix):
    n_stocks = len(returns_matrix)
    n_bars = len(returns_matrix[0])
    means = [statistics.mean(returns_matrix[i]) for i in range(n_stocks)]
    cov = [[0.0] * n_stocks for _ in range(n_stocks)]
    for i in range(n_stocks):
        for j in range(i, n_stocks):
            c = sum((returns_matrix[i][t] - means[i]) * (returns_matrix[j][t] - means[j])
                    for t in range(n_bars)) / (n_bars - 1)
            cov[i][j] = c
            cov[j][i] = c
    K = min(3, n_stocks)
    eigvals = []
    eigvecs = []
    residual = [row[:] for row in cov]
    for k in range(K):
        v = [1.0 / math.sqrt(n_stocks)] * n_stocks
        for _ in range(50):
            av = [sum(residual[i][j] * v[j] for j in range(n_stocks)) for i in range(n_stocks)]
            norm = math.sqrt(sum(x * x for x in av))
            if norm < 1e-12:
                break
            v = [x / norm for x in av]
        av = [sum(residual[i][j] * v[j] for j in range(n_stocks)) for i in range(n_stocks)]
        lam = sum(v[i] * av[i] for i in range(n_stocks))
        eigvals.append(lam)
        eigvecs.append(v)
        for i in range(n_stocks):
            for j in range(n_stocks):
                residual[i][j] -= lam * v[i] * v[j]
    return eigvals, eigvecs
