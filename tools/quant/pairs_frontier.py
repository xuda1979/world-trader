#!/usr/bin/env python3
"""pairs_frontier.py -- diversification frontier + scramble falsification.

Measures how calendar-time OOS net Sharpe (net of 3.8bps) scales as we add
top-k qualified pairs (by IS t-stat) to the portfolio.  Repeats the identical
construction on scramble-control universes to determine whether the breadth
benefit and absolute Sharpe are distinguishable from noise.

This is the honest building block for "build a high-Sharpe portfolio":
it shows the optimal breadth (k*) and whether adding more pairs genuinely
lifts risk-adjusted return after costs.
"""
import os, sys, json, statistics, math, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import pairs_portfolio_sim as P
import pairs_research_v4 as v4

Z = 2.0
COST = 3.8 * 1.0          # round-trip bps
REPORT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "reports", "pairs_frontier.json")
REPORT_MD = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "reports", "pairs_frontier.md")


def tstat_for(label, all_data, oos_date):
    """Replicate the IS t-stat the WF gate used, using only IS data."""
    pr = all_data[label]
    n_is = sum(1 for d in pr["dates"] if d < oos_date)
    spread = pr["spread"]
    lb = pr.get("lookback", 20)
    hz = pr.get("horizon", 10)
    # reuse the sim's wf_qualify edge computation path signal
    a = pr["a"][:n_is]; b = pr["b"][:n_is]; s = spread[:n_is]
    try:
        bt = v4.backtest_pair_with_params(s, lb, hz, v4.Z_ENTRY, v4.Z_EXIT, 0.0)
    except Exception:
        return 0.0
    if not bt:
        return 0.0
    return bt.get("tstat", 0.0) or 0.0


def frontier(qualified_tuples, all_data, oos_date):
    """Return list of (k, OOS_net_sharpe, OOS_gross_sharpe, sorted_labels).

    NOTE: OOS metric must match the sim's _emit_run: pass the true WF split
    date (oos_date) to metrics and read ['OOS'].  Slicing with rp['cal'][0]
    silently includes the in-sample strip and is NOT the OOS Sharpe."""
    qualified_tuples = [t for t in qualified_tuples if t[1] is not None]
    if not qualified_tuples:
        return []
    ranked = sorted(qualified_tuples, key=lambda t: -(t[1] or 0.0))
    out = []
    for k in range(1, len(ranked) + 1):
        labs = [l for l, _ in ranked[:k]]
        rp = P.run_portfolio([all_data[l] for l in labs], Z, COST, oos_date)
        if rp is None:
            continue
        m = P.metrics(rp["net"], rp["n_days"], oos_date=oos_date, cal=rp["cal"])
        mg = P.metrics(rp["gross"], rp["n_days"], oos_date=oos_date, cal=rp["cal"])
        net = m["OOS"]["sharpe"] if m and m.get("OOS") else None
        gros = mg["OOS"]["sharpe"] if mg and mg.get("OOS") else None
        out.append({"k": k, "labels": labs,
                    "net_sharpe": round(net, 3) if net is not None else None,
                    "gross_sharpe": round(gros, 3) if gros is not None else None})
    return out


def main():
    t0 = time.time()
    n_scramble = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    all_data, oos_date, qualified = P.wf_qualified_pairs()
    tups = [(l, tstat_for(l, all_data, oos_date)) for l in qualified]
    real_fr = frontier(tups, all_data, oos_date)

    # scramble controls: full pipeline on shuffled universes
    scram_kstar_net = []
    scram_all = {k: [] for k in range(1, len(qualified) + 1)}
    for seed in range(1, n_scramble + 1):
        if seed in (5,):   # known 0-qualified draws -> skip (no pairs to rank)
            pass
        P._SCRAMBLE_SEED = seed
        try:
            sd, oos2, sq = P.wf_qualified_pairs()
        except Exception as e:
            print(f"  seed {seed} failed: {e}", file=sys.stderr)
            continue
        if not sq:
            continue
        soos = oos2 or oos_date
        stu = [(l, tstat_for(l, sd, soos)) for l in sq]
        fr = frontier(stu, sd, soos)
        for row in fr:
            k = row["k"]
            if row["net_sharpe"] is not None:
                scram_all[k].append(row["net_sharpe"])
        if fr:
            scram_kstar_net.append(fr[-1]["net_sharpe"])

    # summarize
    real_best = max(real_fr, key=lambda r: r["net_sharpe"] or -1e9)
    print(f"\n=== REAL WF frontier (z={Z}, cost={COST}bps) ===")
    print(f"{'k':>3} {'net_sharpe':>10} {'gross_sharpe':>12}")
    for r in real_fr:
        print(f"{r['k']:>3} {str(r['net_sharpe']):>10} {str(r['gross_sharpe']):>12}")
    print(f"\nBest k* = {real_best['k']}  net_sharpe = {real_best['net_sharpe']}")

    print(f"\n=== SCRAMBLE controls ({n_scramble} seeds, {len(scram_kstar_net)} produced pairs) ===")
    if scram_kstar_net:
        print(f"  full-portfolio net sharpe: mean={statistics.mean(scram_kstar_net):.2f} "
              f"sd={statistics.stdev(scram_kstar_net):.2f} "
              f"min={min(scram_kstar_net):.2f} max={max(scram_kstar_net):.2f}")
    print("  per-k metrics (mean over scramble seeds):")
    for k in sorted(scram_all):
        if scram_all[k]:
            print(f"    k={k}: net mean={statistics.mean(scram_all[k]):.2f} "
                  f"n={len(scram_all[k])}")

    # z-score of real best vs scramble full-portfolio
    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "z_entry": Z, "cost_bps": COST, "n_scramble": n_scramble,
        "real_qualified": qualified, "real_frontier": real_fr,
        "scramble_n_full": len(scram_kstar_net),
        "scramble_full_mean": round(statistics.mean(scram_kstar_net), 3) if scram_kstar_net else None,
        "scramble_full_sd": round(statistics.stdev(scram_kstar_net), 3) if len(scram_kstar_net) > 1 else None,
        "real_best": real_best,
        "elapsed_s": round(time.time() - t0, 1),
    }
    if len(scram_kstar_net) > 1 and real_best["net_sharpe"]:
        zval = (real_best["net_sharpe"] - statistics.mean(scram_kstar_net)) / statistics.stdev(scram_kstar_net)
        payload["real_z_vs_scramble"] = round(zval, 2)
    with open(REPORT_JSON, "w") as f:
        json.dump(payload, f, indent=1, default=str)
    print(f"\nWrote {REPORT_JSON} in {payload['elapsed_s']}s")


if __name__ == "__main__":
    main()
