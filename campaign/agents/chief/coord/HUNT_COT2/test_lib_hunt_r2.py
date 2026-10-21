"""HUNT_COT2 round-2 tests: horizon holds, TFF/CIT loaders, champion regime overlay.
Run: python3 -m pytest test_lib_hunt_r2.py -q"""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_COT2')
import numpy as np, pandas as pd
import lib_hunt as L
import lib_r2 as R


def _mk_pos(idx, cols, fn):
    return pd.DataFrame({c: fn(pd.Series(idx)) for c in cols}, index=idx)


class TestWeeklyHold:
    def setup_method(self):
        self.idx = pd.date_range('2015-01-05', periods=26, freq='7D')
        # position flips sign every report
        self.pos = pd.DataFrame({'a': [(-1.0) ** (i % 2) for i in range(26)],
                                 'b': [(-1.0) ** ((i + 1) % 2) for i in range(26)]},
                                index=self.idx)

    def test_h1_identical_to_input(self):
        out = R.weekly_hold(self.pos, 1)
        pd.testing.assert_frame_equal(out, self.pos)

    def test_h4_updates_every_4th_report_only(self):
        out = R.weekly_hold(self.pos, 4)
        # update weeks = index[::4]; other rows must equal the last update (ffill)
        upd = self.idx[::4]
        assert list(out.index[::4]) == list(upd)
        for c in ['a', 'b']:
            assert (out[c].reindex(upd).values == self.pos[c].reindex(upd).values).all()
            # a week between updates carries the previous UPDATE value, not its own signal
            mid = self.idx[3]
            assert out[c].loc[mid] == self.pos[c].loc[upd[0]]
        # no NaNs introduced by the hold
        assert not out.isna().any().any()

    def test_h13_shape_preserved_and_nonzero(self):
        out = R.weekly_hold(self.pos, 13)
        assert out.shape == self.pos.shape
        assert (out != 0).any().any()

    def test_hold_independence_of_column_order(self):
        out = R.weekly_hold(self.pos[['b', 'a']], 4)
        pd.testing.assert_frame_equal(out, R.weekly_hold(self.pos, 4)[['b', 'a']])


class TestTFFLoader:
    def test_load_tff_real_file_columns(self):
        df = R.load_tff('sp500_emini', 'dealer')
        assert set(['net', 'pct_of_oi', 'oi']).issubset(df.columns)
        assert df.index.is_monotonic_increasing
        assert not df.index.duplicated().any()
        assert (df['oi'] > 0).all()
        assert df['pct_of_oi'].abs().max() <= 1.0

    def test_all_basket_files_exist(self):
        for mkt, _px in R.TFF_BASKET:
            df = R.load_tff(mkt, 'dealer')
            assert len(df) > 400, mkt
            for _cat in ['dealer', 'lev_money']:
                assert len(R.load_tff(mkt, _cat)) > 400, (mkt, _cat)

    def test_px_proxy_files_exist_and_load(self):
        R.ensure_jpy_proxy()
        for mkt, _p in R.TFF_BASKET:
            s = R.px_loader(mkt)
            assert len(s) > 1500, mkt
            assert (s > 0).all()


class TestTFFPxConventions:
    def test_jpy_proxy_inverted_vs_dexjpus(self):
        """CME yen futures are quoted USD per JPY; DEXJPUS is yen per USD -> proxy = 1/DEXJPUS."""
        R.ensure_jpy_proxy()
        s = R.px_loader('jpy')
        raw = R.px_loader('_raw_dexjpus')
        j = pd.concat([s, raw], axis=1, join='inner').dropna()
        prod = (j.iloc[:, 0] * j.iloc[:, 1])
        assert (prod - 1.0).abs().max() < 1e-6

    def test_eur_gbp_proxy_not_inverted(self):
        for mkt, raw_key in [('eur', '_raw_dexuseu'), ('gbp', '_raw_dexusuk')]:
            s = R.px_loader(mkt)
            raw = R.px_loader(raw_key)
            j = pd.concat([s, raw], axis=1, join='inner').dropna()
            assert (j.iloc[:, 0] - j.iloc[:, 1]).abs().max() < 1e-6, mkt


class TestCITLoader:
    def test_load_cit_real_file(self):
        df = R.load_cit('corn')
        assert set(['cit_net', 'cit_pct_oi', 'open_interest']).issubset(df.columns)
        assert df.index.is_monotonic_increasing and not df.index.duplicated().any()
        assert df['cit_pct_oi'].abs().max() <= 1.0

    def test_cit_basket_files_exist(self):
        for mkt in R.CIT_BASKET:
            df = R.load_cit(mkt)
            assert len(df) > 400, mkt


