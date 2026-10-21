#!/usr/bin/env python3
"""HUNT_FXCARRY2 round-3: tail-controlled carry (charter a i/ii/iii).

Attacks the DOCUMENTED R2 failure mechanism (-19.4% 2008 crash tail on a
factor whose post-2004 gross drift is ~0) with three pre-registered crash
controls, each a full-gated standalone sleeve on the IDENTICAL R2 engine
(HUNT_FXCARRY2_round2.py: 8-pair monthly IRSTCI01 carry, T+1, 6.4bps FULL
|dW|, borrow+margin, 2004+). These are controls applied on top of the R2
flagship book — NOT a re-tune of the carry signal itself (the signal is
byte-identical to R2: sign(r_fgn - r_usd), month-end, EW).

  (i)   10%-VT carry + trailing-drawdown stop at -10% and -15%:
        when trailing drawdown from the book's running high-water mark (HWM)
        breaches the stop, go to 0 gross until a re-entry rule fires. Re-entry
        is NOT tuned per stop level: a single pre-registered rule for both —
        re-enter at 25% of the way back to HWM... no; simplest honest rule:
        re-enter when the trailing 63d realized return of the book turns
        positive (momentum-confirm re-entry, standard in tail-control lit).
  (ii)  monthly loss-cap de-lever: if the book's realized loss in month m
        breaches a cap (-3%, -5%), cut gross leverage in half for all of
        month m+1 (recover cap +50% of month).
  (iii) equal-risk 8-pair book with crash-cap: inverse-63d-vol pair weights
        (R2 vol_weights machinery, trailing-only) to a 10% VT, plus a hard
        crash-cap: daily book return realized below -2% (one day) forces
        gross to zero for the next 10 business days (crash-cap).

All gates from GATES_CONTRACT.md via round2.gates() + era discipline:
post-2004 ONLY is reported as the verdict era. Scramble 200x, halves,
yearly, corrChamp<0.15, plateau (for mechanism params, pre-registered grids).
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
from bt import metrics as M
from scripts.HUNT_FXCARRY2_round2 import (
    build_signals, book, gates, show, stat, yearly, yearly_ok, champ_corr,
    book_scramble, ANN)

START = "2004-01-01"


# ---------- shared: rebuild the R2 flagship book (signal identical to R2) ----------
def flagship():
    sigs, ylds, rets = build_signals(start=START, mode="nominal")
    net, pos = book(sigs, rets, ylds=ylds, start=START)
    return sigs, ylds, rets, net, pos


# ---------- (i) trailing-drawdown stop (corrected state machine) ----------
def dd_stop(net, stop=-0.10, reentry="mom63"):
    """Trailing-drawdown stop on the NET book. State at t uses ONLY realized
    returns <= t (drawdown measured on the live path itself, i.e. the path the
    trader actually experiences, including any flat days). Stop -> flat from
    t+1; re-entry when trailing 63d net P&L > 0, from t+1. Returns (adj net,
    days spent flat)."""
    idx = net.index
    eq = (1.0 + net).cumprod()
    hwm = eq.cummax()
    dd = eq / hwm - 1.0
    dd_v = dd.values
    mom_v = net.rolling(63, min_periods=1).sum().values
    live = np.ones(len(net), dtype=bool)
    stopped = False
    for i in range(len(net)):
        live[i] = not stopped           # day i held per decision at i-1 (T+1)
        # update state with day i's realized close -> applies from day i+1
        if not stopped:
            if dd_v[i] <= stop:
                stopped = True
        elif reentry == "mom63" and mom_v[i] > 0:
            stopped = False
    # live[i] is the position held ON day i (decided at i-1) — already T+1
    # because the state transition at i only affects live[i+1] onward.
    w = pd.Series(live.astype(float), index=idx)
    out = net * w
    return out, int((~live).sum())


def _apply_cap(x, crash, halt):
    """Crash-cap: hit at day i (x[i] < crash) -> zero days i+1..i+halt.
    Past untouched, exactly `halt` flat days per hit, no double shift."""
    v = x.values.copy()
    h = (v < crash)
    i = 0
    n = len(v)
    while i < n:
        if h[i]:
            v[i + 1:i + 1 + halt] = 0.0
            i += halt + 1
        else:
            i += 1
    return pd.Series(v, index=x.index)


def apply_cap_to_series(x, crash=-0.02, halt=10):
    return _apply_cap(x, crash, halt)


# ---------- (ii) monthly loss-cap de-lever ----------
def monthly_losscap(net, cap=-0.03, halve=0.5):
    """If realized month-m book return < cap, multiply month m+1's net by
    `halve` (de-lever), T+1 (decision at m-end applies from m+1 day 1)."""
    per = net.index.to_period("M")
    mret = net.groupby(per).apply(lambda x: (1 + x).prod() - 1)
    dele = (mret < cap).shift(1).fillna(False)          # flag on month m+1
    scale = pd.Series(1.0, index=net.index)
    per_vals = per.values
    for p, flag in dele.items():
        if flag:
            scale[per_vals == p] = halve
    return net * scale, int(dele.sum())


# ---------- (iii) equal-risk + crash-cap ----------
def equal_risk_crashcap(sigs, rets, ylds, start, crash=-0.02, halt=10, vt=0.10):
    """Inverse-63d-vol pair weights -> VT 10% book, then a crash-cap: any
    realized book day < `crash` forces gross 0 for the next `halt` days
    (decision at t close applies from t+1 — T+1 honest)."""
    names = list(sigs)
    nets, poss = [], []
    for k in names:
        from scripts.HUNT_FXCARRY2_round2 import evaluate, vt_scale
        n_k, w_k = evaluate(sigs[k], rets[k], yield_r=ylds[k])
        nets.append(n_k.rename(k))
        poss.append((k, w_k))
    df = pd.concat(nets, axis=1).fillna(0.0)
    df = df[df.index >= start]
    n = len(names)
    wts = pd.Series({k: 1.0 / n for k, _ in poss})
    book_er = df.mul(wts, axis=1).sum(axis=1)
    # equal-risk: inverse 63d vol re-scaled so the VT is done at book level
    vol = book_er.rolling(63).std() * np.sqrt(ANN)
    vt_only = book_er * (vt / vol.replace(0.0, np.nan)).clip(0.2, 3.0).shift(1).fillna(1.0)
    # crash-cap: hit day i realized, days i+1..i+halt flat (T+1-honest)
    adj = _apply_cap(vt_only, crash, halt)
    n_flat = int((vt_only != adj).sum())
    return adj, n_flat, vt_only


# ---------- plateau helper (pre-registered grids per mechanism) ----------
def plateau_probe(net, apply_fn, grid, label):
    rows = []
    for p in grid:
        adj, _info = apply_fn(net, p)
        rows.append((p, M.sharpe_d(adj)))
    srs = np.array([r[1] for r in rows])
    best = rows[int(np.argmax(srs))]
    print(f"  plateau[{label}]: " + " ".join(f"{p}:{s:.3f}" for p, s in rows)
          + f"  best={best[0]}@{best[1]:.3f}")
    return rows, best


if __name__ == "__main__":
    print(f"=== HUNT_FXCARRY2 round-3 | window {START}+ | tail-controlled carry ===")
    sigs, ylds, rets, net0, pos0 = flagship()
    print("R2 flagship baseline:")
    show(gates(net0, pos0, rets, "R2-carry-nominal-EW (baseline)"))

    print("\n--- (i) 10%VT + trailing-drawdown stop ---")
    for stop in (-0.10, -0.15):
        adj, nstop = dd_stop(net0, stop=stop)
        yr = adj.groupby(adj.index.year).apply(lambda x: (1 + x).prod() - 1)
        neg = int((yr < 0).sum())
        print(f"stop={stop:.2f}: SR={M.sharpe_d(adj):.3f} ann={M.ann_geo(adj):.4f} "
              f"negyr={neg} worst={yr.min():.4f} days_stopped={nstop}")
    plateau_probe(net0, lambda n, p: dd_stop(n, stop=p), [-0.05, -0.075, -0.10, -0.15, -0.20], "dd-stop")
    # full gates on the charter-specified -10 level
    adj, nflat = dd_stop(net0, stop=-0.10)
    w = (adj / net0.where(net0 != 0.0)).fillna(1.0).clip(0.0, 1.0)  # live indicator
    pos_s = {k: v * w for k, v in pos0.items()}
    show(gates(adj, pos_s, rets, "dd-stop-10+mom63-reentry"))
    print(f"   days_flat={nflat}")

    print("\n--- (ii) monthly loss-cap de-lever ---")
    for cap in (-0.03, -0.05):
        adj, nd = monthly_losscap(net0, cap=cap)
        yr = adj.groupby(adj.index.year).apply(lambda x: (1 + x).prod() - 1)
        print(f"cap={cap:.2f}: SR={M.sharpe_d(adj):.3f} ann={M.ann_geo(adj):.4f} "
              f"negyr={int((yr<0).sum())} worst={yr.min():.4f} dele_months={nd}")
    plateau_probe(net0, lambda n, p: monthly_losscap(net0, cap=p), [-0.01, -0.02, -0.03, -0.05, -0.08], "loss-cap")
    adj, nd = monthly_losscap(net0, cap=-0.03)
    scale = (adj / net0.where(net0 != 0.0)).fillna(1.0).clip(0.0, 1.0)  # 1 or halve
    # careful: adj = net0*scale where net0==0 gives nan->fillna(1) is wrong for
    # the deleveraged zero-return days; rebuild scale from month flags instead.
    per = net0.index.to_period("M")
    mret = net0.groupby(per).apply(lambda x: (1 + x).prod() - 1)
    dele = (mret < -0.03).shift(1).fillna(False)
    scale = pd.Series(1.0, index=net0.index)
    pv = per.values
    for p, flag in dele.items():
        if flag:
            scale[pv == p] = 0.5
    pos_s = {k: v * scale for k, v in pos0.items()}
    show(gates(adj, pos_s, rets, "monthly-losscap-3pct-halve"))
    print(f"   dele_months={nd}")

    print("\n--- (iii) equal-risk + crash-cap ---")
    for crash in (-0.02, -0.03):
        adj, nh, _ = equal_risk_crashcap(sigs, rets, ylds, START, crash=crash)
        yr = adj.groupby(adj.index.year).apply(lambda x: (1 + x).prod() - 1)
        print(f"crash={crash:.2f}: SR={M.sharpe_d(adj):.3f} ann={M.ann_geo(adj):.4f} "
              f"negyr={int((yr<0).sum())} worst={yr.min():.4f} halt_days={nh}")

    # Full gate set on the -2% crash-cap variant. Scramble at per-pair level
    # (same random lag rolled into ALL pairs' positions, as in R2), rebuild the
    # equal-risk VT book from scrambled positions, apply the SAME crash-cap,
    # and compare SRs — both arms get the cap, so the test isolates signal
    # timing, not the cap itself.
    crash = -0.02
    adj, nh, vt_only = equal_risk_crashcap(sigs, rets, ylds, START, crash=crash)
    idx = adj.index
    ks = list(sigs)
    # per-pair net series with identical engine (pre-cap), EW-averaged = book_er
    nets = []
    for k in ks:
        from scripts.HUNT_FXCARRY2_round2 import evaluate
        n_k, _ = evaluate(sigs[k], rets[k], yield_r=ylds[k])
        nets.append(n_k.rename(k))
    dfp = pd.concat(nets, axis=1).fillna(0.0)
    dfp = dfp[dfp.index >= START]
    wts = pd.Series({k: 1.0 / len(ks) for k in ks})
    book_er = dfp.mul(wts, axis=1).sum(axis=1)
    # rebuild positions actually held: net_k = w_k*(r_k+yld_k) - costs; for the
    # scramble R2 used pos x (ret+yld) gross. Reconstruct gross pos from the
    # R2 pos map (flagship) — equal-risk weights are EW here, so pos maps match.
    real_p, real_r = book_scramble(pos0, rets, ylds, n=200, seed=7, index=idx)
    # now scramble arm with crash-cap applied to the scrambled book
    rng = np.random.default_rng(7)
    P = np.column_stack([np.asarray(pos0[k].reindex(idx).fillna(0.0), float) for k in ks])
    R = np.column_stack([np.asarray(
        (rets[k] + ylds[k]).reindex(idx).fillna(0.0), float) for k in ks])
    gross_real = pd.Series((P * R).mean(axis=1), index=idx)

    capped_real = apply_cap_to_series(gross_real, crash=crash, halt=10)
    real_sr = M.sharpe_d(capped_real)
    cnt = 0
    n_sc = 200
    T = len(idx)
    for _ in range(n_sc):
        lag = int(rng.integers(10, T - 10 + 1))
        sc_book = pd.Series((np.roll(P, lag, axis=0) * R).mean(axis=1), index=idx)
        sc_capped = apply_cap_to_series(sc_book, crash=crash, halt=10)
        if M.sharpe_d(sc_capped.dropna()) >= real_sr:
            cnt += 1
    p_sc = cnt / n_sc
    st = stat(adj)
    yr = adj.groupby(adj.index.year).apply(lambda x: (1 + x).prod() - 1)
    neg = int((yr < 0).sum())
    h1, h2 = M.half_split(adj)
    corr = champ_corr(adj)
    print(f"eqrisk-crashcap-2pct FULL: SR={st['sr']:.3f} ann={st['ann']:.4f} "
          f"mdd={st['mdd']:.4f} negyr={neg} worst={yr.min():.4f} H=({h1:.2f},{h2:.2f}) "
          f"corr={corr:.4f} scr_p(capped-vs-capped)={p_sc:.3f}")
    print("   years:", {int(k): round(float(v), 4) for k, v in yr.items()})

    # (iii-b) TRUE equal-risk: inverse-63d-vol pair weights (R2 vol_weights,
    # trailing-only) + same crash-cap. R2 tested the weighting alone (-0.097).
    print("\n--- (iii-b) inverse-vol equal-risk + crash-cap ---")
    from scripts.HUNT_FXCARRY2_round2 import vol_weights
    sigs_v = vol_weights(rets, sigs)
    nets_v = []
    for k in ks:
        from scripts.HUNT_FXCARRY2_round2 import evaluate
        n_k, _ = evaluate(sigs_v[k], rets[k], yield_r=ylds[k])
        nets_v.append(n_k.rename(k))
    dfv = pd.concat(nets_v, axis=1).fillna(0.0)
    dfv = dfv[dfv.index >= START]
    n_v = len(nets_v)
    wts_v = pd.Series({k: 1.0 / n_v for k in nets_v[0].index})
    book_v = dfv.mul(1.0 / n_v, axis=1).sum(axis=1)
    for crash_v in (-0.02, -0.03):
        adj_v = apply_cap_to_series(book_v, crash=crash_v, halt=10)
        yr_v = adj_v.groupby(adj_v.index.year).apply(lambda x: (1 + x).prod() - 1)
        h1v, h2v = M.half_split(adj_v)
        print(f"ivvol+crashcap={crash_v:.2f}: SR={M.sharpe_d(adj_v):.3f} "
              f"ann={M.ann_geo(adj_v):.4f} negyr={int((yr_v<0).sum())} "
              f"worst={yr_v.min():.4f} H=({h1v:.2f},{h2v:.2f}) "
              f"corr={champ_corr(adj_v):.4f}")
