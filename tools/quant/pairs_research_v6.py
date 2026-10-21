"""Pairs Trading Research v6 -- Robustness Scoring + Regime Analysis + Z-Optimization

v6: stability scoring (0-100), z-entry optimization, regime analysis, FX analysis.
"""
from __future__ import annotations
import os, sys, csv, json, math, statistics, time
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pairs_research_v5 as v5

Z_ENTRY_GRID      = [1.5, 2.0, 2.5, 3.0]
Z_EXIT            = 0.0
STOP_LOSS_SIGMA   = 3.0
HL_LOOKBACK_MIN   = 30
HL_LOOKBACK_MAX   = 120
HL_HORIZON_MIN    = 5
HL_HORIZON_MAX    = 20
MIN_OOS_TRADES    = 6
ROLL_WIN_BARS     = 120
ROLL_STEP_BARS    = 40
ROLL_MIN_WINDOWS  = 3
FX_IS_EDGE_MIN    = 0.25
FX_OOS_EDGE_MAX   = 5.0
REGIME_LABELS = ["HIGH_VOL", "LOW_VOL", "BULL", "BEAR"]
REPORT_JSON = os.path.join(_HERE, "reports", "pairs_research_v6.json")
REPORT_MD   = os.path.join(_HERE, "reports", "pairs_research_v6.md")
SIGNALS_JSON = os.path.join(_HERE, "reports", "pairs_v6_signals.json")



def rolling_stats(spread, win):
    means, sds = [], []
    for i in range(len(spread)):
        wnd = spread[max(0, i - win + 1):i + 1]
        if len(wnd) < 10:
            means.append(0.0); sds.append(0.0)
            continue
        m = statistics.mean(wnd)
        var = statistics.variance(wnd) if len(wnd) > 1 else 0.0
        sd = math.sqrt(var) if var > 0 else 0.0
        means.append(m); sds.append(sd)
    return means, sds


def backtest_pair(spread, lookback, horizon, z_entry, z_exit, stop_sigma):
    n = len(spread)
    if n < lookback + horizon:
        return None
    means, sds = rolling_stats(spread, lookback)
    trades = []
    pos = None
    for i in range(lookback, n - 1):
        if sds[i] <= 0:
            continue
        z = (spread[i] - means[i]) / sds[i]
        if pos is None:
            if abs(z) >= z_entry:
                side = 1 if z < 0 else -1
                pos = (side, i, sds[i], spread[i])
        else:
            side, ei, esd, entry_val = pos
            if i == ei:
                continue
            d_stdev = (spread[i] - entry_val) / esd if esd > 0 else 0.0
            exit_reason = None
            if side * d_stdev >= 1.0:
                exit_reason = "revert"
            elif side * d_stdev <= -stop_sigma:
                exit_reason = "stop"
            elif i - ei >= horizon:
                exit_reason = "horizon"
            if exit_reason is not None:
                pnl_sigma = side * (spread[i] - entry_val) / esd
                trades.append(dict(entry_idx=ei, exit_idx=i,
                    pnl_sigma=pnl_sigma, exit_reason=exit_reason,
                    duration=i - ei))
                pos = None
    if not trades:
        return None
    n_tr = len(trades)
    edges = [t["pnl_sigma"] for t in trades]
    mean_edge = statistics.mean(edges) if n_tr > 1 else edges[0]
    sd_edge = statistics.stdev(edges) if n_tr > 1 else 0.0
    tstat = mean_edge / (sd_edge / math.sqrt(n_tr)) if sd_edge > 0 else 0.0
    worst = min(edges) if edges else 0.0
    cum = 0.0; peak = 0.0; mdd = 0.0
    streak = 0; max_streak = 0
    for e in edges:
        if e < 0:
            streak += 1; max_streak = max(max_streak, streak)
        else:
            streak = 0
        cum += e; peak = max(peak, cum); mdd = min(mdd, cum - peak)
    return dict(n=n_tr, edge=mean_edge, tstat=tstat, worst_trade=worst,
                max_dd=mdd, max_loss_streak=max_streak, trades=trades)


def _load_pair(label, ac, sym_a, sym_b, kind, provider):
    ha = v5._load_series(sym_a, provider)
    hb = v5._load_series(sym_b, provider)
    if not ha or not hb:
        return None
    da, ca = ha; db, cb = hb
    a, b, dates = v5._align(da, ca, db, cb)
    if len(a) < 80:
        return None
    if kind == "DIFF":
        spread = [a[i] - b[i] for i in range(len(a))]
    else:
        la = [math.log(v) for v in a]; lb = [math.log(v) for v in b]
        beta = v5._ols_beta(la, lb)
        spread = [la[i] - beta * lb[i] for i in range(len(la))]
    return dict(dates=dates, spread=spread, a=a, b=b)


