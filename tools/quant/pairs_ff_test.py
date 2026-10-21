"""pairs_ff_test.py -- century-scale test of the return-predictability families.

The 2-year pair-level data could not reject the null because the sample was
too short.  The Fama-French daily files provide ~26,000 daily observations
(1926-2026) of Mkt-RF, SMB, HML, RF and the momentum factor (MOM).  This is
the largest sample available in the repo, and it lets us ask the definitive
question for each signal family AT THE MARKET/FACTOR LEVEL:

  Does the trailing z-score of a factor's returns (rolling window mean/sd)
  predict future h-day returns?

Families tested: short-horizon reversal (L=5-20), medium momentum (L=40-120),
long-horizon reversion (L=250).  Method: quintile portfolios of the z-signal
with non-overlapping sampling for significance.  Plus a v5-engine trade
simulation on Mkt-RF over the full century, real vs scrambled (rotation).

At SPY-level costs (~1-2 bps) the 3.8 bps budget is not binding for any
signal found here -- this tests signal existence, not cost viability.
"""
from __future__ import annotations
import os, sys, csv, math, statistics, random, json

_HERE = os.path.dirname(os.path.abspath(__file__))
FF_DIR = os.path.join(_HERE, "data", "ff_factors")
OUT = os.path.join(_HERE, "reports", "pairs_ff_test.json")


def parse_ff(path):
    rows = []
    with open(path) as f:
        for l in f:
            l = l.strip()
            if not l or l.startswith(("This", "The", "compounds", "Copyright",
                                      ",Mkt")):
                continue
            parts = l.split(",")
            if len(parts) < 2 or not parts[0].isdigit():
                continue
            try:
                date = parts[0]
                vals = [float(x) for x in parts[1:]]
            except ValueError:
                continue
            rows.append((date, vals))
    return rows


