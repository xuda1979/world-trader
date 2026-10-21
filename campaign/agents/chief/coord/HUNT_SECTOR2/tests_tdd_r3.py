#!/usr/bin/env python3
"""HUNT_SECTOR2 round-3 TDD tests (written RED first, then hunt_sector2_r3.py).
Run: python3 -m pytest tests_tdd_r3.py -q

Blend accounting convention (T+1-honest): allocations drift through close t; the
rebalancing trade decided at close t is held from day t+1, so the drift through close t
is charged ON day t+1. Entry (bought at close -1) is charged on day 0."""
import sys

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign/scripts")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2")


def test_blend_split_identical_legs_no_double_count():
    """Two identical constant-return sleeves at 50/50: legs are self-financing, so the
    only charges are day-0 entry (turnover 1.0) and allocation-drift rebalancing (zero
    here, identical legs never drift apart). Sleeve-internal turnover must NOT be
    re-charged (it is already inside the published net series)."""
    import pandas as pd
    from hunt_sector2_r3 import blend_split
    idx = pd.date_range("2020-01-01", periods=4)
    r = pd.Series([0.0, 0.01, 0.01, 0.01], index=idx)
    net, to = blend_split(r, r.copy(), 0.5, rebal="daily")
    assert abs(to.iloc[0] - 1.0) < 1e-12                      # entry = full notional
    assert abs(net.iloc[0] - (0.0 - 1.0 * 6.4 / 1e4)) < 1e-12
    for t in (1, 2, 3):
        assert abs(to.iloc[t]) < 1e-12                        # no drift between twins
        assert abs(net.iloc[t] - 0.01) < 1e-12                # 0.5*0.01+0.5*0.01


def test_blend_split_asymmetric_drift_charged_tplus1():
    """A +1% while B flat: the A allocation drifts up through close 1; the rebalance
    decided at close 1 is charged on day 2 (T+1). Exact penny check on both days."""
    import pandas as pd
    from hunt_sector2_r3 import blend_split
    idx = pd.date_range("2020-01-01", periods=3)
    a = pd.Series([0.0, 0.01, 0.01], index=idx)
    b = pd.Series([0.0, 0.0, 0.0], index=idx)
    net, to = blend_split(a, b, 0.5, rebal="daily")
    assert abs(to.iloc[1]) < 1e-12                    # close-0 allocs still 50/50
    assert abs(net.iloc[1] - 0.5 * 0.01) < 1e-12      # 0.5*1% + 0.5*0%
    # close-1 allocs: (.5*1.01, .5)/1.005 -> alloc_a = 0.502488; trade back to 50/50
    assert abs(to.iloc[2] - 2 * abs(0.5 - 0.5 * 1.01 / 1.005)) < 1e-12
    # day-2 book return uses the POST-TRADE 50/50 split (trade held from day 2)
    assert abs(net.iloc[2] - (0.5 * 0.01 - to.iloc[2] * 6.4 / 1e4)) < 1e-12


def test_blend_split_monthly_and_never_no_rebal_charge():
    """rebal='never' charges entry only; 'monthly' charges entry + one trade at the
    first session of each new month. Under drift the two are DIFFERENT portfolios, so
    gross parity is only asserted up to the first rebalance."""
    import pandas as pd
    from hunt_sector2_r3 import blend_split
    idx = pd.bdate_range("2020-01-01", periods=40)     # spans Jan into Feb
    a = pd.Series(0.004, index=idx)
    b = pd.Series(0.001, index=idx)
    net0, to0 = blend_split(a, b, 0.5, rebal="never")
    assert abs(to0.sum() - 1.0) < 1e-12                # never = entry only, no trades
    netm, tom = blend_split(a, b, 0.5, rebal="monthly")
    feb1 = [d for d in idx if d.month == 2][0]
    charged = tom[tom > 1e-12].index
    assert list(charged) == [idx[0], feb1]             # entry + first-Feb-session
    k = idx.get_loc(feb1)                              # identical book up to the trade
    assert abs(net0.iloc[:k].sum() - netm.iloc[:k].sum()) < 1e-12
    assert tom.iloc[k] > 0                             # the Feb trade is charged in Feb


