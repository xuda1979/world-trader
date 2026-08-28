"""A5 r3 shared: gates, scramble (fixed signal-permutation version), corr-to-library."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import data as D

def sr(r):
    r = r.dropna()
    return 0.0 if len(r) < 2 or r.std() == 0 else r.mean() / r.std() * np.sqrt(252)

def yearly(r):
    return r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)

def stats(r):
    y = yearly(r.dropna())
    return dict(n=len(r), sr=sr(r), ann=r.mean()*252*100, vol=r.std()*np.sqrt(252)*100,
                neg_yr=int((y < 0).sum()), n_yr=len(y), worst=float(y.min()*100),
                yearly={int(k): round(v*100, 2) for k, v in y.items()})

def halves(r):
    r = r.dropna(); mid = r.index[len(r)//2]
    return sr(r[r.index <= mid]), sr(r[r.index > mid])

def vt_scale(net_gross, target=0.10, minlen=60, cap=2.5):
    """Expanding trailing-only vol scale (position for t+1)."""
    vol = net_gross.expanding(min_periods=minlen).std()
    return (target / np.sqrt(252) / vol).clip(0, cap).shift(1).fillna(0.0)

def net_of_pos(pos, r1, vt=True):
    """pos decided at t (data<=t) -> T+1, 6bps one-side on turnover, trailing vt10."""
    pos1 = pos.shift(1).fillna(0.0)
    to = pos1.diff().abs().fillna(pos1.abs())
    gross = pos1 * r1.reindex(pos.index).fillna(0.0) - to * D.COST / 1e4
    if vt:
        sc = vt_scale(gross)
        posf = pos1 * sc
        to2 = posf.diff().abs().fillna(posf.abs())
        gross = posf * r1.reindex(pos.index).fillna(0.0) - to2 * D.COST / 1e4
    return gross.dropna()

def scramble_sig(pos, r1, n=200, seed=0):
    """FIXED version: permute POSITIONS vs REAL date-aligned returns, re-apply costs. p = P(permSR >= real)."""
    rng = np.random.default_rng(seed)
    idx = pos.index
    rr = r1.reindex(idx).fillna(0.0).values
    pv = pos.values
    def net_of(p):
        p1 = np.roll(p, 1); p1[0] = 0.0
        to = np.abs(np.diff(p, prepend=0.0))
        return pd.Series(p1 * rr - to * D.COST / 1e4, index=idx)
    real = sr(net_of(pv))
    cnt = sum(1 for _ in range(n) if sr(net_of(rng.permutation(pv))) >= real)
    return real, cnt / n

def gates_a_c_d(name, net, extra=""):
    s = stats(net); h1, h2 = halves(net)
    ok_a = s['sr'] >= 0.6; ok_c = (h1 >= 0.3) and (h2 >= 0.3)
    ok_d = (s['neg_yr'] <= 2) and (s['worst'] > -5.0)
    ok = ok_a and ok_c and ok_d
    print(f"[{name}] n={s['n']} SR={s['sr']:.2f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% "
          f"negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% H1={h1:.2f} H2={h2:.2f} "
          f"gates a={ok_a} c={ok_c} d={ok_d} {'PASS_acd' if ok else 'FAIL'} {extra}")
    print(f"    yearly={s['yearly']}")
    return dict(ok=ok, sr=s['sr'], h1=h1, h2=h2, neg=s['neg_yr'], worst=s['worst'])

def lib_corr(r, extra_series=None):
    import os
    names = sorted(f[:-4] for f in os.listdir(D.SLEEVE_LIB) if f.endswith(".csv"))
    out = {}
    for nm in names:
        l = pd.read_csv(f"{D.SLEEVE_LIB}/{nm}.csv", index_col=0, parse_dates=True).iloc[:, 0].astype(float)
        j = pd.concat([r, l], axis=1).dropna()
        if len(j) > 250: out[nm] = float(j.corr().iloc[0, 1])
    if extra_series:
        for nm, l in extra_series.items():
            j = pd.concat([r, l], axis=1).dropna()
            if len(j) > 250: out[nm] = float(j.corr().iloc[0, 1])
    return out

def corr_summary(cs):
    top = sorted(cs.items(), key=lambda kv: -abs(kv[1]))[:5]
    mean_abs = np.mean([abs(v) for v in cs.values()])
    return f"mean|corr|={mean_abs:.2f} top5={[(k, round(v,2)) for k,v in top]}"
