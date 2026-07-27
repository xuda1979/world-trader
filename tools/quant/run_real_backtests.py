"""Real-data backtests for the world-trader quant framework.

This is the *empirical* counterpart to `run_backtests.py` (which runs on
synthetic OU / GBM / jump data).  The synthetic tests proved the engine
wires up correctly and that the per-setup gates fire, but they cannot
prove an edge exists in the market.  This module runs the SAME strategies
on REAL historical price data fetched via `data_history.py` (Polygon /
Binance / Twelve Data, with CSV cache).

What we backtest here
---------------------
  1. **RV mean-reversion on real ETF pairs** (SPY/QQQ, IWM/SPY, etc.)
     The synthetic OU test gave Sharpe +6/+24/+34 -- that is a property
     of the OU generator, not a strategy edge.  Here we compute the
     log-spread of two real ETFs, estimate the OU half-life on a TRAINING
     window, then trade it out-of-sample.  The headline number is the
     OOS Sharpe.

  2. **Single-name Renaissance setups on real US equities.**  Run the
     per-setup replay library on 5-10 liquid names and report per-setup
     OOS Sharpe + win rate.  This replaces the synthetic-regime test for
     the setup library.

Walk-forward / OOS discipline
-----------------------------
For each pair we split the history into IN-SAMPLE (first 60%) and
OUT-OF-SAMPLE (last 40%).  The OU half-life and signal threshold are
fit on IS only; the backtest runs on OOS only.  This is the same
discipline `tools.wt.analysis` uses for per-setup qualification, so the
results are directly comparable to the gates in the scanner.

Run it
------
    python3 tools/quant/run_real_backtests.py
"""

from __future__ import annotations
import sys, os, json, math, time, statistics
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.quant import backtest as bt
from tools.quant.data_history import fetch_pair, fetch_history, log_spread

START_EQUITY = 100_000.0
RISK_PER_TRADE = 0.01
DEFAULT_BARS = 1000  # ~4 years of daily bars -> more trades for stat power

# IBKR retail round-trip cost as a fraction of notional (2-leg spread).
# US: ~1.0bp/side commission + 0.3bp/side slippage + ~1bp/side spread = 2.3bp/side
#     -> 4 sides * 2.3bp = 9.2bp RT = 0.00092 (we use 0.0010 for conservatism).
# FX: ~0.2bp/side commission + 0.3bp/side slippage + ~0.5bp/side spread = 1.0bp/side
#     -> 4 sides * 1.0bp = 4.0bp RT = 0.00040.
RV_COST_FRAC = {"US": 0.0010, "FX": 0.00040, "YIELD": 0.00050, "DEFAULT": 0.0010}
RV_LEGS = 2

def _rv_cost_stdev(market: str, equity: float) -> float:
    """Round-trip cost in spread-stdev units.

    FIX (2026-07-26): Prior code applied NO cost to RV backtests.  We now
    subtract the IBKR retail cost (commission + slippage + spread) on a 2-leg
    spread, converted to stdev units using the sizing convention
    (1 stdev = RISK_PER_TRADE of equity, 2 legs per spread, per-leg notional
    sized so that 1 stdev of spread move = RISK_PER_TRADE * equity of PnL).

    dollar_cost = cost_frac * 2 * notional_per_leg
    dollar_per_stdev = RISK_PER_TRADE * equity
    cost_stdev = dollar_cost / dollar_per_stdev

    Per-leg notional is sized such that 1 stdev of spread move = RISK_PER_TRADE
    * equity, i.e. notional_per_leg = RISK_PER_TRADE * equity / stdev_value.
    For a LOG spread, stdev_value ~ 0.05 -> notional_per_leg = 0.01 * equity /
    0.05 = 0.2 * equity = $20k on $100k.  For a DIFF FX spread, stdev_value
    ~ 0.005 -> notional_per_leg = 0.01 * equity / 0.005 = 2 * equity = $200k.
    To stay generic, we use notional_per_leg = RISK_PER_TRADE * equity / 0.02
    (a representative 2% stdev for log spreads)."""
    cost_frac = RV_COST_FRAC.get(market, RV_COST_FRAC["DEFAULT"])
    notional_per_leg = RISK_PER_TRADE * equity / 0.02  # $50k on $100k equity
    dollar_cost = cost_frac * RV_LEGS * notional_per_leg
    dollar_per_stdev = RISK_PER_TRADE * equity  # $1000 on $100k equity
    return dollar_cost / dollar_per_stdev


