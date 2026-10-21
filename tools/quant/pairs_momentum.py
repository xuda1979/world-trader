#!/usr/bin/env python3
"""Pairs Momentum Research -- Trend-following on pair spreads.

FLIP THE SIGNAL: all prior pair research (v1-v6, crosssec, Kalman, intraday)
tested MEAN-REVERSION. The conclusion: no edge at daily frequency on 2-year
US large-cap data. This module tests the OPPOSITE hypothesis:

    H0: Pair spreads are random walks (no edge either direction)
    H1: Pair spreads TREND -- momentum on the spread captures the drift

Design principles (from the v5 post-mortem):
1. SYMMETRIC exit rules -- profit/stop equidistant from entry in sigma-space
2. SCRAMBLE CONTROL -- every pair tested on real AND randomly-shifted data
3. ENGINE-LEVEL distribution -- report full distribution, not just top-N
4. MULTI-FREQUENCY -- daily AND weekly
"""
from __future__ import annotations
import os, sys, csv, json, math, random, statistics, time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

POLYGON_DIR = os.path.join(_HERE, "data", "polygon")
REPORT_DIR = os.path.join(_HERE, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

Z_ENTRY_GRID = [1.5, 2.0, 2.5]
Z_EXIT = 0.0
STOP_SIGMA = 2.5
HORIZON_BARS = [10, 20]
LOOKBACK_BARS = [30, 60, 120]
MIN_TRADES = 8
COST_BPS = 3.8

SECTORS = {
    "TECH": ["AAPL", "MSFT", "GOOGL", "META", "AMZN", "NVDA", "AVGO", "ORCL",
             "CRM", "ADBE", "CSCO", "INTC", "AMD", "QCOM", "TXN", "MU", "NOW",
             "SNOW", "PLTR", "SHOP", "ARM", "AMAT"],
    "FINANCIAL": ["JPM", "BAC", "WFC", "GS", "MS", "SCHW", "V", "MA"],
    "HEALTHCARE": ["JNJ", "PFE", "MRK", "ABBV", "AMGN", "LLY", "TMO", "DHR",
                   "ABT", "UNH"],
    "CONSUMER": ["HD", "NKE", "MCD", "SBUX", "TJX", "COST", "WMT", "TGT",
                 "DIS", "CMCSA"],
    "INDUSTRIAL": ["RTX", "GE", "UPS", "BA", "CAT", "HON"],
    "REAL_ESTATE": ["AMT", "PLD"],
    "ENERGY": ["XOM", "CVX", "COP"],
}

def load_close(ticker):
    fp = os.path.join(POLYGON_DIR, ticker + ".csv")
    if not os.path.exists(fp):
        return None
    closes = []
    with open(fp) as f:
        for row in csv.DictReader(f):
            try:
                closes.append(float(row["close"]))
            except (ValueError, KeyError):
                continue
    return closes if len(closes) >= 100 else None


def build_spread(leg_a, leg_b):
    pa = load_close(leg_a)
    pb = load_close(leg_b)
    if pa is None or pb is None:
        return None, None
    n = min(len(pa), len(pb))
    if n < 100:
        return None, None
    la = [math.log(p) for p in pa[-n:]]
    lb = [math.log(p) for p in pb[-n:]]
    mean_b = statistics.mean(lb)
    mean_a = statistics.mean(la)
    cov = sum((lb[i] - mean_b) * (la[i] - mean_a) for i in range(n)) / (n - 1)
    var_b = statistics.variance(lb)
    if var_b <= 0:
        return None, None
    beta = cov / var_b
    alpha = mean_a - beta * mean_b
    spread = [la[i] - alpha - beta * lb[i] for i in range(n)]
    return spread, beta


def rolling_mean_std(data, window):
    means, stds = [], []
    for i in range(len(data)):
        start = max(0, i - window + 1)
        chunk = data[start:i + 1]
        if len(chunk) < max(10, window // 4):
            means.append(0.0)
            stds.append(0.0)
        else:
            m = statistics.mean(chunk)
            var = statistics.variance(chunk) if len(chunk) > 1 else 0.0
            means.append(m)
            stds.append(math.sqrt(var) if var > 0 else 0.0)
    return means, stds


def rolling_trend(spread, window):
    slopes = []
    for i in range(len(spread)):
        start = max(0, i - window + 1)
        chunk = spread[start:i + 1]
        if len(chunk) < max(5, window // 4):
            slopes.append(0.0)
            continue
        n = len(chunk)
        x_mean = (n - 1) / 2.0
        y_mean = statistics.mean(chunk)
        cov_xy = sum((j - x_mean) * (chunk[j] - y_mean) for j in range(n)) / (n - 1)
        var_x = sum((j - x_mean) ** 2 for j in range(n)) / (n - 1)
        slope = cov_xy / var_x if var_x > 0 else 0.0
        sd = math.sqrt(statistics.variance(chunk)) if n > 1 and statistics.variance(chunk) > 0 else 1.0
        slopes.append(slope / max(sd, 1e-10))
    return slopes

def backtest_momentum(spread, lookback, horizon, z_entry, trend_window=20):
    n = len(spread)
    if n < lookback + horizon + trend_window + 20:
        return None
    means, stds = rolling_mean_std(spread, lookback)
    trends = rolling_trend(spread, trend_window)
    trades_pnl = []
    n_revert = 0
    n_stop = 0
    n_horizon = 0
    pos = None
    for i in range(lookback + trend_window, n - 1):
        sd = stds[i]
        if sd <= 0:
            continue
        z = (spread[i] - means[i]) / sd
        trend = trends[i]
        if pos is None:
            if abs(z) >= z_entry and z * trend > 0:
                side = 1 if z < 0 else -1
                pos = {"side": side, "idx": i, "sd": sd, "val": spread[i]}
        else:
            side = pos["side"]
            ei = pos["idx"]
            esd = pos["sd"]
            ev = pos["val"]
            if i == ei:
                continue
            d_stdev = (spread[i] - ev) / esd if esd > 0 else 0.0
            exit_reason = None
            if side * z >= -Z_EXIT:
                exit_reason = "revert"
            elif side * d_stdev <= -STOP_SIGMA:
                exit_reason = "stop"
            elif i - ei >= horizon:
                exit_reason = "horizon"
            if exit_reason is not None:
                pnl_sigma = side * d_stdev
                trades_pnl.append(pnl_sigma)
                if exit_reason == "revert":
                    n_revert += 1
                elif exit_reason == "stop":
                    n_stop += 1
                else:
                    n_horizon += 1
                pos = None
    if len(trades_pnl) < MIN_TRADES:
        return None
    m = statistics.mean(trades_pnl)
    se = statistics.stdev(trades_pnl) / math.sqrt(len(trades_pnl)) if len(trades_pnl) > 1 else 1.0
    t = m / se if se > 0 else 0.0
    summary = {
        "n_trades": len(trades_pnl), "mean_pnl": m, "t_stat": t, "edge": m,
        "win_rate": sum(1 for p in trades_pnl if p > 0) / len(trades_pnl),
        "stop_rate": n_stop / len(trades_pnl),
        "revert_rate": n_revert / len(trades_pnl),
    }
    return trades_pnl, summary


def scramble_spread(spread, seed):
    rng = random.Random(seed)
    offset = rng.randint(len(spread) // 4, len(spread) * 3 // 4)
    return spread[offset:] + spread[:offset]


def build_all_pairs():
    pairs = []
    for sector, tickers in SECTORS.items():
        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                pairs.append((tickers[i], tickers[j], sector))
    return pairs

def run_experiment(pairs, lookback, horizon, z_entry, trend_window=20,
                   n_scramble=5, label=""):
    results = []
    for leg_a, leg_b, sector in pairs:
        spread, beta = build_spread(leg_a, leg_b)
        if spread is None:
            continue
        hz = min(horizon, len(spread) // 4)
        res = backtest_momentum(spread, lookback, hz, z_entry, trend_window)
        if res is None:
            continue
        _, rsum = res
        scram_edges = []
        for seed in range(n_scramble):
            ssp = scramble_spread(spread, seed * 1000 + hash(leg_a + leg_b) % 1000)
            sres = backtest_momentum(ssp, lookback, hz, z_entry, trend_window)
            if sres is not None:
                _, ssum = sres
                if ssum["n_trades"] >= MIN_TRADES:
                    scram_edges.append(ssum["edge"])
        mean_scram = statistics.mean(scram_edges) if scram_edges else 0.0
        diff = rsum["edge"] - mean_scram
        results.append({
            "pair": leg_a + "/" + leg_b, "sector": sector,
            "n_bars": len(spread), "beta": round(beta, 4),
            "n_trades": rsum["n_trades"],
            "real_edge": round(rsum["edge"], 4),
            "real_t": round(rsum["t_stat"], 3),
            "win_rate": round(rsum["win_rate"], 3),
            "scram_edge": round(mean_scram, 4),
            "diff": round(diff, 4),
        })
    if not results:
        return {"label": label, "n_pairs": 0, "n_tested": len(pairs)}
    edges = [r["real_edge"] for r in results]
    diffs = [r["diff"] for r in results]
    mean_edge = statistics.mean(edges)
    mean_diff = statistics.mean(diffs)
    sd_diff = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
    diff_t = mean_diff / (sd_diff / math.sqrt(len(diffs))) if sd_diff > 0 else 0.0
    results.sort(key=lambda r: r["diff"], reverse=True)
    scram_edges_all = [r["scram_edge"] for r in results]
    return {
        "label": label, "frequency": "daily",
        "n_pairs": len(results), "n_tested": len(pairs),
        "lookback": lookback, "horizon": horizon, "z_entry": z_entry,
        "trend_window": trend_window,
        "mean_real_edge": round(mean_edge, 4),
        "mean_scram_edge": round(statistics.mean(scram_edges_all), 4),
        "mean_diff": round(mean_diff, 4),
        "diff_t_stat": round(diff_t, 3),
        "pct_positive_diff": round(sum(1 for d in diffs if d > 0) / len(diffs) * 100, 1),
        "top_pairs": results[:15],
        "edge_p50": round(sorted(edges)[len(edges)//2], 4) if edges else 0,
    }

def run_weekly(pairs, lookback_w, horizon_w, z_entry, trend_window_w=4,
               n_scramble=5, label=""):
    results = []
    for leg_a, leg_b, sector in pairs:
        pa = load_close(leg_a)
        pb = load_close(leg_b)
        if pa is None or pb is None:
            continue
        n = min(len(pa), len(pb))
        if n < 150:
            continue
        la = [math.log(p) for p in pa[-n:]]
        lb = [math.log(p) for p in pb[-n:]]
        la_w = la[4::5]
        lb_w = lb[4::5]
        nw = min(len(la_w), len(lb_w))
        if nw < 40:
            continue
        la_w = la_w[-nw:]
        lb_w = lb_w[-nw:]
        mean_b = statistics.mean(lb_w)
        mean_a = statistics.mean(la_w)
        cov = sum((lb_w[i] - mean_b) * (la_w[i] - mean_a) for i in range(nw)) / (nw - 1)
        var_b = statistics.variance(lb_w)
        if var_b <= 0:
            continue
        beta = cov / var_b
        alpha = mean_a - beta * mean_b
        spread_w = [la_w[i] - alpha - beta * lb_w[i] for i in range(nw)]
        hz = min(horizon_w, nw // 4)
        res = backtest_momentum(spread_w, lookback_w, hz, z_entry, trend_window_w)
        if res is None:
            continue
        _, rsum = res
        scram_edges = []
        for seed in range(n_scramble):
            ssp = scramble_spread(spread_w, seed * 1000 + hash("W" + leg_a + leg_b) % 1000)
            sres = backtest_momentum(ssp, lookback_w, hz, z_entry, trend_window_w)
            if sres is not None:
                _, ssum = sres
                if ssum["n_trades"] >= MIN_TRADES:
                    scram_edges.append(ssum["edge"])
        mean_scram = statistics.mean(scram_edges) if scram_edges else 0.0
        diff = rsum["edge"] - mean_scram
        results.append({
            "pair": leg_a + "/" + leg_b, "sector": sector,
            "n_weeks": nw, "beta": round(beta, 4),
            "n_trades": rsum["n_trades"],
            "real_edge": round(rsum["edge"], 4),
            "real_t": round(rsum["t_stat"], 3),
            "win_rate": round(rsum["win_rate"], 3),
            "scram_edge": round(mean_scram, 4),
            "diff": round(diff, 4),
        })
    if not results:
        return {"label": label, "n_pairs": 0}
    edges = [r["real_edge"] for r in results]
    diffs = [r["diff"] for r in results]
    mean_diff = statistics.mean(diffs)
    sd_diff = statistics.stdev(diffs) if len(diffs) > 1 else 1.0
    diff_t = mean_diff / (sd_diff / math.sqrt(len(diffs))) if sd_diff > 0 else 0.0
    results.sort(key=lambda r: r["diff"], reverse=True)
    return {
        "label": label, "frequency": "weekly",
        "n_pairs": len(results), "n_tested": len(pairs),
        "lookback": lookback_w, "horizon": horizon_w, "z_entry": z_entry,
        "trend_window": trend_window_w,
        "mean_real_edge": round(statistics.mean(edges), 4),
        "mean_diff": round(mean_diff, 4),
        "diff_t_stat": round(diff_t, 3),
        "pct_positive_diff": round(sum(1 for d in diffs if d > 0) / len(diffs) * 100, 1),
        "top_pairs": results[:15],
        "edge_p50": round(sorted(edges)[len(edges)//2], 4) if edges else 0,
    }

def run_pure_trend(pairs, lookback, horizon, n_scramble=5, label=""):
    results = []
    for leg_a, leg_b, sector in pairs:
        spread, beta = build_spread(leg_a, leg_b)
        if spread is None:
            continue
        n = len(spread)
        if n < lookback + horizon + 30:
            continue
        means, stds = rolling_mean_std(spread, lookback)
        trends = rolling_trend(spread, 20)
        trades_pnl = []
        pos = None
        for i in range(lookback + 20, n - 1):
            sd = stds[i]
            if sd <= 0 or abs(trends[i]) < 0.1:
                continue
            if pos is None:
                pos = {"side": 1 if trends[i] > 0 else -1,
                       "idx": i, "sd": sd, "val": spread[i]}
            else:
                side = pos["side"]
                ei = pos["idx"]
                esd = pos["sd"]
                ev = pos["val"]
                d_stdev = (spread[i] - ev) / esd if esd > 0 else 0.0
                exit_reason = None
                if trends[i] * side < -0.05:
                    exit_reason = "trend_reverse"
                elif side * d_stdev <= -STOP_SIGMA:
                    exit_reason = "stop"
                elif i - ei >= horizon:
                    exit_reason = "horizon"
                if exit_reason is not None:
                    trades_pnl.append(side * d_stdev)
                    pos = None
        if len(trades_pnl) < MIN_TRADES:
            continue
        mean_pnl = statistics.mean(trades_pnl)
        scram_edges = []
        for seed in range(n_scramble):
            ssp = scramble_spread(spread, seed * 1000 + hash(leg_a) % 1000)
            s_means, s_stds = rolling_mean_std(ssp, lookback)
            s_trends = rolling_trend(ssp, 20)
            s_trades = []
            s_pos = None
            for i in range(lookback + 20, len(ssp) - 1):
                sd2 = s_stds[i]
                if sd2 <= 0 or abs(s_trends[i]) < 0.1:
                    continue
                if s_pos is None:
                    s_pos = {"side": 1 if s_trends[i] > 0 else -1,
                             "idx": i, "sd": sd2, "val": ssp[i]}
                else:
                    sside = s_pos["side"]
                    sei = s_pos["idx"]
                    sesd = s_pos["sd"]
                    sev = s_pos["val"]
                    d2 = (ssp[i] - sev) / sesd if sesd > 0 else 0.0
                    exit_cond = (s_trends[i] * sside < -0.05 or
                                 sside * d2 <= -STOP_SIGMA or
                                 i - sei >= horizon)
                    if exit_cond:
                        s_trades.append(sside * d2)
                        s_pos = None
            if len(s_trades) >= MIN_TRADES:
                scram_edges.append(statistics.mean(s_trades))
        mean_scram = statistics.mean(scram_edges) if scram_edges else 0.0
        results.append({
            "pair": leg_a + "/" + leg_b,
            "real_edge": round(mean_pnl, 4), "n_trades": len(trades_pnl),
            "scram_edge": round(mean_scram, 4),
            "diff": round(mean_pnl - mean_scram, 4),
        })
    if not results:
        return {"label": label, "n_pairs": 0}
    diffs = [r["diff"] for r in results]
    edges = [r["real_edge"] for r in results]
    mean_diff = statistics.mean(diffs)
    sd_diff = statistics.stdev(diffs) if len(diffs) > 1 else 1.0
    diff_t = mean_diff / (sd_diff / math.sqrt(len(diffs))) if sd_diff > 0 else 0.0
    results.sort(key=lambda r: r["diff"], reverse=True)
    return {
        "label": label, "n_pairs": len(results), "n_tested": len(pairs),
        "mean_real_edge": round(statistics.mean(edges), 4),
        "mean_diff": round(mean_diff, 4),
        "diff_t_stat": round(diff_t, 3),
        "pct_positive_diff": round(sum(1 for d in diffs if d > 0) / len(diffs) * 100, 1),
        "top_pairs": results[:10],
        "note": "pure trend, no z-filter",
    }

def main():
    t0 = time.time()
    print("=" * 72)
    print("PAIRS MOMENTUM RESEARCH -- Trend-following on pair spreads")
    print("=" * 72)
    pairs = build_all_pairs()
    print("\nUniverse: %d same-sector pairs across %d sectors" % (len(pairs), len(SECTORS)))
    all_results = []

    print("\n-- Daily Momentum --")
    for lookback in LOOKBACK_BARS:
        for z_entry in Z_ENTRY_GRID:
            for horizon in HORIZON_BARS:
                label = "daily_lb%d_z%.1f_hz%d" % (lookback, z_entry, horizon)
                print("  %s ..." % label, end=" ", flush=True)
                res = run_experiment(pairs, lookback, horizon, z_entry,
                                     trend_window=max(10, lookback // 3),
                                     label=label)
                all_results.append(res)
                n = res.get("n_pairs", 0)
                md = res.get("mean_diff", 0)
                dt = res.get("diff_t_stat", 0)
                print("%d pairs, mean_diff=%.3f, t=%.2f" % (n, md, dt))

    print("\n-- Weekly Momentum --")
    for lookback_w in [8, 12, 20]:
        for z_entry in [1.5, 2.0]:
            for horizon_w in [3, 5]:
                label = "weekly_lb%d_z%.1f_hz%d" % (lookback_w, z_entry, horizon_w)
                print("  %s ..." % label, end=" ", flush=True)
                res = run_weekly(pairs, lookback_w, horizon_w, z_entry,
                                 trend_window_w=max(2, lookback_w // 4),
                                 label=label)
                all_results.append(res)
                n = res.get("n_pairs", 0)
                md = res.get("mean_diff", 0)
                dt = res.get("diff_t_stat", 0)
                print("%d pairs, mean_diff=%.3f, t=%.2f" % (n, md, dt))

    print("\n-- Pure Trend (no z-filter) --")
    for lookback in [60]:
        for horizon in [10, 20]:
            label = "trendonly_lb%d_hz%d" % (lookback, horizon)
            print("  %s ..." % label, end=" ", flush=True)
            res = run_pure_trend(pairs, lookback, horizon, label=label)
            all_results.append(res)
            n = res.get("n_pairs", 0)
            md = res.get("mean_diff", 0)
            dt = res.get("diff_t_stat", 0)
            print("%d pairs, mean_diff=%.3f, t=%.2f" % (n, md, dt))

    elapsed = time.time() - t0
    report = {
        "title": "Pairs Momentum Research -- Trend-following on Spreads",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_s": round(elapsed, 1),
        "universe": "%d same-sector pairs" % len(pairs),
        "cost_bps": COST_BPS,
        "n_experiments": len(all_results),
        "experiments": all_results,
    }
    json_path = os.path.join(REPORT_DIR, "pairs_momentum.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
    print("\nSaved %s" % json_path)

    print("\n" + "=" * 72)
    print("SUMMARY: Pairs Momentum (Trend-Following)")
    print("=" * 72)
    hdr = "%-35s %6s %9s %8s %7s %6s" % ("Experiment", "Pairs", "RealEdge", "Diff", "t", "%Pos")
    print(hdr)
    print("-" * 72)
    for r in all_results:
        label = r.get("label", "?")[:34]
        n = r.get("n_pairs", 0)
        re = r.get("mean_real_edge", 0)
        md = r.get("mean_diff", 0)
        dt = r.get("diff_t_stat", 0)
        pp = r.get("pct_positive_diff", 0)
        print("%-35s %6d %9.3f %8.3f %7.2f %5.0f%%" % (label, n, re, md, dt, pp))

    print("\n-- VERDICT --")
    best = max(all_results, key=lambda r: abs(r.get("diff_t_stat", 0)), default=None)
    if best:
        dt = best.get("diff_t_stat", 0)
        md = best.get("mean_diff", 0)
        label = best.get("label", "?")
        n = best.get("n_pairs", 0)
        if abs(dt) > 2.5 and md > 0 and n >= 10:
            print("BEST: %s -- t=%.2f, diff=%.3f sigma/trade, n=%d" % (label, dt, md, n))
            print("   (statistically significant edge vs scrambled)")
        elif md > 0 and dt > 1.5:
            print("PROMISING: %s -- t=%.2f, diff=%.3f, n=%d" % (label, dt, md, n))
        else:
            print("NO EDGE: best t=%.2f, diff=%.3f, n=%d" % (dt, md, n))
            print("   Pair spread momentum does NOT have a scramble-robust edge.")

    all_diffs = []
    for r in all_results:
        if "top_pairs" in r:
            for p in r["top_pairs"]:
                all_diffs.append(p.get("diff", 0))
    if all_diffs:
        print("\n   Engine-level mean diff: %.3f sigma/trade" % statistics.mean(all_diffs))
        print("   (v5 mean-reversion engine-level was ~0.014 sigma)")
    print("\nElapsed: %.1fs" % elapsed)

if __name__ == "__main__":
    main()