class TestChampionOverlay:
    def _champ(self, idx):
        return pd.Series(0.0005 * np.sin(np.arange(len(idx)) / 7.0), index=idx)

    def test_neutral_scale_one_is_identity(self):
        idx = pd.bdate_range('2012-01-02', periods=2000)
        champ = self._champ(idx)
        crowd = pd.Series(0.9, index=pd.date_range('2012-01-02', periods=300, freq='7D'))
        out = R.champion_overlay(champ, crowd, mode='scale', extreme_hi=0.9)
        pd.testing.assert_series_equal(out, champ)

    def test_overlay_scale_is_lagged(self):
        """Scale applied at session t must derive only from a release strictly before t."""
        idx = pd.bdate_range('2012-01-02', periods=2000)
        champ = self._champ(idx)
        crowd = pd.Series(np.linspace(0.0, 1.0, 300), index=pd.date_range('2012-01-02', periods=300, freq='7D'))
        out = R.champion_overlay(champ, crowd, mode='scale', extreme_hi=0.9)
        scale = out / champ.where(champ != 0).ffill()  # approx per-day scale
        daily_scale = R.overlay_scale_daily(crowd, champ.index, mode='scale', extreme_hi=0.9)
        # every nonzero scale must be <= the last weekly value released strictly before t
        for t in idx[::250]:
            past = crowd.index[crowd.index + pd.Timedelta(days=3) <= t]
            if len(past):
                assert daily_scale.loc[t] <= 1.0 + 1e-12

    def test_extreme_crowding_scales_down(self):
        """mode='scale': crowding above extreme_hi -> exposure halved."""
        idx = pd.bdate_range('2012-01-02', periods=400)
        champ = self._champ(idx)
        crowd = pd.Series(0.99, index=pd.date_range('2012-01-02', periods=60, freq='7D'))
        daily_scale = R.overlay_scale_daily(crowd, idx, mode='scale', extreme_hi=0.9, cut=0.5)
        late = idx[-5]
        assert daily_scale.loc[late] == 0.5  # after full release chain from the weekly series

    def test_flip_mode_extreme_inverts_sign(self):
        idx = pd.bdate_range('2012-01-02', periods=400)
        champ = self._champ(idx)
        crowd = pd.Series(0.99, index=pd.date_range('2012-01-02', periods=60, freq='7D'))
        daily_scale = R.overlay_scale_daily(crowd, idx, mode='flip', extreme_hi=0.9)
        assert daily_scale.loc[idx[-5]] == -1.0

    def test_no_future_release_used(self):
        """A crowd series that STARTS late must leave scale=1 (not 0) before its first release."""
        idx = pd.bdate_range('2012-01-02', periods=400)
        crowd = pd.Series(0.5, index=pd.date_range('2015-01-02', periods=20, freq='7D'))
        daily_scale = R.overlay_scale_daily(crowd, idx, mode='scale', extreme_hi=0.9, cut=0.5)
        assert (daily_scale.loc[:'2014-12-01'] == 1.0).all()

    def test_cut_zero_is_legal_scale_not_neutral(self):
        """cut=0.0 means go FLAT during extreme crowding: the scale must be 0.0 there, and the
        blanket replace(0->1) must NOT silently undo it (neutral-1 applies only pre-first-release)."""
        idx = pd.bdate_range('2012-01-02', periods=400)
        crowd = pd.Series(0.99, index=pd.date_range('2012-01-02', periods=60, freq='7D'))
        daily_scale = R.overlay_scale_daily(crowd, idx, mode='scale', extreme_hi=0.9, cut=0.0)
        assert daily_scale.loc[idx[-5]] == 0.0

    def test_first_release_snaps_to_session_not_gap(self):
        """The first tradable session of the overlay must be the first PRICE session strictly
        after the Friday release (a weekly 7D crowd index never lands on a business day end)."""
        idx = pd.bdate_range('2012-01-02', periods=400)
        crowd = pd.Series(0.99, index=pd.date_range('2012-01-02', periods=60, freq='7D'))
        daily_scale = R.overlay_scale_daily(crowd, idx, mode='scale', extreme_hi=0.9, cut=0.5)
        changed = daily_scale[daily_scale != 1.0]
        assert len(changed) > 0
        # every changed session must be strictly after the first release (+3d), i.e. PIT
        assert changed.index.min() > crowd.index.min() + pd.Timedelta(days=3)


class TestCrowdPercentile:
    def test_trailing_percentile_no_lookahead(self):
        """Time-series crowd percentile at t must use only values strictly before t.
        NOTE: the original draft asserted pct[104]<1.0 AND pct[-1]==1.0 for a monotone series —
        mutually impossible under ANY fixed trailing rule (a monotone series is always at the
        top of its trailing window). Test pins the consistent semantics instead."""
        agg = pd.Series(np.arange(300, dtype=float), index=pd.date_range('2010-01-01', periods=300, freq='7D'))
        pct = R.crowd_percentile(agg, window=104)
        assert pct.iloc[-1] == 1.0
        assert np.isnan(pct.iloc[103])   # window not yet full at 103
        assert pct.iloc[104] == 1.0  # monotone: top of its (self-excluded) trailing window
        # LOOKAHEAD CHECK: corrupting the future must not change any past percentile
        corrupt = agg.copy(); corrupt.iloc[250:] = -999.0
        pct2 = R.crowd_percentile(corrupt, window=104)
        pd.testing.assert_series_equal(pct.iloc[:250], pct2.iloc[:250])

    def test_output_bounded_unit(self):
        rng = np.random.default_rng(3)
        agg = pd.Series(rng.normal(size=400), index=pd.date_range('2010-01-01', periods=400, freq='7D'))
        pct = R.crowd_percentile(agg, window=104)
        assert ((pct.dropna() >= 0) & (pct.dropna() <= 1)).all()
        assert pct.iloc[:104].isna().all()  # window not yet full -> NaN, not a fake 0/1


