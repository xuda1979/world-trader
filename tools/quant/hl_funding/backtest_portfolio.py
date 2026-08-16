"""Combined multi-coin funding-capture backtest + null vs random-entry.

We have only ~500 hourly funding rows per coin (3-ish weeks) ending a fixed 2023
cutoff, and NO price series for the window. So this establishes the CARRY leg.

Two rules compared:
  R1 (both-direction): long when funding<=-e, short when funding>=+e, exit |f|<=x
  R2 (long-only on deep-negative funding): long when funding<=-e, exit f>=x
     (motivated by the persistence asymmetry: negative funding persists, positive snaps back)

Costs swept [15,30,60]bp round-trip (2 legs x taker + slippage).
Null: random entry/exit timestamps (same position counts + holding lengths
shuffled) to test whether any carry edge exceeds chance.

Output: hl_funding_portfolio.json
"""
from __future__ import annotations
import pandas as pd, glob, os, numpy as np, json, argparse

DATADIR = os.path.join(os.path.dirname(__file__), "data")
def load_coin(coin):
    df = pd.read_csv(os.path.join(DATADIR, f"fund_{coin}.csv")).sort_values("time_ms")
    return df["fundingRate"].to_numpy() * 100.0

def backtest(f, enter, exit_, cost_rt, long_only=False):
    n = len(f); side = np.zeros(n, dtype=int); pos = 0
    for i in range(n-1):
        fi = f[i]
        if pos == 0:
            if (not long_only and fi >= enter) :
                pos = -1; side[i] = -1
            elif fi <= -enter:
                pos = 1; side[i] = 1
        else:
            if abs(fi) <= exit_ or (long_only and fi >= exit_):
                pos = 0
            else:
                side[i] = pos
    carry = np.where(side > 0, -f, np.where(side < 0, f, 0.0))
    # count round trips to subtract costs
    n_ent = int(((side[1:] != 0) & (side[:-1] == 0)).sum() + (side[0] != 0))
    gross = carry.sum()
    net = gross - n_ent * cost_rt
    days = n / 24.0
    invested = (side != 0).mean()
    return {"net": net, "gross": gross, "n_ent": n_ent, "invested": invested,
            "ann_full": net / days * 365.0, "ann_inv": net / (invested*days)*365.0 if invested else 0}

def run_all(coins, enter, exit_, cost_rt, long_only=False, n_boot=2000, seed=1):
    rng = np.random.default_rng(seed)
    results = []
    for c in coins:
        f = load_coin(c)
        r = backtest(f, enter, exit_, cost_rt, long_only)
        r["coin"] = c
        # null: shuffle the side-mask (random entry/exit same density)
        nulls = []
        for _ in range(n_boot):
            perm = rng.permutation(len(f))
            fs = f[perm]
            rr = backtest(fs, enter, exit_, cost_rt, long_only)
            nulls.append(rr["net"])
        nulls = np.array(nulls)
        p = (np.abs(nulls) >= abs(r["net"])).mean()
        r["p_random"] = round(float(p), 4)
        r["null_mean_net"] = round(float(nulls.mean()), 3)
        results.append(r)
    return results

if __name__ == "__main__":
    coins = sorted(os.path.basename(f)[5:-4] for f in glob.glob(f"{DATADIR}/fund_*.csv"))
    coins = [c for c in coins if os.path.exists(f"{DATADIR}/fund_{c}.csv")]
    ap = argparse.ArgumentParser()
    ap.add_argument("--enter", type=float, default=0.03)
    ap.add_argument("--exit", type=float, default=0.01)
    ap.add_argument("--cost_rt", type=float, default=0.30)
    ap.add_argument("--long_only", action="store_true")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    res = run_all(coins, args.enter, args.exit, args.cost_rt, args.long_only, args.boot, args.seed)
    tot_net = sum(r["net"] for r in res)
    tot_days = sum(r["n_hour"]/24 for r in res) if False else None
    wins = [r for r in res if r["net"] > 0]
    sig = [r for r in res if r["p_random"] < 0.15]
    print(f"long_only={args.long_only} enter={args.enter} exit={args.exit} cost={args.cost_rt}%rt")
    print(f"total net carry (all coins, sum %): {tot_net:+.2f}")
    print(f"coins with net>0: {len(wins)}/{len(res)} | p<0.15: {len(sig)}")
    for r in res:
        print(f"  {r['coin']:5s} net%win={r['net']:+7.2f} gross={r['gross']:+7.2f} ent={r['n_ent']:3d} "
              f"ann_full={r['ann_full']:+6.1f}% p={r['p_random']:.3f}")
    out = {"long_only": args.long_only, "enter": args.enter, "exit": args.exit,
           "cost_rt": args.cost_rt, "total_net": tot_net, "results": res}
    rdir = os.path.join(os.path.dirname(__file__), "..", "reports"); os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(rdir, "hl_funding_portfolio.json"), "w") as fh:
        json.dump(out, fh, indent=2)
