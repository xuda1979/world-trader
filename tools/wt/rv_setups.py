"""Relative-value (RV) mean-reversion setups on spreads.

A spread is the difference between two price/yield series that SHOULD stay
cointegrated (e.g., 2s10s yield curve, EUR/USD - GBP/USD cross, FANG index
vs SPY). When the spread's rolling z-score exceeds +/-2, bet on reversion.

This is structurally distinct from the price-MR setups in analysis.py:
  - Price MR (OSbounce, OversoldPanic): reverts a single PRICE to its mean.
  - RV MR (RVMR): reverts the RELATIONSHIP between two instruments to its mean.

The edge is cointegration-style: the spread is stationary even when the
underlying prices aren't. We use a rolling-z trigger (lookback=60, z_entry=2)
rather than a full OLS hedge ratio -- good enough for short-term, far less
data-hungry.

Two kinds of spreads are supported:
  1. YIELD spreads: build from FRED historical yields (DGS2, DGS10, etc.).
  2. FX spreads: build from two Twelve Data FX histories (close-to-close).

Output rows have the same shape as the main scan's scored rows so they can
be merged and ranked together. The `qualifies_rv` gate is used (stricter
Sharpe, no price-fraction gate since PnL is in spread-stdev units).
"""
from __future__ import annotations
import sys, os, time
from concurrent.futures import ThreadPoolExecutor

# Support both `from wt import rv_setups` and `python3 tools/wt/rv_setups.py`
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from wt import analysis, altdata, sources, core
else:
    from . import analysis, altdata, sources, core

# Curated RV pair universe. Each entry: (label, kind, args).
#   kind="YIELD":  args = (series_a, series_b)  -- FRED series IDs.
#   kind="FX":     args = (pair_a, pair_b)      -- Twelve Data symbols.
# YIELD pairs are classic curve trades; FX pairs are classic cross-rate arbs.
RV_PAIRS = [
    # Yield curve spreads (basis points)
    ("2s10s",        "YIELD", ("DGS2",  "DGS10")),
    ("2s30s",        "YIELD", ("DGS2",  "DGS30")),
    ("5s30s",        "YIELD", ("DGS5",  "DGS30")),
    ("3m10y",        "YIELD", ("DGS3MO", "DGS10")),
    # FX cross spreads (currency units)
    ("EUR/GBP",      "FX",    ("EUR/USD", "GBP/USD")),
    ("EUR/CHF",      "FX",    ("EUR/USD", "USD/CHF")),
    ("AUD/CAD",      "FX",    ("AUD/USD", "USD/CAD")),
    ("AUD/NZD",      "FX",    ("AUD/USD", "NZD/USD")),
    ("GBP/JPY",      "FX",    ("GBP/USD", "USD/JPY")),
    ("EUR/AUD",      "FX",    ("EUR/USD", "AUD/USD")),
]


def _build_yield_spread(series_a, series_b, limit=400):
    """Align two FRED yield series on date and return (spread_list, err)."""
    va, da, ea = altdata.fred_history(series_a, limit=limit)
    vb, db, eb = altdata.fred_history(series_b, limit=limit)
    if ea: return None, f"{series_a}: {ea}"
    if eb: return None, f"{series_b}: {eb}"
    if not va or not vb: return None, "no data"
    idx_b = {d: i for i, d in enumerate(db)}
    spread = []
    for i, d in enumerate(da):
        if d in idx_b:
            spread.append(va[i] - vb[idx_b[d]])
    if len(spread) < 80:
        return None, "too few aligned obs"
    return spread, None


def _build_fx_spread(pair_a, pair_b, days=400, rate_limit_s=8):
    """Align two Twelve Data FX histories on date and return (spread_list, err).

    Spreads the two close series directly (both in USD-terms for majors, so
    the spread is a meaningful cross-rate difference). Pairs that aren't both
    in USD terms (e.g. 'GBP/JPY') are constructed from the two USD legs."""
    ha, ea = sources.twelvedata_history(pair_a, days=days)
    if ea: time.sleep(rate_limit_s)
    hb, eb = sources.twelvedata_history(pair_b, days=days)
    if ea or eb or not ha or not hb:
        return None, f"{pair_a}={ea} {pair_b}={eb}"
    db = {d: i for i, d in enumerate(hb["date"])}
    spread = []
    for i in range(len(ha["date"])):
        if ha["date"][i] in db:
            spread.append(ha["close"][i] - hb["close"][db[ha["date"][i]]])
    if len(spread) < 80:
        return None, "too few aligned obs"
    return spread, None


