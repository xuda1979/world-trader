"""HUNT_VOL2 round-1 shared lib: CBOE vol-surface features (VVIX/SKEW/GVZ/OVX/
VIX9D/3M/6M/RVX) as T+1 risk gates / standalone sleeves.
Costs: 6.4bps one-side FULL |dW| + borrow 0.5%/yr on short notional.
Vol target 10% ann, trailing-only (min 60d), scale clip <= 3.0. Gates per
GATES_CONTRACT.md."""
import sys
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
VOLDIR = f"{ROOT}/tools/quant/data/more_vol"
sys.path.insert(0, f"{ROOT}/campaign")

COST = 6.4          # bps one-side on FULL |dW| (TRADE_RECORD_STANDARD)
BORROW = 0.005      # /yr on short notional
ANN = 252.0

_CHAMP = None

def t1(sig: pd.Series) -> pd.Series:
    """T+1: decide at close t, hold at t+1. First row flat."""
    return sig.shift(1).fillna(0.0)

def vt_scale(r: pd.Series, target=0.10, minlen=60, cap=3.0) -> pd.Series:
    """Expanding trailing vol scale using r[0..t-1] only; clip [0, cap]."""
    vol = r.expanding(min_periods=minlen).std(ddof=1) * np.sqrt(ANN)
    s = (target / vol.replace(0.0, np.nan)).clip(upper=cap)
    return s.shift(1).fillna(0.0)

def net_of(pos: pd.Series, ret: pd.Series, vt="on") -> pd.Series:
    """net daily returns: pos (already T+1-shifted or not; shift applied here if raw).
    Convention: pass RAW signal; we apply T+1 here.
    vt: 'on' = trailing 10% vol-target (clip<=3), None = off."""
    p = t1(pos)
    r = ret.reindex(p.index).fillna(0.0)
    if vt == "on":
        sc = vt_scale(r, cap=3.0)
        p = p * sc
    to = p.diff().abs(); to.iloc[0] = abs(p.iloc[0])
    gross = p * r
    net = gross - to * COST / 1e4 - (-p.clip(upper=0.0)) * BORROW / ANN
    return net.dropna()

def stats(r: pd.Series) -> dict:
    r = r.dropna()
    if len(r) < 2 or r.std() == 0:
        return dict(n=len(r), sr=0.0, ann=0.0, vol=0.0, neg_yr=0, n_yr=0,
                    worst=0.0, h1=0.0, h2=0.0, yearly={})
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    k = len(r) // 2
    h1 = r.iloc[:k].mean() / r.iloc[:k].std() * np.sqrt(ANN) if k > 1 else 0.0
    h2 = r.iloc[k:].mean() / r.iloc[k:].std() * np.sqrt(ANN) if len(r) - k > 1 else 0.0
    return dict(n=len(r), sr=float(r.mean() / r.std() * np.sqrt(ANN)),
                ann=float(r.mean() * ANN * 100), vol=float(r.std() * np.sqrt(ANN) * 100),
                neg_yr=int((yr < 0).sum()), n_yr=len(yr),
                worst=float(yr.min() * 100), h1=float(h1), h2=float(h2),
                yearly={int(a): round(b * 100, 2) for a, b in yr.items()})

def scramble_p(pos: pd.Series, ret: pd.Series, n=200, seed=0) -> float:
    """Signal-scramble: permute positions against REAL date-aligned returns,
    reapply T+1 + costs (gross, no vt — same treatment as real book)."""
    rng = np.random.default_rng(seed)
    p = t1(pos)
    r = ret.reindex(p.index).fillna(0.0).values
    pv = p.values
    def net_of_arr(q):
        to = np.abs(np.diff(q, prepend=0.0))
        return pd.Series(q * r - to * COST / 1e4 + np.minimum(q, 0) * -BORROW / ANN,
                         index=p.index)
    real = stats(net_of_arr(pv))["sr"]
    cnt = 0
    for _ in range(n):
        if stats(net_of_arr(rng.permutation(pv)))["sr"] >= real:
            cnt += 1
    return cnt / n

