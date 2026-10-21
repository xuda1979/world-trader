"""TDD tests for HUNT_CMDT2 round-1 script (campaign/scripts/HUNT_CMDT2_round1.py).
Run: python3 tests_tdd.py -> prints PASS/FAIL per test, nonzero exit on any FAIL.

RED state (2026-09-07): module does not exist yet. Honesty traps encoded BEFORE the
implementation exists, so the engine is built to pass them, not the reverse.
"""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd

SCRIPT = "/Users/daxu/software/world-trader/campaign/scripts/HUNT_CMDT2_round1.py"


def _load():
    import importlib.util
    spec = importlib.util.spec_from_file_location("hcmdt", SCRIPT)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    return H


def test_carry_weights_gross_bounded():
    """Roll-carry proxy target weights must be gross-normalized rank L/S (sum|w| == gross 2.0),
    never raw carry magnitudes. A 40%/yr carry spread must never mean a 40x book."""
    H = _load()
    px = H.px_frame(H.CARRY_ETFS)
    R = px.pct_change()
    S = H.spot_panel(H.CARRY_PAIRS)
    net, We, gross, W = H.run_carry(px, R, S, k=2)
    live = W[(W.fillna(0.0) != 0).any(axis=1)]
    assert len(live) > 500, f"carry book nearly empty ({len(live)} live days)"
    gmax = live.abs().sum(axis=1).max()
    gmean = live.abs().sum(axis=1).mean()
    assert gmax <= 2.0 + 1e-6, f"carry gross exposure {gmax:.2f} > 2.0 (raw carry leaked in)"
    assert abs(gmean - 2.0) < 0.05, f"carry mean gross {gmean:.3f} != 2.0"
    assert live.abs().max().max() <= 2.0 + 1e-6


def test_carry_no_lookahead_truncation():
    """Truncate all inputs at 2015-06-30: target weights through that date must be IDENTICAL
    to the full-sample run. Any divergence = future data in the signal."""
    H = _load()
    px = H.px_frame(H.CARRY_ETFS)
    R = px.pct_change()
    S = H.spot_panel(H.CARRY_PAIRS)
    probe = "2015-06-30"
    _, _, _, W_full = H.run_carry(px, R, S, k=2)
    pxc = px.loc[:probe]
    _, _, _, W_cut = H.run_carry(pxc, pxc.pct_change(), S, k=2)
    a = W_full.loc[:probe].round(10)
    b = W_cut.round(10)
    assert a.equals(b), "carry weights changed when future data removed -> LOOKAHEAD"


def test_fred_spot_publication_lag():
    """The spot leg of the carry proxy must be lagged for FRED monthly publication. Exact
    invariant: for every day t, S[t] == the latest RAW print whose stamp is <= t - lag
    (lag >= 30d). If S[t] ever equals a print stamped <30d before t, mid-month prints leak."""
    H = _load()
    pairs = {'CORN': 'PMAIZMTUSDM'}
    S = H.spot_panel(pairs)
    raw = pd.read_csv(f"{H.ROOT}/tools/quant/data/more_fred/PMAIZMTUSDM.csv",
                      index_col=0, parse_dates=True)['value'].astype(float)
    assert H.SPOT_PUB_LAG_DAYS >= 30
    j = S['CORN'].dropna()
    assert len(j) > 3000, "panel unexpectedly short"
    ts = j.index[::97]                       # deterministic sparse sample over the full history
    checked = 0
    for t in ts:
        cutoff = t - pd.Timedelta(days=H.SPOT_PUB_LAG_DAYS)
        k = raw.index.searchsorted(cutoff, side='right') - 1
        if k < 0:
            continue
        assert abs(raw.iloc[k] - j.loc[t]) <= 1e-9, (
            f"S[{t.date()}] != latest print stamped <= t-{H.SPOT_PUB_LAG_DAYS}d "
            f"(used {raw.index[k].date()} vs got {j.loc[t]}) -> publication leak")
        checked += 1
    assert checked > 50, f"only {checked} days checked"


