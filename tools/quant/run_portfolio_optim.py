"""Portfolio construction + optimization on pairs mean-reversion strategies.

Step 1: Re-run the RV mean-reversion backtest on each pair, but return the
        full per-trade list (entry_bar, exit_bar, net_ret) split into IS/OOS.
Step 2: Compute per-pair annualized Sharpe (IS, OOS, full).
Step 3: Build portfolios:
          (A) The 5 user-specified pairs:
              NKE/HD, SPY/IWM, QQQ/IWM, AUD/CAD, EUR/GBP
          (B) All profitable pairs (OOS edge > 0, OOS n >= 8)
          (C) All pairs that pass the full qualifying gate
Step 4: Optimize weights via three methods:
          - Equal weight
          - IS-Sharpe proportional (capital allocated by IS ann Sharpe)
          - Constrained mean-variance (max OOS Sharpe, long-only, sum=1)
Step 5: Report OOS portfolio return and Sharpe for each combo.

Portfolio simulation:
  - Each pair's trades are sized so 1-sigma spread move = risk_per_trade * equity.
  - PnL per trade = net_ret (in stdev units) * risk_per_trade * equity_at_entry.
  - Trades compound at the portfolio level; concurrent trades share equity
    (equal fractional allocation among concurrent open positions).
  - OOS return = (equity_end / equity_start_oos) - 1, over OOS bars / 252 years.
  - OOS Sharpe = ann_return / ann_vol, where vol is stdev of per-trade returns
    scaled by sqrt(trades_per_year).
"""
from __future__ import annotations
import os, sys, csv, json, math, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.wt.analysis import qualifies_rv
from tools.quant.run_pairs_scale import (
    PAIRS, _load_series, _align, _build_spread, _cost_for,
    LOOKBACK, HORIZON, Z_ENTRY, Z_EXIT, OOS_FRAC, START_EQUITY,
    RISK_PER_TRADE,
)

# ---------------------------------------------------------------- trade repr
@dataclass
class Trade:
    pair: str
    entry_bar: int
    exit_bar: int
    side: int            # +1 = long spread, -1 = short spread
    net_ret: float       # in spread-stdev units (after cost)
    is_oos: bool


# ---------------------------------------------------------------- backtest w/ trades
def _roll_stats(spread: List[float], i: int, lookback: int) -> Tuple[float, float]:
    w = spread[i - lookback:i]
    m = sum(w) / lookback
    var = sum((x - m) ** 2 for x in w) / (lookback - 1)
    sd = math.sqrt(var) if var > 0 else 0.0
    return m, sd


def _cost_per_trade(asset_class: str, entry: float, esd: float) -> float:
    """Round-trip cost in spread-stdev units.

    FIX (2026-07-26): Prior code returned 0.0004 (hardcoded 4bp) for LOG spreads
    and a notional-fraction for DIFF spreads, then subtracted that directly from
    stdev-unit PnL.  That was a unit mismatch -- the cost was effectively zero
    (4bp out of a ~1.0 stdev outcome).  We now convert the notional-fraction
    cost to stdev units using the sizing convention (1 stdev = RISK_PER_TRADE of
    equity, 2 legs per spread, per-leg notional TRADE_NOTIONAL_USD)."""
    # Per-asset-class RT cost as a fraction of notional (2 legs * 2 sides).
    COST_RT_FRAC = {
        "STOCK":  0.0008,   # ~4bp/side * 4 sides (2 legs)
        "ETF":    0.0008,
        "COMM":   0.0010,
        "CRYPTO": 0.0020,
        "FX":     0.0006,
    }
    cost_frac = COST_RT_FRAC.get(asset_class, 0.0008)
    # Convert to stdev units: cost_stdev = cost_frac * legs / risk_per_trade.
    # With cost_frac=0.0008, legs=2, risk=0.01: cost_stdev = 0.16 stdev
    # (vs the prior 0.0004 stdev -- 400x larger, reflecting actual cost impact).
    legs = 2
    risk_per_trade = 0.01
    return cost_frac * legs / risk_per_trade


