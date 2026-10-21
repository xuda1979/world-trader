"""pairs_research_v7.py -- factor-informed + regime-aware pair trading.

Approach 1: Factor-aligned pair filter
Approach 2: Regime-gated reversion
Approach 3: Combined filter
All use v5 honest engine + scramble control.
"""
from __future__ import annotations
import os, sys, math, statistics, random, json, time
_HERE = os.path.dirname(os.path.abspath(__file__))
for p in (_HERE, os.path.join(os.path.dirname(_HERE), _HERE)):
    sys.path.insert(0, p)
import pairs_research_v4 as v4
import pairs_engine_v5 as v5
import pairs_portfolio_sim as ps
COST_BPS = 3.8
Z_ENTRIES = [1.5, 2.0, 2.5]
OOS_FRAC = 0.40
MIN_BARS = 300
REPORT_JSON = os.path.join(_HERE, "reports", "pairs_research_v7.json")
REPORT_MD = os.path.join(_HERE, "reports", "pairs_research_v7.md")
def compute_factor_scores(all_data):
    """Compute daily cross-sectional factor scores for all stocks."""
    syms = sorted(all_data.keys())
    sym_to_dates = {}
    sym_to_closes = {}
    date_sets = []
    for sym in syms:
        d = all_data[sym]
        if d is None:
            continue
        dates, closes = d
        sym_to_dates[sym] = dates
        sym_to_closes[sym] = closes
        date_sets.append(set(dates))
    common_dates = sorted(set.intersection(*date_sets)) if date_sets else []
    if len(common_dates) < MIN_BARS:
        return None, common_dates
    close_mat = {}
    for dt in common_dates:
        row = {}
        for sym in sym_to_closes:
            dates = sym_to_dates[sym]
            closes = sym_to_closes[sym]
            idx = dates.index(dt) if dt in dates else -1
            if idx >= 0:
                row[sym] = closes[idx]
        if len(row) > 20:
            close_mat[dt] = row
    dates_have_data = sorted(close_mat.keys())
    if len(dates_have_data) < MIN_BARS:
        return None, dates_have_data
    factor_scores = {}
    for i, dt in enumerate(dates_have_data):
        row = close_mat[dt]
        syms_in = sorted(row.keys())
        mom = {}
        for sym in syms_in:
            dts = sym_to_dates[sym]
            cls = sym_to_closes[sym]
            idx = dts.index(dt)
            i12 = idx - 252 if idx >= 252 else -1
            i1 = idx - 21 if idx >= 21 else -1
            if i12 > 0 and i1 > 0:
                mom[sym] = cls[i1] / cls[i12] - 1.0
            else:
                mom[sym] = float("nan")
        rev = {}
        for sym in syms_in:
            dts = sym_to_dates[sym]
            cls = sym_to_closes[sym]
            idx = dts.index(dt)
            i5 = idx - 5 if idx >= 5 else -1
            if i5 > 0:
                rev[sym] = cls[idx] / cls[i5] - 1.0
            else:
                rev[sym] = float("nan")
        vol = {}
        for sym in syms_in:
            dts = sym_to_dates[sym]
            cls = sym_to_closes[sym]
            idx = dts.index(dt)
            start = max(1, idx - 60)
            rets = []
            for j in range(start, idx):
                if cls[j-1] > 0:
                    rets.append(cls[j] / cls[j-1] - 1.0)
            if len(rets) > 10:
                vol[sym] = statistics.pstdev(rets) * math.sqrt(252)
            else:
                vol[sym] = float("nan")
        def cs_z(raw):
            valid = {s: v for s, v in raw.items() if math.isfinite(v)}
            if len(valid) < 10:
                return {s: 0.0 for s in raw}
            vals = list(valid.values())
            mu = statistics.fmean(vals)
            sd = statistics.pstdev(vals) if len(vals) > 1 else 1.0
            if sd <= 0:
                sd = 1.0
            out = {}
            for s in raw:
                if s in valid:
                    out[s] = (valid[s] - mu) / sd
                else:
                    out[s] = 0.0
            return out
        factor_scores[dt] = dict(mom=cs_z(mom), rev=cs_z(rev), vol=cs_z(vol))
    return factor_scores, dates_have_data
def factor_aligned_entry(side, factor_scores_dt, sym_a, sym_b):
    if factor_scores_dt is None:
        return False
    fmom = factor_scores_dt.get("mom", {})
    frev = factor_scores_dt.get("rev", {})
    fvol = factor_scores_dt.get("vol", {})
    mom_a = fmom.get(sym_a, 0.0)
    mom_b = fmom.get(sym_b, 0.0)
    rev_a = frev.get(sym_a, 0.0)
    rev_b = frev.get(sym_b, 0.0)
    vol_a = fvol.get(sym_a, 0.0)
    vol_b = fvol.get(sym_b, 0.0)
    score_a = 0.6 * mom_a + 0.4 * (-rev_a) - 0.2 * vol_a
    score_b = 0.6 * mom_b + 0.4 * (-rev_b) - 0.2 * vol_b
    diff = score_a - score_b
    if side > 0:
        return diff > 0.15
    else:
        return diff < -0.15


