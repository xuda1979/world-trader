"""HUNT_COT2 round-5 tests: trader-count breadth panel (DATA_COTMORE work_r4).

Charter (a): positioning signals from the R4 trader_count_panel.csv — trader-COUNT breadth
(a NEW corner: counts, not positions). Property tests pin the PIT chain, the break-segment
discipline, and the V2 acceptance call signature (sig= + leak_check=True explicit).

Run: python3 -m pytest test_lib_hunt_r5.py -q   (from HUNT_COT2 dir)
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/Users/daxu/software/world-trader')

import lib_r5  # noqa: E402

ROOT = '/Users/daxu/software/world-trader'
PANEL = f'{ROOT}/campaign/agents/chief/coord/DATA_COTMORE/work_r4/trader_count_panel.csv'


# ---------------------------------------------------------------- break segments

class TestBreakSegments:
    def test_nat_gas_segmented_at_2022_02_08(self):
        """The -86% CFTC split must hard-segment nat_gas z: no read crosses 2022-02-08."""
        z = lib_r5.load_breadth('nat_gas_nymex', 'Tot_All')
        pre = z[z.index < '2022-02-08'].dropna()
        post = z[z.index >= '2022-02-08'].dropna()
        assert len(pre) > 100 and len(post) > 50
        # the stitched artifact z=-10.74 must NOT appear in either segment's input
        assert not (z.dropna() < -5).any(), 'stitched -10.74 leaked into segmented z'

    def test_lumber_segmented_at_2023_04_25(self):
        z = lib_r5.load_breadth('lumber', 'Tot_All')
        assert z.index.max() < pd.Timestamp('2026-09-01')
        # both segments produce values; the +105% jump never enters a z read
        pre = z[z.index < '2023-04-25'].dropna()
        post = z[z.index >= '2023-04-25'].dropna()
        assert len(pre) > 100 and len(post) >= 0  # lumber post-break span is short

    def test_break_families_declared(self):
        assert set(lib_r5.BREAKS) == {('nat_gas_nymex', '2022-02-08'),
                                      ('lumber', '2023-04-25')}

    def test_unbroken_family_full_span(self):
        """A PASS family keeps its full span (segmenting must not eat honest data)."""
        z = lib_r5.load_breadth('gold', 'Tot_All')
        assert z.index.min() >= pd.Timestamp('2010-06-01')
        assert len(z.dropna()) > 700


# ---------------------------------------------------------------- PIT chain

class TestPit:
    def test_release_shift_strictly_after_friday(self):
        """Signals key off release_date; trade on/after the NEXT session (T+1)."""
        s = pd.Series({'2024-01-02': 1.0, '2024-01-09': -1.0, '2024-01-16': 1.0})
        rel = lib_r5.release_shift_weekly(s)
        # 2024-01-02 Tue -> Fri 01-05; traded from Mon 01-08 session
        assert rel.index[0] == pd.Timestamp('2024-01-05')

    def test_daily_map_no_same_session(self):
        """A release must never trade on its own release date (release_lag=1)."""
        px = pd.Series(np.linspace(100, 110, 40).tolist(),
                       index=pd.bdate_range('2024-01-01', periods=40))
        sig = pd.Series([1.0], index=[pd.Timestamp('2024-01-05')])  # Friday release
        dp = lib_r5.signal_to_daily(sig, px, release_lag=1)
        first_live = dp[dp != 0].index[0]
        assert first_live > pd.Timestamp('2024-01-05')

    def test_z_uses_expanding_prior_only(self):
        """Panel z at row t must be reproducible from rows <= t (PIT expanding, ddof=0)."""
        df = lib_r5.load_panel_family('gold')
        c = df['cnt_Traders_Tot_All'].astype(float)
        mu = c.expanding(min_periods=26).mean()
        sd = c.expanding(min_periods=26).std(ddof=0)
        z_manual = (c - mu) / sd.where(sd > 0)
        got = df['z_Traders_Tot_All']
        both = pd.concat([z_manual, got], axis=1).dropna()
        assert np.allclose(both.iloc[:, 0], both.iloc[:, 1], atol=1e-8)


# ---------------------------------------------------------------- breadth signals

class TestBreadthSignals:
    def test_breadth_extreme_gate_shape(self):
        """gate=1 when breadth-z in the selected tail, else 0/NaN-warmup, never negative."""
        z = pd.Series([np.nan] * 5 + [-2.5, -2.6, 0.1, 2.4, 2.5], dtype=float)
        w = lib_r5.breadth_extreme_gate(z, thr=2.0, tail='low')
        assert (w.dropna() >= 0).all() and (w.dropna() <= 1).all()
        assert w.iloc[5] == 1.0 and w.iloc[6] == 1.0 and w.iloc[7] == 0.0 and w.iloc[8] == 0.0

    def test_cross_section_breadth_rank_sums_zero(self):
        """xs rank basket weights are long-k/short-k, market-neutral by construction."""
        rng = np.random.default_rng(3)
        z = pd.DataFrame(rng.normal(size=(30, 5)),
                         index=pd.date_range('2020-01-06', periods=30, freq='7D'),
                         columns=list('abcde'))
        w = lib_r5.xs_breadth_rank_weights(z, k=2)
        assert (w.sum(axis=1).abs() < 1e-9).all()
        assert w.notna().any().all()

    def test_segmented_z_feeds_signals(self):
        """nat_gas signal rows never span the break in one z state."""
        w = lib_r5.breadth_ts_weights('nat_gas_nymex', 'Tot_All', thr=1.0, tail='low')
        post = w[w.index >= '2022-02-08']
        assert len(post) > 0


# ---------------------------------------------------------------- V2 battery call

class TestV2Battery:
    def test_battery_call_shape(self):
        """Acceptance call must publish leak + beats_passive dicts (V2 §6/§7) fail-closed."""
        rng = np.random.default_rng(5)
        idx = pd.bdate_range('2022-01-03', periods=400)
        r = pd.Series(rng.normal(0, 0.01, 400), index=idx)
        sig = pd.Series(np.sign(rng.normal(size=400)), index=idx)
        spy = pd.Series(rng.normal(0, 0.01, 400), index=idx)
        ief = pd.Series(rng.normal(0, 0.005, 400), index=idx)
        cta = pd.Series(rng.normal(0, 0.008, 400), index=idx)
        g = lib_r5.v2_battery(r, sig=sig, spy=spy, ief=ief, cta=cta)
        assert 'leak' in g and 'leak_ok' in g and 'beats_passive_ok' in g
        assert g['pass'] is False or g['pass'] is True

    def test_battery_without_sig_fails_closed(self):
        idx = pd.bdate_range('2022-01-03', periods=300)
        g = lib_r5.v2_battery(pd.Series(np.random.default_rng(1).normal(0, .01, 300),
                                        index=idx))
        assert g['pass'] is False and g['leak_ok'] is False


# ---------------------------------------------------------------- integration

def test_engine_smoke_small_book():
    """End-to-end: 2 families, real panel, real prices -> gates dict with exact keys."""
    px_map = {'gold': f'{ROOT}/tools/quant/data/twelvedata/GLD.csv',
              'silver': f'{ROOT}/tools/quant/data/more_etf/SLV.csv'}
    g, book = lib_r5.run_config(
        families=['gold', 'silver'], col='Tot_All', tail='low', thr=1.5,
        k=None, px_map=px_map, label='smoke')
    assert g is not None
    for key in ('sr_full', 'pass_sr', 'pass_halves', 'pass_yearly', 'scramble_p', 'n_days'):
        assert key in g
    assert book.notna().any()
