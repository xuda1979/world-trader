"""TDD tests for HUNT_COT2 round-1 library. Run: python3 -m pytest test_lib_hunt.py -x -q (or python3 test_lib_hunt.py)"""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_COT2')
import numpy as np, pandas as pd
import lib_hunt as L

def test_timing_no_lookahead():
    """Signal released Friday must not earn any return before next trading day's close."""
    idx = pd.bdate_range('2024-01-01', periods=30)  # business days
    prices = pd.Series(np.linspace(100, 130, 30), index=idx)
    # signal dated at 2024-01-05 (Friday): report Tue 01-02 + 3d
    sig = pd.Series({pd.Timestamp('2024-01-05'): 1.0})
    daily = L.signal_to_daily(sig, prices, release_lag=1)  # contract mode
    pos = daily
    first_nonzero = pos[pos.abs() > 0].index[0]
    # pos may first be nonzero on Monday 01-08 (entry at Monday close) -> first P&L day Tue 01-09
    assert first_nonzero == pd.Timestamp('2024-01-08'), f"first pos day {first_nonzero}"
    gross = L.gross_ret(pos, prices)
    earned = gross[gross != 0]
    assert earned.index[0] == pd.Timestamp('2024-01-09'), f"first P&L day {earned.index[0]}"

def test_timing_no_lookahead_lag0():
    """release_lag=0 (borderline Friday-close entry): first P&L Monday, never Friday itself."""
    idx = pd.bdate_range('2024-01-01', periods=30)
    prices = pd.Series(np.linspace(100, 130, 30), index=idx)
    sig = pd.Series({pd.Timestamp('2024-01-05'): 1.0})
    daily = L.signal_to_daily(sig, prices, release_lag=0)
    gross = L.gross_ret(daily, prices)
    earned = gross[gross != 0]
    assert earned.index[0] == pd.Timestamp('2024-01-08'), f"first P&L day {earned.index[0]}"

def test_cost_full_dw():
    """6.4bps on FULL |dW|: one unit traded once costs 6.4bps; round trip 12.8bps."""
    idx = pd.bdate_range('2024-01-01', periods=5)
    prices = pd.Series([100.0]*5, index=idx)  # zero return
    pos = pd.Series([0.0, 0.0, 1.0, 1.0, 0.0], index=idx)
    net, to = L.net_ret(pos, prices, cost=6.4e-4, borrow=0.0)
    # turnover: day2 +1 (0->1), day4 -1 (1->0) => cost 6.4e-4 each on those days' P&L attribution
    assert abs(to.loc[idx[2]] - 1.0) < 1e-12
    assert abs(to.loc[idx[4]] - 1.0) < 1e-12
    assert abs(net.loc[idx[2]] + 6.4e-4) < 1e-12
    assert abs(net.loc[idx[4]] + 6.4e-4) < 1e-12

def test_borrow_cost():
    """0.5%/yr borrow on short notional: pos=-1 for 1 day => 0.005/252 charged."""
    idx = pd.bdate_range('2024-01-01', periods=5)
    prices = pd.Series([100.0]*5, index=idx)
    pos = pd.Series([0.0, -1.0, -1.0, 0.0, 0.0], index=idx)
    net, _ = L.net_ret(pos, prices, cost=0.0, borrow=0.005)
    # short held from close day1 to close day3: charged on days 2 and 3
    per_day = 0.005/252
    assert abs(net.loc[idx[2]] + per_day) < 1e-15
    assert abs(net.loc[idx[3]] + per_day) < 1e-15

def test_net_is_long_minus_short_pct():
    """(d) sanity: (L-S)/OI == L/OI - S/OI, so 'long_pct - short_pct' == net; new content must be ratio/separate-z."""
    rng = np.random.default_rng(0)
    for _ in range(100):
        oi = rng.integers(1000, 100000); lo = rng.integers(0, oi); sh = rng.integers(0, oi)
        assert abs((lo-sh)/oi - (lo/oi - sh/oi)) < 1e-12

def test_lsratio_scale_free():
    """L/(L+S) in [0,1], 0.5-neutral."""
    assert abs(L.ls_ratio(30, 10) - 0.75) < 1e-12
    assert abs(L.ls_ratio(10, 10) - 0.5) < 1e-12

def test_load_cot_9():
    """All 9 charter COT files load with expected columns and weekly cadence."""
    for m in L.MARKETS9:
        df = L.load_cot(m)
        assert {'net_noncomm_pct_oi','open_interest'} <= set(df.columns), m
        assert len(df) > 600, (m, len(df))

