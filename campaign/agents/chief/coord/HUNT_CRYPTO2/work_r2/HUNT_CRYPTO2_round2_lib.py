"""Importable round-2 core (gates/metrics) — shared by HUNT_CRYPTO2_round2.py and the audit.
Sign convention: drawdowns are NEGATIVE; d_mdd = gated - champ; positive d_mdd = improvement."""
import numpy as np, pandas as pd
from bt import metrics

ROOT = "/Users/daxu/software/world-trader"
DATA = f"{ROOT}/tools/quant/data/more_crypto"
COST = 6.4 / 1e4
_ENV = None


def load_env():
    """Champion + crypto price env (cached)."""
    global _ENV
    if _ENV is not None:
        return _ENV
    CHAMP = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0]
    IDX = CHAMP.index

    def px(coin):
        return pd.read_csv(f"{DATA}/{coin}.csv", index_col=0, parse_dates=True)['close'].astype(float)

    def to_idx(s):
        return s.reindex(IDX.union(s.index)).ffill().reindex(IDX)

    BTCi, ETHi = to_idx(px('BTC')), to_idx(px('ETH'))
    ALTS = ['BNB', 'ADA', 'XRP', 'SOL', 'DOT', 'LINK', 'LTC', 'MATIC', 'AVAX', 'DOGE']
    basket = pd.concat({c: px(c) for c in ALTS}, axis=1).dropna(how='all')
    alt_ew = basket.pct_change().mean(axis=1)
    alt_px_i = (1 + to_idx(alt_ew).fillna(0)).cumprod()
    _ENV = dict(CHAMP=CHAMP, IDX=IDX, BTCi=BTCi, ETHi=ETHi, alt_px_i=alt_px_i,
                CHAMP_SR=metrics.sharpe_d(CHAMP), CHAMP_ANN=metrics.ann_geo(CHAMP),
                CHAMP_MDD=metrics.max_dd(CHAMP))
    return _ENV


def compare(a, op, b):
    """NaN-preserving comparison (NaN = warmup, mapped to gate 1.0 downstream)."""
    a, b = pd.Series(a), pd.Series(b)
    out = (a > b) if op == '>' else (a <= b)
    return out.where(a.notna() & b.notna(), np.nan)


def binary_gate(cond, scale, extra_lag=0):
    """cond True = risk-ON (gate 1.0); False -> `scale`. Warmup NaN => no action (1.0).
    T+1 via shift(1+extra_lag)."""
    IDX = load_env()['IDX']
    cond = pd.Series(cond)
    g = pd.Series(np.where(cond.fillna(True).astype(bool), 1.0, scale), index=cond.index)
    g[cond.isna()] = 1.0
    g = g.reindex(IDX.union(g.index)).ffill().reindex(IDX)
    return g.shift(1 + extra_lag).fillna(1.0), int(cond.isna().sum())


def gate_metrics(g, env):
    """Champion * gate, flip costs |dg|*6.4bps, full delta report (R2 conventions)."""
    CHAMP = env['CHAMP']
    gated = CHAMP * g
    flip = g.diff().abs().fillna(0.0)
    costed = gated - flip * COST
    ann, mdd, sr = metrics.ann_geo(costed), metrics.max_dd(costed), metrics.sharpe_d(costed)
    neg, worst = metrics.neg_years(costed)
    return dict(costed=costed, g=g, sr=sr, d_sr=sr - env['CHAMP_SR'],
                ann=ann, d_ann=ann - env['CHAMP_ANN'], mdd=mdd, d_mdd=mdd - env['CHAMP_MDD'],
                neg=neg, worst=worst, off=float((g < 1.0).mean()),
                n_flip=int((flip > 0).sum()))


def cond_a_ratio(ma):
    """ETH-BTC ratio > its MA_n (risk-ON when ratio trending up)."""
    env = load_env()
    ratio = (env['ETHi'] / env['BTCi']).dropna()
    return compare(ratio, '>', ratio.rolling(ma).mean())


def cond_a_dom(ma):
    """BTC-dominance PROXY: BTC price / EW alt-10 price index > MA_n (price-only, no caps)."""
    dom = (load_env()['BTCi'] / load_env()['alt_px_i']).dropna()
    return compare(dom, '>', dom.rolling(ma).mean())


def cond_b_vov(vw, k):
    """BTC realized vol-of-vol <= trailing 252d median (risk-ON in calm-vov states)."""
    bret = load_env()['BTCi'].pct_change().fillna(0.0)
    vol = bret.rolling(vw).std() * np.sqrt(252)
    vov = vol.rolling(k).std()
    return compare(vov, '<=', vov.rolling(252, min_periods=60).quantile(0.5))


def random_gate_null(CHAMP, p_off, flip_prob, seed, n=200, scale=0.5):
    """Persistence-matched Markov null for the dMDD bar (replaces broken AUDIT T1).

    Draws two-state gates (1.0 / `scale`) with stationary transition probs solved so the
    OFF-fraction and daily flip prob match the real gate. Returns (g_of_last_draw, diag)
    with per-draw dMDD stats in diag (charging |dg|*6.4bps flip costs like the real gates).

    Old T1 bug (recorded for the audit trail): it drew flip locations at prob=flipfrac,
    ffilled, then overwrote the ENTIRE series with np.where(u < p_off/flip_prob, ...) and
    p_off/flip_prob = 17.5 > 1 -> all 200 draws collapsed to the CONSTANT 0.5 gate
    (off%=100%, every draw dMDD=+3.383pp, zero variance). Not a null.
    """
    from scipy.optimize import fsolve
    rng = np.random.default_rng(seed)
    N = len(CHAMP)
    p01, p10 = fsolve(lambda p: [2*p[0]*p[1]/(p[0]+p[1]) - flip_prob,
                                 p[0]/(p[0]+p[1]) - p_off], [0.008, 0.03])
    dmdd = lambda g: metrics.max_dd(CHAMP*g - g.diff().abs().fillna(0)*COST) - metrics.max_dd(CHAMP)
    base = metrics.max_dd(CHAMP)
    ds = np.empty(n)
    last = None
    for j in range(n):
        s = np.empty(N)
        on = rng.random() >= p_off
        s[0] = 1.0 if on else scale
        for i in range(1, N):
            if rng.random() < (p01 if on else p10):
                on = not on
            s[i] = 1.0 if on else scale
        g = pd.Series(s, index=CHAMP.index).shift(1).fillna(1.0)
        ds[j] = dmdd(g)
        last = g
    return last, dict(off_frac=float((last < 1.0).mean()),
                      n_flips=int(last.diff().abs().fillna(0).gt(0).sum()),
                      mean_ep_len=float(len(CHAMP) / max(1, last.diff().abs().fillna(0).gt(0).sum())),
                      dMDD_med=float(np.median(ds)), dMDD_p90=float(np.percentile(ds, 90)),
                      dMDD_std=float(ds.std()))


def all_configs():
    """The 34-config charter grid: (name, cond, scale)."""
    cfgs = []
    for ma in [20, 50, 100, 200]:
        for sc in [0.3, 0.5, 0.7, 0.9]:
            cfgs.append((f"ratio_ma{ma}_sc{sc}", cond_a_ratio(ma), sc))
    for ma in [20, 50, 100, 200]:
        cfgs.append((f"dom_ma{ma}_sc0.5", cond_a_dom(ma), 0.5))
    for vw in [10, 20, 30]:
        for k in [20, 60, 126]:
            for sc in [0.5, 0.7]:
                cfgs.append((f"vov_v{vw}_k{k}_sc{sc}", cond_b_vov(vw, k), sc))
    return cfgs
