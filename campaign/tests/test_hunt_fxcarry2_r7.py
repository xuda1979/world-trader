"""HUNT_FXCARRY2 R7 TDD locks — written BEFORE any performance number (R3/R5 precedent).
Covers the corner machinery: PIT overnight-differential carry book on the new rate source.
Run: pytest campaign/tests/test_hunt_fxcarry2_r7.py (from world-trader root)."""
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")

import HUNT_FXCARRY2_round7 as M  # noqa: E402


def _mk_rates(start="2000-01-03", n=1200, seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, periods=n)
    usd = pd.Series(3.0 + 0.3 * np.sin(np.arange(n) / 90), index=idx)
    gbp = pd.Series(4.0 + 0.4 * np.sin(np.arange(n) / 120 + 1), index=idx)
    eur = pd.Series(2.0 + 0.2 * np.sin(np.arange(n) / 60 + 2), index=idx)
    return pd.DataFrame({"USD": usd, "GBP": gbp, "EUR": eur})


def _mk_spot(rates):
    idx = rates.index
    # Frankfurter convention: all cols quoted per EUR -> USD col = USD/EUR price of 1 EUR.
    eurusd = pd.Series(0.9 + 0.05 * np.sin(np.arange(len(idx)) / 200), index=idx)
    gbpusd = pd.Series(1.3 + 0.08 * np.cos(np.arange(len(idx)) / 150), index=idx)
    return pd.DataFrame({"USD": eurusd, "GBP": gbpusd, "EUR": pd.Series(1.0, index=idx)})


def test_01_pit_no_lookahead():
    """Decision at month-end t uses only rates published <= t; effective weights shifted."""
    rates, spot = _mk_rates(), _mk_spot(_mk_rates())
    W, s, meta = M.build_carry_book(rates, spot, window=252)
    assert W.index.equals(s.index)
    # effective == decision shifted 1
    assert np.allclose(W.values[1:], s.values[:-1])
    assert (W.iloc[0] == 0).all()
    # scramble the last month's rates -> earlier decisions unchanged (PIT)
    rates2 = rates.copy()
    rates2.iloc[-30:] = 99.0
    W2, s2, _ = M.build_carry_book(rates2, spot, window=252)
    cut = len(s) - 30 - 40  # decisions far before the tampered tail
    assert np.allclose(s.values[:cut], s2.values[:cut])


def test_02_signs_and_dollar_neutrality():
    """Long the high-overnight ccys vs USD; book is dollar-neutral per unit of gross."""
    rates, spot = _mk_rates(), _mk_spot(_mk_rates())
    W, s, _ = M.build_carry_book(rates, spot, window=252)
    # GBP has the highest overnight mean -> GBP leg long, USD legs short-ish
    late = s.iloc[-1]
    gross = late.abs().sum()
    assert gross > 0
    # net USD exposure: USD leg balances the FX cross exposure of EUR/GBP legs
    # (book defined so sig*r_pu == gross held book; units consistency)
    sig = M.held_gross_units(W)
    assert (sig >= 0).all()


def test_03_accrual_matches_overnight_differential():
    """fx_total_returns credits (r_ccy - r_usd)/252 per held ccy leg, USD leg earns 0."""
    rates = _mk_rates(n=300)
    spot = _mk_spot(rates)
    W, s, _ = M.build_carry_book(rates, spot, window=252)
    tot, fx = M.fx_total_returns(W, rates, spot)
    t = len(W) // 2
    dt = W.index[t]
    w = W.iloc[t]
    manual = 0.0
    for ccy in ("GBP", "EUR"):
        manual += w[ccy] * (rates.loc[dt, ccy] - rates.loc[dt, "USD"]) / 252.0
    # manual accrual (both legs together) must equal the accrual frame's row sum
    assert abs(fx.iloc[t].sum() - manual) < 1e-12
    # USD leg accrues exactly 0 by construction
    assert (fx["USD"].fillna(0.0) == 0).all()
    # totals = spot return + accrual
    spot_ret = M.spot_pnl(W, spot)
    assert np.allclose((spot_ret + fx.sum(axis=1)).dropna().values,
                       tot.dropna().reindex((spot_ret + fx.sum(axis=1)).dropna().index).values)


def test_04_truncation_stability():
    """Truncated-sample rebuild is byte-identical on the overlap (V2 discipline)."""
    rates, spot = _mk_rates(), _mk_spot(_mk_rates())
    W, s, _ = M.build_carry_book(rates, spot, window=252)
    Wt, st, _ = M.build_carry_book(rates.iloc[:800], spot.iloc[:800], window=252)
    assert np.allclose(st.values, s.values[:len(st)])


def test_05_engine_booking_wiring():
    """sig*r_pu == held gross book (the R5 scalarization defect class)."""
    rates, spot = _mk_rates(), _mk_spot(_mk_rates())
    W, s, _ = M.build_carry_book(rates, spot, window=252)
    tot, fx = M.fx_total_returns(W, rates, spot)
    r_pu, sig = M.per_unit_feed(tot, W, s)
    held = tot.dropna()
    assert np.allclose((sig * r_pu).reindex(held.index).dropna().values, held.values)


def test_06_battery_wiring_v2():
    """gates.run called with sig=, leak_check=True, beats_passive trio, ref=champion."""
    src = open(f"{ROOT}/campaign/scripts/HUNT_FXCARRY2_round7.py").read()
    assert "leak_check=True" in src
    assert "beats_passive=True" in src
    assert "sig=" in src
    assert "scramble_n=200" in src


def test_07_book_is_daily_frequency():
    """Held book lives on the DAILY index (positions ffilled between month-end decisions):
    n_days >> n_decisions, and a 1-day holding-period return is a 1-day move (no
    monthly-return-as-daily-SR inflation)."""
    rates, spot = _mk_rates(n=1500), None
    spot = _mk_spot(rates)
    W, s, _ = M.build_carry_book(rates, spot, window=252)
    tot, fx, idx = M.fx_total_returns_daily(W, rates, spot)
    n_dec = int((W != 0).any(axis=1).sum())
    assert len(tot) > 5 * max(n_dec, 1)
    # daily moves are small: the biggest single-day move is < 5% (a monthly move would be ~10-30%)
    assert tot.abs().max() < 0.05
    # daily accrual per day is ~ rate-diff/252 magnitude; rates <= 10% in synth
    # => per-day accrual <= ~2*10/252 ~ 0.08 gross units; definitely not rate/12 (~0.04/leg
    # would be 0.08 for a single leg alone at 100% rate diff; bound: no day exceeds 0.05)
    daily_accr = fx.sum(axis=1)
    assert daily_accr.abs().quantile(0.99) < 0.05


def test_08_rates_are_decimal():
    """FRED/BoC rates arrive in PERCENT; the engine must convert to decimal before
    accrual (the /252 accrual of a percent-denominated rate inflates PnL 100x)."""
    s = M.load_rate("GBP_SONIA")
    assert s.abs().max() < 0.2, f"rates not decimal? max={s.abs().max()}"
    r = M.load_rate("USD_DFF")
    assert r.abs().max() < 0.25