def _scan_one(label, kind, args):
    """Build the spread, backtest RVMR, return a scored row (or None)."""
    if kind == "YIELD":
        spread, err = _build_yield_spread(*args)
    elif kind == "FX":
        spread, err = _build_fx_spread(*args)
    else:
        return None, f"unknown kind {kind}"
    if err or not spread:
        return None, err or "no spread"
    bt = analysis.backtest_rv_mean_reversion(spread)
    if not bt:
        return None, "no backtest (insufficient samples)"
    # Convert the RV stat-dict into the same row shape as the main scan.
    side = bt["side"]
    risk = bt.get("cur_risk") or 0.01
    reward = bt["rr"] * risk
    z = bt.get("z_now", 0.0)
    rr_row = {
        "side": side,
        "entry": z,            # z-score is the "price" of this spread
        "stop":  (-1 if side == "Long" else 1) * 2.0,  # stop at |z|=2
        "target": (-1 if side == "Long" else 1) * 0.0, # target at z=0
        "risk": risk,
        "reward": reward,
        "rr": bt["rr"],
        "passes": False,
        "setup": "RVMR",
    }
    comp = analysis.composite_score(rr_row, regime_score=0.0)  # neutral regime for RV
    return {
        "label": label,
        "sym": f"RV:{label}",
        "native": label,
        "rr": rr_row,
        "comp": comp,
        "price": z,
        "dp": None,             # no price change for a spread
        "tech": None,
        "fresh": "OK",
        "ts": None,
        "live": True,
        "mkt": "RV",
        "bt": bt,
        "setup": "RVMR",
        "sharpe": bt["edge"],
        "exp_ret": bt["exp_ret"],
        "oos_exp": bt.get("oos_exp_ret"),
        "oos_sharpe": bt.get("oos_edge"),
        "n_tests": 1,            # one RV test per spread (RVMR is single-horizon)
        "n_tests_global": 1,
        "qualifies": analysis.qualifies_rv(bt, n_tests=1),
        "news_align": 0,
        "news": None,
        "opt": None,
        "catalyst": None,
        "z_now": z,
    }, None


def scan_rv_pairs(pairs=None, workers=3):
    """Scan all RV pairs in parallel, return (rows, errors)."""
    pairs = pairs or RV_PAIRS
    rows, errors = [], []

    def one(p):
        label, kind, args = p
        row, err = _scan_one(label, kind, args)
        return label, row, err

    # FX pairs hit Twelve Data (rate-limited), so keep parallelism modest.
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(one, pairs))
    for label, row, err in results:
        if row:
            rows.append(row)
        elif err:
            errors.append(f"{label}: {err}")
    return rows, errors


if __name__ == "__main__":
    rows, errors = scan_rv_pairs()
    print(f"=== RV MEAN-REVERSION SCAN {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    qualifying = [r for r in rows if r.get("qualifies")]
    firing = [r for r in rows if r.get("z_now") and abs(r["z_now"]) > 2.0]
    print(f"\n{len(rows)} pairs scanned, {len(qualifying)} qualify, "
          f"{len(firing)} firing (|z|>2)")
    print(f"\n{'Pair':12s} {'z':>7s} {'side':5s} {'sharpe':>7s} {'t':>6s} "
          f"{'oos_sh':>7s} {'n':>4s} {'qual':>5s}")
    for r in sorted(rows, key=lambda x: -abs(x.get("z_now", 0))):
        z = r.get("z_now", 0)
        bt = r["bt"]
        q = "YES" if r.get("qualifies") else ""
        print(f"{r['label']:12s} {z:>+7.2f} {bt['side']:5s} {bt['edge']:>7.3f} "
              f"{bt['tstat']:>6.2f} {bt.get('oos_edge',0) or 0:>7.3f} {bt['n']:>4d} {q:>5s}")
    if errors:
        print(f"\n--- {len(errors)} errors ---")
        for e in errors[:10]:
            print(f"  {e}")
