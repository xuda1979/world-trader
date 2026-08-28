"""Coordinator blend + correlation report over all accepted sleeves."""
import glob, os, sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
LIB = f"{ROOT}/campaign/results/sleeve_library"
AG = f"{ROOT}/campaign/agents"

def load(p):
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index)
    return df["ret"] if "ret" in df.columns else df.iloc[:, 0]

def stats(r):
    r = r.dropna(); r = r[r.abs() < 0.2]
    if len(r) < 250: return None
    sr = r.mean()/r.std()*np.sqrt(252)
    eq = (1+r).cumprod()
    dd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    return dict(n=len(r), sr=sr, ret=r.mean()*252, dd=dd,
                neg=int((yr < 0).sum()), worst=yr.min(),
                start=str(r.index[0].date()), end=str(r.index[-1].date()))

def main():
    paths = sorted(glob.glob(f"{LIB}/*.csv")) +             sorted(glob.glob(f"{AG}/*/sleeves/*.csv"))
    rets = {}
    for p in paths:
        name = p.replace(f"{LIB}/", "LIB:").replace(f"{AG}/", "AG:").replace(".csv", "")
        try:
            s = load(p)
            if len(s) > 500:
                rets[name] = s
        except Exception:
            pass
    df = pd.DataFrame(rets)
    full = df[df.index >= "2008-01-01"]
    cov = full.notna().mean()
    keep = cov[cov > 0.9].index
    df = full[keep]
    print(f"sleeves on common 2008+ window (>=90% coverage): {len(keep)}")
    C = df.corr()

    chosen, cand = [], set(df.columns)
    def blend_sr(cols):
        X = df[list(cols)].fillna(0)
        r = X.mean(axis=1)
        r = r[r.abs() < 0.2]
        return r.mean()/r.std()*np.sqrt(252) if r.std() > 0 else 0
    while cand:
        best, bestsr = None, -9
        for c in cand:
            sr = blend_sr(chosen + [c])
            if sr > bestsr:
                best, bestsr = c, sr
        if best is None: break
        chosen.append(best); cand.discard(best)
        print(f"  +{best:55s} blend SR={bestsr:.2f}")
        if len(chosen) >= 14: break
    X = df[chosen].fillna(0)
    r = X.mean(axis=1)
    r = r[r.abs() < 0.2]
    eq = (1+r).cumprod()
    dd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    sr = r.mean()/r.std()*np.sqrt(252)
    Cc = C.loc[chosen, chosen]
    mean_abs = (Cc.abs().values.sum() - len(chosen)) / (len(chosen)**2 - len(chosen))
    print(f"\nFINAL greedy blend ({len(chosen)} sleeves, EW): SR={sr:.2f}, "
          f"ann={r.mean()*252*100:.1f}%, MaxDD={dd*100:.1f}%, neg years={int((yr<0).sum())}, worst={yr.min()*100:.1f}%")
    print(f"mean pairwise |corr|: {mean_abs:.3f}")
    r.to_csv(f"{ROOT}/campaign/results/blend_greedy_ew.csv")
    with open(f"{ROOT}/campaign/results/blend_report.md", "w") as f:
        f.write(f"# Greedy blend report {pd.Timestamp.now()}\n\n")
        f.write(f"sleeves: {chosen}\n\n")
        f.write(f"SR={sr:.2f} ann={r.mean()*252*100:.1f}% MaxDD={dd*100:.1f}% neg_years={int((yr<0).sum())}\n")

if __name__ == "__main__":
    main()
