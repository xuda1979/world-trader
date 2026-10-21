"""pairs_factor_portfolio.py -- tradeable factor-momentum portfolio.

Century-validated signals (pairs_ff_test): SMB/HML/MOM factor momentum at
5-60d lookbacks.  This script converts the SIGNAL into a STRATEGY:

  - signal: trailing L-day cumulative factor return, z-normalized by the
    window sd (validated in pairs_ff_test)
  - exposure: +1 (long factor) when z > 0, -1 when z < 0 (sign rule);
    variant with dead-band (|z| < z_db -> flat)
  - rebalance every `rebal` days (weekly default) to cut turnover
  - cost: bps per leg per exposure change (2 legs per factor spread)
  - strategy day return = exposure_t * factor_{t+1} - costs

Output: per-factor Sharpe/CAGR/maxDD/turnover at cost 0/1/3.8 bps,
decade breakdown, 3-factor equal-risk portfolio, and the STRATEGY-LEVEL
shuffle control (shuffled factor returns must give Sharpe ~ 0).
"""
from __future__ import annotations
import os, sys, math, statistics, random, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pairs_ff_test import parse_ff

_HERE = os.path.dirname(os.path.abspath(__file__))
FF_DIR = os.path.join(_HERE, "data", "ff_factors")
OUT = os.path.join(_HERE, "reports", "pairs_factor_portfolio.json")


def load_factors():
    ff = parse_ff(os.path.join(FF_DIR, "F-F_Research_Data_Factors_daily.csv"))
    mom = parse_ff(os.path.join(FF_DIR, "F-F_Momentum_Factor_daily.csv"))
    return {"Mkt-RF": [r[0] / 100.0 for _, r in ff],
            "SMB": [r[1] / 100.0 for _, r in ff],
            "HML": [r[2] / 100.0 for _, r in ff],
            "MOM": [r[0] / 100.0 for _, r in mom]}


def run_strategy(series, lookback, rebal, cost_bps, z_db=0.0,
                 max_hold=None):
    """Sign-rule factor momentum.  Returns (daily returns, stats)."""
    n = len(series)
    rets = [0.0] * n
    expo = 0.0
    rebs = 0
    for i in range(lookback, n - 1):
        if i % rebal == 0:
            w = series[i - lookback:i]
            sd = statistics.pstdev(w) if len(w) > 1 else 0.0
            if sd <= 0:
                new_exp = 0.0
            else:
                z = sum(w) / math.sqrt(lookback) / sd
                if z > z_db:
                    new_exp = 1.0
                elif z < -z_db:
                    new_exp = -1.0
                else:
                    new_exp = 0.0
            if new_exp != expo:
                rets[i] -= cost_bps / 1e4 * 2.0 * abs(new_exp - expo)
                expo = new_exp
                rebs += 1
        rets[i + 1] += expo * series[i + 1]
    return rets, rebs


def metrics(rets, cost_bps):
    n = len(rets)
    mu = statistics.fmean(rets)
    sd = statistics.pstdev(rets) if n > 1 else 0.0
    sharpe = mu / sd * math.sqrt(252) if sd > 0 else 0.0
    eq = 0.0; peak = 0.0; mdd = 0.0
    for r in rets:
        eq += r
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)
    cagr = (1.0 + mu) ** 252 - 1.0
    return {"sharpe": round(sharpe, 2), "cagr_pct": round(cagr * 100, 2),
            "maxdd_pct": round(mdd * 100, 1), "mean_bps_d": round(mu * 1e4, 2),
            "vol_d": round(sd * 100, 2), "n_days": n}