def compute_dispersion(dates_with_data, close_mat):
    dispersion = {}
    for i, dt in enumerate(dates_with_data):
        if i < 1:
            continue
        row = close_mat.get(dt, {})
        prev = close_mat.get(dates_with_data[i-1], {})
        rets = []
        for sym in row:
            if sym in prev and prev[sym] > 0:
                rets.append(row[sym] / prev[sym] - 1.0)
        if len(rets) > 20:
            dispersion[dt] = statistics.pstdev(rets)
    return dispersion


def regime_ok(dt, dispersion):
    if not dispersion or dt not in dispersion:
        return True
    vals = sorted(dispersion.values())
    if len(vals) < 30:
        return True
    tercile_hi = vals[int(len(vals) * 2 / 3)]
    return dispersion[dt] >= tercile_hi


def load_all_pairs():
    all_pairs = ps.build_universe()
    result = []
    for p in all_pairs:
        label, ac, sym_a, sym_b, kind, provider = p
        d = ps._pair_data(label, ac, sym_a, sym_b, kind, provider)
        if d is not None and len(d["a"]) >= MIN_BARS:
            result.append((label, ac, sym_a, sym_b, kind, provider, d))
    return result


def backtest_one(pair_data, factor_scores, dispersion, z_entry,
                 use_factor_filter, use_regime_filter, scramble_seed=None):
    a = list(pair_data["a"])
    b = list(pair_data["b"])
    dates = pair_data["dates"]
    sym_a = pair_data.get("sym_a", "")
    sym_b = pair_data.get("sym_b", "")
    n = len(a)
    n_is = int(n * (1 - OOS_FRAC))
    if scramble_seed is not None:
        lbl = pair_data.get("label", "")
        rng = random.Random(scramble_seed + sum(ord(x) for x in lbl))
        lag = rng.randint(20, max(21, n // 3))
        b = [b[(i + lag) % n] for i in range(n)]
    spread, _ = v5.build_spread(a, b, n_is)
    hl = v4.estimate_half_life(spread[:n_is])
    lookback = max(v5.HL_LOOKBACK_MIN, min(v5.HL_LOOKBACK_MAX, int(hl * 3)))
    horizon = max(v5.HORIZON_MIN, min(v5.HORIZON_MAX, int(hl * 1.5)))
    trs = v5.replay_mr(spread, lookback, z_entry, z_entry, horizon, open_from=n_is)
    filtered_trs = []
    for t in trs:
        ei = t["entry_idx"]
        if ei >= len(dates):
            continue
        dt = dates[ei]
        side = t["side"]
        if use_factor_filter:
            fs = factor_scores.get(dt) if factor_scores else None
            if not factor_aligned_entry(side, fs, sym_a, sym_b):
                continue
        if use_regime_filter:
            if not regime_ok(dt, dispersion):
                continue
        filtered_trs.append(t)
    trs_use = filtered_trs if (use_factor_filter or use_regime_filter) else trs
    oos_rets = []
    for t in trs_use:
        esd = t["entry_sd"]
        c = 4.0 * (COST_BPS / 1e4) / esd if esd > 0 else 0.0
        oos_rets.append(t["sigma_net"] - c)
    n_trs = len(oos_rets)
    if n_trs < 5:
        return None
    exp_oos = statistics.fmean(oos_rets)
    sd_oos = statistics.pstdev(oos_rets) if n_trs > 1 else 1.0
    se_oos = sd_oos / math.sqrt(n_trs)
    t_oos = exp_oos / se_oos if se_oos > 0 else 0.0
    return dict(n_oos=n_trs, exp_oos=round(exp_oos, 3),
                t_oos=round(t_oos, 3), hl=round(hl, 0))
def run_research():
    t0 = time.time()
    print("=" * 60)
    print("PAIRS RESEARCH V7: Factor-Informed + Regime-Aware")
    print("=" * 60)
    print("Loading pairs...")
    pairs = load_all_pairs()
    print("  %d pairs" % len(pairs))
    all_syms = set()
    for _, _, sym_a, sym_b, _, _, _ in pairs:
        all_syms.add(sym_a)
        all_syms.add(sym_b)
    stock_data = {}
    for sym in all_syms:
        loaded = v4._load_series(sym, "polygon")
        if loaded:
            stock_data[sym] = loaded
    print("  %d stocks" % len(stock_data))
    print("Computing factor scores...")
    factor_scores, dates_with_factors = compute_factor_scores(stock_data)
    if factor_scores is None:
        print("ERROR: insufficient data")
        return
    print("  %d dates" % len(factor_scores))
    print("Computing dispersion...")
    date_sets = [set(d[0]) for d in stock_data.values() if d]
    common = sorted(set.intersection(*date_sets)) if date_sets else []
    close_mat = {}
    for dt in common:
        row = {}
        for sym, d in stock_data.items():
            if d is None:
                continue
            ds, cs = d
            if dt in ds:
                row[sym] = cs[ds.index(dt)]
        if len(row) > 20:
            close_mat[dt] = row
    dispersion = compute_dispersion(dates_with_factors, close_mat)
    print("  %d values" % len(dispersion))
    print("Running experiments...")
    experiments = []
    for z_entry in Z_ENTRIES:
        for use_factor in [False, True]:
            for use_regime in [False, True]:
                name = "z=%.1f" % z_entry
                if use_factor:
                    name += "+F"
                if use_regime:
                    name += "+R"
                experiments.append(dict(name=name, z_entry=z_entry,
                                        use_factor=use_factor,
                                        use_regime=use_regime))
    all_results = []
    for exp_idx, exp in enumerate(experiments):
        name = exp["name"]
        z_entry = exp["z_entry"]
        use_factor = exp["use_factor"]
        use_regime = exp["use_regime"]
        t_exp = time.time()
        sys.stdout.write("  [%d/%d] %s... " % (exp_idx+1, len(experiments), name))
        sys.stdout.flush()
        pair_results = []
        for label, ac, sym_a, sym_b, kind, provider, pair_data in pairs:
            pair_data["label"] = label
            pair_data["sym_a"] = sym_a
            pair_data["sym_b"] = sym_b
            r = backtest_one(pair_data, factor_scores, dispersion, z_entry,
                           use_factor, use_regime)
            if r:
                r["label"] = label
                r["real_exp_oos"] = r["exp_oos"]
                r["real_t_oos"] = r["t_oos"]
                scr_seed = 42 + sum(ord(x) for x in label)
                s = backtest_one(pair_data, factor_scores, dispersion, z_entry,
                               use_factor, use_regime, scramble_seed=scr_seed)
                if s:
                    r["scram_exp_oos"] = s["exp_oos"]
                    r["delta"] = round(r["real_exp_oos"] - s["exp_oos"], 3)
                else:
                    r["scram_exp_oos"] = 0.0
                    r["delta"] = r["real_exp_oos"]
                pair_results.append(r)
        n_pairs = len(pair_results)
        if n_pairs == 0:
            print("0 pairs")
            all_results.append(dict(name=name, z_entry=z_entry, n_pairs=0,
                                    mean_real=0, mean_scram=0, mean_delta=0,
                                    t_delta=0, n_pos_delta=0, n_neg_delta=0,
                                    mean_t_oos=0, n_t_gt2=0))
            continue
        mean_real = statistics.fmean([r["real_exp_oos"] for r in pair_results])
        mean_scram = statistics.fmean([r["scram_exp_oos"] for r in pair_results])
        deltas = [r["delta"] for r in pair_results]
        mean_delta = statistics.fmean(deltas)
        sd_delta = statistics.pstdev(deltas) if len(deltas) > 1 else 0.0
        t_delta = mean_delta / (sd_delta / math.sqrt(n_pairs)) if sd_delta > 0 else 0.0
        n_pos = sum(1 for d in deltas if d > 0.05)
        n_neg = sum(1 for d in deltas if d < -0.05)
        mean_t = statistics.fmean([r["real_t_oos"] for r in pair_results])
        n_t2 = sum(1 for r in pair_results if r["real_t_oos"] > 2.0)
        elapsed = time.time() - t_exp
        print("%dp real=%+.3f scram=%+.3f D=%+.3f(t=%+.2f) pos=%d neg=%d t>2:%d %ds" % (
            n_pairs, mean_real, mean_scram, mean_delta, t_delta, n_pos, n_neg, n_t2, int(elapsed)))
        all_results.append(dict(name=name, z_entry=z_entry,
                                use_factor=use_factor, use_regime=use_regime,
                                n_pairs=n_pairs,
                                mean_real=round(mean_real, 4),
                                mean_scram=round(mean_scram, 4),
                                mean_delta=round(mean_delta, 4),
                                sd_delta=round(sd_delta, 4),
                                t_delta=round(t_delta, 2),
                                n_pos_delta=n_pos, n_neg_delta=n_neg,
                                mean_t_oos=round(mean_t, 3), n_t_gt2=n_t2))
    print("Generating report...")
    elapsed_total = time.time() - t0
    out = dict(generated=time.strftime("%Y-%m-%d %H:%M:%S"),
               cost_bps=COST_BPS, n_pairs_tested=len(pairs),
               n_stocks=len(stock_data),
               n_factor_dates=len(factor_scores) if factor_scores else 0,
               elapsed_seconds=round(elapsed_total, 0),
               experiments=all_results)
    with open(REPORT_JSON, "w") as f:
        json.dump(out, f, indent=1)

    # Console summary
    print("")
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("%-22s %5s %9s %9s %9s %7s" % ("Config", "P", "Real", "Scram", "Delta", "t"))
    print("-" * 62)
    for e in all_results:
        flag = " *** SIG" if e["t_delta"] > 2.0 else (" * prom" if e["t_delta"] > 1.5 else "")
        print("%-22s %5d %+9.4f %+9.4f %+9.4f %+6.2f%s" % (
            e["name"], e["n_pairs"], e["mean_real"], e["mean_scram"],
            e["mean_delta"], e["t_delta"], flag))
    print("")
    print("Wrote %s" % REPORT_JSON)
    print("Total: %ds" % int(elapsed_total))
    return out


if __name__ == "__main__":
    run_research()