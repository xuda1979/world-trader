#!/usr/bin/env python3
import os, sys, json, math, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)

from pairs_kalman import kalman_spread, engle_granger_test

OOS_FRAC = 0.40; Z_ENTRY = 2.0; Z_EXIT = 0.0
HL_LOOKBACK_MIN = 30; HL_LOOKBACK_MAX = 120
HL_HORIZON_MIN = 5; HL_HORIZON_MAX = 20
VIX_MAX_PAIR = 25.0; FDR_ALPHA = 0.05
MIN_SAMPLE = 20; MIN_OOS_SAMPLE = 8
KALMAN_DELTA = 1e-5; KALMAN_VT = 1e-3; EG_MAX_LAG = 5

print("PAIRS RESEARCH v2 - Kalman + Cointegration + FX Gates")
print("=" * 60)
print("Importing v1 infrastructure...")
import pairs_research_v2 as v1
print("v1 OK (" + str(len(v1.FX_PAIRS) + len(v1.ETF_PAIRS) + len(v1.EQUITY_PAIRS) + len(v1.CRYPTO_PAIRS)) + " base pairs)")
print("v2 (kalman + EG) OK")

COST_STOCK = 0.0010; COST_ETF = 0.0010; COST_CRYPTO = 0.0020; COST_FX = 0.0008

def _cost_for(ac):
    m = {"STOCK": COST_STOCK, "ETF": COST_ETF, "CRYPTO": COST_CRYPTO, "FX": COST_FX, "CROSS": COST_CRYPTO}
    return m.get(ac, COST_STOCK)

def _p_from_t(t):
    if t is None: return 1.0
    return math.erfc(abs(t) / math.sqrt(2))

def _bonferroni_t(m):
    m = max(1, int(m)); alpha = 0.05 / m; p = 1 - alpha / 2
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        z = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= ph:
        q = p - 0.5; r = q*q
        z = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        z = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    return max(2.0, z)

def qualifies_v2(bt, n_tests=1, use_fdr=False, all_pvals=None):
    ac = bt.get("asset_class", "STOCK")
    if not bt: return False
    if bt["n"] < MIN_SAMPLE: return False
    if ac == "FX":
        is_edge_min = 0.30; oos_edge_max = 5.0; worst_trade_max = -5.0; max_dd_max = 10.0
    else:
        is_edge_min = 0.60; oos_edge_max = 3.0; worst_trade_max = -3.0; max_dd_max = 6.0
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
    if worst is not None and worst < worst_trade_max: return False
    max_dd = bt.get("max_dd")
    if max_dd is not None and max_dd > max_dd_max: return False
    streak = bt.get("max_loss_streak")
    if streak is not None and streak > 5: return False
    return True

def backtest_pair_v2(label, ac, sym_a, sym_b, kind, provider, vix_proxy=None, use_hl=True, use_rf=False, use_kalman=False):
    ha = v1._load_series(sym_a, provider)
    hb = v1._load_series(sym_b, provider)
    if not ha or not hb: return label, None, "no data"
    da, ca = ha; db, cb = hb
    a, b, dates = v1._align(da, ca, db, cb)
    if len(a) < 80: return label, None, "too few obs"
    if use_kalman and kind != "DIFF":
        _, spread = kalman_spread(a, b, KALMAN_DELTA, KALMAN_VT)
    else:
        spread = v1._build_spread(kind, a, b)
    cost = _cost_for(ac)
    hl = v1.estimate_half_life(spread)
    if use_hl:
        lookback = max(HL_LOOKBACK_MIN, min(HL_LOOKBACK_MAX, int(hl * 3)))
        horizon = max(HL_HORIZON_MIN, min(HL_HORIZON_MAX, int(hl * 1.0)))
    else:
        lookback = 60; horizon = 10
    if len(a) < lookback + horizon + 5: return label, None, "too few obs for hl params"
    vix_aligned = None
    if use_rf and vix_proxy:
        spy_data = v1._load_series("SPY", "polygon")
        if spy_data:
            spy_dates, _ = spy_data
            vix_map = {spy_dates[i]: vix_proxy[i] for i in range(min(len(spy_dates), len(vix_proxy)))}
            vix_aligned = [vix_map.get(d) for d in dates]
    bt = v1.backtest_pair_with_params(spread, lookback, horizon, Z_ENTRY, Z_EXIT, cost, vix_series=vix_aligned)
    if not bt: return label, None, "insufficient trades"
    eg_coint, eg_adf, eg_pval, eg_beta = engle_granger_test([math.log(v) for v in a], [math.log(v) for v in b], EG_MAX_LAG)
    bt["label"] = label; bt["asset_class"] = ac
    bt["sym_a"] = sym_a; bt["sym_b"] = sym_b
    bt["half_life"] = round(hl, 1)
    bt["first_date"] = dates[0] if dates else ""
    bt["last_date"] = dates[-1] if dates else ""
    bt["regime_filter"] = use_rf; bt["kalman_spread"] = use_kalman
    bt["eg_cointegrated"] = eg_coint; bt["eg_adf_stat"] = round(eg_adf, 3)
    bt["eg_pvalue"] = round(eg_pval, 4)
    return label, bt, None