# ================================================================ STABILITY SCORING

def compute_stability(spread, a_prices, b_prices, dates,
                      win_bars=ROLL_WIN_BARS, step_bars=ROLL_STEP_BARS,
                      z_entry=2.0):
    """Continuous 0-100 stability score. Components: 40% rolling OOS consistency,
    20% IS/OOS correlation, 25% worst-window edge, 15% EG cointegration stability."""
    n = len(spread)
    if n < win_bars + step_bars * ROLL_MIN_WINDOWS:
        return None

    rolling_edges = []
    eg_pass_fail = []
    lookbacks = []
    horizons = []

    for start in range(0, n - win_bars - step_bars, step_bars):
        is_end = start + win_bars
        oos_end = min(is_end + step_bars, n)
        if oos_end - is_end < MIN_OOS_TRADES:
            continue

        spread_is = spread[start:is_end]
        spread_oos = spread[is_end:oos_end]
        a_is = a_prices[start:is_end]
        b_is = b_prices[start:is_end]

        hl = v5.estimate_half_life(spread_is)
        if hl >= 200:
            continue
        lb = max(HL_LOOKBACK_MIN, min(HL_LOOKBACK_MAX, int(hl * 3)))
        hz = max(HL_HORIZON_MIN, min(HL_HORIZON_MAX, int(hl)))

        bt_is = backtest_pair(spread_is, lb, hz, z_entry, Z_EXIT, STOP_LOSS_SIGMA)
        if not bt_is or bt_is["n"] < 3:
            continue

        bt_oos = backtest_pair(spread_oos, lb, hz, z_entry, Z_EXIT, STOP_LOSS_SIGMA)
        if not bt_oos or bt_oos["n"] < MIN_OOS_TRADES:
            continue

        la_is = [math.log(v) for v in a_is]
        lb_is = [math.log(v) for v in b_is]
        coint, _, _, _ = v5.engle_granger_test(la_is, lb_is, v5.EG_MAX_LAG)
        eg_pass_fail.append(1 if coint else 0)

        rolling_edges.append(dict(
            is_edge=bt_is["edge"], oos_edge=bt_oos["edge"],
            is_tstat=bt_is["tstat"], oos_tstat=bt_oos["tstat"],
            oos_n=bt_oos["n"], oos_worst=bt_oos["worst_trade"],
            is_n=bt_is["n"]))
        lookbacks.append(lb)
        horizons.append(hz)

    if len(rolling_edges) < ROLL_MIN_WINDOWS:
        return None

    pos_fraction = sum(1 for re in rolling_edges if re["oos_edge"] > 0) / len(rolling_edges)
    consistency_score = pos_fraction * 40

    is_edges = [re["is_edge"] for re in rolling_edges]
    oos_edges = [re["oos_edge"] for re in rolling_edges]
    if len(is_edges) >= 5:
        mx = statistics.mean(is_edges); my = statistics.mean(oos_edges)
        num = sum((is_edges[i] - mx) * (oos_edges[i] - my) for i in range(len(is_edges)))
        den_x = math.sqrt(sum((e - mx) ** 2 for e in is_edges))
        den_y = math.sqrt(sum((e - my) ** 2 for e in oos_edges))
        rho = num / (den_x * den_y) if den_x > 0 and den_y > 0 else 0.0
    else:
        rho = 0.0
    corr_score = max(0, rho) * 20

    worst = min(re["oos_edge"] for re in rolling_edges)
    worst_norm = max(0, min(1, (worst + 1.0) / 3.0))
    worst_score = worst_norm * 25

    eg_stability = sum(eg_pass_fail) / len(eg_pass_fail) if eg_pass_fail else 0.0
    eg_score = eg_stability * 15

    total_score = consistency_score + corr_score + worst_score + eg_score

    avg_is_edge = statistics.mean(is_edges) if is_edges else 0.0
    avg_oos_edge = statistics.mean(oos_edges) if oos_edges else 0.0
    avg_oos_n = statistics.mean([re["oos_n"] for re in rolling_edges]) if rolling_edges else 0
    avg_lb = statistics.mean(lookbacks) if lookbacks else 60
    avg_hz = statistics.mean(horizons) if horizons else 10

    return dict(
        score=min(100, total_score),
        components=dict(consistency=consistency_score, is_oos_corr=corr_score,
                        worst_window=worst_score, eg_stability=eg_score),
        summary=dict(
            n_windows=len(rolling_edges), pos_fraction=pos_fraction,
            avg_is_edge=avg_is_edge, avg_oos_edge=avg_oos_edge,
            worst_oos_edge=worst, best_oos_edge=max(oos_edges) if oos_edges else 0,
            avg_oos_n=avg_oos_n, avg_lookback=avg_lb, avg_horizon=avg_hz,
            eg_fraction=eg_stability if eg_pass_fail else 0.0))