def test_invvol_weights_trailing_only():
    """Inverse-vol blend weights at t must use returns <= t-1 (T+1): perturbing B at t
    leaves w[:t+1] identical and moves w only at t+1."""
    import numpy as np, pandas as pd
    from hunt_sector2_r3 import invvol_weights
    rng = np.random.default_rng(0)
    idx = pd.date_range("2015-01-01", periods=300)
    a = pd.Series(rng.normal(0.0003, 0.01, 300), index=idx)
    b = pd.Series(rng.normal(0.0002, 0.008, 300), index=idx)
    w1 = invvol_weights(a, b, lookback=60)
    b2 = b.copy(); b2.iloc[150] += 5.0
    w2 = invvol_weights(a, b2, lookback=60)
    d1 = (w1.iloc[:151] - w2.iloc[:151]).abs().to_numpy()
    assert float(np.nanmax(d1)) == 0.0        # leading lookback NaNs are by design
    d2 = (w1.iloc[151] - w2.iloc[151]).abs().to_numpy()
    assert float(np.nanmax(d2)) > 0.0
    d = w1.dropna()
    assert bool((d >= 0).all().all()) and bool((d <= 1).all().all())
    assert bool(((d.sum(axis=1) - 1).abs() < 1e-9).all())


def test_composite_window_is_exact_overlap():
    """The composite book must span the published sleeves' overlap grid EXACTLY - no
    dropped rows (the R2 truncation bug class)."""
    import numpy as np, pandas as pd
    from hunt_sector2_r3 import blend_split
    idx = pd.bdate_range("2018-06-20", periods=500)
    a = pd.Series(np.random.default_rng(1).normal(0.0003, 0.007, 500), index=idx)
    b = pd.Series(np.random.default_rng(2).normal(0.0002, 0.006, 500), index=idx)
    net, to = blend_split(a, b, 0.5, rebal="daily")
    assert (net.index == idx).all() and len(net) == 500


def test_control_matched_random_rejects_pure_drift():
    """HUNT_VOL2-charter-style adversarial control: a corr-and-vol-matched ZERO-MEAN
    random leg must NOT reliably beat leg B's slot. If the composite's edge were pure
    diversification-of-noise, the random control would clear it ~50% of the time."""
    import numpy as np, pandas as pd
    from hunt_sector2_r3 import random_control_p
    rng = np.random.default_rng(5)
    idx = pd.bdate_range("2020-01-01", periods=600)
    a = pd.Series(rng.normal(4e-4, 7e-3, 600), index=idx)   # positive drift leg
    b = pd.Series(rng.normal(3e-4, 6e-3, 600), index=idx)   # the slot in question
    p = random_control_p(a, b, n=100, seed=0)
    assert 0.0 <= p <= 1.0
    # true positive drift in A -> the composite with A beats corr-matched noise <50%
    assert p < 0.5


def test_control_matched_random_passes_when_leg_is_pure_noise():
    """Symmetric check: if leg B itself is zero-mean noise, the control clears it ~50%
    (the control is calibrated, not rigged to pass or fail)."""
    import numpy as np, pandas as pd
    from hunt_sector2_r3 import random_control_p
    rng = np.random.default_rng(6)
    idx = pd.bdate_range("2020-01-01", periods=600)
    a = pd.Series(rng.normal(4e-4, 7e-3, 600), index=idx)
    b = pd.Series(rng.normal(0.0, 6e-3, 600), index=idx)    # zero-mean slot
    p = random_control_p(a, b, n=100, seed=0)
    assert 0.25 < p < 0.75


# ---------------------------------------------------------------------------
# ROUND-3 session-2 TDD (RED first): blend_dynamic accepts a RETURNS pair, not a
# precomputed weight frame. The prior session's bug: invvol_weights() output was
# passed as `wa`, and blend_dynamic cumprod'ed ~0.5/day "returns" into overflow
# (SR 48.9, ann 5228%, yearly ~e+25) -> garbage PASS artifact on disk.
# ---------------------------------------------------------------------------

