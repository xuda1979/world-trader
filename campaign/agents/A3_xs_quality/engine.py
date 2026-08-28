"""Shared PIT monthly-rebalance L/S backtest engine for A3_xs_quality.
Honesty: signal at t uses data <= t (PIT lag applied upstream); weights set at
month-end t apply to returns from t+1 (T+1); costs 6bps x one-side turnover;
vol targeting uses trailing expanding window only (min 60d).
"""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader")
import numpy as np
import pandas as pd
from campaign.harness import data as D

COST = 6.0

def load_rets():
    px = D.closes()
    return px, px.pct_change()

def month_ends(px):
    idx = px.index
    s = pd.Series(idx, index=idx)
    me = s.groupby([idx.year, idx.month]).max()
    return list(me.values)

def backtest(signal_wide, rets, long_frac=1/3, short_frac=1/3,
             leverage=2.0, min_names=10, rebalance="ME"):
    """signal_wide: DataFrame index=dates(trading), cols=symbols, value=score
    (higher=long). NaN=no position. PIT must be applied upstream.
    Returns daily net-of-cost gross strategy return series (before vol target)."""
    idx = rets.index
    sig = signal_wide.reindex(idx)
    mes = [d for d in month_ends(rets) if d in idx and d >= sig.dropna(how="all").index[0]]
    w = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    prev = pd.Series(0.0, index=rets.columns)
    turn = pd.Series(0.0, index=idx)
    for t in mes:
        row = sig.loc[t].dropna()
        if len(row) < min_names:
            neww = pd.Series(0.0, index=rets.columns)
        else:
            row = row.sort_values()
            n = len(row)
            nl = max(int(np.floor(n * long_frac)), 1)
            ns = max(int(np.floor(n * short_frac)), 1)
            lw = pd.Series(1.0 / nl, index=row.index[-nl:])
            sw = pd.Series(1.0 / ns, index=row.index[:ns])
            neww = (lw.subtract(sw, fill_value=0.0)).reindex(rets.columns).fillna(0.0)
            neww *= leverage / 2.0  # leverage=2 -> 100% long, 100% short
        # T+1: weights effective from next trading day
        pos = idx.get_loc(t)
        if pos + 1 < len(idx):
            turn.iloc[pos + 1] = 0.5 * (neww - prev).abs().sum()
            w.iloc[pos + 1] = neww.values
            # hold until next rebalance
            nxt = mes[mes.index(t) + 1] if mes.index(t) + 1 < len(mes) else idx[-1]
            w.iloc[pos + 1:idx.get_loc(nxt) + 1 if idx.get_loc(nxt) + 1 <= len(idx) else len(idx)] = 0.0
            w.iloc[pos + 1: idx.get_loc(nxt) + 1] = np.tile(neww.values, (idx.get_loc(nxt) + 1 - (pos + 1), 1))
            w.iloc[pos + 1] = neww.values
        prev = neww
    gross = (w.shift(0) * rets.fillna(0.0)).sum(axis=1)
    net = gross - turn * COST / 1e4
    # first day after first rebalance has spurious w-row from hold-fill; gross fine
    return net, w, turn

def vol_target(net, target=0.10, min_obs=60, cap=5.0):
    """Scale returns to ~10% ann vol using trailing expanding window only."""
    r = net.copy()
    vol = r.expanding(min_periods=min_obs).std().shift(1) * np.sqrt(252)
    scale = (target / vol).clip(upper=cap).fillna(0.0)
    return r * scale

def scramble_test(sig_panel, rets, real_sr, nrep=200, start=None, **bt_kw):
    """Permute signal values globally (destroy xs link), rerun, SR distribution."""
    vals2d = sig_panel.values.copy()
    mask = ~np.isnan(vals2d)
    v = vals2d[mask]
    rng = np.random.default_rng(42)
    srs = []
    for _ in range(nrep):
        pv = v.copy(); rng.shuffle(pv)
        p2 = np.full_like(vals2d, np.nan)
        p2[mask] = pv
        sp = pd.DataFrame(p2, index=sig_panel.index, columns=sig_panel.columns)
        net, _, _ = backtest(sp, rets, **bt_kw)
        rr = strategy_ret(net, start)
        sd = rr.std()
        srs.append(rr.mean() / sd * np.sqrt(252) if sd and sd > 0 else 0.0)
    srs = np.array(srs)
    return (srs < real_sr).mean(), float(np.percentile(srs, 95))

def strategy_ret(net, start=None):
    """Trim to signal start, vol-target on trailing expanding window of the
    active period only, drop first 5 warmup days."""
    if start is not None:
        net = net[net.index >= start]
    vt = vol_target(net)
    return vt.iloc[5:].dropna()

def full_gates(net_final, name="", scramble_p=None, verbose=True):
    r = net_final.dropna()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    sr = r.mean() / r.std() * np.sqrt(252)
    mid = r.index[len(r) // 2]
    h1 = r[r.index <= mid]; h2 = r[r.index > mid]
    sr1 = h1.mean() / h1.std() * np.sqrt(252); sr2 = h2.mean() / h2.std() * np.sqrt(252)
    gates = dict(SR=round(sr, 2), H1=round(sr1, 2), H2=round(sr2, 2),
                 neg_years=int((yr < 0).sum()), worst_year=round(yr.min() * 100, 1),
                 ann=round(r.mean() * 252 * 100, 2), vol=round(r.std() * np.sqrt(252) * 100, 2),
                 maxdd=round(((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min() * 100, 1))
    ok = (sr >= 0.6) and (sr1 >= 0.3) and (sr2 >= 0.3) and \
         (int((yr < 0).sum()) <= 2) and (yr[yr < 0].max() if (yr < 0).any() else 0) > -0.05
    if verbose:
        print(f"[{name}] {gates} yearly={ {int(k): round(v*100,1) for k,v in yr.items()} }")
        print(f"   gates {'PASS' if ok else 'FAIL'} (scramble_p={scramble_p})")
    return ok, gates
