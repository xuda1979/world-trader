"""RV mean-reversion backtest AT SCALE on real historical data.

Universe: 10 RV pairs from tools/wt/rv_setups.py
  - 4 yield-curve spreads (FRED): 2s10s, 2s30s, 5s30s, 3m10y
  - 6 FX cross spreads (Twelve Data): EUR/GBP, EUR/CHF, AUD/CAD, AUD/NZD, GBP/JPY, EUR/AUD

Cost model (user-specified, 2026-07-23):
  - IBKR commission per leg, per side:
      US equity: $0.0035/share, $0.35 min (we use notional-based bps equivalent)
      FX:        0.2 bp/side, $2 min on $20k  -> ~0.2 bp/side for $25k notional
      Yield:     treated as cash spread; we use the US equity schedule on $100k 2y-notional
  - Slippage: 0.3 bp per side (bid/ask crossing + market impact)
  - A spread trade has TWO legs, each round-tripped -> 4 sides total
    => round-trip cost = 4 * (commission_side + 0.3bp)

Walk-forward: 60% in-sample (rolling-z lookback tuning done in backtest_rv_mean_reversion),
40% out-of-sample.  The IS/OOS split is chronological (capital-preserving).

Output: per-pair tear-sheet + portfolio-level compounded equity curve.
"""
from __future__ import annotations
import os, sys, json, math, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.wt import altdata
from tools.wt.analysis import backtest_rv_mean_reversion, qualifies_rv

# ---------------------------------------------------------------- config
START_EQUITY        = 100_000.0
RISK_PER_TRADE      = 0.01      # 1% equity at 1-sigma spread risk
TRADE_NOTIONAL_USD  = 25_000.0  # per-leg notional for commission modeling
SLIPPAGE_BPS_SIDE   = 0.3       # user-specified: 0.3 bps per side
DEFAULT_BARS        = 1500      # ~6 years of daily bars
OOS_FRAC            = 0.40      # last 40% is out-of-sample

# IBKR commission per side, in bps of notional (Fixed plan, retail).
# These are *additive* to slippage.  A spread has TWO legs x TWO sides = 4 sides.
IBKR_COMM_BPS_SIDE = {
    "US":    1.0,    # ~$0.005/share on $50 stock, $25k notional = ~1.0 bp/side (Fixed plan)
    "FX":    0.8,    # $2 min on $25k = 0.8 bp/side for majors (IBKR retail)
    "YIELD": 0.5,    # ~0.5 bp/side on a Treasury cash-spread proxy
}


def round_trip_cost_bps(market: str) -> float:
    """Total round-trip cost in bps for a 2-leg spread trade.

    2 legs * 2 sides (buy+sell) = 4 sides.  Each side pays commission + slippage.
    """
    comm = IBKR_COMM_BPS_SIDE.get(market, IBKR_COMM_BPS_SIDE["US"])
    per_side = comm + SLIPPAGE_BPS_SIDE
    return 4.0 * per_side


def cost_frac(market: str) -> float:
    """Round-trip cost as a FRACTION of notional."""
    return round_trip_cost_bps(market) / 10000.0


# Sizing convention for RV: 1-sigma spread move = RISK_PER_TRADE of equity.
# A 2-leg spread trade notional is 2 * TRADE_NOTIONAL_USD.  Converting a
# notional-fraction cost to stdev units:
#   cost_stdev = (cost_frac * 2 * TRADE_NOTIONAL_USD) / (RISK_PER_TRADE * equity)
# Normalizing equity = TRADE_NOTIONAL_USD / RISK_PER_TRADE (i.e. one-leg notional
# is 1/RISK_PER_TRADE of equity), this simplifies to:
#   cost_stdev = cost_frac * 2 / RISK_PER_TRADE
# Prior code subtracted cost_frac directly from a stdev-unit PnL -- a unit
# mismatch that under-charged cost by ~50x for FX (rt_cost=0.000128) and ~20x
# for US (rt_cost=0.00032).
RV_LEGS = 2
def _rv_cost_stdev(cost_frac: float) -> float:
    """Convert a notional-fraction RT cost to spread-stdev units."""
    if cost_frac is None or cost_frac <= 0:
        return 0.0
    return float(cost_frac) * RV_LEGS / RISK_PER_TRADE