def test_blend_dynamic_takes_return_series_not_weights():
    """blend_dynamic must be fed RETURN series for both legs. Feeding a weight frame
    (rows ~0.5/0.5) must fail loudly, not overflow into SR~49 / ann~5228%."""
    import numpy as np, pandas as pd, pytest
    from hunt_sector2_r3 import blend_dynamic, invvol_weights
    rng = np.random.default_rng(7)
    idx = pd.bdate_range("2020-01-01", periods=400)
    a = pd.Series(rng.normal(3e-4, 7e-3, 400), index=idx)
    b = pd.Series(rng.normal(2e-4, 6e-3, 400), index=idx)
    w = invvol_weights(a, b, lookback=60).dropna()      # weights, not returns
    with pytest.raises((AssertionError, ValueError)):
        blend_dynamic(w, rebal="monthly")
    # correct usage: returns -> finite, sane book (|ret| <= ~ clip * leg vol)
    net, to = blend_dynamic(pd.concat({"a": a, "b": b}, axis=1), rebal="monthly")
    assert net.notna().all() and np.isfinite(net).all()
    assert float(net.abs().max()) < 0.20
    assert 0.0 <= float(to.max()) <= 2.0


def test_blend_dynamic_monthly_rebalance_matches_blend_split_at_constant_w():
    """Sanity anchor: with a CONSTANT target weight the dynamic path must reproduce
    blend_split's turnover schedule (entry + month-end trades) and identical net."""
    import numpy as np, pandas as pd
    from hunt_sector2_r3 import blend_split, blend_dynamic
    rng = np.random.default_rng(8)
    idx = pd.bdate_range("2020-01-01", periods=400)
    a = pd.Series(rng.normal(3e-4, 7e-3, 400), index=idx)
    b = pd.Series(rng.normal(2e-4, 6e-3, 400), index=idx)
    net0, to0 = blend_split(a, b, 0.5, rebal="monthly")
    netd, tod = blend_dynamic(pd.concat({"a": a, "b": b}, axis=1), rebal="monthly",
                              w_const=0.5)
    assert (tod.index == to0.index).all()
    assert float((tod - to0).abs().max()) < 1e-12       # same trade schedule
    assert float((netd - net0).abs().max()) < 1e-12     # identical book


def test_blend_dynamic_output_guards():
    """Fail-closed: non-finite net -> AssertionError; turnover bounded, finite book."""
    import numpy as np, pandas as pd
    from hunt_sector2_r3 import blend_dynamic
    rng = np.random.default_rng(9)
    idx = pd.bdate_range("2020-01-01", periods=300)
    a = pd.Series(rng.normal(3e-4, 7e-3, 300), index=idx)
    b = pd.Series(rng.normal(2e-4, 6e-3, 300), index=idx)
    net, to = blend_dynamic(pd.concat({"a": a, "b": b}, axis=1), rebal="monthly")
    assert np.isfinite(net.values).all()
    assert (to >= -1e-12).all() and (to <= 2.0 + 1e-9).all()


# ---------------------------------------------------------------------------
# ROUND-3 session-3 TDD (RED first): two more defects in the dead session's
# gates_r3 block. (i) vt_apply vol-targeted rets.sum(axis=1) = the 2x-GROSS
# sum of leg returns, so the composite ran at ~5% realized vol vs the 10%
# target (halving the book's risk budget; SR mis-stated). (ii) the scramble
# gate ran the degenerate constant-split permutation (p==1.0 by construction)
# and stamped FAIL_SCRAMBLE_DEGENERATE on every verdict; the informative
# control is random_control_p (corr/vol-matched zero-mean leg in B's slot).
# ---------------------------------------------------------------------------

