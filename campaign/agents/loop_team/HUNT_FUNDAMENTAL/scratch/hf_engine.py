"""HUNT_FUNDAMENTAL engine: monthly-rebalance fundamental-factor L/S from
alphaportfolio_replication/data/fundamentals_annual.parquet, priced on the actual
twelve_extend daily panel. NO SPREAD-TO-DAILY: the book holds CONSTANT NOMINAL
WEIGHTS intra-month and PnL accrues from actual daily price moves (true ETF/panel
path with intra-month vol).
Honesty: T+1 (weights set at month-end t priced from t+1), 6 bps one-side on
turnover, 0.5%/yr borrow on short notional, vol target via trailing expanding
window only (min 60d, cap 5x). PIT: FY y usable only from Jul-1 of y+1.
"""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader")
import numpy as np
import pandas as pd
from campaign.harness import data as D

COST_BPS = 6.0
BORROW = 0.005  # 50 bps/yr on short notional

ROOT = "/Users/daxu/software/world-trader"
FUND = f"{ROOT}/alphaportfolio_replication/data/fundamentals_annual.parquet"


def load_panel():
    """Union of twelve_big (298 S&P names) + twelve_extend (440 OTC/micro) panels."""
    ps_big = D.panel(extended=False)
    ps_ext = D.panel(extended=True)
    cols = {}
    for k, v in {**ps_ext, **ps_big}.items():
        s = v["close"]
        s = s[~s.index.duplicated(keep="last")]
        cols[k] = s
    px = pd.DataFrame(cols).sort_index()
    rets = px.pct_change(fill_method=None)
    return px, rets


def month_ends(idx):
    s = pd.Series(idx, index=idx)
    me = s.groupby([idx.year, idx.month]).max()
    return [d for d in me.values]


def build_signal(px, score_fn):
    """Wide signal panel (index=trading days, cols=symbols). PIT lag: FY y usable
    from Jul-1 y+1 through Jun-30 y+2 (next FY's data then takes over)."""
    f = pd.read_parquet(FUND)
    f = f[f.symbol.isin(px.columns)].copy()
    f["score"] = score_fn(f)
    f = f[f.score.notna()]
    f = f.sort_values("fy")
    f["avail"] = pd.to_datetime((f.fy + 1).astype(str) + "-07-01")
    dates = px.index
    sig = pd.DataFrame(np.nan, index=dates, columns=px.columns)
    sym_map = {s: i for i, s in enumerate(px.columns)}
    for _, r in f.iterrows():
        j = sym_map.get(r.symbol)
        if j is None:
            continue
        mask = (dates >= r.avail) & (dates <= pd.Timestamp(str(r.fy + 2) + "-06-30"))
        ii = np.where(mask)[0]
        sig.iloc[ii, j] = r.score
    sig = sig.where(px.notna())  # trade only names with live price data
    return sig


def backtest(sig, rets, long_frac, short_frac, leverage, min_names=10):
    """Monthly rebalance at month-end, T+1 (weights effective next trading day),
    CONSTANT nominal weights held to next month-end. Returns net daily series."""
    idx = rets.index
    mes = [d for d in month_ends(idx) if d in idx]
    w = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    prev = pd.Series(0.0, index=rets.columns)
    turn = pd.Series(0.0, index=idx)
    for k, t in enumerate(mes):
        row = sig.loc[t].dropna()
        if len(row) < min_names:
            neww = pd.Series(0.0, index=rets.columns)
        else:
            rs = row.sort_values()
            n = len(rs)
            nl = max(int(np.floor(n * long_frac)), 1)
            ns = max(int(np.floor(n * short_frac)), 1)
            lw = pd.Series(1.0 / nl, index=rs.index[-nl:])
            sw = pd.Series(1.0 / ns, index=rs.index[:ns])
            neww = lw.subtract(sw, fill_value=0.0).reindex(rets.columns).fillna(0.0)
            neww *= leverage / 2.0
        nxt = mes[k + 1] if k + 1 < len(mes) else idx[-1]
        i0 = idx.get_loc(t) + 1
        i1 = idx.get_loc(nxt) + 1  # exclusive: hold [t+1, nxt]
        if i0 >= len(idx):
            break
        seg = slice(i0, min(i1, len(idx)))
        w.iloc[seg] = neww.values[None, :]
        turn.iloc[i0] = 0.5 * (neww - prev).abs().sum()
        prev = neww
    gross = (w * rets.fillna(0.0)).sum(axis=1)
    short_notional = -(w.clip(upper=0.0)).sum(axis=1)
    net = gross - turn * COST_BPS / 1e4 - short_notional * BORROW / 252
    return net, w, turn