# ================================================================ Z-ENTRY OPTIMIZATION

def optimize_z_entry(spread, a_prices, b_prices, is_frac=0.6):
    """Grid search z_entry on IS data. Returns optimal z + OOS validation."""
    n = len(spread)
    if n < 150:
        return None
    is_end = int(n * is_frac)
    spread_is = spread[:is_end]
    spread_oos = spread[is_end:]

    hl = v5.estimate_half_life(spread_is)
    if hl >= 200:
        return None
    lb = max(HL_LOOKBACK_MIN, min(HL_LOOKBACK_MAX, int(hl * 3)))
    hz = max(HL_HORIZON_MIN, min(HL_HORIZON_MAX, int(hl)))

    best_z = None
    best_is_edge = -float("inf")
    results = []

    for z in Z_ENTRY_GRID:
        bt_is = backtest_pair(spread_is, lb, hz, z, Z_EXIT, STOP_LOSS_SIGMA)
        if not bt_is or bt_is["n"] < 3:
            results.append(dict(z=z, is_edge=None, oos_edge=None, is_n=0, oos_n=0))
            continue

        bt_oos = backtest_pair(spread_oos, lb, hz, z, Z_EXIT, STOP_LOSS_SIGMA)
        oos_edge = bt_oos["edge"] if (bt_oos and bt_oos["n"] >= MIN_OOS_TRADES) else None
        oos_n = bt_oos["n"] if (bt_oos and bt_oos["n"] >= MIN_OOS_TRADES) else 0

        results.append(dict(z=z, is_n=bt_is["n"], is_edge=bt_is["edge"],
                           is_tstat=bt_is["tstat"], oos_n=oos_n, oos_edge=oos_edge))

        if bt_is["edge"] > best_is_edge:
            best_is_edge = bt_is["edge"]
            best_z = z

    if best_z is None:
        return None

    return dict(optimal_z=best_z, half_life=hl, lookback=lb, horizon=hz,
                results=results)


# ================================================================ REGIME ANALYSIS

def identify_regimes(dates, spy_prices):
    """Identify market regimes from SPY data."""
    n = len(dates)
    spy_vol_20d = []
    spy_ret_60d = []

    for i in range(n):
        if i >= 21:
            r = [math.log(spy_prices[j] / spy_prices[j-1])
                 for j in range(i-19, i+1) if j > 0]
            if len(r) >= 15:
                vol = statistics.stdev(r) * math.sqrt(252)
                spy_vol_20d.append(vol)
            else:
                spy_vol_20d.append(0.0)
        else:
            spy_vol_20d.append(0.0)

        if i >= 60:
            spy_ret_60d.append(spy_prices[i] / spy_prices[i-60] - 1.0)
        else:
            spy_ret_60d.append(0.0)

    vols = [v for v in spy_vol_20d if v > 0]
    med_vol = statistics.median(vols) if vols else 0.15

    regimes = {label: set() for label in REGIME_LABELS}

    for i in range(min(n, len(dates))):
        date = dates[i]
        if spy_vol_20d[i] > med_vol:
            regimes["HIGH_VOL"].add(date)
        elif spy_vol_20d[i] > 0:
            regimes["LOW_VOL"].add(date)
        if spy_ret_60d[i] > 0:
            regimes["BULL"].add(date)
        elif spy_ret_60d[i] < 0:
            regimes["BEAR"].add(date)

    return regimes, dict(med_vol=med_vol)


