#!/usr/bin/env python3
"""Emit the synthetic 3-sleeve mini-champion fixture for bt/verify_champion.py TDD.

Deterministic (numpy Generator(PCG64) seed 7, fresh per call so every emit() of the same
variant is byte-identical). Layout matches the committed champion family in FORMAT so
verify_champion can be exercised end-to-end:
  {out}/mini_champion.csv        [date,ret]        net daily returns of the mini book
  {out}/mini_weights.csv         [ ,relw]          IS-SR-fitted relw per sleeve
  {out}/sleeves/{name}.csv       [date,ret]        net sleeve returns (already net of own costs)

The mini book is built with EXACTLY the champion mechanism (rawew13v2_build.py):
  relw_i = max(IS_SR_i, 0)^P on IS window (index < is_end)
  nav = (1 + r).cumprod().shift(1).fillna(1.0)        # T+1 causal (R1 re-emit mechanism)
  d2 = nav / rowmean(nav) * relw ; row-normalize to sum(N); Wg = d2 * (GEAR/N)
  port = sum_i r_i * Wg_i
  to = sum_i |dWg_i| (FULL |dW|, one-side, per TRADE_RECORD_STANDARD)
  net = port - to*bps/1e4 - max(margin_gear-1,0)*rate/252

Defect knobs (used ONLY by the TDD tests to inject single defects):
  causal=False        same-day weights (nav NOT shifted)  -> verifier must FAIL
  cost_mult=0.5       half-turn undercharge                -> verifier must FAIL
  gear=1.7            gross above the 1.6 cap              -> verifier must FAIL
  year_mutation       rescale one sleeve in one calendar yr -> neg-year gate must FAIL

Usage: python3 make_mini_champion.py OUTDIR
"""
import os, sys
import numpy as np
import pandas as pd

N_DAYS = 600
START = "2024-01-01"
IS_END = pd.Timestamp("2025-01-01")   # IS window = first ~252 bdays; OOS the rest
GEAR, RATE, BPS, P = 1.6, 0.045, 6.4, 0.55
NAMES = ["alfa", "bravo", "charlie"]


def sleeve_paths(outdir):
    return {n: f"{outdir}/sleeves/{n}.csv" for n in NAMES}


def emit(outdir, causal=True, cost_mult=1.0, gear=GEAR, margin_gear=None,
         year_mutation=None):
    """Build + write one fixture variant. Returns dict of internals for assertions.

    year_mutation: (name, year, factor) -> multiply that sleeve's returns in `year`.
    """
    os.makedirs(f"{outdir}/sleeves", exist_ok=True)
    rng = np.random.default_rng(7)
    idx = pd.bdate_range(START, periods=N_DAYS)
    # Sleeve returns: mild AR-free noise, per-sleeve scale; positive drift so IS SR > 0 and
    # relw spreads across sleeves; yearly drift chosen so the CLEAN book has 0 neg years
    # (calibrated 2026-09-07: x1.0/1.5/2.0 all leave 2026 negative, x2.5 gives negyr=0).
    scales = {"alfa": 0.006, "bravo": 0.004, "charlie": 0.003}
    drift = {"alfa": 7.5e-4, "bravo": 5.5e-4, "charlie": 4.0e-4}
    df = pd.DataFrame(
        {n: drift[n] + rng.normal(0.0, scales[n], N_DAYS) for n in NAMES}, index=idx)
    if year_mutation is not None:
        n, yr, f = year_mutation
        df.loc[df.index.year == yr, n] *= f
    # champion mechanism, verbatim from rawew13v2_build.py
    isr = df[df.index < IS_END]
    sr = {n: float(isr[n].mean() / isr[n].std(ddof=1) * np.sqrt(252)) for n in NAMES}
    relw = pd.Series({n: max(sr[n], 0.0) ** P for n in NAMES})
    nav = (1 + df.fillna(0)).cumprod()
    if causal:
        nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (gear / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    mg = gear if margin_gear is None else margin_gear
    net = (pd.Series(port, index=idx) - to * (cost_mult * BPS) / 1e4
           - max(mg - 1, 0) * RATE / 252)
    net.to_frame("ret").to_csv(f"{outdir}/mini_champion.csv")
    relw.to_frame("relw").to_csv(f"{outdir}/mini_weights.csv", index_label="")
    for n in NAMES:
        df[n].to_frame("ret").to_csv(f"{outdir}/sleeves/{n}.csv")
    return dict(sr=sr, relw=relw, Wg=Wg, net=net, to=to, df=df)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "mini_champion")
    info = emit(out)
    y = (1 + info["net"]).groupby(info["net"].index.year).prod().sub(1)
    navc = (1 + info["net"]).cumprod()
    print(f"emitted fixture to {out}: n={len(info['net'])} IS-SR={info['sr']}")
    print(f"  neg_years={int((y < 0).sum())} worst_year={y.min():.4f} "
          f"MDD={(navc / navc.cummax() - 1).min():.4f}")
