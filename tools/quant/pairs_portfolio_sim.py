"""pairs_portfolio_sim.py -- calendar-time, cost-aware pair-portfolio simulation.

The research reports ("Sharpe 17.5", per-pair "edge") are computed per-trade in
spread-stdev units, aggregated across non-overlapping trades, with a fixed
1%-spread-stdev cost conversion.  That is NOT a portfolio Sharpe: it ignores
calendar overlap, position state, real spread volatility (which drives the
true cost per trade), and produces a number that cannot be compared to any
live strategy Sharpe.

This script replays the SAME v4 signal engine (Kalman spread, half-life
parameters, z>=2.0 entry, revert-1-sigma profit, -2-sigma stop, horizon
expiry) on a SHARED daily calendar with proper per-pair position state, sizes
each trade so a 1-sigma spread move = RISK_FRAC of equity (dollar-neutral
legs), and charges a round-trip cost of COST_BPS bps on gross notional per
trade.  Output: TRUE annualized Sharpe / Sortino / maxDD / turnover for the
in-sample and out-of-sample windows, net of costs.

Usage:
    python3 pairs_portfolio_sim.py [--z 1.5,2.0,2.5] [--cost-bps 0,3.8,7.6]
                                   [--risk 0.01] [--max-pairs N] [--eg-only]
"""
from __future__ import annotations
import os, sys, json, math, statistics, time
from concurrent.futures import ThreadPoolExecutor, as_completed

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import pairs_research_v4 as v4

# ------------------------------------------------------------------ config
Z_ENTRY_DEFAULTS = (2.0,)
COST_BPS_DEFAULTS = (3.8,)          # user's stated round-trip cost
COST_BPS_ALT     = (0.0, 3.8, 7.6)  # cost-drag sweep (7.6 = per-side reading)
RISK_FRAC        = 0.01             # 1 sigma spread move = 1% of equity
ANNUAL_FACTOR    = 252.0
OOS_SPLIT        = 0.60             # first 60% IS, last 40% OOS (mirrors v4)
MIN_IS_TSTAT     = 0.0              # research knob: stricter IS t-stat floor
                                    # (0 = Bonferroni-only, unchanged default)

REPORT_JSON = os.path.join(_HERE, "reports", "pairs_portfolio_sim.json")
REPORT_MD   = os.path.join(_HERE, "reports", "pairs_portfolio_sim.md")


# ------------------------------------------------------------------ data
_SCRAMBLE_SEED = None

