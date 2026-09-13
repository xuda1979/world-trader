"""AUDIT_GATES2 round 1: negative + positive controls for the hunt-gate battery.

Every control maps to a GATES_CONTRACT.md gate. Contract is the SPEC; bt.gates is the IMPL.
A control going RED means the gate as-implemented can spuriously pass noise, miss a real
signal, or diverge from the contract — i.e. agents' 'pass' is not trustworthy.
"""
import numpy as np, pandas as pd, pytest
from bt import gates as G
from bt import engine as E
from bt.metrics import sharpe_d, half_split, neg_years

import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ROOT = "/Users/daxu/software/world-trader"
# cwd-relative CHAMP broke when pytest ran from anywhere but repo root
# (5 false FAILs from coord/, standup 2026-09-07 00:5x); mirror test_rawew13v2.py.
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"


def _idx(n, start='2015-01-01'):
    return pd.date_range(start, periods=n, freq='B')


def _series(vals, start='2015-01-01'):
    return pd.Series(np.asarray(vals, dtype=float), index=_idx(len(vals), start))


# ---------------------------------------------------------------- contract lock
def test_audit_defaults_match_contract():
    """GATES_CONTRACT: full SR>=1.0, H1/H2>=0.5, <=2 neg yrs each > -5%, |corr|<0.15, p<0.05."""
    d = G.DEFAULTS
    assert d['sr_min'] == 1.0, f"DEFAULTS sr_min={d['sr_min']} but contract requires >=1.0"
    assert d['h_min'] == 0.5, f"DEFAULTS h_min={d['h_min']} but contract requires >=0.5"
    assert d['neg_max'] == 2
    assert d['neg_floor'] == -0.05
    assert d['corr_max'] == 0.15
    assert d['p_max'] == 0.05


# ---------------------------------------------------------------- signal-scramble
def test_audit_scramble_noise_no_spurious_pass():
    """200 synthetic NOISE sleeves: p must NOT cluster low (no spurious p<0.05 passes)."""
    rng = np.random.default_rng(7)
    ps = []
    for _ in range(200):
        ret = rng.normal(0, 0.01, 900)
        sig = rng.normal(0, 1, 900)          # positions unrelated to returns
        p, real = G.scramble_positions(sig, ret, n=200, block=20, rng=rng)
        ps.append(p)
    ps = np.array(ps)
    frac_pass = float((ps < 0.05).mean())
    assert frac_pass <= 0.08, f"noise false-pass rate {frac_pass:.3f} (spurious gates!)"
    assert 0.35 < ps.mean() < 0.65, f"noise p mean {ps.mean():.3f} not ~centered"


def test_audit_scramble_noise_p_approx_uniform():
    """Charter: noise p ~ uniform. KS distance vs U(0,1) must be small."""
    from scipy.stats import kstest
    rng = np.random.default_rng(8)
    ps = []
    for _ in range(200):
        ret = rng.normal(0, 0.01, 900)
        sig = rng.normal(0, 1, 900)
        p, _ = G.scramble_positions(sig, ret, n=200, block=20, rng=rng)
        ps.append(p)
    ps = np.array(ps)
    ks = float(kstest(ps, 'uniform').statistic)
    assert ks < 0.15, f"noise p distribution not ~uniform (KS={ks:.3f}, mean={ps.mean():.3f})"


def test_audit_scramble_strong_detected():
    """Synthetic STRONG timing sleeve at contract n=200 scrambles must be detected (p<0.05)."""
    rng = np.random.default_rng(11)
    n = 1200
    ret = rng.normal(0.0004, 0.01, n)                    # modest drift
    sig = np.sign(pd.Series(ret).rolling(5).mean().fillna(0.0).values)  # momentum timing
    p, real = G.scramble_positions(sig, ret, n=200, block=20, rng=rng)
    assert real > 0.5, f"fixture broken: real book SR {real:.3f} not strong"
    assert p < 0.05, f"strong book NOT detected, p={p:.3f}"


