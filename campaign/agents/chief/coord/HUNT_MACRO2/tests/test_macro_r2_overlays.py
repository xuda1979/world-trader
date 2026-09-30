"""HUNT_MACRO2 round-2 TDD: FRED OVERLAYS on the committed champion.

Acceptance (CHARTER round 2): overlay must improve champion ann by >=0.3pp OR MDD by
>=0.5pp WITHOUT violating 0-neg-years or leverage<=1.6, scramble-stable, PIT-safe lags.

Overlays under test (pre-specified BEFORE any evaluation run):
 (a) USREC recession flag, 1-YEAR publication lag (NBER dating is not real-time), trigger
     = flag==1 for the trailing 3 consecutive months -> scale 0.6x. Slot variant scales
     ONLY risk-on slots (C5ng, C5ngsum, carryv2, QAxasts, dualmom, diescrack, CFX4);
     duration/defensive slots (brwt15/10/7/5, a6r7, A5r2) untouched. Classification is
     committed HERE, before results, to avoid post-hoc cherry-picking.
 (b) T5YIFR 126bd trend -> TIPS-vs-nominal tilt inside the a6r7 bond slot.
 (c) T10Y2Y z63 < -2 de-risk gate; VIXCLS mean(21bd) > 30 vol-regime overlay; alone+joint.
 (d) TOTALSL yoy growth < 0 (G.19, ref month m visible m_end+40d) risk-appetite gate.

Run: pytest campaign/agents/chief/coord/HUNT_MACRO2/tests/ -q
"""
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_MACRO2/work_r2")

r2 = pytest.importorskip("HUNT_MACRO2_round2")

GEAR, RATE, BPS = 1.6, 0.045, 6.4


# ---------------------------------------------------------- 1. PIT release lags
def test_usrec_one_year_pub_lag():
    """CHARTER (a): NBER USREC has ~1yr publication lag. The flag for month m must be
    invisible strictly before m_end + 365 calendar days on the business-day grid."""
    s = pd.Series([0.0, 1.0, 1.0],
                  index=pd.to_datetime(['2008-11-30', '2008-12-31', '2009-01-31']))
    pit = r2.pit_monthly(s, pub_days=365)
    cal = pd.bdate_range('2008-12-01', '2010-03-31')
    d = pit.reindex(cal).ffill()
    dec1 = pd.Timestamp('2008-12-31') + pd.Timedelta(days=365)
    # R2 spec repair: the Nov-2008 flag (0.0) is legitimately visible from 2008-11-30+365 =
    # 2009-11-30; what must be invisible before 2009-12-31 is the RECESSION ONSET (flag 1.0).
    assert (d.loc[d.index < dec1].fillna(0.0) == 0.0).all(), 'USREC onset visible before Dec+365d'
    # Nov-2008 flag (0.0) visible from 2009-11-30; Dec flag (1.0) visible exactly 2009-12-31
    nov_vis = d.loc['2009-11-25':'2009-12-30'].dropna()
    assert len(nov_vis) > 0 and (nov_vis == 0.0).all(), 'Nov flag must show 0.0 before Dec+365d'
    assert d.loc[d.index >= dec1].dropna().iloc[0] == 1.0  # Dec flag lands exactly on +365d
    assert d.loc['2009-12-31':].dropna().min() == 1.0      # Dec/Jan flags eventually visible


def test_totalsl_g19_lag():
    """CHARTER (d): G.19 consumer credit ref month m is visible ~day-7 of m+1; we use a
    conservative m_end + 40 calendar days. Value must not appear earlier."""
    s = pd.Series([100.0, 110.0], index=pd.to_datetime(['2010-05-31', '2010-06-30']))
    pit = r2.pit_monthly(s, pub_days=40)
    cal = pd.bdate_range('2010-06-01', '2010-09-30')
    d = pit.reindex(cal).ffill()
    vis = pd.Timestamp('2010-06-30') + pd.Timedelta(days=40)
    # R2 spec repair: the PRIOR ref month (May, 100.0) is legitimately visible from 2010-07-10;
    # what must be invisible before +40d is the JUNE value itself.
    assert (d.loc[d.index < vis] == 110.0).sum() == 0, 'June value visible before m_end+40d'
    assert d.loc[d.index >= vis].dropna().iloc[0] == 110.0


