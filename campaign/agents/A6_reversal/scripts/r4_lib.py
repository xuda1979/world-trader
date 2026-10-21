"""A6 r4 shared: cached legs, composite circular-shift scramble (costs+VT repriced),
gates incl. charter targets SR>=0.8, ann>=12%, |corr|<=0.3 to champion."""
import sys, os, pickle
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import stats, halves_sr, vol_target, closes
import r3_lib as R3

CACHE = "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts/r4_cache"
os.makedirs(CACHE, exist_ok=True)
LIB = "/Users/daxu/software/world-trader/campaign/results/sleeve_library"

def rm_leg():
    """Gated resid-mom leg: raw net returns + weight path (cached)."""
    f = f"{CACHE}/rm.pkl"
    if os.path.exists(f):
        d = pickle.load(open(f, "rb")); return d["raw"], d["Wg"]
    from idea234_engine import resid_momentum, weights_long, rets, px
    _, resid_mom, _ = resid_momentum()
    ok = rets.notna() & (px.notna().cumsum() >= 120)
    W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
    mkt = px.mean(axis=1)
    ma = mkt.rolling(150, min_periods=75).mean()
    dd = mkt / mkt.rolling(252, min_periods=126).max() - 1.0
    n = len(mkt); state = np.zeros(n); s = 0; cnt = 0
    for i in range(n):
        if np.isnan(ma.iloc[i]): continue
        need = 20 if (not np.isnan(dd.iloc[i]) and dd.iloc[i] < -0.15) else 10
        if s == 1 and mkt.iloc[i] < ma.iloc[i]*0.98: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if mkt.iloc[i] > ma.iloc[i] else 0
            if cnt >= need: s = 1
        state[i] = s
    gate = pd.Series(state, index=mkt.index)
    Wg = W.mul(gate, axis=0)
    gross = (Wg.shift(1)*rets).sum(axis=1)["2007-01-01":]
    turn = (Wg.shift(1)-Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    raw = (gross - turn*6/1e4).dropna()
    pickle.dump({"raw": raw, "Wg": Wg}, open(f, "wb"))
    return raw, Wg

def load_series(path):
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index)
    s = pd.Series(df.iloc[:, 0].astype(float).values, index=df.index)
    return s[~s.index.duplicated(keep="last")].sort_index()

def vt(r, target):
    return vol_target(r.dropna(), target)[0]

def composite_sr(leg_nets, vt_lvl=0.15, mix_w=None):
    """legs already vt'd; equal-or-weighted mix, then mix-level VT."""
    df = pd.concat(leg_nets, axis=1).dropna(how="all").fillna(0.0)
    w = pd.Series(mix_w, index=df.columns) if mix_w is not None else pd.Series(1.0/len(df.columns), index=df.columns)
    mix = df.mul(w, axis=1).sum(axis=1)
    mix = mix[mix.index >= "2007-01-01"]
    return vt(mix, vt_lvl)

def composite_scramble_p(real_sr, leg_specs, n=200, seed=13, vt_lvl=0.15, start="2007-01-01"):
    """Composite signal-scramble: independent circular shifts of each leg's timing
    (leg1: weight path rolled -> costs repriced from rets; library legs: return series rolled),
    all legs re-vt'd, mix re-vt'd. p = P(null SR >= real)."""
    from idea234_engine import rets
    rng = np.random.default_rng(seed)
    idx = rets.index
    cnt = 0
    for rep in range(n):
        comps = []
        for spec in leg_specs:
            if spec["kind"] == "W":
                W = spec["W"]; Wv = W.values
                sh = int(rng.integers(252, len(idx)-252))
                Ws = pd.DataFrame(np.roll(Wv, sh, axis=0), index=idx, columns=W.columns)
                gross = (Ws.shift(1)*rets).sum(axis=1)[start:]
                turn = (Ws.shift(1)-Ws.shift(2)).abs().sum(axis=1)[start:].fillna(0.0)
                comps.append(vt((gross - turn*6/1e4).dropna(), vt_lvl))
            else:
                x = spec["ret"]
                sh = int(rng.integers(252, len(x)-252))
                comps.append(vt(pd.Series(np.roll(x.values, sh), index=x.index), vt_lvl))
        sr_series = composite_sr(comps, vt_lvl)
        s = sr_series.dropna()
        sr = s.mean()/s.std()*np.sqrt(252) if s.std() > 0 else 0.0
        if real_sr <= sr: cnt += 1
    return cnt/n

def yearly(r):
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    neg = {int(y): round(v*100, 1) for y, v in yr.items() if v < 0}
    return neg, yr

def corr_to_champion(r, freq="ME"):
    champ, _ = R3.champion_mix()
    a = (1+r.dropna()).resample(freq).prod()-1 if freq else r
    b = (1+champ).resample(freq).prod()-1 if freq else champ
    j = pd.concat([a, b], axis=1).dropna()
    return j.corr().iloc[0, 1], len(j)

def full_gates(r, tag, vt_lvl=0.15, verbose=True, charter=True):
    r = r.dropna()
    s = stats(r); h = halves_sr(r); neg, yr = yearly(r)
    real = s["sr"]
    g = {"full>=0.8": real >= 0.8 if charter else real >= 0.6,
         "ann>=12%": s["ann_ret"] >= 12.0,
         "H1>=0.3": h["H1"] >= 0.3, "H2>=0.3": h["H2"] >= 0.3,
         "negYr<=2": s["neg_years"] <= 2, "worst>-5%": s["worst_year"] > -5.0}
    cm, ncm = corr_to_champion(r)
    cd, _ = corr_to_champion(r, freq=None)
    g["|corrM|<=0.3"] = abs(cm) <= 0.3
    ok = all(g.values())
    if verbose:
        print(f"{tag:46s} SR={real:.2f} ann={s['ann_ret']:5.1f}% vol={s['ann_vol']:4.1f}% H1={h['H1']:.2f} H2={h['H2']:.2f} "
              f"negYr={s['neg_years']}{neg} worst={s['worst_year']:5.1f}% corrM={cm:+.2f} corrD={cd:+.2f}(n={ncm})"
              + ("  *** PASS ***" if ok else "  fail:" + str([k for k, v in g.items() if not v])))
    return ok, dict(sr=real, ann=s["ann_ret"], halves=h, neg=neg, worst=s["worst_year"], corrM=cm, corrD=cd, gates=g)
