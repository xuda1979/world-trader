"""TDD tests for HUNT_INTERNATIONAL2 round-1 script (campaign/scripts/HUNT_INTL2_round1.py).
Run: python3 tests_tdd.py  -> prints PASS/FAIL per test, nonzero exit on any FAIL.
RED state (2026-09-06): carry weights = raw yield levels (gross ~4.6, not 2.0);
momentum SR evaluated over ~7y of flat-zero warmup rows; scramble gate passes negative-SR books.
"""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd

SCRIPT = "/Users/daxu/software/world-trader/campaign/scripts/HUNT_INTL2_round1.py"


def test_carry_weights_gross_normalized():
    """Carry target weights must be the gross-normalized deviation weights (sum|w| == gross),
    NOT raw yield levels. A 4.5% yield must never mean a 450% position."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("hintl", SCRIPT)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    pxc = H.px_frame(list(H.CARRY.values()))
    Rc = pxc.pct_change()
    net, We, gross, W = H.run_carry(pxc, Rc)
    # gate applies to TARGET weights W (pre vol-target overlay; VT clip <=3.0 is sanctioned)
    live = W[(W != 0).any(axis=1)]
    gmax = live.abs().sum(axis=1).max()
    gmean = live.abs().sum(axis=1).mean()
    assert gmax <= 2.0 * (1 + 1e-6), f"carry gross exposure {gmax:.2f} > gross 2.0 (raw yield levels leaked in)"
    assert abs(gmean - 2.0) < 0.05, f"carry mean gross {gmean:.2f} != 2.0"
    # individual position sizes must be sane too (<= gross, not yield magnitude)
    assert live.abs().max().max() <= 2.0 + 1e-6, f"single position {live.abs().max().max():.2f} > gross"


def test_momentum_eval_excludes_zero_warmup():
    """SR must be measured from the first day the book is live (|W|>0), not from the raw
    series start including years of flat-zero rows (EWT starts 2000, rest 2006-10)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("hintl", SCRIPT)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    px = H.px_frame(H.UNIV)
    R = px.pct_change()
    net, We, gross, W = H.run_momentum(px, R, 12, 3)
    # first P&L day = first nonzero EFFECTIVE weight (T+1 shifted target); the raw series
    # starts ~7y earlier (EWT 2000) so an untrimmed evaluate would dilute SR with zeros.
    live = We[(We.fillna(0.0) != 0).any(axis=1)]
    first_pnl = live.index[0]
    trimmed = H.trim_warmup(net, We)
    assert trimmed.index[0] == first_pnl, (
        f"evaluate series starts {trimmed.index[0].date()} but book first P&L day {first_pnl.date()} "
        f"-> {(trimmed.index < first_pnl).sum()} flat-zero days diluting SR")
    # and it must actually have trimmed something off the raw net series
    assert len(trimmed) < len(net.dropna()), "no warmup trimmed; EWT-2000 rows leaked into eval"


def test_scramble_gate_requires_positive_sr():
    """A book that is significantly WORSE than random (SR<0, p=0.000) must FAIL the scramble
    gate, not pass it. p<=0.05 alone is only meaningful when real SR > 0."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("hintl", SCRIPT)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2010-01-04", periods=750)
    R = pd.DataFrame({"A": rng.normal(0, 0.01, 750), "B": rng.normal(0, 0.01, 750)}, index=idx)
    W = pd.DataFrame({"A": 1.0, "B": -1.0}, index=idx)
    # adversarial: pick weights anti-aligned with returns -> negative SR, tiny p
    sign = np.sign((W * R).sum(axis=1))
    Rbad = R.mul(-sign, axis=0) * 1.0
    net, We, _ = H.net_of(W, Rbad, vt=False)
    sr = net.mean() / net.std() * np.sqrt(252)
    assert sr < 0
    res = H.evaluate("adversarial", net, We, Rbad, verbose=False)
    assert res["ok"]["e_scramble"] is False, (
        f"negative-SR book (SR={sr:.2f}, p={res['p']:.3f}) wrongly passed scramble gate")


if __name__ == "__main__":
    tests = [test_carry_weights_gross_normalized,
             test_momentum_eval_excludes_zero_warmup,
             test_scramble_gate_requires_positive_sr]
    fails = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            fails += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests)-fails}/{len(tests)} green")
    sys.exit(1 if fails else 0)