# ---------------------------------------------------------------- halves
def test_audit_halves_strongH1_weakH2_must_fail():
    """Contract c): H1>=0.5 AND H2>=0.5. H2 SR ~0.4 violates contract -> gate must FAIL it."""
    rng = np.random.default_rng(5)
    n = 2000
    drift = np.concatenate([np.full(n // 2, 0.0015), np.full(n - n // 2, -0.0004)])
    r = pd.Series(rng.normal(0, 0.01, n) + drift, index=_idx(n))
    h1, h2 = half_split(r)
    assert h1 >= 0.5 and h2 < 0.5, f"fixture: H1={h1:.2f} H2={h2:.2f}"
    g = G.run(r, ref=pd.Series(rng.normal(0, 0.01, n), index=r.index))
    assert g['halves_ok'] is False, f"contract-violating halves PASSED (H1={h1:.2f}, H2={h2:.2f})"
    assert g['pass'] is False, "a sleeve failing the contract must not gate-pass"


def test_audit_halves_two_strong_halves_pass():
    rng = np.random.default_rng(6)
    n = 2000
    r = pd.Series(rng.normal(0.0009, 0.01, n), index=_idx(n))
    h1, h2 = half_split(r)
    assert h1 >= 0.5 and h2 >= 0.5, f"fixture: H1={h1:.2f} H2={h2:.2f}"
    g = G.run(r, ref=pd.Series(rng.normal(0, 0.01, n), index=r.index))
    assert g['halves_ok'] is True


# ---------------------------------------------------------------- yearly
def test_audit_yearly_one_minus6pct_year_fails():
    """Contract d): each negative year must be > -5%. One -6% year must FAIL."""
    yr = {2020: 0.10, 2021: -0.06, 2022: 0.10}
    r = _series_from_yearly(yr, seed=31)
    neg, worst = neg_years(r)
    assert neg == 1 and abs(worst + 0.06) < 0.01, f"fixture: neg={neg} worst={worst:.4f}"
    g = G.run(r, ref=pd.Series(np.random.default_rng(32).normal(0, 0.01, len(r)), index=r.index))
    assert g['neg_ok'] is False, f"-6% year PASSED the yearly gate (worst={worst:.4f})"


def test_audit_yearly_shallow_neg_passes():
    yr = {2020: 0.10, 2021: -0.03, 2022: 0.10}
    r = _series_from_yearly(yr, seed=33)
    g = G.run(r, ref=pd.Series(np.random.default_rng(34).normal(0, 0.01, len(r)), index=r.index))
    assert g['neg_ok'] is True, "a -3% year must NOT fail the yearly gate"


def _series_from_yearly(yr_map, seed=0, days=252):
    """Build a daily series hitting approx target yearly returns (simple scaled draws)."""
    rng = np.random.default_rng(seed)
    parts = []
    for y, tgt in sorted(yr_map.items()):
        x = rng.normal(0, 0.01, days)
        # shift to hit the target yearly log-return
        x += (np.log1p(tgt) - np.log1p((1 + x).prod() - 1)) / days
        parts.append(pd.Series(x, index=pd.date_range(f'{y}-01-01', periods=days, freq='B')))
    return pd.concat(parts)


# ---------------------------------------------------------------- plateau
def test_audit_plateau_spike_rejected():
    """Contract b): chosen params must sit on a plateau (neighbors within 20% of peak SR).
    A single-spike param grid must be REJECTED."""
    grid = {0.8: 0.20, 0.9: 0.40, 1.0: 2.50, 1.1: 0.35, 1.2: 0.15}   # spike at 1.0
    ok, info = G.plateau_ok(grid, chosen=1.0, tol=0.2)
    assert ok is False, f"single-spike param passed plateau gate: {info}"


def test_audit_plateau_smooth_accepted():
    grid = {0.8: 1.90, 0.9: 2.10, 1.0: 2.50, 1.1: 2.20, 1.2: 2.05}   # broad plateau
    ok, info = G.plateau_ok(grid, chosen=1.0, tol=0.2)
    assert ok is True, f"smooth plateau rejected: {info}"


def test_audit_plateau_edge_of_grid_uses_available_neighbors():
    grid = {0.8: 2.40, 0.9: 2.30, 1.0: 2.50}   # chosen at grid edge, neighbors strong
    ok, _ = G.plateau_ok(grid, chosen=0.8, tol=0.2)
    assert ok is True


# ---------------------------------------------------------------- decorrelation
def test_audit_corr_computation_matches_manual():
    """corr_to must equal a manual Pearson on the date-aligned overlap."""
    champ = pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']
    rng = np.random.default_rng(41)
    cand = pd.Series(rng.normal(0, 0.01, len(champ)), index=champ.index)
    g = G.run(cand, ref=champ)
    both = pd.concat([champ.rename('a'), cand.rename('b')], axis=1).dropna()
    manual = float(np.corrcoef(both.a, both.b)[0, 1])
    assert abs(g['corr'] - manual) < 1e-12, f"corr mismatch: gates={g['corr']:.6f} manual={manual:.6f}"


def test_audit_corr_self_champion_fails():
    """corr(champion, champion)=1 must NOT pass the |corr|<0.15 gate (sanity of sign/abs)."""
    champ = pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']
    g = G.run(champ, ref=champ)
    assert abs(g['corr'] - 1.0) < 1e-9
    assert g['corr_ok'] is False


def test_audit_corr_noise_vs_champion_passes():
    champ = pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']
    rng = np.random.default_rng(42)
    cand = pd.Series(rng.normal(0, 0.01, len(champ)), index=champ.index)
    g = G.run(cand, ref=champ)
    assert abs(g['corr']) < 0.15 and g['corr_ok'] is True


def test_audit_corr_no_overlap_fails_closed():
    """Almost-disjoint calendars -> corr undefined -> gate must FAIL CLOSED, not pass."""
    champ = pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']
    cand = pd.Series([0.01, -0.01, 0.005],
                     index=pd.date_range('2030-01-01', periods=3, freq='B'))
    g = G.run(cand, ref=champ)
    assert g['corr_ok'] is False, f"undefined corr must fail closed, got {g['corr']}"


# ---------------------------------------------------------------- leverage / cost (full |dW|)
def test_audit_cost_is_full_dw_one_side():
    """TRADE_RECORD_STANDARD: cost = FULL |dW| one-side * 6.4bps, incl. the entry trade."""
    w = pd.DataFrame({'w': [0.0, 1.0, 1.0, -0.5, 0.0]})
    c = E.cost_turnover(w, cost_bps=6.4)
    dw = float(np.abs(np.diff(np.concatenate([[0.0], w['w'].values]))).sum())
    assert abs(c.sum() - dw * 6.4e-4) < 1e-12, f"cost {c.sum():.3e} != full|dW| {dw}*6.4e-4"


def test_audit_entry_trade_charged():
    w = pd.DataFrame({'w': [1.0, 1.0]})
    c = E.cost_turnover(w, cost_bps=6.4)
    assert abs(c.iloc[0] - 6.4e-4) < 1e-12, f"entry trade not charged: {c.iloc[0]:.3e}"


def test_audit_cap_leverage_enforces_gross():
    w = pd.DataFrame({'a': [1.0, -1.2], 'b': [1.0, 0.8]})   # gross 2.0
    wc = E.cap_leverage(w, max_lev=1.6)
    gross = wc.abs().sum(axis=1)
    assert (gross <= 1.6 + 1e-9).all(), f"leverage cap violated: {gross.max():.4f}"
    assert abs(gross.iloc[0] - 1.6) < 1e-6


# ---------------------------------------------------------------- composite end-to-end
def test_audit_composite_noise_sleeve_fails_all():
    """Full battery on a NOISE sleeve: must NOT pass (SR gate is the first line of defense)."""
    rng = np.random.default_rng(51)
    n = 2000
    r = pd.Series(rng.normal(0, 0.01, n), index=_idx(n))
    g = G.run(r, ref=pd.Series(rng.normal(0, 0.01, n), index=r.index))
    assert g['pass'] is False and g['sr_ok'] is False


def test_audit_composite_strong_sleeve_passes():
    """Full battery on a genuinely strong, decorrelated sleeve: must PASS every gate."""
    rng = np.random.default_rng(52)
    n = 2000
    # exact-centered noise (mean removed) + drift set so realized full SR ~2.0: the neg-year
    # gate (each year > -5%) needs enough drift headroom that sample noise in one 252d year
    # cannot produce a -10% year on a sleeve whose TRUE yearly edge is ~+22%.
    draws = rng.normal(0, 0.01, n)
    # AUDIT_GATES2 R2: run() enforces the scramble gate fail-closed, so this composite
    # control must supply REAL timing positions. AR(1) raw + lagged 5d-mean sign gives a
    # genuinely timed book; r stays the PER-UNIT return stream (engine builds sig*r itself).
    eps = draws
    raw = np.empty(n)
    raw[0] = eps[0]
    for t in range(1, n):
        raw[t] = 0.55 * raw[t - 1] + eps[t]
    sig = np.sign(pd.Series(raw).rolling(5).mean().shift(1).fillna(0.0).values)
    r = pd.Series(raw, index=_idx(n))
    ref = pd.Series(rng.normal(0, 0.01, n), index=r.index)
    g = G.run(r, ref=ref, sig=sig, scramble_n=200)
    assert g['scr_ok'] is True, f"timed strong sleeve failed enforced scramble: scr_p={g['scr_p']}"
    assert g['pass'] is True, {k: v for k, v in g.items() if not str(k).endswith('ok')}


def test_audit_champion_stats_reachable():
    """The committed champion must clear SR/halves/yearly gates (corr-to-self excluded)."""
    champ = pd.read_csv(CHAMP, parse_dates=['date']).set_index('date')['ret']
    sr = sharpe_d(champ)
    h1, h2 = half_split(champ)
    neg, worst = neg_years(champ)
    assert sr >= 1.0, f"champion SR {sr:.2f}"
    assert h1 >= 0.5 and h2 >= 0.5, f"champion halves {h1:.2f}/{h2:.2f}"
    assert neg <= 2 and worst > -0.05, f"champion yearly neg={neg} worst={worst:.4f}"


# ---------------------------------------------------------------- R1 addendum (hole-hunt)
def test_audit_plateau_one_sided_cliff_rejected():
    """Contract b) says NEIGHBORS (plural) within 20% of peak. A chosen param with one strong
    and one collapsed neighbor is a half-spike, not a plateau: must be REJECTED."""
    grid = {0.8: 2.40, 0.9: 2.45, 1.0: 2.50, 1.1: 0.08, 1.2: 0.10}  # right neighbor cliff
    ok, info = G.plateau_ok(grid, chosen=1.0, tol=0.2)
    assert ok is False, f"one-sided cliff passed plateau gate: {info}"


def test_audit_corr_missing_ref_fails_closed():
    """Contract header: ALL gates fail-closed. run() without a champion ref must NOT report
    corr_ok=True / pass=True — the decorrelation gate cannot silently pass."""
    rng = np.random.default_rng(61)
    n = 2000
    r = pd.Series(rng.normal(0.0013, 0.01, n), index=_idx(n))
    g = G.run(r, ref=None)
    assert g['corr_ok'] is False, f"missing ref must fail closed, got corr_ok={g['corr_ok']}"
    assert g['pass'] is False
