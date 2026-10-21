"""pairs_intraday.py -- engine-level test of 5-min intraday pair mean
reversion with the v5 (symmetric) engine, real vs scrambled.

Motivation: daily-bar pair mean reversion showed NO edge once the
rule-geometry artifact was removed (real ~= scrambled ~= 0).  Mean
reversion is primarily an intraday phenomenon, so test it on 5-min bars.
The 3.8 bps cost model is identical to the daily engine (4 x cost per
trade, normalized by realized spread vol) -- which is expected to be
brutal at intraday vol scales.
"""
from __future__ import annotations
import os, sys, csv, math, statistics, random, time, datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
for p in (_HERE, _ROOT, os.path.join(_ROOT, "tools")):
    sys.path.insert(0, p)

from wt import sources
import pairs_engine_v5 as v5

INTRA_DIR = os.path.join(_HERE, "data", "polygon_intraday")
PAIRS = [
    ("SO/DUK", "SO", "DUK"), ("AAPL/AMAT", "AAPL", "AMAT"),
    ("AAPL/ARM", "AAPL", "ARM"), ("META/INTC", "META", "INTC"),
    ("INTC/CRM", "INTC", "CRM"), ("INTC/ORCL", "INTC", "ORCL"),
    ("INTC/NOW", "INTC", "NOW"), ("INTC/MU", "INTC", "MU"),
    ("INTC/ARM", "INTC", "ARM"), ("ORCL/MU", "ORCL", "MU"),
    ("TXN/ARM", "TXN", "ARM"), ("QCOM/AMAT", "QCOM", "AMAT"),
    ("AMAT/ARM", "AMAT", "ARM"), ("JNJ/ABBV", "JNJ", "ABBV"),
    ("BA/RTX", "BA", "RTX"),
]
DAYS = 400          # trading days back (~1.6y of 5-min bars)
LOOKBACK = 60       # 5-hour trailing z window
HORIZON = 39        # half-session horizon cap
Z_ENTRY = 2.0


def fetch(sym):
    path = os.path.join(INTRA_DIR, f"{sym}.csv")
    if os.path.exists(path):
        with open(path, newline="") as f:
            rdr = csv.DictReader(f)
            rows = [(int(r["t"]), r["session"], float(r["close"]))
                    for r in rdr if r.get("close")]
        if len(rows) > 500:
            return rows
    h, err = sources.polygon_intraday(sym, interval=5, days=DAYS)
    if err:
        print(f"  fetch {sym}: {err}", file=sys.stderr)
        return None
    rows = [(int(t), s, c) for t, s, c in zip(h["date"], h["session"], h["close"])]
    os.makedirs(INTRA_DIR, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "session", "close"])
        for r in rows:
            w.writerow(r)
    return rows


def align(ra, rb):
    """Intersect on (session, timestamp); return aligned closes."""
    kb = {(s, t): c for t, s, c in rb}
    a, b = [], []
    for t, s, c in ra:
        if (s, t) in kb:
            a.append(c)
            b.append(kb[(s, t)])
    return a, b


def engine_test(z_entry=Z_ENTRY, cost_bps=3.8):
    data = {}
    syms = sorted({s for _, x, y in PAIRS for s in (x, y)})
    print(f"Fetching {len(syms)} symbols (5-min, ~{DAYS} days)...", file=sys.stderr)
    for s in syms:
        r = fetch(s)
        if r:
            data[s] = r
        time.sleep(0.3)
    print(f"Loaded {len(data)}/{len(syms)} symbols", file=sys.stderr)

    random.seed(31337)
    rows = []
    for label, sa, sb in PAIRS:
        if sa not in data or sb not in data:
            continue
        a, b = align(data[sa], data[sb])
        if len(a) < 2000:
            print(f"  {label}: only {len(a)} aligned bars, skip", file=sys.stderr)
            continue
        n = len(a)
        split = int(n * 0.6)
        for name, aa, bb in (("REAL", a, b), ("SCRAMBLED", a, b)):
            if name == "SCRAMBLED":
                lag = random.randint(200, 2000)
                bb = [bb[(i + lag) % len(bb)] for i in range(n)]
            la = [math.log(x) for x in aa]
            lb = [math.log(x) for x in bb]
            beta = v4_ols(la, lb, split)
            spread = [la[i] - beta * lb[i] for i in range(n)]
            # OOS replay with v5 symmetric engine
            trs = v5.replay_mr(spread, LOOKBACK, z_entry, z_entry, HORIZON,
                               open_from=split)
            if not trs:
                continue
            rets = []
            for t in trs:
                esd = t["entry_sd"]
                cost_sigma = 4.0 * (cost_bps / 1e4) / esd if esd > 0 else 0.0
                rets.append(t["sigma_net"] - cost_sigma)
            rows.append({"pair": label, "name": name, "n": len(rets),
                         "mean": statistics.fmean(rets),
                         "sd": statistics.pstdev(rets) if len(rets) > 1 else 0.0})
    # aggregate
    for name in ("REAL", "SCRAMBLED"):
        rs = [r for r in rows if r["name"] == name]
        if not rs:
            continue
        n = sum(r["n"] for r in rs)
        mean = sum(r["mean"] * r["n"] for r in rs) / n
        sd = math.sqrt(sum(r["sd"] ** 2 * r["n"] for r in rs) / n) if n else 0.0
        per_tr = sum(r["mean"] * r["n"] for r in rs) / n
        per_ann = (per_tr / sd) * math.sqrt(252 * 78) if sd > 0 else 0.0
        print(f"{name:10s} trades={n:5d}  per-trade net {per_tr:+.3f} sigma  "
              f"pooled sd {sd:.3f}  ann Sharpe* {per_ann:+.1f}")
        for r in sorted(rs, key=lambda x: -x["mean"]):
            print(f"    {r['pair']:12s} n={r['n']:4d} net {r['mean']:+.3f} sigma")


def v4_ols(y, x, n):
    import pairs_research_v4 as v4
    return v4._ols_beta(y[:n], x[:n])


if __name__ == "__main__":
    engine_test()
