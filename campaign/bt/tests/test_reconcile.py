"""TDD tests for bt.reconcile."""
import numpy as np, pandas as pd
from bt import reconcile as R


def test_repro_ok_identical():
    a = pd.Series([0.01, -0.02, 0.03], index=pd.date_range('2020-01-01', periods=3, freq='B'))
    assert R.repro_ok(a, a.copy())
    assert not R.repro_ok(a, a * 1.001)


def test_ledgers_reproduce_smoke():
    idx = pd.date_range('2020-01-01', periods=4, freq='B')
    champ = pd.Series([0.01, -0.005, 0.007, 0.0], index=idx)
    # ledger rows summing to the champion daily net exactly
    rows = []
    for i, dt in enumerate(idx):
        rows.append(dict(date=dt, sleeve='x', pnl_contrib=champ.iloc[i], cost_total=0.0))
    led = pd.DataFrame(rows)
    r = R.ledgers_reproduce(led, champ)
    assert r['ok'] is True
    assert r['max_diff'] == 0.0


def test_turnover_reconciles():
    idx = pd.date_range('2020-01-01', periods=3, freq='B')
    pos = pd.DataFrame({'a': [0.0, 0.5, 0.1],
                        'b': [0.0, -0.3, 0.2]}, index=idx)
    # build ledger with qty == |dW| per sleeve
    d = pos.diff().abs()
    rows = []
    for sleeve in pos.columns:
        for i, dt in enumerate(idx):
            q = d.iloc[i][sleeve]
            if q > 0:
                rows.append(dict(date=dt, sleeve=sleeve, qty_notional=q))
    led = pd.DataFrame(rows)
    r = R.turnover_reconciles(led, pos)
    assert r['ok'] is True


def test_max_abs_diff_nan_fails_closed():
    """AUDIT_FWBUGS R2(b) mutation M27: no round-1 test pinned the NaN fail-closed path of
    max_abs_diff, so deleting the NaN->inf guard passed the whole file. A NaN in either
    series makes the comparison unmeasurable -> must return inf (which repro_ok rejects)."""
    idx = pd.date_range('2020-01-01', periods=3, freq='B')
    a = pd.Series([0.01, 0.02, 0.03], index=idx)
    b = pd.Series([0.01, np.nan, 0.03], index=idx)
    d = R.max_abs_diff(a, b)
    assert np.isinf(d), f"NaN in comparison must be inf, got {d}"
    assert not R.repro_ok(a, b), "repro_ok must reject a NaN-poisoned comparison"