# ---------------------------------------------------------------- RV pair universe
# (label, kind, args, market-for-cost)
# FX pairs use FRED daily exchange-rate series (no API rate limit, unlike
# Twelve Data free tier).  FRED series:
#   DEXUSEU = EUR/USD (USD per EUR)
#   DEXUSUK = GBP/USD (USD per GBP)
#   DEXSZUS = USD/CHF (CHF per USD)
#   DEXUSAL = AUD/USD (USD per AUD)
#   DEXCAUS = USD/CAD (CAD per USD)
#   DEXUSNZ = NZD/USD (USD per NZD)
#   DEXJPUS = USD/JPY (JPY per USD)
RV_PAIRS = [
    # Yield curve spreads (basis points) — FRED daily
    ("2s10s",  "YIELD", ("DGS2",   "DGS10"), "YIELD"),
    ("2s30s",  "YIELD", ("DGS2",   "DGS30"), "YIELD"),
    ("5s30s",  "YIELD", ("DGS5",   "DGS30"), "YIELD"),
    ("3m10y",  "YIELD", ("DGS3MO", "DGS10"), "YIELD"),
    # FX cross spreads — FRED daily (DEX* series)
    ("EUR/GBP", "FX", ("DEXUSEU", "DEXUSUK"), "FX"),
    ("EUR/CHF", "FX", ("DEXUSEU", "DEXSZUS"), "FX"),
    ("AUD/CAD", "FX", ("DEXUSAL", "DEXCAUS"), "FX"),
    ("AUD/NZD", "FX", ("DEXUSAL", "DEXUSNZ"), "FX"),
    ("GBP/JPY", "FX", ("DEXUSUK", "DEXJPUS"), "FX"),
    ("EUR/AUD", "FX", ("DEXUSEU", "DEXUSAL"), "FX"),
]


# ---------------------------------------------------------------- data fetch
def _build_yield_spread(series_a: str, series_b: str, limit: int = DEFAULT_BARS):
    va, da, ea = altdata.fred_history(series_a, limit=limit)
    if ea: return None, None, f"{series_a}: {ea}"
    vb, db, eb = altdata.fred_history(series_b, limit=limit)
    if eb: return None, None, f"{series_b}: {eb}"
    if not va or not vb: return None, None, "no data"
    idx_b = {d: i for i, d in enumerate(db)}
    spread, dates = [], []
    for i, d in enumerate(da):
        if d in idx_b:
            spread.append(va[i] - vb[idx_b[d]])
            dates.append(d)
    if len(spread) < 80:
        return None, None, f"too few aligned obs ({len(spread)})"
    return spread, dates, None


def _build_fx_spread(series_a: str, series_b: str, limit: int = DEFAULT_BARS):
    """Build an FX cross spread from two FRED DEX* exchange-rate series.

    Both series are in "USD per 1 unit of foreign currency" (DEXUSEU, DEXUSUK,
    DEXUSAL, DEXUSNZ) EXCEPT DEXSZUS, DEXCAUS, DEXJPUS which are "foreign
    currency per 1 USD" (i.e., USD/CHF, USD/CAD, USD/JPY).  We subtract the
    two series directly; the spread is the difference between two FX rates
    in compatible units (a cross-rate basis).  This is exactly how the
    Twelve Data version worked (close_a - close_b).
    """
    va, da, ea = altdata.fred_history(series_a, limit=limit)
    if ea: return None, None, f"{series_a}: {ea}"
    vb, db, eb = altdata.fred_history(series_b, limit=limit)
    if eb: return None, None, f"{series_b}: {eb}"
    if not va or not vb: return None, None, "no data"
    idx_b = {d: i for i, d in enumerate(db)}
    spread, dates = [], []
    for i, d in enumerate(da):
        if d in idx_b:
            spread.append(va[i] - vb[idx_b[d]])
            dates.append(d)
    if len(spread) < 80:
        return None, None, f"too few aligned obs ({len(spread)})"
    return spread, dates, None


def build_spread(label: str, kind: str, args: tuple):
    if kind == "YIELD":
        return _build_yield_spread(*args, limit=DEFAULT_BARS)
    if kind == "FX":
        return _build_fx_spread(*args, limit=DEFAULT_BARS)
    return None, None, f"unknown kind {kind}"


# ---------------------------------------------------------------- backtest
@dataclass
class RVTrade:
    pair: str
    entry_bar: int
    exit_bar: int
    side: str           # "Long" or "Short"
    entry_z: float
    exit_z: float
    gross_ret: float    # in spread-stdev units
    cost_frac: float    # round-trip cost as fraction of notional
    net_ret: float      # gross_ret - cost_frac (in stdev units)
    pnl_usd: float
    equity_after: float
    in_oos: bool
    exit_reason: str = ""  # "tp", "sl", "time", "eod"


