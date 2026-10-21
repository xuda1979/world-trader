"""ITER17: causal walk-forward refit of the champion's slot weights.

The champion's weights are fitted ONCE on the IS window (< 2017-01-01) and then held
for 19 years. A book whose covariance/mean structure drifts should refit as evidence
arrives. `wf_relw_frame` does that: at each refit date t it re-runs the SAME
correlation-aware max-Sharpe fit on data strictly before t, and the new weights apply
from t forward. No lookahead by construction -- proven below by perturbing future
returns and asserting past weights do not move.

Selected under the campaign's pre-committed discipline: the refit cadence was chosen
on IS data ONLY (walk-forward from 2011, evaluated 2012-2016; annual won at IS ann
30.496% / SR 3.5765 / MDD -4.6676% / 0 neg yrs), and the OOS/FULL result was revealed
once afterwards. See campaign/agents/chief/coord/ITER17_WALKFORWARD/FINDINGS.md.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402


def _synth(n=1400, seed=7):
    """13-sleeve synthetic frame, ~5.5y, with a covariance break halfway through."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2010-01-04", periods=n, freq="B")
    base = rng.standard_normal((n, len(B.NAMES))) * 0.004
    # second half: brwt5 becomes much noisier -> a correct refit must reweight away from it
    base[n // 2:, B.NAMES.index("brwt5")] *= 6.0
    return pd.DataFrame(base, index=idx, columns=B.NAMES)


def test_walk_forward_weights_are_causal():
    """Weights at t must not move when returns strictly AFTER t are perturbed."""
    df = _synth()
    frame = B.wf_relw_frame(df, step="YS", first="2011-01-03")
    t = pd.Timestamp("2013-06-03")
    shocked = df.copy()
    shocked.loc[shocked.index > t] += 0.05
    frame2 = B.wf_relw_frame(shocked, step="YS", first="2011-01-03")
    a = frame.loc[:t].iloc[-1]
    b = frame2.loc[:t].iloc[-1]
    assert float((a - b).abs().max()) < 1e-12, "future returns leaked into past weights"


def test_walk_forward_actually_refits():
    """The frame must not be a constant copy of the initial fit."""
    df = _synth()
    frame = B.wf_relw_frame(df, step="YS", first="2011-01-03")
    assert frame.index.is_unique
    assert (frame - frame.iloc[0]).abs().max().max() > 1e-6, "no refit ever changed the weights"
    # weights are constant BETWEEN refit dates (a step function, not a daily re-fit)
    n_unique = frame.round(12).drop_duplicates().shape[0]
    assert 1 < n_unique < len(frame) / 10


def test_walk_forward_respects_the_documented_cap():
    df = _synth()
    frame = B.wf_relw_frame(df, step="YS", first="2011-01-03")
    k = len(B.NAMES)
    assert frame.max().max() <= B.W_MAX / k + 1e-9


def _ann(net):
    net = net.dropna()
    return float((1.0 + net).prod() ** (252.0 / len(net)) - 1.0)


def _pool_without_cfx4():
    """(names, paths) with the discredited CFX4 sleeve removed entirely."""
    return ([n for n in B.NAMES if n != "CFX4"],
            {k: v for k, v in B.PATHS.items() if k != "CFX4"})


def _sr(net):
    net = net.dropna()
    return float(net.mean() / net.std(ddof=1) * np.sqrt(252.0))


def test_walkforward_edge_is_attributed_to_cfx4_and_rejected():
    """HONEST NEGATIVE, pinned so it cannot return as a 'new gain'.

    History of this pin:
    * ITER17 (2026-09-13, ann-max book): the refit's +0.389pp ann edge was 100% CFX4
      (the discredited twelvedata vendor feed); it vanished (-0.016pp) without CFX4.
    * ITER19 (ann-max book): on the pruned pool the refit was simply a loss
      (-0.125pp / -0.257pp) -- the negative was unconditional.
    * ITER20 (2026-09-18, Sharpe-max book): re-anchored to the OPERATOR OBJECTIVE. The
      refit's uncapped raw-fit concentration RAISES ann again (+2.51pp with CFX4,
      +2.25pp without -- the gain is now mostly concentration, NOT primarily CFX4),
      but it LOWERS Sharpe on both arms (-0.167 / -0.191). Under the objective that
      defines the champion (Sharpe-max s.t. ann>=20%, gross<=1.6) the refit is a
      strictly worse book, and the champion's CFX4=0 invariant is untouched.
    """
    wf_all, _, _, _, _ = B.build(wf_step=B.WF_STEP_TRIED)
    st_all, _, _, _, _ = B.build(wf_step=None)
    assert _sr(wf_all) - _sr(st_all) < 0, "the WF refit must not beat the static book on SR"

    saved_names, saved_paths = B.NAMES, B.PATHS
    try:
        B.NAMES, B.PATHS = _pool_without_cfx4()
        wf_nc, _, _, _, _ = B.build(wf_step=B.WF_STEP_TRIED)
        st_nc, _, _, _, _ = B.build(wf_step=None)
    finally:
        B.NAMES, B.PATHS = saved_names, saved_paths

    # static book is unchanged by dropping a zero-weight sleeve
    assert abs(_ann(st_nc) - _ann(st_all)) < 1e-9
    # ... and the refit is no better on the objective without CFX4 either
    assert _sr(wf_nc) - _sr(st_nc) < 0, "WF SR edge appeared -- re-examine"
