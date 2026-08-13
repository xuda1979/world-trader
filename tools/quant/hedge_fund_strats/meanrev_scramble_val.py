"""Signal-scramble validation of the mean-reversion crash-sleeve.

Uses the SINGLE validated engine (meanrev_episode_research.backtest, now with a
scramble flag). Per rebalance the rank order is randomized (rng), destroying the
'long-worst/short-best -> future return' map. p = fraction(scramble SR >= real
SR); PASS if p<0.05 (real edge not reproduced by random chance).

Usage: python tools/quant/hedge_fund_strats/meanrev_scramble_val.py
"""
import json
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from tools.quant.hedge_fund_strats.meanrev_episode_research import (
    load_prices_rets, backtest)

RES = Path(__file__).resolve().parent / "results"
N_SCRAMBLE = 40
SEED = 1234
EPS = [("2018 Q4", "2018-10-10", "2019-08-07"), ("2020 COVID", "2020-02-24", "2020-04-17"),
       ("2011 Euro", "2011-07-27", "2012-01-13"), ("2022-24 bear", "2022-01-05", "2024-02-29")]


def per_eps(r):
    return {name: round(float(r[(r.index >= a) & (r.index <= e)].sum() * 100), 2)
            for name, a, e in EPS}


def main():
    prices, rets = load_prices_rets()
    rng = np.random.default_rng(SEED)
    out = {}
    print("=" * 72, flush=True)
    print("SIGNAL-SCRAMBLE VALIDATION (single validated engine)", flush=True)
    print("=" * 72, flush=True)
    for k, n in [(5, 30), (3, 30)]:
        real = backtest(prices, rets, k, n, rng=rng, scramble=False)
        real_sr = float(real.mean() / real.std() * np.sqrt(252))
        sc_srs = []
        for s in range(N_SCRAMBLE):
            sc = backtest(prices, rets, k, n, rng=rng, scramble=True)
            sc_srs.append(float(sc.mean() / sc.std() * np.sqrt(252)))
            if (s + 1) % 10 == 0:
                print(f"  k{k}n{n} scramble {s+1}/{N_SCRAMBLE}", flush=True)
        sc_srs = np.array(sc_srs)
        p = float((sc_srs >= real_sr).mean())
        verdict = "PASS" if p < 0.05 else "FAIL"
        print(f"\nk={k} n={n}: real SR {real_sr:+.3f} | scrambles mean {sc_srs.mean():+.3f} "
              f"p95 {np.percentile(sc_srs,95):+.3f} | p(sc>=real)={p:.3f} => {verdict}", flush=True)
        print(f"  real episodes: {per_eps(real)}", flush=True)
        out[f"k{k}_n{n}"] = {"real_sr": round(real_sr, 4),
                             "scramble_mean_sr": round(float(sc_srs.mean()), 4),
                             "scramble_p95": round(float(np.percentile(sc_srs, 95)), 4),
                             "p_fraction_scramble_ge_real": round(float(p), 4),
                             "verdict": verdict, "real_loss_episodes": per_eps(real)}
    with open(RES / "meanrev_scramble_val.json", "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print("\nWrote results/meanrev_scramble_val.json", flush=True)


if __name__ == "__main__":
    main()
