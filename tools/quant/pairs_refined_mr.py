#!/usr/bin/env python3
"""Refined Mean-Reversion Pairs -- Anti-trend filter from momentum findings.

KEY INSIGHT from pairs_momentum.py:
- Trend-following on spreads has NEGATIVE edge (t=-4 to -6)
- Therefore: when z and trend are ALIGNED, mean-reversion LOSES
- Therefore: enter mean-reversion ONLY when z and trend are OPPOSITE (spread
  already turning back toward mean)

This is the COMPLEMENT of the momentum strategy:
- Momentum: z * trend > 0  (enter, go with trend) -> LOSES
- Refined MR: |z| >= threshold AND z * trend < 0 (enter, go vs trend) -> ??

Scramble control mandatory.
"""
import os, sys, csv, json, math, random, statistics, time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

POLYGON_DIR = os.path.join(_HERE, 'data', 'polygon')
REPORT_DIR = os.path.join(_HERE, 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

SECTORS = {
    'TECH': ['AAPL','MSFT','GOOGL','META','AMZN','NVDA','AVGO','ORCL',
             'CRM','ADBE','CSCO','INTC','AMD','QCOM','TXN','MU','NOW',
             'SNOW','PLTR','SHOP','ARM','AMAT'],
    'FINANCIAL': ['JPM','BAC','WFC','GS','MS','SCHW','V','MA'],
    'HEALTHCARE': ['JNJ','PFE','MRK','ABBV','AMGN','LLY','TMO','DHR','ABT','UNH'],
    'CONSUMER': ['HD','NKE','MCD','SBUX','TJX','COST','WMT','TGT','DIS','CMCSA'],
}

def load_close(ticker):
    fp = os.path.join(POLYGON_DIR, ticker + '.csv')
    if not os.path.exists(fp):
        return None
    closes = []
    with open(fp) as f:
        for row in csv.DictReader(f):
            try:
                closes.append(float(row['close']))
            except:
                continue
    return closes if len(closes) >= 100 else None

def build_spread(leg_a, leg_b):
    pa = load_close(leg_a); pb = load_close(leg_b)
    if pa is None or pb is None:
        return None, None
    n = min(len(pa), len(pb))
    if n < 100:
        return None, None
    la = [math.log(p) for p in pa[-n:]]
    lb = [math.log(p) for p in pb[-n:]]
    mb = statistics.mean(lb); ma = statistics.mean(la)
    cov = sum((lb[i]-mb)*(la[i]-ma) for i in range(n))/(n-1)
    vb = statistics.variance(lb)
    if vb <= 0:
        return None, None
    beta = cov/vb; alpha = ma - beta*mb
    spread = [la[i]-alpha-beta*lb[i] for i in range(n)]
    return spread, beta

def rolling_mean_std(data, win):
    means, stds = [], []
    for i in range(len(data)):
        chunk = data[max(0,i-win+1):i+1]
        if len(chunk) < max(10, win//4):
            means.append(0.0); stds.append(0.0)
        else:
            m = statistics.mean(chunk)
            v = statistics.variance(chunk) if len(chunk)>1 else 0.0
            means.append(m); stds.append(math.sqrt(v) if v>0 else 0.0)
    return means, stds

def rolling_slope(spread, win):
    slopes = []
    for i in range(len(spread)):
        chunk = spread[max(0,i-win+1):i+1]
        if len(chunk) < max(5, win//4):
            slopes.append(0.0); continue
        n = len(chunk)
        xm = (n-1)/2.0; ym = statistics.mean(chunk)
        cov_xy = sum((j-xm)*(chunk[j]-ym) for j in range(n))/(n-1)
        var_x = sum((j-xm)**2 for j in range(n))/(n-1)
        slp = cov_xy/var_x if var_x>0 else 0.0
        sd = math.sqrt(statistics.variance(chunk)) if n>1 and statistics.variance(chunk)>0 else 1.0
        slopes.append(slp/max(sd,1e-10))
    return slopes

print('Module loaded.')