def _rolling_z(spread: list, i: int, lookback: int) -> Tuple[float, float, float]:
    """Return (z, mean, sd) for bar i using the prior `lookback` bars (causal)."""
    if i < lookback:
        return 0.0, 0.0, 0.0
    w = spread[i-lookback:i]
    m = sum(w) / lookback
    var = sum((x - m) ** 2 for x in w) / (lookback - 1)
    sd = math.sqrt(var) if var > 0 else 0.0
    z = (spread[i] - m) / sd if sd > 0 else 0.0
    return z, m, sd


def backtest_pair(label: str, spread: list, dates: list, market: str,
                  z_entry: float = 2.0, z_exit: float = 0.0,
                  horizon: int = 10, lookback: int = 60,
                  start_equity: float = START_EQUITY,
                  risk_per_trade: float = RISK_PER_TRADE) -> Optional[dict]:
    """Run the RV mean-reversion rule on a single spread, return trades + stats.

    Rule: at each bar i, compute rolling z over prior `lookback` bars.
      z < -z_entry  -> go LONG the spread (expect reversion up)
      z > +z_entry  -> go SHORT the spread
    Exit when z crosses z_exit (toward 0) or at `horizon` bars.
    PnL is in spread-stdev units; we size so 1-sigma spread move = risk_per_trade * equity.
    """
    N = len(spread)
    if N < lookback + horizon + 5:
        return None
    rt_cost = cost_frac(market)
    oos_split = int(N * (1 - OOS_FRAC))

    trades: List[RVTrade] = []
    equity = start_equity
    entries = []
    for i in range(lookback, N - 1):
        z, m, sd = _rolling_z(spread, i, lookback)
        if sd <= 0:
            continue
        if z < -z_entry:
            entries.append((i, 1, spread[i], sd))
        elif z > z_entry:
            entries.append((i, -1, spread[i], sd))

    if len(entries) < 5:
        return None

    for i, side, entry, esd in entries:
        outcome = None
        exit_bar = None
        exit_z = 0.0
        exit_reason = ""
        for j in range(i + 1, min(i + 1 + horizon, N)):
            zj, _, _ = _rolling_z(spread, j, lookback)
            d_stdev = (spread[j] - entry) / esd if esd > 0 else 0.0
            # FIX 2026-07-26 (Bug 9): exit on SPREAD move, not z move.
            #   (a) take profit: spread moved >= 1.0 stdev toward mean
            #   (b) stop loss:   spread moved >= 2.0 stdev against entry
            #   (c) time stop:   held for `horizon` bars without tp/sl
            if side * d_stdev >= 1.0:
                outcome = side * d_stdev
                exit_bar = j
                exit_z = zj
                exit_reason = "tp"
                break
            if side * d_stdev <= -2.0:
                outcome = side * d_stdev
                exit_bar = j
                exit_z = zj
                exit_reason = "sl"
                break
        if outcome is None:
            j = min(i + horizon, N - 1)
            outcome = side * (spread[j] - entry) / esd
            exit_bar = j
            exit_z, _, _ = _rolling_z(spread, j, lookback)
            exit_reason = "time"

        gross_ret = outcome  # in stdev units
        net_ret = gross_ret - _rv_cost_stdev(rt_cost)  # convert notional-frac to stdev units
        risk_usd = equity * risk_per_trade
        pnl = net_ret * risk_usd
        equity += pnl
        trades.append(RVTrade(
            pair=label, entry_bar=i, exit_bar=exit_bar,
            side="Long" if side == 1 else "Short",
            entry_z=(spread[i] - m) / esd if esd > 0 else 0.0,
            exit_z=exit_z,
            gross_ret=gross_ret, cost_frac=rt_cost, net_ret=net_ret,
            pnl_usd=pnl, equity_after=equity,
            in_oos=(i >= oos_split),
            exit_reason=exit_reason,
        ))
    if not trades:
        return None

    # split IS/OOS
    is_trades = [t for t in trades if not t.in_oos]
    oos_trades = [t for t in trades if t.in_oos]

    def stats(ts: List[RVTrade]) -> dict:
        if not ts:
            return {"n": 0}
        rets = [t.net_ret for t in ts]
        wins = [r for r in rets if r > 0]
        losses = [r for r in rets if r <= 0]
        n = len(rets)
        p_win = len(wins) / n
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        exp_ret = sum(rets) / n
        sd = statistics.pstdev(rets) if n > 1 else 0.0
        edge = exp_ret / sd if sd > 0 else 0.0
        se = sd / math.sqrt(n) if (sd and n > 1) else 0.0
        tstat = exp_ret / se if se > 0 else 0.0
        # max drawdown on cumulative rets
        cum = 0.0; peak = 0.0; mdd = 0.0
        for r in rets:
            cum += r
            if cum > peak: peak = cum
            dd = peak - cum
            if dd > mdd: mdd = dd
        # loss streak
        cur = 0; mx = 0
        for r in rets:
            if r < 0:
                cur += 1
                if cur > mx: mx = cur
            else:
                cur = 0
        return {
            "n": n, "p_win": p_win, "avg_win": avg_win, "avg_loss": avg_loss,
            "exp_ret": exp_ret, "sd": sd, "edge": edge, "tstat": tstat,
            "worst_trade": min(rets), "best_trade": max(rets),
            "max_dd": mdd, "max_loss_streak": mx,
            "total_pnl_usd": sum(t.pnl_usd for t in ts),
        }

    is_st = stats(is_trades)
    oos_st = stats(oos_trades)
    all_st = stats(trades)
    # equity curve (only at trade exits)
    eq_curve = [start_equity] + [t.equity_after for t in trades]
    return {
        "pair": label, "market": market, "n_bars": N, "oos_split_bar": oos_split,
        "rt_cost_bps": round_trip_cost_bps(market),
        "rt_cost_frac": rt_cost,
        "lookback": lookback, "z_entry": z_entry, "z_exit": z_exit,
        "horizon": horizon,
        "is": is_st, "oos": oos_st, "all": all_st,
        "trades": trades,
        "equity_curve": eq_curve,
        "final_equity": equity,
        "total_return": (equity / start_equity - 1.0),
    }


