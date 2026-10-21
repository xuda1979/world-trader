"""TDD: HUNT_CREDIT2 round-2 stress-gate bug (found live 2026-09-07).

RED condition: stress_gate() must map z>thr -> scale (0.7) and z<=thr -> 1.0. The live run
gated 4602/4805 days (96%) because `.replace(0.0,1.0) * scale` multiplied BOTH states by the
scale, making the "gate" a permanent 0.7x de-gear (champion SR delta meaningless).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import pytest
import HUNT_CREDIT2_round2 as cr2


def _fake_spread(n=1500, seed=5, stress_frac=0.05, spike=3.0):
    """Series that is ~N(2.0, 0.5) with a few extreme spikes so z>2 actually fires."""
    rng = np.random.default_rng(seed)
    s = pd.Series(rng.normal(2.0, 0.5, n), index=pd.bdate_range('2015-01-05', periods=n))
    spike_idx = rng.choice(np.arange(300, n), size=int(n * stress_frac), replace=False)
    s.iloc[spike_idx] = 2.0 + spike * 0.5
    return s


def test_gate_scales_only_stressed_days():
    """z>thr days -> scale; z<=thr days -> 1.0. NOT everything scaled. g is T+1, so compare
    g.shift(-1) (undo the shift) against same-day z."""
    s = _fake_spread()
    monkey = pytest.MonkeyPatch()
    monkey.setattr(cr2, "yld", lambda sid: s)
    g, z = cr2.stress_gate('FAKE', N=252, z_thr=2.0, scale=0.7)
    gs = g.shift(-1)                     # realign: gs_t == gate decided from z_t
    valid = z.dropna().index
    on = gs.loc[valid][z.loc[valid] > 2.0].dropna()
    off = gs.loc[valid][z.loc[valid] <= 2.0].dropna()   # dropna: shift(-1) tail artifact only
    assert len(on) > 0, "test series never fires the gate"
    assert (on == 0.7).all(), f"stressed days not scaled to 0.7: {on.unique()}"
    assert (off == 1.0).all(), f"calm days scaled (leak of the permanent de-gear): {off.unique()}"


def test_gate_fraction_fired_is_small():
    """The gate must be a STRESS regime, not a permanent state: fired fraction << 50%."""
    s = _fake_spread()
    monkey = pytest.MonkeyPatch()
    monkey.setattr(cr2, "yld", lambda sid: s)
    g, z = cr2.stress_gate('FAKE', N=252, z_thr=2.0, scale=0.7)
    fired = float((g < 1.0).mean())
    assert fired < 0.5, f"gate fired {fired*100:.0f}% of days — permanent de-gear, not a gate"


def test_gate_t1_and_warmup_unity():
    """T+1 (shift(1)) and warmup (undefined z) must sit at 1.0, never 0.7. The first warmup
    row (NaN z, index 0) shifts OUT of the frame under shift(1), so check warmup==1.0 on the
    realigned series gs.shift(-1)."""
    s = _fake_spread(n=400)
    monkey = pytest.MonkeyPatch()
    monkey.setattr(cr2, "yld", lambda sid: s)
    g, z = cr2.stress_gate('FAKE', N=252, z_thr=2.0, scale=0.7)
    gs = g.shift(-1)                     # realign to decision date
    warm = z.isna()
    assert (gs[warm].dropna() == 1.0).all(), "warmup days must be 1.0"
    # T+1: gate applied on day t+1 uses z_t. The day AFTER the first defined-z day may be
    # scaled (z could be >thr there); but the first defined-z day itself must be unity.
    first_def = z.dropna().index[0]
    assert gs.loc[first_def] == 1.0, "z at t must not scale day t (T+1 violation)"


def test_gate_z_uses_only_trailing_data():
    """z at t must be invariant to future data (trailing rolling, no centering leak)."""
    s = _fake_spread()
    monkey = pytest.MonkeyPatch()
    monkey.setattr(cr2, "yld", lambda sid: s)
    g_full, z_full = cr2.stress_gate('FAKE', N=252, z_thr=2.0, scale=0.7)
    cut = int(len(s) * 0.7)
    monkey.setattr(cr2, "yld", lambda sid: s.iloc[:cut])
    g_cut, z_cut = cr2.stress_gate('FAKE', N=252, z_thr=2.0, scale=0.7)
    j = pd.concat({'f': z_full, 'c': z_cut}, axis=1).dropna()
    j = j[j.index < s.index[cut]]
    assert np.allclose(j.f, j.c), "z must be trailing-only (prefix-invariant)"


# ---- Round-4 audit addition (2026-09-07): C5 dd() diagnostic bug in gate2 script ----
def _dd_correct(x):
    """Reference max drawdown on daily returns (cumulative wealth = cumprod(1+r))."""
    cp = (1 + x).cumprod()
    return float(1 - (cp / cp.cummax()).min())


def test_gate2_C5_dd_uses_wealth_not_returns():
    """gate2 C5 prints maxDD via a dd() that cumprods the RETURN series itself (a wealth
    decays ~0, sign alternates on negative-return days -> 'maxDD=100.1%' on a champion
    whose true maxDD is -6.69%). Pin the reference definition: on the champion of record
    the correct dd is ~6.69%, and products-of-returns diverges from it."""
    import importlib.util
    ch = cr2.CHAMP.dropna()
    # reference: correct wealth-based dd
    assert abs(_dd_correct(ch) - 0.0669) < 0.01, f"ref dd drifted: {_dd_correct(ch):.4f}"
    # reproduce the buggy expression exactly as shipped in gate2 C5:
    buggy = float(1 - (ch.cumprod() / ch.cumprod().cummax()).min())
    assert buggy > 0.5, (
        "if products-of-returns no longer produce a nonsense dd, the champion series changed "
        "and this bug-pin is stale")
    # and the correct one is much smaller
    assert _dd_correct(ch) < 0.2 < buggy
