"""ITER19 ADOPTION — prune the dominated brwt sleeve (operator-approved 2026-09-13).

`brwt15` was the weakest and dominated member of the brwt block: IS SR 2.937 against its
siblings brwt5 2.978 / brwt10 3.614 / brwt7 3.726, with +0.62..+0.84 mutual correlation — one
Brent-WTI mean-reversion bet expressed four times, and it held 12.7% of the champion's book.
Its presence forced the rule's `IS MDD >= -6.0%` bound to bite at shrink 0.62; without it the
pre-committed rule concentrates to shrink 0.98 and the pool shrink 13 -> 12.

Why this is not the usual in-sample trap: the gain is OOS-DRIVEN (OOS +1.44pp EXCEEDS the
IS +1.16pp) and positive in ALL FIVE sub-windows. Every metric improves at once:

    FULL ann  38.114% -> 39.500%      SR 3.2358 -> 3.2176 (flat)
    FULL MDD  -6.5620% -> -6.5232%    (BETTER)
    turnover  5.3030 -> 4.7660 bp/yr  (BETTER)
    OOS ann   41.692% -> 43.150%      OOS >= IS  PASS

Contrast with the two candidates REJECTED this session: brwt(15,1.0) (+1.118pp, but IS +2.26
vs OOS +0.04) and RB_hobr (+0.52pp IS, -1.39pp OOS). Those were in-sample fits; this is not.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402


def _stats(net):
    net = net.dropna()
    nav = (1 + net).cumprod()
    ann = float(nav.iloc[-1] ** (252.0 / len(net)) - 1)
    sr = float(net.mean() / net.std(ddof=1) * np.sqrt(252))
    mdd = float((nav / nav.cummax() - 1).min())
    return ann, sr, mdd


def test_brwt15_is_pruned_from_the_pool():
    assert "brwt15" not in B.NAMES, "the dominated brwt sleeve must be out of the champion pool"
    assert len(B.NAMES) == 12
    # ITER20 (2026-09-18): the operator objective moved to Sharpe-max and the (shrink, cap)
    # re-selection picks 0.70 + brwt-cap 0.30; the ITER19 ann-max re-selection was 0.98 and
    # stays byte-reproducible via build(shrink_d=0.98, brwt_cap=None).
    assert abs(B.SHRINK_D - 0.70) < 1e-12, "ITER20 re-selection picks shrink 0.70 on the 12-sleeve pool"


def test_adopted_champion_stats_and_gates():
    # Re-pinned at ITER20 (2026-09-18), ITER21 (2026-09-18) and ITER43 (2026-09-19): champion
    # of record is the Sharpe-max weight vector at the canonical gear 1.0 (the gear lever:
    # margin 4.5%/yr on (gear-1) makes net SR strictly decreasing above gear 1). ITER43
    # re-pin: A5r2 VT-axis argmax (vt015 sleeve); was 23.6054 / 3.751429 / -3.6130 at ITER21
    # -- that era's champion is preserved in coord/ITER43_A5R2_VT/prior_champion_backup/.
    # ITER47 re-pin (2026-09-19): vt024 extension; was 23.6813 / 3.764764 / -3.6603.
    # ITER49 re-pin (2026-09-19): tsmom vt015 adoption; was 23.7668 / 3.784099 / -3.7012 at ITER47.
    # (was 39.500 / 3.2176 / -6.5232 under ann-max; 36.4150 / 3.4551 / -5.9284 at ITER20.)
    net, relw, gross, to, _ = B.build()
    ann, sr, mdd = _stats(net)
    assert abs(ann * 100 - 23.9215) < 0.05, f"ann drifted: {ann*100:.3f}%"
    assert abs(sr - 3.820357) < 0.002, f"SR drifted: {sr:.4f}"
    assert abs(mdd * 100 + 3.7339) < 0.02, f"MDD drifted: {mdd*100:.4f}%"
    # gates
    assert gross.max() <= 1.6 + 1e-9, "leverage cap breached"
    assert int((gross > 1.6 + 1e-9).sum()) == 0
    assert to.mean() * 252 * B.BPS <= 8.0, "cost limit breached"
    years = net.groupby(net.index.year).apply(lambda r: (1 + r).prod() - 1)
    assert int((years < 0).sum()) == 0, "negative calendar year"
    is_end = pd.Timestamp("2017-01-01")
    assert _stats(net[net.index >= is_end])[0] >= _stats(net[net.index < is_end])[0], "OOS < IS"


def test_pruning_is_not_a_header_only_change():
    """brwt15's weight must be gone from the emitted book, not merely zeroed downstream."""
    _, relw, _, _, _ = B.build()
    assert "brwt15" not in relw.index
    assert float(relw.sum()) > 0