# ---------------------------------------------------------------- portfolio
def run_portfolio(pairs=RV_PAIRS, start_equity=START_EQUITY,
                  risk_per_trade=RISK_PER_TRADE, workers=3) -> Tuple[List[dict], List[str]]:
    """Run the RV backtest on all pairs in parallel and compound into ONE
    portfolio equity curve (each pair sized at risk_per_trade of portfolio
    equity at entry time)."""
    results, errors = [], []

    def one(p):
        label, kind, args, market = p
        spread, dates, err = build_spread(label, kind, args)
        if err:
            return label, None, err
        r = backtest_pair(label, spread, dates, market,
                          start_equity=start_equity,
                          risk_per_trade=risk_per_trade)
        if not r:
            return label, None, "no backtest (insufficient samples)"
        return label, r, None

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(one, p): p for p in pairs}
        for fut in as_completed(futs):
            label, r, err = fut.result()
            if r:
                results.append(r)
            elif err:
                errors.append(f"{label}: {err}")
    return results, errors


def portfolio_equity_curve(results: List[dict], start_equity=START_EQUITY,
                           risk_per_trade=RISK_PER_TRADE) -> Tuple[List[float], List[RVTrade]]:
    """Compound ALL pairs into ONE portfolio equity curve.

    Each pair's trades were sized off the *pair-level* start_equity; to build a
    true portfolio curve we re-size each trade off the running portfolio equity.
    We assume trades across pairs are approximately non-overlapping (RV horizon
    is 10 bars; FX and yields fire on different days).  For overlapping bars we
    still compound sequentially -- this slightly understates the equity when
    multiple positions are open simultaneously (conservative)."""
    all_trades: List[RVTrade] = []
    for r in results:
        for t in r["trades"]:
            all_trades.append(t)
    # sort by entry bar
    all_trades.sort(key=lambda t: (t.entry_bar, t.pair))
    equity = start_equity
    curve = [equity]
    bars = [0]
    for t in all_trades:
        # re-size PnL off running portfolio equity
        # original pnl was sized off pair-level start_equity; scale linearly
        scale = equity / START_EQUITY
        equity += t.pnl_usd * scale
        curve.append(equity)
        bars.append(t.entry_bar)
    return curve, all_trades