def test_load_prodmerc_swap():
    """Raw disagg re-parse gives prod_merc + swap longs/shorts for all 9 markets, aligned to report dates."""
    for m in L.MARKETS9:
        df = L.load_hedger(m)
        assert {'pm_net','pm_pct','sw_net','sw_pct'} <= set(df.columns), m
        assert len(df) > 600, (m, len(df))
        assert df['pm_pct'].abs().max() <= 1.0

def test_load_hedger_single_market_exact_match():
    """BUGFIX RED: load_hedger(m) must return ONLY that market's family rows (prior version returned
    all 9 families mixed: gold n=6181), and must use the audited exact cot_matcher rules so the
    mm_pct series reproduces the committed legacy net_noncomm_pct_oi EXACTLY (corr 1.0, max|d|=0
    for the 7 exact-rule markets; wti/natgas too once HENRY HUB / micro-contract collisions are
    resolved by the audited priority)."""
    for m in L.MARKETS9:
        h = L.load_hedger(m)
        assert h.index.is_unique, m
        assert len(h) < 1000, (m, len(h))   # one row per week, not all families
    g = L.load_hedger('gold')
    leg = L.load_cot('gold')['net_noncomm_pct_oi']
    j = pd.concat([leg, g['mm_pct']], axis=1, join='inner').dropna()
    j = j[j.index >= '2013-06-01']
    assert len(j) > 600, len(j)
    assert j.iloc[:, 0].corr(j.iloc[:, 1]) > 0.9999, j.iloc[:, 0].corr(j.iloc[:, 1])
    # legacy CSV stores %OI rounded to 6dp (e.g. 0.351946) -> max allowed rounding residual 5e-7
    assert (j.iloc[:, 0] - j.iloc[:, 1]).abs().max() < 6e-7, (j.iloc[:, 0] - j.iloc[:, 1]).abs().max()
    for m in ['wti', 'nat_gas_nymex']:   # collision markets must also reproduce legacy
        h = L.load_hedger(m)
        leg = L.load_cot(m)['net_noncomm_pct_oi']
        j = pd.concat([leg, h['mm_pct']], axis=1, join='inner').dropna()
        j = j[j.index >= '2013-06-01']
        assert j.iloc[:, 0].corr(j.iloc[:, 1]) > 0.9999, (m, len(j))
        assert (j.iloc[:, 0] - j.iloc[:, 1]).abs().max() < 6e-7, (m, (j.iloc[:, 0]-j.iloc[:, 1]).abs().max())

def test_price_proxies():
    for m, p in L.PX9.items():
        s = L.load_px(p)
        assert len(s) > 2000, (m, len(s))

# ---------- charter aggregates (a)-(d) ----------

def test_release_shift_report_to_friday():
    """Real COT sig is indexed by REPORT date (Tuesday); +3 calendar days = Friday release.
    After shifting, lag1 timing must place first P&L at the 2nd session after Friday."""
    idx = pd.bdate_range('2024-01-01', periods=30)
    prices = pd.Series(np.linspace(100, 130, 30), index=idx)
    report = pd.Timestamp('2024-01-02')          # Tuesday
    sig = pd.Series({report: 1.0})
    rel = pd.Series({L.release_shift(report): 1.0})
    assert L.release_shift(report) == pd.Timestamp('2024-01-05')
    daily = L.signal_to_daily(rel, prices, release_lag=1)
    gross = L.gross_ret(daily, prices)
    earned = gross[gross != 0]
    assert earned.index[0] == pd.Timestamp('2024-01-09'), earned.index[0]

def test_signal_to_daily_lag0_enters_release_session():
    """lag0: position first nonzero ON the release session (Fri 01-05), P&L starts Mon 01-08."""
    idx = pd.bdate_range('2024-01-01', periods=30)
    prices = pd.Series(np.linspace(100, 130, 30), index=idx)
    sig = pd.Series({pd.Timestamp('2024-01-05'): 1.0})
    d = L.signal_to_daily(sig, prices, release_lag=0)
    assert d[d.abs() > 0].index[0] == pd.Timestamp('2024-01-05')
    g = L.gross_ret(d, prices)
    assert g[g != 0].index[0] == pd.Timestamp('2024-01-08')

def test_load_cot_dates_are_tuesdays():
    """Aggregated COT files must be indexed by Tuesday report dates (release_shift convention)."""
    import pandas as _pd
    df = L.load_cot('gold')
    dows = _pd.Series(df.index.dayofweek).value_counts()
    assert dows.idxmax() == 1, dows   # 1 == Tuesday