def test_vt_apply_targets_the_composite_book():
    """vt_apply must vol-target the ACTUAL composite book (weighted legs), not the
    2x-gross sum. a = +-1% alternating (ann vol 15.9%), b = flat -> 50/50 book vol
    is 7.9%, so VT10 must scale UP to ~10%, not down to ~5%."""
    import numpy as np, pandas as pd
    from hunt_sector2_r3 import vt_apply
    idx = pd.bdate_range("2015-01-01", periods=750)
    a = pd.Series([0.01 if i % 2 == 0 else -0.01 for i in range(750)], index=idx)
    b = pd.Series(0.0, index=idx)
    net_raw = 0.5 * a + 0.5 * b                      # pre-VT composite book
    rets = pd.concat({"a": a, "b": b}, axis=1)
    net = vt_apply(net_raw, rets)
    v = float(net.iloc[60:].std(ddof=1) * np.sqrt(252))
    assert 0.09 <= v <= 0.11, f"composite VT vol {v:.3f} not ~10% (2x-gross bug)"


def test_gates_r3_scramble_gate_rejects_a_noise_leg():
    """gates_r3's scramble gate must be the informative random_control_p: a composite
    whose B leg is corr/vol-matched ZERO-MEAN noise must FAIL_SCRAMBLE (p >= 0.05);
    it cannot pass on diversification of noise alone."""
    import numpy as np, pandas as pd
    import hunt_sector2_r3 as R
    rng = np.random.default_rng(11)
    idx = pd.bdate_range("2018-06-20", periods=1200)
    a = pd.Series(rng.normal(4e-4, 7e-3, 1200), index=idx)   # genuine drift leg
    b = pd.Series(rng.normal(0.0, 6e-3, 1200), index=idx)    # pure-noise slot
    g = R.gates_r3("T_NOISELEG", 0.5 * a + 0.5 * b,
                   pd.concat({"a": a, "b": b}, axis=1), save=False)
    assert "FAIL_SCRAMBLE" in g["verdict"], f"noise leg not rejected: {g['verdict']}"


def test_gates_r3_scramble_gate_passes_genuine_legs():
    """Complement: a composite of two GENUINE drift legs must NOT be stamped
    FAIL_SCRAMBLE. The dead session's degenerate constant-split permutation returned
    p=0.4 and stamped it on every real composite (see COMP_50_50_daily.csv.meta)."""
    import numpy as np, pandas as pd
    import hunt_sector2_r3 as R
    rng = np.random.default_rng(12)
    idx = pd.bdate_range("2018-06-20", periods=1200)
    a = pd.Series(rng.normal(4e-4, 7e-3, 1200), index=idx)
    b = pd.Series(rng.normal(3e-4, 6e-3, 1200), index=idx)
    g = R.gates_r3("T_GENUINE", 0.5 * a + 0.5 * b,
                   pd.concat({"a": a, "b": b}, axis=1), save=False)
    assert "FAIL_SCRAMBLE" not in g["verdict"], f"genuine legs flagged: {g['verdict']}"


def test_invvol_warmup_extension_covers_full_window():
    """invvol_weights() has a 63d trailing NaN warm-up, so blend_dynamic's fail-closed
    cover-guard rejects the A11/B overlap window. The R3 engine must expose
    invvol_blend_weights(): the raw weights with the FIRST computable trailing-63d
    weight extended back over the warm-up (a documented convention, not a new fitted
    param -- the sleeves themselves start 2018-06-20, i.e. the published nets already
    embed 126d of prior data). Guards: extension constant, full coverage, in [0,1]."""
    import numpy as np, pandas as pd, pytest
    import hunt_sector2_r3 as R
    rng = np.random.default_rng(7)
    idx = pd.bdate_range("2018-06-20", periods=300)
    a = pd.Series(rng.normal(2e-4, 6e-3, 300), index=idx)
    b = pd.Series(rng.normal(2e-4, 5e-3, 300), index=idx)
    wa = R.invvol_blend_weights(a, b, lookback=63)["a"]
    assert len(wa) == 300 and wa.notna().all(), "must cover the full window"
    raw = R.invvol_weights(a, b, lookback=63)["a"]
    ext = wa.iloc[:63]
    assert (ext == raw.iloc[63]).all(), "extension must be constant = first computable w"
    assert (wa.iloc[63:] == raw.iloc[63:]).all(), "post-warm-up weights must be untouched"
    assert wa.between(0, 1).all()
    net, to = R.blend_dynamic(pd.concat({"a": a, "b": b}, axis=1), rebal="monthly", wa=wa)
    assert len(net) == 300 and np.isfinite(net.values).all()
