"""HUNT_CLASSIC_SPREADS — classic strategy families research engine.
Mirrors the frozen brwt/HUNT_BASIS2 honesty mechanics:
  - T+1 execution (sp.diff().shift(-1))
  - FULL |dpos| one-side cost @ 6.4bps (CAMP_COST R2 costfix convention)
  - borrow 0.5%/yr on 1-unit short-leg notionals (nonzero days)
  - trailing vol-target 0.08 (expanding, min 60d, cap 3.0)
  - NO flattening (real daily path)
  - trailing-window z-score signals only (no lookahead)
"""
import numpy as np, pandas as pd
import os, sys

ROOT = "/Users/daxu/software/world-trader"
DATA = f"{ROOT}/tools/quant/data"

# ---------------------------------------------------------------- load helpers
def load(path, value_col=None):
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    col = value_col if value_col else ('value' if 'value' in df.columns else df.columns[0])
    s = df[col]
    return s[~s.index.duplicated(keep='last')].sort_index()

def eia(name):
    return load(f"{DATA}/eia_weekly/{name}.csv")

def newdata(name):
    return load(f"{DATA}/newdata/{name}.csv")

def newdata2(name):
    s = load(f"{DATA}/newdata2/{name}.csv")
    return s

def champ_ref():
    c = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv",
                    index_col=0, parse_dates=True)['ret'].astype(float)
    return c[~c.index.duplicated()].sort_index()

# ---------------------------------------------------------------- strategy core
def zrev_margin(margin, lookback=15, gate=1.5, min_start='2008-01-01',
                cost_bps=6.4, do_borrow=True, sign=+1):
    """z-score mean-reversion on a real (dollar) margin series.
    Long when z<-gate (margin cheap), short when z>gate (margin rich).
    Returns (net, gross, pos, tup). Cost = FULL |dpos| @ cost_bps."""
    sp = margin.dropna() * sign
    sp = sp[sp.index >= min_start]
    m = sp.rolling(lookback, min_periods=lookback).mean()
    sd = sp.rolling(lookback, min_periods=lookback).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -gate] = 1.0
    pos[z > gate] = -1.0
    ret = sp.diff().shift(-1)
    gr = (pos * ret).dropna()
    tup = pos.diff().abs().reindex(gr.index).fillna(0.0)
    net = gr - tup * cost_bps / 1e4
    if do_borrow:
        short = pos.clip(upper=0.0).abs().reindex(net.index).fillna(0.0)
        net = net - 0.005 / 252 * (short > 0).astype(float)
    return net, gr, pos.reindex(gr.index), tup


def zscore_exit(margin, lookback=15, gate=2.0, exit_z=0.5, stop_z=3.5,
                min_start='2008-01-01', cost_bps=6.4, sign=+1):
    """z-rev WITH explicit exit bands: enter |z|>gate, exit |z|<exit_z, stop |z|>stop_z."""
    sp = margin.dropna() * sign
    sp = sp[sp.index >= min_start]
    m = sp.rolling(lookback, min_periods=lookback).mean()
    sd = sp.rolling(lookback, min_periods=lookback).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    state = 0.0
    for i, zz in z.items():
        if state == 0.0:
            if zz < -gate: state = 1.0
            elif zz > gate: state = -1.0
        elif state == 1.0:
            if abs(zz) < exit_z: state = 0.0
            elif zz > stop_z: state = -1.0
        elif state == -1.0:
            if abs(zz) < exit_z: state = 0.0
            elif zz < -stop_z: state = 1.0
        pos.loc[i] = state
    ret = sp.diff().shift(-1)
    gr = (pos * ret).dropna()
    tup = pos.diff().abs().reindex(gr.index).fillna(0.0)
    net = gr - tup * cost_bps / 1e4
    short = pos.clip(upper=0.0).abs().reindex(net.index).fillna(0.0)
    net = net - 0.005 / 252 * (short > 0).astype(float)
    return net, gr, pos.reindex(gr.index), tup


def vol_target(r, vt_ann=0.08, min_days=60, cap=3.0):
    rv = r.expanding(min_days).std() * np.sqrt(252)
    scale = (vt_ann / rv).clip(upper=cap)
    return (r * scale).dropna(), scale


# ---------------------------------------------------------------- stats / gates
def full_stats(r):
    r = r.dropna()
    if len(r) == 0: return dict(n=0, sr=np.nan)
    mu, sd = r.mean(), r.std()
    sr = mu / sd * np.sqrt(252) if sd > 0 else np.nan
    eq = (1 + r).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return dict(n=len(r), ann_geo=(eq.iloc[-1]) ** (252 / len(r)) - 1 if eq.iloc[-1] > 0 else -1,
                sr=sr, mdd=dd, negy=int((yr < 0).sum()), worst=yr.min() if len(yr) else 0,
                years=len(yr), ann_arith=mu * 252)