# ---------- charter aggregates (a)-(d) ----------

def _synth_weeks(n=520):
    rng = np.random.default_rng(7)
    dates = pd.bdate_range('2010-01-05', periods=n, freq='C', weekmask='Tue')
    mks = L.MARKETS9
    pm = pd.DataFrame(rng.normal(0, .15, (n, len(mks))), index=dates, columns=mks)  # pm_pct (hedger short)
    mm = pd.DataFrame(rng.normal(0, .15, (n, len(mks))), index=dates, columns=mks)  # mm_pct (spec)
    oi = pd.DataFrame(np.abs(rng.normal(1e5, 2e4, (n, len(mks)))), index=dates, columns=mks)
    return pm, mm, oi

def test_cross_market_rank_baskets():
    """(a) cross-market rank: long most-crowded-SHORT basket, short most-crowded-LONG basket;
    with 9 markets and k=3 -> basket NET exposure 0 (fully offset), self-exclusive, no overlap;
    gross 2/3 (each leg k * 1/k = 1.0 notional per side of the 9-market universe scaled by 1/k)."""
    pm, mm, oi = _synth_weeks()
    pos = L.cross_market_rank_positions(mm_pct=mm, oi=oi, k=3)
    w = pos.iloc[-1]
    longs = w[w > 0]; shorts = w[w < 0]
    assert len(longs) == 3 and len(shorts) == 3
    assert abs(longs.sum() - 1.0) < 1e-12 and abs(shorts.sum() + 1.0) < 1e-12
    assert abs(shorts.sum() + 1.0) < 1e-12
    assert set(longs.index).isdisjoint(set(shorts.index))
    # most-crowded-SHORT spec (most negative mm_pct) must be IN the long basket
    assert mm.iloc[-1].idxmin() in set(longs.index)
    assert mm.iloc[-1].idxmax() in set(shorts.index)

def test_hedger_fade_positions():
    """(b) hedger fade: LONG when commercials are crowded SHORT (pm_pct low), short when crowded LONG.
    Monotone in pm_pct: pos(z=-2) > pos(z=0) > pos(z=+2), sign flipped vs spec-follow."""
    pm, mm, oi = _synth_weeks(n=30)
    pos = L.hedger_fade_positions(pm_pct=pm, lookback=12)
    z = (pm - pm.rolling(12, min_periods=6).mean()) / pm.rolling(12, min_periods=6).std()
    for t in range(14, 20):
        row = z.iloc[t]
        assert pos.iloc[t][row.idxmin()] > pos.iloc[t][row.idxmax()] > 0 or \
               pos.iloc[t][row.idxmin()] > 0 > pos.iloc[t][row.idxmax()]
        assert pos.iloc[t][row.idxmax()] < 0

def test_oi_change_overlay():
    """(c) OI-change regime overlay: output in [0,1], zero when OI flat/falling, ramps with OI growth."""
    idx = pd.bdate_range('2010-01-05', periods=40, freq='C', weekmask='Tue')
    cols = ['a', 'b']
    flat_oi = pd.DataFrame(np.ones((40, 2)) * 1e5, index=idx, columns=cols)
    ov_flat = L.oi_change_overlay(flat_oi, lookback=8)
    assert (ov_flat == 0).all().all(), ov_flat          # flat OI -> zero overlay everywhere
    rising = flat_oi.copy()
    rising.iloc[12:] = np.linspace(1.05, 1.60, 28)[:, None] * 1e5   # steady +5%/wk
    ovr = L.oi_change_overlay(rising, lookback=8)
    assert (ovr >= 0).all().all() and (ovr <= 1).all().all()
    assert (ovr.iloc[22] > 0).all(), ovr.iloc[22]       # sustained growth -> positive overlay
    falling = flat_oi.copy()
    falling.iloc[12:] = np.linspace(0.95, 0.60, 28)[:, None] * 1e5
    assert (L.oi_change_overlay(falling, lookback=8).iloc[22] == 0).all()   # falling OI -> 0