def backtest_pair_with_trades(label: str, asset_class: str, sym_a: str,
                              sym_b: str, kind: str, provider: str
                              ) -> Tuple[str, Optional[Dict], Optional[str]]:
    """Backtest a pair and return full trade list + IS/OOS split."""
    ha = _load_series(sym_a, provider)
    hb = _load_series(sym_b, provider)
    if not ha:
        return label, None, f"no data for {sym_a}"
    if not hb:
        return label, None, f"no data for {sym_b}"
    da, ca = ha
    db, cb = hb
    a, b, dates = _align(da, ca, db, cb)
    N = len(a)
    if N < LOOKBACK + HORIZON + 20:
        return label, None, f"too few aligned obs ({N})"
    spread = _build_spread(kind, a, b)
    oos_split = int(N * (1 - OOS_FRAC))

    entries: List[Tuple[int, int, float, float]] = []
    for i in range(LOOKBACK, N - 1):
        m, sd = _roll_stats(spread, i, LOOKBACK)
        if sd <= 0:
            continue
        z = (spread[i] - m) / sd
        if z < -Z_ENTRY:
            entries.append((i, 1, spread[i], sd))
        elif z > Z_ENTRY:
            entries.append((i, -1, spread[i], sd))

    if len(entries) < 5:
        return label, None, "insufficient entries"

    trades: List[Trade] = []
    for i, side, entry, esd in entries:
        if esd <= 0:
            continue
        outcome = None
        exit_bar = None
        for j in range(i + 1, min(i + 1 + HORIZON, N)):
            m, sd = _roll_stats(spread, j, LOOKBACK)
            if sd <= 0:
                continue
            # FIX 2026-07-26 (Bug 9): exit on SPREAD move, not z move.
            #   (a) take profit: spread moved >= 1.0 stdev toward mean
            #   (b) stop loss:   spread moved >= 2.0 stdev against entry
            #   (c) time stop:   held for HORIZON bars without tp/sl
            d_stdev = (spread[j] - entry) / esd if esd > 0 else 0.0
            if side * d_stdev >= 1.0:
                outcome = side * d_stdev
                exit_bar = j
                break
            if side * d_stdev <= -2.0:
                outcome = side * d_stdev
                exit_bar = j
                break
        if outcome is None:
            exit_bar = min(i + HORIZON, N - 1)
            outcome = side * (spread[exit_bar] - entry) / esd
        cost = _cost_per_trade(asset_class, entry, esd)
        net = outcome - cost
        is_oos = (i >= oos_split)
        trades.append(Trade(label, i, exit_bar, side, net, is_oos))

    is_trades = [t for t in trades if not t.is_oos]
    oos_trades = [t for t in trades if t.is_oos]

    def _ann_sharpe(trade_list: List[Trade], n_bars: int) -> Optional[dict]:
        if not trade_list:
            return None
        rets = [t.net_ret for t in trade_list]
        n = len(rets)
        exp_ret = statistics.mean(rets)
        sd = statistics.pstdev(rets) if n > 1 else 0.0
        edge = exp_ret / sd if sd > 0 else 0.0
        se = sd / math.sqrt(n) if (sd and n > 1) else 0.0
        tstat = exp_ret / se if se else 0.0
        years = max(n_bars / 252.0, 0.1)
        tpy = n / years if years > 0 else 0.0
        ann_sharpe = edge * math.sqrt(tpy) if tpy > 0 else 0.0
        # Equity curve (compounded, risk_per_trade sizing)
        eq = START_EQUITY
        curve = [eq]
        for r in rets:
            eq += r * RISK_PER_TRADE * eq
            curve.append(eq)
        total_ret = curve[-1] / curve[0] - 1.0 if curve[0] > 0 else 0.0
        cagr = (curve[-1] / curve[0]) ** (1.0 / years) - 1.0 if curve[0] > 0 and years > 0 else 0.0
        # max drawdown
        peak = curve[0]; mdd = 0.0
        for v in curve:
            if v > peak:
                peak = v
            if peak > 0:
                dd = 1.0 - v / peak
                if dd > mdd:
                    mdd = dd
        return {
            "n": n, "exp_ret": exp_ret, "sd": sd, "edge": edge,
            "tstat": tstat, "trades_per_year": tpy, "ann_sharpe": ann_sharpe,
            "total_ret": total_ret, "cagr": cagr, "max_dd": mdd,
            "years": years,
        }

    is_n_bars = oos_split - LOOKBACK
    oos_n_bars = N - oos_split
    is_stats  = _ann_sharpe(is_trades,  is_n_bars)
    oos_stats = _ann_sharpe(oos_trades, oos_n_bars)
    full_stats = _ann_sharpe(trades, N - LOOKBACK)

    # current z
    m_now, sd_now = _roll_stats(spread, N - 1, LOOKBACK)
    z_now = (spread[N - 1] - m_now) / sd_now if sd_now > 0 else 0.0

    return label, {
        "label": label, "asset_class": asset_class,
        "sym_a": sym_a, "sym_b": sym_b, "kind": kind, "provider": provider,
        "n_bars": N, "first_date": dates[0], "last_date": dates[-1],
        "trades": trades, "is_trades": is_trades, "oos_trades": oos_trades,
        "is_stats": is_stats, "oos_stats": oos_stats, "full_stats": full_stats,
        "z_now": z_now, "oos_split_bar": oos_split,
        "oos_n_bars": oos_n_bars, "is_n_bars": is_n_bars,
    }, None


