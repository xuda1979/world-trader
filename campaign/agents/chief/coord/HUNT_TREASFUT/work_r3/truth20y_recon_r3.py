#!/usr/bin/env python3
"""HUNT_TREASFUT round 3(a) — TRUTH20Y reconstruction, calendar-forensics variant.

Prior attempt (campaign/scripts/HUNT_TREASFUT_truth20y_rebuild.py, straight construct()):
maxdev 1.6e-2 and 5196 rows vs committed 4990. Forensics this round:
  1. Committed index = union(pool) in window MINUS US federal holidays WITH
     Sat->Fri / Sun->Mon observance, MINUS remaining non-weekday rows.
     Evidence: dropped (m,d) set is exactly {NewYear, MLK, Presidents, Memorial,
     Juneteenth(2021+), July4, Labor, Columbus, Veterans, Thanksgiving, Christmas};
     Good Friday (NYSE-closed) is KEPT on all 20/20 years -> "NYSE calendar" in
     GOAL100_TRUTH20Y.json is a FEDERAL-holiday calendar, not NYSE.
  2. Test both placements of that filter: post-construction (rows dropped, values
     untouched) vs pre-construction (filter each sleeve BEFORE vt/blend/DD throttle).
No other knob is tuned. Verdict <=1e-12 on all 3 books => reproduced; else quarantine.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import importlib.util

spec = importlib.util.spec_from_file_location(
    "trb", "/Users/daxu/software/world-trader/campaign/scripts/HUNT_TREASFUT_truth20y_rebuild.py")
trb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trb)

ROOT = trb.ROOT
START, END = pd.Timestamp("2006-10-02"), pd.Timestamp("2026-08-28")


def nth_weekday(y, m, wd, n):
    d = pd.Timestamp(y, m, 1)
    return d + pd.Timedelta(days=((wd - d.dayofweek) % 7) + 7 * (n - 1))


def last_weekday(y, m, wd):
    d = pd.Timestamp(y, m + 1, 1) - pd.Timedelta(days=1)
    return d - pd.Timedelta(days=((d.dayofweek - wd) % 7))


def federal_holidays_observed(years):
    out = []
    for y in years:
        out += [pd.Timestamp(y, 1, 1), pd.Timestamp(y, 7, 4), pd.Timestamp(y, 11, 11),
                pd.Timestamp(y, 12, 25), nth_weekday(y, 1, 0, 3), nth_weekday(y, 2, 0, 3),
                last_weekday(y, 5, 0), nth_weekday(y, 9, 0, 1), nth_weekday(y, 10, 0, 2),
                nth_weekday(y, 11, 3, 4)]
        if y >= 2021:
            out.append(pd.Timestamp(y, 6, 19))
    obs = []
    for h in sorted(set(out)):
        if h.dayofweek == 5:
            obs.append(h - pd.Timedelta(days=1))
        elif h.dayofweek == 6:
            obs.append(h + pd.Timedelta(days=1))
        else:
            obs.append(h)
    return pd.DatetimeIndex(sorted(set(obs)))


def truth_calendar():
    V = {n: trb.load(p) for n, p in trb.POOL_H.items()}
    Vn = pd.DataFrame(V)
    win = Vn[(Vn.index >= START) & (Vn.index <= END)]
    idx = win.index
    hol = federal_holidays_observed(range(2006, 2027))
    keep = ~idx.isin(hol) & (idx.dayofweek < 5)
    return idx[keep], Vn


def construct_on(pool, TGT, THR, calendar):
    """trb.construct verbatim, except every sleeve is pre-filtered to `calendar`."""
    V, S = {}, {}
    for n, p in pool.items():
        r = trb.load(p)
        r = r[r.index.isin(calendar)]
        v, s = trb.vt(r, 0.10)
        V[n], S[n] = v, s
    Vn = pd.DataFrame(V)
    Sn = pd.DataFrame(S)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1)
    blend = blend[blend.index >= "2006-10-01"]
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, _ = trb.vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(126).max().shift(1)
    tdd = eq.shift(1) / rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index)
    b = b * sc
    dsc = sc.diff().abs() * 0.5
    tot = tw.reindex(b.index).fillna(0) + dsc.fillna(0)
    return (b - tot * trb.COST).dropna()


def main():
    cal, Vn = truth_calendar()
    print(f"truth calendar n={len(cal)} (union minus fed-holidays-with-observance, weekdays)")
    A_post = trb.construct(trb.POOL_H, 0.072, 0.040)
    B_post = trb.construct(trb.POOL_H, 0.093, 0.030)
    post = {"SAFE": A_post, "AGGRESSIVE": B_post, "BALANCED": ((A_post + B_post) / 2).dropna()}

    A_pre = construct_on(trb.POOL_H, 0.072, 0.040, cal)
    B_pre = construct_on(trb.POOL_H, 0.093, 0.030, cal)
    pre = {"SAFE": A_pre, "AGGRESSIVE": B_pre, "BALANCED": ((A_pre + B_pre) / 2).dropna()}

    worst = 0.0
    print(f"\n{'book':11s} {'variant':5s} {'n_rec':>5s} {'n_com':>5s} {'idx_eq':>6s} {'maxdev':>12s}")
    for book in ["SAFE", "AGGRESSIVE", "BALANCED"]:
        com = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_TRUTH20Y_{book}_daily.csv",
                          index_col=0, parse_dates=True).iloc[:, 0]
        for tag, r in [("post", post[book]), ("pre", pre[book])]:
            idx_eq = r.index.equals(com.index)
            j = pd.concat([r.rename("rec"), com.rename("com")], axis=1, join="inner").dropna()
            md = float((j.rec - j.com).abs().max()) if len(j) else float("nan")
            ok = idx_eq and len(r) == len(com) and md <= 1e-12
            worst = max(worst, md if md == md else 0.0)
            print(f"{book:11s} {tag:5s} {len(r):5d} {len(com):5d} {str(idx_eq):>6s} {md:12.4e}"
                  f"{'   <= REPRODUCED' if ok else ''}")
    print(f"\nVERDICT: {'REPRODUCED <=1e-12' if worst <= 1e-12 else 'NOT REPRODUCED — quarantine stands'}")
    return 0 if worst <= 1e-12 else 1


if __name__ == "__main__":
    sys.exit(main())
