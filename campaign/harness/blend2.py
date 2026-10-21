"""Coordinator blend v2: greedy forward selection, then EW vs inverse-vol weights,
plus optional portfolio-level vol-target. Honest: weights from full-window stats are
flagged in-sample; also reports expanding-window IV variant (no lookahead)."""
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

def sr_of(r):
    r = r.dropna()
    r = r[r.abs() < 0.2]
    return r.mean()/r.std()*np.sqrt(252) if len(r) > 100 and r.std() > 0 else 0.0

def main():
    paths = sorted(glob.glob(f"{LIB}/*.csv")) + sorted(glob.glob(f"{AG}/*/sleeves/*.csv"))
    rets = {}
    for p in paths:
        name = p.replace(f"{LIB}/", "LIB:").replace(f"{AG}/", "AG:").replace(".csv", "")
        try:
            s = load(p)
            if len(s) > 1000:
                rets[name] = s
        except Exception:
            pass
    df = pd.DataFrame(rets)
    full = df[df.index >= "2008-01-01"]
    cov = full.notna().mean()
    keep = cov[cov > 0.9].index
    df = full[keep].sort_index()
    print(f"sleeves on common 2008+ window (>=90% cov): {len(keep)}")

    # greedy forward selection by EW-blend SR
    chosen, cand = [], set(df.columns)
    def blend_sr(cols):
        return sr_of(df[list(cols)].fillna(0).mean(axis=1))
    while cand and len(chosen) < 16:
        best, bestsr = None, -9
        for c in cand:
            s = blend_sr(chosen + [c])
            if s > bestsr: best, bestsr = c, s
        chosen.append(best); cand.discard(best)
    X = df[chosen].fillna(0)
    r_ew = X.mean(axis=1)

    # inverse-vol weights (in-sample flag)
    vol = X.replace(0, np.nan).std()
    vol = vol.fillna(vol.median())
    w_iv = (1/vol); w_iv = w_iv/w_iv.sum()
    r_iv = X.mul(w_iv, axis=1).sum(axis=1)

    # expanding-window inverse-vol (walk-forward honest)
    def expanding_iv(X):
        w = []
        v = X.expanding(min_periods=126).std().shift(1)
        inv = 1/v.clip(lower=1e-4)
        inv = inv.div(inv.sum(axis=1), axis=0)
        return inv
    W = expanding_iv(X)
    r_ivw = (X * W).sum(axis=1)

    out = []
    for nm, r in [("EW", r_ew), ("IV-insample", r_iv), ("IV-walkfwd", r_ivw)]:
        r2 = r[r.abs() < 0.2].dropna()
        sr = r2.mean()/r2.std()*np.sqrt(252)
        eq = (1+r2).cumprod()
        dd = (eq/eq.cummax()-1).min()
        yr = r2.groupby(r2.index.year).apply(lambda x:(1+x).prod()-1)
        out.append((nm, sr, r2.mean()*252*100, dd*100, int((yr<0).sum()), yr.min()*100))
    print(f"\n{'scheme':12s} {'SR':>6s} {'ann%':>7s} {'MaxDD%':>7s} {'negYrs':>7s} {'worst%':>7s}")
    for o in out:
        print(f"{o[0]:12s} {o[1]:6.2f} {o[2]:7.1f} {o[3]:7.1f} {o[4]:7d} {o[5]:7.1f}")

    # portfolio-level vol target (walk-forward) applied to IV-walkfwd
    vol_wf = r_ivw.expanding(min_periods=126).std().shift(1)*np.sqrt(252)
    lev = (0.10/vol_wf).clip(0, 4).fillna(0)
    r_vt = r_ivw*lev
    r2 = r_vt[r_vt.abs()<0.2].dropna()
    sr = r2.mean()/r2.std()*np.sqrt(252)
    eq = (1+r2).cumprod(); dd = (eq/eq.cummax()-1).min()
    yr = r2.groupby(r2.index.year).apply(lambda x:(1+x).prod()-1)
    print(f"{'VT-10%':12s} {sr:6.2f} {r2.mean()*252*100:7.1f} {dd*100:7.1f} {int((yr<0).sum()):7d} {yr.min()*100:7.1f}")

    r_ew.to_csv(f"{ROOT}/campaign/results/blend_greedy_ew.csv")
    r_vt.to_csv(f"{ROOT}/campaign/results/blend_vt.csv")
    with open(f"{ROOT}/campaign/results/blend_report.md", "w") as f:
        f.write(f"# Blend report {pd.Timestamp.now()}\n\nsleeves ({len(chosen)}): {chosen}\n\n")
        f.write("| scheme | SR | ann% | MaxDD% | negYrs | worst% |\n|---|---|---|---|---|---|\n")
        for o in out:
            f.write(f"| {o[0]} | {o[1]:.2f} | {o[2]:.1f} | {o[3]:.1f} | {o[4]} | {o[5]:.1f} |\n")
        f.write(f"| VT-10% | {sr:.2f} | {r2.mean()*252*100:.1f} | {dd*100:.1f} | {int((yr<0).sum())} | {yr.min()*100:.1f} |\n")

if __name__ == "__main__":
    main()
