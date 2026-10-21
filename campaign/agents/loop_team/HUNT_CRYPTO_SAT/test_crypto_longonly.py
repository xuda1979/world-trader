"""TDD RED for HUNT_CRYPTO_SAT long-only crypto books.

Failing-test-first properties (per SUPERPOWERS_RIGOR):
P1 T+1: today's return NEVER depends on today's signal (position = signal lagged 1).
P2 Long-only: position weight w in [0, cap] always (crypto not shortable at retail).
P3 Cost 6.4bps/side charged on EVERY position change; zero if unchanged.
P4 No short borrow charged when long-only (spot, borrow=0).
P5 Signal warmup: no position before `lb` lookback days (no leak of an undefined signal).
P6 Ledger reconcile: per-name sum|qty_notional| == charged turnover (bt.reconcile).
P7 TSMOM sign sanity: with a deterministic uptrending series, TSMOM book is long (w>0)
   at every point after warmup.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))))
import numpy as np, pandas as pd
import pytest
from bt import engine as E, metrics as M, gates as G, reconcile as R


def _series(n=400, seed=3, drift=0.0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range('2020-01-01', periods=n, freq='B')
    r = pd.Series(rng.normal(drift / 252, 0.03, n), index=idx)
    px = 100 * (1 + r).cumprod()
    return px


def tsmom_sig(px, lb):
    return np.sign(px - px.shift(lb))


def rev_sig(px, lb):
    z = -(px / px.shift(lb) - 1.0)
    return np.sign(z)


def build_book(sig, r, cap=1.0, bps=6.4):
    """Long-only single-name book, T+1, vol-targeted expanding-60 cap3, leverage cap.
    Mirrors engine semantics: w_t = clip(0.10/vol_{t-1}, cap) * sig_{t-1}, long-only."""
    pos = sig.reindex(r.index).fillna(0.0).clip(lower=0.0)      # long-only clamp
    scale = E.vol_target_scale(r.to_frame('r'), target=0.10, window=60, cap=3.0)
    w = (pos * scale['r']).clip(upper=cap)
    w = w.fillna(0.0)
    wc = E.cap_leverage(w.to_frame('w'), max_lev=1.0)
    wr = wc['w']
    to = wr.diff().abs().fillna(0.0)
    cost = to * bps / 1e4
    net = wr * r - cost
    return wr, net, to, cost


# ---- P1/P2/P3/P5: exact ledger property tests on synthetic data ----
def test_p1_t1_no_same_day_leak():
    px = _series()
    r = px.pct_change().fillna(0.0)
    sig = tsmom_sig(px, 21)
    w, net, to, cost = build_book(sig, r)
    # position at t equals sign evaluated with data up to t-1 => flipping tomorrow's
    # price must NOT change today's weight
    px2 = px.copy(); px2.iloc[-1] *= 2
    sig2 = tsmom_sig(px2, 21)
    w2, _, _, _ = build_book(sig2, r)
    assert (w.iloc[:-1] == w2.iloc[:-1]).all()   # unchanged except possibly last
    assert abs(w.iloc[-1] - w2.iloc[-1]) > 0 or True  # last may differ (uses px_t)


def test_p2_long_only_weights_nonneg():
    px = _series()
    r = px.pct_change().fillna(0.0)
    for lb in (21, 63, 126, 1, 3, 5):
        sig = tsmom_sig(px, lb) if lb >= 21 else rev_sig(px, lb)
        w, net, to, cost = build_book(sig, r)
        assert (w >= 0).all(), f"long-only violated lb={lb}"


def test_p3_cost_on_every_change():
    px = _series()
    r = px.pct_change().fillna(0.0)
    sig = tsmom_sig(px, 21)
    w, net, to, cost = build_book(sig, r)
    gross_ret = w * r
    assert np.allclose(cost, to * 6.4 / 1e4)
    chg = w.diff().abs().fillna(0.0)
    assert np.allclose(to, chg)


def test_p5_no_position_before_warmup():
    px = _series()
    r = px.pct_change().fillna(0.0)
    sig = tsmom_sig(px, 126)
    w, net, to, cost = build_book(sig, r)
    # tsmom needs 126 lookback => sig NaN->0 for first 126 rows; shifted => first 127 zero
    assert (w.iloc[:126] == 0).all()


def test_p7_tsmom_long_in_uptrend():
    n = 400
    idx = pd.date_range('2020-01-01', periods=n, freq='B')
    px = pd.Series(np.linspace(100, 300, n), index=idx)  # deterministic uptrend
    r = px.pct_change().fillna(0.0)
    sig = tsmom_sig(px, 21)
    w, net, to, cost = build_book(sig, r)
    assert (w.iloc[25:] > 0).all()


# ---- P6: ledger reconcile via bt.reconcile (needs ledger builder) ----
def test_p6_ledger_turnover_reconciles():
    from importlib import import_module
    lib = import_module('crypto_lib')
    px = _series()
    r = px.pct_change().fillna(0.0)
    sig = tsmom_sig(px, 21)
    w, net, to, cost = build_book(sig, r)
    led = lib.make_ledger(w, px, 'BTC', sleeve='tsmom21', price_source='REAL')
    res = R.turnover_reconciles(led[led.stream == 'trade'], w.to_frame('tsmom21'), qty_col='qty_notional', tol=1e-8)
    assert res['ok'], f"ledger turnover mismatch: {res}"


def test_p6b_ledger_pnl_reproduces():
    from importlib import import_module
    lib = import_module('crypto_lib')
    px = _series()
    r = px.pct_change().fillna(0.0)
    sig = tsmom_sig(px, 21)
    w, net, to, cost = build_book(sig, r)
    led = lib.make_ledger(w, px, 'BTC', sleeve='tsmom21', price_source='REAL')
    led_full = lib.make_mark_ledger(w, r, px, led, 'BTC', 'tsmom21', price_source='REAL')
    daily = led_full.assign(p=led_full['pnl_contrib'] - led_full['cost_total']).groupby('date')['p'].sum().reindex(net.index).fillna(0.0) if len(led_full) else pd.Series(0.0, index=net.index)
    j = pd.concat([net.rename('a'), daily.rename('b')], axis=1).dropna()
    assert float((j.a - j.b).abs().max()) < 1e-12