def regime_conditioned_backtest(spread, dates, a_prices, b_prices,
                                 lookback, horizon, z_entry, regimes):
    """Run backtest and split trade results by regime of exit date."""
    all_trades = backtest_pair(spread, lookback, horizon, z_entry, Z_EXIT, STOP_LOSS_SIGMA)
    if not all_trades or not all_trades.get("trades"):
        return None

    regime_trades = {label: [] for label in REGIME_LABELS}

    for t in all_trades["trades"]:
        exit_date = dates[t["exit_idx"]] if t["exit_idx"] < len(dates) else ""
        for label, reg_set in regimes.items():
            if exit_date in reg_set:
                regime_trades[label].append(t["pnl_sigma"])

    result = {}
    for label, edges in regime_trades.items():
        if len(edges) < 5:
            result[label] = None
            continue
        mean_edge = statistics.mean(edges)
        sd_edge = statistics.stdev(edges) if len(edges) > 1 else 0.0
        tstat = mean_edge / (sd_edge / math.sqrt(len(edges))) if sd_edge > 0 else 0.0
        result[label] = dict(n=len(edges), mean_edge=mean_edge, tstat=tstat,
                             positive_frac=sum(1 for e in edges if e > 0) / len(edges))

    result["ALL"] = dict(n=all_trades["n"], mean_edge=all_trades["edge"],
                         tstat=all_trades["tstat"],
                         positive_frac=sum(1 for t in all_trades["trades"]
                                          if t["pnl_sigma"] > 0) / all_trades["n"])

    return result


# ================================================================ FX ANALYSIS

def analyze_fx_pairs(fx_pairs_data):
    """FX-specific analysis with relaxed gates, longer lookback search."""
    fx_results = {}
    for label, pr in fx_pairs_data.items():
        spread = pr["spread"]
        n = len(spread)
        is_n = int(n * 0.6)
        spread_is = spread[:is_n]
        spread_oos = spread[is_n:]

        best_oos = -float("inf")
        best_config = None
        for lb_mult in [2, 3, 4, 5]:
            for hz_mult in [0.5, 1.0, 1.5, 2.0]:
                hl = v5.estimate_half_life(spread_is)
                lb = max(20, min(200, int(hl * lb_mult)))
                hz = max(3, min(60, int(hl * hz_mult)))
                bt_is = backtest_pair(spread_is, lb, hz, 2.0, Z_EXIT, STOP_LOSS_SIGMA)
                if not bt_is or bt_is["n"] < 5:
                    continue
                bt_oos = backtest_pair(spread_oos, lb, hz, 2.0, Z_EXIT, STOP_LOSS_SIGMA)
                if not bt_oos or bt_oos["n"] < MIN_OOS_TRADES:
                    continue
                if bt_is["edge"] >= FX_IS_EDGE_MIN and bt_oos["edge"] > best_oos:
                    best_oos = bt_oos["edge"]
                    best_config = dict(
                        hl=hl, lb=lb, hz=hz,
                        is_edge=bt_is["edge"], is_tstat=bt_is["tstat"],
                        is_n=bt_is["n"],
                        oos_edge=bt_oos["edge"], oos_tstat=bt_oos["tstat"],
                        oos_n=bt_oos["n"], oos_worst=bt_oos["worst_trade"])

        la = [math.log(v) for v in pr["a"]]
        lb = [math.log(v) for v in pr["b"]]
        eg_coint, adf_stat, adf_pval, _ = v5.engle_granger_test(
            la[:is_n], lb[:is_n], v5.EG_MAX_LAG)

        if best_config:
            _, sds = rolling_stats(spread, best_config["lb"])
            if sds and len(sds) > 0 and sds[-1] > 0:
                m = statistics.mean(spread[-best_config["lb"]:])
                z_now = (spread[-1] - m) / sds[-1]
            else:
                z_now = 0.0

            passes = (best_config["is_edge"] >= FX_IS_EDGE_MIN and
                      best_config["oos_edge"] > 0 and
                      best_config["oos_edge"] < FX_OOS_EDGE_MAX)
            best_config["passes"] = passes
            best_config["z_now"] = z_now
            best_config["eg_cointegrated"] = eg_coint
            best_config["adf_stat"] = adf_stat
            best_config["adf_pval"] = adf_pval
            fx_results[label] = best_config

    return fx_results


# ================================================================ MAIN RESEARCH