def portfolio_stats(curve: List[float], trades: List[RVTrade], start_equity=START_EQUITY) -> dict:
    if not trades:
        return {"n_trades": 0, "n": 0, "p_win": 0.0, "avg_win": 0.0,
                "avg_loss": 0.0, "exp_ret_per_trade": 0.0, "sd_per_trade": 0.0,
                "per_trade_sharpe": 0.0, "t_stat": 0.0, "total_return": 0.0,
                "final_equity": start_equity, "max_drawdown": 0.0,
                "max_dd_peak_bar": 0, "max_dd_trough_bar": 0, "years": 0.0,
                "trades_per_year": 0.0, "cagr": 0.0, "ann_sharpe": 0.0,
                "calmar": 0.0, "total_pnl_usd": 0.0, "worst_trade": 0.0,
                "best_trade": 0.0}
    eq = curve
    total_ret = (eq[-1] / eq[0] - 1.0) if eq[0] > 0 else 0.0
    # max drawdown
    peak = eq[0]; mdd = 0.0; pi = 0; ti = 0; m_pi = 0; m_ti = 0
    for i, v in enumerate(eq):
        if v > peak:
            peak = v; pi = i
        if peak > 0:
            dd = 1.0 - v / peak
            if dd > mdd:
                mdd = dd; m_pi = pi; m_ti = i
    # per-trade stats
    rets = [t.net_ret for t in trades]
    n = len(rets)
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    p_win = len(wins) / n if n else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    exp_ret = sum(rets) / n if n else 0.0
    sd = statistics.pstdev(rets) if n > 1 else 0.0
    edge = exp_ret / sd if sd > 0 else 0.0
    se = sd / math.sqrt(n) if (sd and n > 1) else 0.0
    tstat = exp_ret / se if se > 0 else 0.0
    # annualized return: ~252 trading days; avg holding ~5 bars; estimate years
    last_bar = max(t.exit_bar for t in trades) if trades else 1
    years = max(last_bar / 252.0, 0.1)
    cagr = (eq[-1] / eq[0]) ** (1.0 / years) - 1.0 if eq[0] > 0 and years > 0 else 0.0
    # Sharpe (per-trade * sqrt(trades_per_year))
    trades_per_year = n / years if years > 0 else 0.0
    ann_sharpe = edge * math.sqrt(trades_per_year) if trades_per_year > 0 else 0.0
    calmar = cagr / mdd if mdd > 0 else 0.0
    return {
        "n_trades": n, "p_win": p_win, "avg_win": avg_win, "avg_loss": avg_loss,
        "exp_ret_per_trade": exp_ret, "sd_per_trade": sd,
        "per_trade_sharpe": edge, "t_stat": tstat,
        "total_return": total_ret, "final_equity": eq[-1],
        "max_drawdown": mdd, "max_dd_peak_bar": m_pi, "max_dd_trough_bar": m_ti,
        "years": years, "trades_per_year": trades_per_year,
        "cagr": cagr, "ann_sharpe": ann_sharpe, "calmar": calmar,
        "total_pnl_usd": eq[-1] - start_equity,
        "worst_trade": min(rets) if rets else 0.0,
        "best_trade": max(rets) if rets else 0.0,
    }


# ---------------------------------------------------------------- reporting
def fmt_pct(x, digits=2):
    return f"{x*100:.{digits}f}%"


def fmt_bp(x, digits=1):
    return f"{x:.{digits}f}bp"


def print_per_pair(results: List[dict]):
    print(f"\n{'Pair':10s} {'mkt':5s} {'rtcost':>7s} {'IS_n':>5s} {'IS_sh':>6s} "
          f"{'OOS_n':>5s} {'OOS_sh':>6s} {'OOS_pwin':>8s} {'OOS_pnl$':>10s} "
          f"{'final_eq$':>11s} {'tot_ret':>8s}")
    print("-" * 95)
    for r in sorted(results, key=lambda x: -(x["oos"].get("edge") or 0)):
        is_st = r["is"]; oos_st = r["oos"]
        oos_edge = oos_st.get("edge", 0) if oos_st.get("n") else 0
        oos_pwin = oos_st.get("p_win", 0) if oos_st.get("n") else 0
        oos_pnl = oos_st.get("total_pnl_usd", 0) if oos_st.get("n") else 0
        is_n = is_st.get("n", 0)
        oos_n = oos_st.get("n", 0)
        print(f"{r['pair']:10s} {r['market']:5s} {fmt_bp(r['rt_cost_bps']):>7s} "
              f"{is_n:>5d} {is_st.get('edge',0):>6.2f} "
              f"{oos_n:>5d} {oos_edge:>6.2f} {fmt_pct(oos_pwin):>8s} "
              f"{oos_pnl:>10.0f} {r['final_equity']:>11.0f} "
              f"{fmt_pct(r['total_return']):>8s}")


