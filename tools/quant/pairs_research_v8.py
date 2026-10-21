"""pairs_research_v8.py -- Honest-Engine Integration: v5 Symmetric MR + Factor/Regime Filters

CRITICAL RESEARCH QUESTIONS:
1. Does the HONEST v5 engine produce positive OOS edge above scramble baseline?
2. Do factor-informed entry + regime-gating filters IMPROVE the edge?
3. What is the REALISTIC per-trade sigma edge after costs with honest controls?

METHODOLOGY:
- v5 engine (symmetric MR, noise-neutral) - pairs_engine_v5.replay_mr
- Scramble: N=5 random lags of leg B, compare real vs scramble edges
- Factor filter: cross-sectional mom/rev/vol z-scores aligned with trade
- Regime filter: only enter in top-tercile cross-sectional dispersion
"""
from __future__ import annotations
import os, sys, csv, json, math, random, statistics, time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pairs_engine_v5 as v5
import pairs_research_v4 as v4

Z_ENTRIES = [1.5, 2.0, 2.5]
COST_BPS_VALS = [1.0, 3.8, 7.6]
RISK_FRAC = 0.01
ANNUAL_FACTOR = 252.0
N_SCRAMBLE = 5
MIN_OOS_TRADES = 8
MIN_BARS = 300
OOS_SPLIT = 0.60

DATA_DIR = os.path.join(_HERE, "data")
REPORT_JSON = os.path.join(_HERE, "reports", "pairs_research_v8.json")
REPORT_MD = os.path.join(_HERE, "reports", "pairs_research_v8.md")
SIGNALS_JSON = os.path.join(_HERE, "reports", "pairs_v8_signals.json")
DAILY_JSON = os.path.join(_HERE, "reports", "pairs_v8_daily.json")

# ================================================================ DATA LOADING
def _load_pair_data(label, ac, sym_a, sym_b, kind, provider):
    ha = v4._load_series(sym_a, provider)
    hb = v4._load_series(sym_b, provider)
    if not ha or not hb:
        return None
    da, ca = ha; db, cb = hb
    a, b, dates = v4._align(da, ca, db, cb)
    if len(a) < MIN_BARS:
        return None
    return {"label": label, "asset_class": ac, "sym_a": sym_a, "sym_b": sym_b,
            "kind": kind, "provider": provider, "a": a, "b": b, "dates": dates}


def build_universe():
    all_pairs = list(v4.FX_PAIRS)
    for lst in [v4.ETF_PAIRS, v4.EQUITY_PAIRS, v4.CRYPTO_PAIRS]:
        all_pairs.extend(lst)
    for sname, stocks in v4.SECTORS.items():
        avail = [s for s in stocks if v4._load_series(s, "polygon")]
        if len(avail) >= 2:
            all_pairs.extend(v4.generate_sector_pairs(avail))
    seen = set(); uniq = []
    for p in all_pairs:
        key = (p[2], p[3]) if p[2] < p[3] else (p[3], p[2])
        if key not in seen:
            seen.add(key); uniq.append(p)
    return uniq


def load_all_data(all_pairs):
    all_data = {}
    for p in all_pairs:
        label, ac, sym_a, sym_b, kind, provider = p
        d = _load_pair_data(label, ac, sym_a, sym_b, kind, provider)
        if d is not None:
            all_data[label] = d
    return all_data


# ================================================================ SPREAD CONSTRUCTION
def build_spread_v5(a, b, n_is=None):
    la = [math.log(x) for x in a]
    lb = [math.log(x) for x in b]
    n = n_is if n_is is not None else len(la)
    beta = v4._ols_beta(la[:n], lb[:n])
    return [la[i] - beta * lb[i] for i in range(len(la))], beta


def build_spread_kalman(a, b, delta=1e-5, vt=1e-3):
    betas, spread = v4.kalman_spread(a, b, delta, vt)
    return spread, betas


