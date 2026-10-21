#!/usr/bin/env python3
"""pairs_gate_sweep.py -- sweep IS t-stat qualification strictness (MIN_IS_TSTAT)
and measure REAL vs SCRAMBLE separation of the OOS net portfolio Sharpe.

The base WF gate (Bonferroni at n_tests, FDR_ALPHA=0.05) admits IS t>=~3.84.
We tighten MIN_IS_TSTAT and ask: does the REAL portfolio's OOS Sharpe pull
away from the scramble-control distribution (higher z)?  That identifies the
strictest gate that still leaves enough genuinely-cointegrated pairs to build
a high-Sharpe, falsifiable portfolio.  net = net of 3.8bps round-trip.
"""
import os, sys, json, statistics, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import pairs_portfolio_sim as P

Z = 2.0
COST = 3.8
N_SCRAMBLE = int(sys.argv[2]) if len(sys.argv) > 2 else 12
THRESHOLDS = [float(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 \
    else [4.0, 4.5, 5.0, 5.5, 6.0]
REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "reports", "pairs_gate_sweep.json")


def oos_sharpe(qualified, all_data, oos_date):
    if not qualified:
        return None
    rp = P.run_portfolio([all_data[l] for l in qualified], Z, COST, oos_date)
    if rp is None:
        return None
    m = P.metrics(rp["net"], rp["n_days"], oos_date=oos_date, cal=rp["cal"])
    try:
        return m["OOS"]["sharpe"]
    except Exception:
        return None


def main():
    t0 = time.time()
    results = []
    for T in THRESHOLDS:
        P._SCRAMBLE_SEED = None
        P.MIN_IS_TSTAT = T
        try:
            ad, oos, qual = P.wf_qualified_pairs()
            real_s = oos_sharpe(qual, ad, oos)
        except Exception as e:
            print(f"T={T}: real failed {e}", file=sys.stderr)
            real_s = None
            qual = []

        scram = []
        for seed in range(1, N_SCRAMBLE + 1):
            P._SCRAMBLE_SEED = seed
            try:
                sd, soos, sq = P.wf_qualified_pairs()
            except Exception:
                sd = {}; soos = oos; sq = []
            if not sq:
                continue
            s = oos_sharpe(sq, sd, soos or oos)
            if s is not None:
                scram.append(s)
        P._SCRAMBLE_SEED = None

        row = {"min_is_tstat": T, "n_real_qualified": len(qual),
               "real_oos_sharpe": round(real_s, 3) if real_s is not None else None,
               "n_scramble_runs": len(scram)}
        if len(scram) > 1:
            row["scram_mean"] = round(statistics.mean(scram), 3)
            row["scram_sd"] = round(statistics.stdev(scram), 3)
            row["scram_max"] = round(max(scram), 3)
            if real_s is not None:
                z = (real_s - statistics.mean(scram)) / statistics.stdev(scram)
                row["real_z_vs_scramble"] = round(z, 2)
                row["pct_scramble_below_real"] = round(
                    100 * sum(1 for x in scram if x < real_s) / len(scram), 1)
        results.append(row)
        P._SCRAMBLE_SEED = None
        print(f"T={T}: qual={len(qual)} real={row.get('real_oos_sharpe')} "
              f"scram_n={len(scram)} "
              f"scram(mean,sd)={row.get('scram_mean')},{row.get('scram_sd')} "
              f"z={row.get('real_z_vs_scramble')}", flush=True)

    with open(REPORT, "w") as f:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "z_entry": Z, "cost_bps": COST, "n_scramble": N_SCRAMBLE,
                   "results": results,
                   "elapsed_s": round(time.time() - t0, 1)}, f, indent=1, default=str)
    print(f"\nWrote {REPORT}  elapsed {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