def predict_test(series, lookback, horizon):
    """Quintile test: z_t (trailing window mean/sd) vs future h-day return.
    Non-overlapping sampling for significance.  Returns dict."""
    n = len(series)
    zs, futs = [], []
    for i in range(lookback, n - horizon):
        w = series[i - lookback:i]
        mu = statistics.fmean(w)
        sd = statistics.pstdev(w) if len(w) > 1 else 0.0
        if sd <= 0:
            continue
        # signal = trailing L-day cumulative return in units of its iid std
        # (time-series momentum signal; regression slope reveals direction)
        z = sum(w) / math.sqrt(lookback) / sd
        fut = sum(series[i:i + horizon])
        zs.append(z)
        futs.append(fut)
    if len(zs) < 200:
        return None
    # quintiles on non-overlapping samples
    q_edges = [zs[0], zs[len(zs) // 4], zs[len(zs) // 2],
               zs[3 * len(zs) // 4], zs[-1]]
    qs = {q: [] for q in range(5)}
    for z, f in zip(zs, futs):
        q = min(4, max(0, sum(1 for e in q_edges[1:] if z >= e)))
        qs[q].append(f)
    means = [statistics.fmean(qs[q]) for q in range(5)]
    spread = means[4] - means[0]
    # significance on non-overlapping samples (every horizon-th obs)
    idxs = list(range(0, len(futs), horizon))
    q5 = [futs[j] for j in idxs if zs[j] >= q_edges[3]]
    q1 = [futs[j] for j in idxs if zs[j] < q_edges[1]]
    # also the continuous regression t on non-overlapping
    sel = [(zs[j], futs[j]) for j in idxs]
    x = [s[0] for s in sel]; y = [s[1] for s in sel]
    if len(x) < 30:
        return None
    mx = statistics.fmean(x); my = statistics.fmean(y)
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(len(x)))
    var = sum((xi - mx) ** 2 for xi in x)
    b = cov / var if var > 0 else 0.0
    resid = [y[i] - my - b * (x[i] - mx) for i in range(len(x))]
    rv = sum(r * r for r in resid) / max(1, len(resid) - 2)
    se = math.sqrt(rv / var) if var > 0 else 0.0
    t = b / se if se > 0 else 0.0
    return {"L": lookback, "H": horizon, "n": len(zs),
            "q_means_pct": [round(m * 100, 3) for m in means],
            "q5_q1_spread_pct": round(spread * 100, 3),
            "beta": round(b, 5), "t": round(t, 2)}


def main():
    t0 = __import__("time").time()
    ff = parse_ff(os.path.join(FF_DIR, "F-F_Research_Data_Factors_daily.csv"))
    mom = parse_ff(os.path.join(FF_DIR, "F-F_Momentum_Factor_daily.csv"))
    print(f"FF file: {len(ff)} obs ({ff[0][0]} .. {ff[-1][0]}); "
          f"MOM file: {len(mom)} obs ({mom[0][0]} .. {mom[-1][0]})",
          file=sys.stderr)
    factors = {
        "Mkt-RF": [r[0] / 100.0 for _, r in ff],
        "SMB": [r[1] / 100.0 for _, r in ff],
        "HML": [r[2] / 100.0 for _, r in ff],
        "MOM": [r[0] / 100.0 for _, r in mom],
    }
    grid = [(5, 5), (5, 20), (20, 20), (60, 20), (120, 60), (250, 60),
            (250, 120)]
    out = {"factors": {}, "v5_mkt": {}}
    for name, s in factors.items():
        out["factors"][name] = []
        print(f"\n== {name} ({len(s)} obs) ==")
        print(f"  {'L':>4} {'H':>4} {'n':>7}  Q1..Q5 (pct)  "
              f"Q5-Q1   t(reg)")
        for L, H in grid:
            r = predict_test(s, L, H)
            if not r:
                continue
            out["factors"][name].append(r)
            print(f"  {L:>4} {H:>4} {r['n']:>7}  "
                  f"{' '.join(f'{m:7.2f}' for m in r['q_means_pct'])}  "
                  f"{r['q5_q1_spread_pct']:+7.2f}  {r['t']:+6.2f}")

    # v5-engine sim on Mkt-RF full century, real vs rotated
    print("\n== v5 engine on Mkt-RF (L=60, H=60, z=2.0, full century) ==")
    import pairs_engine_v5 as v5
    mkt = factors["Mkt-RF"]
    trs = v5.replay_mr(mkt, 60, 2.0, 2.0, 60)
    rets = [t["sigma_net"] for t in trs]
    if rets:
        mu = statistics.fmean(rets)
        sd = statistics.pstdev(rets) if len(rets) > 1 else 0.0
        t = mu / (sd / math.sqrt(len(rets))) if sd > 0 else 0.0
        out["v5_mkt"]["real"] = {"n": len(rets), "mean_sigma": round(mu, 4),
                                 "t": round(t, 2)}
        print(f"  REAL: {len(rets)} trades, per-trade {mu:+.4f} sigma, "
              f"t={t:+.2f}")
    rng = random.Random(11)
    rot = rng.randrange(1000, len(mkt) - 1000)
    mkt_r = mkt[rot:] + mkt[:rot]
    trs_r = v5.replay_mr(mkt_r, 60, 2.0, 2.0, 60)
    rets_r = [t["sigma_net"] for t in trs_r]
    if rets_r:
        mu_r = statistics.fmean(rets_r)
        sd_r = statistics.pstdev(rets_r) if len(rets_r) > 1 else 0.0
        t_r = mu_r / (sd_r / math.sqrt(len(rets_r))) if sd_r > 0 else 0.0
        out["v5_mkt"]["rotated"] = {"n": len(rets_r),
                                    "mean_sigma": round(mu_r, 4),
                                    "t": round(t_r, 2)}
        print(f"  ROTATED: {len(rets_r)} trades, per-trade {mu_r:+.4f} sigma, "
              f"t={t_r:+.2f}")

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(f"\nWrote {OUT} in {__import__('time').time()-t0:.0f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