def test_momentum_hold3_weights_constant_between_rebals():
    """Rank-12m/hold-3m book: target weights may change ONLY on scheduled hold-3 rebalance
    rows (every 3rd month-first day measured from the panel's own start — phase depends on
    data span, so the test derives the rebalance set the same way the engine does, instead of
    assuming calendar quarters). A change on any other day means the hold period is broken
    (or daily leakage). 2026-09-07: GLD history refresh shifted the panel start 2006-10 ->
    2004-11, which rotated the rebalance phase off calendar quarters; the OLD test wrongly
    failed on that (phase assumption), engine hold discipline was intact."""
    H = _load()
    px = H.px_frame(H.CORE9)
    R = px.pct_change()
    _, _, _, W = H.run_momentum(px, R, months=12, topk=3, hold=3)
    idx = W.index
    ms = H.month_first_positions(idx)
    mseq = {p: j for j, p in enumerate(sorted({idx[i].to_period('M') for i in ms}))}
    reb = {i for i in ms if mseq[idx[i].to_period('M')] % 3 == 0}
    changed = []
    for i in range(1, len(W)):
        if not np.allclose(W.iloc[i].fillna(0), W.iloc[i - 1].fillna(0), atol=1e-12):
            changed.append(i)
    bad = [i for i in changed if i not in reb]
    assert not bad, f"{len(bad)} weight changes on non-rebalance days (e.g. {W.index[bad[0]].date()})"
    assert len(reb) >= 20, f"rebalance set suspiciously small ({len(reb)})"


def test_momentum_no_lookahead_truncation():
    """Truncate closes at 2015-06-30 -> momentum target weights through that date identical."""
    H = _load()
    px = H.px_frame(H.CORE9)
    probe = "2015-06-30"
    _, _, _, W_full = H.run_momentum(px, px.pct_change(), months=12, topk=3, hold=3)
    pxc = px.loc[:probe]
    _, _, _, W_cut = H.run_momentum(pxc, pxc.pct_change(), months=12, topk=3, hold=3)
    a = W_full.loc[:probe].round(10)
    b = W_cut.round(10)
    assert a.equals(b), "momentum weights changed when future data removed -> LOOKAHEAD"


def test_evaluate_trims_warmup():
    """SR must be measured from the first live (|We|>0) day, not from series start; CORE9's
    oldest member starts 2006-10 but the 12m signal needs ~1y of warmup."""
    H = _load()
    px = H.px_frame(H.CORE9)
    R = px.pct_change()
    net, We, _, W = H.run_momentum(px, R, months=12, topk=3, hold=3)
    live = We[(We.fillna(0.0) != 0).any(axis=1)]
    trimmed = H.trim_warmup(net, We)
    assert trimmed.index[0] == live.index[0], (
        f"eval starts {trimmed.index[0].date()} but first P&L day is {live.index[0].date()}")


def test_scramble_gate_requires_positive_sr():
    """A book significantly WORSE than random (SR<0, p~0) must FAIL the scramble gate.
    p<=0.05 is only a pass when real SR > 0 (TDD 2026-09-06, carried into this hunt)."""
    H = _load()
    rng = np.random.default_rng(5)
    idx = pd.bdate_range("2012-01-03", periods=750)
    R = pd.DataFrame({"A": rng.normal(0, 0.01, 750), "B": rng.normal(0, 0.01, 750)}, index=idx)
    W = pd.DataFrame({"A": 1.0, "B": -1.0}, index=idx)
    sign = np.sign((W * R).sum(axis=1))
    Rbad = R.mul(-sign, axis=0)
    net, We, _ = H.net_of(W, Rbad, vt=False)
    sr = net.mean() / net.std() * np.sqrt(252)
    assert sr < 0
    res = H.evaluate("adversarial", net, We, Rbad, verbose=False)
    assert res["ok"]["e_scramble"] is False, (
        f"negative-SR book (SR={sr:.2f}, p={res['p']:.3f}) wrongly passed scramble gate")


if __name__ == "__main__":
    tests = [test_carry_weights_gross_bounded,
             test_carry_no_lookahead_truncation,
             test_fred_spot_publication_lag,
             test_momentum_hold3_weights_constant_between_rebals,
             test_momentum_no_lookahead_truncation,
             test_evaluate_trims_warmup,
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
