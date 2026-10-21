"""pairs_engine_v5.py -- falsification-first mean-reversion engine.

v4's edge was a rule-geometry artifact (near profit target +1 sigma vs far
stop -2 sigma => positive expectancy on ANY process, proven by scramble
control: +1.92 sigma/trade on pure noise).  v5 fixes the geometry so the
trade is noise-neutral BY CONSTRUCTION:

  - spread: static OLS log-spread, beta refit on the episode's IS slice
  - entry:  |z| >= z_entry, z vs trailing-window stats, stats FIXED at entry
  - exit:   spread crosses the entry-window MEAN (full reversion, z=0)
            OR symmetric stop (z_stop sigma beyond entry)
            OR horizon expiry
  - profit and stop boundaries are equidistant from entry in sigma-space,
    so a symmetric random walk hits them 50/50 -> E[trade] ~ 0 on noise.

The scramble control (`--scramble SEED` in pairs_portfolio_sim.py) must show
~0 Sharpe on scrambled data before any real-data number is trusted.
"""
from __future__ import annotations
import math, statistics

import pairs_research_v4 as v4

HL_LOOKBACK_MIN, HL_LOOKBACK_MAX = 30, 120
HORIZON_MIN, HORIZON_MAX = 20, 120
MIN_SAMPLE = 20
EDGE_MIN = 0.30
T_MIN = 2.0
EG_ALPHA = 0.10


def _roll(i, win, spread):
    w = spread[max(0, i - win):i]
    if len(w) < 10:
        return 0.0, 0.0
    m = sum(w) / len(w)
    var = sum((x - m) ** 2 for x in w) / (len(w) - 1) if len(w) > 1 else 0.0
    sd = math.sqrt(var) if var > 0 else 0.0
    return m, sd


def build_spread(a, b, n_is=None):
    """Static OLS log-spread; beta from the first n_is bars (or full sample).
    The IS slice uses beta from its own data -> no lookahead."""
    la = [math.log(x) for x in a]
    lb = [math.log(x) for x in b]
    n = n_is if n_is is not None else len(la)
    beta = v4._ols_beta(la[:n], lb[:n])
    return [la[i] - beta * lb[i] for i in range(len(la))], beta


def replay_mr(spread, lookback, z_entry, z_stop, horizon,
              open_from=0, open_until=None):
    """v5 trade replay.  Returns trades in pairs_portfolio_sim format:
    {side, entry_idx, exit_idx, sigma_net, daily, entry_sd}."""
    N = len(spread)
    trades = []
    pos = None  # (side, ei, esd, m_e, z_e)
    for i in range(lookback, N - 1):
        m, sd = _roll(i, lookback, spread)
        if sd <= 0:
            continue
        z = (spread[i] - m) / sd
        if pos is None:
            if (i >= open_from and abs(z) >= z_entry
                    and (open_until is None or i < open_until)):
                pos = (1 if z < 0 else -1, i, sd, m, z)
            continue
        side, ei, esd, m_e, z_e = pos
        d = (spread[i] - m_e) / esd
        exit_idx = None
        if side * d <= 0:                     # crossed entry-window mean
            exit_idx = i
        elif side * (d - z_e) <= -z_stop:     # symmetric stop beyond entry
            exit_idx = i
        elif i - ei >= horizon:
            exit_idx = i
        if exit_idx is not None:
            daily = [side * (spread[k] - spread[k - 1]) / esd
                     for k in range(ei + 1, exit_idx + 1)]
            trades.append({"side": side, "entry_idx": ei, "exit_idx": exit_idx,
                           "sigma_net": sum(daily), "daily": daily,
                           "entry_sd": esd})
            pos = None
    return trades