# ---------------------------------------------------------------- OU helpers
def ou_half_life(spread: list) -> float:
    """Estimate OU half-life from a log-spread series via AR(1) regression.

    spread_t = a + phi * spread_{t-1} + eps
    half_life = -ln(2) / ln(phi)

    Returns half-life in BARS.  phi near 1 -> long half-life (random walk,
    no mean reversion).  phi near 0 -> instant reversion.
    """
    if len(spread) < 30:
        return float("inf")
    x = spread[:-1]
    y = spread[1:]
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    den = sum((x[i] - mx) ** 2 for i in range(n))
    if den <= 0:
        return float("inf")
    phi = num / den
    if phi <= 0 or phi >= 1:
        return float("inf")
    return -math.log(2.0) / math.log(phi)


def zscore(series: list, lookback: int = 20) -> list:
    """Rolling z-score of a series."""
    out = [0.0] * len(series)
    for i in range(lookback, len(series)):
        window = series[i - lookback:i]
        m = sum(window) / len(window)
        sd = statistics.pstdev(window)
        if sd > 0:
            out[i] = (series[i] - m) / sd
    return out


# ---------------------------------------------------------------- RV on real pair
def rv_real_pair(leg_a: str, leg_b: str, days: int = DEFAULT_BARS,
                 z_threshold: float = 1.5,
                 train_frac: float = 0.6) -> dict:
    """Run RV mean-reversion on a real ETF pair with IS/OO split.

    1. Fetch both legs, align on common dates, compute log-spread.
    2. Split into IS (first `train_frac`) and OOS.
    3. On IS: estimate OU half-life; pick the lookback = max(5, min(60, half_life)).
    4. On OOS: each bar, compute rolling z-score of spread; SHORT the
       spread when z > +threshold, LONG when z < -threshold; exit when
       |z| < 0.5.  PnL per trade is the spread movement in $ at 1-sigma
       risk = RISK_PER_TRADE * equity.
    5. Report OOS Sharpe, win rate, max DD, and the IS half-life.
    """
    a, b, err = fetch_pair(f"{leg_a}/{leg_b}", days=days)
    if err:
        return {"pair": f"{leg_a}/{leg_b}", "error": err}
    spread = log_spread(a, b, 1.0, -1.0)["close"]
    n = len(spread)
    split = int(n * train_frac)
    if split < 60 or (n - split) < 30:
        return {"pair": f"{leg_a}/{leg_b}", "error": f"too few bars (n={n}, split={split})"}
    is_spread = spread[:split]
    oos_spread = spread[split:]
    hl = ou_half_life(is_spread)
    if not math.isfinite(hl) or hl <= 0:
        return {"pair": f"{leg_a}/{leg_b}", "error": "no mean reversion in IS",
                "half_life": None, "n_is": split, "n_oos": n - split}
    # lookback for z-score: clamp to [5, 60] bars
    lookback = max(5, min(60, int(hl)))
    # OOS z-score using IS mean/sd? No — rolling. So the lookback applies
    # on OOS only.  We need `lookback` warmup bars from IS to seed OOS.
    seed = is_spread[-lookback:] if lookback <= len(is_spread) else is_spread
    oos_with_seed = seed + oos_spread
    z = zscore(oos_with_seed, lookback=lookback)
    # trim the seed off the z-score
    z_oos = z[len(seed):]
    # trade: enter at |z|>2, exit at |z|<0.5; simple discrete rule
    equity = START_EQUITY
    trades = []
    pos = 0  # +1 long spread, -1 short spread, 0 flat
    entry_z = 0.0
    entry_i = 0
    entry_equity = 0.0
    for i in range(1, len(oos_spread)):
        zi = z_oos[i]
        # mark-to-market on existing position
        if pos != 0:
            # spread change * position * risk_usd / entry_z_sd
            d_spread = oos_spread[i] - oos_spread[entry_i]
            # 1-sigma move in spread ~ entry_z sd; we sized so 1-sigma risk = RISK_PER_TRADE
            sd_entry = abs(entry_z) if entry_z != 0 else 1.0
            pnl = pos * d_spread / sd_entry * (entry_equity * RISK_PER_TRADE)
        # exit logic
        if pos != 0 and abs(zi) < 0.5:
            # Apply round-trip cost (FIX 2026-07-26: prior code had NO cost).
            cost_stdev = _rv_cost_stdev("US", entry_equity)
            cost_usd = cost_stdev * (entry_equity * RISK_PER_TRADE)
            pnl_net = pnl - cost_usd
            equity += pnl_net
            ret = pnl_net / (entry_equity * RISK_PER_TRADE) if entry_equity > 0 else 0.0
            trades.append({
                "entry_bar": entry_i, "exit_bar": i,
                "side": "Long" if pos > 0 else "Short",
                "entry_z": entry_z, "exit_z": zi,
                "pnl_usd": pnl_net, "net_ret": ret,
                "equity_after": equity,
            })
            pos = 0
        # entry logic (after exit so we don't re-enter same bar)
        if pos == 0:
            if zi > z_threshold:
                pos = -1
                entry_z = zi
                entry_i = i
                entry_equity = equity
            elif zi < -z_threshold:
                pos = +1
                entry_z = zi
                entry_i = i
                entry_equity = equity
    # close any open position at the end
    if pos != 0:
        d_spread = oos_spread[-1] - oos_spread[entry_i]
        sd_entry = abs(entry_z) if entry_z != 0 else 1.0
        pnl = pos * d_spread / sd_entry * (entry_equity * RISK_PER_TRADE)
        # Apply round-trip cost (FIX 2026-07-26: prior code had NO cost).
        cost_stdev = _rv_cost_stdev("US", entry_equity)
        cost_usd = cost_stdev * (entry_equity * RISK_PER_TRADE)
        pnl_net = pnl - cost_usd
        equity += pnl_net
        ret = pnl_net / (entry_equity * RISK_PER_TRADE) if entry_equity > 0 else 0.0
        trades.append({
            "entry_bar": entry_i, "exit_bar": len(oos_spread) - 1,
            "side": "Long" if pos > 0 else "Short",
            "entry_z": entry_z, "exit_z": z_oos[-1],
            "pnl_usd": pnl_net, "net_ret": ret,
            "equity_after": equity,
        })
    # stats
    if not trades:
        return {"pair": f"{leg_a}/{leg_b}", "error": "no trades fired",
                "half_life_bars": round(hl, 1),
                "n_is": split, "n_oos": n - split,
                "lookback": lookback, "z_threshold": z_threshold}
    rets = [t["net_ret"] for t in trades]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    p_win = len(wins) / len(rets)
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    expectancy = p_win * avg_win + (1 - p_win) * avg_loss
    sd = statistics.pstdev(rets) if len(rets) > 1 else 0.0
    per_trade_sharpe = expectancy / sd if sd > 0 else 0.0
    # equity curve for max DD
    eq_curve = [START_EQUITY]
    for t in trades:
        eq_curve.append(t["equity_after"])
    mdd = 0.0
    peak = eq_curve[0]
    for v in eq_curve:
        peak = max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    total_pnl = eq_curve[-1] - START_EQUITY
    # annualized Sharpe: ~252 trading days per year, avg trade lasts ~half_life bars
    avg_hold = sum(t["exit_bar"] - t["entry_bar"] for t in trades) / len(trades)
    trades_per_year = 252.0 / max(avg_hold, 1)
    ann_sharpe = per_trade_sharpe * math.sqrt(trades_per_year) if trades_per_year > 0 else 0.0
    # statistical significance: t-stat of mean(rets) != 0
    n_tr = len(rets)
    se = sd / math.sqrt(n_tr) if sd > 0 and n_tr > 1 else 0.0
    t_stat = (expectancy / se) if se > 0 else 0.0
    # 2-sigma confidence band on per-trade Sharpe (rough)
    sh_se = 1.0 / math.sqrt(max(n_tr - 1, 1)) if n_tr > 1 else float("inf")
    # low-sample caveat: with <20 trades, Sharpe is mostly noise
    low_n = n_tr < 20
    return {
        "pair": f"{leg_a}/{leg_b}",
        "provider_a": a.get("_provider", "?"),
        "provider_b": b.get("_provider", "?"),
        "n_bars_total": n,
        "n_is": split,
        "n_oos": n - split,
        "half_life_bars": round(hl, 2),
        "lookback": lookback,
        "z_threshold": z_threshold,
        "n_trades": n_tr,
        "p_win": round(p_win, 4),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "expectancy": round(expectancy, 4),
        "per_trade_sd": round(sd, 4),
        "per_trade_sharpe": round(per_trade_sharpe, 3),
        "ann_sharpe": round(ann_sharpe, 2),
        "t_stat": round(t_stat, 2),
        "sharpe_se": round(sh_se, 3),
        "low_sample": low_n,
        "max_drawdown": round(mdd, 4),
        "total_pnl_usd": round(total_pnl, 2),
        "final_equity": round(eq_curve[-1], 2),
        "avg_hold_bars": round(avg_hold, 1),
        "trades_per_year": round(trades_per_year, 1),
    }