def champion() -> pd.Series:
    global _CHAMP
    if _CHAMP is None:
        _CHAMP = pd.read_csv(
            f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
            index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    return _CHAMP

def corr_champ(net: pd.Series) -> float:
    ch = champion()
    j = pd.concat([net.rename("a"), ch.rename("c")], axis=1, join="inner").dropna()
    return float(j.corr().iloc[0, 1])

def corr_library(net: pd.Series, topn=5) -> dict:
    """Max |corr| vs all 83 sleeve-library CSVs + champion."""
    import glob, os
    outs = {}
    for p in glob.glob(f"{ROOT}/campaign/results/sleeve_library/*.csv"):
        nm = os.path.basename(p)[:-4]
        try:
            l = pd.read_csv(p, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
            j = pd.concat([net.rename("a"), l.rename("b")], axis=1, join="inner").dropna()
            if len(j) >= 250:
                outs[nm] = float(j.corr().iloc[0, 1])
        except Exception:
            pass
    j = pd.concat([net.rename("a"), champion().rename("CHAMP")], axis=1, join="inner").dropna()
    outs["CHAMP"] = float(j.corr().iloc[0, 1])
    s = pd.Series(outs)
    top = s.reindex(s.abs().sort_values(ascending=False).index)[:topn]
    return dict(n=len(s), maxabs=float(s.abs().max()), top={k: round(v, 2) for k, v in top.items()})

def vol(name: str) -> pd.Series:
    """Load a CBOE close series; VVIX trimmed to >=2007-01-01 (2006=pilot junk)."""
    df = pd.read_csv(f"{VOLDIR}/{name}.csv", parse_dates=["date"]).set_index("date")
    s = df["close"].astype(float)
    s = s[s > 0]
    if name == "VVIX":
        s = s[s.index >= "2007-01-01"]
    return s[~s.index.duplicated(keep="last")].sort_index()

def spy() -> pd.Series:
    """Spliced SPX proxy returns 1993+ (same as a5_r6_lib.spy_returns_2000)."""
    sys.path.insert(0, ROOT)
    from campaign.harness import data as D
    e = D.fred("spy_early")
    b = D.closes()["SPY"]; b.index = b.index.tz_localize(None)
    re_ = e.pct_change(); rb = b.pct_change()
    r = pd.concat([re_[re_.index < "2006-01-01"], rb[rb.index >= "2006-09-01"]])
    r = r[~r.index.duplicated(keep="last")].sort_index()
    seam = rb.index[rb.index >= "2006-09-01"][0]
    r.loc[seam] = np.nan
    return r.dropna()

def etf_ret(name: str) -> pd.Series:
    path = f"{ROOT}/tools/quant/data/more_etf/{name}.csv"
    import os
    if not os.path.exists(path):  # SPY et al live in twelve_liq, not more_etf
        path = f"{ROOT}/tools/quant/data/twelve_liq/{name}.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df["close"].astype(float).pct_change()

def gates_line(name, net, pos, R, extra="") -> tuple:
    """All gates a-e + f-corr + g-vt built-in. Returns (okdict, line)."""
    s = stats(net)
    sp = scramble_p(pos, R, n=200, seed=7)
    cc = corr_champ(net)
    cl = corr_library(net)
    ok = dict(
        a_sr=s["sr"] >= 1.0,
        b_plateau=None,  # filled by caller (grid)
        c_halves=(s["h1"] >= 0.5) and (s["h2"] >= 0.5),
        d_yearly=(s["neg_yr"] <= 2) and (s["worst"] > -5.0),
        e_scramble=sp <= 0.05,
        f_corr=abs(cc) < 0.15,
    )
    line = (f"[{name}] n={s['n']} SR={s['sr']:.2f} ann={s['ann']:.2f}% vol={s['vol']:.1f}% "
            f"negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% H1={s['h1']:.2f} H2={s['h2']:.2f} "
            f"scram_p={sp:.3f} corrChamp={cc:+.2f} corrLibMax={cl['maxabs']:.2f} {extra}")
    return ok, line