def test_spec_asymmetry_positions():
    """(d) long/short asymmetry: L/(L+S) ratio needs SEPARATE long_pct/short_pct columns;
    net alone is mathematically identical -> raises on net-only input."""
    pm, mm, oi = _synth_weeks(n=30)
    try:
        L.spec_asymmetry_positions(net_pct=mm, oi=oi)
        assert False, "net-only input must raise (no new information)"
    except ValueError:
        pass
    # with real L/S split: high L/(L+S) => short (fade)
    rng = np.random.default_rng(3)
    lo = pd.DataFrame(rng.uniform(.05, .3, (30, 9)), index=pm.index, columns=L.MARKETS9)
    sh = pd.DataFrame(rng.uniform(.05, .3, (30, 9)), index=pm.index, columns=L.MARKETS9)
    pos = L.spec_asymmetry_positions(long_pct=lo, short_pct=sh, lookback=12)
    ratio = (lo / (lo + sh))
    assert pos.iloc[20][ratio.iloc[20].idxmax()] < pos.iloc[20][ratio.iloc[20].idxmin()]

def test_vol_target_trailing_only():
    """(g) vol target: trailing-only realized vol (incl. today's lagged ret), scale clip <= max_lev."""
    rng = np.random.default_rng(5)
    r = pd.Series(rng.normal(0.0005, .01, 600))
    tgt = L.vol_target_scale(r, target=0.10, max_lev=3.0)
    assert (tgt <= 3.0 + 1e-12).all() and (tgt >= 0).all()
    # big shock day -> next scale capped, not negative
    r2 = r.copy(); r2.iloc[400] = -0.25
    t2 = L.vol_target_scale(r2, target=0.10, max_lev=3.0)
    assert np.isfinite(t2).all()

def test_gates_full_eval():
    """Gates: net SR>=1, halves>=0.5, <=2 neg years >-5%, scramble p<0.05, plateau, corr gate.
    Scramble gate is FAIL-CLOSED when no signal (pos,prices) supplied: a return-only permutation
    preserves mean/std exactly (degenerate null), so it can never be a valid p-value."""
    rng = np.random.default_rng(11)
    ret = pd.Series(rng.normal(0.001, .005, 2000), index=pd.bdate_range('2016-01-04', periods=2000))
    g = L.eval_gates(ret, champion_rets=None)
    assert g['sr_full'] > 1 and g['pass_halves']
    assert not g['pass_scramble'] and g['scramble_p'] != g['scramble_p']  # NaN, fail-closed
    bad = pd.Series(rng.normal(0.0, .01, 2000), index=ret.index)
    g2 = L.eval_gates(bad, champion_rets=None)
    assert g2['sr_full'] < 0.5 and not g2['pass_sr']

def test_scramble_statistic():
    """Signal-scramble: circular shift of POSITION series vs returns. Positions that truly
    anticipate returns (AR(1) prices) must beat the null; a random pos must not."""
    rng = np.random.default_rng(2)
    n = 1500
    eps = rng.normal(0, .004, n)
    ret = pd.Series(eps, index=pd.bdate_range('2015-01-01', periods=n))
    for i in range(1, n):                     # AR(1): +0.25 persistence -> exploitable timing
        ret.iloc[i] += 0.25 * ret.iloc[i - 1]
    px = (1 + ret).cumprod() * 100
    # skilled: hold sign of yesterday's return (exploits AR(1) with ~0.25*corr)
    skilled = np.sign(ret.shift(1)).fillna(0)
    p_good = L.scramble_pvalue(skilled, px, n=200, seed=3)
    assert 0.0 <= p_good <= 1.0 and p_good < 0.05, p_good
    p_rand = L.scramble_pvalue(pd.Series(rng.normal(0, 1, n), index=ret.index), px, n=200, seed=3)
    assert p_rand > 0.05, p_rand   # random timing must NOT pass

def test_signal_to_daily_price_history_starts_late():
    """Regression: many releases predate the first price session (e.g. copper px starts
    2010-04-20 vs COT 2010-01-05). searchsorted(side='right') maps them all to session 0 ->
    duplicate labels. Must dedupe keep-last (latest report wins at first tradable session)."""
    idx = pd.bdate_range('2010-04-20', periods=30)
    prices = pd.Series(np.linspace(100, 130, 30), index=idx)
    rels = pd.bdate_range('2010-01-05', periods=8, freq='C', weekmask='Tue')  # 8 releases, all pre-history
    sig = pd.Series(np.arange(1.0, 9.0), index=rels)
    daily = L.signal_to_daily(sig, prices, release_lag=1)
    assert daily.index.is_unique
    # all pre-history releases map to session 0; LATEST report (value 8.0) wins there,
    # position goes on at that close, P&L accrues from session 2 onward
    assert daily.iloc[0] == 8.0, daily.iloc[0]

if __name__ == '__main__':
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc(); sys.exit(1)
    print("ALL TESTS PASS")