def main():
    t0 = time.time()
    vix_proxy = v1.load_vix_proxy()
    print("VIX proxy: " + ("loaded" if vix_proxy else "N/A"))
    all_pairs = list(v1.FX_PAIRS)
    for lst in [v1.ETF_PAIRS, v1.EQUITY_PAIRS, v1.CRYPTO_PAIRS]:
        all_pairs.extend(lst)
    sys_count = 0
    for sname, stocks in v1.SECTORS.items():
        avail = [s for s in stocks if v1._load_series(s, "polygon")]
        if len(avail) >= 2:
            gen = v1.generate_sector_pairs(avail)
            all_pairs.extend(gen)
            sys_count += len(gen)
    seen = set(); unique = []
    for p in all_pairs:
        key = (p[2], p[3]) if p[2] < p[3] else (p[3], p[2])
        if key not in seen: seen.add(key); unique.append(p)
    all_pairs = unique; n_total = len(all_pairs)
    print("Pairs: %d total (%d FX + %d ETF + %d eq + %d crypto + %d sys)" % (n_total, len(v1.FX_PAIRS), len(v1.ETF_PAIRS), len(v1.EQUITY_PAIRS), len(v1.CRYPTO_PAIRS), sys_count))

    experiments = []
    exp_configs = [
        ("BASELINE (static OLS)", False, False, False),
        ("HALF-LIFE (static OLS)", True, False, False),
        ("+REGIME (static OLS)", True, True, False),
        ("HALF-LIFE (Kalman)", True, False, True),
        ("+REGIME (Kalman)", True, True, True),
    ]
    for exp_name, use_hl, use_rf, use_kalman in exp_configs:
        if use_rf and not vix_proxy: continue
        print("EXP: " + exp_name)
        results = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {}
            for p in all_pairs:
                futs[ex.submit(backtest_pair_v2, *p, vix_proxy, use_hl, use_rf, use_kalman)] = p
            for fut in as_completed(futs):
                label, r, err = fut.result()
                if r: results.append(r)
        experiments.append((exp_name, results))

    def summarize(results, n_tests):
        all_pvals = [_p_from_t(r.get("tstat")) for r in results]
        rows = []
        for r in results:
            ac = r.get("asset_class", "STOCK")
            qb = qualifies_v2(r, n_tests=n_tests, use_fdr=False)
            qf = qualifies_v2(r, n_tests=n_tests, use_fdr=True, all_pvals=all_pvals)
            rows.append(dict(
                label=r["label"], class_=ac,
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
        nfx = sum(1 for r in rows if r["class_"] == "FX" and r["qualifies_fdr"])
        ncoint = sum(1 for r in rows if r["eg_coint"])
        print("%s: OK=%d Bonf=%d FDR=%d FX=%d Fire=%d EG=%d" % (exp_name, len(results), nb, nf, nfx, nfire, ncoint))
        print("%-20s %5s %7s %6s %5s %9s %6s %7s %5s %5s %5s %5s" % ("Pair", "Cls", "edge", "t", "oos_n", "oos_edge", "HL", "z_now", "fire", "Bonf", "FDR", "EG"))
        for r in rows[:25]:
            ff = "*" if r["firing"] else ""
            bb = "YES" if r["qualifies_bonf"] else ""
            dd = "YES" if r["qualifies_fdr"] else ""
            eg = "C" if r["eg_coint"] else ""
            print("%-20s %5s %+7.3f %6.2f %5d %+9.3f %6.0f %+7.2f %5s %5s %5s %5s" % (r["label"], r["class_"], r["edge"], r["tstat"], r["oos_n"], r["oos_edge"], r["half_life"] or 0, r["z_now"], ff, bb, dd, eg))

    out_dir = os.path.join(_HERE, "reports")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "pairs_research_v2.json")
    md_path = os.path.join(out_dir, "pairs_research_v2.md")

    exp_data = {}
    for exp_name, results, rows in all_summaries:
        key = exp_name.lower().replace(" ", "_").replace("+", "").replace("(", "").replace(")", "")
        exp_data[key] = dict(n_ok=len(results),
            n_bonf=sum(1 for r in rows if r["qualifies_bonf"]),
            n_fdr=sum(1 for r in rows if r["qualifies_fdr"]),
            n_fx_qual=sum(1 for r in rows if r["class_"] == "FX" and r["qualifies_fdr"]),
            top20=[{k: v for k, v in r.items()} for r in rows[:20]])

    payload = dict(generated=time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        elapsed_s=round(elapsed, 2), n_pairs_tested=n_total, experiments=exp_data)
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    with open(md_path, "w") as f:
        f.write("# Pairs Trading Research v2 - Kalman + Cointegration + FX Gates

")
        f.write("Generated: %s | Elapsed: %.1fs

" % (payload["generated"], elapsed))
        f.write("## v2 Improvements

")
        f.write("1. Kalman filter dynamic hedge ratio - time-varying beta vs static OLS
")
        f.write("2. Engle-Granger cointegration test - statistical filter (p<0.10)
")
        f.write("3. FX-specific qualification gates - IS edge>=0.30 (vs 0.60), OOS cap<=5.0 (vs 3.0)
")
        f.write("4. All v1 features retained: half-life calibration, VIX regime filter, systematic screening, FDR

")
        f.write("## Universe: %d pairs

" % n_total)

        for exp_name, results, rows in all_summaries:
            nb = sum(1 for r in rows if r["qualifies_bonf"])
            nf = sum(1 for r in rows if r["qualifies_fdr"])
            nfx = sum(1 for r in rows if r["class_"] == "FX" and r["qualifies_fdr"])
            f.write("## %s: %d Bonf / %d FDR (FX: %d)

" % (exp_name, nb, nf, nfx))
            f.write("| Pair | Cls | n | edge | t | OOS n | OOS edge | HL | z_now | Fire | Bonf | FDR | EG |
")
            f.write("|------|-----|---|------|---|-------|----------|----|-------|------|------|-----|----|
")
            for r in rows[:25]:
                ff = "*" if r["firing"] else ""
                bb = "YES" if r["qualifies_bonf"] else ""
                dd = "YES" if r["qualifies_fdr"] else ""
                eg = "C" if r["eg_coint"] else ""
                f.write("| %s | %s | %d | %+.3f | %.2f | %d | %+.3f | %.0f | %+.2f | %s | %s | %s | %s |
" % (r["label"], r["class_"], r["n"], r["edge"], r["tstat"], r["oos_n"], r["oos_edge"], r["half_life"] or 0, r["z_now"], ff, bb, dd, eg))
            f.write("
")

        f.write("
## Cross-Experiment Summary

")
        f.write("| Experiment | OK | Bonf | FDR | FX Qual | EG Coint |
")
        f.write("|------------|----|------|-----|---------|----------|
")
        for exp_name, results, rows in all_summaries:
            nb = sum(1 for r in rows if r["qualifies_bonf"])
            nf = sum(1 for r in rows if r["qualifies_fdr"])
            nfx = sum(1 for r in rows if r["class_"] == "FX" and r["qualifies_fdr"])
            neg = sum(1 for r in rows if r["eg_coint"])
            f.write("| %s | %d | %d | %d | %d | %d |
" % (exp_name, len(results), nb, nf, nfx, neg))

        f.write("
## Live Pairs (FDR qual, Kalman spread)

")
        for exp_name, results, rows in all_summaries:
            if "Kalman" in exp_name and "REGIME" not in exp_name:
                live = [r for r in rows if r["qualifies_fdr"]][:15]
                if live:
                    f.write("| Pair | Cls | OOS edge | HL | z_now | Firing | EG coint |
")
                    f.write("|------|-----|----------|----|-------|--------|----------|
")
                    for r in live:
                        eg = "YES" if r["eg_coint"] else ""
                        fire = "YES" if r["firing"] else ""
                        f.write("| %s | %s | %+.3f | %.0f | %+.2f | %s | %s |
" % (r["label"], r["class_"], r["oos_edge"], r["half_life"] or 0, r["z_now"], fire, eg))
                break

        f.write("
## Cointegration Analysis (EG test, p<0.10)

")
        for exp_name, results, rows in all_summaries:
            if "Kalman" in exp_name and "REGIME" not in exp_name:
                coint_pairs = [r for r in rows if r["eg_coint"]]
                ncoint = len(coint_pairs)
                f.write("%d/%d pairs are cointegrated

" % (ncoint, len(rows)))
                if coint_pairs:
                    f.write("| Pair | ADF stat | p-value | OOS edge | Qualifies |
")
                    f.write("|------|----------|---------|----------|----------|
")
                    for r in sorted(coint_pairs, key=lambda x: x["eg_adf"])[:25]:
                        qual = "YES" if r["qualifies_fdr"] else ""
                        f.write("| %s | %+.3f | %.4f | %+.3f | %s |
" % (r["label"], r["eg_adf"], r["eg_pval"], r["oos_edge"], qual))
                break

    print("JSON: " + json_path)
    print("MD:   " + md_path)
    print("Done in %.1fs" % elapsed)
    return 0

if __name__ == "__main__":
    sys.exit(main())