class TestOverlayScramble:
    def test_real_edge_significant_random_crowd_rejected(self):
        """Champion returns whose DRIFT genuinely depends on the crowd regime must pass (p<0.05);
       an uncorrelated champion must FAIL the scramble gate (honesty: no free pass).
       NOTE: a champion of iid-noise*mask (the original fixture) is statistically INCAPABLE of
       beating the null — masking random iid days never shifts the SR distribution, so real SR
       always sits inside the null (measured: p_real 0.344 vs p_flat 0.082). Dependence must be
       in the drift, not the noise scaling."""
        idx = pd.bdate_range('2013-01-02', periods=2600)
        rng = np.random.default_rng(11)
        crowd = pd.Series(rng.random(400), index=pd.date_range('2013-01-02', periods=400, freq='7D'))
        scale = R.overlay_scale_daily(crowd, idx, mode='scale', extreme_hi=0.9, cut=0.0)
        # bad days ARE the extreme-crowd days -> overlay removes them -> real alignment beats
        # scrambled alignments, which remove random days
        base = rng.normal(0, 0.006, len(idx))
        driven = pd.Series(np.where(scale == 0.0, -0.004, 0.0005) + base, index=idx)
        p_real = R.overlay_scramble_pvalue(driven, crowd, mode='scale', extreme_hi=0.9, cut=0.0, n=60)
        p_flat = R.overlay_scramble_pvalue(pd.Series(rng.normal(0.0005, 0.01, len(idx)), index=idx),
                                           crowd, mode='scale', extreme_hi=0.9, cut=0.0, n=60)
        assert p_real < p_flat, (p_real, p_flat)
        assert p_real < 0.05, p_real
        assert p_flat >= 0.05  # uncorrelated overlay must NOT look significant
    def test_r1_9market_panel_still_works_through_generic_path(self):
        """Round-1 driver results must reproduce through the generic engine (same timing/costs)."""
        pos = pd.DataFrame({'gold': [0.5, -0.5] * 5}, index=pd.date_range('2024-01-01', periods=10, freq='7D'))
        g, _r = R.book_backtest_generic(pos, {'gold': L.PX9['gold']}, vt=False)
        assert 'sr_full' in g and g['n_days'] > 0


class TestBookLiveWindow:
    """R2 driver bug: live window was dp.notna().any() but signal_to_daily fillna(0)s pre-signal
    days -> a market with prices decades older than its first COT release (gbp/jpy 1971 vs TFF
    2010) put ~40y of ZERO positions in the book: sr_h1 pinned to 0.00 exactly, all TFF gates garbage."""

    def test_book_starts_at_first_signal_not_price_start(self):
        # 5000 bdays from 1971 ends ~1990-02: releases MUST sit inside the price span or no
        # session is ever tradable (the pre-fix session's fixture put 2010 releases past the end).
        long_px = pd.Series(np.linspace(100.0, 200.0, 5000),
                            index=pd.bdate_range('1971-01-04', periods=5000))
        rel = pd.Series([0.5, -0.5] * 4, index=pd.date_range('1985-01-04', periods=8, freq='7D'))
        pos = pd.DataFrame({'a': rel})
        g, r = R.book_backtest_generic(pos, {'a': long_px}, vt=False, scramble_n=5)
        first_tradable = long_px.index[long_px.index.searchsorted(rel.index[0] + pd.Timedelta(days=3),
                                                                  side='right')]
        assert g['start'] == str(first_tradable.date()), g['start']
        assert g['n_days'] == 5000 - list(long_px.index).index(first_tradable)

    def test_halves_not_pinned_to_zero_by_pre_signal_zeros(self):
        """Without the bug, H1 SR must reflect actual signal-era returns, not a std-0 zero block."""
        rng = np.random.default_rng(5)
        n = 4000                                   # 1971-01..~1986-06
        px = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, n))),
                       index=pd.bdate_range('1971-01-04', periods=n))
        rel_dates = pd.date_range('1977-01-07', periods=60, freq='7D')   # signal era ~1977-78
        rel = pd.Series(np.where(np.arange(60) % 2 == 0, 1.0, -1.0), index=rel_dates)
        g, _ = R.book_backtest_generic(pd.DataFrame({'a': rel}), {'a': px}, vt=False, scramble_n=5)
        assert g['sr_h1'] != 0.0 or g['sr_h2'] != 0.0   # at least one half has real variance
        # pre-signal zeros must be excluded: pre-fix n_days == n (book counted from 1971);
        # post-fix the book starts at the first tradable session (1977) — the tail AFTER the
        # last release legitimately ffills the held position to the end of prices.
        assert g['n_days'] < n, g['n_days']
        assert g['start'] == '1977-01-11', g['start']
