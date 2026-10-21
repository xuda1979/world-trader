"""TDD for champ_tier_delta REALISTIC semantics (RED first).

REALISTIC treatment must re-price ONLY slots whose base rate is explicitly given
(the stock-loan slots). A slot absent from base_rate is UNTOUCHED (delta 0) — the
committed generator's own borrow treatment stands. Passing {n:0.0 for all} is the
BOUND treatment. The old .get(n, 0.0) default silently turned REALISTIC into BOUND.
"""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/CAMP_SHORT/work_r2")
from champ_short import champ_tier_delta


def _W():
    idx = pd.date_range("2020-01-01", periods=4)
    return pd.DataFrame({"stockloan_slot": [-0.4] * 4, "fut_slot": [-0.6] * 4}, index=idx)


def _expo():
    idx = pd.date_range("2020-01-01", periods=4)
    return {"stockloan_slot": pd.Series(1.0, index=idx),
            "fut_slot": pd.Series(1.0, index=idx)}


def test_realistic_leaves_unlisted_slots_untouched():
    d = champ_tier_delta(_W(), _expo(), {"stockloan_slot": 0.005}, 0.08)
    exp = 0.4 * (0.08 - 0.005) / 252.0   # ONLY the stockloan slot, from its true base
    assert np.allclose(d, exp), (
        f"REALISTIC must re-price only listed slots: got {d.iloc[0]:.3e} want {exp:.3e}")


def test_bound_covers_every_slot_when_base_zero_given():
    W, E = _W(), _expo()
    d = champ_tier_delta(W, E, {n: 0.0 for n in W.columns}, 0.08)
    exp = 1.0 * (0.08 - 0.0) / 252.0
    assert np.allclose(d, exp), "all-zero base must re-price every slot (BOUND)"


def test_negative_delta_is_a_credit_not_clipped():
    d = champ_tier_delta(_W(), _expo(), {"stockloan_slot": 0.02}, 0.005)
    assert (d < 0).any(), "cheaper tier must produce a (negative) credit"