def test_daily_market_series_one_day_lag():
    """H.15/VIX prints at t are usable from t+1 (pub_days=1): on day t the value printed
    AT t must NOT be visible; the t-1 print must be. R2 spec repair: the stale expectation
    asserted d[t] == print[t] (same-day visibility = leak) contradicting its own docstring."""
    idx = pd.bdate_range('2015-01-01', periods=6)
    s = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0], index=idx)
    d = r2.pit_daily(s, pub_days=1)
    assert pd.isna(d.reindex([idx[0]]).iloc[0])  # no print visible on day 0 (not on the grid)
    assert d.loc[idx[1]] == 10.0        # day t sees the PREVIOUS business day's print
    assert d.loc[idx[2]] == 11.0        # consecutive bdays: day t sees print t-1
    assert d.loc[idx[5]] == 14.0


# ---------------------------------------------------------- 2. trigger mechanics
def test_usrec_trailing3_all_trigger():
    """Trigger = flag==1 for the trailing 3 consecutive monthly PIT flags (all-3, strict).
    Two recession months must NOT fire; three must."""
    m = pd.Series([0, 0, 1, 1, 1, 0], index=pd.date_range('2008-01-31', periods=6, freq='ME'))
    trig = r2.trailing3_all(m)
    assert list(trig.astype(int)) == [0, 0, 0, 0, 1, 0]


def test_vix_sustained21_gate():
    """CHARTER (c): VIXCLS>30 SUSTAINED 21d. R2 spec repair: the pinned cases (20 obs at 40
    then a 0 must NOT fire; 21 consecutive >=31 must) are the ALL-21-OBS semantics — a
    rolling-MEAN gate computes 20*40/21 = 38.1 > 30 on the first case and cannot satisfy it.
    So 'sustained' = rolling(21).min() > 30; the mean variant is kept for the scan."""
    idx = pd.bdate_range('2020-01-01', periods=42)
    v = pd.Series(40.0, index=idx)
    v.iloc[20:] = 0.0                       # only 20 high obs before the drop
    t = r2.vix_gate(v, mode='sustained')
    assert not t.iloc[:21].any()
    assert not t.iloc[21:].any()            # every 21-window now contains the 0
    v2 = pd.Series(31.0, index=idx)
    t2 = r2.vix_gate(v2, mode='sustained')
    assert t2.iloc[20] and t2.iloc[21]      # fires from the 21st obs onward
    # mean variant documented: it fires on the diluted window (softer regime definition)
    assert bool(r2.vix_gate(v, mode='mean').iloc[20])


def test_t10y2y_z63_threshold():
    """CHARTER (c): z = (y - mean63)/std63 < -2 fires de-risk. Synthetic known-z path."""
    idx = pd.bdate_range('2018-01-01', periods=120)
    y = pd.Series(1.0, index=idx)
    y.iloc[-3:] = 0.0                       # crash the level -> z << -2 at the tail
    z = r2.z63(y)
    trig = z < -2
    assert trig.iloc[-1]
    assert not trig.iloc[:63].any()         # warmup: no trigger before 63 obs


def test_totalsl_growth_collapse():
    """CHARTER (d): trigger = 12-month yoy growth of TOTALSL < 0."""
    idx = pd.date_range('2010-01-31', periods=15, freq='ME')
    s = pd.Series(np.linspace(100, 130, 15), index=idx)
    s.iloc[-4:] = [128, 126, 125, 124]      # yoy still positive
    g = r2.yoy12(s)
    assert not (g < 0).any()
    s2 = s.copy()
    s2.iloc[-1] = 95.0                      # yoy = 95/124 - 1 < 0
    assert (r2.yoy12(s2) < 0).iloc[-1]