# ================================================================ FACTOR SCORES
def compute_factor_scores(all_data):
    sym_to_dates = {}; sym_to_closes = {}
    for label, pr in all_data.items():
        for sym_key in ("sym_a", "sym_b"):
            sym = pr.get(sym_key, "")
            if sym and sym not in sym_to_dates:
                loaded = v4._load_series(sym, "polygon")
                if loaded:
                    sym_to_dates[sym] = loaded[0]; sym_to_closes[sym] = loaded[1]
    syms = sorted(sym_to_dates.keys())
    if len(syms) < 10:
        return None, []
    date_sets = [set(sym_to_dates[s]) for s in syms]
    common_dates = sorted(set.intersection(*date_sets)) if date_sets else []
    if len(common_dates) < MIN_BARS:
        return None, common_dates
    close_mat = {}
    for dt in common_dates:
        row = {}
        for sym in syms:
            dates = sym_to_dates[sym]; closes = sym_to_closes[sym]
            idx = dates.index(dt) if dt in dates else -1
            if idx >= 0: row[sym] = closes[idx]
        if len(row) > 20: close_mat[dt] = row
    dates_have_data = sorted(close_mat.keys())
    if len(dates_have_data) < MIN_BARS:
        return None, dates_have_data
    factor_scores = {}
    for i, dt in enumerate(dates_have_data):
        row = close_mat[dt]; syms_in = sorted(row.keys())
        mom = {}; rev = {}; vol = {}
        for sym in syms_in:
            dts = sym_to_dates[sym]; cls = sym_to_closes[sym]
            idx = dts.index(dt)
            i12 = idx - 252 if idx >= 252 else -1
            i1 = idx - 21 if idx >= 21 else -1
            if i12 > 0 and i1 > 0: mom[sym] = cls[i1] / cls[i12] - 1.0
            else: mom[sym] = float("nan")
            i5 = idx - 5 if idx >= 5 else -1
            if i5 > 0: rev[sym] = cls[idx] / cls[i5] - 1.0
            else: rev[sym] = float("nan")
            start = max(1, idx - 60)
            rets = [cls[j]/cls[j-1]-1.0 for j in range(start, idx) if cls[j-1] > 0]
            if len(rets) > 10: vol[sym] = statistics.pstdev(rets) * math.sqrt(252)
            else: vol[sym] = float("nan")
        def cs_z(raw):
            valid = {s: v for s, v in raw.items() if math.isfinite(v)}
            if len(valid) < 10: return {s: 0.0 for s in raw}
            vals = list(valid.values())
            mu = statistics.fmean(vals)
            sd = statistics.pstdev(vals) if len(vals) > 1 else 1.0
            if sd <= 0: sd = 1.0
            out = {}
            for s in raw:
                out[s] = ((valid[s] - mu) / sd) if s in valid else 0.0
            return out
        factor_scores[dt] = dict(mom=cs_z(mom), rev=cs_z(rev), vol=cs_z(vol))
    return factor_scores, dates_have_data


# ================================================================ DISPERSION
def compute_dispersion(dates_with_data, close_mat):
    dispersion = {}
    for i, dt in enumerate(dates_with_data):
        if i < 1: continue
        row = close_mat.get(dt, {}); prev = close_mat.get(dates_with_data[i-1], {})
        rets = [row[sym]/prev[sym]-1.0 for sym in row if sym in prev and prev[sym] > 0]
        if len(rets) > 20: dispersion[dt] = statistics.pstdev(rets)
    return dispersion


def regime_ok(dt, dispersion):
    if not dispersion or dt not in dispersion: return True
    vals = sorted(dispersion.values())
    if len(vals) < 30: return True
    return dispersion[dt] >= vals[int(len(vals) * 2 / 3)]


def factor_aligned(side, factor_scores_dt, sym_a, sym_b):
    if factor_scores_dt is None: return True
    fmom = factor_scores_dt.get("mom", {})
    frev = factor_scores_dt.get("rev", {})
    fvol = factor_scores_dt.get("vol", {})
    mom_a = fmom.get(sym_a, 0.0); mom_b = fmom.get(sym_b, 0.0)
    rev_a = frev.get(sym_a, 0.0); rev_b = frev.get(sym_b, 0.0)
    vol_a = fvol.get(sym_a, 0.0); vol_b = fvol.get(sym_b, 0.0)
    score_a = 0.6 * mom_a + 0.4 * (-rev_a) - 0.2 * vol_a
    score_b = 0.6 * mom_b + 0.4 * (-rev_b) - 0.2 * vol_b
    diff = score_a - score_b
    return diff > 0.15 if side > 0 else diff < -0.15


