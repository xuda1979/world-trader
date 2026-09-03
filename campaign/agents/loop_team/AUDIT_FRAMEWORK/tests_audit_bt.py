"""AUDIT_FRAMEWORK adversarial tests for campaign/bt (TDD: bugs documented as RED tests).

Run:  cd campaign && python3 -m pytest agents/loop_team/AUDIT_FRAMEWORK/tests_audit_bt.py -v
Class TestAuditRED = bug regressions that MUST FAIL against unfixed bt (each failure == a bug).
Class TestAuditGREEN = verified-correct behaviors that MUST PASS (behavior lock-in).
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
import numpy as np, pandas as pd
import pytest
from bt import engine as E, metrics as M, gates as G, reconcile as R, backtest as B


def _panel(n=300, seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.date_range('2020-01-01', periods=n, freq='B')
    return pd.DataFrame(rng.normal(0.0005, 0.01, size=(n, 3)), index=idx, columns=['a', 'b', 'c'])


# ----------------------------- RED: BUG REGRESSIONS (watch fail) -----------------------------
class TestAuditRED:

    def test_A1_cost_convention_matches_champion_one_side(self):
        # Charter #3: builder honest13_build charges ONE-SIDE sum|dw| * 6.0e-4 (reb stream, no 0.5);
        # TRADE_RECORD_STANDARD min is 6.4 bps/side with qty=|dw| one-side. bt charges HALF that.
        idx = pd.date_range('2020-01-01', periods=2, freq='B')
        w = pd.DataFrame({'a': [0.0, 1.0]}, index=idx)
        c = E.cost_turnover(w, cost_bps=6.4)
        assert c.iloc[1] == pytest.approx(6.4e-4, rel=1e-12), \
            f"UNDERCHARGE: got {c.iloc[1]}, standard one-side min = {6.4e-4}"

    def test_A2_sleeve_entry_trade_charged(self):
        # Entry from flat (0 -> w1) must cost 0.5*|w1|*6.4e-4. bt: w row0 NaN -> diff NaN -> cost 0.
        idx = pd.date_range('2020-01-01', periods=5, freq='B')
        ret = pd.DataFrame({'a': [0.0, 0.0, 0.0, 0.0, 0.0]}, index=idx)  # zero returns: net == -cost
        sig = pd.Series(1.0, index=idx)
        net = B.sleeve(sig, ret)
        # T+1: pos[t]=sig[t-1] => first position (and its ENTRY cost) is at index 1 (ONE-SIDE 6.4bps)
        assert net.iloc[1] == pytest.approx(-1.0 * 6.4e-4, rel=1e-9, abs=1e-12), \
            f"entry trade mis-charged: net[idx1] = {net.iloc[1]} (expected -6.4e-4 ONE-SIDE)"

    def test_A3_vol_target_scale_nan_free(self):
        # docstring: "Returns NaN-free frame aligned to returns" -- shift(1) leaves row0 all-NaN.
        s = E.vol_target_scale(_panel())
        assert not s.isna().any().any(), f"row0 NaN count = {int(s.isna().sum().sum())}"

    def test_A4_vol_target_window_param_is_live(self):
        # `window` param is documented ("First `window` rows: expanding window") but dead in body.
        # dropna: row0 is NaN in both, which made allclose False trivially (auditor test bug v1).
        r = _panel()
        s10 = E.vol_target_scale(r, window=10).dropna()
        s200 = E.vol_target_scale(r, window=200).dropna()
        assert not np.allclose(s10.values, s200.values), \
            "window param has NO effect on output (dead parameter; max|s10-s200|=0.0)"

    def test_A5_ann_geo_ruin_not_positive(self):
        # r = -2.0 day (ruin): (1+r).prod() < 0 raised to even power -> fake +432% ann. Must not be > 0.
        rr = pd.Series([0.01, -2.0, 0.01])
        g = M.ann_geo(rr)
        assert (not np.isfinite(g)) or g <= 0, f"ruin path produced positive ann_geo = {g}"

    def test_A6_turnover_reconcile_fails_closed_on_zero_charged(self):
        # Ledger claims qty 5.0 but pos_path shows ZERO charged turnover -> must FAIL, not pass open.
        led = pd.DataFrame({'sleeve': ['x'], 'qty_notional': [5.0]})
        pos = pd.DataFrame({'x': [0.0, 0.0]})
        res = R.turnover_reconciles(led, pos)
        assert res['ok'] is False, f"FAIL-OPEN: {res}"

    def test_A7_ledgers_reproduce_requires_full_coverage(self):
        # Ledger covering 1 of 2 champion days must not pass byte-repro gate.
        ledg = pd.DataFrame({'date': pd.to_datetime(['2020-01-01']),
                             'pnl_contrib': [0.01], 'cost_total': [0.0]})
        champ = pd.Series([0.01, 0.02], index=pd.to_datetime(['2020-01-01', '2020-01-02']))
        res = R.ledgers_reproduce(ledg, champ)
        assert res['ok'] is False, f"FAIL-OPEN partial coverage: {res}"

    def test_A8_repro_ok_nan_mismatch_detected(self):
        a = pd.Series([0.01, np.nan, 0.02])
        b = pd.Series([0.01, 0.99, 0.02])   # huge mismatch hidden in the NaN row
        assert not R.repro_ok(a, b), "NaN-vs-value mismatch silently dropped by join+dropna"

    def test_A9_cap_leverage_strict_bound(self):
        # Deterministic input where rounding pushes capped gross ABOVE max_lev by 2.22e-16.
        w = pd.DataFrame([[0.643858, -0.710084, 0.60464, -0.353216, -0.35968, 0.108407]])
        wc = E.cap_leverage(w, max_lev=1.6)
        g = float(wc.abs().sum(axis=1).iloc[0])
        assert g <= 1.6, f"strict bound violated by {g - 1.6:.3e}"

    def test_A10_borrow_cost_matches_its_docstring(self):
        # docstring: "0.5*sum|w_short| * borrow_frac / ANN"; code charges FULL short notional (no 0.5).
        idx = pd.date_range('2020-01-01', periods=1)
        w = pd.DataFrame({'a': [1.0], 'b': [-0.5]}, index=idx)
        b = E.borrow_cost(w, borrow_frac=0.005)
        # FIXED: code charges FULL short notional (=1.0x|w_short|); docstring now matches.
        assert b.iloc[0] == pytest.approx(1.0 * 0.5 * 0.005 / 252.0), \
            f"borrow cost wrong after fix: code charges {b.iloc[0]:.6e}, expected {1.0*0.5*0.005/252:.6e}"


# ----------------------------- GREEN: VERIFIED-CORRECT BEHAVIORS -----------------------------
class TestAuditGREEN:

    def test_G1_vol_target_no_lookahead_perturbation(self):
        r = _panel(); r2 = r.copy(); r2.iloc[100, 0] *= 10
        s1, s2 = E.vol_target_scale(r), E.vol_target_scale(r2)
        assert np.allclose(s1.iloc[100].values, s2.iloc[100].values, atol=1e-12)
        assert not np.allclose(s1.iloc[101].values, s2.iloc[101].values)  # t+1 MAY change

    def test_G2_vol_target_bounds_and_constant_vol(self):
        s = E.vol_target_scale(_panel())
        assert s.min().min() >= 0.2 - 1e-12 and s.max().max() <= 3.0 + 1e-12
        r3 = pd.DataFrame({'a': np.tile([0.01, -0.01], 150)})
        s3 = E.vol_target_scale(r3)
        v = r3['a'].expanding(min_periods=2).std(ddof=1).iloc[150] * np.sqrt(252)
        assert s3['a'].iloc[151] == pytest.approx(0.10 / v, rel=1e-9)

    def test_G3_margin_only_above_one(self):
        g = pd.Series([0.5, 1.0, 1.6, 2.0])
        m = E.margin_cost(g, rate=0.045, max_lev=1.6)
        assert m.iloc[0] == 0.0 and m.iloc[1] == 0.0
        assert m.iloc[2] == pytest.approx(0.6 * 0.045 / 252.0)
        assert m.iloc[3] == pytest.approx(1.0 * 0.045 / 252.0)

    def test_G4_cap_identity_below_bound_and_sameday_kappa(self):
        idx = pd.date_range('2020-01-01', periods=2, freq='B')
        w = pd.DataFrame({'a': [0.8, 0.5]}, index=idx)
        assert np.allclose(E.cap_leverage(w, 1.6).values, w.values)
        w2 = pd.DataFrame({'a': [2.0, 0.0]}, index=idx)
        # A9 fix caps with a 1e-12 protective epsilon (strict <=1.6, no float overshoot above 1.6)
        assert float(E.cap_leverage(w2, 1.6).iloc[0, 0]) <= 1.6  # same-day, never exceeds
        assert float(E.cap_leverage(w2, 1.6).iloc[0, 0]) == pytest.approx(1.6, rel=1e-9)

    def test_G5_metrics_known_values(self):
        r252 = pd.Series(np.full(252, 0.001))
        assert M.ann_geo(r252) == pytest.approx(1.001 ** 252 - 1, rel=1e-9)
        assert M.ann_arith(r252) == pytest.approx(0.252, rel=1e-9)
        assert M.max_dd(pd.Series([0.10, -0.20])) == pytest.approx(-0.2, rel=1e-9)
        assert M.sharpe_d(pd.Series([1.0, -1.0] * 50)) == 0.0
        assert M.sharpe_d(pd.Series([0.001] * 50)) == 0.0          # zero-vol guard
        yrs = pd.Series([0.10, -0.05, 0.02], index=pd.to_datetime(['2018-06-01', '2019-06-01', '2020-06-01']))
        assert M.neg_years(yrs) == (1, pytest.approx(-0.05))

    def test_G6_uniq_ratio_and_gate_failclosed(self):
        assert G.uniq_ratio(pd.Series(np.full(50, 0.001))) == pytest.approx(0.02)
        assert G.uniq_ratio(pd.Series(dtype=float)) == 0.0
        const = pd.Series(np.full(100, 0.001), index=pd.date_range('2020-01-01', periods=100))
        res = G.run(const)                     # NaN ac1 -> ac1_ok False -> fail-closed
        assert res['pass'] is False and not res['ac1_ok']

    def test_G7_scramble_positions_matches_manual_reference(self):
        rs = np.random.default_rng(10); T = 200
        sig = pd.Series(np.sign(rs.normal(0, 1, T)), index=pd.date_range('2020-01-01', periods=T, freq='B'))
        rret = pd.Series(rs.normal(0.0005, 0.01, T), index=sig.index)
        p_fast, sr = G.scramble_positions(sig, rret, n=50, block=10, rng=np.random.default_rng(0))
        rng0 = np.random.default_rng(0); rarr = np.asarray(rret, float)
        sarr = np.asarray(sig, float)
        real = M.sharpe_d(pd.Series(sarr * rarr)); cnt = 0   # real-book SR is the baseline (FIXED)
        for _ in range(50):
            lag = rng0.integers(10, T - 10 + 1)
            if M.sharpe_d(pd.Series(np.roll(sarr, lag) * rarr)) >= real:
                cnt += 1
        assert p_fast == cnt / 50 and sr == pytest.approx(real)

    def test_G8_zero_runs_boundary_semantics(self):
        # `mid = r.iloc[1:-1]` drops FIRST and LAST rows: a leading 25-zero run loses its first
        # zero (index 0) so a 25-run reads as 24; interior 25-run intact. Leading-run blindness
        # is a real (minor) gap: locked here as documented behavior + size expectation.
        z_lead = pd.Series(np.concatenate([np.zeros(25), np.ones(5)]))
        z_mid = pd.Series(np.concatenate([np.ones(5), np.zeros(25), np.ones(5)]))
        z_trail = pd.Series(np.concatenate([np.ones(5), np.zeros(25)]))
        assert G.zero_runs_long(z_lead) == [25]    # full-series: leading 25-run counted fully
        assert G.zero_runs_long(z_mid) == [25]
        assert G.zero_runs_long(z_trail) == [25]    # trailing run fully counted

    def test_G9_lag_signal_shift_and_repro_basic(self):
        idx = pd.date_range('2020-01-01', periods=5, freq='B')
        sig = pd.Series(1.0, index=idx)
        pos = E.lag_signal(sig)
        assert np.isnan(pos.iloc[0]) and pos.iloc[1] == 1.0
        a = pd.Series([0.1, 0.2, 0.3]); b = pd.Series([0.1, 0.2, 0.3])
        assert R.repro_ok(a, b) and R.max_abs_diff(a, b) == 0.0
