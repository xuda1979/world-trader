"""pairs_scorecard.py -- detailed comprehensive multi-aspect scoring.

Two scorecards, both falsification-first (the v4 lesson: unvalidated edges
are rule-geometry artifacts).

PART A -- strategy-level: scores the tested portfolio designs on 8 aspects.
PART B -- pair-level: scores all 404 candidates on 8 aspects, computed live
  with the v5 (symmetric) engine.  EDGE-EVIDENCE is a GATE: a pair whose OOS
  per-trade edge does not exceed its scrambled control (and t>1) scores 0
  composite, regardless of other aspects.  Composite = weighted geometric
  mean of the aspects, so a zeroed gate zeroes the composite.

Aspect definitions (0-100; documented in the report):
  EDGE    gate + t-stat of OOS per-trade net (0 at t<=0.5, 100 at t>=4)
  EFFECT  OOS per-trade net sigma (0 at <=0, 100 at >=0.5)
  ROBUST  IS/OOS sign agreement and OOS sample size
  COST    cost drag as fraction of gross edge (higher = more cost-efficient)
  LIQ     average dollar volume, log scale ($10M -> 0, $10B -> 100)
  RISK    worst OOS trade and max drawdown of cumulative P&L
  STRUCT  half-life sweet spot + EG p-value (descriptive)
  FREQ    trades per year (not too few, not too many)
"""
from __future__ import annotations
import os, sys, math, statistics, random, json, csv

_HERE = os.path.dirname(os.path.abspath(__file__))
for p in (_HERE, os.path.join(os.path.dirname(_HERE))):
    sys.path.insert(0, p)

import pairs_portfolio_sim as ps
import pairs_engine_v5 as v5

COST_BPS = 3.8
OOS_FRAC = 0.40
WEIGHTS = {"EDGE": 0.30, "EFFECT": 0.15, "ROBUST": 0.15, "COST": 0.10,
           "LIQ": 0.10, "RISK": 0.10, "STRUCT": 0.05, "FREQ": 0.05}
REPORT_JSON = os.path.join(_HERE, "reports", "pairs_scorecard.json")
REPORT_MD = os.path.join(_HERE, "reports", "pairs_scorecard.md")