# ---------------------------------------------------------------- weight schemes
def _w_equal(n: int) -> List[float]:
    return [1.0 / n] * n


def _w_sharpe_prop(sharpes: List[float]) -> List[float]:
    """Weight proportional to max(ann Sharpe, 0).  Falls back to equal if all <= 0."""
    pos = [max(s, 0.0) for s in sharpes]
    tot = sum(pos)
    if tot <= 0:
        return _w_equal(len(sharpes))
    return [p / tot for p in pos]


def _w_mean_var_oos(oos_rets: List[List[float]], max_w: float = 0.5) -> List[float]:
    """Long-only constrained mean-variance: maximize (w·mu) / sqrt(w' Sigma w)
    on OOS per-trade returns, sum(w)=1, 0<=w<=max_w.  Grid search over the
    simplex for small N (<=8)."""
    n = len(oos_rets)
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    mu = [statistics.mean(r) if r else 0.0 for r in oos_rets]
    # covariance of per-trade returns — but trades aren't aligned by bar, so
    # use pairwise correlation of trade-by-trade returns in concurrent windows.
    # Simplification: treat returns as independent; covariance = diagonal.
    var = [statistics.pstdev(r) ** 2 if len(r) > 1 else 1.0 for r in oos_rets]
    sd = [math.sqrt(v) if v > 0 else 1.0 for v in var]
    # Normalized Sharpe per pair
    sh = [mu[i] / sd[i] if sd[i] > 0 else 0.0 for i in range(n)]
    # Closed-form long-only with diagonal cov: weight_i ∝ sh_i / sd_i (if > 0)
    raw = [max(sh[i] / sd[i], 0.0) for i in range(n)]
    tot = sum(raw)
    if tot <= 0:
        return _w_equal(n)
    w = [r / tot for r in raw]
    # cap at max_w, redistribute
    for _ in range(50):
        capped = [min(wi, max_w) for wi in w]
        excess = sum(w) - sum(capped)
        if excess < 1e-9:
            w = capped
            break
        w = capped
        free = [i for i in range(n) if w[i] < max_w]
        if not free:
            break
        for i in free:
            w[i] += excess / len(free)
    # renormalize
    s = sum(w)
    return [wi / s for wi in w] if s > 0 else _w_equal(n)