# ================================================================ SCRAMBLE CONTROL
def scramble_leg(data, seed):
    rng = random.Random(seed)
    n = len(data)
    lag = rng.randint(20, max(21, n // 3))
    return [data[(i + lag) % n] for i in range(n)]


# ================================================================ MAIN BACKTEST ENGINE
def backtest_one_pair(pr, spread_type, z_entry, cost_bps,
                      use_factor, use_regime,
                      factor_scores, dispersion,
                      scramble_seed=None):
    a = list(pr["a"]); b = list(pr["b"]); dates = pr["dates"]
    sym_a = pr.get("sym_a", ""); sym_b = pr.get("sym_b", "")
    label = pr["label"]; n = len(a)

    # Scramble: shift leg B
    b_use = list(b)
    if scramble_seed is not None:
        total_seed = scramble_seed + sum(ord(c) for c in label)
        b_use = scramble_leg(b_use, total_seed)

    # Build spread
    n_is = int(n * OOS_SPLIT)
    if spread_type == "static":
        spread, beta = build_spread_v5(a, b_use, n_is)
    elif spread_type == "kalman":
        spread, betas = build_spread_kalman(a, b_use)
    else:
        return None

    # Half-life calibration on IS only
    hl = v4.estimate_half_life(spread[:n_is])
    lookback = max(v5.HL_LOOKBACK_MIN, min(v5.HL_LOOKBACK_MAX, int(hl * 3)))
    horizon = max(v5.HORIZON_MIN, min(v5.HORIZON_MAX, int(hl * 1.5)))

    # Replay trades using v5 symmetric engine (OOS only)
    trs = v5.replay_mr(spread, lookback, z_entry, z_entry, horizon, open_from=n_is)

    # Apply filters
    filtered_trs = []
    for t in trs:
        ei = t["entry_idx"]
        if ei >= len(dates): continue
        dt = dates[ei]; side = t["side"]
        if use_factor:
            fs = factor_scores.get(dt) if factor_scores else None
            if not factor_aligned(side, fs, sym_a, sym_b): continue
        if use_regime:
            if not regime_ok(dt, dispersion): continue
        filtered_trs.append(t)

    trs_use = filtered_trs if (use_factor or use_regime) else trs

    # Per-trade sigma P&L (cost-adjusted)
    oos_rets = []
    for t in trs_use:
        esd = t["entry_sd"]
        c = 2.0 * (cost_bps / 1e4) / esd if esd > 0 else 0.0
        oos_rets.append(t["sigma_net"] - c)

    n_trs = len(oos_rets)
    if n_trs < MIN_OOS_TRADES: return None

    exp_oos = statistics.fmean(oos_rets)
    sd_oos = statistics.pstdev(oos_rets) if n_trs > 1 else 0.0
    se_oos = sd_oos / math.sqrt(n_trs)
    t_oos = exp_oos / se_oos if se_oos > 0 else 0.0
    edge_oos = exp_oos / sd_oos if sd_oos > 0 else 0.0

    # Current z-score
    m_now, sd_now = v5._roll(n - 1, lookback, spread)
    z_now = (spread[n - 1] - m_now) / sd_now if sd_now > 0 else 0.0

    return {
        "label": label, "asset_class": pr["asset_class"],
        "sym_a": sym_a, "sym_b": sym_b,
        "spread_type": spread_type, "z_entry": z_entry, "cost_bps": cost_bps,
        "use_factor": use_factor, "use_regime": use_regime,
        "scramble_seed": scramble_seed,
        "n_trades": n_trs, "exp_oos": round(exp_oos, 6),
        "sd_oos": round(sd_oos, 6), "t_oos": round(t_oos, 3),
        "edge_oos": round(edge_oos, 4),
        "hl": round(hl, 1), "lookback": lookback, "horizon": horizon,
        "z_now": round(z_now, 3),
        "firing": abs(z_now) >= z_entry,
    }


# ================================================================ EXPERIMENT RUNNER
def run_experiment(all_data, spread_type, z_entry, cost_bps,
                   use_factor, use_regime,
                   factor_scores, dispersion,
                   scramble_seeds=None):
    seeds = scramble_seeds or [None]
    all_results = []
    for label, pr in all_data.items():
        real_r = None; scram_rs = []
        for si, seed in enumerate(seeds):
            r = backtest_one_pair(pr, spread_type, z_entry, cost_bps,
                                  use_factor, use_regime,
                                  factor_scores, dispersion,
                                  scramble_seed=seed)
            if r is None: continue
            if si == 0:
                real_r = r; real_r["is_real"] = True
            else:
                r["is_real"] = False; scram_rs.append(r)
        if real_r is None: continue
        if scram_rs:
            scram_edges = [s["exp_oos"] for s in scram_rs]
            scram_mu = statistics.fmean(scram_edges)
            scram_sd = statistics.pstdev(scram_edges) if len(scram_edges) > 1 else 0.0
            real_r["scram_mean"] = round(scram_mu, 6)
            real_r["scram_sd"] = round(scram_sd, 6)
            delta = real_r["exp_oos"] - scram_mu
            real_r["delta"] = round(delta, 6)
            real_r["delta_t"] = round(delta / scram_sd, 3) if scram_sd > 0 else 0.0
            real_r["n_scramble"] = len(scram_rs)
        else:
            real_r["scram_mean"] = None; real_r["scram_sd"] = None
            real_r["delta"] = None; real_r["delta_t"] = None
            real_r["n_scramble"] = 0
        all_results.append(real_r)
    return all_results


def experiment_name(spread_type, z_entry, cost_bps, use_factor, use_regime):
    parts = [spread_type[:3], "z=%g" % z_entry, "c=%g" % cost_bps]
    if use_factor: parts.append("F")
    if use_regime: parts.append("R")
    return "_".join(parts)


# ================================================================ MAIN
def main():
    t0 = time.time()
    print("=" * 70)
    print("  PAIRS RESEARCH V8: Honest Engine + Factor/Regime Filters")
    print("=" * 70)

    # 1. LOAD UNIVERSE
    print("\n[1/6] Loading universe...")
    all_pairs = build_universe()
    print("  %d candidate pairs" % len(all_pairs))
    all_data = load_all_data(all_pairs)
    print("  %d pairs with sufficient data" % len(all_data))

    # 2. COMPUTE FACTOR SCORES
    print("\n[2/6] Computing factor scores...")
    factor_scores, factor_dates = compute_factor_scores(all_data)
    if factor_scores:
        n_stocks = len(next(iter(factor_scores.values()))["mom"])
        print("  %d dates, %d stocks" % (len(factor_scores), n_stocks))
    else:
        print("  WARNING: Could not compute factor scores")

    # 3. COMPUTE DISPERSION
    print("\n[3/6] Computing cross-sectional dispersion...")
    stock_data = {}
    for label, pr in all_data.items():
        for sym_key in ("sym_a", "sym_b"):
            sym = pr.get(sym_key, "")
            if sym and sym not in stock_data:
                loaded = v4._load_series(sym, "polygon")
                if loaded: stock_data[sym] = loaded
    date_sets = [set(d[0]) for d in stock_data.values() if d]
    common = sorted(set.intersection(*date_sets)) if date_sets else []
    close_mat = {}
    for dt in common:
        row = {}
        for sym, d in stock_data.items():
            if d is None: continue
            ds, cs = d
            if dt in ds: row[sym] = cs[ds.index(dt)]
        if len(row) > 20: close_mat[dt] = row
    dispersion = compute_dispersion(common, close_mat)
    print("  %d dispersion values" % len(dispersion))

    # 4. DEFINE EXPERIMENTS
    print("\n[4/6] Defining experiments...")
    experiments = []

    # Core grid: OLS static, 3 z-levels, 3.8bps, factor+regime combos
    for z_entry in Z_ENTRIES:
        for use_factor in [False, True]:
            for use_regime in [False, True]:
                experiments.append({
                    "spread_type": "static", "z_entry": z_entry,
                    "cost_bps": 3.8,
                    "use_factor": use_factor,
                    "use_regime": use_regime,
                })

    # Cost sweep at z=2.0
    for cost_bps in [COST_BPS_VALS[0], COST_BPS_VALS[2]]:
        for use_factor in [False, True]:
            for use_regime in [False, True]:
                experiments.append({
                    "spread_type": "static", "z_entry": 2.0,
                    "cost_bps": cost_bps,
                    "use_factor": use_factor,
                    "use_regime": use_regime,
                })

    # Kalman sweep (subset - expensive)
    for use_regime in [False, True]:
        experiments.append({
            "spread_type": "kalman", "z_entry": 2.0,
            "cost_bps": 3.8, "use_factor": False,
            "use_regime": use_regime,
        })

    print("  %d experiments to run" % len(experiments))

    # 5. RUN ALL EXPERIMENTS
    print("\n[5/6] Running experiments...")
    all_experiments = []
    for ei, exp in enumerate(experiments):
        name = experiment_name(exp["spread_type"], exp["z_entry"],
                               exp["cost_bps"], exp["use_factor"],
                               exp["use_regime"])
        t_exp = time.time()
        sys.stdout.write("  [%d/%d] %s... " % (ei+1, len(experiments), name))
        sys.stdout.flush()

        scramble_seeds = [42, 142, 242, 342, 442]  # N=5 scramble seeds
        results = run_experiment(
            all_data, exp["spread_type"], exp["z_entry"], exp["cost_bps"],
            exp["use_factor"], exp["use_regime"],
            factor_scores, dispersion,
            scramble_seeds=scramble_seeds)

        n_pairs = len(results)
        if n_pairs == 0:
            print("0 pairs")
            all_experiments.append({"name": name, "n_pairs": 0, **exp})
            continue

        real_edges = [r["exp_oos"] for r in results]
        real_tstats = [r["t_oos"] for r in results]
        deltas = [r.get("delta", 0) or 0 for r in results]

        mean_real = statistics.fmean(real_edges)
        mean_real_t = statistics.fmean(real_tstats)
        mean_delta = statistics.fmean(deltas)
        sd_delta = statistics.pstdev(deltas) if len(deltas) > 1 else 0.0
        t_delta = mean_delta / (sd_delta / math.sqrt(n_pairs)) if sd_delta > 0 else 0.0

        n_pos_edge = sum(1 for e in real_edges if e > 0)
        n_genuine = sum(1 for r in results
                        if (r.get("delta_t") or 0) > 2.0
                        and r["exp_oos"] > 0)
        n_solid = sum(1 for r in results
                      if (r.get("delta_t") or 0) > 1.0
                      and r["exp_oos"] > 0)
        n_firing = sum(1 for r in results if r.get("firing"))

        elapsed = time.time() - t_exp
        print("%dp  real=%+.4f  t=%+.2f  d=%+.4f(t=%+.2f)  pos=%d/%d  sol=%d gen=%d  fire=%d  %ds" % (
            n_pairs, mean_real, mean_real_t, mean_delta, t_delta,
            n_pos_edge, n_pairs, n_solid, n_genuine, n_firing, int(elapsed)))

        all_experiments.append({
            "name": name, "n_pairs": n_pairs, **exp,
            "mean_real_edge": round(mean_real, 6),
            "mean_real_t": round(mean_real_t, 3),
            "mean_delta": round(mean_delta, 6),
            "sd_delta": round(sd_delta, 6),
            "t_delta": round(t_delta, 3),
            "frac_pos_edge": round(n_pos_edge / n_pairs, 3) if n_pairs else 0,
            "n_solid": n_solid, "n_genuine": n_genuine, "n_firing": n_firing,
            "top_genuine": sorted(
                [r for r in results if (r.get("delta_t") or 0) > 2.0 and r["exp_oos"] > 0],
                key=lambda r: -(r["delta_t"] or 0))[:10],
            "top_solid": sorted(
                [r for r in results if (r.get("delta_t") or 0) > 1.0 and r["exp_oos"] > 0],
                key=lambda r: -(r["delta_t"] or 0))[:15],
            "top_firing": sorted(
                [r for r in results if r.get("firing")],
                key=lambda r: -(r.get("delta_t") or 0))[:10],
            "all_pairs": sorted(results,
                key=lambda r: -(r.get("delta_t") or 0))[:50],
        })

    # 6. GENERATE REPORT
    print("\n[6/6] Generating report...")
    elapsed_total = time.time() - t0

    report = {
        "title": "Pairs Research v8: Honest Engine Integration",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_s": round(elapsed_total, 1),
        "n_candidate_pairs": len(all_pairs),
        "n_loaded_pairs": len(all_data),
        "n_factor_dates": len(factor_scores) if factor_scores else 0,
        "n_dispersion_dates": len(dispersion),
        "engine": "v5_symmetric_mr",
        "scramble_seeds": 5,
        "n_experiments": len(all_experiments),
        "experiments": all_experiments,
    }

    os.makedirs(os.path.dirname(REPORT_JSON), exist_ok=True)
    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=1, default=str)

    _write_md(report)
    _write_signals(all_experiments)
    _write_daily_signals(all_data, all_experiments)

    # Console summary
    print("\n" + "=" * 70)
    print("SUMMARY -- Honest Engine (v5 symmetric MR)")
    print("=" * 70)
    hdr = "%-35s %4s %8s %8s %6s %4s %4s %4s" % (
        "Experiment", "P", "Real", "d", "td", "Sol", "Gen", "Fire")
    print(hdr)
    print("-" * 72)
    for e in all_experiments:
        if e.get("n_pairs", 0) == 0: continue
        flag = (" ***" if e["t_delta"] > 2.0 and e["n_genuine"] >= 3 else
                " **" if e["t_delta"] > 1.5 else
                " *" if e["t_delta"] > 1.0 else "")
        print("%-35s %4d %+8.4f %+8.4f %+6.2f %4d %4d %4d%s" % (
            e["name"], e["n_pairs"], e["mean_real_edge"], e["mean_delta"],
            e["t_delta"], e.get("n_solid", 0), e["n_genuine"],
            e["n_firing"], flag))

    best = max(all_experiments,
               key=lambda e: (e.get("n_genuine", 0), e.get("t_delta", -99)),
               default=None)
    if best:
        print("\nBest: %s -- %d genuine, %d solid, td=%+.2f" % (
            best["name"], best.get("n_genuine", 0),
            best.get("n_solid", 0), best.get("t_delta", 0)))

    print("\n  Wrote %s, %s, %s" % (REPORT_JSON, REPORT_MD, SIGNALS_JSON))
    print("  Total: %ds" % int(elapsed_total))
    return report


# ================================================================ REPORT GENERATION
def _write_md(report):
    with open(REPORT_MD, "w") as f:
        f.write("# Pairs Trading Research v8 -- Honest Engine Integration\n\n")
        f.write("Generated: %s | Elapsed: %.1fs\n\n" % (
            report["generated"], report["elapsed_s"]))

        f.write("## Methodology\n\n")
        f.write("- **Engine**: v5 symmetric mean-reversion (z_exit = z_entry, "
                "noise-neutral by construction)\n")
        f.write("- **Scramble control**: N=5 random lags of leg B, "
                "delta = real_edge - mean_scram_edge\n")
        f.write("- **Factor filter**: cross-sectional mom/rev/vol z-scores "
                "aligned with trade direction\n")
        f.write("- **Regime filter**: only enter in top-tercile dispersion\n")
        f.write("- **Universe**: %d pairs loaded (%d candidates)\n\n" % (
            report["n_loaded_pairs"], report["n_candidate_pairs"]))

        f.write("## Experiment Results\n\n")
        f.write("| Experiment | Pairs | Real Edge | d(vs scram) | t(d) | "
                "%%Pos | Solid | Genuine | Fire |\n")
        f.write("|------------|-------|-----------|-------------|------|"
                "------|-------|---------|------|\n")
        for e in report["experiments"]:
            if e.get("n_pairs", 0) == 0: continue
            pct_pos = "%d%%" % int(e.get("frac_pos_edge", 0) * 100)
            flag = ("++" if e["n_genuine"] >= 5 else
                    "+" if e["n_genuine"] >= 3 else
                    "~" if e.get("n_solid", 0) >= 3 else "-")
            f.write("| %s | %d | %+.4f | %+.4f | %+.2f | %s | %d | %d | %d | %s |\n" % (
                e["name"], e["n_pairs"], e["mean_real_edge"],
                e["mean_delta"], e["t_delta"], pct_pos,
                e.get("n_solid", 0), e["n_genuine"], e["n_firing"], flag))

        # Top genuine pairs
        best = max(report["experiments"],
                   key=lambda e: (e.get("n_genuine", 0), e.get("t_delta", -99)),
                   default=None)
        f.write("\n## Top Genuine Pairs (delta > 2x scram_sd)\n\n")
        if best and best.get("top_genuine"):
            f.write("Config: %s (z=%s, c=%sbps, F=%s, R=%s)\n\n" % (
                best["name"], best.get("z_entry", "?"), best.get("cost_bps", "?"),
                best.get("use_factor", "?"), best.get("use_regime", "?")))
            f.write("| Pair | Class | Trades | Real Edge | Scram Edge | "
                    "d | td | z_now | Fire |\n")
            f.write("|------|-------|--------|-----------|------------|"
                    "----|-----|-------|------|\n")
            for r in best["top_genuine"][:15]:
                sc = "%+.4f" % r.get("scram_mean", 0) if r.get("scram_mean") is not None else "N/A"
                fire = "YES" if r.get("firing") else ""
                f.write("| %s | %s | %d | %+.4f | %s | %+.4f | %+.2f | %+.2f | %s |\n" % (
                    r["label"], r.get("asset_class", ""), r["n_trades"],
                    r["exp_oos"], sc, r.get("delta", 0),
                    r.get("delta_t", 0), r["z_now"], fire))
        else:
            f.write("*No pairs meet the genuine threshold (real_edge > 2x scram_sd).*\n\n")

        # All solid pairs visual
        f.write("\n## Solid Pairs (delta > scram_sd) -- All Configs\n\n")
        for e in report["experiments"][:8]:
            if e.get("n_pairs", 0) == 0 or not e.get("top_solid"): continue
            top3 = e["top_solid"][:3]
            f.write("- **%s**: %s\n" % (e["name"],
                ", ".join("%s(d=%.2f)" % (r["label"], r.get("delta_t", 0))
                         for r in top3)))
        f.write("\n")

        # Firing pairs
        firing_all = []
        for e in report["experiments"]:
            for r in e.get("top_firing", []):
                if r["label"] not in [x["label"] for x in firing_all]:
                    firing_all.append(r)
        f.write("## Current Firing Pairs\n\n")
        if firing_all:
            f.write("| Pair | Config | z_now | z_entry | Real Edge | d | td |\n")
            f.write("|------|--------|-------|---------|-----------|----|-----|\n")
            for r in firing_all[:15]:
                f.write("| %s | z=%s | %+.2f | %s | %+.4f | %+.4f | %+.2f |\n" % (
                    r["label"], r.get("z_entry", "?"), r["z_now"],
                    r.get("z_entry", "?"), r["exp_oos"],
                    r.get("delta", 0), r.get("delta_t", 0)))
        else:
            f.write("*No pairs currently at entry threshold.*\n\n")

        # Verdict section
        f.write("\n## Research Verdict\n\n")
        if best and best.get("n_genuine", 0) >= 3:
            f.write("**+ Promising**: Best config `%s` -- %d genuine pairs "
                    "(mean d=%+.4f, t=%+.2f).\n\n" % (
                best["name"], best["n_genuine"],
                best["mean_delta"], best["t_delta"]))
            f.write("Live: %d firing.\n\n" % best["n_firing"])
        elif best and best.get("n_solid", 0) >= 3:
            f.write("**~ Marginal**: `%s` shows %d solid pairs, "
                    "%d genuine. "
                    "v5 honest engine greatly reduces v4 artifact edge.\n\n" % (
                best["name"], best.get("n_solid", 0),
                best.get("n_genuine", 0)))
        else:
            f.write("**- No Reliable Edge**: The honest v5 engine reveals "
                    "NO pairs with statistically significant edge above "
                    "scramble baseline.\n\n")
            f.write("The high OOS edges (6-10 sigma) in v4/v5 were artifacts "
                    "of asymmetric engine geometry (+1s profit / -2s stop), "
                    "which produces positive expectancy on ANY random walk.\n\n")

        f.write("## Next Directions\n\n")
        f.write("1. Longer data history (2yr is too short for MR signals)\n")
        f.write("2. Multi-frequency confirmation (intraday ORB + daily z)\n")
        f.write("3. Pairs momentum (trade WITH the trend, not against it)\n")
        f.write("4. Cross-asset structural pairs (Gold/Oil, Equity/Bond)\n")
        f.write("5. Vol-scaled position sizing\n")
        f.write("6. Ensemble methods (OLS + Kalman + PCA consensus)\n\n")

        f.write("---\n*Generated by pairs_research_v8.py "
                "(v5 honest engine + scramble controls)*\n")


def _write_signals(all_experiments):
    best = max(all_experiments,
               key=lambda e: (e.get("n_genuine", 0), e.get("t_delta", -99)),
               default=None)
    if not best or best.get("n_pairs", 0) == 0: return
    signals = []
    for r in (best.get("top_genuine", []) + best.get("top_firing", [])):
        z_entry = r.get("z_entry", 2.0)
        if r["z_now"] < -z_entry: direction = "LONG_A_SHORT_B"
        elif r["z_now"] > z_entry: direction = "SHORT_A_LONG_B"
        else: direction = "NONE"
        signals.append({
            "label": r["label"], "asset_class": r.get("asset_class", ""),
            "sym_a": r.get("sym_a", ""), "sym_b": r.get("sym_b", ""),
            "z_entry": z_entry, "z_now": r["z_now"],
            "direction": direction, "firing": r.get("firing", False),
            "exp_oos": r["exp_oos"], "t_oos": r["t_oos"],
            "delta": r.get("delta"), "delta_t": r.get("delta_t"),
            "hl": r.get("hl"),
        })
    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "experiment": best["name"],
        "n_genuine": best.get("n_genuine", 0),
        "n_solid": best.get("n_solid", 0),
        "n_firing": best.get("n_firing", 0),
        "signals": signals,
    }
    with open(SIGNALS_JSON, "w") as f:
        json.dump(payload, f, indent=1, default=str)


