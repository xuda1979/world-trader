"""pairs_momentum_map.py -- characterize the 40d tech-sector momentum lead.

Checks that decide whether the candidate deserves a data investment:

  A. Per-sector momentum map (40/20, k2, net): which sectors carry it?
  B. Tech robustness grid: formation x hold x k -> net Sharpe plateau or spike?
  C. Market beta: regress the tech book's daily returns on SPY.  Is the
     "momentum" really tech beta in disguise?
  D. Up/down market split: Sharpe in SPY-up vs SPY-down regimes (momentum
     crash check).
  E. Name-level contributions: which tech names are the longs/shorts, and
     who carries the P&L.
  F. Block bootstrap (63-day) CI on the tech book's net Sharpe.
"""
from __future__ import annotations
import os, sys, csv, math, statistics, random, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pairs_crosssec as pc

OUT = os.path.join(pc._HERE, "reports", "pairs_momentum_map.json")
COST = 3.8


def load_spy():
    p = os.path.join(pc._HERE, "data", "polygon", "SPY.csv")
    dates, closes = [], []
    with open(p) as f:
        for r in csv.DictReader(f):
            try:
                closes.append(float(r["close"]))
                dates.append(r["date"])
            except (ValueError, KeyError):
                continue
    return dict(zip(dates, closes))


def tech_book(cal, m, secs, form, hold, k, momentum=True):
    rn, g = pc.run_book(cal, m, secs, form, hold, top_k=k, scramble=False,
                        cost_bps=COST, momentum=momentum)
    return rn, g