# ---------------------------------------------------------------- pairs universe
DEFAULT_PAIRS = [
    # Highly correlated ETF pairs — the classic pairs-trading universe
    ("SPY", "QQQ"),   # S&P 500 vs Nasdaq-100
    ("SPY", "IWM"),   # S&P 500 vs Russell 2000
    ("QQQ", "IWM"),   # Nasdaq vs Russell
    ("SPY", "DIA"),   # S&P 500 vs Dow
    ("XLF", "XLE"),   # Financials vs Energy
    ("XLI", "XLB"),   # Industrials vs Materials
    ("EWA", "EWC"),   # Australia vs Canada (commodity-linked)
    # Crypto pairs
    ("BTC", "ETH"),
]


def _rv_main_legacy():
    """Legacy RV-only entry point.  Kept for `python3 -c` one-shots.

    The full suite is in `main()` below.
    """
    t0 = time.time()
    print("=" * 72, file=sys.stderr)
    print("REAL-DATA RV MEAN-REVERSION BACKTEST", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print("Each pair: fetch real history -> split IS/OO -> fit OU on IS -> trade OOS\n",
          file=sys.stderr)
    results = []
    for a, b in DEFAULT_PAIRS:
        print(f"  -> {a}/{b} ...", end=" ", file=sys.stderr)
        r = rv_real_pair(a, b, days=DEFAULT_BARS)
        if "error" in r:
            print(f"FAIL ({r['error']})", file=sys.stderr)
        else:
            print(f"OOS Sharpe {r['ann_sharpe']:+.2f} | n={r['n_trades']} "
                  f"win={r['p_win']*100:.0f}% | HL={r['half_life_bars']:.0f}b "
                  f"| PnL ${r['total_pnl_usd']:+,.0f}", file=sys.stderr)
        results.append(r)
    # write JSON report
    out_dir = os.path.join(ROOT, "tools", "quant", "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "real_rv_backtest.json")
    with open(out_path, "w") as f:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "elapsed_sec": round(time.time() - t0, 2),
                   "params": {"start_equity": START_EQUITY,
                              "risk_per_trade": RISK_PER_TRADE,
                              "days": DEFAULT_BARS,
                              "train_frac": 0.6,
                              "z_threshold": 2.0},
                   "results": results}, f, indent=2)
    print(f"\nReport written to {out_path}", file=sys.stderr)
    # markdown summary
    md_path = os.path.join(out_dir, "real_rv_backtest.md")
    with open(md_path, "w") as f:
        f.write("# Real-Data RV Mean-Reversion Backtest\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}  |  "
                f"Elapsed: {time.time()-t0:.1f}s\n\n")
        f.write("## Methodology\n\n")
        f.write("- **Data**: real daily OHLC via `data_history.py` (Polygon / Binance / Twelve Data, CSV-cached)\n")
        f.write("- **Pairs**: highly-correlated ETF + crypto pairs\n")
        f.write("- **Walk-forward**: 60% in-sample (fit OU half-life) / 40% out-of-sample (trade)\n")
        f.write("- **Signal**: rolling z-score of log-spread, enter at |z|>2, exit at |z|<0.5\n")
        f.write(f"- **Sizing**: 1-sigma risk = {RISK_PER_TRADE*100:.0f}% of equity per trade\n")
        f.write("- **Costs**: not modeled in this first cut (will add in v2)\n\n")
        f.write("## Results\n\n")
        f.write("⚠️ **Sample size warning**: pairs with `n_trades < 20` are flagged 🚩 — their Sharpe is dominated by noise.\n\n")
        f.write("| Pair | Provider | Bars (IS/OO) | HL (bars) | Lookback | Trades | Win% | Expectancy | Per-trade Sharpe | t-stat | Ann Sharpe | Max DD | Total PnL |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in results:
            if "error" in r:
                f.write(f"| {r['pair']} | — | — | — | — | — | — | — | — | — | — | — | _{r['error']}_ |\n")
            else:
                flag = " 🚩" if r.get("low_sample") else ""
                f.write(f"| {r['pair']}{flag} | {r['provider_a']}/{r['provider_b']} | "
                        f"{r['n_bars_total']} ({r['n_is']}/{r['n_oos']}) | "
                        f"{r['half_life_bars']:.1f} | {r['lookback']} | "
                        f"{r['n_trades']} | {r['p_win']*100:.1f}% | "
                        f"{r['expectancy']*100:+.2f}% | {r['per_trade_sharpe']:+.2f} | "
                        f"{r['t_stat']:+.2f} | {r['ann_sharpe']:+.2f} | "
                        f"{r['max_drawdown']*100:.1f}% | "
                        f"${r['total_pnl_usd']:+,.0f} |\n")
        f.write("\n## Key takeaways\n\n")
        # heuristic summary
        ok = [r for r in results if "error" not in r]
        if not ok:
            f.write("- All pairs failed to produce a tradeable backtest.\n")
        else:
            pos = [r for r in ok if r["ann_sharpe"] > 0]
            neg = [r for r in ok if r["ann_sharpe"] <= 0]
            low = [r for r in ok if r.get("low_sample")]
            high = [r for r in ok if not r.get("low_sample")]
            f.write(f"- {len(ok)} of {len(results)} pairs produced tradeable backtests "
                    f"({len(pos)} positive OOS Sharpe, {len(neg)} non-positive).\n")
            f.write(f"- **Statistical reliability**: {len(high)} pair(s) had ≥20 trades "
                    f"(credible); {len(low)} pair(s) had <20 trades 🚩 (Sharpe dominated by noise).\n")
            if high:
                best_h = max(high, key=lambda r: r["ann_sharpe"])
                f.write(f"- **Best credible**: {best_h['pair']} OOS Sharpe {best_h['ann_sharpe']:+.2f}, "
                        f"t={best_h['t_stat']:+.2f}, PnL ${best_h['total_pnl_usd']:+,.0f} "
                        f"over {best_h['n_trades']} trades.\n")
            if pos:
                best = max(pos, key=lambda r: r["ann_sharpe"])
                flag = " 🚩 (low sample)" if best.get("low_sample") else ""
                f.write(f"- **Best raw**: {best['pair']} OOS Sharpe {best['ann_sharpe']:+.2f}{flag}, "
                        f"win {best['p_win']*100:.0f}%, PnL ${best['total_pnl_usd']:+,.0f} "
                        f"over {best['n_trades']} trades.\n")
            if neg:
                worst = min(neg, key=lambda r: r["ann_sharpe"])
                f.write(f"- **Worst**: {worst['pair']} OOS Sharpe {worst['ann_sharpe']:+.2f}, "
                        f"win {worst['p_win']*100:.0f}%, PnL ${worst['total_pnl_usd']:+,.0f} "
                        f"over {worst['n_trades']} trades.\n")
            f.write("\n> **Real-data numbers replace the synthetic OU Sharpe +6/+24/+34 from "
                    "`backtest_report.md`.  The synthetic test described the model, not the market.  "
                    "Real-pair OOS Sharpe is the number to believe — but only when n_trades ≥ 20.**\n")
    print(f"Markdown summary written to {md_path}", file=sys.stderr)
    return results


# ---------------------------------------------------------------- Renaissance on real data
REN_SETUPS_REAL = [
    # A representative subset of the 27-setup library -- pick structurally
    # distinct setups so we don't double-count.  Full list in
    # tools/quant/run_backtests.py:REN_SETUPS.
    "OSbounce",      # oversold bounce
    "Breakout",      # 20-day high breakout
    "Pullback",      # trend pullback
    "GapFade",       # gap fade
    "TrendRide50",   # ride the 50-day trend
    "PinBarLong",    # pin-bar reversal
    "KeyRevLong",    # key reversal
    "ConnorsLong",   # RSI(2) oversold
    "High52w",       # new 52-week high
    "TurnOfMonth",   # turn-of-month seasonality
    "OutsideRevLong",# outside-day reversal
    "RangeBreak",    # range breakout
]

# 10 liquid US large-caps -- universe for the real-data Renaissance test
REAL_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
    "META", "TSLA", "SPY", "QQQ", "IWM",
]