def _pair_data(label, ac, sym_a, sym_b, kind, provider):
    ha = v4._load_series(sym_a, provider)
    hb = v4._load_series(sym_b, provider)
    if not ha or not hb:
        return None
    da, ca = ha; db, cb = hb
    a, b, dates = v4._align(da, ca, db, cb)
    if len(a) < 80:
        return None
    if _SCRAMBLE_SEED is not None:
        # FALSIFICATION CONTROL: shift leg B by a per-pair random lag,
        # destroying cointegration while keeping each leg's own vol and
        # autocorrelation.  The whole pipeline (qualify + replay) must
        # then produce ~zero Sharpe if it is honest.
        import random as _r
        _r.seed(_SCRAMBLE_SEED + sum(ord(c) for c in label))
        lag = _r.randint(20, len(a) // 3)
        b = [b[(i + lag) % len(b)] for i in range(len(a))]
    if kind == "DIFF":
        spread = [a[i] - b[i] for i in range(len(a))]
    else:
        _, spread = v4.kalman_spread(a, b, v4.KALMAN_DELTA, v4.KALMAN_VT)
    static_spread = v4._build_spread(kind, a, b)
    hl = v4.estimate_half_life(static_spread)
    return {"dates": dates, "spread": spread, "static": static_spread,
            "hl": hl, "a": a, "b": b}


def _roll(i, win, spread):
    w = spread[max(0, i - win):i]
    if len(w) < 10:
        return 0.0, 0.0
    m = sum(w) / len(w)
    var = sum((x - m) ** 2 for x in w) / (len(w) - 1) if len(w) > 1 else 0.0
    sd = math.sqrt(var) if var > 0 else 0.0
    return m, sd


def replay_pair(pair, z_entry, open_from=0, lookback=None, horizon=None,
                open_until=None):
    """Replay one pair on its own axis; return list of trade dicts with
    per-day sigma P&L attribution and entry/exit dates (day indices).
    open_from: only OPEN positions at index >= open_from (walk-forward).
    open_until: only OPEN positions at index < open_until (rolling WF
    episode window; positions may EXIT beyond it).
    lookback/horizon: override (walk-forward uses IS-estimated params)."""
    spread = pair["spread"]
    N = len(spread)
    if lookback is None:
        lookback = max(v4.HL_LOOKBACK_MIN, min(v4.HL_LOOKBACK_MAX, int(pair["hl"] * 3)))
    if horizon is None:
        horizon = max(v4.HL_HORIZON_MIN, min(v4.HL_HORIZON_MAX, int(pair["hl"] * 1.0)))
    trades = []
    pos = None  # None | (side, entry_idx, esd, entry_val)
    for i in range(lookback, N - 1):
        m, sd = _roll(i, lookback, spread)
        if sd <= 0:
            continue
        z = (spread[i] - m) / sd
        if pos is None:
            if (i >= open_from and abs(z) >= z_entry
                    and (open_until is None or i < open_until)):
                pos = (1 if z < 0 else -1, i, sd, spread[i])
            continue
        side, ei, esd, entry_val = pos
        # exit check on day i (first bar after entry is i=ei+1)
        if i == ei:
            continue
        if sd <= 0:
            continue
        d_stdev = (spread[i] - entry_val) / esd
        exit_idx = None
        if side * d_stdev >= 1.0:
            exit_idx = i
        elif side * d_stdev <= -2.0:
            exit_idx = i
        elif i - ei >= horizon:
            exit_idx = i
        if exit_idx is not None:
            # daily sigma P&L from ei+1 .. exit_idx inclusive
            daily = []
            for k in range(ei + 1, exit_idx + 1):
                dk = side * (spread[k] - spread[k - 1]) / esd
                daily.append(dk)
            trades.append({
                "side": side, "entry_idx": ei, "exit_idx": exit_idx,
                "sigma_net": sum(daily), "daily": daily,
                "entry_sd": esd,
            })
            pos = None
    return trades, lookback, horizon


# ------------------------------------------------------------------ portfolio
def _aggregate(pair_recs, cost_bps):
    """Shared-calendar aggregation of replayed pairs into daily returns."""
    if not pair_recs:
        return None
    cal = sorted({d for pr in pair_recs for d in pr["dates"]})
    cidx = {d: i for i, d in enumerate(cal)}
    n_days = len(cal)

    def day_index(pr, idx):
        return cidx[pr["dates"][idx]]

    gross = [0.0] * n_days
    net = [0.0] * n_days
    per_pair = []
    for pr in pair_recs:
        sigma_daily = [0.0] * n_days
        cost_daily = [0.0] * n_days
        n_tr = 0
        net_sigma = 0.0
        for t in pr["trades"]:
            n_tr += 1
            esd = t["entry_sd"]
            c_sigma = 2.0 * (cost_bps / 1e4) / esd if esd > 0 else 0.0
            e = day_index(pr, t["entry_idx"])
            x = day_index(pr, t["exit_idx"])
            for k, dk in zip(range(e + 1, x + 1), t["daily"]):
                sigma_daily[k] += dk
            cost_daily[e] += c_sigma
            cost_daily[x] += c_sigma
            net_sigma += t["sigma_net"] - c_sigma
        for i in range(n_days):
            gross[i] += sigma_daily[i] * RISK_FRAC
            net[i] += (sigma_daily[i] - cost_daily[i]) * RISK_FRAC
        per_pair.append({"label": pr["label"], "n_trades": n_tr,
                         "net_sigma": net_sigma})
    return {"cal": cal, "gross": gross, "net": net,
            "per_pair": per_pair, "n_days": n_days}


def run_portfolio(qualified, z_entry, cost_bps, oos_date=None):
    """Replay every qualified pair, aggregate on shared calendar.  If
    oos_date is given (walk-forward), positions may only open on or after
    it, and metrics are computed over that OOS region only."""
    pair_recs = []
    for p in qualified:
        data = _pair_data(p["label"], p.get("asset_class", "STOCK"),
                          p["sym_a"], p["sym_b"], p["kind"], p["provider"])
        if data is None:
            continue
        open_from = 0
        if oos_date is not None:
            open_from = next((i for i, dt in enumerate(data["dates"])
                              if dt >= oos_date), len(data["dates"]))
        trades, lb, hz = replay_pair(data, z_entry, open_from,
                                     lookback=data.get("lookback"),
                                     horizon=data.get("horizon"))
        if not trades:
            continue
        pair_recs.append({**p, "dates": data["dates"], "trades": trades,
                          "lookback": lb, "horizon": hz})
    return _aggregate(pair_recs, cost_bps)


def wf_qualify(spread_is, log_a, log_b, n_tests):
    """Walk-forward qualification: signal stats on IS data ONLY, Bonferroni
    gate (no OOS peek), EG cointegration on IS slice.  Static OLS spread is
    refit on the IS slice only (no full-sample beta leak)."""
    beta = v4._ols_beta(log_a, log_b)
    static_is = [log_a[i] - beta * log_b[i] for i in range(len(log_a))]
    hl = v4.estimate_half_life(static_is)
    lookback = max(v4.HL_LOOKBACK_MIN, min(v4.HL_LOOKBACK_MAX, int(hl * 3)))
    horizon = max(v4.HL_HORIZON_MIN, min(v4.HL_HORIZON_MAX, int(hl * 1.0)))
    bt = v4.backtest_pair_with_params(spread_is, lookback, horizon,
                                      v4.Z_ENTRY, v4.Z_EXIT, 0.0)
    if not bt or bt["n"] < v4.MIN_SAMPLE:
        return None
    if bt["edge"] < 0.60:
        return None
    if (bt.get("tstat") or 0) < max(v4._bonferroni_t(n_tests), MIN_IS_TSTAT):
        return None
    if bt.get("worst_trade") is not None and bt["worst_trade"] < -3.0:
        return None
    if bt.get("max_dd") is not None and bt["max_dd"] > 6.0:
        return None
    if bt.get("max_loss_streak") is not None and bt["max_loss_streak"] > 5:
        return None
    coint, _, _, _ = v4.engle_granger_test(log_a, log_b, v4.EG_MAX_LAG)
    if not coint:
        return None
    return {"lookback": lookback, "horizon": horizon, "edge_is": bt["edge"],
            "tstat_is": bt["tstat"]}


def metrics(daily, n_days, oos_date=None, cal=None):
    def _m(seg):
        n = len(seg)
        if n < 5:
            return None
        mu = statistics.fmean(seg)
        sd = statistics.pstdev(seg) if n > 1 else 0.0
        if sd <= 0:
            return None
        sharpe = (mu / sd) * math.sqrt(ANNUAL_FACTOR) if mu > 0 else mu / sd
        neg = [r for r in seg if r < 0]
        dsd = statistics.pstdev(neg) if len(neg) > 1 else 0.0
        sortino = (mu / dsd) * math.sqrt(ANNUAL_FACTOR) if dsd > 0 else None
        eq = 0.0; peak = 0.0; mdd = 0.0
        for r in seg:
            eq += r; peak = max(peak, eq); mdd = min(mdd, eq - peak)
        # CAGR at a fixed 10% annualized vol book (Sharpe is scale-free;
        # raw CAGR of the leveraged book is meaningless).
        cagr10 = ((1.0 + 0.10 * sharpe / ANNUAL_FACTOR) ** ANNUAL_FACTOR - 1.0) \
            if sharpe > 0 else -1.0
        return {"n_days": n, "mean_d": mu, "vol_d": sd,
                "sharpe": sharpe, "sortino": sortino, "max_dd": mdd,
                "cagr10": cagr10}
    if oos_date is not None and cal is not None:
        split = next((i for i, d in enumerate(cal) if d >= oos_date),
                     len(cal))
        return {"IS": None, "OOS": _m(daily[split:]), "ALL": _m(daily[split:])}
    split = int(n_days * OOS_SPLIT)
    return {"IS": _m(daily[:split]), "OOS": _m(daily[split:]), "ALL": _m(daily)}


def build_universe():
    all_pairs = list(v4.FX_PAIRS)
    for lst in [v4.ETF_PAIRS, v4.EQUITY_PAIRS, v4.CRYPTO_PAIRS]:
        all_pairs.extend(lst)
    for sname, stocks in v4.SECTORS.items():
        avail = [s for s in stocks if v4._load_series(s, "polygon")]
        if len(avail) >= 2:
            all_pairs.extend(v4.generate_sector_pairs(avail))
    seen = set(); uniq = []
    for p in all_pairs:
        key = (p[2], p[3]) if p[2] < p[3] else (p[3], p[2])
        if key not in seen:
            seen.add(key); uniq.append(p)
    return uniq


def wf_qualified_pairs():
    """Load full universe, run walk-forward qualification, return
    (all_data, oos_date, qualified_labels).  Reused by main() and by the
    diversification analysis."""
    all_pairs = build_universe()
    all_data = {}
    for p in all_pairs:
        label, ac, sym_a, sym_b, kind, provider = p
        data = _pair_data(label, ac, sym_a, sym_b, kind, provider)
        if data is not None:
            all_data[label] = {"label": label, "asset_class": ac,
                               "sym_a": sym_a, "sym_b": sym_b,
                               "kind": kind, "provider": provider,
                               **data}
    lens = sorted(len(pr["dates"]) for pr in all_data.values())
    med = lens[len(lens) // 2]
    target = sorted(all_data.values(), key=lambda pr: abs(len(pr["dates"]) - med))[0]
    oos_date = target["dates"][int(med * OOS_SPLIT)]
    qualified = []
    for label, pr in all_data.items():
        is_dates = [d for d in pr["dates"] if d < oos_date]
        if len(is_dates) < 100:
            continue
        q = wf_qualify(pr["spread"][:len(is_dates)],
                       [math.log(v) for v in pr["a"][:len(is_dates)]],
                       [math.log(v) for v in pr["b"][:len(is_dates)]],
                       n_tests=len(all_pairs))
        if q:
            all_data[label]["lookback"] = q["lookback"]
            all_data[label]["horizon"] = q["horizon"]
            qualified.append(label)
    return all_data, oos_date, qualified


def _pearson(x, y):
    both = [(a, b) for a, b in zip(x, y)
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


def _cluster_keep(qualified, all_data, q0, cap, rho=0.5):
    """Greedy keep top-`cap` pairs per correlation cluster (single-link,
    rho) using ONLY IS data: cluster membership from IS spread returns,
    rank by IS t-stat.  cap>=99 keeps everything."""
    if cap >= 99:
        return [q[0] for q in qualified]
    series = {}
    for label, lbk, hz, tstat in qualified:
        pr = all_data[label]
        n_is = sum(1 for d in pr["dates"] if d < q0)
        spread = pr["spread"]
        s = []
        for i in range(max(lbk, 1), n_is):
            m, sd = _roll(i, lbk, spread)
            if sd > 0:
                s.append((spread[i] - spread[i - 1]) / sd)
            else:
                s.append(0.0)
        series[label] = s
    labels = [q[0] for q in qualified]
    clusters = []
    for l in labels:
        joined = None
        for cl in clusters:
            if any(_pearson(series[l], series[m]) >= rho for m in cl):
                joined = cl
                break
        if joined is None:
            clusters.append([l])
        else:
            joined.append(l)
    tstat = {q[0]: q[3] for q in qualified}
    keep = []
    for cl in clusters:
        sel = sorted(cl, key=lambda l: -tstat[l])[:cap]
        keep += [q for q in qualified if q[0] in sel]
    return keep


# ------------------------------------------------------------------ rolling WF
def run_rolling(all_data, z_entry, cost_bps, is_bars=250, step=50, cap=99):
    """Rolling walk-forward: at every step, re-qualify pairs on the past
    `is_bars` of data (IS-only params, Bonferroni + EG), trade the next
    `step` bars, re-qualify again.  All traded days are out-of-sample
    relative to their own qualification episode.  Returns daily net/gross
    series over the traded region + per-episode stats."""
    lens = sorted(len(pr["dates"]) for pr in all_data.values())
    med_pr = sorted(all_data.values(),
                    key=lambda pr: abs(len(pr["dates"]) - lens[len(lens) // 2]))[0]
    med_dates = med_pr["dates"]
    n_tested = len(all_data)
    n_eps = max(1, (len(med_dates) - is_bars) // step)
    eps = []
    for e in range(n_eps):
        q0 = med_dates[is_bars + e * step]
        q1 = med_dates[min(is_bars + (e + 1) * step, len(med_dates) - 1)]
        qualified = []
        for label, pr in all_data.items():
            n_is = sum(1 for d in pr["dates"] if d < q0)
            if n_is < 120:
                continue
            q = wf_qualify(pr["spread"][:n_is],
                           [math.log(v) for v in pr["a"][:n_is]],
                           [math.log(v) for v in pr["b"][:n_is]],
                           n_tests=n_tested)
            if q:
                qualified.append((label, q["lookback"], q["horizon"],
                                  q["tstat_is"]))
        keep = _cluster_keep(qualified, all_data, q0, cap)
        eps.append({"q0": q0, "q1": q1, "qualified": keep,
                    "n_qualified_raw": len(qualified)})

    # replay per episode, aggregate on shared calendar
    recs = []
    for e in eps:
        for label, lbk, hz, _ in e["qualified"]:
            pr = all_data[label]
            open_from = next((i for i, d in enumerate(pr["dates"]) if d >= e["q0"]),
                             len(pr["dates"]))
            open_until = next((i for i, d in enumerate(pr["dates"]) if d >= e["q1"]),
                              len(pr["dates"]))
            trs, _, _ = replay_pair(pr, z_entry, open_from,
                                    lookback=lbk, horizon=hz,
                                    open_until=open_until)
            for t in trs:
                recs.append((label, t))

    # aggregate trades into per-pair records on the shared calendar
    by_pair = {}
    for label, t in recs:
        by_pair.setdefault(label, []).append(t)
    pair_recs = []
    for label, trs in by_pair.items():
        pr = all_data[label]
        pair_recs.append({**pr, "dates": pr["dates"], "trades": trs})
    agg = _aggregate(pair_recs, cost_bps)
    if agg is None:
        return None
    cal = agg["cal"]
    i0 = next((i for i, d in enumerate(cal) if d >= eps[0]["q0"]), len(cal))
    return {"cal": cal[i0:], "gross": agg["gross"][i0:],
            "net": agg["net"][i0:],
            "per_pair": agg["per_pair"], "episodes": eps}


# ------------------------------------------------------------------ main
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", default=",".join(str(x) for x in Z_ENTRY_DEFAULTS))
    ap.add_argument("--cost-bps", default=",".join(str(x) for x in COST_BPS_DEFAULTS))
    ap.add_argument("--max-pairs", type=int, default=0)
    ap.add_argument("--eg-only", action="store_true")
    ap.add_argument("--walk-forward", action="store_true")
    ap.add_argument("--rolling", action="store_true")
    ap.add_argument("--is-bars", type=int, default=250)
    ap.add_argument("--step", type=int, default=50)
    ap.add_argument("--rolling-cap", type=int, default=99,
                    help="max pairs per correlation cluster per episode")
    ap.add_argument("--scramble", type=int, default=0, metavar="SEED",
                    help="falsification control: shift leg B by random lag "
                         "(seeded), run the full pipeline, expect ~0 Sharpe")
    ap.add_argument("--engine", choices=["v4", "v5"], default="v5",
                    help="signal engine: v4 (artifact, for comparison) or "
                         "v5 (symmetric mean-reversion, scramble-tested)")
    args = ap.parse_args()
    zs = [float(x) for x in args.z.split(",") if x.strip()]
    costs = [float(x) for x in args.cost_bps.split(",") if x.strip()]

    t0 = time.time()
    if args.scramble:
        global _SCRAMBLE_SEED
        _SCRAMBLE_SEED = args.scramble
    all_pairs = build_universe()
    print(f"Universe: {len(all_pairs)} pairs"
          f"{'  [SCRAMBLED CONTROL seed=%d]' % args.scramble if args.scramble else ''}",
          file=sys.stderr)

    out = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"),
           "mode": "walk-forward" if args.walk_forward else "full-sample-qualified",
           "risk_frac": RISK_FRAC,
           "oosp_split": OOS_SPLIT, "annual_factor": ANNUAL_FACTOR,
           "runs": []}

    if args.walk_forward:
        all_data, oos_date, qualified = wf_qualified_pairs()
        print(f"WF: {len(all_data)} pairs with data tested on IS, "
              f"{len(qualified)} qualified (Bonferroni + EG)",
              file=sys.stderr)
        out["n_qualified"] = len(qualified)
        out["oos_date"] = oos_date
        out["qualified_labels"] = qualified
        for z in zs:
            for c in costs:
                rp = run_portfolio([all_data[l] for l in qualified], z, c,
                                   oos_date=oos_date)
                _emit_run(out, rp, z, c, oos_date=oos_date)
    elif args.rolling:
        all_data, _, _ = wf_qualified_pairs()
        print(f"Universe loaded: {len(all_data)} pairs", file=sys.stderr)
        out["is_bars"] = args.is_bars
        out["step"] = args.step
        out["n_qualified"] = "-"
        for z in zs:
            for c in costs:
                if args.engine == "v5":
                    import pairs_engine_v5 as v5
                    rr = v5.rolling(all_data, z, c, args.is_bars, args.step)
                else:
                    rr = run_rolling(all_data, z, c, args.is_bars, args.step,
                                     cap=args.rolling_cap)
                if rr is None:
                    continue
                eps = rr["episodes"]
                prev = None
                print(f"\n=== rolling WF (z={z}, cost={c}bps, IS={args.is_bars}, "
                      f"step={args.step}, cap/cluster={args.rolling_cap}): "
                      f"{len(eps)} episodes ===")
                for ei, e in enumerate(eps):
                    labs = [l for l, _, _, _ in e["qualified"]]
                    jac = ""
                    if prev:
                        inter = len(set(labs) & set(prev))
                        jac = f"  Jaccard={inter/max(1,len(set(labs)|set(prev))):.2f}"
                    print(f"  ep{ei} {e['q0']} -> {e['q1']}: "
                          f"{len(labs)}/{e['n_qualified_raw']} pairs"
                          f"{'' if len(labs)<12 else ' [' + ', '.join(labs[:6]) + '...]'}{jac}")
                    prev = labs
                m = metrics(rr["net"], len(rr["net"]), oos_date=rr["cal"][0],
                            cal=rr["cal"])
                mg = metrics(rr["gross"], len(rr["gross"]), oos_date=rr["cal"][0],
                             cal=rr["cal"])
                n_tr = sum(p["n_trades"] for p in rr["per_pair"])
                run = {"z_entry": z, "cost_bps": c,
                       "n_pairs_traded": len(rr["per_pair"]), "n_trades": n_tr,
                       "metrics": {"IS": None, "OOS": {"net": m["OOS"],
                                                       "gross": mg["OOS"]},
                                   "ALL": {"net": m["OOS"], "gross": mg["OOS"]}},
                       "daily_net": [round(x, 6) for x in rr["net"]],
                       "daily_cal": rr["cal"],
                       "per_pair": sorted(rr["per_pair"],
                                          key=lambda x: -x["net_sigma"]),
                       "episodes": [{"q0": e["q0"], "q1": e["q1"],
                                     "n_qualified": len(e["qualified"])}
                                    for e in eps]}
                out["runs"].append(run)
                o = m["OOS"]
                g = mg["OOS"]
                print(f"  TRADED REGION ({rr['cal'][0]} -> {rr['cal'][-1]}, "
                      f"{o['n_days']} days):")
                print(f"  net Sharpe={o['sharpe']:6.2f}  "
                      f"Sortino={o['sortino'] if o['sortino'] else float('nan'):6.2f}  "
                      f"maxDD={o['max_dd']*100:5.1f}%  "
                      f"CAGR@10%vol={o['cagr10']*100:6.1f}%  "
                      f"(gross Sharpe={g['sharpe']:6.2f})")
                print(f"  pairs traded: {len(rr['per_pair'])}, "
                      f"trades: {n_tr}, per pair: "
                      f"{', '.join(p['label'] + ':' + str(p['n_trades']) for p in rr['per_pair'][:10])}")
    else:
        results = {}
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(v4.backtest_pair, *p, None, True, False, True): p
                    for p in all_pairs}
            for fut in as_completed(futs):
                label, r, err = fut.result()
                if r:
                    results[label] = r
        print(f"{len(results)} pairs OK in {time.time()-t0:.1f}s", file=sys.stderr)
        all_pvals = [v4._p_from_t(r.get("tstat")) for r in results.values()]
        qualified = []
        for label, r in results.items():
            if v4.qualifies_pair(r, n_tests=len(results), use_fdr=True,
                                 all_pvals=all_pvals,
                                 asset_class=r.get("asset_class", "STOCK")):
                qualified.append(r)
        if args.eg_only:
            qualified = [r for r in qualified if r.get("eg_cointegrated")]
        qualified.sort(key=lambda r: -(r.get("oos_edge") or 0.0))
        if args.max_pairs:
            qualified = qualified[:args.max_pairs]
        print(f"{len(qualified)} FDR-qualified pairs", file=sys.stderr)
        out["n_qualified"] = len(qualified)
        out["qualified_labels"] = [r["label"] for r in qualified]
        for z in zs:
            for c in costs:
                rp = run_portfolio(qualified, z, c)
                _emit_run(out, rp, z, c)

    with open(REPORT_JSON, "w") as f:
        json.dump(out, f, indent=1, default=str)
    _write_md(out)
    print(f"\nWrote {REPORT_JSON} and {REPORT_MD}", file=sys.stderr)


def _emit_run(out, rp, z, c, oos_date=None):
    if rp is None:
        return
    m = metrics(rp["net"], rp["n_days"], oos_date, rp["cal"])
    mg = metrics(rp["gross"], rp["n_days"], oos_date, rp["cal"])
    n_tr = sum(p["n_trades"] for p in rp["per_pair"])
    ann = {}
    for w in ("IS", "OOS", "ALL"):
        ann[w] = {"net": m[w], "gross": mg[w] if mg else None}
    run = {"z_entry": z, "cost_bps": c, "n_pairs_traded": len(rp["per_pair"]),
           "n_trades": n_tr, "metrics": ann,
           "daily": {"dates": rp["cal"], "net": rp["net"]},
           "per_pair": sorted(rp["per_pair"], key=lambda x: -x["net_sigma"])}
    out["runs"].append(run)
    _print_run(run)


def _print_run(run):
    print(f"\n=== z_entry={run['z_entry']}  cost={run['cost_bps']}bps RT ===")
    print(f"pairs traded: {run['n_pairs_traded']}  total trades: {run['n_trades']}")
    for w in ("IS", "OOS", "ALL"):
        n = run["metrics"][w]["net"]
        g = run["metrics"][w]["gross"]
        if not n:
            continue
        print(f"  {w:4s} net Sharpe={n['sharpe']:6.2f}  "
              f"Sortino={n['sortino'] if n['sortino'] is not None else float('nan'):6.2f}  "
              f"maxDD={n['max_dd']*100:5.1f}%  CAGR@10%vol={n['cagr10']*100:6.1f}%  "
              f"(gross Sharpe={g['sharpe']:6.2f})" if g else "")
    print("  top OOS pairs by net sigma P&L:")
    for p in run["per_pair"][:8]:
        print(f"    {p['label']:12s} trades={p['n_trades']:3d} net_sigma={p['net_sigma']:+.2f}")


def _write_md(out):
    with open(REPORT_MD, "w") as f:
        f.write("# Pair Portfolio Simulation (calendar-time, net of costs)\n\n")
        f.write(f"Generated: {out['generated']}  |  mode: {out['mode']}  |  "
                f"{out.get('n_ok', '-')} pairs tested, "
                f"{out['n_qualified']} qualified\n\n")
        f.write(f"- Sizing: 1-sigma spread move = 1% equity per pair (dollar-neutral)\n")
        f.write(f"- Annualization: {out['annual_factor']:.0f} daily bars\n")
        f.write(f"- IS = first {out['oosp_split']:.0%} of shared calendar, "
                f"OOS = last {(1-out['oosp_split'])*100:.0f}%\n\n")
        f.write("| z | cost bps | pairs | trades | IS Sharpe | OOS Sharpe | OOS Sortino | OOS maxDD | CAGR@10%vol | gross OOS Sharpe |\n")
        f.write("|---|----------|-------|--------|-----------|------------|-------------|-----------|-------------|------------------|\n")
        for r in out["runs"]:
            o = r["metrics"]["OOS"]["net"]; g = r["metrics"]["OOS"]["gross"]
            is_ = r["metrics"].get("IS")
            is_s = f"{is_['net']['sharpe']:6.2f}" if (is_ and is_["net"]) else "   n/a"
            row = (f"| {r['z_entry']:.1f} | {r['cost_bps']:.1f} | {r['n_pairs_traded']} | "
                   f"{r['n_trades']} | {is_s} | "
                   f"{o['sharpe']:6.2f} | "
                   f"{o['sortino'] if o['sortino'] is not None else float('nan'):6.2f} | "
                   f"{o['max_dd']*100:5.1f}% | {o['cagr10']*100:6.1f}% | "
                   f"{g['sharpe']:6.2f} |\n")
            f.write(row)


if __name__ == "__main__":
    main()