def main():
    t0 = __import__("time").time()
    secs = {k: v for k, v in pc.v4.SECTORS.items() if k != "ETFs"}
    cal, m, _ = pc.build_matrix(secs)
    spy = load_spy()
    spy_ret = {}
    spy_keys = sorted(spy)
    for i in range(1, len(spy_keys)):
        spy_ret[spy_keys[i]] = spy[spy_keys[i]] / spy[spy_keys[i - 1]] - 1.0

    out = {"cost_bps": COST, "A": [], "B": [], "C": {}, "D": {},
           "E": [], "F": {}}

    # ---- A. per-sector momentum map
    print("== A. per-sector momentum (40/20, k2, net Sharpe) ==")
    for name, syms in sorted(secs.items()):
        sub = {name: syms}
        rn, _ = tech_book(cal, m, sub, 40, 20, 2)
        mm = pc.metrics(rn)
        if mm.get("mean_bps") is None:
            print(f"  {name:18s} no trades (missing data)")
            continue
        out["A"].append({"sector": name, "net_sharpe": round(mm["sharpe"], 2),
                         "bps_d": round(mm["mean_bps"], 2)})
        print(f"  {name:18s} net={mm['sharpe']:+.2f} ({mm['mean_bps']:+.2f} bps/d)")

    # ---- B. tech robustness grid
    print("\n== B. tech momentum robustness grid (net Sharpe) ==")
    tech = {"Technology": secs["Technology"]}
    grid = []
    for form in (20, 30, 40, 50, 60):
        row = []
        for hold in (10, 20, 30):
            for k in (1, 2, 3):
                rn, _ = tech_book(cal, m, tech, form, hold, k)
                s = pc.metrics(rn)["sharpe"]
                grid.append({"form": form, "hold": hold, "k": k,
                             "net_sharpe": round(s, 2)})
                row.append(s)
        print(f"  form={form:2d}: hold 10/20/30 x k1..3 -> "
              f"{' '.join(f'{x:+.1f}' for x in row)}")
    out["B"] = grid

    # ---- C. market beta (base cell)
    print("\n== C. market beta of tech book ==")
    rn, _ = tech_book(cal, m, tech, 40, 20, 2)
    xy, xx, n_ = [], [], 0
    for i, dt in enumerate(cal):
        if dt in spy_ret:
            xy.append(rn[i] * spy_ret[dt])
            xx.append(spy_ret[dt] * spy_ret[dt])
            n_ += 1
    beta = sum(xy) / sum(xx) if sum(xx) > 0 else 0.0
    alpha_d = statistics.fmean(rn) - beta * statistics.fmean(
        [spy_ret[d] for d in cal if d in spy_ret])
    out["C"] = {"beta": round(beta, 3), "alpha_bps_d": round(alpha_d * 1e4, 2)}
    print(f"  beta vs SPY = {beta:+.3f}   alpha = {alpha_d*1e4:+.2f} bps/d")

    # ---- D. up/down market split
    print("\n== D. up/down market split (SPY 20d return sign) ==")
    spy_20 = {}
    sk = sorted(spy)
    for i in range(20, len(sk)):
        spy_20[sk[i]] = spy[sk[i]] / spy[sk[i - 20]] - 1.0
    up, dn = [], []
    for i, dt in enumerate(cal):
        if dt in spy_20:
            (up if spy_20[dt] >= 0 else dn).append(rn[i])
    mu_up = pc.metrics(up); mu_dn = pc.metrics(dn)
    out["D"] = {"up": mu_up, "down": mu_dn,
                "n_up": len(up), "n_down": len(dn)}
    print(f"  SPY up   ({len(up)} d): net Sharpe {mu_up['sharpe']:+.2f} "
          f"({mu_up['mean_bps']:+.2f} bps/d)")
    print(f"  SPY down ({len(dn)} d): net Sharpe {mu_dn['sharpe']:+.2f} "
          f"({mu_dn['mean_bps']:+.2f} bps/d)")

    # ---- E. name-level contributions
    print("\n== E. name-level contributions (tech, 40/20 k2) ==")
    contrib = {}
    exposure = {}
    for i, dt in enumerate(cal):
        if i < 40:
            continue
        r = {s: m[dt][s] / m[cal[i - 40]][s] - 1.0 for s in tech["Technology"]
             if s in m[dt] and s in m[cal[i - 40]]}
        syms = list(r)
        vals = [r[s] for s in syms]
        ranked = sorted(range(len(syms)), key=lambda j: vals[j])
        pos = {}
        for j in ranked[-2:]:
            pos[syms[j]] = +1
        for j in ranked[:2]:
            pos[syms[j]] = -1
        for s, side in pos.items():
            exposure.setdefault(s, [0, 0])[0 if side > 0 else 1] += 1
            # daily return of this leg (hold 20 overlap handled approx)
            nxt = cal[i + 1] if i + 1 < len(cal) else cal[i]
            ret_leg = m[nxt][s] / m[dt][s] - 1.0 if s in m[nxt] else 0.0
            contrib[s] = contrib.get(s, 0.0) + side * ret_leg
    for s in sorted(contrib, key=lambda s: -abs(contrib[s])):
        out["E"].append({"name": s, "contrib_bps": round(contrib[s] * 1e4, 1),
                         "n_long": exposure[s][0], "n_short": exposure[s][1]})
        print(f"  {s:6s} contrib {contrib[s]*1e4:+8.1f} bps  "
              f"(long {exposure[s][0]}d / short {exposure[s][1]}d)")

    # ---- F. block bootstrap CI on net Sharpe
    print("\n== F. block bootstrap (63d blocks, 2000 reps) ==")
    rng = random.Random(7)
    block = 63
    n = len(rn)
    nb = n // block
    boot = []
    for _ in range(2000):
        seg = []
        for _ in range(nb):
            b = rng.randrange(0, n - block)
            seg.extend(rn[b:b + block])
        boot.append(pc.metrics(seg)["sharpe"])
    boot.sort()
    lo, hi = boot[50], boot[-50]
    out["F"] = {"p5": round(lo, 2), "median": round(boot[1000], 2),
                "p95": round(hi, 2)}
    print(f"  net Sharpe CI: p5 {lo:+.2f}  median {boot[1000]:+.2f}  "
          f"p95 {hi:+.2f}")

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(f"\nWrote {OUT} in {__import__('time').time()-t0:.0f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
