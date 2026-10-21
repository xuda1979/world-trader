"""pairs_crosssec.py -- cross-sectional same-sector reversal book.

The last untested signal family: cross-sectional reversal ("pairs trading at
scale").  Within each sector, every day, long the recent LOSERS and short the
recent WINNERS of the formation return (cross-sectional z), hold H days with
overlap, sector-neutral weights.  This is the Lo-MacKinlay / Lehmann-style
anomaly -- the most documented relative-value effect in equities.

Falsification-first: the SAME book is run on scrambled data (per-day
permutation of formation returns within each sector), which destroys the
cross-sectional signal while keeping marginals, calendar and trade counts.
Only real-minus-scrambled > 0 is evidence.

Cost: 3.8 bps per leg per side (entry + exit) = 7.6 bps per leg-trade,
charged on the day the position opens/closes.
"""
from __future__ import annotations
import os, sys, csv, math, statistics, random, json

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import pairs_research_v4 as v4

COST_BPS = 3.8            # per leg, per side
SIDES = 2                 # entry + exit
REPORT_JSON = os.path.join(_HERE, "reports", "pairs_crosssec.json")
REPORT_MD = os.path.join(_HERE, "reports", "pairs_crosssec.md")
MIN_SECTOR = 4            # sectors with >= this many members trade


