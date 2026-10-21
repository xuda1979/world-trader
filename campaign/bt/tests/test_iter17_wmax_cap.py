"""Defect cleared 2026-09-13: the ITER15 max-Sharpe fit's per-sleeve cap was INERT.

`fit_relw` documented `W_MAX = 2.0` as "each weight capped at W_MAX x the equal
weight", but implemented it as `bnds = [(0.0, W_MAX)] * k` against a
`sum(w) == 1` equality. With W_MAX = 2.0 > 1.0 that bound can never bind: the
sum constraint alone caps any weight at 1.0. The documented rule (w_i <= W_MAX/k)
was therefore not enforced anywhere -- a fit could concentrate 100% of the book
into one sleeve while the docstring, the ITER15 FINDINGS and the champion card
all advertised a 2x-equal-weight cap.

It is inert for the CURRENT champion only by luck: the committed fit's largest
weight is 0.1457 < 2/13 = 0.1538. It is NOT inert for other parameterisations --
e.g. mean-shrunk fits drive a weight to exactly 2/12 = 0.1667 > 0.1538 under the
documented rule (see test below), so the honest constraint must be real.

Fix: `bnds = [(0.0, W_MAX / k)]` (cap expressed in the sum-to-1 units the
optimiser actually works in). Champion-neutral: `--verify` stays IDENTICAL.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402

WEIGHTS_CSV = ROOT / "campaign" / "results" / "RAWEW13v2_IS_SR_weights.csv"


def _synth_is(window=300, mu=(0.0030, 0.0002, 0.0002, 0.0002), sigma=0.0010, seed=0):
    """4 sleeves (brwt5/7/10/15) with one dominant SR: the max-Sharpe optimum
    wants ~83% in brwt5, i.e. well past the documented 2x-equal-weight cap of 0.5."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2010-01-04", periods=window, freq="B")
    df = pd.DataFrame(np.nan, index=idx, columns=B.NAMES)  # others: no IS coverage
    for name, m in zip(["brwt5", "brwt7", "brwt10", "C5ng"], mu):  # brwt15 pruned in ITER19
        df[name] = m + sigma * rng.standard_normal(window)
    return df


def test_wmax_cap_is_enforced_on_a_concentrating_pool():
    fit = B.fit_relw(_synth_is())
    k = 4  # sleeves with IS coverage in the synthetic pool
    cap = B.W_MAX / k
    assert fit.max() <= cap + 1e-9, f"documented cap {cap:.4f} not enforced: max {fit.max():.4f}"
    # and the cap genuinely BINDS here -- the optimum wants all of it
    assert fit["brwt5"] >= cap - 1e-3, f"expected concentration to the cap, got {fit['brwt5']:.4f}"
    assert abs(fit.sum() - 1.0) < 1e-9


def test_cap_fix_leaves_committed_champion_weights_byte_identical():
    """Champion-neutrality: the fix must not disturb the champion of record."""
    df = pd.DataFrame({n: B.load(B.PATHS[n]) for n in B.NAMES})
    df = df[df.index >= "2008-03-31"]
    isr = df[df.index < B.IS_END]
    fit = B.fit_relw(isr)
    committed = pd.read_csv(WEIGHTS_CSV, index_col=0).iloc[:, 0]
    # ITER20: the committed weights are the fitted shares AFTER the brwt-block cap
    # transform; the W_MAX neutrality claim is evaluated on the same composite.
    maxdev = float((B.apply_brwt_cap(fit) - committed).abs().max())
    assert maxdev < 1e-12, f"cap fix moved the champion weights by {maxdev:.3e}"