def _write_daily_signals(all_data, all_experiments):
    seen = set(); firing_pairs = []
    for e in all_experiments:
        for r in e.get("top_genuine", []) + e.get("top_firing", []):
            if r["label"] not in seen:
                seen.add(r["label"]); firing_pairs.append(r)
    if not firing_pairs: return
    daily_signals = []
    for r in firing_pairs[:20]:
        z_entry = r.get("z_entry", 2.0)
        if r["z_now"] < -z_entry: direction = "LONG_A_SHORT_B"
        elif r["z_now"] > z_entry: direction = "SHORT_A_LONG_B"
        else: direction = "NONE"
        daily_signals.append({
            "pair": r["label"],
            "sym_a": r.get("sym_a", ""), "sym_b": r.get("sym_b", ""),
            "asset_class": r.get("asset_class", ""),
            "direction": direction,
            "z_now": r["z_now"], "z_entry": z_entry,
            "firing": r.get("firing", False),
            "half_life_days": r.get("hl", 0),
            "lookback": r.get("lookback", 0), "horizon": r.get("horizon", 0),
            "exp_oos_per_trade": r.get("exp_oos", 0),
            "delta_vs_scramble": r.get("delta"),
            "delta_tstat": r.get("delta_t"),
        })
    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "n_signals": len(daily_signals),
        "n_firing": sum(1 for s in daily_signals if s["firing"]),
        "signals": daily_signals,
    }
    with open(DAILY_JSON, "w") as f:
        json.dump(payload, f, indent=1, default=str)


if __name__ == "__main__":
    main()