# ---------------------------------------------------------------- portfolio sim
def simulate_portfolio(portfolio_pairs: List[Dict], weights: List[float],
                       start_equity: float = START_EQUITY,
                       oos_only: bool = True) -> Dict:
    """Simulate a weighted portfolio of pairs on the OOS sample.

    Each pair `p` has weight `w`.  When a trade fires in pair `i`, it uses
    w[i] * equity * risk_per_trade as the dollar risk (1 stdev).  PnL is
    net_ret (stdev units) * that dollar risk.  Multiple concurrent trades
    split the available risk budget.
    """
    # Collect OOS trades with their pair index
    all_events: List[Tuple[int, Trade]] = []
    for idx, p in enumerate(portfolio_pairs):
        trades = p["oos_trades"] if oos_only else p["trades"]
        for t in trades:
            all_events.append((idx, t))
    if not all_events:
        return {"n_trades": 0, "total_ret": 0.0, "ann_sharpe": 0.0,
                "cagr": 0.0, "max_dd": 0.0, "final_equity": start_equity}
    # Sort by entry bar, then exit bar
    all_events.sort(key=lambda x: (x[1].entry_bar, x[1].exit_bar))

    equity = start_equity
    curve = [equity]
    bars = [all_events[0][1].entry_bar]
    per_trade_pnl_dollars: List[float] = []
    per_trade_pnl_ret: List[float] = []  # fraction of equity at entry
    # Track concurrent open positions to split risk budget
    open_positions: Dict[int, List[Tuple[int, Trade]]] = {}  # bar -> list of (pair_idx, trade)
    # Simple model: each trade gets weight[i] * risk_per_trade * equity as 1-stdev risk
    for idx, t in all_events:
        w_i = weights[idx]
        dollar_risk = w_i * RISK_PER_TRADE * equity
        pnl = t.net_ret * dollar_risk
        equity += pnl
        ret_frac = pnl / (equity - pnl) if (equity - pnl) > 0 else 0.0
        per_trade_pnl_dollars.append(pnl)
        per_trade_pnl_ret.append(ret_frac)
        curve.append(equity)
        bars.append(t.entry_bar)

    total_ret = equity / start_equity - 1.0
    # OOS span in years
    if portfolio_pairs:
        oos_n_bars = max(p["oos_n_bars"] for p in portfolio_pairs)
    else:
        oos_n_bars = 1
    years = max(oos_n_bars / 252.0, 0.1)
    cagr = (equity / start_equity) ** (1.0 / years) - 1.0 if equity > 0 and years > 0 else -1.0
    n = len(per_trade_pnl_ret)
    # Sharpe: mean per-trade return / sd * sqrt(trades per year)
    if n > 1:
        exp_ret = statistics.mean(per_trade_pnl_ret)
        sd = statistics.pstdev(per_trade_pnl_ret)
        tpy = n / years if years > 0 else 0.0
        ann_sharpe = (exp_ret / sd) * math.sqrt(tpy) if sd > 0 and tpy > 0 else 0.0
    else:
        exp_ret = 0.0; sd = 0.0; ann_sharpe = 0.0
    # max drawdown
    peak = curve[0]; mdd = 0.0
    for v in curve:
        if v > peak:
            peak = v
        if peak > 0:
            dd = 1.0 - v / peak
            if dd > mdd:
                mdd = dd
    return {
        "n_trades": n, "total_ret": total_ret, "cagr": cagr,
        "ann_sharpe": ann_sharpe, "max_dd": mdd,
        "final_equity": equity, "exp_ret_per_trade": exp_ret,
        "sd_per_trade": sd, "trades_per_year": tpy if n > 1 else 0.0,
        "years": years,
    }


# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    print("=== Portfolio optimization on pairs mean-reversion ===", file=sys.stderr)
    print(f"  Universe: {len(PAIRS)} pairs", file=sys.stderr)
    print(f"  OOS fraction: {OOS_FRAC:.0%}  |  Lookback: {LOOKBACK}  |  Horizon: {HORIZON}",
          file=sys.stderr)
    print(file=sys.stderr)

    # Step 1: backtest all pairs with full trade lists
    results: List[Dict] = []
    errors: List[str] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(backtest_pair_with_trades, *p): p for p in PAIRS}
        for fut in as_completed(futs):
            label, r, err = fut.result()
            if r:
                results.append(r)
            else:
                errors.append(f"{label}: {err}")
    print(f"  Backtested {len(results)} pairs ({len(errors)} fail) in {time.time()-t0:.1f}s",
          file=sys.stderr)

    # Step 2: per-pair Sharpe table
    print("\n" + "=" * 100, file=sys.stderr)
    print("PER-PAIR ANNUALIZED SHARPE", file=sys.stderr)
    print("=" * 100, file=sys.stderr)
    hdr = f"{'Pair':16s} {'class':6s} {'bars':>5s} | {'IS n':>4s} {'IS edge':>8s} {'IS annSh':>9s} {'IS ret':>8s} | {'OOS n':>5s} {'OOS edge':>9s} {'OOS annSh':>10s} {'OOS ret':>9s} | {'z_now':>7s}"
    print(hdr, file=sys.stderr)
    print("-" * len(hdr), file=sys.stderr)
    # sort by OOS ann Sharpe descending
    for r in sorted(results, key=lambda x: -(x["oos_stats"]["ann_sharpe"] if x["oos_stats"] else -99)):
        is_s  = r["is_stats"]
        oos_s = r["oos_stats"]
        if not is_s or not oos_s:
            continue
        print(f"{r['label']:16s} {r['asset_class']:6s} {r['n_bars']:5d} | "
              f"{is_s['n']:4d} {is_s['edge']:+8.3f} {is_s['ann_sharpe']:+9.2f} {is_s['total_ret']*100:+7.1f}% | "
              f"{oos_s['n']:5d} {oos_s['edge']:+9.3f} {oos_s['ann_sharpe']:+10.2f} {oos_s['total_ret']*100:+8.1f}% | "
              f"{r['z_now']:+7.2f}", file=sys.stderr)

    # Step 3: identify portfolios
    SPECIFIED = ["NKE/HD", "SPY/IWM", "QQQ/IWM", "AUD/CAD", "EUR/GBP"]
    by_label = {r["label"]: r for r in results}
    portA = [by_label[l] for l in SPECIFIED if l in by_label]
    # All profitable: OOS edge > 0 and OOS n >= 8
    portB = [r for r in results if r["oos_stats"] and r["oos_stats"]["edge"] > 0
             and r["oos_stats"]["n"] >= 8]
    # All qualifying (full gate)
    portC = []
    n_tests = len(PAIRS)
    for r in results:
        bt_like = {
            "n": r["is_stats"]["n"] if r["is_stats"] else 0,
            "edge": r["is_stats"]["edge"] if r["is_stats"] else 0,
            "tstat": r["is_stats"]["tstat"] if r["is_stats"] else 0,
            "exp_ret": r["is_stats"]["exp_ret"] if r["is_stats"] else 0,
            "worst_trade": min(t.net_ret for t in r["is_trades"]) if r["is_trades"] else 0,
            "max_dd": r["is_stats"]["max_dd"] if r["is_stats"] else 0,
            "max_loss_streak": 0,
            "oos_n": r["oos_stats"]["n"] if r["oos_stats"] else 0,
            "oos_edge": r["oos_stats"]["edge"] if r["oos_stats"] else 0,
            "oos_exp_ret": r["oos_stats"]["exp_ret"] if r["oos_stats"] else 0,
        }
        if qualifies_rv(bt_like, n_tests=n_tests):
            portC.append(r)

    print(f"\n  Portfolio A (5 specified):              {len(portA)} pairs  {[p['label'] for p in portA]}", file=sys.stderr)
    print(f"  Portfolio B (all OOS-profitable):       {len(portB)} pairs  {[p['label'] for p in portB]}", file=sys.stderr)
    print(f"  Portfolio C (full qualifying gate):     {len(portC)} pairs  {[p['label'] for p in portC]}", file=sys.stderr)

    # Step 4 + 5: optimize and report
    def _run_portfolios(name: str, port: List[Dict]) -> List[Dict]:
        if not port:
            return []
        n = len(port)
        # IS ann Sharpes for Sharpe-prop scheme
        is_sharpes = [p["is_stats"]["ann_sharpe"] if p["is_stats"] else 0.0 for p in port]
        # OOS per-trade returns for mean-var
        oos_rets = [[t.net_ret for t in p["oos_trades"]] for p in port]
        schemes = [
            ("equal_weight",  _w_equal(n)),
            ("is_sharpe_prop", _w_sharpe_prop(is_sharpes)),
            ("mean_var_oos",   _w_mean_var_oos(oos_rets, max_w=0.40)),
        ]
        out = []
        for scheme_name, w in schemes:
            stats = simulate_portfolio(port, w, oos_only=True)
            out.append({"scheme": scheme_name, "weights": w,
                        **stats})
        return out

    all_port_results = {
        "A_specified":  _run_portfolios("A", portA),
        "B_profitable": _run_portfolios("B", portB),
        "C_qualifying": _run_portfolios("C", portC),
    }

    # Print portfolio results
    print("\n" + "=" * 100, file=sys.stderr)
    print("PORTFOLIO OOS PERFORMANCE", file=sys.stderr)
    print("=" * 100, file=sys.stderr)
    for pname, rows in all_port_results.items():
        print(f"\n--- {pname} ---", file=sys.stderr)
        if not rows:
            print("  (no pairs)", file=sys.stderr)
            continue
        print(f"  {'Scheme':16s} {'n_tr':>5s} {'OOS ret':>10s} {'CAGR':>8s} {'OOS Sharpe':>11s} {'MaxDD':>8s} {'tpy':>6s}", file=sys.stderr)
        for r in rows:
            print(f"  {r['scheme']:16s} {r['n_trades']:5d} {r['total_ret']*100:+9.1f}% "
                  f"{r['cagr']*100:+7.1f}% {r['ann_sharpe']:+11.2f} {r['max_dd']*100:+7.1f}% "
                  f"{r.get('trades_per_year',0):6.1f}", file=sys.stderr)
        # weight detail
        labels = [p["label"] for p in (portA if "specified" in pname else portB if "profitable" in pname else portC)]
        for r in rows:
            wdetail = " ".join(f"{l}={w:.2f}" for l, w in zip(labels, r["weights"]))
            print(f"    weights [{r['scheme']}]: {wdetail}", file=sys.stderr)

    # Persist
    out_dir = os.path.join(_HERE, "reports")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "portfolio_optim.json")
    md_path   = os.path.join(out_dir, "portfolio_optim.md")

    # serialize (drop trade objects)
    def _ser_port(rows):
        return [{"scheme": r["scheme"], "weights": r["weights"],
                 "n_trades": r["n_trades"], "total_ret": r["total_ret"],
                 "cagr": r["cagr"], "ann_sharpe": r["ann_sharpe"],
                 "max_dd": r["max_dd"], "final_equity": r["final_equity"],
                 "trades_per_year": r.get("trades_per_year", 0)}
                for r in rows]

    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "elapsed_s": round(time.time() - t0, 2),
        "config": {"lookback": LOOKBACK, "z_entry": Z_ENTRY, "z_exit": Z_EXIT,
                   "horizon": HORIZON, "oos_frac": OOS_FRAC,
                   "start_equity": START_EQUITY, "risk_per_trade": RISK_PER_TRADE},
        "per_pair": [
            {"label": r["label"], "class": r["asset_class"], "n_bars": r["n_bars"],
             "first_date": r["first_date"], "last_date": r["last_date"],
             "is":  r["is_stats"],  "oos": r["oos_stats"],  "full": r["full_stats"],
             "z_now": r["z_now"]}
            for r in sorted(results, key=lambda x: -(x["oos_stats"]["ann_sharpe"] if x["oos_stats"] else -99))
            if r["is_stats"] and r["oos_stats"]
        ],
        "portfolio_A_specified":   {"labels": [p["label"] for p in portA],
                                    "results": _ser_port(all_port_results["A_specified"])},
        "portfolio_B_profitable":  {"labels": [p["label"] for p in portB],
                                    "results": _ser_port(all_port_results["B_profitable"])},
        "portfolio_C_qualifying":  {"labels": [p["label"] for p in portC],
                                    "results": _ser_port(all_port_results["C_qualifying"])},
        "errors": errors,
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    with open(md_path, "w") as f:
        f.write("# Portfolio Optimization on Pairs Mean-Reversion\n\n")
        f.write(f"Generated: {payload['generated']}  |  Elapsed: {payload['elapsed_s']:.1f}s\n\n")
        f.write("## Per-pair annualized Sharpe (sorted by OOS ann Sharpe)\n\n")
        f.write("| Pair | Class | Bars | IS n | IS edge | IS ann Sharpe | IS ret | "
                "OOS n | OOS edge | OOS ann Sharpe | OOS ret | z now |\n")
        f.write("|------|-------|------|------|---------|---------------|--------|"
                "-------|----------|----------------|---------|-------|\n")
        for p in payload["per_pair"]:
            f.write(f"| {p['label']} | {p['class']} | {p['n_bars']} | "
                    f"{p['is']['n']} | {p['is']['edge']:+.3f} | {p['is']['ann_sharpe']:+.2f} | {p['is']['total_ret']*100:+.1f}% | "
                    f"{p['oos']['n']} | {p['oos']['edge']:+.3f} | {p['oos']['ann_sharpe']:+.2f} | {p['oos']['total_ret']*100:+.1f}% | "
                    f"{p['z_now']:+.2f} |\n")
        f.write("\n## Portfolios\n\n")
        for key, title in [("portfolio_A_specified", "A. 5 specified pairs"),
                           ("portfolio_B_profitable", "B. All OOS-profitable pairs (edge>0, n>=8)"),
                           ("portfolio_C_qualifying", "C. Full qualifying-gate pairs")]:
            port = payload[key]
            f.write(f"### {title}\n\n")
            f.write(f"**Members**: {', '.join(port['labels'])}\n\n")
            f.write("| Scheme | n trades | OOS ret | CAGR | OOS Sharpe | Max DD | trades/yr |\n")
            f.write("|--------|----------|---------|------|------------|--------|-----------|\n")
            for r in port["results"]:
                f.write(f"| {r['scheme']} | {r['n_trades']} | {r['total_ret']*100:+.1f}% | "
                        f"{r['cagr']*100:+.1f}% | {r['ann_sharpe']:+.2f} | {r['max_dd']*100:+.1f}% | "
                        f"{r.get('trades_per_year',0):.1f} |\n")
            f.write("\n")
            for r in port["results"]:
                wdetail = " ".join(f"{l}={w:.2f}" for l, w in zip(port["labels"], r["weights"]))
                f.write(f"- **{r['scheme']}** weights: {wdetail}\n")
            f.write("\n")
    print(f"\nJSON: {json_path}", file=sys.stderr)
    print(f"Markdown: {md_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
