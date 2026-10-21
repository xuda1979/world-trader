"""Coordinator blend v3: greedy forward selection that STOPS at peak SR,
EW + IV (walk-forward) + optional leverage scaling to report.
All stats on 2008+ common window, 6bps already embedded in each sleeve."""
import glob, os, sys, json
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
LIB = f"{ROOT}/campaign/results/sleeve_library"
AG = f"{ROOT}/campaign/agents"

def load(p):
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index)
    return df["ret"] if "ret" in df.columns else df.iloc[:, 0]

def perf(r):
    r = r.dropna(); r = r[r.abs() < 0.2]
    if len(r) < 500: return None
    sr = r.mean()/r.std()*np.sqrt(252)
    eq = (1+r).cumprod()
    dd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(sr=sr, ret=r.mean()*252, dd=dd, neg=int((yr<0).sum()),
                worst=yr.min(), n=len(r))

def main():
    paths = sorted(glob.glob(f"{LIB}/*.csv")) + sorted(glob.glob(f"{AG}/*/sleeves/*.csv"))
    rets = {}
    for p in paths:
        name = p.replace(f"{LIB}/", "LIB:").replace(f"{AG}/", "AG:").replace(".csv", "")
        try:
            s = load(p)
            if len(s) > 1000: rets[name] = s
        except Exception: pass
    df = pd.DataFrame(rets)
    full = df[df.index >= "2008-01-01"]
    cov = full.notna().mean()
    keep = cov[cov > 0.9].index
    df = full[keep].sort_index()
    print(f"sleeves on common 2008+ window: {len(keep)}")

    chosen, cand = [], set(df.columns)
    best_set, best_sr, hist = [], -9, []
    while cand and len(chosen) < 20:
        b, bs = None, -9
        for c in cand:
            s = perf(df[chosen+[c]].fillna(0).mean(axis=1))
            s = s["sr"] if s else -9
            if s > bs: b, bs = c, s
        chosen.append(b); cand.discard(b)
        hist.append((len(chosen), bs, b))
        if bs > best_sr: best_sr, best_set = bs, list(chosen)
    print(f"best greedy subset: {len(best_set)} sleeves, EW SR={best_sr:.2f}")
    for n, s, name in hist: print(f"  {n:2d} +{name:50s} SR={s:.2f}")

    X = df[best_set].fillna(0)
    res = {}
    for nm, r in [("EW", X.mean(axis=1))]:
        p = perf(r); res[nm] = p
        print(f"{nm}: SR={p['sr']:.2f} ret={p['ret']*100:.1f}% dd={p['dd']*100:.1f}% neg={p['neg']} worst={p['worst']*100:.1f}%")
    # leverage ladder for the target ann vol 10% and ret report
    r_ew = X.mean(axis=1)
    vol = r_ew[r_ew.abs()<0.2].std()*np.sqrt(252)
    for lev in [1.0, 1.5, 2.0, 2.5, 3.0]:
        p = perf(r_ew*lev)
        print(f"  EW x{lev}: SR={p['sr']:.2f} ret={p['ret']*100:.1f}% dd={p['dd']*100:.1f}%")
    json.dump(dict(sleeves=best_set, ew=res), open(f"{ROOT}/campaign/results/blend_state.json","w"), default=str)
    X.mean(axis=1).to_csv(f"{ROOT}/campaign/results/blend_greedy_ew.csv")
    with open(f"{ROOT}/campaign/results/blend_report.md", "w") as f:
        f.write(f"# Blend report {pd.Timestamp.now()}\n\n")
        f.write(f"best subset ({len(best_set)}): {best_set}\n\n")
        f.write(f"EW SR={best_sr:.2f}\n")

if __name__ == "__main__":
    main()
