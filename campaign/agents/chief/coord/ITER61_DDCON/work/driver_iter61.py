#!/usr/bin/env python3
"""ITER61_DDCON driver — pre-registered arms per FINDINGS_PRECOMMIT.md (sealed 2026-10-10).

Re-implements rawew13v2_build.build() math locally (canonical builder read-only:
PATHS/NAMES/params imported, never executed for writes). Arms:
  D1/D2 control (must reproduce staged incumbent), D3 W_MAX rule audit,
  A1-A4 natgas block cap (after-fit redistribution, apply_brwt_cap pattern),
  B1-B2 constraint-in-fit natgas cap,
  C1-C2 DD-aware/tail-penalized IS objective (soft-constraint proxies).
Deterministic, seeded, FAIL-CLOSED on D1 divergence.
"""
import sys, json, hashlib
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)

from campaign.scripts.rawew13v2_build import (  # noqa: E402  (read-only import)
    NAMES, PATHS, GEAR, RATE, BPS, IS_END, SHRINK_D, W_MAX, W_BRWT_CAP,
    BRWT_BLOCK, load, fit_relw, apply_brwt_cap,
)

NG_BLOCK = ("C5ng", "C5ngsum")
START = "2008-03-31"
END = pd.Timestamp("2026-08-28")  # charter §3: staged-vintage evaluation window (staged daily last row)
# REPRO BASIS (discovered during D1, sealed as the round's sleeve basis BEFORE any arm ran):
# the staged champion was built from the PRE-09-28-refresh C5ngsum vintage (rows only through
# 2026-08-24; commit 17e5be62 later appended 08-25..09-21 which are NOT in the staged daily).
# Repro verified: disk sleeves + C5ngsum truncated at 2026-08-24 + window pin 08-28 =>
# max |staged - rebuild| = 9.99e-17, 0 days > 1e-10. All arms use THIS basis.
C5NGSUM_TRUNC = pd.Timestamp("2026-08-24")
OUT = f"{ROOT}/campaign/agents/chief/coord/ITER61_DDCON/work"


def _load_c5ngsum_trunc():
    s = load(PATHS["C5ngsum"])
    return s[s.index <= C5NGSUM_TRUNC]


def load_df():
    parts = {}
    for n in NAMES:
        parts[n] = _load_c5ngsum_trunc().dropna() if n == "C5ngsum" else load(PATHS[n]).dropna()
    df = pd.DataFrame(parts)
    df = df[df.index >= START]
    # working-tree sleeves drift past the staged vintage (2026-09-18 at driver-writing time);
    # pin to the staged champion vintage per charter §3 — vintage pin, NOT a fit change.
    df = df[df.index <= END]
    return df


def stats(r):
    r = r.dropna()
    if len(r) < 100:
        return {}
    mu, sd = r.mean(), r.std(ddof=1)
    nav = (1 + r).cumprod()
    ddser = nav / nav.cummax() - 1.0
    mdd = float(ddser.min())
    trough = ddser.idxmin()
    peak = nav.loc[:trough].idxmax()
    rec = nav.loc[trough:]
    recov = rec[rec >= nav.loc[peak]].index.min()
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    isr = r[r.index < IS_END]; oos = r[r.index >= IS_END]
    onav = (1 + oos).cumprod()
    return dict(
        n=len(r), ann=(nav.iloc[-1]) ** (252 / len(r)) - 1,
        sr=mu / sd * np.sqrt(252), mdd=mdd, trough=str(trough.date()),
        peak=str(peak.date()), recov=str(recov.date()) if pd.notna(recov) else "n/a",
        negy=int((yr < 0).sum()), worst_yr=float(yr.min()),
        worst_day=float(r.min()), worst_day_d=str(r.idxmin().date()),
        is_sr=float(isr.mean() / isr.std(ddof=1) * np.sqrt(252)) if len(isr) > 100 else np.nan,
        is_ann=float(isr.mean() * 252), is_mdd=float(((1 + isr).cumprod() / (1 + isr).cumprod().cummax() - 1).min()),
        oos_sr=float(oos.mean() / oos.std(ddof=1) * np.sqrt(252)) if len(oos) > 100 else np.nan,
        oos_ann=float(oos.mean() * 252),
        oos_mdd=float((onav / onav.cummax() - 1).min()),
    )


