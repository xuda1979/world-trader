"""A1 engine: honest TSMOM/T+1/6bps pipeline on FRED macro series + gates."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from data import fred, COST

COST_D = COST / 1e4

def load(names, start="2006-01-01"):
    out = {}
    for nm in names:
        s = fred(nm)
        s = s[~s.index.duplicated(keep="last")].sort_index()
        out[nm] = s[s.index >= pd.Timestamp(start)]
    return out

def align(specs, start="2006-01-01"):
    """specs: list of (name, flip). Returns (levels, rets, siglv) where trend is computed
    on ORIGINAL levels and the flip is applied to the resulting trend sign.
    (Ratio momentum on flipped negative levels is invariant: (-a)/(-b)=a/b — hence this.)"""
    ss = load([n for n, _ in specs], start)
    idx = sorted(set().union(*[set(ss[n].dropna().index) for n, _ in specs]))
    idx = pd.DatetimeIndex(idx)
    lv = pd.DataFrame({n: ss[n].reindex(idx).ffill() for n, _ in specs})
    rets = lv.pct_change()
    for n, fl in specs:
        rets[n] = rets[n] * fl   # traded return: inverse asset for flip=-1
    return lv, rets, lv.copy()

def signs_from_levels(lv, L, min_hist=63):
    """sign_m: +1 iff original level momentum up. flip applied downstream."""
    return var_mom(lv, L, min_hist)

def var_mom(siglv, L, min_hist=63):
    """sign(P_t / P_{t-L} - 1), variable lag min(L, hist-1) once hist-1>=min_hist. No lookahead."""
    out = {}
    for c in siglv.columns:
        v = siglv[c].values
        m = np.full(len(v), np.nan)
        cnt = 0; last_valid = -1; hist = []
        for i in range(len(v)):
            if np.isnan(v[i]):
                continue
            cnt += 1; hist.append(i)
            j = cnt - 1
            if j >= min_hist:
                lag_i = hist[j - min(L, j)]
                m[i] = np.sign(v[i] / v[lag_i] - 1.0)
        out[c] = pd.Series(m, index=siglv.index)
    return pd.DataFrame(out)

def positions(rets, sign_m, rb=21, target=0.10, cap=5.0, vol_lb=60):
    """Per-asset vol-scaled positions, sampled every rb days. Uses rets<=t, sign_m<=t."""
    N = rets.shape[1]
    vol = rets.rolling(vol_lb, min_periods=vol_lb).std() * np.sqrt(252)
    tgt = (target / N) / vol
    pos = sign_m * tgt.clip(upper=cap / N)
    pos = pos.where(sign_m.notna())
    # sample-and-hold on rb grid
    held = pos.copy()
    mask = np.arange(len(pos)) % rb != 0
    held[pos.notna()] = pos[pos.notna()].ffill()
    held[mask] = np.nan
    held = held.ffill()
    return held.fillna(0.0)

def scale_pipeline(held, rets, target=0.10, min_hist=60, lo=0.2, hi=3.0):
    """Sequential: eff_t = S_{t-1} * held_{t-1}; net_t = eff*ret_t - cost(turnover).
    S_t from expanding std of net returns <= t-1 (min_hist)."""
    R = rets.values; H = held.values
    T, N = R.shape
    net = np.zeros(T); S = np.zeros(T); S_prev = 1.0
    eff_prev = np.zeros(N)
    varsum = 0.0; cnt = 0; mean = 0.0; M2 = 0.0
    for t in range(T):
        eff = S_prev * H[t - 1] if t > 0 else np.zeros(N)
        gross = np.nansum(eff * R[t])
        cost = np.abs(eff - eff_prev).sum() * COST_D
        r = gross - cost
        net[t] = r
        S[t] = S_prev
        eff_prev = eff
        # update running stats with r (known at end of t)
        cnt += 1; d = r - mean; mean += d / cnt; M2 += d * (r - mean)
        if cnt > min_hist:
            sd = np.sqrt(M2 / (cnt - 1)) * np.sqrt(252)
            S_prev = float(np.clip(target / sd, lo, hi)) if sd > 0 else S_prev
    s = pd.Series(S, index=rets.index)
    return pd.Series(net, index=rets.index), s

def build(specs, L=252, rb=21, target=0.10, min_hist=63, start="2006-01-01"):
    lv, rets, _ = align(specs, start)
    sm = var_mom(lv, L, min_hist)
    fl = pd.Series({n: f for n, f in specs})
    sm = sm * fl
    held = positions(rets, sm, rb, target)
    net, S = scale_pipeline(held, rets, target)
    return net, held, rets, S

# ---------- gates ----------
def sr(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0

def yearly(r):
    return r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)

def halves_sr(r):
    mid = r.index[len(r) // 2]
    return sr(r[r.index <= mid]), sr(r[r.index > mid])

def scramble_p(net, held, rets, S, n=200, min_shift=252, seed=7):
    """Rotate held-position matrix by random k>=min_shift, rerun identical pipeline."""
    rng = np.random.RandomState(seed)
    T = len(held); H = held.values
    real = sr(net); wins = 0
    for _ in range(n):
        k = rng.randint(min_shift, max(min_shift + 1, T - min_shift))
        Hr = np.roll(H, k, axis=0); Hr[:k] = 0.0
        hd = pd.DataFrame(Hr, index=held.index, columns=held.columns)
        nr, _ = scale_pipeline(hd, rets)
        if sr(nr) >= real:
            wins += 1
    return wins / n

def gates(net, held, rets, S, grid_srs=None):
    """grid_srs: dict param->sr including chosen. Returns dict of gate results."""
    full = sr(net)
    h1, h2 = halves_sr(net)
    yr = yearly(net); neg = yr[yr < 0]
    g_full = full >= 0.6
    g_halves = (h1 >= 0.3) and (h2 >= 0.3)
    g_year = (len(neg) <= 2) and (len(neg) == 0 or neg.max() > -0.05)
    g_plateau = None
    if grid_srs:
        mx = max(grid_srs.values())
        on_plateau = sum(1 for v in grid_srs.values() if v >= 0.8 * mx)
        g_plateau = (grid_srs.get("CHOSEN", 0) >= 0.8 * mx) and on_plateau >= 3
    return dict(sr=round(full, 3), h1=round(h1, 3), h2=round(h2, 3),
                neg_years=int(len(neg)), worst_neg=round(neg.min() * 100, 2) if len(neg) else 0.0,
                g_full=g_full, g_halves=g_halves, g_year=g_year,
                g_plateau=g_plateau, pass_all=False)

def summary(r):
    eq = (1 + r).cumprod()
    return dict(sr=round(sr(r), 2), ann=round(r.mean() * 252 * 100, 2),
                vol=round(r.std() * np.sqrt(252) * 100, 2),
                dd=round((eq / eq.cummax() - 1).min() * 100, 1))
