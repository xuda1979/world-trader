"""pairs_crossasset.py -- does daily mean reversion exist ANYWHERE at 3.8 bps?

The v5 engine found no edge on 404 US large-cap pairs (real ~= scrambled ~= 0).
This extends the SAME falsification-first protocol to other asset classes and
to the long-horizon "pair-level value" variant:

  Part 1 (cross-asset): BTC/ETH (binance, 1434 bars), ETF pairs (twelvedata
    1000 bars), FX majors (twelvedata fetch, single-cross z reversion).
  Part 2 (long horizon): all 404 US pairs with lookback=250 (1y), horizon=120
    -- z-scores at the yearly horizon, the De Bondt-Thaler-style reversion.

Every test reports per-trade net expectancy (sigma units, 4 x 3.8 bps per
trade) REAL vs SCRAMBLED.  Only real-minus-scrambled > 0 is evidence.
"""
from __future__ import annotations
import os, sys, math, statistics, random, time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
for p in (_HERE, _ROOT, os.path.join(_ROOT, "tools")):
    sys.path.insert(0, p)

from wt import sources
import pairs_engine_v5 as v5
import pairs_portfolio_sim as ps

COST_BPS = 3.8
FX_CROSSES = ["EUR/GBP", "GBP/JPY", "AUD/NZD", "EUR/CHF", "AUD/JPY"]


def load_csv(path, close_col=4, date_col=0):
    import csv
    dates, closes = [], []
    with open(path, newline="") as f:
        rdr = csv.reader(f)
        next(rdr, None)
        for row in rdr:
            if len(row) <= close_col:
                continue
            try:
                c = float(row[close_col])
            except (ValueError, IndexError):
                continue
            if not math.isfinite(c) or c <= 0:
                continue
            dates.append(row[date_col])
            closes.append(c)
    return dates, closes


def engine_eval(spreads, labels, name, lookback, horizon, z_entry,
                split_frac=0.6, cost_bps=COST_BPS):
    """spreads: list of series; returns per-trade net stats real & scrambled."""
    random.seed(4242)
    out = {}
    for tag in ("REAL", "SCRAMBLED"):
        rows = []
        for s, lab in zip(spreads, labels):
            n = len(s)
            if n < lookback + horizon + 30:
                continue
            split = int(n * split_frac)
            if tag == "SCRAMBLED":
                hi = max(21, n // 3)
                lag = random.randint(20, hi)
                s = [s[(i + lag) % n] for i in range(n)]
            trs = v5.replay_mr(s, lookback, z_entry, z_entry, horizon,
                               open_from=split)
            if not trs:
                continue
            rets = []
            for t in trs:
                esd = t["entry_sd"]
                c = 4.0 * (cost_bps / 1e4) / esd if esd > 0 else 0.0
                rets.append(t["sigma_net"] - c)
            rows.append({"label": lab, "n": len(rets),
                         "mean": statistics.fmean(rets) if rets else 0.0})
        n = sum(r["n"] for r in rows)
        mean = sum(r["mean"] * r["n"] for r in rows) / n if n else 0.0
        out[tag] = {"rows": rows, "n_trades": n, "per_trade": mean}
        print(f"  {name:28s} {tag:9s} trades={n:5d}  "
              f"per-trade net {mean:+.4f} sigma")
    return out


def part1_cross_asset():
    print("== Part 1: cross-asset daily mean reversion (v5, z=2.0, "
          f"{COST_BPS} bps) ==")
    # BTC/ETH
    ba = load_csv(os.path.join(_HERE, "data", "binance", "BTC.csv"))
    bb = load_csv(os.path.join(_HERE, "data", "binance", "ETH.csv"))
    if ba and bb:
        a, b, dates = ps.v4._align(*ba, *bb) if False else _align(ba, bb)
        if len(a) > 500:
            la = [math.log(x) for x in a]; lb = [math.log(x) for x in b]
            beta = ps.v4._ols_beta(la[:int(len(la) * 0.6)], lb[:int(len(lb) * 0.6)])
            spread = [la[i] - beta * lb[i] for i in range(len(la))]
            engine_eval([spread], ["BTC/ETH"], "BTC/ETH", 60, 60, 2.0)
    # ETF pairs (twelvedata cache)
    etf_pairs = [("EWA/EWC", "EWA", "EWC"), ("XLB/XLE", "XLB", "XLE"),
                 ("XLI/XLB", "XLI", "XLB")]
    spreads, labs = [], []
    for lab, x, y in etf_pairs:
        dx = load_csv(os.path.join(_HERE, "data", "twelvedata", f"{x}.csv"))
        dy = load_csv(os.path.join(_HERE, "data", "twelvedata", f"{y}.csv"))
        if not dx or not dy:
            continue
        a, b, _ = _align(dx, dy)
        if len(a) < 500:
            continue
        la = [math.log(v) for v in a]; lb = [math.log(v) for v in b]
        beta = ps.v4._ols_beta(la[:int(len(la) * 0.6)], lb[:int(len(lb) * 0.6)])
        spreads.append([la[i] - beta * lb[i] for i in range(len(la))])
        labs.append(lab)
    if spreads:
        engine_eval(spreads, labs, "ETF pairs (twelvedata 1000b)", 60, 60, 2.0)
    # FX crosses (single-series z reversion)
    fx_spreads, fx_labs = [], []
    for cross in FX_CROSSES:
        h, err = sources.twelvedata_history(cross, days=1000)
        if err or not h:
            print(f"  FX fetch {cross}: {err}", file=sys.stderr)
            continue
        c = h["close"]
        if len(c) < 500:
            continue
        fx_spreads.append(c)  # level series; engine uses z-scores on it
        fx_labs.append(cross)
        time.sleep(1.5)
    if fx_spreads:
        engine_eval(fx_spreads, fx_labs, "FX majors (twelvedata)",
                    60, 60, 2.0)


def part2_long_horizon():
    print(f"\n== Part 2: long-horizon reversion, 404 US pairs, "
          f"lookback=250 horizon=120 (v5, {COST_BPS} bps) ==")
    pairs = ps.build_universe()
    spreads, labs = [], []
    for p in pairs:
        label, ac, sa, sb, kind, prov = p
        if ac != "STOCK":
            continue
        d = ps._pair_data(label, ac, sa, sb, kind, prov)
        if d is None or len(d["spread"]) < 400:
            continue
        spreads.append(d["spread"])
        labs.append(label)
    print(f"  pairs with data: {len(spreads)}")
    engine_eval(spreads, labs, "all US stock pairs", 250, 120, 2.0)
    engine_eval(spreads, labs, "all US stock pairs", 250, 120, 1.5)


def _align(da_ca, db_cb):
    da, ca = da_ca
    db, cb = db_cb
    idx = {d: i for i, d in enumerate(db)}
    a, b, dates = [], [], []
    for i, d in enumerate(da):
        if d in idx:
            a.append(ca[i]); b.append(cb[idx[d]]); dates.append(d)
    return a, b, dates


if __name__ == "__main__":
    part1_cross_asset()
    part2_long_horizon()
