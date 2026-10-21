#!/usr/bin/env python3
"""AUDIT_GATES2 ROUND 3 (b) — composition-preserving scramble DIAGNOSTIC.

NOT-A-GATE: this is NOT wired into bt.gates.run and must never be. The regular
signal-scramble (gates.scramble_positions) certifies SIGNAL timing; R2 proved it is
vacuous for composition books (champion p=0.83 under weight-roll on the pre-costfix
vintage). This diagnostic asks the complementary question: does a book's SR come from
the COMPOSITION's timing (when each slot is loaded), or would any time-shift of the
same composition earn the same thing?

Two lag variants are measured; only A is the calibrated diagnostic:

  A. COMMON-LAG (PRIMARY, "composition-preserving"): roll the ENTIRE weight matrix
     W by ONE random lag L ~ U[block, T-block] per draw (R fixed). The 13-column
     composition moves as a block, so cross-slot composition is preserved exactly;
     each slot's alpha stream is untouched (alpha-preserving); only the TIMING of the
     composition vs the slot returns is destroyed. Costs re-charged on the shifted
     book's own |dW| + margin (an honest re-pricing of the hypothetical book).
     Calibration target: champion NOT flagged (p >= 0.05; charter cites R2's ~0.5-0.8
     reading), noise books flag at ~5% (null uniform), DETECT fixture p < 0.05.

  B. PER-SLOT independent lags (documented NEGATIVE result, not the diagnostic):
     rolling each slot's returns by an INDEPENDENT lag desynchronizes cross-slot
     co-movement — a variance effect, not a timing effect (mean of the sum is
     lag-invariant, correlated slots' co-movement is not). On the champion the null
     mean SR sits ABOVE the real SR (p degenerates to 1.000), so B is a synchrony /
     risk-structure probe, NOT a composition-timing probe. Reported to close the door
     on per-slot lags as a "composition" scramble for correlated-slot books.

Fixtures:
  champion     real builder-reproduced champion (byte-verified to the committed CSV).
  noise        200 static-composition books on iid noise slots -> must NOT be flagged
               (flag rate <= 5% under A).
  detect       composition-TIMING fixture: 13 persistent-alpha slots, weights =
               trailing-63d momentum rotation (long recent winners). Real SR must beat
               every common-lagged null (p < 0.05) — a mistimed composition loses it.
  detect_ctl   SAME slots, weights frozen constant -> timing-independent by
               construction, must NOT be flagged (isolates TIMING as the quantity).

Usage: python3 campaign/agents/chief/coord/AUDIT_GATES2/r3/r3b_composition_scramble.py
"""
from __future__ import annotations
import sys, json
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")

from bt.metrics import sharpe_d                      # noqa: E402
import rawew13v2_build as builder                    # noqa: E402

SEED = 7
BLOCK = 20
GEAR, RATE, BPS = builder.GEAR, builder.RATE, builder.BPS


def book_sr(W: np.ndarray, R: np.ndarray) -> float:
    """Net book SR with the campaign cost algebra: full |dW| x 6.4bps + margin on
    (gear-1). Re-charged per draw, so each hypothetical book pays its own turnover."""
    port = (R * W).sum(axis=1)
    to = np.abs(np.diff(W, axis=0, prepend=W[:1])).sum(axis=1)
    net = port - to * BPS / 1e4 - max(GEAR - 1, 0) * RATE / 252
    return float(sharpe_d(pd.Series(net)))


def common_lag_p(W: np.ndarray, R: np.ndarray, n: int = 200, seed: int = SEED,
                 block: int = BLOCK) -> dict:
    """Variant A: p-value of the real book under whole-matrix block-lags of W."""
    rng = np.random.default_rng(seed)
    T = len(R)
    real = book_sr(W, R)
    nulls = np.empty(n)
    vols = np.empty(n)
    for j in range(n):
        lag = int(rng.integers(block, T - block + 1))
        nulls[j] = book_sr(np.roll(W, lag, axis=0), R)
        vols[j] = float(pd.Series((R * np.roll(W, lag, axis=0)).sum(axis=1)).std())
    real_vol = float(pd.Series((R * W).sum(axis=1)).std())
    return dict(p=float((nulls >= real).mean()), real_sr=real,
                null_mean=float(nulls.mean()), null_sd=float(nulls.std()),
                null_p05=float(np.percentile(nulls, 5)),
                null_p95=float(np.percentile(nulls, 95)),
                real_port_vol=real_vol, null_port_vol_mean=float(vols.mean()),
                n=n, block=block, seed=seed, nulls=nulls.tolist())