def test_t5yifr_tilt_sign():
    """CHARTER (b): rising 5y5y inflation expectation (126bd) -> TIPS (1); falling -> nominal (0)."""
    idx = pd.bdate_range('2015-01-01', periods=200)
    up = pd.Series(np.linspace(2.0, 3.0, 200), index=idx)
    dn = up.iloc[::-1].set_axis(idx)
    assert r2.tilt_tips(up, N=126).iloc[-1] == 1.0
    assert r2.tilt_tips(dn, N=126).iloc[-1] == 0.0


# ---------------------------------------------------------- 3. champion identities
def test_champion_rebuild_matches_committed():
    """The slot-level weight frame rebuilt by round2 must reproduce the COMMITTED champion
    net series to <1e-12 (same construction as rawew13v2_build, no drift)."""
    net, Wg, df = r2.build_champion()
    champ = r2.CHAMP
    j = pd.concat([champ.rename('c'), net.rename('n')], axis=1, join='inner').dropna()
    assert len(j) >= 4800
    assert float((j.c - j.n).abs().max()) < 1e-12
    # gross is exactly 1.6 every day and never above the cap
    assert abs(Wg.abs().sum(axis=1).max() - GEAR) < 1e-9


def test_book_overlay_identity_at_m1():
    """m(t) == 1 must reproduce the committed champion EXACTLY: scaling the gross book and
    re-applying the identical margin/cost leaves c_t unchanged (margin add-back identity)."""
    champ = r2.CHAMP
    m = pd.Series(1.0, index=champ.index)
    ov = r2.overlay_book(champ, m)
    j = pd.concat([champ.rename('c'), ov.rename('o')], axis=1).dropna()
    assert float((j.c - j.o).abs().max()) < 1e-12


def test_slot_overlay_identity_at_m1():
    """Slot multipliers == 1 must reproduce the committed champion net exactly (proves the
    rebuilt cost machinery — full |dW| turnover day-1 seeded + margin — is the champion's)."""
    net, Wg, df = r2.build_champion()
    M = pd.DataFrame(1.0, index=Wg.index, columns=Wg.columns)
    net2 = r2.apply_slot_overlay(Wg, df, M)
    j = pd.concat([net.rename('n'), net2.rename('n2')], axis=1).dropna()
    assert float((j.n - j.n2).abs().max()) < 1e-12


# ---------------------------------------------------------- 4. overlay economics
def test_overlay_is_t_plus_1():
    """A trigger that fires at close t must affect PnL from t+1, not t. Baseline m=1 with a
    single-day dip to 0.6 at d0 (We=m.shift(1)): day d0 itself must be IDENTICAL to champion
    (dip not yet held), d0+1 scaled (dip held), d0+2 back to champion (dip expired)."""
    champ = r2.CHAMP
    m = pd.Series(1.0, index=champ.index)
    d0 = champ.index[300]
    m.loc[d0] = 0.6
    ov = r2.overlay_book(champ, m)
    assert abs(ov.loc[d0] - champ.loc[d0]) < 1e-12                # day t: unaffected
    assert abs(ov.loc[champ.index[301]] - champ.loc[champ.index[301]]) > 1e-9  # day t+1: scaled
    # R2 spec repair: day t+2 exposure IS back at full, but the 0.6->1.0 dip-back trades
    # 0.4*1.6 notional -> exactly -4.096bp turnover vs champion (honest entry+exit costs).
    cost = 0.4 * GEAR * BPS / 1e4
    assert abs(ov.loc[champ.index[302]] - (champ.loc[champ.index[302]] - cost)) < 1e-12


