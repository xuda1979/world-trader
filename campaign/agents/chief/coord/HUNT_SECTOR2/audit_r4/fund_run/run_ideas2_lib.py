"""HUNT_FUNDAMENTAL idea pass 2: quarterly refresh, mom + fundamentals hybrids.
All T+1, 6bps, borrow, EW terciles or z-score weights, vt10 expanding."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
import numpy as np, pandas as pd

px, rets = load_panel()
F = pd.read_parquet(FUND)
F = F[F.symbol.isin(px.columns)].copy()

def zsc(f2, x):
    med = x.groupby(f2["fy"]).transform("median")
    sd = x.groupby(f2["fy"]).transform(lambda s: s.std())
    return ((x - med) / sd.where(sd > 0)).clip(-3, 3)

def score_value(f):
    eb = f.net_income / f.equity.replace(0, np.nan)
    ic = (f.equity + f.debt - f.cash).where(lambda s: s > 0)
    oic = f.op_income / ic
    sta = f.revenue / f.total_assets.where(lambda s: s > 0)
    legs = pd.DataFrame({"eb": eb, "oic": oic, "sta": sta})
    out = pd.Series(np.nan, index=f.index)
    for c in legs.columns:
        out = out.add(zsc(f, legs[c]), fill_value=0)
    n = legs.notna().sum(axis=1)
    return (out / n.where(n > 0)).where(n > 0)

def score_piotroski(f):
    f2 = f.sort_values(["symbol", "fy"]).copy()
    ta = f2.total_assets.where(lambda s: s > 0)
    roa = f2.net_income / ta
    leg1 = (roa > 0).astype(float).where(f2.net_income.notna())
    leg2 = (roa > roa.groupby(f2.symbol).shift(1)).astype(float).where(f2.net_income.notna())
    shg = f2.shares.groupby(f2.symbol).pct_change()
    leg3 = (shg <= 0).astype(float).where(f2.shares.notna())
    return leg1.fillna(0) + leg2.fillna(0) + leg3.fillna(0)

def mom121(q, sym, t):
    s = px[sym]
    if t not in s.index: return np.nan
    i = s.index.get_loc(t)
    if i < 252: return np.nan
    # skip most recent month: use t-21d vs t-252d prices
    return s.iloc[i-21] / s.iloc[i-252] - 1

def quarterly_score_frame():
    """Wide frame of fundamental score, updated quarterly (stale between)."""
    f = F.copy().sort_values(["symbol", "fy"])
    f["score_v"] = score_value(f)
    f["score_p"] = score_piotroski(f)
    f["avail"] = pd.to_datetime((f.fy + 1).astype(str) + "-07-01")
    # next avail per name (for masking): when the NEXT fy row exists, that one overwrites
    f = f.sort_values(["symbol", "avail"])
    dates = px.index
    sigv = pd.DataFrame(np.nan, index=dates, columns=px.columns)
    sigp = pd.DataFrame(np.nan, index=dates, columns=px.columns)
    cols = {s: i for i, s in enumerate(px.columns)}
    for _, r in f.iterrows():
        j = cols.get(r.symbol)
        if j is None: continue
        m = dates >= r.avail
        sigv.iloc[np.where(m)[0], j] = r.score_v
        sigp.iloc[np.where(m)[0], j] = r.score_p
    sigv = sigv.where(px.notna()); sigp = sigp.where(px.notna())
    return sigv, sigp

sigv, sigp = quarterly_score_frame()

# momentum wide frame (monthly refresh naturally by formula)
i252 = pd.Series(np.arange(len(px)), index=px.index)
mom = px.shift(21) / px.shift(252) - 1

def rebalance_q(sig, kind, lf, sf, lev, min_names=10):
    """Quarterly rebalance at FMA (first month of quarter mid). kind: 'ls' terciles or none."""
    idx = px.index
    qstarts = [d for d in idx if d.month in (1, 4, 7, 10)]
    qs = []
    seen = set()
    for d in qstarts:
        k = (d.year, d.month)
        if k in seen: continue
        seen.add(k)
        # first trading day of quarter
        qs.append(d)
    mes = [d for d in qs if d in idx]
    w = pd.DataFrame(0.0, index=idx, columns=px.columns)
    prev = pd.Series(0.0, index=px.columns)
    turn = pd.Series(0.0, index=idx)
    for k, t in enumerate(mes):
        row = sig.loc[t].dropna()
        if len(row) < min_names:
            neww = pd.Series(0.0, index=px.columns)
        elif kind == "ls":
            rs = row.sort_values(); n = len(rs)
            nl = max(int(np.floor(n * lf)), 1); ns = max(int(np.floor(n * sf)), 1)
            lw = pd.Series(1.0/nl, index=rs.index[-nl:]); sw = pd.Series(1.0/ns, index=rs.index[:ns])
            neww = lw.subtract(sw, fill_value=0.0).reindex(px.columns).fillna(0.0)
            neww *= lev / 2.0
        nxt = mes[k+1] if k+1 < len(mes) else idx[-1]
        i0 = idx.get_loc(t) + 1
        if i0 >= len(idx): break
        i1 = min(idx.get_loc(nxt) + 1, len(idx))
        w.iloc[i0:i1] = neww.values[None, :]
        turn.iloc[i0] = 0.5 * (neww - prev).abs().sum()
        prev = neww
    gross = (w * rets.fillna(0.0)).sum(axis=1)
    sn = -(w.clip(upper=0.0)).sum(axis=1)
    net = gross - turn * COST_BPS/1e4 - sn * BORROW/252
    return net, w, turn

def rebalance_m(sigfn, lf, sf, lev, min_names=10):
    """Monthly rebalance using callable sig(t) -> Series."""
    idx = px.index
    mes = month_ends(idx)
    w = pd.DataFrame(0.0, index=idx, columns=px.columns)
    prev = pd.Series(0.0, index=px.columns)
    turn = pd.Series(0.0, index=idx)
    for k, t in enumerate(mes):
        row = sigfn(t)
        row = row.dropna()
        if len(row) < min_names:
            neww = pd.Series(0.0, index=px.columns)
        else:
            rs = row.sort_values(); n = len(rs)
            nl = max(int(np.floor(n * lf)), 1); ns = max(int(np.floor(n * sf)), 1)
            lw = pd.Series(1.0/nl, index=rs.index[-nl:]); sw = pd.Series(1.0/ns, index=rs.index[:ns])
            neww = lw.subtract(sw, fill_value=0.0).reindex(px.columns).fillna(0.0)
            neww *= lev / 2.0
        nxt = mes[k+1] if k+1 < len(mes) else idx[-1]
        i0 = idx.get_loc(t) + 1
        if i0 >= len(idx): break
        i1 = min(idx.get_loc(nxt) + 1, len(idx))
        w.iloc[i0:i1] = neww.values[None, :]
        turn.iloc[i0] = 0.5 * (neww - prev).abs().sum()
        prev = neww
    gross = (w * rets.fillna(0.0)).sum(axis=1)
    sn = -(w.clip(upper=0.0)).sum(axis=1)
    net = gross - turn * COST_BPS/1e4 - sn * BORROW/252
    return net, w, turn

def report(name, net, start=None):
    r = vol_target(net).iloc[5:].dropna()
    if start: r = r[r.index >= start]
    ok, g = full_gates(r, name, verbose=False)
    fg = flatten_gate(r)
    print(f"{name:28s} SR={g['SR']:+.2f} H1={g['H1']:+.2f} H2={g['H2']:+.2f} ann={g['ann']:+.1f}% negy={g['neg_years']} worst={g['worst_year']}% MDD={g['maxdd']}% flat={fg['pass_']} {'PASS' if ok else 'fail'}")
    return ok, g, r