def per_slot_lag_p(W: np.ndarray, R: np.ndarray, n: int = 200, seed: int = SEED,
                   block: int = BLOCK) -> dict:
    """Variant B (negative result, see module docstring): independent per-slot lags of R."""
    rng = np.random.default_rng(seed)
    T = len(R)
    real = book_sr(W, R)
    nulls = np.empty(n)
    vols = np.empty(n)
    lags = rng.integers(block, T - block + 1, size=(n, R.shape[1]))
    for j in range(n):
        Rj = np.column_stack([np.roll(R[:, i], lags[j, i]) for i in range(R.shape[1])])
        nulls[j] = book_sr(W, Rj)
        vols[j] = float(pd.Series((Rj * W).sum(axis=1)).std())
    real_vol = float(pd.Series((R * W).sum(axis=1)).std())
    return dict(p=float((nulls >= real).mean()), real_sr=real,
                null_mean=float(nulls.mean()), null_sd=float(nulls.std()),
                null_p05=float(np.percentile(nulls, 5)),
                null_p95=float(np.percentile(nulls, 95)),
                real_port_vol=real_vol, null_port_vol_mean=float(vols.mean()),
                n=n, block=block, seed=seed, nulls=nulls.tolist())


def champion_weights(df: pd.DataFrame) -> np.ndarray:
    """The builder's causal weight path for sleeve frame df (verbatim pipeline)."""
    isr = df[df.index < builder.IS_END]
    SR = pd.Series({k: builder.is_sr(isr[k]) for k in df.columns})
    relw = np.maximum(SR, 0.0) ** builder.P
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(df.columns)
    return (d2 * (GEAR / len(df.columns))).values


def champion_frame():
    names = builder.NAMES
    df = pd.DataFrame({k: builder.load(builder.PATHS[k]).dropna() for k in names})
    return df[df.index >= "2008-03-31"]


def make_slots(T: int, n_slot: int, phi: float, alpha_share: float,
               rng: np.random.Generator) -> np.ndarray:
    """Persistent-alpha slots: r = mu + e with AR(1) mu. alpha_share sets mu's vol
    fraction; phi sets its persistence (the thing a momentum rotation can harvest)."""
    sd_tot = 0.01
    sd_mu = sd_tot * alpha_share
    sd_e = sd_tot * np.sqrt(1 - alpha_share ** 2)
    mu = np.empty((T, n_slot))
    mu[0] = rng.normal(0, sd_mu, n_slot)
    for t in range(1, T):
        mu[t] = phi * mu[t - 1] + rng.normal(0, sd_mu * np.sqrt(1 - phi ** 2), n_slot)
    return mu + rng.normal(0, sd_e, (T, n_slot))


def rotation_weights(R: np.ndarray, lookback: int = 63, gross: float = GEAR) -> np.ndarray:
    """Momentum composition: overweight recent WINNERS (relu of cross-sectional z of the
    trailing mean return), T+1 causal. Not |z|: a magnitude tilt would key on vol, not
    direction (first-draft bug: real book SR came out negative)."""
    mom = pd.DataFrame(R).rolling(lookback).mean().shift(1).values
    z = (mom - np.nanmean(mom, axis=1, keepdims=True)) / (
        np.nanstd(mom, axis=1, keepdims=True) + 1e-12)
    w = np.nan_to_num(np.maximum(np.nan_to_num(z), 0.0))
    w = w / np.maximum(w.sum(axis=1, keepdims=True), 1e-12) * gross
    return w


