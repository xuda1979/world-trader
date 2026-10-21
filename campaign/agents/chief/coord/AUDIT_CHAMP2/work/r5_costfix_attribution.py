#!/usr/bin/env python3
"""R5(a) CHAMPION20Y_V2 costfix attribution (AUDIT_CHAMP2 round 5).

Q: do the committed 2026-09-01 CHAMPION20Y_V2 CSVs reproduce from the PRE-costfix
   sleeve bytes (git blobs at de890d0e/335eff07, i.e. before costfix commit b268e524)?
Method: swap each changed sleeve back to its pre-09-07 blob (in-memory, no tree edits),
rebuild A/B/BAL exactly as champion20y_build.py does, compare to committed CSVs.
"""
import subprocess, hashlib, io, sys
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
COST = 6 / 10000
CFX = "b268e524"  # costfix commit

POOL = {
 "A5r7":    "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "a6r7":    "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "A1inf":   "campaign/agents/E1_20yspan/sleeves/E1_A1inf_GLD_2006.csv",
 "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "XGB1y":   "campaign/results/sleeve_library/XGB1y_deploy.csv",
 "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "brwt":    "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "B3momhml":"campaign/agents/B3_antiregime/ref_momhml_composite.csv",
 "C5ng":    "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "MHX":     "campaign/agents/COORD/sleeves/MHX_multihorizon_xgb.csv",
}

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def load_blob(sha, p):
    r = subprocess.run(["git", "show", f"{sha}:{p}"], cwd=ROOT, capture_output=True)
    assert r.returncode == 0, f"{sha}:{p}"
    df = pd.read_csv(io.BytesIO(r.stdout), index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def vt(r, tgt, min_win=60, cap=8.0):
    vol = r.rolling(min_win).std().shift(1) * np.sqrt(252)
    s = (tgt / vol).clip(upper=cap)
    s[vol.isna()] = 0
    return r * s.fillna(0), s

def construct(pool, TGT, THR, start, FR=0.5, LB=126):
    V, S = {}, {}
    for n, src in pool.items():
        r = load(src) if isinstance(src, str) else load_blob(*src)
        v, s = vt(r, 0.10); V[n] = v; S[n] = s
    Vn = pd.DataFrame(V); Sn = pd.DataFrame(S)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= start]
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, _ = vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(LB).max().shift(1); tdd = eq.shift(1) / rm - 1
    sc = pd.Series(np.where(tdd < -THR, FR, 1.0), index=b.index)
    b = b * sc; dsc = sc.diff().abs() * 0.5
    tot = tw.reindex(b.index).fillna(0) + dsc.fillna(0)
    return (b - tot * COST).dropna()

def stats(r):
    r = r.dropna()
    yrs = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    eq = (1+r).cumprod()
    dd = (eq/eq.cummax()-1).min()
    ann = eq.iloc[-1]**(252/((r.index[-1]-r.index[0]).days or 1))-1
    sr = r.mean()/r.std(ddof=1)*np.sqrt(252)
    return ann, sr, dd, int((yrs<0).sum()), len(r)

def pre_sha(p):
    # last commit on/before 2026-09-06 touching p
    logs = subprocess.run(["git","log","--format=%H|%aI","--",p],cwd=ROOT,
                          capture_output=True,text=True).stdout.strip().splitlines()
    for l in logs:
        c,d = l.split("|")
        if d[:10] <= "2026-09-06":
            return c
    return None

# 1. identify changed sleeves
changed = {}
print("=== costfix-wave changes among the 13 POOL20 sleeves ===")
for n, p in POOL.items():
    cur = hashlib.sha256(open(f"{ROOT}/{p}","rb").read()).hexdigest()[:12]
    pc = pre_sha(p)
    if pc is None:
        print(f"{n:9s} no pre-costfix blob"); continue
    old = hashlib.sha256(subprocess.run(["git","show",f"{pc}:{p}"],cwd=ROOT,
                         capture_output=True).stdout).hexdigest()[:12]
    if old == cur:
        print(f"{n:9s} unchanged (blob {cur} since <=09-06)")
    else:
        j = pd.concat([load_blob(pc,p).rename("old"), load(p).rename("new")], axis=1, join="inner").dropna()
        dev = float((j.old-j.new).abs().max())
        print(f"{n:9s} CHANGED by costfix: blob {old} -> {cur}, inner-join n={len(j)}, max|old-new|={dev:.3e}")
        changed[n] = pc

# 2. rebuild with pre-costfix bytes for the changed ones
pool = dict(POOL)
for n, pc in changed.items():
    pool[n] = (pc, POOL[n])
A = construct(pool, 0.090, 0.030, "2006-10-01")
B = construct(pool, 0.106, 0.0255, "2006-10-01")
BAL = ((A+B)/2).dropna()
print(f"\n=== rebuild from PRE-costfix bytes ({len(changed)} swapped) vs committed CSVs ===")
for k, r in [("BALANCED",BAL),("SAFE",A),("AGGRESSIVE",B)]:
    old = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_CHAMPION20Y_V2_{k}_daily.csv",
                      index_col=0, parse_dates=True).iloc[:,0]
    j = pd.concat([old.rename("old"), r.rename("new")], axis=1, join="inner").dropna()
    md = float((j.old-j.new).abs().max())
    print(f"{k:10s} n_inner={len(j)} max|new-old| = {md:.3e}  {'IDENTICAL' if md<1e-12 else 'DIFF'}")

print("\n=== stats: pre-costfix rebuild vs committed vintage (BALANCED) ===")
old = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_CHAMPION20Y_V2_BALANCED_daily.csv",
                  index_col=0, parse_dates=True).iloc[:,0]
for tag, r in [("committed(0901)", old), ("pre-costfix rebuild", BAL)]:
    ann, sr, dd, ny, n = stats(r)
    print(f"{tag:20s} ann={ann*100:6.2f}%  SR={sr:5.2f}  MDD={dd*100:6.2f}%  negyrs={ny}  n={n}")

# 3. POST-costfix rebuild stats (what the rebuilt 20y champion would be)
pool2 = dict(POOL)
A2 = construct(pool2, 0.090, 0.030, "2006-10-01")
B2 = construct(pool2, 0.106, 0.0255, "2006-10-01")
BAL2 = ((A2+B2)/2).dropna()
print("\n=== stats: POST-costfix rebuild (current tree bytes, BALANCED) ===")
ann, sr, dd, ny, n = stats(BAL2)
print(f"post-costfix           ann={ann*100:6.2f}%  SR={sr:5.2f}  MDD={dd*100:6.2f}%  negyrs={ny}  n={n}")
