#!/usr/bin/env python3
"""pairs_rolling_oos.py -- longer-OOS truth test via rolling walk-forward.

The static walk-forward book reports OOS net Sharpe 6.96, but with only ~509
bars total and a 60/40 split the "OOS" is just 204 days with a fixed
IS-qualified set.  To get a longer, more trustworthy out-of-sample read we
re-fit qualification on a rolling IS window and trade forward, so every traded
day (post-warmup) is out-of-sample relative to its own qualification.

We compare the REAL rolling result against lag-SCRAMBLE controls under the
identical rolling machinery.  If the real rolling Sharpe does not separate from
the scramble floor, the 6.96 static number is a fixed-selection artifact, not a
tradeable edge.  Cost = 3.8 bps RT.
"""
import os, sys, time, json, statistics
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import pairs_portfolio_sim as P

Z = 2.0
COST = 3.8
REPORT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "reports", "pairs_rolling_oos.json")
CONFIGS = [(150, 30), (200, 50), (250, 50), (200, 100), (250, 30)]


def run_rolling(is_bars, step, scramble_seed=None):
    """Rolling WF via the v5 engine.  Passing scrambled all_data (loaded with
    _SCRAMBLE_SEED set) gives the disguise control under identical rolling
    machinery.  Every traded day is OOS relative to its own episode refit."""
    import pairs_engine_v5 as v5
    P._SCRAMBLE_SEED = scramble_seed
    try:
        ad, _, _ = P.wf_qualified_pairs()   # load universe (respects scramble)
        rr = v5.rolling(ad, Z, COST, is_bars=is_bars, step=step)
    finally:
        P._SCRAMBLE_SEED = None
    if rr is None:
        return None, None
    m = P.metrics(rr["net"], len(rr["net"]), cal=rr["cal"])
    return m, rr


def main():
    t0 = time.time()
    n_scramble = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    results = []
    for is_bars, step in CONFIGS:
        m, rr = run_rolling(is_bars, step)
        real_sh = m["ALL"]["sharpe"] if m else None
        real_gross = None
        if rr is not None:
            mg = P.metrics(rr["gross"], len(rr["gross"]), cal=rr["cal"])
            real_gross = mg["ALL"]["sharpe"] if mg else None
        # scramble
        scram = []
        for seed in range(1, n_scramble + 1):
            ms, _ = run_rolling(is_bars, step, scramble_seed=seed)
            if ms and ms["ALL"] and ms["ALL"]["sharpe"] is not None:
                scram.append(ms["ALL"]["sharpe"])
        row = {"is_bars": is_bars, "step": step,
               "traded_days": len(rr["cal"]) if rr else 0,
               "real_net_sharpe": round(real_sh, 3) if real_sh is not None else None,
               "real_gross_sharpe": round(real_gross, 3) if real_gross is not None else None,
               "n_scramble": len(scram)}
        if len(scram) > 1:
            row["scram_mean"] = round(statistics.mean(scram), 3)
            row["scram_sd"] = round(statistics.stdev(scram), 3)
            row["scram_max"] = round(max(scram), 3)
            if real_sh is not None:
                row["real_z"] = round((real_sh - statistics.mean(scram)) / statistics.stdev(scram), 2)
        results.append(row)
        print(f"IS={is_bars} step={step} days={row['traded_days']} "
              f"real={row['real_net_sharpe']} scram={row.get('scram_mean')}+/-{row.get('scram_sd')} "
              f"z={row.get('real_z')}", flush=True)
    with open(REPORT, "w") as f:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "z_entry": Z, "cost_bps": COST,
                   "configs": results, "elapsed_s": round(time.time()-t0,1)},
                  f, indent=1, default=str)
    print(f"\nWrote {REPORT}  elapsed {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
