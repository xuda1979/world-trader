"""Local loader for A6 — dedupes per-file (shared closes() breaks on dup dates)."""
import os, numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
PANEL = f"{ROOT}/tools/quant/data/twelve_big"
COST_BPS = 6.0

def load_panel():
    out = {}
    for f in os.listdir(PANEL):
        if f.endswith(".csv"):
            df = pd.read_csv(os.path.join(PANEL, f), parse_dates=["date"], index_col="date")
            df = df[~df.index.duplicated(keep="last")].sort_index()
            out[f[:-4]] = df
    return out

def closes():
    ps = load_panel()
    px = pd.DataFrame({k: v["close"] for k, v in ps.items()}).sort_index()
    return px

def volumes():
    ps = load_panel()
    return pd.DataFrame({k: v["vol"] for k, v in ps.items()}).sort_index()

def stats(r):
    r = r.dropna()
    mu, sd = r.mean(), r.std()
    sr = mu/sd*np.sqrt(252) if sd > 0 else 0.0
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    return dict(n=len(r), start=str(r.index[0].date()), end=str(r.index[-1].date()),
                ann_ret=mu*252*100, ann_vol=sd*np.sqrt(252)*100, sr=sr,
                neg_years=int((yr<0).sum()), years=len(yr),
                worst_year=yr.min()*100, yearly={int(k): v*100 for k,v in yr.items()})

def halves_sr(r):
    mid = r.dropna().index[len(r.dropna())//2]
    rr = r.dropna()
    out = {}
    for name, seg in [("H1", rr[rr.index <= mid]), ("H2", rr[rr.index > mid])]:
        s = stats(seg); out[name] = s["sr"]
    return out

def scramble_pvalue(r, n=200, seed=7):
    """Shuffle the ORDER of daily returns 200x, compute SR each time; p = frac(scrambled SR >= real).
    Tests whether the return series' SR is higher than a path-shuffled version of itself."""
    r = r.dropna().values
    real = r.mean()/r.std()*np.sqrt(252)
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        rs = rng.permutation(r)
        sr = rs.mean()/rs.std()*np.sqrt(252)
        if real <= sr: cnt += 1
    return cnt/n

def check_gates(r, name=""):
    s = stats(r); h = halves_sr(r); p = scramble_pvalue(r)
    g = {}
    g["full_sr>=0.6"] = s["sr"] >= 0.6
    g["H1>=0.3"] = h["H1"] >= 0.3
    g["H2>=0.3"] = h["H2"] >= 0.3
    g["neg_years<=2"] = s["neg_years"] <= 2
    g["worst_year>-5%"] = s["worst_year"] > -5.0
    g["scramble_p<0.05"] = p < 0.05
    print(f"--- {name}: SR={s['sr']:.2f} ann={s['ann_ret']:.1f}% vol={s['ann_vol']:.1f}% H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}/{s['years']} worst={s['worst_year']:.1f}% scr_p={p:.3f}")
    print(f"    gates: {g}")
    ok = all(g.values())
    return ok, dict(stats=s, halves=h, scramble_p=p, gates=g)

def vol_target(r, target=0.10, min_obs=60):
    """Expanding-window vol targeting using ONLY trailing data. Returns realized net-of-targeting returns."""
    r = r.copy()
    sd = r.expanding(min_obs).std().shift(1)   # trailing vol up to t-1
    lev = (target/np.sqrt(252)/sd).clip(0, 5).fillna(0.0)
    return r*lev, lev

def yearly_neg_ok(yearly, maxneg=2, floor=-0.05):
    bad = [y for y,v in yearly.items() if v < floor]
    return len(bad) <= maxneg, bad