def print_portfolio(port_stats: dict):
    print("\n" + "=" * 72)
    print("PORTFOLIO TEAR-SHEET (10 RV pairs, compounded)")
    print("=" * 72)
    print(f"  Trades:            {port_stats['n_trades']}")
    print(f"  Win rate:          {fmt_pct(port_stats['p_win'])}")
    print(f"  Avg win:           {port_stats['avg_win']:+.3f} stdev")
    print(f"  Avg loss:          {port_stats['avg_loss']:+.3f} stdev")
    print(f"  Exp/trade:         {port_stats['exp_ret_per_trade']:+.3f} stdev")
    print(f"  SD/trade:          {port_stats['sd_per_trade']:.3f} stdev")
    print(f"  Per-trade Sharpe:  {port_stats['per_trade_sharpe']:+.2f}")
    print(f"  t-stat:            {port_stats['t_stat']:+.2f}")
    print(f"  Total return:      {fmt_pct(port_stats['total_return'])}")
    print(f"  Final equity:      ${port_stats['final_equity']:,.0f}")
    print(f"  Max drawdown:      {fmt_pct(port_stats['max_drawdown'])}")
    print(f"  Years (est):       {port_stats['years']:.1f}")
    print(f"  Trades/year:       {port_stats['trades_per_year']:.1f}")
    print(f"  CAGR:              {fmt_pct(port_stats['cagr'])}")
    print(f"  Ann. Sharpe:       {port_stats['ann_sharpe']:+.2f}")
    print(f"  Calmar:            {port_stats['calmar']:+.2f}")
    print(f"  Total PnL:         ${port_stats['total_pnl_usd']:,.0f}")
    print(f"  Worst trade:       {port_stats['worst_trade']:+.3f} stdev")
    print(f"  Best trade:        {port_stats['best_trade']:+.3f} stdev")


# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    print("=" * 72, file=sys.stderr)
    print("RV MEAN-REVERSION BACKTEST AT SCALE (REAL DATA)", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(f"  Universe:     {len(RV_PAIRS)} RV pairs (4 yield + 6 FX)", file=sys.stderr)
    print(f"  Data:         FRED (yields + FX DEX* series), {DEFAULT_BARS} bars", file=sys.stderr)
    print(f"  IS/OOS:       {1-OOS_FRAC:.0%}/{OOS_FRAC:.0%} chronological split", file=sys.stderr)
    print(f"  Commission:   IBKR Fixed (US $0.0035/sh min $0.35; FX 0.2bp/side)", file=sys.stderr)
    print(f"  Slippage:     {SLIPPAGE_BPS_SIDE} bp/side (user-specified)", file=sys.stderr)
    print(f"  RT cost:      YIELD={fmt_bp(round_trip_cost_bps('YIELD'))}, "
          f"FX={fmt_bp(round_trip_cost_bps('FX'))}", file=sys.stderr)
    print(f"  Risk/trade:   {fmt_pct(RISK_PER_TRADE)} of equity at 1-sigma", file=sys.stderr)
    print(f"  Start equity: ${START_EQUITY:,.0f}\n", file=sys.stderr)

    results, errors = run_portfolio()
    print(f"\nFetched & backtested {len(results)}/{len(RV_PAIRS)} pairs in "
          f"{time.time()-t0:.1f}s", file=sys.stderr)
    if errors:
        print(f"  Errors: {len(errors)}", file=sys.stderr)
        for e in errors[:10]:
            print(f"    {e}", file=sys.stderr)

    # per-pair table
    print_per_pair(results)

    # portfolio-level compounded curve
    port_curve, all_trades = portfolio_equity_curve(results)
    port_st = portfolio_stats(port_curve, all_trades)
    print_portfolio(port_st)

    # IS/OOS breakdown for portfolio
    is_trades = [t for t in all_trades if not t.in_oos]
    oos_trades = [t for t in all_trades if t.in_oos]
    print(f"\n  IS trades:         {len(is_trades)}  "
          f"(exp/trade {sum(t.net_ret for t in is_trades)/max(len(is_trades),1):+.3f} stdev)")
    print(f"  OOS trades:        {len(oos_trades)}  "
          f"(exp/trade {sum(t.net_ret for t in oos_trades)/max(len(oos_trades),1):+.3f} stdev)")

    # save report
    out_dir = os.path.join(ROOT, "tools", "quant", "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rv_scale_backtest.json")
    rep = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_s": round(time.time() - t0, 1),
        "config": {
            "start_equity": START_EQUITY,
            "risk_per_trade": RISK_PER_TRADE,
            "slippage_bps_side": SLIPPAGE_BPS_SIDE,
            "ibkr_comm_bps_side": IBKR_COMM_BPS_SIDE,
            "rt_cost_bps": {m: round_trip_cost_bps(m) for m in ["US", "FX", "YIELD"]},
            "default_bars": DEFAULT_BARS,
            "oos_frac": OOS_FRAC,
            "lookback": 60, "z_entry": 2.0, "z_exit": 0.0, "horizon": 10,
        },
        "per_pair": [{
            "pair": r["pair"], "market": r["market"],
            "n_bars": r["n_bars"], "rt_cost_bps": r["rt_cost_bps"],
            "is": {k: (round(v, 4) if isinstance(v, float) else v)
                   for k, v in r["is"].items()},
            "oos": {k: (round(v, 4) if isinstance(v, float) else v)
                    for k, v in r["oos"].items()},
            "all": {k: (round(v, 4) if isinstance(v, float) else v)
                    for k, v in r["all"].items()},
            "final_equity": round(r["final_equity"], 2),
            "total_return": round(r["total_return"], 4),
        } for r in results],
        "portfolio": {k: (round(v, 4) if isinstance(v, float) else v)
                      for k, v in port_st.items()},
        "errors": errors,
    }
    with open(out_path, "w") as f:
        json.dump(rep, f, indent=2)
    print(f"\nReport: {out_path}", file=sys.stderr)

    # markdown tear-sheet
    md_path = os.path.join(out_dir, "rv_scale_backtest.md")
    with open(md_path, "w") as f:
        f.write("# RV Mean-Reversion Backtest at Scale (Real Data)\n\n")
        f.write(f"Generated: {rep['generated']}  |  Elapsed: {rep['elapsed_s']}s\n\n")
        f.write("## Methodology\n\n")
        f.write(f"- **Universe**: {len(RV_PAIRS)} RV pairs "
                f"(4 yield-curve spreads + 6 FX crosses, all via FRED)\n")
        f.write(f"- **Data**: real daily history, ~{DEFAULT_BARS} bars (~6 years)\n")
        f.write(f"- **Walk-forward**: 60% IS / 40% OOS chronological split\n")
        f.write(f"- **Signal**: rolling z-score over prior {60} bars, enter at |z|>2.0, "
                f"exit at z crosses 0, max hold 10 bars\n")
        f.write(f"- **Sizing**: 1% equity at 1-sigma spread move\n")
        f.write(f"- **Commission**: IBKR Fixed (FX 0.2bp/side, YIELD 0.05bp/side)\n")
        f.write(f"- **Slippage**: {SLIPPAGE_BPS_SIDE} bp/side (user-specified)\n")
        f.write(f"- **Round-trip cost**: FX={round_trip_cost_bps('FX'):.2f}bp, "
                f"YIELD={round_trip_cost_bps('YIELD'):.2f}bp "
                f"(2 legs x 2 sides x (comm+slip))\n\n")
        f.write("## Per-Pair Results (sorted by OOS Sharpe)\n\n")
        f.write("| Pair | Mkt | RT cost | IS n | IS Sharpe | OOS n | OOS Sharpe | "
                "OOS Win% | OOS PnL $ | Final Eq $ | Total Ret |\n")
        f.write("|------|-----|---------|------|-----------|-------|------------|"
                "----------|-----------|------------|-----------|\n")
        for p in sorted(rep["per_pair"], key=lambda x: -(x["oos"].get("edge") or 0)):
            is_s = p["is"]; oos_s = p["oos"]
            f.write(f"| {p['pair']} | {p['market']} | {p['rt_cost_bps']:.2f}bp | "
                    f"{is_s['n']} | {is_s.get('edge',0):+.2f} | "
                    f"{oos_s.get('n',0)} | {(oos_s.get('edge',0) or 0):+.2f} | "
                    f"{((oos_s.get('p_win',0) or 0)*100):.1f}% | "
                    f"${oos_s.get('total_pnl_usd',0) or 0:,.0f} | "
                    f"${p['final_equity']:,.0f} | "
                    f"{p['total_return']*100:+.1f}% |\n")
        f.write("\n## Portfolio Tear-Sheet (compounded across all 10 pairs)\n\n")
        ps = rep["portfolio"]
        f.write("| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Trades | {ps['n_trades']:,} |\n")
        f.write(f"| Win rate | {ps['p_win']*100:.1f}% |\n")
        f.write(f"| Avg win | {ps['avg_win']:+.3f} stdev |\n")
        f.write(f"| Avg loss | {ps['avg_loss']:+.3f} stdev |\n")
        f.write(f"| Exp/trade | {ps['exp_ret_per_trade']:+.3f} stdev |\n")
        f.write(f"| SD/trade | {ps['sd_per_trade']:.3f} stdev |\n")
        f.write(f"| Per-trade Sharpe | {ps['per_trade_sharpe']:+.2f} |\n")
        f.write(f"| t-stat | {ps['t_stat']:+.2f} |\n")
        f.write(f"| Total return | {ps['total_return']*100:+.1f}% |\n")
        f.write(f"| Final equity | ${ps['final_equity']:,.0f} |\n")
        f.write(f"| Max drawdown | {ps['max_drawdown']*100:.1f}% |\n")
        f.write(f"| Years (est) | {ps['years']:.1f} |\n")
        f.write(f"| Trades/year | {ps['trades_per_year']:.1f} |\n")
        f.write(f"| CAGR | {ps['cagr']*100:+.1f}% |\n")
        f.write(f"| Ann. Sharpe | {ps['ann_sharpe']:+.2f} |\n")
        f.write(f"| Calmar | {ps['calmar']:+.2f} |\n")
        f.write(f"| Total PnL | ${ps['total_pnl_usd']:,.0f} |\n")
        f.write(f"| Worst trade | {ps['worst_trade']:+.3f} stdev |\n")
        f.write(f"| Best trade | {ps['best_trade']:+.3f} stdev |\n\n")
        n_is = len([t for t in all_trades if not t.in_oos])
        n_oos = len([t for t in all_trades if t.in_oos])
        is_exp = sum(t.net_ret for t in all_trades if not t.in_oos) / max(n_is, 1)
        oos_exp = sum(t.net_ret for t in all_trades if t.in_oos) / max(n_oos, 1)
        f.write(f"**IS/OOS split**: {n_is} IS trades (exp/trade {is_exp:+.3f} stdev), "
                f"{n_oos} OOS trades (exp/trade {oos_exp:+.3f} stdev)\n\n")
        f.write("## Key Findings\n\n")
        pos_oos = [p for p in rep["per_pair"] if (p["oos"].get("edge") or 0) > 0]
        neg_oos = [p for p in rep["per_pair"] if (p["oos"].get("edge") or 0) <= 0]
        f.write(f"- **{len(pos_oos)}/{len(rep['per_pair'])} pairs have positive OOS Sharpe**; "
                f"{len(neg_oos)} have non-positive.\n")
        fx_pos = [p for p in pos_oos if p["market"] == "FX"]
        yld_pos = [p for p in pos_oos if p["market"] == "YIELD"]
        fx_all = [p for p in rep["per_pair"] if p["market"] == "FX"]
        yld_all = [p for p in rep["per_pair"] if p["market"] == "YIELD"]
        if fx_all:
            if fx_pos:
                fxb = max(fx_pos, key=lambda x: x["oos"].get("edge") or 0)
                f.write(f"- **FX pairs**: {len(fx_pos)}/{len(fx_all)} positive OOS Sharpe.  "
                        f"Best: {fxb['pair']} (+{fxb['oos']['edge']:.2f}).\n")
            else:
                fxb = max(fx_all, key=lambda x: x["oos"].get("edge") or -9)
                f.write(f"- **FX pairs**: 0/{len(fx_all)} positive OOS Sharpe.  "
                        f"Best (least bad): {fxb['pair']} ({fxb['oos'].get('edge',0):+.2f}).\n")
        if yld_all:
            if yld_pos:
                yb = max(yld_pos, key=lambda x: x["oos"].get("edge") or 0)
                f.write(f"- **Yield pairs**: {len(yld_pos)}/{len(yld_all)} positive OOS Sharpe.  "
                        f"Best OOS: {yb['pair']} ({yb['oos'].get('edge',0):+.2f}).\n")
            else:
                yb = max(yld_all, key=lambda x: x["oos"].get("edge") or -9)
                f.write(f"- **Yield pairs**: 0/{len(yld_all)} positive OOS Sharpe.  "
                        f"Best (least bad): {yb['pair']} ({yb['oos'].get('edge',0):+.2f}).\n")
        f.write(f"- **Portfolio max DD = {ps['max_drawdown']*100:.1f}%** — "
                f"**UNTRADEABLE as-is**.  Despite a 2-stdev stop-loss (added "
                f"2026-07-26), yield-curve trades can still move 4+ stdev "
                f"against before the stop triggers.\n")
        f.write(f"- **CAGR {ps['cagr']*100:+.1f}% / Ann Sharpe {ps['ann_sharpe']:+.2f}** "
                f"is DOMINATED by the {ps['max_drawdown']*100:.0f}% DD — Calmar "
                f"{ps['calmar']:+.2f} confirms risk-adjusted return is poor.\n")
        tpy = ps['trades_per_year']
        avg_rt_bp = (round_trip_cost_bps('FX') + round_trip_cost_bps('YIELD')) / 2.0
        f.write(f"- **Cost impact**: at ~{avg_rt_bp:.1f}bp RT per trade and ~{tpy:.0f} trades/year, "
                f"cost drag ~{(avg_rt_bp/10000)*tpy*100:.1f}%/year — small relative to "
                f"signal variance but meaningful for low-edge pairs.\n")
    print(f"Markdown: {md_path}", file=sys.stderr)
    return results, errors, port_st


if __name__ == "__main__":
    main()