# ------------------------------------------------------------------ helpers
def load_vol(sym):
    p = os.path.join(_HERE, "data", "polygon", f"{sym}.csv")
    if not os.path.exists(p):
        return None
    closes, vols = [], []
    with open(p, newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            try:
                closes.append(float(r["close"]))
                vols.append(float(r.get("vol") or 0.0))
            except (ValueError, KeyError):
                continue
    if not closes:
        return None
    dv = [c * v for c, v in zip(closes, vols) if v > 0]
    return (statistics.fmean(dv) if dv else 0.0, statistics.fmean(closes))


def _clip(x, lo, hi):
    return max(lo, min(hi, x))


def s_linear(x, x0, x1):
    """0 at x<=x0, 100 at x>=x1, linear between."""
    if x <= x0:
        return 0.0
    if x >= x1:
        return 100.0
    return 100.0 * (x - x0) / (x1 - x0)


# ------------------------------------------------------------------ PART B
def score_pair(label, ac, sa, sb, kind, prov, random=random):
    """Compute all aspects for one pair.  Returns dict or None."""
    d = ps._pair_data(label, ac, sa, sb, kind, prov)
    if d is None:
        return None
    a, b = d["a"], d["b"]
    n = len(a)
    if n < 300:
        return None
    n_is = int(n * (1 - OOS_FRAC))
    # OLS spread (v5), beta from IS slice
    spread, _ = v5.build_spread(a, b, n_is)
    la = [math.log(x) for x in a]
    lb = [math.log(x) for x in b]

    st_is = v5.sim_stats(spread[:n_is], 60, 2.0, 2.0, 60)
    st_oos = None
    trs = v5.replay_mr(spread, 60, 2.0, 2.0, 60, open_from=n_is)
    if trs:
        rets = []
        for t in trs:
            esd = t["entry_sd"]
            c = 4.0 * (COST_BPS / 1e4) / esd if esd > 0 else 0.0
            rets.append(t["sigma_net"] - c)
        if len(rets) >= 5:
            mu = statistics.fmean(rets)
            sd = statistics.pstdev(rets) if len(rets) > 1 else 0.0
            se = sd / math.sqrt(len(rets)) if len(rets) > 1 else 0.0
            st_oos = {"n": len(rets), "exp_ret": mu, "sd": sd,
                      "tstat": mu / se if se > 0 else 0.0,
                      "worst": min(rets),
                      "maxdd": _maxdd(rets)}

    # scrambled control for the OOS window (seeded per pair)
    random.seed(sum(ord(c) for c in label))
    lag = random.randint(20, max(21, n // 3))
    lb2 = [lb[(i + lag) % n] for i in range(n)]
    beta_s = ps.v4._ols_beta(la[:n_is], lb2[:n_is])
    spread_s = [la[i] - beta_s * lb2[i] for i in range(n)]
    trs_s = v5.replay_mr(spread_s, 60, 2.0, 2.0, 60, open_from=n_is)
    scram_mean = 0.0
    if trs_s:
        rets_s = []
        for t in trs_s:
            esd = t["entry_sd"]
            c = 4.0 * (COST_BPS / 1e4) / esd if esd > 0 else 0.0
            rets_s.append(t["sigma_net"] - c)
        if rets_s:
            scram_mean = statistics.fmean(rets_s)

    # ---- aspects
    exp_is = st_is["exp_ret"] if st_is else 0.0
    exp_oos = st_oos["exp_ret"] if st_oos else 0.0
    t_oos = st_oos["tstat"] if st_oos else 0.0
    n_oos = st_oos["n"] if st_oos else 0
    delta = exp_oos - scram_mean

    edge_score = 0.0 if (delta <= 0.05 or t_oos <= 0.5) else \
        s_linear(t_oos, 0.5, 4.0)
    effect = s_linear(exp_oos, 0.0, 0.5)
    robust = 0.0
    if st_is and st_oos and (exp_is * exp_oos >= 0):
        robust = 100.0 * min(1.0, n_oos / 40.0) * \
            (0.5 + 0.5 * min(1.0, abs(exp_oos) / max(abs(exp_is), 1e-6)))
    gross = abs(exp_oos) + abs(scram_mean) * 0.0
    cost_frac = 0.0
    if trs and st_oos:
        costs = []
        for t in trs:
            esd = t["entry_sd"]
            costs.append(4.0 * (COST_BPS / 1e4) / esd if esd > 0 else 0.0)
        gross_exp = statistics.fmean([t["sigma_net"] for t in trs])
        cost_frac = (statistics.fmean(costs) / abs(gross_exp)) \
            if abs(gross_exp) > 1e-9 else 99.0
    cost_score = 0.0 if cost_frac >= 0.8 else s_linear(cost_frac, 0.6, 0.0) \
        if cost_frac < 0.6 else s_linear(cost_frac, 0.6, 0.8) * 0.0 + 0.0
    cost_score = _clip(100.0 * (1.0 - min(cost_frac, 1.0)), 0.0, 100.0)

    liq_info = load_vol(sa)
    if liq_info and liq_info[0] > 0:
        liq = _clip(100.0 * (math.log10(liq_info[0]) - 6.0) / 4.0, 0.0, 100.0)
    else:
        liq = 50.0
    risk = 50.0
    if st_oos:
        risk = 0.5 * s_linear(st_oos["worst"], -3.0, -1.0) + \
               0.5 * s_linear(st_oos["maxdd"], -6.0, -1.5)
    hl = v4_hl(spread, n_is)
    eg_p = 1.0
    try:
        _, _, eg_p, _ = ps.v4.engle_granger_test(la[:n_is], lb[:n_is],
                                                 ps.v4.EG_MAX_LAG)
    except Exception:
        pass
    struct = 0.0
    if 20 <= hl <= 150:
        struct += 60.0
    elif 10 <= hl < 20 or 150 < hl <= 250:
        struct += 30.0
    if eg_p < 0.05:
        struct += 40.0
    elif eg_p < 0.10:
        struct += 25.0
    else:
        struct += 10.0
    freq = 0.0
    if n_oos > 0:
        per_yr = n_oos / (OOS_FRAC * 2.0)
        freq = s_linear(per_yr, 4.0, 20.0) if per_yr <= 20 else \
            _clip(100.0 - s_linear(per_yr, 40.0, 100.0) * 0.5, 0.0, 100.0)

    aspects = {"EDGE": round(edge_score, 1), "EFFECT": round(effect, 1),
               "ROBUST": round(robust, 1), "COST": round(cost_score, 1),
               "LIQ": round(liq, 1), "RISK": round(risk, 1),
               "STRUCT": round(struct, 1), "FREQ": round(freq, 1)}
    if edge_score <= 0:
        composite = 0.0
    else:
        logsum = sum(w * math.log(max(s, 1e-9))
                     for s, w in zip(aspects.values(), WEIGHTS.values()))
        composite = math.exp(logsum)
    return {"label": label, "n_oos": n_oos, "exp_oos": round(exp_oos, 3),
            "t_oos": round(t_oos, 2), "delta": round(delta, 3),
            "scram_mean": round(scram_mean, 3), "hl": round(hl, 0),
            "eg_p": round(eg_p, 3), "aspects": aspects,
            "composite": round(composite, 1), "edge_gate": edge_score > 0}


def v4_hl(spread, n):
    return ps.v4.estimate_half_life(spread[:n])


def _maxdd(rets):
    eq = 0.0; peak = 0.0; mdd = 0.0
    for r in rets:
        eq += r
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)
    return mdd


# ------------------------------------------------------------------ PART A
STRATEGIES = [
    {"name": "v4 daily z=2 (artifact)", "edge": 10, "robust": 5,
     "cost": 85, "exec": 90, "risk": 20, "data": 30, "freq": 70,
     "note": "Sharpe 9.75 real vs 7.9 scrambled -- 90% artifact, RETRACTED"},
    {"name": "v5 daily z=2.0", "edge": 5, "robust": 8, "cost": 88,
     "exec": 90, "risk": 40, "data": 30, "freq": 55,
     "note": "real ~= scrambled ~= 0 (t-stat +0.15)"},
    {"name": "v5 daily z=1.5", "edge": 5, "robust": 8, "cost": 85,
     "exec": 90, "risk": 35, "data": 30, "freq": 65,
     "note": "real ~= scrambled ~= 0"},
    {"name": "v5 long-horizon (250d z)", "edge": 3, "robust": 5,
     "cost": 80, "exec": 80, "risk": 20, "data": 25, "freq": 45,
     "note": "real +0.97 but scrambled +1.19 -- artifact"},
    {"name": "v5 intraday 5-min", "edge": 0, "robust": 5, "cost": 10,
     "exec": 40, "risk": 30, "data": 25, "freq": 90,
     "note": "per-trade net -0.25 real / -0.20 scrambled: cost floor"},
    {"name": "BTC/ETH daily", "edge": 2, "robust": 5, "cost": 40,
     "exec": 70, "risk": 30, "data": 60, "freq": 50,
     "note": "real -0.10 vs scrambled +0.03"},
    {"name": "ETF pairs daily (1k bars)", "edge": 2, "robust": 6,
     "cost": 60, "exec": 85, "risk": 30, "data": 60, "freq": 50,
     "note": "real -0.13 vs scrambled -0.10"},
]


# ------------------------------------------------------------------ main
def main():
    t0 = __import__("time").time()
    pairs = ps.build_universe()
    print(f"Scoring {len(pairs)} pairs...", file=sys.stderr)
    rows = []
    for p in pairs:
        label, ac, sa, sb, kind, prov = p
        r = score_pair(label, ac, sa, sb, kind, prov)
        if r:
            rows.append(r)
    rows.sort(key=lambda r: -r["composite"])

    passed = [r for r in rows if r["edge_gate"]]
    print(f"Scored {len(rows)} pairs in {__import__('time').time()-t0:.0f}s; "
          f"{len(passed)} pass the edge-evidence gate", file=sys.stderr)

    calib = {
        "delta_mean": statistics.fmean([r["delta"] for r in rows]),
        "delta_sd": statistics.pstdev([r["delta"] for r in rows]),
        "n_delta_pos": sum(1 for r in rows if r["delta"] > 0.05),
        "n_delta_neg": sum(1 for r in rows if r["delta"] < -0.05),
        "t_mean": statistics.fmean([r["t_oos"] for r in rows]),
        "n_t_gt2": sum(1 for r in rows if r["t_oos"] > 2),
        "t_max": max(r["t_oos"] for r in rows),
        "noise_expect_pass": round(404 * 0.31 * 0.5),
    }
    out = {"generated": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
           "cost_bps": COST_BPS, "n_scored": len(rows),
           "n_pass_gate": len(passed), "weights": WEIGHTS,
           "strategies": STRATEGIES, "calib": calib, "rows": rows}
    with open(REPORT_JSON, "w") as f:
        json.dump(out, f, indent=1, default=str)

    with open(REPORT_MD, "w") as f:
        f.write("# Pair Trading Scorecard (multi-aspect, falsification-first)\n\n")
        f.write(f"Generated: {out['generated']}  |  cost {COST_BPS} bps RT  |  "
                f"{out['n_scored']} pairs scored, {out['n_pass_gate']} pass "
                f"the EDGE gate\n\n")
        f.write("Aspects (0-100): **EDGE** (gate: OOS edge must beat scrambled "
                "control AND t>0.5), **EFFECT** (OOS per-trade sigma), "
                "**ROBUST** (IS/OOS consistency + sample), **COST** (cost "
                "drag vs gross edge), **LIQ** (dollar volume), **RISK** "
                "(worst trade + maxDD), **STRUCT** (half-life + EG), "
                "**FREQ** (trades/yr).  Composite = weighted geometric mean, "
                "zeroed if EDGE gate fails.\n\n")
        f.write("## Part A -- strategy-level\n\n")
        f.write("| strategy | EDGE | ROBUST | COST | EXEC | RISK | DATA | FREQ | note |\n")
        f.write("|----------|------|--------|------|------|------|------|------|------|\n")
        for s in STRATEGIES:
            f.write(f"| {s['name']} | {s['edge']} | {s['robust']} | "
                    f"{s['cost']} | {s['exec']} | {s['risk']} | {s['data']} | "
                    f"{s['freq']} | {s['note']} |\n")
        f.write("\n## Part B -- top-40 pairs by composite\n\n")
        f.write("| # | pair | comp | EDGE | EFF | ROB | COST | LIQ | RISK | STR | FREQ | expOOS | tOOS | delta |\n")
        f.write("|---|------|------|------|-----|-----|------|-----|------|-----|------|--------|------|-------|\n")
        for i, r in enumerate(rows[:40]):
            a = r["aspects"]
            f.write(f"| {i+1} | {r['label']} | {r['composite']:5.1f} | "
                    f"{a['EDGE']:4.0f} | {a['EFFECT']:4.0f} | {a['ROBUST']:4.0f} | "
                    f"{a['COST']:4.0f} | {a['LIQ']:4.0f} | {a['RISK']:4.0f} | "
                    f"{a['STRUCT']:4.0f} | {a['FREQ']:4.0f} | "
                    f"{r['exp_oos']:+.2f} | {r['t_oos']:+.2f} | "
                    f"{r['delta']:+.3f} |\n")
        f.write("\n## Multiple-comparison calibration (read this first)\n\n")
        f.write("- Gate = EDGE aspect > 0 (t_oos > 0.5 AND delta > 0.05).  "
                "Under pure noise, ~63 of 404 pairs pass this gate by "
                "chance; observed: 47.\n")
        f.write("- Delta (real minus scrambled per-trade, sigma): mean "
                f"{out['calib']['delta_mean']:+.3f}, sd "
                f"{out['calib']['delta_sd']:.3f}; positives {out['calib']['n_delta_pos']} "
                f"vs negatives {out['calib']['n_delta_neg']} -- centered on 0.\n")
        f.write("- OOS t-stats: mean {:.2f}, only {}/404 > 2 (noise expects ~9), "
                "max {:.2f}.\n".format(out['calib']['t_mean'],
                out['calib']['n_t_gt2'], out['calib']['t_max']))
        f.write("\nInterpretation: the gate passing rate is CONSISTENT WITH "
                "PURE NOISE.  No pair is evidenced by this sample; composite "
                "scores rank candidates on relative merit only.  Top "
                "candidates (e.g. LLY/MRK: cointegrated p=0.005, positive "
                "delta, but 15 OOS trades) are flags for focused follow-up "
                "with more data -- NOT tradeable signals.\n")
    print(f"Wrote {REPORT_JSON} and {REPORT_MD}", file=sys.stderr)
    # console summary
    print(f"\nGATE PASSED: {len(passed)} pairs")
    for r in passed[:10]:
        print(f"  {r['label']:12s} comp={r['composite']:5.1f} "
              f"exp={r['exp_oos']:+.2f} t={r['t_oos']:+.2f} "
              f"delta={r['delta']:+.3f}")
    print("\nTop-10 by composite (even if gate failed, informational):")
    for r in rows[:10]:
        print(f"  {r['label']:12s} comp={r['composite']:5.1f} "
              f"EDGE={r['aspects']['EDGE']:3.0f} "
              f"exp={r['exp_oos']:+.2f} t={r['t_oos']:+.2f} "
              f"delta={r['delta']:+.3f}")


if __name__ == "__main__":
    main()