def halves_sr(r):
    r = r.dropna(); mid = r.index[len(r) // 2]
    a = full_stats(r[r.index <= mid])['sr']; b = full_stats(r[r.index > mid])['sr']
    return a, b


def negyr_tol(r, max_neg=2, floor=-0.05):
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = yr[yr < 0]; bad = neg[neg <= floor]
    return (len(neg) <= max_neg and len(bad) == 0), {int(k): round(v, 4) for k, v in neg.items()}


def scramble_p_lag(r, n=200, seed=0):
    r = r.dropna().values
    T = len(r); rng = np.random.default_rng(seed)
    real = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan
    if r.std() == 0: return 1.0, real
    cnt = 0
    for _ in range(n):
        lag = int(rng.integers(21, max(T - 21, 22)))
        rc = np.concatenate([r[lag:], r[:lag]])
        if rc.std() > 0 and rc.mean() / rc.std() * np.sqrt(252) >= real:
            cnt += 1
    return cnt / n, real


def flatten_gates(r):
    r = r.dropna()
    ac1 = r.autocorr(1)
    uniq = r.nunique() / len(r)
    v = r.values; runs = []; cur = 1
    for i in range(1, len(v)):
        if v[i] == v[i-1] and v[i] != 0.0: cur += 1
        else:
            if cur > 1: runs.append(cur)
            cur = 1
    if cur > 1: runs.append(cur)
    return dict(ac1=float(ac1), uniqR=float(uniq), max_run_nz=int(max(runs) if runs else 0))


def corr_to_champion(r, champ):
    j = pd.concat([r.rename('s'), champ.rename('c')], axis=1, join='inner').dropna()
    return float(j['s'].corr(j['c'])), len(j)


def evaluate(r, champ, name):
    out = {}
    st = full_stats(r)
    out['SR'] = st['sr']; out['ann_geo'] = st['ann_geo']; out['MDD'] = st['mdd']
    out['negyr'] = st['negy']; out['worst'] = st['worst']
    h1, h2 = halves_sr(r); out['H1_H2'] = (h1, h2)
    out['negyr_pass'], out['negyr_map'] = negyr_tol(r)
    p, sr_real = scramble_p_lag(r); out['scramble_p'] = p
    fg = flatten_gates(r); out['ac1'] = fg['ac1']; out['uniqR'] = fg['uniqR']
    c, n = corr_to_champion(r, champ); out['corr_champ'] = c; out['corr_n'] = n
    out['SR_pass'] = st['sr'] >= 0.6
    out['H_pass'] = h1 >= 0.3 and h2 >= 0.3
    out['scramble_pass'] = p < 0.05
    out['corr_pass'] = abs(c) < 0.15
    out['flatten_pass'] = fg['ac1'] < 0.5 and fg['uniqR'] >= 0.08
    all_pass = (out['SR_pass'] and out['H_pass'] and out['negyr_pass'] and
                out['scramble_pass'] and out['corr_pass'] and out['flatten_pass'])
    out['ALL_PASS'] = bool(all_pass)
    return out


def save_sleeve(net, path):
    net.dropna().to_csv(path, header=['ret']) if hasattr(net, 'dropna') else None

# spread builders
def build_crack321(wti, gas_bbl, uld_bbl):
    return (2 * gas_bbl + 1 * uld_bbl) / 3 - wti

def build_crack211(wti, gas_bbl, uld_bbl):
    return (1 * gas_bbl + 1 * uld_bbl) / 2 - wti


def position_rotation_p(pos, margin, n=200, seed=0, cost_bps=6.4, do_borrow=True,
                        vt=True, min_start='2008-01-01'):
    """PROPER scramble: circular-shift the POSITION series by a uniform lag in [21, T-21],
    recompute P&L through the FULL pipeline (costs, borrow, vol-target) and compare SR.
    This tests signal ALIGNMENT (timing), the honest discriminator for z-rev engines
    (a literal series-shuffle is degenerate for alternating-sign returns)."""
    sp = margin.dropna()
    sp = sp[sp.index >= min_start]
    pos = pos.reindex(sp.index).fillna(0.0)
    ret = sp.diff().shift(-1)
    def build(p):
        g = (p * ret).dropna()
        tup = p.diff().abs().reindex(g.index).fillna(0.0)
        net = g - tup * cost_bps / 1e4
        if do_borrow:
            short = p.clip(upper=0).abs().reindex(net.index).fillna(0.0)
            net = net - 0.005 / 252 * (short > 0).astype(float)
        if vt:
            net, _ = vol_target(net)
        return net.dropna()
    net_real = build(pos)
    real = net_real.mean() / net_real.std() * np.sqrt(252)
    pv = pos.values; T = len(pv); rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        lag = int(rng.integers(21, max(T - 21, 22)))
        psh = np.roll(pv, lag)
        p_ser = pd.Series(psh, index=pos.index)
        nb = build(p_ser)
        if len(nb) and nb.std() > 0:
            s = nb.mean() / nb.std() * np.sqrt(252)
            if s >= real: cnt += 1
    return cnt / n, real
