"""Campaign eval harness — the single honest scorer for every sleeve.

Contract for a sleeve CSV: columns [date, ret] (daily portfolio return,
net of 6 bps one-side, T+1 execution, no lookahead). One row per trading day.

Usage: python eval.py <csv> [csv...]   (or --dir campaign/agents/<a>/sleeves)
"""
import glob, json, sys, os
import numpy as np
import pandas as pd

COST_BPS = 6.0

def load_ret(path):
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index)
    col = "ret" if "ret" in df.columns else df.columns[0]
    s = df[col].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    return s[~s.index.duplicated(keep="last")]

def stats(r):
    r = r.dropna()
    if len(r) < 250: return None
    mu, sd = r.mean(), r.std()
    sr = mu/sd*np.sqrt(252) if sd > 0 else 0.0
    eq = (1+r).cumprod()
    dd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    return dict(
        n=len(r), start=str(r.index[0].date()), end=str(r.index[-1].date()),
        ann_ret=round(mu*252*100, 2), ann_vol=round(sd*np.sqrt(252)*100, 2),
        sr=round(sr, 2), max_dd=round(dd*100, 2),
        skew=round(r.skew(), 2), worst_year=round(yr.min()*100, 2),
        best_year=round(yr.max()*100, 2), neg_years=int((yr < 0).sum()),
        years=int(len(yr)),
        yearly={int(k): round(v*100, 1) for k, v in yr.items()},
    )

def halves(r):
    out = {}
    mid = r.index[len(r)//2]
    for name, seg in [("H1", r[r.index <= mid]), ("H2", r[r.index > mid])]:
        s = stats(seg)
        out[name] = s["sr"] if s else None
    return out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    paths = []
    for a in args:
        if os.path.isdir(a):
            paths += sorted(glob.glob(os.path.join(a, "*.csv")))
        else:
            paths.append(a)
    if not paths:
        print("no input"); sys.exit(1)
    for p in paths:
        r = load_ret(p)
        s = stats(r)
        if not s:
            print(f"{p}: too short ({len(r)} rows)"); continue
        h = halves(r)
        print(f"\n== {os.path.basename(p)} ==")
        print(f"  n={s['n']} {s['start']}..{s['end']}  ann={s['ann_ret']}% vol={s['ann_vol']}% SR={s['sr']} MaxDD={s['max_dd']}% skew={s['skew']}")
        print(f"  halves SR: H1={h['H1']} H2={h['H2']}   neg years: {s['neg_years']}/{s['years']} (worst {s['worst_year']}%)")
        print(f"  yearly%: {s['yearly']}")

if __name__ == "__main__":
    main()
