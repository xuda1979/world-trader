"""pairs_fixed_engine.py - Geometry-corrected pairs backtest with mandatory scramble control.
"""
from __future__ import annotations
import os, sys, json, math, statistics, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import pairs_research_v4 as v4

Z_ENTRY = 2.0
MIN_SAMPLE = 20
MIN_OOS_SAMPLE = 8
OOS_FRAC = v4.OOS_FRAC

def symmetric_backtest(spread, lookback, horizon, z_entry=2.0):
    N = len(spread)
    if N < lookback + horizon + 5:
        return None
    sym_dist = z_entry
    entries = []
    for i in range(lookback, N - 1):
        w = spread[max(0, i - lookback):i]
        if len(w) < 10:
            continue
        m = sum(w) / len(w)
        var = sum((x - m) ** 2 for x in w) / (len(w) - 1) if len(w) > 1 else 0.0
        sd = math.sqrt(var) if var > 0 else 0.0
        if sd <= 0:
            continue
        z = (spread[i] - m) / sd
        if z < -z_entry:
            entries.append((i, 1, spread[i], sd))
        elif z > z_entry:
            entries.append((i, -1, spread[i], sd))
    if len(entries) < MIN_SAMPLE:
        return None
    split = int(N * (1 - OOS_FRAC))
    is_rets, oos_rets = [], []
    for i, side, entry_val, entry_sd in entries:
        if entry_sd <= 0:
            continue
        outcome = None
        end = min(i + 1 + horizon, N)
        for j in range(i + 1, end):
            d_stdev = (spread[j] - entry_val) / entry_sd
            if side * d_stdev >= sym_dist:
                outcome = side * d_stdev
                break
            if side * d_stdev <= -sym_dist:
                outcome = side * d_stdev
                break
        if outcome is None:
            outcome = side * (spread[min(i + horizon, N - 1)] - entry_val) / entry_sd
        if i < split:
            is_rets.append(outcome)
        else:
            oos_rets.append(outcome)
    def _stats(rets):
        n = len(rets)
        if n == 0:
            return dict(n=0, exp_ret=0.0, edge=0.0, tstat=0.0, worst=0.0, max_dd=0.0, win_rate=0.0, streak=0)
        exp_ret = statistics.mean(rets)
        sd = statistics.pstdev(rets) if n > 1 else 0.0
        edge = exp_ret / sd if sd > 0 else 0.0
        se = sd / math.sqrt(n) if sd > 0 and n > 1 else 0.0
        tstat = exp_ret / se if se > 0 else 0.0
        worst = min(rets)
        cum = 0.0; peak = 0.0; mdd = 0.0
        for r in rets:
            cum += r
            if cum > peak: peak = cum
            mdd = min(mdd, cum - peak)
        cur = 0; ms = 0
        for r in rets:
            if r < 0: cur += 1; ms = max(ms, cur)
            else: cur = 0
        wins = sum(1 for r in rets if r > 0)
        return dict(n=n, exp_ret=exp_ret, edge=edge, tstat=tstat, worst=worst, max_dd=mdd, win_rate=wins/n, streak=ms)
    is_st = _stats(is_rets)
    oos_st = _stats(oos_rets)
    w = spread[max(0, N - 1 - lookback):N - 1]
    m_now = sum(w) / len(w) if w else 0.0
    var_now = sum((x - m_now) ** 2 for x in w) / (len(w) - 1) if len(w) > 1 else 0.0
    sd_now = math.sqrt(var_now) if var_now > 0 else 0.0
    z_now = (spread[N - 1] - m_now) / sd_now if sd_now > 0 else 0.0
    return dict(n=is_st["n"], edge=is_st["edge"], tstat=is_st["tstat"],
                exp_ret=is_st["exp_ret"], worst_trade=is_st["worst"],
                max_dd=is_st["max_dd"], max_loss_streak=is_st["streak"],
                win_rate=is_st["win_rate"], oos_n=oos_st["n"],
                oos_edge=oos_st["edge"], oos_exp_ret=oos_st["exp_ret"],
                oos_worst_trade=oos_st["worst"], oos_max_dd=oos_st["max_dd"],
                firing=abs(z_now) > z_entry, z_now=z_now,
                n_bars=N, lookback=lookback, horizon=horizon,
                z_entry=z_entry, engine="symmetric")


def test_pair(label, ac, sym_a, sym_b, kind, provider, scramble=False, seed=0):
    ha = v4._load_series(sym_a, provider)
    hb = v4._load_series(sym_b, provider)
    if not ha or not hb:
        return label, None, "no data"
    da, ca = ha; db, cb = hb
    a, b, dates = v4._align(da, ca, db, cb)
    if len(a) < 80:
        return label, None, "too few obs"
    if scramble:
        rng = random.Random(seed + sum(ord(c) for c in label))
        lag = rng.randint(20, max(20, len(b) // 3))
        b = [b[(i + lag) % len(b)] for i in range(len(b))]
    spread = v4._build_spread(kind, a, b)
    hl = v4.estimate_half_life(spread)
    lookback = max(v4.HL_LOOKBACK_MIN, min(v4.HL_LOOKBACK_MAX, int(hl * 3)))
    horizon = max(v4.HL_HORIZON_MIN, min(v4.HL_HORIZON_MAX, int(hl * 1.0)))
    bt = symmetric_backtest(spread, lookback, horizon, Z_ENTRY)
    if not bt:
        return label, None, "insufficient trades"
    bt["label"] = label
    bt["asset_class"] = ac
    bt["sym_a"] = sym_a; bt["sym_b"] = sym_b
    bt["kind"] = kind; bt["provider"] = provider
    bt["half_life"] = round(hl, 1)
    bt["n_bars"] = len(a)
    bt["scrambled"] = scramble
    if not scramble and kind != "DIFF":
        eg_coint, eg_adf, eg_pval, _ = v4.engle_granger_test(
            [math.log(v) for v in a], [math.log(v) for v in b])
        bt["eg_cointegrated"] = eg_coint
        bt["eg_adf_stat"] = round(eg_adf, 3)
        bt["eg_pvalue"] = round(eg_pval, 4)
    else:
        bt["eg_cointegrated"] = False
        bt["eg_adf_stat"] = 0.0
        bt["eg_pvalue"] = 1.0
    return label, bt, None