def main():
    out = {"seed": SEED, "block": BLOCK, "not_a_gate": True}
    champ_path = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

    # -- champion: reproduce the builder, byte-verify against the committed CSV -------
    df = champion_frame()
    W = champion_weights(df)
    R = df.fillna(0).values
    port = (R * W).sum(axis=1)
    to = pd.DataFrame(W).diff().abs().sum(axis=1).fillna(0.0).values
    net = pd.Series(port - to * BPS / 1e4 - max(GEAR - 1, 0) * RATE / 252, index=df.index)
    committed = pd.read_csv(champ_path, index_col=0, parse_dates=True).iloc[:, 0]
    dev = float((net - committed.reindex(net.index)).abs().max())
    out["champion_byte_repro_max_dev"] = dev
    assert dev < 1e-12, f"champion rebuild deviates: {dev}"
    T = len(R)

    # -- 1. champion under the composition-preserving common-lag (PRIMARY) ------------
    r1 = common_lag_p(W, R, n=200)
    out["champion_common_lag"] = {k: v for k, v in r1.items() if k != "nulls"}
    print(f"champion common-lag: p={r1['p']:.3f} real={r1['real_sr']:.4f} "
          f"null mean={r1['null_mean']:.4f}+-{r1['null_sd']:.3f} "
          f"[p05 {r1['null_p05']:.4f}, p95 {r1['null_p95']:.4f}] "
          f"vol real/null={r1['real_port_vol']:.5f}/{r1['null_port_vol_mean']:.5f}")

    # -- 2. champion under per-slot independent lags (documented negative result) -----
    r2 = per_slot_lag_p(W, R, n=200)
    out["champion_per_slot_lag"] = {k: v for k, v in r2.items() if k != "nulls"}
    print(f"champion per-slot  : p={r2['p']:.3f} real={r2['real_sr']:.4f} "
          f"null mean={r2['null_mean']:.4f} [p05 {r2['null_p05']:.4f}, "
          f"p95 {r2['null_p95']:.4f}] vol real/null="
          f"{r2['real_port_vol']:.5f}/{r2['null_port_vol_mean']:.5f}  <- synchrony probe")

    # -- 3. noise control: static random compositions must NOT be flagged -------------
    rng = np.random.default_rng(SEED + 2)
    flags = 0
    n_books, n_nulls = 200, 100
    noise_ps = np.empty(n_books)
    for b in range(n_books):
        Rb = rng.normal(0, 0.01, (T, len(df.columns)))
        vol = rng.uniform(0.005, 0.02, len(df.columns))
        Rb = Rb / Rb.std(axis=0) * vol
        Wb = np.abs(rng.normal(1, 0.3, (T, len(df.columns))))
        slow = pd.DataFrame(Wb).rolling(60).mean().fillna(1.0).values
        Wb = slow / slow.sum(axis=1, keepdims=True) * GEAR
        noise_ps[b] = common_lag_p(Wb, Rb, n=n_nulls, seed=SEED + 100 + b)["p"]
        flags += int(noise_ps[b] < 0.05)
    out["noise_static"] = dict(n_books=n_books, n_nulls=n_nulls, flag_rate=flags / n_books,
                               p_mean=float(noise_ps.mean()), p_min=float(noise_ps.min()),
                               p_max=float(noise_ps.max()))
    print(f"noise static x{n_books} (100 nulls each): flag rate {flags}/{n_books}="
          f"{flags / n_books:.3f} p mean={noise_ps.mean():.3f} "
          f"[min {noise_ps.min():.3f}, max {noise_ps.max():.3f}]")

    # -- 4. DETECT fixture: composition-timing book (trailing-momentum rotation) ------
    # phi=0.99 daily (~69d half-life, matched to the 63d lookback): probed grid
    # phi in {0.15,0.99,0.995,0.998,0.999} x alpha_share in {0.3,0.5}; phi=0.15
    # (4-day half-life) gives the rotation nothing to harvest (real SR -0.34, p=0.41)
    # and was rejected — a DETECT fixture must contain real timing to detect.
    Rf = make_slots(T, len(df.columns), phi=0.99, alpha_share=0.30,
                    rng=np.random.default_rng(SEED + 3))
    Wf = rotation_weights(Rf)
    r4 = common_lag_p(Wf, Rf, n=200)
    out["detect_rotation_fixture"] = {k: v for k, v in r4.items() if k != "nulls"}
    print(f"DETECT rotation  : p={r4['p']:.3f} real={r4['real_sr']:.4f} "
          f"null mean={r4['null_mean']:.4f} [p05 {r4['null_p05']:.4f}, "
          f"p95 {r4['null_p95']:.4f}]")
    # static control: SAME slots, weights frozen constant -> timing-independent
    Ws = np.repeat(Wf[80:81], T, axis=0)
    r4s = common_lag_p(Ws, Rf, n=200)
    out["detect_static_control"] = {k: v for k, v in r4s.items() if k != "nulls"}
    print(f"  static control : p={r4s['p']:.3f} real={r4s['real_sr']:.4f} "
          f"null mean={r4s['null_mean']:.4f} (must NOT be flagged)")

    # -- verdict ------------------------------------------------------------------------
    ok = (out["champion_common_lag"]["p"] >= 0.05
          and out["noise_static"]["flag_rate"] <= 0.05
          and out["detect_rotation_fixture"]["p"] < 0.05
          and out["detect_static_control"]["p"] >= 0.05)
    out["calibration_ok"] = bool(ok)
    print(f"\nCALIBRATION {'OK' if ok else 'FAILED'}: champion not flagged under "
          f"common-lag, noise flag rate <=5%, DETECT fixture p<0.05, static control not flagged")
    json.dump(out, open(f"{ROOT}/campaign/agents/chief/coord/AUDIT_GATES2/r3/r3b_results.json",
                        "w"), indent=1)
    print("saved r3b_results.json")


if __name__ == "__main__":
    main()
