"""pairs_diversify.py -- correlation clustering + sector-capped portfolios.

The walk-forward-qualified list (15 pairs) is dominated by the semiconductor
complex (9/15).  This script quantifies how many INDEPENDENT bets that list
really is:

1. Replays each qualified pair (z=2.0, open in OOS only) and builds daily
   sigma-spread-return series over the OOS window.
2. Clusters pairs by Pearson correlation of those spread returns
   (single-link, rho >= CLUSTER_RHO).
3. Rebuilds the portfolio keeping at most MAX_PER_CLUSTER pairs per cluster
   (greedy by OOS net sigma P&L) and reports OOS Sharpe for each cap.

Usage:
    python3 pairs_diversify.py [--z 2.0] [--cost-bps 3.8] [--rho 0.5]
"""
from __future__ import annotations
import os, sys, json, math, statistics, time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import pairs_portfolio_sim as ps

CLUSTER_RHO = 0.50
REPORT_JSON = os.path.join(_HERE, "reports", "pairs_diversify.json")
REPORT_MD = os.path.join(_HERE, "reports", "pairs_diversify.md")

# coarse ticker->sector map for labeling only (labels are not used to cap)
_SECTOR = {
    "SO": "UTIL", "DUK": "UTIL",
    "AAPL": "TECH", "META": "TECH", "CRM": "TECH", "ORCL": "TECH",
    "NOW": "TECH", "INTC": "SEMI", "MU": "SEMI", "AMAT": "SEMI",
    "ARM": "SEMI", "TXN": "SEMI", "QCOM": "SEMI",
    "JNJ": "PHARMA", "ABBV": "PHARMA",
    "BA": "AERO", "RTX": "AERO",
}
def sector_of(pair):
    a, b = pair.split("/")
    return (_SECTOR.get(a, "?") + "/" + _SECTOR.get(b, "?"))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=float, default=2.0)
    ap.add_argument("--cost-bps", type=float, default=3.8)
    ap.add_argument("--rho", type=float, default=CLUSTER_RHO)
    ap.add_argument("--max-per-cluster", default="1,2,3,99")
    args = ap.parse_args()
    caps = [int(x) for x in args.max_per_cluster.split(",")]

    t0 = time.time()
    all_data, oos_date, qualified = ps.wf_qualified_pairs()
    print(f"WF-qualified: {len(qualified)} pairs in {time.time()-t0:.1f}s",
          file=sys.stderr)

    # replay each qualified pair, OOS window only
    cal = sorted({d for pr in (all_data[l] for l in qualified)
                  for d in pr["dates"]})
    oos_i0 = next((i for i, d in enumerate(cal) if d >= oos_date), len(cal))
    oos_cal = cal[oos_i0:]
    cidx = {d: i for i, d in enumerate(cal)}
    n_oos = len(oos_cal)

    series = {}   # label -> daily sigma spread-return over OOS window
    trades = {}   # label -> replay trade list
    for l in qualified:
        pr = all_data[l]
        open_from = next((i for i, d in enumerate(pr["dates"]) if d >= oos_date),
                         len(pr["dates"]))
        trs, lb, hz = ps.replay_pair(pr, args.z, open_from,
                                     lookback=pr.get("lookback"),
                                     horizon=pr.get("horizon"))
        trades[l] = trs
        spread = pr["spread"]
        lbk = pr.get("lookback") or 60
        s = [0.0] * len(cal)
        for i in range(max(lbk, 1), len(spread)):
            m, sd = ps._roll(i, lbk, spread)
            if sd <= 0:
                continue
            ci = cidx.get(pr["dates"][i])
            if ci is not None and ci >= oos_i0:
                s[ci] = (spread[i] - spread[i - 1]) / sd
        series[l] = s

    # Pearson correlation + single-link clustering
    labels = qualified
    n = len(labels)
    def pearson(x, y):
        px = [x[i] for i in range(len(cal)) if i >= oos_i0]
        py = [y[i] for i in range(len(cal)) if i >= oos_i0]
        both = [(a, b) for a, b in zip(px, py)
                if math.isfinite(a) and math.isfinite(b) and a != 0 and b != 0]
        if len(both) < 30:
            return 0.0
        ax = [a for a, _ in both]; ay = [b for _, b in both]
        mx = statistics.fmean(ax); my = statistics.fmean(ay)
        cov = sum((ax[i] - mx) * (ay[i] - my) for i in range(len(ax)))
        sx = math.sqrt(sum((a - mx) ** 2 for a in ax))
        sy = math.sqrt(sum((b - my) ** 2 for b in ay))
        if sx <= 0 or sy <= 0:
            return 0.0
        return cov / (sx * sy)

    corr = [[pearson(series[a], series[b]) for b in labels] for a in labels]

    # single-link clustering (union by threshold)
    clusters = []
    for i, l in enumerate(labels):
        joined = None
        for cl in clusters:
            if any(corr[i][labels.index(m)] >= args.rho for m in cl):
                joined = cl
                break
        if joined is None:
            clusters.append([l])
        else:
            joined.append(l)
    clusters.sort(key=lambda c: -len(c))
    cluster_of = {}
    for ci, cl in enumerate(clusters):
        for l in cl:
            cluster_of[l] = ci

    # per-pair OOS net sigma (z=2.0, 3.8bps)
    net_sigma = {}
    for l in qualified:
        ns = 0.0
        for t in trades[l]:
            esd = t["entry_sd"]
            c = 2.0 * (args.cost_bps / 1e4) / esd if esd > 0 else 0.0
            ns += t["sigma_net"] - c
        net_sigma[l] = ns

    def build(keep):
        recs = []
        for l in keep:
            pr = all_data[l]
            open_from = next((i for i, d in enumerate(pr["dates"])
                              if d >= oos_date), len(pr["dates"]))
            trs, _, _ = ps.replay_pair(pr, args.z, open_from,
                                       lookback=pr.get("lookback"),
                                       horizon=pr.get("horizon"))
            if trs:
                recs.append({**pr, "dates": pr["dates"], "trades": trs})
        agg = ps._aggregate(recs, args.cost_bps)
        if agg is None:
            return None, None
        m_net = ps.metrics(agg["net"], agg["n_days"], oos_date, agg["cal"])
        m_gr = ps.metrics(agg["gross"], agg["n_days"], oos_date, agg["cal"])
        return m_net, m_gr

    out = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
           "z_entry": args.z, "cost_bps": args.cost_bps, "rho": args.rho,
           "qualified": qualified, "clusters": clusters,
           "net_sigma": net_sigma, "runs": []}
    print(f"\nClusters (rho>={args.rho}) -- {len(clusters)} independent bets:")
    for ci, cl in enumerate(clusters):
        tot = sum(net_sigma[l] for l in cl)
        print(f"  C{ci} [{tot:+.1f} sigma total] " + ", ".join(
            f"{l}({net_sigma[l]:+.1f},{sector_of(l)})" for l in cl))

    print("\nPortfolio variants (OOS, net of "
          f"{args.cost_bps}bps):")
    for cap in caps:
        keep = []
        for cl in clusters:
            keep += sorted(cl, key=lambda l: -net_sigma[l])[:cap]
        m, mg = build(keep)
        if not m or not m["OOS"]:
            continue
        o = m["OOS"]
        g = mg["OOS"] if mg else None
        gs = f"gross {g['sharpe']:5.2f}" if g else ""
        print(f"  cap={cap:2d} pairs={len(keep):2d}  "
              f"Sharpe={o['sharpe']:6.2f}  "
              f"Sortino={o['sortino'] if o['sortino'] else float('nan'):6.2f}  "
              f"maxDD={o['max_dd']*100:5.1f}%  CAGR@10%vol={o['cagr10']*100:6.1f}%  "
              f"({gs})")
        out["runs"].append({"cap": cap, "pairs": sorted(keep),
                            "oos_sharpe": o["sharpe"],
                            "oos_sortino": o["sortino"],
                            "oos_maxdd": o["max_dd"],
                            "oos_cagr10": o["cagr10"]})

    with open(REPORT_JSON, "w") as f:
        json.dump(out, f, indent=1, default=str)
    with open(REPORT_MD, "w") as f:
        f.write("# Pair Portfolio Diversification\n\n")
        f.write(f"Generated: {out['generated']}  |  z={args.z}  "
                f"cost={args.cost_bps}bps  rho>={args.rho}\n\n")
        f.write(f"**{len(qualified)} WF-qualified pairs collapse into "
                f"{len(clusters)} correlation clusters.**\n\n")
        for ci, cl in enumerate(clusters):
            f.write(f"### C{ci} ({sum(net_sigma[l] for l in cl):+.1f} sigma OOS)\n")
            for l in sorted(cl, key=lambda l: -net_sigma[l]):
                f.write(f"- {l} ({sector_of(l)})  net {net_sigma[l]:+.2f} sigma\n")
            f.write("\n")
        f.write("| max per cluster | pairs | OOS Sharpe | Sortino | maxDD | CAGR@10%vol |\n")
        f.write("|-----------------|-------|-----------|---------|-------|-------------|\n")
        for r in out["runs"]:
            so = f"{r['oos_sortino']:6.2f}" if r["oos_sortino"] else "    n/a"
            f.write(f"| {r['cap']} | {len(r['pairs'])} | "
                    f"{r['oos_sharpe']:6.2f} | {so} | "
                    f"{r['oos_maxdd']*100:5.1f}% | {r['oos_cagr10']*100:6.1f}% |\n")
    print(f"\nWrote {REPORT_JSON} and {REPORT_MD}", file=sys.stderr)


if __name__ == "__main__":
    main()