def main():
    t0 = __import__("time").time()
    F = load_factors()
    print(f"factors loaded: { {k: len(v) for k, v in F.items()} }",
          file=sys.stderr)
    out = {"cost_sweep": {}, "decades": {}, "portfolio": {}, "control": {}}

    print("== per-factor strategy (sign rule, weekly rebalance) ==")
    print(f"{'factor':6s} {'L':>3s} {'cost':>5s}  Sharpe  CAGR%  maxDD%  "
          f"bps/d  rebs/yr")
    best = {}
    for name in ("SMB", "HML", "MOM"):
        best[name] = None
        for L in (5, 20, 60):
            for cb in (0.0, 1.0, 3.8):
                rets, rebs = run_strategy(F[name], L, 5, cb)
                m = metrics(rets, cb)
                yrs = len(rets) / 252
                tag = f"{name}-L{L}"
                out["cost_sweep"].setdefault(tag, {})[cb] = m
                if cb == 0.0 and (best[name] is None or
                                  m["sharpe"] > best[name][1]["sharpe"]):
                    best[name] = (L, m)
                if cb in (0.0, 3.8) and L in (5, 20):
                    print(f"{name:6s} {L:3d} {cb:5.1f}  {m['sharpe']:6.2f} "
                          f"{m['cagr_pct']:6.2f} {m['maxdd_pct']:6.1f} "
                          f"{m['mean_bps_d']:6.2f} {rebs/yrs:5.1f}")
    print(f"\nbest (cost 0): { {k: v[0] for k, v in best.items()} }")

    # ---- 3-factor equal-risk portfolio (each factor's best L, sign rule)
    print("\n== 3-factor portfolio (best L per factor, weekly, 3.8 bps) ==")
    nmin = min(len(v) for v in F.values())
    TGT_VOL = 0.10 / math.sqrt(252)   # scale each factor to 10% ann vol

    def build_port(series_map, z_db=0.0, cost=3.8, long_series=None):
        port = [0.0] * nmin
        for name, (L, _) in best.items():
            r, _ = run_strategy(series_map[name][-nmin:], L, 5, cost,
                                z_db=z_db)
            sd = statistics.pstdev(r) if len(r) > 1 else 1.0
            if sd > 0:
                for i in range(nmin):
                    port[i] += r[i] / sd * TGT_VOL
        if long_series is not None:
            r, _ = run_strategy(long_series[-nmin:], 250, 63, cost)
            sd = statistics.pstdev(r) if len(r) > 1 else 1.0
            if sd > 0:
                for i in range(nmin):
                    port[i] += r[i] / sd * TGT_VOL
        return port

    port = build_port(F)
    mp = metrics(port, 0.0)   # costs already inside the legs
    out["portfolio"] = mp
    print(f"  equal-risk 3-factor: Sharpe={mp['sharpe']}  "
          f"CAGR={mp['cagr_pct']}%  maxDD={mp['maxdd_pct']}%  "
          f"bps/d={mp['mean_bps_d']}")

    # ---- improved variants on the 3-factor book
    print("\n== improved variants (3-factor, 3.8 bps) ==")
    for z_db, vt, lh in ((1.0, False, False), (0.5, True, False),
                         (0.0, False, True)):
        port2 = build_port(F, z_db=z_db,
                           long_series=F["Mkt-RF"] if lh else None)
        m2 = metrics(port2, 0.0)
        out.setdefault("variants", {})[f"zdb={z_db} vt={int(vt)} lh={int(lh)}"] = m2
        print(f"  z_db={z_db} vol-target={int(vt)} +LH={int(lh)}: "
              f"Sharpe={m2['sharpe']}  CAGR={m2['cagr_pct']}%  "
              f"maxDD={m2['maxdd_pct']}%")

    # ---- decade breakdown (SMB L=20 + HML L=20 + MOM L=5, cost 3.8)
    print("\n== decade breakdown (3-factor, 3.8 bps) ==")
    starts = [("1930s", 1929, 1940), ("1940s", 1940, 1950), ("1950s", 1950, 1960),
              ("1960s", 1960, 1970), ("1970s", 1970, 1980), ("1980s", 1980, 1990),
              ("1990s", 1990, 2000), ("2000s", 2000, 2010), ("2010s", 2010, 2020),
              ("2020s", 2020, 2030)]
    ff_dates = [d for d, _ in parse_ff(
        os.path.join(FF_DIR, "F-F_Research_Data_Factors_daily.csv"))]
    ff_dates = ff_dates[-nmin:]     # align with the truncated series
    yr_of = {d: int(d[:4]) for d in ff_dates}
    legs = [(F["SMB"], 20), (F["HML"], 20), (F["MOM"], 5)]
    for dec, y0, y1 in starts:
        seg = [0.0] * nmin
        for ser, L in legs:
            r, _ = run_strategy(ser[-nmin:], L, 5, 3.8)
            sd = statistics.pstdev(r) if len(r) > 1 else 1.0
            if sd > 0:
                for i in range(nmin):
                    seg[i] += r[i] / sd * TGT_VOL
        idx = [i for i, d in enumerate(ff_dates) if y0 <= yr_of[d] < y1]
        if len(idx) < 100:
            continue
        sub = [seg[i] for i in idx]
        m = metrics(sub, 0.0)
        out["decades"][dec] = m
        print(f"  {dec}: Sharpe={m['sharpe']:6.2f}  CAGR={m['cagr_pct']:7.2f}%  "
              f"maxDD={m['maxdd_pct']:6.1f}%")

    # ---- strategy-level shuffle control (3-factor, 3.8 bps)
    print("\n== strategy-level shuffle control (3-factor) ==")
    ctrl = []
    for seed in (41, 42, 43, 44, 45):
        rng = random.Random(seed)
        p2 = [0.0] * len(port)
        for ser, L in legs:
            sh = ser[:]
            rng.shuffle(sh)
            r, _ = run_strategy(sh, L, 5, 3.8)
            sd = statistics.pstdev(r) if len(r) > 1 else 1.0
            for i in range(len(p2)):
                p2[i] += r[i] / sd
        ctrl.append(metrics(p2, 0.0)["sharpe"])
    out["control"] = {"shuffled_sharpes": ctrl,
                      "real_sharpe": mp["sharpe"],
                      "z_vs_control": round((mp["sharpe"] -
                                             statistics.fmean(ctrl)) /
                                            statistics.pstdev(ctrl), 2)}
    print(f"  shuffled Sharpes: {['%.2f' % s for s in ctrl]}")
    print(f"  real {mp['sharpe']} vs control mean "
          f"{statistics.fmean(ctrl):+.2f} "
          f"(z={out['control']['z_vs_control']:+.2f})")

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(f"\nWrote {OUT} in {__import__('time').time()-t0:.0f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