def sim_stats(spread, lookback, z_entry, z_stop, horizon):
    """Per-trade outcome stats on a slice (for qualification)."""
    rets = []
    n = len(spread)
    for i in range(lookback, n - 1):
        m, sd = _roll(i, lookback, spread)
        if sd <= 0:
            continue
        z = (spread[i] - m) / sd
        if abs(z) < z_entry:
            continue
        side = 1 if z < 0 else -1
        m_e, esd = m, sd
        z_e = z
        outcome = None
        for j in range(i + 1, min(i + 1 + horizon, n)):
            d = (spread[j] - m_e) / esd
            if side * d <= 0:
                outcome = side * (d - z_e)
                break
            if side * (d - z_e) <= -z_stop:
                outcome = side * (d - z_e)
                break
        if outcome is None:
            j = min(i + horizon, n - 1)
            d = (spread[j] - m_e) / esd
            outcome = side * (d - z_e)
        rets.append(outcome)
    if len(rets) < MIN_SAMPLE:
        return None
    mu = statistics.fmean(rets)
    sd = statistics.pstdev(rets) if len(rets) > 1 else 0.0
    edge = mu / sd if sd > 0 else 0.0
    se = sd / math.sqrt(len(rets)) if len(rets) > 1 else 0.0
    tstat = mu / se if se > 0 else 0.0
    worst = min(rets)
    cum = 0.0; peak = 0.0; max_dd = 0.0
    for r in rets:
        cum += r
        peak = max(peak, cum)
        max_dd = min(max_dd, cum - peak)
    streak = 0; cur = 0
    for r in rets:
        if r < 0:
            cur += 1
            streak = max(streak, cur)
        else:
            cur = 0
    return {"n": len(rets), "exp_ret": mu, "sd": sd, "edge": edge,
            "tstat": tstat, "worst_trade": worst, "max_dd": max_dd,
            "max_loss_streak": streak}


def qualify(spread, a, b, n_is, n_tests):
    """v5 gate: loose statistical gate + EG cointegration on IS slice.
    The scramble control is the REAL gate; this only prunes noise."""
    hl = v4.estimate_half_life(spread)
    lookback = max(HL_LOOKBACK_MIN, min(HL_LOOKBACK_MAX, int(hl * 3)))
    horizon = max(HORIZON_MIN, min(HORIZON_MAX, int(hl * 1.5)))
    z_entry, z_stop = 2.0, 2.0
    st = sim_stats(spread, lookback, z_entry, z_stop, horizon)
    if not st or st["n"] < MIN_SAMPLE:
        return None
    if st["edge"] < EDGE_MIN or st["tstat"] < T_MIN:
        return None
    la = [math.log(x) for x in a[:n_is]]
    lb = [math.log(x) for x in b[:n_is]]
    coint, adf, pval, _ = v4.engle_granger_test(la, lb, v4.EG_MAX_LAG)
    if not coint:
        return None
    return {"lookback": lookback, "horizon": horizon, "edge_is": st["edge"],
            "tstat_is": st["tstat"], "n_is": n_is}


def rolling(all_data, z_entry, cost_bps, is_bars=250, step=50):
    """Rolling walk-forward with the v5 engine.  Same return shape as
    pairs_portfolio_sim.run_rolling so main() can reuse its printing."""
    lens = sorted(len(pr["dates"]) for pr in all_data.values())
    med_pr = sorted(all_data.values(),
                    key=lambda pr: abs(len(pr["dates"]) - lens[len(lens) // 2]))[0]
    med_dates = med_pr["dates"]
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
            spread, _ = build_spread(pr["a"], pr["b"], n_is)
            q = qualify(spread[:n_is], pr["a"], pr["b"], n_is,
                        n_tests=len(all_data))
            if q:
                qualified.append((label, q["lookback"], q["horizon"],
                                  q["tstat_is"]))
        eps.append({"q0": q0, "q1": q1, "qualified": qualified,
                    "n_qualified_raw": len(qualified)})

    recs = []
    for e in eps:
        for label, lbk, hz, _ in e["qualified"]:
            pr = all_data[label]
            n_is = sum(1 for d in pr["dates"] if d < e["q0"])
            spread, _ = build_spread(pr["a"], pr["b"], n_is)
            open_from = next((i for i, d in enumerate(pr["dates"])
                              if d >= e["q0"]), len(pr["dates"]))
            open_until = next((i for i, d in enumerate(pr["dates"])
                               if d >= e["q1"]), len(pr["dates"]))
            trs = replay_mr(spread, lbk, z_entry, z_entry, hz,
                            open_from=open_from, open_until=open_until)
            for t in trs:
                recs.append((label, t))

    by_pair = {}
    for label, t in recs:
        by_pair.setdefault(label, []).append(t)
    import pairs_portfolio_sim as ps
    pair_recs = []
    for label, trs in by_pair.items():
        pr = all_data[label]
        pair_recs.append({**pr, "dates": pr["dates"], "trades": trs})
    agg = ps._aggregate(pair_recs, cost_bps)
    if agg is None:
        return None
    cal = agg["cal"]
    i0 = next((i for i, d in enumerate(cal) if d >= eps[0]["q0"]), len(cal))
    return {"cal": cal[i0:], "gross": agg["gross"][i0:],
            "net": agg["net"][i0:],
            "per_pair": agg["per_pair"], "episodes": eps}