def vol_target(net, target=0.10, min_obs=60, cap=5.0):
    r = net.copy()
    vol = r.expanding(min_periods=min_obs).std().shift(1) * np.sqrt(252)
    scale = (target / vol).clip(upper=cap).fillna(0.0)
    return r * scale


def scramble_test(sig, rets, real_sr, long_frac, short_frac, leverage, nrep=200, seed=42):
    """Permute signal values globally (destroy xs link, keep panel shape)."""
    vals2d = sig.values.copy()
    mask = ~np.isnan(vals2d)
    v = vals2d[mask]
    rng = np.random.default_rng(seed)
    srs = []
    for _ in range(nrep):
        pv = v.copy()
        rng.shuffle(pv)
        p2 = np.full_like(vals2d, np.nan)
        p2[mask] = pv
        sp = pd.DataFrame(p2, index=sig.index, columns=sig.columns)
        net, _, _ = backtest(sp, rets, long_frac, short_frac, leverage)
        rr = vol_target(net).iloc[5:].dropna()
        sd = rr.std()
        srs.append(rr.mean() / sd * np.sqrt(252) if sd and sd > 0 else 0.0)
    srs = np.array(srs)
    return float((srs < real_sr).mean()), float(np.percentile(srs, 95))


def full_gates(r, name="", verbose=True):
    r = r.dropna()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    sr = r.mean() / r.std() * np.sqrt(252)
    mid = r.index[len(r) // 2]
    h1 = r[r.index <= mid]; h2 = r[r.index > mid]
    sr1 = h1.mean() / h1.std() * np.sqrt(252); sr2 = h2.mean() / h2.std() * np.sqrt(252)
    mdd = ((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min() * 100
    gates = dict(SR=round(sr, 2), H1=round(sr1, 2), H2=round(sr2, 2),
                 neg_years=int((yr < 0).sum()), worst_year=round(yr.min() * 100, 1),
                 ann=round((1 + r).prod() ** (252 / len(r)) * 100 - 100, 2),
                 vol=round(r.std() * np.sqrt(252) * 100, 2), maxdd=round(mdd, 1))
    ok = (sr >= 0.6) and (sr1 >= 0.3) and (sr2 >= 0.3) and \
         (int((yr < 0).sum()) <= 2) and ((yr[yr < 0].max() if (yr < 0).any() else 0) > -0.05)
    if verbose:
        print(f"[{name}] {gates}")
        print(f"   yearly={ {int(k): round(v*100,1) for k,v in yr.items()} }")
        print(f"   gates {'PASS' if ok else 'FAIL'}")
    return ok, gates


def flatten_gate(r):
    """From campaign/audit_harness.py logic: uniqR>=0.08 and ac1<0.5."""
    rr = r.dropna()
    uniqr = rr.nunique() / len(rr) if len(rr) else 0.0
    ac1 = rr.autocorr(1)
    ac1 = 0.0 if ac1 != ac1 else ac1
    return dict(uniqR=round(float(uniqr), 4), ac1=round(float(ac1), 3),
                pass_=bool(uniqr >= 0.08 and ac1 < 0.5))