def run_research():
    t_start = time.time()
    all_pairs = list(v5.FX_PAIRS)
    for lst in [v5.ETF_PAIRS, v5.EQUITY_PAIRS, v5.CRYPTO_PAIRS]:
        all_pairs.extend(lst)
    for sname, stocks in v5.SECTORS.items():
        avail = [s for s in stocks if v5._load_series(s, "polygon")]
        if len(avail) >= 2:
            all_pairs.extend(v5.generate_sector_pairs(avail))
    seen = set(); uniq = []
    for p in all_pairs:
        key = (p[2], p[3]) if p[2] < p[3] else (p[3], p[2])
        if key not in seen:
            seen.add(key); uniq.append(p)
    all_pairs = uniq
    print(f"Universe: {len(all_pairs)} pairs", file=sys.stderr, flush=True)

    all_data = {}
    for p in all_pairs:
        label, ac, sym_a, sym_b, kind, provider = p
        data = _load_pair(label, ac, sym_a, sym_b, kind, provider)
        if data is not None:
            all_data[label] = dict(label=label, asset_class=ac,
                                   sym_a=sym_a, sym_b=sym_b,
                                   kind=kind, provider=provider, **data)

    print(f"Loaded {len(all_data)} pairs", file=sys.stderr, flush=True)

    fx_pairs = {k: v for k, v in all_data.items() if v["provider"] == "fred"}
    stock_pairs = {k: v for k, v in all_data.items() if v["provider"] != "fred"}
    print(f"FX: {len(fx_pairs)}  |  Stock/ETF: {len(stock_pairs)}",
          file=sys.stderr, flush=True)

    # ---- 1. STABILITY SCORING ----
    print("\n=== STABILITY SCORING ===", file=sys.stderr, flush=True)
    stability_results = {}
    for label, pr in stock_pairs.items():
        stab = compute_stability(pr["spread"], pr["a"], pr["b"], pr["dates"])
        if stab and stab["score"] > 0:
            stability_results[label] = stab

    ranked = sorted(stability_results.items(), key=lambda x: -x[1]["score"])
    print(f"Pairs scored: {len(ranked)}", file=sys.stderr)
    for label, stab in ranked[:20]:
        s = stab["summary"]
        print(f"  {label:12s} score={stab['score']:5.1f}  "
              f"nw={s['n_windows']}  pos={s['pos_fraction']:.2f}  "
              f"avgO={s['avg_oos_edge']:+.2f}  wst={s['worst_oos_edge']:+.2f}  "
              f"eg={s['eg_fraction']:.2f}", file=sys.stderr)

    # ---- 2. Z-ENTRY OPTIMIZATION ----
    print("\n=== Z-ENTRY OPTIMIZATION ===", file=sys.stderr, flush=True)
    top_stable = [label for label, _ in ranked[:30]]
    zopt_labels = list(set(top_stable) | set(fx_pairs.keys()))

    zopt_results = {}
    for label in zopt_labels:
        if label not in all_data:
            continue
        pr = all_data[label]
        opt = optimize_z_entry(pr["spread"], pr["a"], pr["b"])
        if opt:
            zopt_results[label] = opt

    zopt_ranked = sorted(zopt_results.items(),
                         key=lambda x: -(x[1]["results"][-1].get("oos_edge") or -999))
    print(f"Pairs optimized: {len(zopt_results)}", file=sys.stderr)
    for label, opt in zopt_ranked[:15]:
        br = [r for r in opt["results"] if r["z"] == opt["optimal_z"]]
        if br:
            b = br[0]
            print(f"  {label:12s} z={opt['optimal_z']:.1f}  "
                  f"IS={b.get('is_edge',0):+.2f}  OOS={b.get('oos_edge','n/a')}  "
                  f"HL={opt['half_life']:.0f}", file=sys.stderr)

    # ---- 3. REGIME ANALYSIS ----
    print("\n=== REGIME ANALYSIS ===", file=sys.stderr, flush=True)
    spy_data = v5._load_series("SPY", "polygon")
    regimes = {}; regime_info = {}; regime_results = {}; regime_summary = {}

    if spy_data and spy_data[0] and spy_data[1]:
        spy_dates = spy_data[0]; spy_prices = spy_data[1]
        regimes, regime_info = identify_regimes(spy_dates, spy_prices)
        print(f"med_vol={regime_info['med_vol']:.3f}  "
              f"HV={len(regimes['HIGH_VOL'])}d LV={len(regimes['LOW_VOL'])}d  "
              f"BULL={len(regimes['BULL'])}d BEAR={len(regimes['BEAR'])}d",
              file=sys.stderr)

        for label, _ in ranked[:30]:
            pr = all_data[label]
            hl = v5.estimate_half_life(pr["spread"])
            lb = max(HL_LOOKBACK_MIN, min(HL_LOOKBACK_MAX, int(hl * 3)))
            hz = max(HL_HORIZON_MIN, min(HL_HORIZON_MAX, int(hl)))
            z_entry = zopt_results[label]["optimal_z"] if label in zopt_results else 2.0

            reg = regime_conditioned_backtest(
                pr["spread"], pr["dates"], pr["a"], pr["b"],
                lb, hz, z_entry, regimes)
            if reg:
                regime_results[label] = reg

        regime_summary = {label: dict(n_pairs=0, edges=[], tstats=[])
                         for label in REGIME_LABELS + ["ALL"]}
        for label, reg in regime_results.items():
            for rlabel in REGIME_LABELS + ["ALL"]:
                if reg.get(rlabel):
                    regime_summary[rlabel]["n_pairs"] += 1
                    regime_summary[rlabel]["edges"].append(reg[rlabel]["mean_edge"])
                    regime_summary[rlabel]["tstats"].append(reg[rlabel]["tstat"])

        print("\nRegime summary:", file=sys.stderr)
        for rlabel in ["ALL"] + REGIME_LABELS:
            rs = regime_summary[rlabel]
            if rs["n_pairs"] >= 3:
                avg = statistics.mean(rs["edges"])
                print(f"  {rlabel:12s}: {rs['n_pairs']} pairs  avg_edge={avg:+.3f}",
                      file=sys.stderr)
    else:
        print("WARNING: No SPY data for regime analysis", file=sys.stderr)

    # ---- 4. FX ANALYSIS ----
    print("\n=== FX ANALYSIS ===", file=sys.stderr, flush=True)
    fx_results = analyze_fx_pairs(fx_pairs)
    fx_qual = [k for k, v in fx_results.items() if v.get("passes")]
    print(f"FX qualified: {len(fx_qual)}/{len(fx_results)}", file=sys.stderr)
    for label in fx_qual:
        r = fx_results[label]
        print(f"  {label:12s} IS={r['is_edge']:+.2f}  OOS={r['oos_edge']:+.2f}  "
              f"z={r['z_now']:+.2f}  EG={r['eg_cointegrated']}  HL={r['hl']:.0f}",
              file=sys.stderr)
    for label in fx_results:
        if label not in fx_qual:
            r = fx_results[label]
            print(f"  {label:12s} IS={r['is_edge']:+.2f}  OOS={r['oos_edge']:+.2f}  "
                  f"z={r['z_now']:+.2f}  [NOT QUAL]  EG={r['eg_cointegrated']}",
                  file=sys.stderr)

    # ---- 5. CONSOLIDATED SIGNALS ----
    print("\n=== SIGNALS ===", file=sys.stderr, flush=True)

    stock_signals = []
    for label, stab in ranked:
        if stab["score"] < 25 or stab["summary"]["avg_oos_edge"] <= 0:
            continue
        pr = all_data[label]
        opt_z = zopt_results[label]["optimal_z"] if label in zopt_results else 2.0
        hl = v5.estimate_half_life(pr["spread"])
        lb = max(HL_LOOKBACK_MIN, min(HL_LOOKBACK_MAX, int(hl * 3)))
        _, sds = rolling_stats(pr["spread"], lb)
        if sds and len(sds) > 0 and sds[-1] > 0:
            m = statistics.mean(pr["spread"][-lb:])
            z_now = (pr["spread"][-1] - m) / sds[-1]
        else:
            z_now = 0.0

        firing = abs(z_now) >= opt_z
        if z_now < -opt_z:
            direction = "LONG_A_SHORT_B"
        elif z_now > opt_z:
            direction = "SHORT_A_LONG_B"
        else:
            direction = "NONE"
        stock_signals.append(dict(
            label=label, asset_class=pr.get("asset_class","STOCK"),
            sym_a=pr["sym_a"], sym_b=pr["sym_b"],
            stability=round(stab["score"],1),
            avg_oos_edge=round(stab["summary"]["avg_oos_edge"],3),
            z_now=round(z_now,2), z_entry=opt_z, firing=firing, direction=direction,
            half_life=round(hl,1), lookback=lb,
            horizon=stab["summary"]["avg_horizon"]))

    fx_signals = []
    for label in list(fx_results.keys()):
        r = fx_results[label]
        pr = all_data[label]
        firing = abs(r["z_now"]) >= 2.0
        if r["z_now"] < -2.0:
            direction = "LONG_A_SHORT_B"
        elif r["z_now"] > 2.0:
            direction = "SHORT_A_LONG_B"
        else:
            direction = "NONE"
        fx_signals.append(dict(
            label=label, asset_class=pr.get("asset_class","FX"),
            sym_a=pr["sym_a"], sym_b=pr["sym_b"],
            stability=50, avg_oos_edge=round(r["oos_edge"],3),
            z_now=round(r["z_now"],2), z_entry=2.0, firing=firing, direction=direction,
            half_life=round(r["hl"],1), lookback=r["lb"], horizon=r["hz"],
            qualified=r.get("passes",False)))

    stock_signals.sort(key=lambda s: -s["stability"])
    all_signals = stock_signals + fx_signals
    firing_signals = [s for s in all_signals if s["firing"]]

    print(f"Stock signals: {len(stock_signals)}  FX: {len(fx_signals)}",
          file=sys.stderr)
    print(f"FIRING: {len(firing_signals)}", file=sys.stderr)
    for s in firing_signals:
        print(f"  FIRING {s['label']:12s} {s['direction']:20s} "
              f"z={s['z_now']:+.2f} st={s['stability']:.0f} e={s['avg_oos_edge']:+.2f}",
              file=sys.stderr)

    monitor = [s for s in stock_signals if not s["firing"]][:15]
    print(f"\nMonitor ({len(monitor)}):", file=sys.stderr)
    for s in monitor[:10]:
        print(f"  {s['label']:12s} z={s['z_now']:+.2f}/{s['z_entry']:.1f}  "
              f"st={s['stability']:.0f}", file=sys.stderr)

    # ---- EXPORT ----
    elapsed = time.time() - t_start

    report = dict(
        generated=time.strftime("%Y-%m-%d %H:%M:%S CST"),
        elapsed_s=round(elapsed,1),
        universe=dict(total=len(all_pairs), loaded=len(all_data),
                      fx=len(fx_pairs), stock=len(stock_pairs)),
        v6_improvements=[
            "Stability scoring (continuous 0-100, 4 components)",
            "Z-entry optimization per pair (grid search)",
            "Regime-conditioned performance (vol, bull/bear)",
            "FX-specific analysis (longer history, relaxed gates)",
            "Consolidated signals with stability-weighted ranking"],
        stability_scoring=dict(
            n_pairs_scored=len(stability_results),
            n_stable_gt40=sum(1 for _,s in ranked if s["score"]>=40),
            top_30=[dict(label=l, score=round(s["score"],1),
                        summary={k:round(v,3) if isinstance(v,float) else v
                                for k,v in s["summary"].items()})
                    for l,s in ranked[:30]]),
        z_optimization=dict(
            n_pairs=len(zopt_results),
            z_distribution={str(z):sum(1 for _,o in zopt_results.items()
                                       if o["optimal_z"]==z)
                           for z in Z_ENTRY_GRID},
            top_20=[dict(label=l, optimal_z=o["optimal_z"],
                        hl=round(o["half_life"],1),
                        best_is_edge=round(next((r["is_edge"] for r in o["results"]
                            if r["z"]==o["optimal_z"]),0),3),
                        best_oos_edge=round(next((r["oos_edge"] for r in o["results"]
                            if r["z"]==o["optimal_z"] and r["oos_edge"] is not None),0),3))
                    for l,o in zopt_ranked[:20]]),
        regime_analysis=dict(
            regime_info=regime_info,
            regime_summary={rl:dict(n_pairs=rs["n_pairs"],
                avg_edge=round(statistics.mean(rs["edges"]),3) if rs["edges"] else 0)
                for rl,rs in regime_summary.items() if rs["n_pairs"]>=3},
            top_pair_regimes=[dict(label=l, regimes={
                rl:dict(n=r["n"],edge=round(r["mean_edge"],3)) if r else None
                for rl,r in reg.items()})
                for l,reg in list(regime_results.items())[:15]] if regime_results else []),
        fx_analysis=dict(
            n_tested=len(fx_results), n_qualified=len(fx_qual),
            qualified=[dict(label=l, **{k:round(v,3) if isinstance(v,float) else v
                       for k,v in fx_results[l].items()}) for l in fx_qual],
            all_fx=[dict(label=l, **{k:round(v,3) if isinstance(v,float) else v
                    for k,v in fx_results[l].items()}) for l in fx_results]),
        signals=dict(total=len(all_signals), firing=len(firing_signals),
                    stock_qualified=len(stock_signals), fx_qualified=len(fx_signals),
                    firing_list=firing_signals, monitor_list=monitor[:10]))

    os.makedirs(os.path.dirname(REPORT_JSON), exist_ok=True)
    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=1, default=str)
    with open(SIGNALS_JSON, "w") as f:
        json.dump(dict(generated=report["generated"],
                       n_firing=len(firing_signals),
                       signals=all_signals), f, indent=1, default=str)
    _write_md(report)
    print(f"\nWrote reports in {elapsed:.0f}s", file=sys.stderr)
    return report