def load(sym):
    p = os.path.join(_HERE, "data", "polygon", f"{sym}.csv")
    if not os.path.exists(p):
        return None
    dates, closes = [], []
    with open(p, newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            try:
                closes.append(float(r["close"]))
                dates.append(r["date"])
            except (ValueError, KeyError):
                continue
    if len(closes) < 300:
        return None
    return dates, closes


def build_matrix(sectors):
    """Common-calendar close matrix: {date: {sym: close}}."""
    syms = []
    for sec in sectors.values():
        for s in sec:
            if s not in syms:
                syms.append(s)
    data = {}
    for s in syms:
        d = load(s)
        if d:
            data[s] = d
    cal = sorted(set.intersection(*[set(d[0]) for d in data.values()]))
    m = {dt: {s: dict(zip(data[s][0], data[s][1]))[dt] for s in data}
         for dt in cal}
    return cal, m, data


def run_book(cal, m, sectors, formation, hold, top_k=2, scramble=False,
             rng=None, cost_bps=COST_BPS, weekly=False, z_thresh=0.0,
             vol_scale=False, momentum=False):
    """Overlapping cross-sectional book.  Returns (net, gross) daily series.
    Gross is the falsification comparison (costs cancel in
    real-minus-scrambled).  weekly: enter every 5th day (cuts turnover).
    z_thresh: only trade |z| above threshold.  vol_scale: rank by
    formation return / own 20d vol (vol-managed reversal).  momentum:
    long WINNERS / short losers (form/hold define the momentum window)."""
    rng2 = rng if scramble else random.Random(1)
    n = len(cal)
    w_daily = {}
    for i, dt in enumerate(cal):
        if i < formation:
            continue
        r = {}   # sym -> formation return
        for s in m[dt]:
            p0 = m[cal[i - formation]][s]
            p1 = m[dt][s]
            r[s] = p1 / p0 - 1.0
        if vol_scale:
            # r / own 20d daily-return vol
            for s in m[dt]:
                v = []
                for k in range(max(1, i - 20), i):
                    v.append(m[cal[k]][s] / m[cal[k - 1]][s] - 1.0)
                sd = statistics.pstdev(v) if len(v) > 2 else 0.0
                if sd > 0:
                    r[s] = r[s] / sd
        sec_syms = {sec: [s for s in syms if s in r] for sec, syms in sectors.items()}
        sec_syms = {k: v for k, v in sec_syms.items() if len(v) >= MIN_SECTOR}
        if weekly and i % 5 != 0:
            w_daily[dt] = ([], i)
            continue
        entries = []   # (sym, side) side=+1 long, -1 short
        for sec, syms in sec_syms.items():
            vals = [r[s] for s in syms]
            if scramble:
                rng.shuffle(vals)
            mu = statistics.fmean(vals)
            sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
            zs = [(vals[j] - mu) / sd if sd > 0 else 0.0 for j in range(len(vals))]
            ranked = sorted(range(len(syms)), key=lambda j: vals[j])
            if momentum:
                # momentum: long winners, short losers
                for j in ranked[-top_k:]:
                    if zs[j] >= z_thresh:
                        entries.append((syms[j], +1))
                for j in ranked[:top_k]:
                    if zs[j] <= -z_thresh:
                        entries.append((syms[j], -1))
            else:
                for j in ranked[:top_k]:
                    if zs[j] <= -z_thresh:
                        entries.append((syms[j], +1))   # losers -> long
                for j in ranked[-top_k:]:
                    if zs[j] >= z_thresh:
                        entries.append((syms[j], -1))   # winners -> short
        w_daily[dt] = (entries, i)
    # simulate with overlap
    n_sec = sum(1 for v in sectors.values() if len(v) >= MIN_SECTOR)
    w_leg = 1.0 / (n_sec * 2.0 * top_k) if n_sec else 0.0
    open_pos = []   # (close_day_index, sym, side)
    daily_net = []
    daily_gross = []
    for dt in cal:
        i = cal.index(dt)
        if dt not in w_daily:
            daily_net.append(0.0)
            daily_gross.append(0.0)
            continue
        entries, ei = w_daily[dt]
        gross = 0.0
        cost = 0.0
        # P&L of open positions (close i-1 -> close i); drop finished ones
        # and charge their exit cost
        still = []
        for (ci, s, side) in open_pos:
            gross += w_leg * side * (m[dt][s] / m[cal[ci]][s] - 1.0)
            if i - ci < hold:
                still.append((ci, s, side))
            else:
                cost += w_leg * (cost_bps / 1e4) * SIDES   # exit cost
        open_pos = still
        # open new positions at close i (entry cost)
        for s, side in entries:
            open_pos.append((i, s, side))
            cost += w_leg * (cost_bps / 1e4) * SIDES
        daily_net.append(gross - cost)
        daily_gross.append(gross)
    return daily_net, daily_gross


def metrics(daily):
    mu = statistics.fmean(daily)
    sd = statistics.pstdev(daily) if len(daily) > 1 else 0.0
    if sd <= 0:
        return {"sharpe": 0.0, "sortino": None, "maxdd": 0.0, "mean": mu}
    sharpe = mu / sd * math.sqrt(252) if mu > 0 else mu / sd * math.sqrt(252)
    neg = [r for r in daily if r < 0]
    dsd = statistics.pstdev(neg) if len(neg) > 1 else 0.0
    sortino = mu / dsd * math.sqrt(252) if dsd > 0 else None
    eq = 0.0; peak = 0.0; mdd = 0.0
    for r in daily:
        eq += r; peak = max(peak, eq); mdd = min(mdd, eq - peak)
    return {"sharpe": sharpe, "sortino": sortino, "maxdd": mdd,
            "mean_bps": mu * 1e4}


def main():
    rng = random.Random(2026)
    sectors = {k: v for k, v in v4.SECTORS.items() if k != "ETFs"}
    cal, m, data = build_matrix(sectors)
    print(f"Common calendar: {len(cal)} days; symbols loaded: {len(data)}",
          file=sys.stderr)
    print(f"Sectors with >= {MIN_SECTOR} members: "
          f"{[k for k, v in sectors.items() if len(v) >= MIN_SECTOR]}",
          file=sys.stderr)

    out = {"generated": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
           "cost_bps": COST_BPS, "runs": []}
    rows = []
    N_SEEDS = 8
    # (name, kwargs); blend = 0.5 reversal + 0.5 momentum
    configs = [
        ("rev vol-managed 5/10", dict(formation=5, hold=10, top_k=2,
                                      z_thresh=0.0, vol_scale=True)),
        ("rev vol-managed wk 5/10", dict(formation=5, hold=10, top_k=1,
                                         z_thresh=1.0, vol_scale=True,
                                         weekly=True)),
        ("mom 20/20", dict(formation=20, hold=20, top_k=2, z_thresh=0.0,
                           momentum=True)),
        ("rev 5/10 + mom 20/20 blend", dict(blend=True)),
    ]
    for name, kw in configs:
        if kw.get("blend"):
            real_n1, real_g1 = run_book(cal, m, sectors, 5, 10, top_k=2,
                                        scramble=False)
            real_n2, real_g2 = run_book(cal, m, sectors, 20, 20, top_k=2,
                                        scramble=False, momentum=True)
            real_g = [(a + b) / 2 for a, b in zip(real_g1, real_g2)]
            real_n = [(a + b) / 2 for a, b in zip(real_n1, real_n2)]
            scram_grosses = []
            for s in range(N_SEEDS):
                _, sg1 = run_book(cal, m, sectors, 5, 10, top_k=2,
                                  scramble=True, rng=random.Random(2000 + s))
                _, sg2 = run_book(cal, m, sectors, 20, 20, top_k=2,
                                  scramble=True, momentum=True,
                                  rng=random.Random(3000 + s))
                sg = [(a + b) / 2 for a, b in zip(sg1, sg2)]
                scram_grosses.append(metrics(sg)["sharpe"])
        else:
            real_n, real_g = run_book(cal, m, sectors, scramble=False,
                                      cost_bps=COST_BPS, **kw)
            scram_grosses = []
            for s in range(N_SEEDS):
                _, sg = run_book(cal, m, sectors, scramble=True,
                                 rng=random.Random(1000 + s),
                                 cost_bps=COST_BPS, **kw)
                scram_grosses.append(metrics(sg)["sharpe"])
        mr, mgr = metrics(real_n), metrics(real_g)
        mu_s = statistics.fmean(scram_grosses)
        sd_s = statistics.pstdev(scram_grosses) if N_SEEDS > 1 else 0.0
        z_real = (mgr["sharpe"] - mu_s) / sd_s if sd_s > 0 else 0.0
        # t-stat of the daily gross mean (own-noise significance)
        t_daily = 0.0
        if mgr["sharpe"] > 0:
            sd_d = mgr["mean_bps"] / 1e4 / (mgr["sharpe"] / math.sqrt(252)) \
                if mgr["sharpe"] != 0 else 0.0
            t_daily = (mgr["mean_bps"] / 1e4) / sd_d * math.sqrt(len(real_g)) \
                if sd_d > 0 else 0.0
        rows.append((name, mr, mgr, mu_s, sd_s, z_real, t_daily))
        out["runs"].append({
            "name": name, "real_net": mr, "real_gross": mgr,
            "scrambled_gross_mean": round(mu_s, 2),
            "scrambled_gross_sd": round(sd_s, 2),
            "z_real_vs_scrambled": round(z_real, 2),
            "t_daily_mean": round(t_daily, 2)})
        print(f"{name:26s}  REAL net={mr['sharpe']:6.2f} "
              f"gross={mgr['sharpe']:6.2f} ({mgr['mean_bps']:+.2f} bps/d)  "
              f"SCRAM {mu_s:+.2f}+-{sd_s:.2f}  z={z_real:+.2f}  "
              f"t_mean={t_daily:+.2f}")

    with open(REPORT_JSON, "w") as f:
        json.dump(out, f, indent=1, default=str)
    with open(REPORT_MD, "w") as f:
        f.write("# Cross-Sectional Same-Sector Reversal Book\n\n")
        f.write(f"Generated: {out['generated']}  |  cost "
                f"{COST_BPS} bps/leg/side  |  long losers / short winners "
                f"within sector, overlapping hold\n\n")
        f.write("| variant | REAL net | REAL gross | REAL bps/d | "
                "SCRAM gross (mean+-sd, 8 seeds) | z(real vs scram) | "
                "t(daily mean) |\n")
        f.write("|---------|----------|------------|------------|"
                "-------------------------------|------------------|--------------|\n")
        for name, mr, mgr, mu_s, sd_s, zr, td in rows:
            f.write(f"| {name} | {mr['sharpe']:6.2f} | "
                    f"{mgr['sharpe']:6.2f} | {mgr['mean_bps']:+.2f} | "
                    f"{mu_s:+.2f} +- {sd_s:.2f} | {zr:+.2f} | {td:+.2f} |\n")
        f.write("\nFalsification: the honest comparison is on GROSS (costs "
                "cancel in real-minus-scrambled).  A positive deltaGross "
                "with the scrambled gross ~ 0 is the signal test.\n")
    print(f"\nWrote {REPORT_JSON} and {REPORT_MD}", file=sys.stderr)


if __name__ == "__main__":
    main()