def book(df, relw_ts, gear=GEAR):
    """NAV-drift weights + costs, exactly build()'s math."""
    relw_ts = relw_ts.reindex(df.columns)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw_ts, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (gear / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = pd.Series(port, index=df.index) - to * BPS / 1e4 - np.maximum(gear - 1, 0) * RATE / 252
    gross = Wg.abs().sum(axis=1)
    return net, gross, to


def solve_fit(df_is, shrink_d, extra_bounds=None, extra_conses=None, soft=None):
    """fit_relw's SLSQP with optional extra bounds/constraints/soft penalty.
    Mirrors fit_relw's shrinkage and normalization EXACTLY; only the
    objective/constraint set is extended for B/C arms."""
    from scipy.optimize import minimize
    X = df_is.dropna(axis=1, how="all")
    X = X.fillna(0.0)
    have = [n for n in NAMES if n in X.columns]
    mu = (X[have].mean() * 252).values
    Sig = X[have].cov().values * 252
    Sig = (1.0 - shrink_d) * Sig + shrink_d * np.diag(np.diag(Sig))

    def neg_sharpe(w):
        v = float(np.sqrt(w @ Sig @ w))
        base = -(float(w @ mu)) / v if v > 1e-14 else 0.0
        if soft is not None:
            base = base + soft(w, X[have])
        return base

    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    if extra_conses:
        cons += extra_conses
    bnds = [(0.0, W_MAX / len(have))] * len(have) if extra_bounds is None else extra_bounds
    x0 = np.full(len(have), 1.0 / len(have))
    res = minimize(neg_sharpe, x0, method="SLSQP", bounds=bnds, constraints=cons,
                   options=dict(maxiter=1000, ftol=1e-12))
    if not res.success:
        return None, None
    relw = pd.Series(0.0, index=NAMES); relw[have] = res.x
    return relw, res


def cap_block(relw, block, cap):
    """apply_brwt_cap pattern generalized: cap block share, redistribute pro-rata."""
    relw = relw.copy()
    blk = [n for n in block if n in relw.index]
    s = relw[blk].sum()
    if s <= cap or s <= 0:
        return relw
    other = [n for n in relw.index if n not in blk and relw[n] > 0]
    excess = s - cap
    k = excess / s
    relw[blk] = relw[blk] * (1 - k)
    oo = relw[other].sum()
    if oo > 0:
        relw[other] = relw[other] * (1 + excess / oo)
    return relw


def main():
    df = load_df()
    isr = df[df.index < IS_END]
    log = {}

    # ---------- D1: uncapped rebuild of staged incumbent ----------
    relw_d1 = apply_brwt_cap(fit_relw(isr, shrink_d=SHRINK_D), cap=W_BRWT_CAP)
    net1, gross1, to1 = book(df, relw_d1)
    s1 = stats(net1)
    log["D1"] = {**s1, "relw": {k: float(v) for k, v in relw_d1.items()}}
    INC = dict(sr=3.820357, ann=0.239215, mdd=-0.037339)
    dev = dict(sr=abs(s1["sr"] - INC["sr"]), ann=abs(s1["ann"] - INC["ann"]),
               mdd=abs(s1["mdd"] - INC["mdd"]))
    log["D1_dev"] = dev
    print("D1:", json.dumps({k: s1[k] for k in ("n", "ann", "sr", "mdd", "negy")}))
    print("D1 dev vs staged:", json.dumps(dev))
    FAIL_CLOSED = dev["sr"] > 1e-4 or dev["mdd"] > 1e-6 or dev["ann"] > 1e-4
    if FAIL_CLOSED:
        print("D1 DIVERGED — FAIL CLOSED. No further arms.")
        json.dump(log, open(f"{OUT}/arms_iter61.json", "w"), indent=1, default=str)
        sys.exit(1)

    # ---------- D3: W_MAX rule audit ----------
    k = 12
    wmax_share = W_MAX / k
    over = {n: float(relw_d1[n]) for n in NAMES if relw_d1[n] > wmax_share + 1e-12}
    log["D3"] = {"wmax_share": wmax_share, "shares_over_wmax": over,
                 "note": "cap-after-fit redistribution may exceed W_MAX/k; incumbent mechanism, disclosed only"}
    print("D3 shares over W_MAX/k:", over)

    # ---------- Family A: after-fit natgas block cap ----------
    for cap in (0.25, 0.28, 0.30, 0.35):
        arm = f"A_cap{int(cap*100)}"
        relw = cap_block(relw_d1, NG_BLOCK, cap)
        net, gross, to = book(df, relw)
        st = stats(net)
        log[arm] = {**st, "relw": {kk: float(v) for kk, v in relw.items()},
                    "ng_share": float(relw[list(NG_BLOCK)].sum()),
                    "to_bpyr": float(to.mean() * 252 * BPS / 1e4 * 1e4) / 1e4,
                    "gross_max": float(gross.max())}
        print(arm, json.dumps({kk: st[kk] for kk in ("ann", "sr", "mdd", "is_sr", "oos_sr", "oos_mdd", "negy", "worst_day")}))

    # ---------- Family B: constraint-in-fit ----------
    have = [n for n in NAMES if n in isr.dropna(axis=1, how="all").columns]
    iC = have.index("C5ng"); iS = have.index("C5ngsum")
    con_b1 = [{"type": "ineq",
               "fun": lambda w, i1=iC, i2=iS: 0.30 - (w[i1] + w[i2])}]
    relw, res = solve_fit(isr, SHRINK_D, extra_conses=con_b1)
    if relw is None:
        log["B1"] = {"error": "SLSQP failed"}
    else:
        relw = apply_brwt_cap(relw, cap=W_BRWT_CAP)
        net, gross, to = book(df, relw)
        st = stats(net)
        log["B1_cap030_infit"] = {**st, "relw": {kk: float(v) for kk, v in relw.items()},
                                  "ng_share": float(relw[list(NG_BLOCK)].sum())}
        print("B1_cap030_infit", json.dumps({kk: st[kk] for kk in ("ann", "sr", "mdd", "is_sr", "oos_sr", "oos_mdd", "negy")}))

    bnds_b2 = []
    for n in have:
        hi = 0.15 if n in NG_BLOCK else W_MAX / len(have)
        bnds_b2.append((0.0, hi))
    relw, res = solve_fit(isr, SHRINK_D, extra_bounds=bnds_b2)
    if relw is None:
        log["B2"] = {"error": "SLSQP failed"}
    else:
        relw = apply_brwt_cap(relw, cap=W_BRWT_CAP)
        net, gross, to = book(df, relw)
        st = stats(net)
        log["B2_percap015"] = {**st, "relw": {kk: float(v) for kk, v in relw.items()},
                               "ng_share": float(relw[list(NG_BLOCK)].sum())}
        print("B2_percap015", json.dumps({kk: st[kk] for kk in ("ann", "sr", "mdd", "is_sr", "oos_sr", "oos_mdd", "negy")}))

    # ---------- Family C: DD-aware / tail-penalized IS objective (soft proxies) ----------
    Xis = isr.dropna(axis=1, how="all").fillna(0.0)[have]
    Xv = Xis.values

    def soft_c1(w, X=Xv):
        # IS-MDD soft floor -2.0%: penalize cumulative-path depths below -0.02
        r = Xv @ w
        nav = np.cumprod(1 + r)
        dd = nav / np.maximum(np.maximum.accumulate(nav), 1e-12) - 1
        pen = np.minimum(0.0, dd + 0.02) ** 2
        return 10.0 * float(pen.sum())

    relw, res = solve_fit(isr, SHRINK_D, soft=soft_c1)
    if relw is None:
        log["C1"] = {"error": "SLSQP failed"}
    else:
        relw = apply_brwt_cap(relw, cap=W_BRWT_CAP)
        net, gross, to = book(df, relw)
        st = stats(net)
        log["C1_isddsoft020"] = {**st, "relw": {kk: float(v) for kk, v in relw.items()}}
        print("C1_isddsoft020", json.dumps({kk: st[kk] for kk in ("ann", "sr", "mdd", "is_sr", "is_mdd", "oos_sr", "oos_mdd", "negy")}))

    def soft_c2(w, X=Xv):
        r = Xv @ w
        tail = np.minimum(0.0, r + 0.015) ** 2
        return 10.0 * float(tail.sum())

    relw, res = solve_fit(isr, SHRINK_D, soft=soft_c2)
    if relw is None:
        log["C2"] = {"error": "SLSQP failed"}
    else:
        relw = apply_brwt_cap(relw, cap=W_BRWT_CAP)
        net, gross, to = book(df, relw)
        st = stats(net)
        log["C2_tailsoft015"] = {**st, "relw": {kk: float(v) for kk, v in relw.items()}}
        print("C2_tailsoft015", json.dumps({kk: st[kk] for kk in ("ann", "sr", "mdd", "is_sr", "oos_sr", "oos_mdd", "negy")}))

    json.dump(log, open(f"{OUT}/arms_iter61.json", "w"), indent=1, default=str)
    print("WROTE", f"{OUT}/arms_iter61.json")


if __name__ == "__main__":
    main()
