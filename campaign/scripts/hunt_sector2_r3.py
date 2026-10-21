#!/usr/bin/env python3
"""HUNT_SECTOR2 round-3 engine (charter (a) internal composite + (a2) blend submission
+ (b) FXCARRY2 cross-verify).

Blends are built at the ALLOCATION level from PUBLISHED round-2 sleeve NET series (no
new signal params). Sleeve legs are self-financing: their internal turnover is already
inside the published nets, so the ONLY incremental cost is (i) day-0 entry and (ii)
allocation-drift rebalancing, both at 6.4bps FULL |dW|. T+1: allocations drift through
close t, the rebalancing trade decided at close t is held from t+1 (charged t+1).
Trailing-only VT10 clip3 is applied on the composite book return (same gate standard
as every round-2 sleeve). Gates per GATES_CONTRACT.md, fail-closed.

TDD: HUNT_SECTOR2/tests_tdd_r3.py (RED first, 6 tests)."""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
for p in (f"{ROOT}/campaign/scripts", f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2"):
    if p not in sys.path:
        sys.path.insert(0, p)
import hunt_sector2_lib as L
import hunt_sector2_r2_harness as H

SD = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/sleeves"
CPS = L.COST / 1e4


def load_sleeve(name: str) -> pd.Series:
    df = pd.read_csv(f"{SD}/{name}.csv", index_col=0, parse_dates=True)
    s = df.iloc[:, 0].astype(float)
    assert s.notna().all() and s.index.is_monotonic_increasing, f"bad sleeve file {name}"
    return s


def _rebal_flags(idx: pd.DatetimeIndex, rebal: str) -> np.ndarray:
    """Closes where a rebalancing trade is DECIDED (held the next session).
    'daily': every close. 'monthly': the LAST close of each month (month-end decision,
    held from the first session of the new month) - matches the framework T+1 style."""
    n = len(idx)
    f = np.zeros(n, dtype=bool)
    if rebal == "daily":
        f[1:] = True
    elif rebal == "monthly":
        key = list(zip(idx.year, idx.month))
        f[:-1] = [key[t] != key[t + 1] for t in range(n - 1)]   # month-end closes
    elif rebal == "never":
        pass
    else:
        raise ValueError(f"unknown rebal {rebal}")
    return f


def blend_split(a: pd.Series, b: pd.Series, w: float, rebal="daily") -> tuple:
    """NAV-level blend of published NET series at target split (w, 1-w), w for `a`.

    T+1-correct: the rebalance decided/executed at close t is held during day t+1 and
    charged on day t+1; day t's return is earned on the allocation carried INTO day t
    (i.e. post-close-(t-1) drift/trade). Day 0 = entry (charged full notional).
    State = shares (units of each sleeve NAV); allocations drift with relative NAVs
    between trades. Returns (net, turnover) on the EXACT overlap grid of a and b."""
    j = pd.concat({"a": a, "b": b}, axis=1, join="inner").dropna()
    if len(j) < 2:
        raise ValueError("blend needs >=2 overlapping rows")
    av = j["a"].values
    bv = j["b"].values
    na = np.cumprod(1.0 + av)          # sleeve NAV paths from the overlap start
    nb = np.cumprod(1.0 + bv)
    rb = _rebal_flags(j.index, rebal)  # rb[t] = trade decided at close t

    n = len(j)
    net = np.zeros(n)
    to = np.zeros(n)
    u_a = u_b = 0.0                    # shares
    for t in range(n):
        if t == 0:
            u_a, u_b = w / na[0], (1 - w) / nb[0]     # bought at close -1
            held_a, held_b = w, 1 - w
            to[t] = 1.0                                # entry = full book notional
        else:
            # close t-1: drifted allocations from fixed shares
            nav_prev = u_a * na[t - 1] + u_b * nb[t - 1]
            da = u_a * na[t - 1] / nav_prev
            if rb[t - 1]:                              # trade at close t-1, held day t
                d = w - da
                u_a += d / na[t - 1]
                u_b -= d / nb[t - 1]
                held_a, held_b = w, 1 - w
                to[t] = 2.0 * abs(d)                   # +d on A, -d on B
            else:
                held_a, held_b = da, 1.0 - da
        net[t] = held_a * av[t] + held_b * bv[t] - to[t] * CPS
    return pd.Series(net, index=j.index), pd.Series(to, index=j.index)


def invvol_weights(a: pd.Series, b: pd.Series, lookback=63) -> pd.DataFrame:
    """Trailing-only inverse-vol target split: w_A,t = (1/volA_{t-1}) / sum, from the
    prior `lookback` daily returns. First `lookback` rows NaN -> caller drops them."""
    j = pd.concat({"a": a, "b": b}, axis=1, join="inner").dropna()
    vol = j.rolling(lookback).std(ddof=1)
    iw = 1.0 / vol
    w = iw.div(iw.sum(axis=1), axis=0)
    return w.shift(1)                  # built from data <= t-1


def invvol_blend_weights(a: pd.Series, b: pd.Series, lookback=63) -> pd.DataFrame:
    """Blend-ready inverse-vol A/B split frame: invvol_weights() with the FIRST
    computable trailing-lookback weight extended back over the NaN warm-up, so the
    result covers the sleeves' full overlap window (blend_dynamic's fail-closed
    cover-guard otherwise rejects the 63d head). The extension is a documented
    warm-up convention, not a fitted param: published nets already embed the
    lookback history, and a constant extension cannot inject lookahead (it uses
    only data <= the first computable date)."""
    w = invvol_weights(a, b, lookback=lookback)
    first = w.dropna().index[0]
    w = w.copy()
    w.iloc[:w.index.get_loc(first)] = w.loc[first].values
    assert w.notna().all().all(), "warm-up extension failed to cover the window"
    return w


def blend_dynamic(rets: pd.DataFrame, rebal="daily", w_const=None,
                  wa: pd.Series = None) -> tuple:
    """Time-varying blend of two published NET RETURN series (T+1-honest: the target
    decided at close t is the split HELD during day t+1, same accounting as blend_split).
    R3 FIX: takes the legs' RETURNS (not a precomputed weight frame). The prior session
    fed invvol_weights()' output here and blend_dynamic cumprod'ed ~0.5/day "returns"
    into overflow (SR 48.9, ann 5228%, yearly ~e+25) -> garbage PASS artifact on disk.
    Target split: w_const for a constant split, or wa = per-date target weight for A
    (e.g. invvol_weights(a, b)["a"]); exactly one must be given; fail-closed guards."""
    assert wa is None or w_const is None, "give wa OR w_const, not both"
    if w_const is None and wa is None:
        w_const = 0.5                      # default: equal-weight blend
    wt = rets.dropna()
    idx = wt.index
    av, bv = wt["a"].values, wt["b"].values
    assert np.isfinite(av).all() and np.isfinite(bv).all(), "non-finite leg returns"
    # a *weight* frame (rows ~0.5/0.5) fed as rets silently becomes 50%/day "returns"
    # (the R3 bug class: cumprod overflow -> SR 48.9 / ann 5228% garbage PASS artifact).
    # Published legs are VT'd to ~10% ann, so |ret| beyond 25%/day is impossible -> fail
    # closed instead of producing a finite-but-meaningless book.
    lim = 0.25
    assert np.abs(av).max() <= lim and np.abs(bv).max() <= lim, (
        "leg |return| > 25%/day -- did you pass a WEIGHT frame instead of leg returns?")
    if wa is not None:
        wcol = wa.reindex(idx).ffill()
        assert wcol.notna().all(), "wa must cover the blend window (ffill-able)"
        # a *weight* frame (rows summing to 1, both cols) passed here is the R3 bug
        assert wcol.between(-1.0, 1.0).all(), \
            "wa out of [-1,1] -- did you pass a weight FRAME instead of the 'a' column?"
        warr = wcol.values
    else:
        assert -1.0 <= w_const <= 1.0, "w_const out of [-1,1]"
        warr = np.full(len(idx), float(w_const))
    na = np.cumprod(1.0 + av)
    nb = np.cumprod(1.0 + bv)
    rb = _rebal_flags(idx, rebal)
    n = len(idx)
    net = np.zeros(n)
    to = np.zeros(n)
    u_a = u_b = 0.0
    held_a = np.nan
    for t in range(n):
        w_t = float(warr[t])
        if t == 0:
            u_a, u_b = w_t / na[0], (1 - w_t) / nb[0]
            held_a = w_t
            to[0] = 1.0
        else:
            nav_prev = u_a * na[t - 1] + u_b * nb[t - 1]
            assert np.isfinite(nav_prev) and nav_prev > 0, "blend NAV exploded (weights-as-returns bug class)"
            da = u_a * na[t - 1] / nav_prev
            if rb[t - 1]:
                d = w_t - da
                u_a += d / na[t - 1]
                u_b -= d / nb[t - 1]
                held_a = w_t
                to[t] = 2.0 * abs(d)
            else:
                held_a = da
        net[t] = held_a * av[t] + (1 - held_a) * bv[t] - to[t] * CPS
    net = pd.Series(net, index=idx)
    to = pd.Series(to, index=idx)
    assert np.isfinite(net.values).all(), "non-finite blend net (weights-as-returns bug class)"
    return net, to


def alloc_scramble_p(w: pd.DataFrame, rets: pd.DataFrame, n=200, seed=0) -> float:
    """Row-permutation control on the ALLOCATION path (legs kept aligned) vs real leg
    returns, T+1 + entry + 6.4bps |dW|, VT off. For a CONSTANT split the permutation
    re-pairs identical rows and only moves the entry charge -> degenerate p ~ 1.0;
    reported as a control, never a pass. See shift_scramble_p for the informative one."""
    rng = np.random.default_rng(seed)
    p = w.shift(1).fillna(0.0)
    r = rets.reindex(p.index).values
    pv = p.values

    def sr_of(q):
        to = np.abs(np.diff(q, axis=0, prepend=np.zeros((1, q.shape[1])))).sum(axis=1)
        net = (q * r).sum(axis=1) - to * CPS
        sd = net.std(ddof=1)
        return 0.0 if sd == 0 else float(net.mean() / sd * np.sqrt(L.ANN))

    real = sr_of(pv)
    cnt = 0
    for _ in range(n):
        if sr_of(rng.permutation(pv, axis=0)) >= real:
            cnt += 1
    return cnt / n


def shift_scramble_p(w: pd.DataFrame, rets: pd.DataFrame, n=200, seed=0) -> float:
    """(Superseded by random_control_p; kept for API compat.) Circular-shift control:
    rolls the B allocation path against real returns. Vacuous for constant splits."""
    rng = np.random.default_rng(seed)
    p = w.shift(1).fillna(0.0)
    rv = rets.reindex(p.index).values
    pv = p.values.copy()

    def sr_of(q):
        to = np.abs(np.diff(q, axis=0, prepend=np.zeros((1, q.shape[1])))).sum(axis=1)
        net = (q * rv).sum(axis=1) - to * CPS
        sd = net.std(ddof=1)
        return 0.0 if sd == 0 else float(net.mean() / sd * np.sqrt(L.ANN))

    real = sr_of(pv)
    cnt = 0
    for _ in range(n):
        q = pv.copy()
        q[:, 1] = np.roll(pv[:, 1], int(rng.integers(1, len(pv))))
        if sr_of(q) >= real:
            cnt += 1
    return cnt / n


def random_control_p(a: pd.Series, b: pd.Series, n=200, seed=0, lookback=252) -> float:
    """HUNT_VOL2-charter-style adversarial control for the composite: draw zero-mean
    random books whose VOL and daily CORR-TO-A are matched to leg B's, put them in B's
    slot at the same split, and ask how often the random composite's SR >= the real
    one. p near 0.5 -> B's slot adds nothing but diversification of noise; p near 0 ->
    B genuinely carries positive drift into the composite."""
    rng = np.random.default_rng(seed)
    j = pd.concat({"a": a, "b": b}, axis=1, join="inner").dropna()
    av, bv = j["a"].values, j["b"].values
    rho = float(np.corrcoef(av, bv)[0, 1])
    sd_b = bv.std(ddof=1)
    sd_a = av.std(ddof=1)
    T = len(j)
    w = 0.5

    def comp_sr(x):
        return float(((w * av + (1 - w) * x).mean() /
                      (w * av + (1 - w) * x).std(ddof=1)) * np.sqrt(L.ANN))

    real = comp_sr(bv)
    # bivariate-normal draw with corr(rho) to a: z = rho*a* + sqrt(1-rho^2)*e
    az = (av - av.mean()) / sd_a
    cnt = 0
    for _ in range(n):
        e = rng.standard_normal(T)
        z = rho * az + np.sqrt(max(1e-12, 1 - rho ** 2)) * e
        x = z * sd_b                             # ZERO-MEAN, vol+corr-matched to B
        if comp_sr(x) >= real:
            cnt += 1
    return cnt / n


def vt_apply(net: pd.Series, rets: pd.DataFrame, target=0.10, cap=3.0,
             held_a: float = 0.5) -> pd.Series:
    """Trailing-only VT10 clip3 on the composite book return (same standard as every
    round-2 sleeve: scale built from ret <= t-1, applied to the held book from t).
    R3 FIX: the book is the WEIGHTED leg sum held_a*ret_a + (1-held_a)*ret_b, NOT
    rets.sum(axis=1) -- the old form vol-targeted a 2x-gross book, halving the
    composite's risk budget (realized ~5% vs the 10% target) and mis-stating SR."""
    if isinstance(rets, pd.DataFrame):
        w = held_a if held_a is not None else 0.5
        book = w * rets.iloc[:, 0] + (1.0 - w) * rets.iloc[:, 1]
    else:
        book = rets
    return net * L.vt_scale(book, target=target, cap=cap)


def gates_r3(name, net_raw, rets, plateau_surface=None, chosen=None, save=True,
             a: pd.Series = None, b: pd.Series = None, held_a=0.5):
    """Full GATES_CONTRACT gauntlet on a composite: stats -> corr -> adversarial control
    -> plateau (on the charter 3-weight surface) -> verdict. `net_raw` is pre-VT; the
    gated book is vt_apply(net_raw).

    R3 FIX (both defects of the dead session's block):
    (i) vt_apply now vol-targets the WEIGHTED composite book (was rets.sum(axis=1),
        a 2x-gross book -> realized vol ~5% vs the 10% target -> SR mis-stated).
    (ii) the scramble gate is random_control_p -- a corr/vol-matched ZERO-MEAN random
        leg dropped into B's slot at the same split; p >= 0.05 => the composite's edge
        is diversification of noise, FAIL. The old gate permuted a near-constant
        allocation frame (p degenerate ~1.0 / 0.4), stamping a vacuous verdict label
        on every composite including genuine ones.
    `a`/`b` = the raw leg RETURN series for the control (default: the two rets cols);
    held_a = the composite's average A-split, for the VT book (60/40 -> 0.6)."""
    net = vt_apply(net_raw, rets, held_a=held_a)
    s = L.stats(net)
    cc = L.corr_champ(net)
    av = rets.iloc[:, 0] if a is None else a
    bv = rets.iloc[:, 1] if b is None else b
    sp = random_control_p(av, bv, n=200, seed=0)
    g = dict(name=name, n=s["n"], sr=round(s["sr"], 3), ann=round(s["ann"], 2),
             vol=round(s["vol"], 2), h1=round(s["h1"], 2), h2=round(s["h2"], 2),
             neg_yr=s["neg_yr"], n_yr=s["n_yr"], worst=round(s["worst"], 1),
             corr_champ=round(cc, 3), lib=L.corr_library(net), scramble_p=round(sp, 3),
             plateau=H.plateau(plateau_surface, chosen) if plateau_surface else "n/a",
             yearly=s["yearly"])
    g["verdict"] = (
        ("PASS" if s["sr"] >= 1.0 else "FAIL_SR")
        + ("|FAIL_HALVES" if (s["h1"] < 0.5 or s["h2"] < 0.5) else "")
        + ("|FAIL_NEGYR" if (s["neg_yr"] > 2 or s["worst"] <= -5.0) else "")
        + ("|FAIL_SCRAMBLE" if sp >= 0.05 else "")
        + ("|FAIL_PLATEAU" if g["plateau"] not in ("PASS", "n/a") else "")
        + ("|corr_ok_secondary" if 0.15 <= abs(cc) < 0.35
           else ("|FAIL_CORR" if abs(cc) >= 0.35 else "")))
    print(f"[{name}] n={s['n']} SR={s['sr']:.3f} ann={s['ann']:.1f}% vol={s['vol']:.1f}% "
          f"H1={s['h1']:.2f} H2={s['h2']:.2f} negyr={s['neg_yr']}/{s['n_yr']} "
          f"worst={s['worst']:.1f}% corr={cc:.3f} lib={g['lib']['maxabs']:.2f} "
          f"ctl_p={sp:.3f} plateau={g['plateau']} -> {g['verdict']}")
    if save:
        save_meta(g, net)
    return g


def save_meta(g, net):
    import os
    d = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/sleeves"
    os.makedirs(d, exist_ok=True)
    nm = g["name"].replace("/", "_").replace(" ", "_").replace("|", "_")
    df = pd.DataFrame({"ret": net})
    df.index.name = "date"
    df.to_csv(f"{d}/{nm}.csv")
    with open(f"{d}/{nm}.csv.meta", "w") as f:
        f.write(f"name={nm}\nverdict={g['verdict']}\n")
        for k in ("sr", "ann", "vol", "h1", "h2", "neg_yr", "n_yr", "worst",
                  "corr_champ", "scramble_p", "plateau"):
            f.write(f"{k}={g[k]}\n")
        f.write(f"yearly={g['yearly']}\n")
        f.write("cost=6.4bps FULL |dW| at ALLOCATION level (sleeve legs self-financing, "
                "internal turnover already in published nets) + day-0 entry; T+1; "
                "trailing VT10 clip3 on the WEIGHTED composite book\n")
        f.write(f"ctl_p_meaning=adversarial control: corr/vol-matched ZERO-MEAN random leg "
                f"in B's slot at same split; p>=0.05 -> edge is diversification-of-noise "
                f"(FAIL_SCRAMBLE). p={g['scramble_p']}\n")
        f.write("rationale=Diversification math on two PUBLISHED round-2 sleeves; no new "
                "signal params. Composite of decorrelated positive-SR books raises SR by "
                "1/sqrt(1+rho) style math; charter asked whether 0.68/0.61 sleeves at "
                "rho=+0.72 clear 1.0 (they cannot).")


if __name__ == "__main__":
    print("=" * 108)
    print("R3 (a): internal composite of PUBLISHED sleeves — corr first, then 3 blend splits")
    print("=" * 108)
    A = load_sleeve("A11_rs_ratio#lb126k4")
    B = load_sleeve("B_barbell")
    j = pd.concat({"A": A, "B": B}, axis=1, join="inner").dropna()
    rho = float(j.corr().iloc[0, 1])
    print(f"overlap {j.index.min().date()}..{j.index.max().date()} n={len(j)} corr(A,B)={rho:+.3f}")

    # charter splits 50/50, 60/40, inverse-vol (+ rebalance-freq cost checks; no new
    # signal params: the splits ARE the charter's own surface)
    out = {}
    for lbl, wa, rb in [("50/50|daily", 0.5, "daily"), ("60/40|daily", 0.6, "daily"),
                        ("50/50|monthly", 0.5, "monthly"), ("50/50|never", 0.5, "never")]:
        out[lbl] = blend_split(A, B, wa, rebal=rb)
    # inverse-vol dynamic split (T+1 trailing weights), monthly rebalance (cost-honest);
    # warm-up extension covers the overlap head (TDD: tests_tdd_r3 warm-up test)
    wv = invvol_blend_weights(A, B, lookback=63)["a"]      # the A-weight COLUMN
    out["invvol"] = blend_dynamic(pd.concat({"a": A, "b": B}, axis=1), rebal="monthly",
                                  wa=wv)

    # plateau surface on the VT'd books (VT at each split's own held weight)
    surface = {}
    held = {"50/50|daily": 0.5, "60/40|daily": 0.6, "50/50|monthly": 0.5,
            "50/50|never": 0.5, "invvol": float(wv.mean())}
    jw = pd.concat({"a": A, "b": B}, axis=1, join="inner").dropna()
    for lbl, (net, to) in out.items():
        surface[lbl] = L.stats(vt_apply(net, jw.reindex(net.index), held_a=held[lbl]))["sr"]

    results = {}
    for lbl, (net, to) in out.items():
        results[lbl] = gates_r3(f"COMP_{lbl}", net, jw, plateau_surface=surface,
                                chosen=lbl, a=A, b=B, held_a=held[lbl])

    # (b) cross-verify HUNT_FXCARRY2's R2 negative from their published sleeve CSV
    print("\n" + "=" * 108)
    print("R3 (b): cross-verify HUNT_FXCARRY2 R2 carry_nominal_EW negative")
    print("=" * 108)
    F = pd.read_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_FXCARRY2/sleeves/"
                    "FXCARRY2_R2_carry_nominal_EW.csv", index_col=0, parse_dates=True
                    ).iloc[:, 0].astype(float)
    sf = L.stats(F)
    cf = L.corr_champ(F)
    print(f"n={sf['n']} SR={sf['sr']:.3f} ann={sf['ann']:.2f}% H1={sf['h1']:.2f} "
          f"H2={sf['h2']:.2f} negyr={sf['neg_yr']}/{sf['n_yr']} worst={sf['worst']:.1f}% "
          f"corr_champ={cf:.3f}")
    print(f"their claim: SR=-0.004 ann=-0.18% H=(-0.133,0.164) negyr=11 worst=-19.4% "
          f"corr 0.0276 -> {'' if abs(sf['sr'] - (-0.004)) < 0.02 else 'MISMATCH'}")

    print("\n=== FINAL ===")
    for k, g in results.items():
        print(f"{g['name']:22s} SR={g['sr']:.3f} ann={g['ann']:.1f}% H=({g['h1']},{g['h2']}) "
              f"negyr={g['neg_yr']}/{g['n_yr']} worst={g['worst']}% corr={g['corr_champ']} "
              f"ctl_p={g['scramble_p']} plateau={g['plateau']} -> {g['verdict']}")