def test_overlay_turnover_cost_charged():
    """A 1.0 -> 0.6 rescale of a 1.6-gross book trades 0.4*1.6 notional -> cost
    |dm|*GEAR*BPS/1e4 on the first held day. Measured against an m=1 run on a FLAT book.
    R2 spec repair: the stale expectation ov[4] == -cost ignored the margin add-back that
    the sibling test (test_overlay_margin_scales_down) co-specifies: with c_t=0 flat, the
    book's pnl stream is +margin_const/day, so the overlaid day is m*margin_const - cost.
    Both tests pin the same construction; the identity below is the consistent one."""
    idx = pd.bdate_range('2020-01-01', periods=6)
    champ = pd.Series(0.0, index=idx)       # flat champion book isolates costs
    m = pd.Series(1.0, index=idx)
    m.iloc[3:] = 0.6
    ov = r2.overlay_book(champ, m)
    exp_cost = 0.4 * GEAR * BPS / 1e4       # 0.4 * 1.6 * 6.4e-4
    assert abs(ov.iloc[:3].sum()) < 1e-15                       # m=1 vs c=0: margin cancels
    # day 4 = first day the 0.6 dip is held: m*margin_const - cost (T+1)
    assert abs(ov.iloc[4] - (0.6 * r2.MARGIN_CONST - exp_cost)) < 1e-15
    assert abs(ov.iloc[5] - 0.6 * r2.MARGIN_CONST) < 1e-15      # held, no further turnover


def test_overlay_margin_scales_down():
    """Margin must be charged on the OVERLAID gross max(m*1.6-1,0): at m=0.6 gross=0.96<1
    so margin is ZERO (the naive m*c would keep charging the champion's full margin)."""
    idx = pd.bdate_range('2020-01-01', periods=6)
    champ = pd.Series(0.0, index=idx)       # c_t = 0 means gross_pnl = +margin_const
    m = pd.Series(0.6, index=idx)
    ov = r2.overlay_book(champ, m)
    # day>=1: m=0.6 held -> port = 0.6*margin_const; margin 0; entry cost 0.4*1.6*bps on day1
    day2 = ov.iloc[2]
    assert abs(day2 - 0.6 * r2.MARGIN_CONST) < 1e-15


def test_overlay_gross_never_above_cap():
    """Leverage gate: overlaid gross = m*1.6 <= 1.6 for any m in [0,1]; slot overlay gross
    must also stay <= 1.6 every day."""
    net, Wg, df = r2.build_champion()
    rng = np.random.default_rng(5)
    m = pd.Series(rng.uniform(0.3, 1.0, len(Wg)), index=Wg.index)
    M = pd.DataFrame({c: m for c in Wg.columns})
    g = Wg.mul(M, axis=0).abs().sum(axis=1)
    assert g.max() <= GEAR + 1e-9


def test_overlay_no_lookahead_vix():
    """Rebuilding the VIX gate from inputs truncated at T yields the identical prefix."""
    full = r2.build_vix_trigger()
    T = pd.Timestamp('2020-04-15')
    tr = r2.build_vix_trigger(upto=T)
    exp = full[full.index <= T]
    pd.testing.assert_series_equal(exp.round(10), tr.reindex(exp.index).round(10))


# ---------------------------------------------------------- 5. acceptance machinery
def test_acceptance_gate_logic():
    """Acceptance: (d_ann >= +0.3pp OR d_mdd >= +0.5pp) AND neg_years==0 AND gross<=1.6
    AND scramble-stable. Border cases pinned."""
    assert r2.accepts(d_ann=0.004, d_mdd=0.000, neg=0, gross_max=1.6, p_scramble=0.02)
    assert r2.accepts(d_ann=-0.010, d_mdd=0.006, neg=0, gross_max=1.6, p_scramble=0.01)
    assert not r2.accepts(d_ann=0.002, d_mdd=0.004, neg=0, gross_max=1.6, p_scramble=0.01)
    assert not r2.accepts(d_ann=0.005, d_mdd=0.000, neg=0, gross_max=1.6, p_scramble=0.30)
    assert not r2.accepts(d_ann=0.005, d_mdd=0.000, neg=1, gross_max=1.6, p_scramble=0.01)
    assert not r2.accepts(d_ann=0.005, d_mdd=0.000, neg=0, gross_max=1.62, p_scramble=0.01)