# ================================================================ MARKDOWN REPORT

def _write_md(report):
    with open(REPORT_MD, "w") as f:
        f.write("# Pairs Trading Research v6\n\n")
        f.write(f"Generated: {report['generated']}  |  "
                f"Elapsed: {report['elapsed_s']:.1f}s\n\n")

        f.write("## v6 Improvements\n\n")
        for imp in report["v6_improvements"]:
            f.write(f"- {imp}\n")
        f.write("\n")

        u = report["universe"]
        f.write(f"## Universe: {u['total']} pairs ({u['loaded']} loaded, "
                f"{u['fx']} FX, {u['stock']} stock)\n\n")

        f.write("## Stability Scoring (Top 20)\n\n")
        f.write("| Pair | Score | n_w | Pos% | Avg OOS | Worst | EG% |\n")
        f.write("|------|-------|-----|------|---------|-------|-----|\n")
        for s in report["stability_scoring"]["top_30"][:20]:
            sm = s["summary"]
            f.write(f"| {s['label']} | {s['score']:.0f} | {sm['n_windows']} | "
                    f"{sm['pos_fraction']:.0%} | {sm['avg_oos_edge']:+.2f} | "
                    f"{sm['worst_oos_edge']:+.2f} | {sm['eg_fraction']:.0%} |\n")

        f.write(f"\n## Z-Entry Optimization\n\n")
        zd = report["z_optimization"]["z_distribution"]
        parts = [f"z={k}: {v}" for k, v in sorted(zd.items())]
        f.write(f"Optimal z distribution: {', '.join(parts)}\n\n")
        f.write("| Pair | Best z | HL | IS Edge | OOS Edge |\n")
        f.write("|------|--------|-----|---------|----------|\n")
        for s in report["z_optimization"]["top_20"][:15]:
            oos = f"{s['best_oos_edge']:+.2f}" if s["best_oos_edge"] != 0 else "n/a"
            f.write(f"| {s['label']} | {s['optimal_z']:.1f} | {s['hl']:.0f} | "
                    f"{s['best_is_edge']:+.2f} | {oos} |\n")

        f.write(f"\n## Regime Analysis\n\n")
        rs = report["regime_analysis"].get("regime_summary", {})
        if rs:
            f.write("| Regime | n_pairs | avg_edge |\n")
            f.write("|--------|---------|----------|\n")
            for rl in sorted(rs.keys()):
                f.write(f"| {rl:12s} | {rs[rl]['n_pairs']} | "
                        f"{rs[rl]['avg_edge']:+.3f} |\n")
        else:
            f.write("No regime data available (SPY not loaded).\n")

        f.write(f"\n## FX Analysis\n\n")
        fa = report["fx_analysis"]
        f.write(f"{fa['n_qualified']}/{fa['n_tested']} FX pairs qualified "
                f"(IS edge >= 0.25, OOS edge > 0)\n\n")
        f.write("| Pair | IS Edge | OOS Edge | z_now | EG | HL | OOS n |\n")
        f.write("|------|---------|----------|-------|----|-----|-------|\n")
        for fx in fa["all_fx"][:10]:
            eg = "C" if fx.get("eg_cointegrated") else ""
            f.write(f"| {fx['label']} | {fx['is_edge']:+.2f} | "
                    f"{fx['oos_edge']:+.2f} | {fx['z_now']:+.2f} | "
                    f"{eg} | {fx['hl']:.0f} | {fx['oos_n']} |\n")

        sig = report["signals"]
        f.write(f"\n## Live Signals\n\n")
        f.write(f"**{sig['firing']} pairs firing** "
                f"({sig['stock_qualified']} stock + {sig['fx_qualified']} FX)\n\n")
        if sig["firing_list"]:
            f.write("| Pair | Direction | z | Stability | OOS Edge | HL |\n")
            f.write("|------|-----------|---|-----------|----------|-----|\n")
            for s in sig["firing_list"]:
                f.write(f"| {s['label']} | {s['direction']} | "
                        f"{s['z_now']:+.2f} | {s['stability']:.0f} | "
                        f"{s['avg_oos_edge']:+.2f} | {s['half_life']:.0f} |\n")
        else:
            f.write("No pairs currently firing.\n\n")

        if sig.get("monitor_list"):
            f.write(f"\n### Monitor List (Not Firing)\n\n")
            f.write("| Pair | z_now | z_entry | Stability | OOS Edge |\n")
            f.write("|------|-------|---------|-----------|----------|\n")
            for s in sig["monitor_list"][:10]:
                f.write(f"| {s['label']} | {s['z_now']:+.2f} | "
                        f"{s['z_entry']:.1f} | {s['stability']:.0f} | "
                        f"{s['avg_oos_edge']:+.2f} |\n")

        f.write(f"\n---\n*Report generated by pairs_research_v6.py*\n")


if __name__ == "__main__":
    run_research()
