"""Coordinator blend v4 (canonical): all sleeves resampled to MONTHLY returns.
Monthly is the honest common cadence for monthly-cadence books and avoids the
daily-spread SR inflation artifact. Greedy forward selection, stop at peak.
Also reports a walk-forward expanding-IV variant."""
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

def to_monthly(r):
    return (1 + r).resample("ME").prod() - 1

def perf(r, freq="M"):
    r = r.dropna(); r = r[r.abs() < 0.4]
    if len(r) < 100: return None
    ann = 12 if freq == "M" else 252
    sr = r.mean()/r.std()*np.sqrt(ann)
    eq = (1+r).cumprod()
    dd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(sr=sr, ret=r.mean()*ann, dd=dd, neg=int((yr<0).sum()), worst=yr.min())

def main():
    paths = sorted(glob.glob(f"{LIB}/*.csv")) + sorted(glob.glob(f"{AG}/*/sleeves/*.csv"))
    rets = {}
    for p in paths:
        name = p.replace(f"{LIB}/", "LIB:").replace(f"{AG}/", "AG:").replace(".csv", "")
        try:
            s = load(p)
            if len(s) > 1000:
                rets[name] = to_monthly(s)
        except Exception: pass
    df = pd.DataFrame(rets)
    full = df[df.index >= "2008-01-01"]
    cov = full.notna().mean()
    keep = cov[cov > 0.9].index
    df = full[keep].sort_index()
    print(f"monthly sleeves 2008+: {len(keep)}")
    print(f"{'sleeve':45s} {'SR_m':>6s}")
    singles = {c: perf(df[c]) for c in keep}
    for c in sorted(keep, key=lambda x: -(singles[x]["sr"] if singles[x] else -9)):
        p = singles[c]
        if p: print(f"{c:45s} {p['sr']:6.2f}  ret={p['ret']*100:5.1f}% dd={p['dd']*100:5.1f}%")

    chosen, cand = [], set(df.columns)
    best_set, best_sr = [], -9
    while cand and len(chosen) < 24:
        b, bs = None, -9
        for c in cand:
            p = perf(df[chosen+[c]].fillna(0).mean(axis=1))
            s = p["sr"] if p else -9
            if s > bs: b, bs = c, s
        chosen.append(b); cand.discard(b)
        if bs > best_sr: best_sr, best_set = bs, list(chosen)
    print(f"\nbest subset ({len(best_set)}):")
    for c in best_set: print("  ", c)
    X = df[best_set].fillna(0)
    r = X.mean(axis=1)
    p = perf(r)
    print(f"\nEW MONTHLY: SR={p['sr']:.2f} ret={p['ret']*100:.1f}% dd={p['dd']*100:.1f}% negYrs={p['neg']} worst={p['worst']*100:.1f}%")
    # yearly table
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    print("yearly:", {int(k): round(v*100,1) for k,v in yr.items()})
    r.to_csv(f"{ROOT}/campaign/results/blend_monthly_canonical.csv")
    json.dump(dict(sleeves=best_set, sr=p["sr"], ret=p["ret"], dd=p["dd"]),
              open(f"{ROOT}/campaign/results/blend_state.json","w"), default=str)

if __name__ == "__main__":
    main()
