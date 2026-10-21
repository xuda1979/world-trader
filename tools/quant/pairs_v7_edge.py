#!/usr/bin/env python3
"""Pairs Edge Research v7 -- Momentum + Anti-trend Mean-Reversion."""
import os, sys, csv, json, math, random, statistics, time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

POLYGON_DIR = os.path.join(_HERE, "data", "polygon")
REPORT_DIR = os.path.join(_HERE, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

SECTORS = {
    "TECH": ["AAPL","MSFT","GOOGL","META","AMZN","NVDA","AVGO","ORCL",
             "CRM","ADBE","CSCO","INTC","AMD","QCOM","TXN","MU","NOW",
             "SNOW","PLTR","SHOP","ARM","AMAT"],
    "FINANCIAL": ["JPM","BAC","WFC","GS","MS","SCHW","V","MA"],
    "HEALTHCARE": ["JNJ","PFE","MRK","ABBV","AMGN","LLY","TMO","DHR","ABT","UNH"],
    "CONSUMER": ["HD","NKE","MCD","SBUX","TJX","COST","WMT","TGT","DIS","CMCSA"],
}

Z_ENTRIES = [1.5, 2.0]
LOOKBACKS = [30, 60]
HORIZONS = [10, 20]
TREND_WIN = 20
STOP_SIGMA = 2.5
MIN_TRADES = 8
N_SCRAMBLE = 5


def load_close(ticker):
    fp = os.path.join(POLYGON_DIR, ticker + ".csv")
    if not os.path.exists(fp): return None
    closes = []
    with open(fp) as f:
        for row in csv.DictReader(f):
            try: closes.append(float(row["close"]))
            except: continue
    return closes if len(closes) >= 100 else None


def build_spread(leg_a, leg_b):
    pa = load_close(leg_a); pb = load_close(leg_b)
    if pa is None or pb is None: return None, None
    n = min(len(pa), len(pb))
    if n < 100: return None, None
    la = [math.log(p) for p in pa[-n:]]
    lb = [math.log(p) for p in pb[-n:]]
    mb = statistics.mean(lb); ma = statistics.mean(la)
    cov = sum((lb[i]-mb)*(la[i]-ma) for i in range(n))/(n-1)
    vb = statistics.variance(lb)
    if vb <= 0: return None, None
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


def backtest(spread, lookback, horizon, z_entry, trend_win, strategy):
    n = len(spread)
    if n < lookback + horizon + trend_win + 20: return None
    means, stds = rolling_mean_std(spread, lookback)
    trends = rolling_slope(spread, trend_win)
    pnls = []
    pos = None
    for i in range(lookback + trend_win, n - 1):
        sd = stds[i]
        if sd <= 0: continue
        z = (spread[i] - means[i]) / sd
        trend = trends[i]
        if pos is None:
            entry_ok = abs(z) >= z_entry
            if strategy == 'momentum':
                entry_ok = entry_ok and z * trend > 0
                side = 1 if z < 0 else -1
            else:
                entry_ok = entry_ok and z * trend < 0
                side = -1 if z < 0 else 1
            if entry_ok:
                pos = {"side": side, "idx": i, "sd": sd, "val": spread[i]}
        else:
            side = pos["side"]; ei = pos["idx"]
            esd = pos["sd"]; ev = pos["val"]
            if i == ei: continue
            d_stdev = (spread[i] - ev) / esd if esd > 0 else 0.0
            exit_ok = False
            if side * z >= 0: exit_ok = True
            elif side * d_stdev <= -STOP_SIGMA: exit_ok = True
            elif i - ei >= horizon: exit_ok = True
            if exit_ok:
                pnls.append(side * d_stdev)
                pos = None
    if len(pnls) < MIN_TRADES: return None
    m = statistics.mean(pnls)
    se = statistics.stdev(pnls)/math.sqrt(len(pnls)) if len(pnls)>1 else 1.0
    t = m/se if se>0 else 0.0
    win_rate = sum(1 for p in pnls if p>0)/len(pnls)
    return {"edge": m, "t_stat": t, "n": len(pnls), "win_rate": win_rate}


def scramble(spread, seed):
    rng = random.Random(seed)
    off = rng.randint(len(spread)//4, len(spread)*3//4)
    return spread[off:] + spread[:off]


def build_pairs():
    pairs = []
    for s, ts in SECTORS.items():
        for i in range(len(ts)):
            for j in range(i+1, len(ts)):
                pairs.append((ts[i], ts[j], s))
    return pairs


def run_config(pairs, lookback, horizon, z_entry, trend_win, strategy, label):
    results = []
    for leg_a, leg_b, sector in pairs:
        sp, beta = build_spread(leg_a, leg_b)
        if sp is None: continue
        hz = min(horizon, len(sp)//4)
        r = backtest(sp, lookback, hz, z_entry, trend_win, strategy)
        if r is None: continue
        scram_edges = []
        for s in range(N_SCRAMBLE):
            ssp = scramble(sp, s*1000 + hash(leg_a+leg_b)%1000)
            sr = backtest(ssp, lookback, hz, z_entry, trend_win, strategy)
            if sr and sr["n"] >= MIN_TRADES:
                scram_edges.append(sr["edge"])
        ms = statistics.mean(scram_edges) if scram_edges else 0.0
        diff = r["edge"] - ms
        pair_name = leg_a + '/' + leg_b
        results.append({
            "pair": pair_name, "sector": sector,
            "n_trades": r["n"], "real_edge": round(r["edge"],4),
            "real_t": round(r["t_stat"],3), "win_rate": round(r["win_rate"],3),
            "scram_edge": round(ms,4), "diff": round(diff,4),
        })
    if not results: return {"label": label, "n_pairs": 0}
    edges = [x["real_edge"] for x in results]
    diffs = [x["diff"] for x in results]
    md = statistics.mean(diffs)
    sdd = statistics.stdev(diffs) if len(diffs)>1 else 0.0
    dt = md/(sdd/math.sqrt(len(diffs))) if sdd>0 else 0.0
    results.sort(key=lambda x: x['diff'], reverse=True)
    return {
        "label": label, "strategy": strategy,
        "n_pairs": len(results), "lookback": lookback,
        "horizon": horizon, "z_entry": z_entry,
        "mean_real_edge": round(statistics.mean(edges),4),
        "mean_diff": round(md,4), "diff_t_stat": round(dt,3),
        "pct_pos": round(sum(1 for d in diffs if d>0)/len(diffs)*100,1),
        "edge_p50": round(sorted(edges)[len(edges)//2],4) if edges else 0,
        "top_pairs": results[:10],
    }


def main():
    t0 = time.time()
    pairs = build_pairs()
    print('PAIRS EDGE RESEARCH v7 -- Momentum + Anti-Trend MR')
    print('Universe: ' + str(len(pairs)) + ' same-sector pairs')
    all_res = []
    strategies = [('momentum','MOM'), ('antitrend','ATMR')]
    for lookback in LOOKBACKS:
        for z_entry in Z_ENTRIES:
            for horizon in HORIZONS:
                for strategy, tag in strategies:
                    label = tag + '_lb' + str(lookback) + '_z' + str(z_entry) + '_hz' + str(horizon)
                    print('  ' + label + ' ...', end=' ', flush=True)
                    r = run_config(pairs, lookback, horizon, z_entry, TREND_WIN, strategy, label)
                    all_res.append(r)
                    n = r.get('n_pairs',0)
                    md = r.get('mean_diff',0)
                    dt = r.get('diff_t_stat',0)
                    print(str(n) + ' pairs, diff=' + str(round(md,3)) + ', t=' + str(round(dt,2)))
    elapsed = time.time()-t0
    report = {
        'title': 'Pairs Edge Research v7',
        'generated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'elapsed_s': round(elapsed,1),
        'n_experiments': len(all_res),
        'experiments': all_res,
    }
    jp = os.path.join(REPORT_DIR, 'pairs_v7_edge.json')
    with open(jp, 'w') as f: json.dump(report, f, indent=2)
    print('Saved ' + jp)
    print()
    print('%-35s %6s %9s %8s %7s %6s' % ('Experiment','Pairs','RealEdge','Diff','t','%Pos'))
    print('-'*72)
    for r in all_res:
        l = r.get('label','?')[:34]
        n = r.get('n_pairs',0)
        re = r.get('mean_real_edge',0)
        md = r.get('mean_diff',0)
        dt = r.get('diff_t_stat',0)
        pp = r.get('pct_pos',0)
        print('%-35s %6d %9.3f %8.3f %7.2f %5.0f%%' % (l, n, re, md, dt, pp))
    print()
    print('-- BY STRATEGY --')
    for strat in ['momentum', 'antitrend']:
        strat_res = [r for r in all_res if r.get('strategy')==strat and r.get('n_pairs',0)>0]
        if strat_res:
            avg_diff = statistics.mean([r['mean_diff'] for r in strat_res])
            avg_t = statistics.mean([r['diff_t_stat'] for r in strat_res])
            ncfg = len(strat_res)
            print('  ' + strat + ': avg_diff=' + str(round(avg_diff,3)) + ', avg_t=' + str(round(avg_t,2)) + ' (' + str(ncfg) + ' configs)')
    print()
    print('-- VERDICT --')
    best = max(all_res, key=lambda r: r.get('diff_t_stat',0), default=None)
    if best:
        dt = best.get('diff_t_stat',0)
        md = best.get('mean_diff',0)
        label = best.get('label','?')
        npairs = best.get('n_pairs',0)
        print('  Best: ' + label + ' t=' + str(round(dt,2)) + ' diff=' + str(round(md,3)) + ' n=' + str(npairs))
    print('Elapsed: ' + str(round(elapsed,1)) + 's')


if __name__ == "__main__":
    main()