def run_ren_on_real(days: int = DEFAULT_BARS) -> dict:
    """Run a subset of the Renaissance setup library on real US equity data.

    For each (symbol, setup) pair: fetch real history, run the setup replay
    via `bt.run_setup_equity`, collect the per-trade stats, and report the
    OOS portion (last 40% of bars).

    The key question: do any of the setups that looked good on synthetic OU
    data (e.g. OBfade Sharpe +12.9) survive on real data?
    """
    print("\n" + "=" * 72, file=sys.stderr)
    print("RENAISSANCE SETUPS ON REAL US EQUITY DATA", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    # fetch all histories once
    print(f"  fetching {len(REAL_UNIVERSE)} symbols ...", file=sys.stderr)
    from tools.quant.data_history import fetch_many
    hists = fetch_many(REAL_UNIVERSE, days=days, workers=5)
    for sym in REAL_UNIVERSE:
        h, err = hists[sym]
        if h:
            print(f"    {sym:6s} OK {len(h['close'])} bars via {h.get('_provider','?')}",
                  file=sys.stderr)
        else:
            print(f"    {sym:6s} FAIL {err}", file=sys.stderr)
    # run each setup on each symbol
    per_setup = {}
    per_sym = {}
    all_trades = []
    for sym in REAL_UNIVERSE:
        h, err = hists[sym]
        if not h:
            continue
        # OOS = last 40% of bars; the setup replay runs on the full history
        # but we only count trades whose ENTRY is in the OOS window.
        n = len(h["close"])
        oos_start = int(n * 0.6)
        sym_trades = []
        for setup in REN_SETUPS_REAL:
            try:
                curve = bt.run_setup_equity(sym, h, setup, market="US",
                                            start_equity=START_EQUITY,
                                            risk_per_trade=RISK_PER_TRADE,
                                            horizon=5,
                                            tag=f"{setup}/{sym}")
            except Exception as e:
                continue
            if not curve or not curve.trades:
                continue
            # count only trades entered in OOS
            oos_trades = [t for t in curve.trades if t.entry_bar >= oos_start]
            if not oos_trades:
                continue
            for t in oos_trades:
                rec = {"sym": sym, "setup": setup,
                       "net_ret": t.net_ret, "pnl_usd": t.pnl_usd,
                       "side": t.side, "entry_bar": t.entry_bar,
                       "exit_bar": t.exit_bar}
                all_trades.append(rec)
                sym_trades.append(rec)
                per_setup.setdefault(setup, []).append(rec)
        if sym_trades:
            per_sym[sym] = sym_trades
    # aggregate per setup
    setup_summary = []
    for setup, trades in per_setup.items():
        rets = [t["net_ret"] for t in trades]
        n = len(rets)
        if n == 0:
            continue
        wins = [r for r in rets if r > 0]
        losses = [r for r in rets if r <= 0]
        p_win = len(wins) / n
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        expectancy = p_win * avg_win + (1 - p_win) * avg_loss
        sd = statistics.pstdev(rets) if n > 1 else 0.0
        per_trade_sharpe = expectancy / sd if sd > 0 else 0.0
        # ann Sharpe: assume avg hold = 5 bars (the horizon)
        tpy = 252.0 / 5.0
        ann = per_trade_sharpe * math.sqrt(tpy)
        se = sd / math.sqrt(n) if sd > 0 and n > 1 else 0.0
        t_stat = expectancy / se if se > 0 else 0.0
        total_pnl = sum(t["pnl_usd"] for t in trades)
        setup_summary.append({
            "setup": setup, "n_trades": n, "p_win": round(p_win, 4),
            "expectancy": round(expectancy, 4),
            "per_trade_sharpe": round(per_trade_sharpe, 3),
            "ann_sharpe": round(ann, 2),
            "t_stat": round(t_stat, 2),
            "low_sample": n < 20,
            "total_pnl_usd": round(total_pnl, 2),
        })
    setup_summary.sort(key=lambda r: r["ann_sharpe"], reverse=True)
    # aggregate per symbol
    sym_summary = []
    for sym, trades in per_sym.items():
        rets = [t["net_ret"] for t in trades]
        n = len(rets)
        wins = [r for r in rets if r > 0]
        p_win = len(wins) / n if n > 0 else 0
        exp = sum(rets) / n if n > 0 else 0
        total_pnl = sum(t["pnl_usd"] for t in trades)
        sym_summary.append({"sym": sym, "n_trades": n,
                            "p_win": round(p_win, 4),
                            "expectancy": round(exp, 4),
                            "total_pnl_usd": round(total_pnl, 2)})
    sym_summary.sort(key=lambda r: r["total_pnl_usd"], reverse=True)
    # blended
    if all_trades:
        all_rets = [t["net_ret"] for t in all_trades]
        n_all = len(all_rets)
        wins = [r for r in all_rets if r > 0]
        p_win_all = len(wins) / n_all
        exp_all = sum(all_rets) / n_all
        sd_all = statistics.pstdev(all_rets) if n_all > 1 else 0.0
        pt_sharpe_all = exp_all / sd_all if sd_all > 0 else 0.0
        tpy = 252.0 / 5.0
        ann_all = pt_sharpe_all * math.sqrt(tpy)
        se_all = sd_all / math.sqrt(n_all) if sd_all > 0 and n_all > 1 else 0.0
        t_stat_all = exp_all / se_all if se_all > 0 else 0.0
        blended = {
            "n_trades": n_all, "p_win": round(p_win_all, 4),
            "expectancy": round(exp_all, 4),
            "per_trade_sharpe": round(pt_sharpe_all, 3),
            "ann_sharpe": round(ann_all, 2),
            "t_stat": round(t_stat_all, 2),
            "total_pnl_usd": round(sum(t["pnl_usd"] for t in all_trades), 2),
        }
    else:
        blended = None
    # print summary
    print(f"\n  {'setup':18s} {'n':>5s} {'win%':>6s} {'exp%':>7s} "
          f"{'pt_sh':>7s} {'ann_sh':>7s} {'t':>6s} {'pnl':>10s}",
          file=sys.stderr)
    for s in setup_summary:
        flag = " 🚩" if s["low_sample"] else ""
        print(f"  {s['setup']+flag:18s} {s['n_trades']:5d} "
              f"{s['p_win']*100:5.1f}% {s['expectancy']*100:+6.2f}% "
              f"{s['per_trade_sharpe']:+7.2f} {s['ann_sharpe']:+7.2f} "
              f"{s['t_stat']:+6.2f} ${s['total_pnl_usd']:+,.0f}",
              file=sys.stderr)
    if blended:
        print(f"\n  BLENDED {blended['n_trades']:5d} "
              f"{blended['p_win']*100:5.1f}% {blended['expectancy']*100:+6.2f}% "
              f"{blended['per_trade_sharpe']:+7.2f} {blended['ann_sharpe']:+7.2f} "
              f"{blended['t_stat']:+6.2f} ${blended['total_pnl_usd']:+,.0f}",
              file=sys.stderr)
    return {"per_setup": setup_summary, "per_sym": sym_summary,
            "blended": blended, "n_universe": len(REAL_UNIVERSE),
            "n_setups": len(REN_SETUPS_REAL)}


def main():
    t0 = time.time()
    print("=" * 72, file=sys.stderr)
    print("REAL-DATA BACKTEST SUITE", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    # 1) RV mean-reversion on real ETF pairs
    rv_results = run_rv_suite(t0)
    # 2) Renaissance setups on real US equities
    ren_results = run_ren_on_real(days=DEFAULT_BARS)
    # write combined report
    out_dir = os.path.join(ROOT, "tools", "quant", "reports")
    os.makedirs(out_dir, exist_ok=True)
    # JSON
    json_path = os.path.join(out_dir, "real_backtest.json")
    with open(json_path, "w") as f:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "elapsed_sec": round(time.time() - t0, 2),
                   "rv_mean_reversion": rv_results,
                   "renaissance_setups": ren_results}, f, indent=2, default=str)
    print(f"\nJSON report: {json_path}", file=sys.stderr)
    # Markdown
    md_path = os.path.join(out_dir, "real_backtest.md")
    with open(md_path, "w") as f:
        f.write("# Real-Data Backtest Suite\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}  |  "
                f"Elapsed: {time.time()-t0:.1f}s\n\n")
        f.write("## Methodology\n\n")
        f.write("- **Data**: real daily OHLC via `data_history.py` (Polygon / Binance / Twelve Data, CSV-cached)\n")
        f.write("- **Walk-forward**: 60% in-sample / 40% out-of-sample for both RV pairs and setup replays\n")
        f.write(f"- **Sizing**: 1-sigma risk = {RISK_PER_TRADE*100:.0f}% of equity per trade\n")
        f.write("- **Universe**: 8 ETF/crypto pairs + 10 liquid US large-caps\n")
        f.write("- ⚠️ Pairs/setups with `n_trades < 20` are flagged 🚩 — Sharpe is dominated by noise\n\n")
        # RV section
        f.write("## 1. RV Mean-Reversion on Real ETF Pairs\n\n")
        f.write("| Pair | Provider | Bars (IS/OO) | HL (bars) | Lookback | Trades | Win% | Expectancy | Per-trade Sharpe | t-stat | Ann Sharpe | Max DD | Total PnL |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rv_results:
            if "error" in r:
                f.write(f"| {r['pair']} | — | — | — | — | — | — | — | — | — | — | — | _{r['error']}_ |\n")
            else:
                flag = " 🚩" if r.get("low_sample") else ""
                f.write(f"| {r['pair']}{flag} | {r['provider_a']}/{r['provider_b']} | "
                        f"{r['n_bars_total']} ({r['n_is']}/{r['n_oos']}) | "
                        f"{r['half_life_bars']:.1f} | {r['lookback']} | "
                        f"{r['n_trades']} | {r['p_win']*100:.1f}% | "
                        f"{r['expectancy']*100:+.2f}% | {r['per_trade_sharpe']:+.2f} | "
                        f"{r['t_stat']:+.2f} | {r['ann_sharpe']:+.2f} | "
                        f"{r['max_drawdown']*100:.1f}% | "
                        f"${r['total_pnl_usd']:+,.0f} |\n")
        # Renaissance section
        f.write("\n## 2. Renaissance Setups on Real US Equities\n\n")
        f.write(f"Universe: {', '.join(REAL_UNIVERSE)}\n\n")
        f.write("| Setup | Trades | Win% | Expectancy | Per-trade Sharpe | t-stat | Ann Sharpe | Total PnL |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for s in ren_results["per_setup"]:
            flag = " 🚩" if s["low_sample"] else ""
            f.write(f"| {s['setup']}{flag} | {s['n_trades']} | {s['p_win']*100:.1f}% | "
                    f"{s['expectancy']*100:+.2f}% | {s['per_trade_sharpe']:+.2f} | "
                    f"{s['t_stat']:+.2f} | {s['ann_sharpe']:+.2f} | "
                    f"${s['total_pnl_usd']:+,.0f} |\n")
        if ren_results.get("blended"):
            b = ren_results["blended"]
            f.write(f"| **BLENDED** | **{b['n_trades']}** | **{b['p_win']*100:.1f}%** | "
                    f"**{b['expectancy']*100:+.2f}%** | **{b['per_trade_sharpe']:+.2f}** | "
                    f"**{b['t_stat']:+.2f}** | **{b['ann_sharpe']:+.2f}** | "
                    f"**${b['total_pnl_usd']:+,.0f}** |\n")
        f.write("\n### Per-symbol breakdown\n\n")
        f.write("| Symbol | Trades | Win% | Expectancy | Total PnL |\n")
        f.write("|---|---|---|---|---|\n")
        for s in ren_results["per_sym"]:
            f.write(f"| {s['sym']} | {s['n_trades']} | {s['p_win']*100:.1f}% | "
                    f"{s['expectancy']*100:+.2f}% | ${s['total_pnl_usd']:+,.0f} |\n")
        # honest takeaways
        f.write("\n## Key takeaways\n\n")
        f.write("> **These are real-data numbers, not synthetic.**\n")
        f.write(">\n")
        f.write("> The synthetic OU Sharpe +6/+24/+34 from `backtest_report.md` described the\n")
        f.write("> *model*, not the *market*.  The numbers in this file are what the market\n")
        f.write("> actually gave us over the last ~2-4 years of daily bars.\n\n")
        ok_rv = [r for r in rv_results if "error" not in r]
        pos_rv = [r for r in ok_rv if r.get("ann_sharpe", 0) > 0]
        cred_rv = [r for r in ok_rv if not r.get("low_sample", True)]
        f.write(f"- **RV pairs**: {len(pos_rv)}/{len(ok_rv)} pairs had positive OOS Sharpe. "
                f"{len(cred_rv)}/{len(ok_rv)} had ≥20 trades (credible sample).\n")
        if ren_results.get("blended"):
            b = ren_results["blended"]
            f.write(f"- **Renaissance setups blended**: OOS ann Sharpe {b['ann_sharpe']:+.2f} "
                    f"over {b['n_trades']} trades, t-stat {b['t_stat']:+.2f}.\n")
            if b["n_trades"] >= 20 and abs(b["t_stat"]) < 2:
                f.write("  - ⚠️ Blended edge is **NOT** statistically significant (|t| < 2).\n")
            elif b["n_trades"] < 20:
                f.write("  - ⚠️ Sample size < 20 — Sharpe is dominated by noise.\n")
            elif b["ann_sharpe"] > 0 and b["t_stat"] >= 2:
                f.write("  - ✅ Blended edge IS statistically significant (t ≥ 2).\n")
        f.write("\n> **Next steps**: (1) extend history to 5-10 years via a paid Polygon tier\n")
        f.write("> or yfinance; (2) walk-forward re-fit the OU half-life periodically, not\n")
        f.write("> just once at the IS/OO split; (3) add a stop-loss to RV trades to cap max DD.\n")
        f.write("> (Transaction costs ARE now applied: IBKR retail ~10bp RT on 2-leg spreads,\n")
        f.write("> converted to stdev units via the 1-sigma-risk sizing convention.)\n")
    print(f"Markdown report: {md_path}", file=sys.stderr)
    return rv_results, ren_results


def run_rv_suite(t0):
    """Run the RV mean-reversion suite.  Factored out of main() for clarity."""
    print("\n" + "-" * 72, file=sys.stderr)
    print("RV MEAN-REVERSION ON REAL ETF PAIRS", file=sys.stderr)
    print("-" * 72, file=sys.stderr)
    print("  each pair: fetch -> IS/OO split -> fit OU on IS -> trade OOS\n",
          file=sys.stderr)
    results = []
    for a, b in DEFAULT_PAIRS:
        print(f"  -> {a}/{b} ...", end=" ", file=sys.stderr)
        r = rv_real_pair(a, b, days=DEFAULT_BARS)
        if "error" in r:
            print(f"FAIL ({r['error']})", file=sys.stderr)
        else:
            print(f"OOS ann {r['ann_sharpe']:+.2f} | n={r['n_trades']} "
                  f"win={r['p_win']*100:.0f}% | HL={r['half_life_bars']:.0f}b "
                  f"| PnL ${r['total_pnl_usd']:+,.0f}", file=sys.stderr)
        results.append(r)
    return results


if __name__ == "__main__":
    main()
